"""动作目录的应用服务：编排事务性的动作与指导写操作。

读操作直接透传仓储；写操作保证“一次用户动作一个事务”。
校验规则本身属于领域层（domain/exercises.py），这里只负责调用与事务编排。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ..domain.exercises import GuidanceStatus, require_review_metadata

if TYPE_CHECKING:
    from ..data.exercise_repositories import ExerciseRepository


class ExerciseService:
    def __init__(self, repository: "ExerciseRepository"):
        self.repository = repository

    def list(self, query: str = "", include_inactive: bool = False) -> list[dict[str, Any]]:
        if query.strip():
            return self.repository.search(query, include_inactive)
        return self.repository.list(include_inactive)

    def add_guidance_draft(self, exercise_id: int, guidance: dict[str, Any]) -> int:
        with self.repository.transaction():
            return self.repository.add_guidance_revision(exercise_id, guidance)

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
        with self.repository.transaction():
            exercise_id = self.repository.create(name, category, equipment, body_areas)
            for alias in aliases:
                self.repository.add_alias(exercise_id, alias)
            self.repository.add_guidance_revision(exercise_id, guidance)
            return exercise_id

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

    def set_active(self, exercise_id: int, active: bool) -> None:
        self._run_transaction(lambda: self.repository.set_active(exercise_id, active))

    def _run_transaction(self, operation: Callable[[], None]) -> None:
        with self.repository.transaction():
            operation()
