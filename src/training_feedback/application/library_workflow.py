"""New-model catalog browsing, exact-version review and shared eligibility entry points."""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ..data.catalog_resources import CatalogError, managed_path
from ..data.database import transaction
from ..data.library_images import decode_image_size, inspect_images
from ..data.review_attachments import store_review_answer
from ..domain.catalog import ExerciseReference, require_content_envelope
from ..domain.exercises import normalize_name, require_review_occurrence
from ..domain.library_eligibility import assess_eligibility, image_hashes
from .library_service import LibraryService


@dataclass(frozen=True)
class LibraryTarget:
    exercise: ExerciseReference
    content: dict


class LibraryWorkflowService(LibraryService):
    def _display_image_checks(self, entry: dict):
        """Reuse unchanged image checks for browsing; actions still validate afresh."""
        images = entry["content"]["guidance"]["images"]
        signature = []
        for image in images:
            try:
                declaration = managed_path(self.data_root, image["path"])
                if "assets" in entry:
                    digest = entry["assets"][image["path"]]
                    path = managed_path(self.assets.root, digest)
                else:
                    path = managed_path(self.catalog.directory, image["path"])
                actual_hash = None
                if image["status"] == "available" and not image.get("placeholder"):
                    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                signature.append((str(declaration), str(path), image["sha256"],
                                  image["status"], image["required"],
                                  image.get("placeholder"), actual_hash))
            except (OSError, ValueError, KeyError, TypeError):
                signature.append((image.get("path"), image.get("sha256"), None))
        key = entry["reference"]["sha256"]
        signature = tuple(signature)
        cache = getattr(self, "_display_checks_cache", None)
        if cache is None:
            cache = self._display_checks_cache = {}
        cached = cache.get(key)
        if cached is not None and cached[0] == signature:
            return cached[1]
        checks = inspect_images(images, lambda image: self._read_image(entry, image))
        if len(cache) >= 128:
            cache.clear()
        cache[key] = (signature, checks)
        return checks

    def target_entry(self, target: LibraryTarget) -> dict:
        exercise = self.get(target.exercise)
        if exercise is None:
            raise CatalogError("Unknown exercise identity.")
        candidates = list(exercise["local_contents"])
        if exercise["bundled"]:
            candidates.append(exercise["bundled"])
        entry = next((item for item in candidates if item["reference"] == target.content), None)
        if entry is None:
            raise CatalogError("The displayed content changed.")
        return entry

    def latest_target(self, exercise: ExerciseReference) -> LibraryTarget | None:
        """最新内容版本的显示目标：本地覆盖版本优先，其次程序内置。"""
        row = self.get(exercise)
        if row is None:
            return None
        entry = row["local_contents"][-1] if row["local_contents"] else row["bundled"]
        if entry is None:
            return None
        return LibraryTarget(exercise, entry["reference"])

    def _read_image(self, entry: dict, image: dict) -> bytes:
        # Validate the stored declaration even when content-addressed bytes are used.
        managed_path(self.data_root, image["path"])
        if image["path"].split("/")[0] not in {"images", "custom-exercise-images"}:
            raise CatalogError("Image is outside the managed image directories.")
        if "assets" in entry:
            digest = entry["assets"][image["path"]]
            if digest != image["sha256"]:
                raise CatalogError("Image binding does not match the content revision.")
            return self.assets.read(digest)
        return self.catalog.image_bytes(image)

    def review_events(self, target: LibraryTarget) -> list[dict]:
        entry = self.target_entry(target)
        return self.user.review_events(entry["id"]) if "id" in entry else []

    def eligibility(self, target: LibraryTarget):
        return self.content_eligibility(
            target, removed=self.removal_state(target.exercise)["removed"],
        )

    def content_eligibility(self, target: LibraryTarget, *, removed=False):
        entry = self.target_entry(target)
        checks = inspect_images(entry["content"]["guidance"]["images"],
                                lambda image: self._read_image(entry, image))
        events = self.user.review_events(entry["id"]) if "id" in entry else []
        return assess_eligibility(entry["content"], entry["reference"]["sha256"], checks,
                                  events[-1] if events else None, removed=removed)

    def checked_image(self, target: LibraryTarget, index: int) -> bytes:
        entry = self.target_entry(target)
        image = entry["content"]["guidance"]["images"][index]
        data = self._read_image(entry, image)
        checks = inspect_images([image], lambda _: data)
        if not checks[0].valid:
            raise CatalogError("Image is unavailable or invalid.")
        return data

    def display_image(self, target: LibraryTarget, check) -> bytes:
        """Read bytes for an image validated in the current browse result."""
        entry = self.target_entry(target)
        image = entry["content"]["guidance"]["images"][check.index]
        if not check.valid or check.sha256 != image["sha256"]:
            raise CatalogError("Image is unavailable or invalid.")
        return self._read_image(entry, image)

    def display_eligibility(self, target: LibraryTarget):
        entry = self.target_entry(target)
        checks = self._display_image_checks(entry)
        events = self.user.review_events(entry["id"]) if "id" in entry else []
        return assess_eligibility(
            entry["content"], entry["reference"]["sha256"], checks,
            events[-1] if events else None,
            removed=self.removal_state(target.exercise)["removed"],
        )

    def _require_eligible(self, target: LibraryTarget):
        status = self.eligibility(target)
        if not status.eligible:
            raise CatalogError("Content is not eligible: " + ", ".join(status.reasons))
        return status

    @contextmanager
    def _action(self):
        try:
            with transaction(self.user.connection, immediate=True):
                yield
        except Exception:
            with transaction(self.user.connection, immediate=True):
                self.assets.recover_unreferenced(self.user.asset_hashes())
            raise

    def _retain_target(self, target: LibraryTarget) -> int:
        entry = self.target_entry(target)
        if "id" in entry:
            return entry["id"]
        return self._retain_in_transaction(
            entry, "bundled", {"catalog_version": self.catalog.version},
            lambda image: self._read_image(entry, image),
        )

    def select_content(self, target: LibraryTarget, *, user_confirmed: bool) -> None:
        self.select_contents([target], user_confirmed=user_confirmed)

    def select_contents(self, targets: list[LibraryTarget], *, user_confirmed: bool) -> None:
        self._require_confirmation(targets, user_confirmed)
        if len({target.exercise for target in targets}) != len(targets):
            raise CatalogError("Select one content revision per exercise.")
        with self._action():
            for target in targets:
                self._require_eligible(target)
                identifier = self._retain_target(target)
                self.user.select(target.exercise, identifier)

    def set_enabled(self, target: LibraryTarget, enabled: bool, *, user_confirmed: bool) -> None:
        self.set_enabled_batch([target], enabled, user_confirmed=user_confirmed)

    def set_enabled_batch(self, targets: list[LibraryTarget], enabled: bool,
                          *, user_confirmed: bool) -> None:
        self._require_confirmation(targets, user_confirmed)
        if type(enabled) is not bool:
            raise CatalogError("Enablement must be Boolean.")
        with self._action():
            for target in targets:
                entry = self.target_entry(target)
                state = self.user.state(target.exercise)
                if "id" not in entry or state["selected_content_id"] != entry["id"]:
                    raise CatalogError("The selected content changed; refresh the target.")
                if enabled:
                    self._require_eligible(target)
                self.user.set_enabled(target.exercise, enabled)

    def require_for_activation(self, targets: list[LibraryTarget]) -> tuple[str, ...]:
        """D calls within its write transaction; returned names require unreviewed disclosure."""
        return self._require_training_targets(targets)

    def require_for_new_session(self, targets: list[LibraryTarget]) -> tuple[str, ...]:
        """E rechecks frozen plan targets in its session-creation transaction."""
        return self._require_training_targets(targets)

    def _require_training_targets(self, targets):
        if not targets:
            raise CatalogError("At least one training target is required.")
        unreviewed = []
        for target in targets:
            status = self._require_eligible(target)
            if not self.user.state(target.exercise)["enabled"]:
                raise CatalogError("Exercise is not enabled.")
            if not status.reviewed:
                name = self.target_entry(target)["content"]["canonical_name"]
                if name not in unreviewed:
                    unreviewed.append(name)
        return tuple(unreviewed)

    @staticmethod
    def _require_confirmation(targets, confirmed):
        if confirmed is not True:
            raise CatalogError("Explicit confirmation is required.")
        if not targets:
            raise CatalogError("Select at least one content revision.")
        keys = [(target.exercise, tuple(sorted(target.content.items()))) for target in targets]
        if len(set(keys)) != len(keys):
            raise CatalogError("Duplicate review targets are not allowed.")

    def record_review(self, targets: list[LibraryTarget], *, reviewer_type: str,
                      source: str, occurred_at: str, note: str, user_confirmed: bool,
                      answer_file: Path | None = None) -> None:
        self._require_confirmation(targets, user_confirmed)
        if reviewer_type not in {"external_ai_expert", "human_expert"}:
            raise CatalogError("A real external reviewer type is required.")
        if not isinstance(source, str) or not source.strip() or not isinstance(note, str):
            raise CatalogError("Review source and note must be text.")
        require_review_occurrence(occurred_at)
        attachment = None
        try:
            with self._action():
                for target in targets:
                    status = self._require_eligible(target)
                    # The actual reviewer must have inspected all supplied illustrations.
                    if any(not check.valid and check.reason != "missing"
                           for check in status.image_checks):
                        raise CatalogError("Repair unavailable illustrations before review.")
                    identifier = self._retain_target(target)
                    events = self.user.review_events(identifier)
                    if events and events[-1]["event_type"] == "approved":
                        raise CatalogError("Withdraw the prior review before recording another.")
                    if answer_file is not None and attachment is None:
                        managed_path(self.data_root, "reviews")
                        attachment = store_review_answer(self.data_root, answer_file)
                    self.user.append_review(identifier, {
                        "event_type": "approved", "content_sha256": target.content["sha256"],
                        "image_hashes": image_hashes(status.image_checks),
                        "reviewer_type": reviewer_type, "review_source": source,
                        "reviewed_at": occurred_at, "confirmed_at": self.clock.now().isoformat(),
                        "note": note, "attachment": None if attachment is None else {
                            "path": attachment.relative_path, "sha256": attachment.sha256,
                            "original_name": attachment.original_name,
                        },
                    })
        except Exception:
            if attachment is not None:
                attachment.remove_from(self.data_root)
            raise

    def withdraw_review(self, target: LibraryTarget, expected_event_id: int,
                        *, note: str, user_confirmed: bool) -> None:
        self._require_confirmation([target], user_confirmed)
        if not isinstance(note, str):
            raise CatalogError("Review note must be text.")
        with self._action():
            entry = self.target_entry(target)
            events = self.review_events(target)
            if not events or events[-1]["id"] != expected_event_id:
                raise CatalogError("The displayed review changed.")
            previous = events[-1]
            if previous["event_type"] != "approved":
                raise CatalogError("There is no current review to withdraw.")
            self.user.append_review(entry["id"], {
                **previous, "event_type": "withdrawn", "reviewer_type": "user",
                "review_source": "user_withdrawal", "reviewed_at": None,
                "confirmed_at": self.clock.now().isoformat(), "note": note, "attachment": None,
            })

    def attach_illustration(self, target: LibraryTarget, source: Path, caption: str) -> int:
        content = deepcopy(self.target_entry(target)["content"])
        data = Path(source).read_bytes()
        decode_image_size(data)
        digest = hashlib.sha256(data).hexdigest()
        path = managed_path(self.data_root, f"custom-exercise-images/{digest}.image")
        path.parent.mkdir(parents=True, exist_ok=True)
        created = not path.exists()
        if created:
            with path.open("xb") as stream:
                stream.write(data)
        content["guidance"]["images"] = [{"path": path.relative_to(self.data_root).as_posix(),
            "sha256": digest, "caption": caption, "required": True, "status": "available"}]
        try:
            return self.save_override(target.exercise, content, target.content)
        except Exception:
            if created:
                path.unlink(missing_ok=True)
            raise

    def _local_entry(self, content):
        entry = super()._local_entry(content)
        self._validate_family(entry["content"])
        self._validate_names(entry["content"])
        return entry

    def _retain_in_transaction(self, entry, origin, provenance, read_image):
        # Revalidate names and relationships after acquiring the SQLite writer lock.
        if origin != "bundled":
            self._validate_family(entry["content"])
            self._validate_names(entry["content"])
        return super()._retain_in_transaction(entry, origin, provenance, read_image)

    def _validate_names(self, content):
        requested = [normalize_name(name) for name in
                     (content["canonical_name"], *content["aliases"])]
        if len(set(requested)) != len(requested):
            raise CatalogError("Names and aliases must be distinct.")
        for row in self.list():
            if row["exercise"] == content["exercise"]:
                continue
            entry = row["local_contents"][-1] if row["local_contents"] else row["bundled"]
            other = entry["content"]
            if set(requested) & {normalize_name(name) for name in
                                 (other["canonical_name"], *other["aliases"])}:
                raise CatalogError("A name or alias belongs to another exercise.")

    def _validate_family(self, content):
        require_content_envelope(content)
        classification = content["classification"]
        families = {family["key"] for family in self.catalog.families()}
        if (classification["family_key"] is not None
                and classification["family_key"] not in families):
            raise CatalogError("Unknown exercise family.")
        reference = ExerciseReference(**content["exercise"])
        graph = {}
        for row in self.list():
            candidate = row["local_contents"][-1] if row["local_contents"] else row["bundled"]
            graph[ExerciseReference(**row["exercise"])] = candidate["content"]["classification"]
        graph[reference] = classification
        anchors = self.relationship_anchors()
        for child, relation in graph.items():
            seen = {child}
            parent = relation["parent_exercise_key"]
            while parent:
                parent_ref = ExerciseReference(**parent)
                if parent_ref in seen:
                    raise CatalogError("Exercise family parent links cannot form a cycle.")
                seen.add(parent_ref)
                if (parent_ref not in graph
                        and relation["family_key"] in anchors.get(parent_ref, set())):
                    # Retained child facts resolve the missing parent's stable identity/family;
                    # no missing parent guidance or further ancestry is invented.
                    break
                if (parent_ref not in graph
                        or graph[parent_ref]["family_key"] != relation["family_key"]):
                    raise CatalogError("Exercise parent must be in the same family.")
                parent = graph[parent_ref]["parent_exercise_key"]

    def relationship_anchors(self, *, include_bundled=True):
        anchors = {}
        for row in self.list():
            entries = list(row["local_contents"])
            if include_bundled and row["bundled"]:
                entries.append(row["bundled"])
            for entry in entries:
                relation = entry["content"]["classification"]
                if relation["parent_exercise_key"]:
                    reference = ExerciseReference(**relation["parent_exercise_key"])
                    anchors.setdefault(reference, set()).add(relation["family_key"])
        return anchors

    def parent_choices(self):
        rows = [{"exercise": row["exercise"], "name": row["display"]["content"]["canonical_name"],
                 "missing": False} for row in self.browse()]
        known = {ExerciseReference(**row["exercise"]) for row in rows}
        for reference in self.relationship_anchors():
            if reference not in known:
                rows.append({"exercise": {"source": reference.source.value, "key": reference.key},
                             "name": reference.key, "missing": True})
        return rows

    def browse(self, query: str = "", position: str | None = None,
               *, latest: bool = False, for_display: bool = False,
               defer_checks: bool = False) -> list[dict]:
        rows = []
        for exercise in self.list():
            current = (
                exercise["local_contents"][-1]
                if exercise["local_contents"] else exercise["bundled"]
            )
            entry = current if latest else exercise["selected"] or current
            content = entry["content"]
            if position and content["classification"]["starting_position_class"] != position:
                continue
            if normalize_name(query) not in normalize_name(
                " ".join([content["canonical_name"], *content["aliases"]])
            ):
                continue
            target = LibraryTarget(ExerciseReference(**exercise["exercise"]), entry["reference"])
            if defer_checks:
                eligibility = None
            elif for_display:
                eligibility = self.display_eligibility(target)
            else:
                eligibility = self.eligibility(target)
            rows.append({**exercise, "display": entry, "target": target,
                         "eligibility": eligibility})
        return sorted(rows, key=lambda row: (
            row["display"]["content"]["classification"]["family_key"] or "~",
            row["display"]["content"]["classification"]["variant_order"],
            row["display"]["content"]["canonical_name"],
        ))

    def compare_base(self, target: LibraryTarget) -> tuple[dict | None, dict]:
        entry = self.target_entry(target)
        family_key = entry["content"]["classification"]["family_key"]
        family = next((f for f in self.catalog.families() if f["key"] == family_key), None)
        base = self.catalog.get(family["base_key"]) if family and family["base_key"] else None
        return base, entry
