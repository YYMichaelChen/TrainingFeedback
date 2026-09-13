"""动作目录的应用服务：编排事务性的动作与指导写操作。

读操作直接透传仓储；写操作保证“一次用户动作一个事务”。
校验规则本身属于领域层（domain/exercises.py），这里只负责调用与事务编排。
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from ..data.review_attachments import ReviewAttachmentError, store_review_answer
from ..domain.clock import Clock, SystemClock
from ..domain.exercises import (
    GuidanceStatus,
    fresh_guidance_draft,
    require_review_metadata,
    require_review_occurrence,
    review_status,
    validate_guidance,
)

if TYPE_CHECKING:
    from ..data.exercise_repositories import ExerciseRepository


class ExerciseService:
    def __init__(
        self,
        repository: "ExerciseRepository",
        clock: Clock | None = None,
        data_root: Path | None = None,
    ):
        self.repository = repository
        self.clock = clock or SystemClock()
        # 数据根仅用于保存受管的审核答复原件；没有它时附件功能明确不可用，而不是静默跳过。
        self.data_root = Path(data_root) if data_root is not None else None

    def list(self, query: str = "", include_inactive: bool = False) -> list[dict[str, Any]]:
        if query.strip():
            return self.repository.search(query, include_inactive)
        return self.repository.list(include_inactive)

    def get(self, exercise_id: int) -> dict[str, Any] | None:
        return self.repository.get(exercise_id)

    def preview_bundled_guidance(self) -> list[dict[str, Any]]:
        """Describe bundled drafts and possible local targets without making writes."""
        from ..data.seed.catalog import bundled_catalog

        all_exercises = self.repository.list(include_inactive=True)
        preview = []
        for item in bundled_catalog():
            bound = self.repository.get_by_bundled_key(item["exercise_key"])
            matches = self.repository.find_identity_matches(
                [item["canonical_name"], *item["aliases"]]
            )
            target = None
            if bound is not None:
                target = bound
                match_status = "bound"
                candidates = [bound]
            else:
                candidates = matches
                eligible_matches = [
                    match
                    for match in matches
                    if match.get("bundled_exercise_key") in (None, item["exercise_key"])
                ]
                if len(matches) > 1:
                    match_status = "ambiguous"
                elif len(matches) == 1 and not eligible_matches:
                    match_status = "conflict"
                elif len(eligible_matches) == 1:
                    target = eligible_matches[0]
                    match_status = "name_match"
                else:
                    match_status = "missing"
            if target is not None and self.repository.has_bundled_guidance(
                target["id"], item["content_id"], item["content_version"]
            ):
                match_status = "up_to_date"
            options = [
                {
                    "id": exercise["id"],
                    "canonical_name": exercise["canonical_name"],
                    "active": exercise["active"],
                    "bundled_exercise_key": exercise.get("bundled_exercise_key"),
                }
                for exercise in all_exercises
                if exercise.get("bundled_exercise_key") in (None, item["exercise_key"])
            ]
            preview.append(
                {
                    **item,
                    "match_status": match_status,
                    "target_exercise_id": target["id"] if target is not None else None,
                    "target_exercise_name": (
                        target["canonical_name"] if target is not None else None
                    ),
                    "candidate_exercises": [
                        {
                            "id": candidate["id"],
                            "canonical_name": candidate["canonical_name"],
                            "bundled_exercise_key": candidate.get(
                                "bundled_exercise_key"
                            ),
                        }
                        for candidate in candidates
                    ],
                    "target_options": options,
                }
            )
        return preview

    def accept_bundled_guidance(
        self, selections: dict[str, int], import_keys: Sequence[str] = ()
    ) -> list[int]:
        """Link selected local exercises and append the selected bundled drafts atomically.

        `import_keys` 里的内置动作在本地不存在，按用户明确选择创建为新动作，连带别名、
        分类、器械与主次部位，并只附一份未审核草稿；不会写入任何批准或启用事实。
        """
        from ..data.seed.catalog import bundled_catalog

        imports = list(dict.fromkeys(import_keys))
        if not selections and not imports:
            return []
        bundled = bundled_catalog()
        by_key = {item["exercise_key"]: item for item in bundled}
        unknown = (set(selections) | set(imports)) - set(by_key)
        if unknown:
            raise ValueError("Unknown bundled exercise selection.")
        if set(selections) & set(imports):
            raise ValueError("A bundled exercise is either imported or mapped, not both.")
        if len(set(selections.values())) != len(selections):
            raise ValueError("Each bundled exercise requires a different local exercise.")
        created = []
        with self.repository.transaction(immediate=True):
            for key in imports:
                created.append(self._import_bundled_exercise(by_key[key]))
            for item in bundled:
                if item["exercise_key"] not in selections:
                    continue
                exercise_id = selections[item["exercise_key"]]
                exercise = self.repository.get(exercise_id)
                if exercise is None:
                    raise ValueError("Selected exercise was not found.")
                current_key = exercise.get("bundled_exercise_key")
                if current_key not in (None, item["exercise_key"]):
                    raise ValueError(
                        "Selected exercise is linked to different bundled content."
                    )
                self.repository.set_bundled_exercise_key(
                    exercise_id, item["exercise_key"]
                )
                if self.repository.has_bundled_guidance(
                    exercise_id, item["content_id"], item["content_version"]
                ):
                    continue
                validation = validate_guidance(
                    item["guidance"], require_body_areas=True
                )
                if not validation.complete:
                    raise ValueError("Bundled guidance is incomplete.")
                draft = fresh_guidance_draft(item["guidance"])
                created.append(
                    self.repository.add_guidance_revision(
                        exercise_id,
                        draft,
                        bundled_content_id=item["content_id"],
                        bundled_content_version=item["content_version"],
                    )
                )
        return created

    def _import_bundled_exercise(self, item: dict[str, Any]) -> int:
        """在调用方事务内把一个内置动作创建为新动作，返回其未审核草稿的版本 id。"""
        if self.repository.get_by_bundled_key(item["exercise_key"]) is not None:
            raise ValueError("The bundled exercise is already present in this data root.")
        # 事务内重查同名/别名，避免预览之后本地又出现同一动作。
        if self.repository.find_identity_matches(
            [item["canonical_name"], *item["aliases"]]
        ):
            raise ValueError(
                "A local exercise already uses that name or alias; map it instead of importing."
            )
        validation = validate_guidance(item["guidance"], require_body_areas=True)
        if not validation.complete:
            raise ValueError("Bundled guidance is incomplete.")
        exercise_id = self.repository.create(
            item["canonical_name"],
            item["category"],
            item["equipment_summary"],
            item["body_areas"],
            bundled_exercise_key=item["exercise_key"],
        )
        for alias in item["aliases"]:
            self.repository.add_alias(exercise_id, alias)
        return self.repository.add_guidance_revision(
            exercise_id,
            fresh_guidance_draft(item["guidance"]),
            bundled_content_id=item["content_id"],
            bundled_content_version=item["content_version"],
        )

    def add_guidance_draft(self, exercise_id: int, guidance: dict[str, Any]) -> int:
        draft = fresh_guidance_draft(guidance)
        with self.repository.transaction():
            return self.repository.add_guidance_revision(exercise_id, draft)

    def create_exercise(
        self,
        name: str,
        category: str,
        equipment: str,
        body_areas: list[tuple[str, bool]],
        aliases: list[str],
        guidance: dict[str, Any],
    ) -> int:
        """新建动作及其别名、首个指导草稿，全部在一个事务中完成。"""
        draft = fresh_guidance_draft(guidance)
        with self.repository.transaction():
            self.repository.validate_identity(None, name, aliases)
            exercise_id = self.repository.create(name, category, equipment, body_areas)
            for alias in aliases:
                self.repository.add_alias(exercise_id, alias)
            self.repository.add_guidance_revision(exercise_id, draft)
            return exercise_id

    def edit_exercise(
        self,
        exercise_id: int,
        name: str,
        category: str,
        equipment: str,
        primary_areas: list[str],
        aliases: list[str],
        guidance: dict[str, Any],
    ) -> int:
        """Save every editable exercise field and its new guidance draft atomically."""
        draft = fresh_guidance_draft(guidance)
        with self.repository.transaction():
            self.repository.validate_identity(exercise_id, name, aliases)
            self.repository.replace_aliases(exercise_id, aliases, name)
            self.repository.update_metadata(exercise_id, name, category, equipment)
            self.repository.replace_primary_body_areas(exercise_id, primary_areas)
            return self.repository.add_guidance_revision(exercise_id, draft)

    def update_metadata(self, exercise_id: int, name: str, category: str, equipment: str) -> None:
        self._run_transaction(
            lambda: self.repository.update_metadata(exercise_id, name, category, equipment)
        )

    def submit_for_review(self, revision_id: int) -> None:
        self._run_transaction(
            lambda: self.repository.set_guidance_status(revision_id, GuidanceStatus.PENDING_REVIEW)
        )

    def approve_guidance(self, revision_id: int, review: dict[str, Any]) -> None:
        require_review_metadata(review)
        self._run_transaction(
            lambda: self.repository.set_guidance_status(
                revision_id, GuidanceStatus.APPROVED, review
            )
        )

    def activate_guidance(self, revision_id: int) -> None:
        self._run_transaction(lambda: self.repository.activate_guidance(revision_id))

    def review_and_activate_guidance(self, revision_id: int, review: dict[str, Any]) -> None:
        """审核并立即启用指导；仓储方法内部已用单个立即事务保证原子性。"""
        require_review_metadata(review)
        self.repository.review_and_activate_guidance(revision_id, review)

    def confirm_guidance_review(
        self,
        revision_id: int,
        *,
        review_source: str,
        reviewed_at: str,
        review_note: str = "",
        user_confirmed: bool = False,
        answer_file: Path | None = None,
    ) -> None:
        """Record actual external evidence and this explicit approval as separate facts."""
        self.confirm_guidance_reviews(
            [revision_id],
            review_source=review_source,
            reviewed_at=reviewed_at,
            review_note=review_note,
            user_confirmed=user_confirmed,
            answer_file=answer_file,
        )

    def confirm_guidance_reviews(
        self,
        revision_ids: Sequence[int],
        *,
        review_source: str,
        reviewed_at: str,
        review_note: str = "",
        user_confirmed: bool = False,
        answer_file: Path | None = None,
    ) -> int:
        """把同一次真实外部审核批准到多个明确选中的版本上。

        每一项都是独立的用户批准事实，但共享这一次审核的来源、发生时间和可选原件；
        任一项失败则整体回滚，并删除本次刚复制的受管原件。
        """
        if user_confirmed is not True:
            raise ValueError("Explicit user approval is required.")
        selected = list(dict.fromkeys(revision_ids))
        if not selected:
            raise ValueError("Select at least one guidance revision to approve.")
        require_review_occurrence(reviewed_at)
        review = {
            "reviewer_type": "external_ai_expert",
            "review_source": review_source,
            "reviewed_at": reviewed_at,
            "review_note": review_note,
            "user_approved_at": self.clock.now().isoformat(),
        }
        require_review_metadata(review)
        attachment = None
        if answer_file is not None:
            if self.data_root is None:
                raise ReviewAttachmentError(
                    "This data root cannot store review answer files."
                )
            attachment = store_review_answer(self.data_root, answer_file)
            review["review_answer_file"] = attachment.relative_path
            review["review_answer_sha256"] = attachment.sha256
            review["review_answer_original_name"] = attachment.original_name
        try:
            self.repository.review_and_activate_guidance_batch(selected, review)
        except Exception:
            if attachment is not None:
                attachment.remove_from(self.data_root)
            raise
        return len(selected)

    def list_reviewable_guidance(self) -> list[dict[str, Any]]:
        """列出可进入批准流程的版本（草稿、待审核、已拒绝），供批量审核使用。"""
        reviewable = []
        for summary in self.repository.list(include_inactive=True):
            exercise = self.repository.get(summary["id"])
            if exercise is None:
                continue
            active_id = exercise.get("active_guidance_revision_id")
            for revision in exercise.get("guidance", []):
                if review_status(revision["guidance"]) not in {
                    GuidanceStatus.DRAFT,
                    GuidanceStatus.PENDING_REVIEW,
                    GuidanceStatus.REJECTED,
                }:
                    continue
                reviewable.append(
                    {
                        "exercise_id": exercise["id"],
                        "exercise_name": exercise["canonical_name"],
                        "exercise_active": bool(exercise.get("active")),
                        "revision_id": revision["id"],
                        "revision_number": revision["revision_number"],
                        "bundled_content_id": revision.get("bundled_content_id"),
                        "bundled_content_version": revision.get("bundled_content_version"),
                        "guidance": revision["guidance"],
                        "active_revision_id": active_id,
                        "active_guidance": next(
                            (
                                item["guidance"]
                                for item in exercise.get("guidance", [])
                                if item["id"] == active_id
                            ),
                            None,
                        ),
                    }
                )
        return reviewable

    def set_active(self, exercise_id: int, active: bool) -> None:
        self._run_transaction(lambda: self.repository.set_active(exercise_id, active))

    def _run_transaction(self, operation: Callable[[], None]) -> None:
        with self.repository.transaction():
            operation()
