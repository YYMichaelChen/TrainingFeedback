"""Reviewed removal/restoration with transaction-bound content and impact checks."""

from copy import deepcopy

from ..domain.catalog import ExerciseReference, content_sha256
from ..domain.exercises import require_review_occurrence
from ..domain.library_lifecycle import TRANSITIONS, require_transition
from .library_workflow import LibraryTarget


class LibraryLifecycleService:
    def __init__(self, library, repository):
        self.library, self.repository = library, repository

    def get(self, identifier):
        return self.repository.get(identifier)

    def requests(self):
        return self.repository.requests()

    def publisher_events(self, reference=None):
        return self.repository.publisher_events(reference)

    def available_actions(self, request):
        return TRANSITIONS[request["status"]]

    def sync_publisher(self):
        """Observe package state; the observation is not an invented publisher decision time."""
        library = self.library
        with library._action():
            references = {ref for ref in library.user.references() if ref.source == "bundled"}
            references.update(ref for ref in library.relationship_anchors(include_bundled=False)
                              if ref.source == "bundled")
            references.update(ExerciseReference(**entry["content"]["exercise"])
                              for entry in library.catalog.list() if entry["withdrawn"])
            manifest_hash = content_sha256(library.catalog.manifest)
            now = library.clock.now().isoformat()
            for reference in sorted(references, key=lambda ref: ref.key):
                entry = library.catalog.get(reference.key)
                disposition = library.removal_state(reference)["publisher"]
                content = entry["reference"] if entry else None
                previous = self.repository.publisher_events(reference)
                if previous and (
                    previous[-1]["disposition"], previous[-1]["content_reference"]
                ) == (disposition, content):
                    continue
                reference_id = library.user.reference_id(reference, now)
                event_id = self.repository.observe_publisher(
                    reference_id, library.catalog.version, manifest_hash, disposition, content, now,
                )
                if disposition != "available":
                    library.user.set_enabled(reference, False)
                    self.repository.invalidate_plans(reference_id, event_id, publisher=True)

    def _content_state(self, target):
        row = self.library.get(target.exercise)
        entry = self.library.target_entry(target)
        return {"exercise": deepcopy(entry["content"]["exercise"]),
                "content": deepcopy(entry["reference"]),
                "name": entry["content"]["canonical_name"],
                "catalog_content": row["bundled"]["reference"] if row["bundled"] else None,
                "local_revisions": [value["reference"] for value in row["local_contents"]
                                    if value["origin"] != "bundled"],
                "selected": row["selected"]["reference"] if row["selected"] else None,
                "removal": self.library.removal_state(target.exercise)}

    def _variants(self, exercise):
        variants = []
        seen = set()
        for row in self.library.list():
            for entry in [*row["local_contents"], *([row["bundled"]] if row["bundled"] else [])]:
                content = entry["content"]
                if content["classification"]["parent_exercise_key"] != exercise:
                    continue
                identity = (row["exercise"]["source"], row["exercise"]["key"],
                            entry["reference"]["sha256"])
                if identity not in seen:
                    seen.add(identity)
                    variants.append({"exercise": row["exercise"], "content": entry["reference"],
                                     "name": content["canonical_name"]})
        return variants

    def preview(self, targets, operation="remove"):
        self.library._require_confirmation(targets, True)
        if operation not in {"remove", "restore"}:
            raise ValueError("Unknown lifecycle operation.")
        if len({target.exercise for target in targets}) != len(targets):
            raise ValueError("Select one content revision per exercise.")
        states, impacts = [], []
        for target in targets:
            state = self._content_state(target)
            local_removed = bool(state["removal"]["local"] and
                                 state["removal"]["local"]["disposition"] == "removed")
            if local_removed != (operation == "restore"):
                raise ValueError("The local removal state does not match this operation.")
            if operation == "restore":
                if state["removal"]["publisher"] in {"withdrawn", "missing"}:
                    raise ValueError("Publisher withdrawal cannot be restored by a local decision.")
                status = self.library.content_eligibility(target)
                if not status.eligible or any(
                    not check.valid and check.reason != "missing" for check in status.image_checks
                ):
                    raise ValueError("Repair current content and images before restoration.")
            states.append(state)
            impacts.append({"exercise": state["exercise"],
                            **self.repository.impacts(state["exercise"]),
                            "variants": self._variants(state["exercise"]),
                            "enabled": bool(self.library.user.state(target.exercise)["enabled"])})
        value = {"operation": operation, "targets": states, "impacts": impacts}
        return {**value, "token": content_sha256(value)}

    @staticmethod
    def _targets(preview):
        return [LibraryTarget(ExerciseReference(**row["exercise"]), row["content"])
                for row in preview["targets"]]

    @staticmethod
    def _decision(source, occurred_at, note, confirmed):
        if confirmed is not True:
            raise ValueError("Explicit confirmation is required.")
        if not isinstance(source, str) or not source.strip() or not isinstance(note, str):
            raise ValueError("A decision source and a text note are required.")
        require_review_occurrence(occurred_at)

    def request(self, targets, *, operation="remove", reason, expected_preview, user_confirmed):
        self.library._require_confirmation(targets, user_confirmed)
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("A lifecycle reason is required.")
        with self.library._action():
            preview = self.preview(targets, operation)
            self._check_token(preview, expected_preview)
            for request in self.requests():
                if request["status"] not in {"requested", "under_review", "approved"}:
                    continue
                if {target.exercise for target in targets} & {
                    target.exercise for target in self._targets(request["preview"])
                }:
                    raise ValueError(
                        "An unfinished lifecycle request already exists for this exercise."
                    )
            now = self.library.clock.now().isoformat()
            identifier = self.repository.create(operation, reason, preview, now)
            self.repository.append(identifier, "requested", "user", now, reason, preview, now)
            return identifier

    @staticmethod
    def _check_token(preview, expected):
        if preview["token"] != expected:
            raise ValueError("The removal impact changed. Refresh and review it again.")

    def preview_request(self, identifier):
        request = self.get(identifier)
        preview = self.preview(self._targets(request["preview"]), request["operation"])
        if preview["targets"] != request["preview"]["targets"]:
            raise ValueError("The lifecycle content changed. Cancel and submit a new request.")
        return preview

    def transition(self, identifier, kind, *, expected_event_id, source, occurred_at, note,
                   user_confirmed, expected_preview=None, apply=False):
        self._decision(source, occurred_at, note, user_confirmed)
        if apply and kind != "approved":
            raise ValueError("This lifecycle transition is not allowed.")
        with self.library._action():
            request = self.get(identifier)
            last = request["events"][-1]
            if last["id"] != expected_event_id:
                raise ValueError("The lifecycle request changed. Reload its history.")
            require_transition(request["status"], kind)
            preview = last["preview"]
            if kind not in {"cancelled", "rejected"}:
                preview = self.preview_request(identifier)
                self._check_token(preview, expected_preview)
                if kind in {"approved", "applied"}:
                    self._check_token(preview, last["preview"]["token"])
            now = self.library.clock.now().isoformat()
            event_id = self.repository.append(
                identifier, kind, source, occurred_at, note, preview, now,
            )
            if apply:
                event_id = self.repository.append(
                    identifier, "applied", source, occurred_at, note, preview, now,
                )
            if kind == "applied" or apply:
                self._apply(request["operation"], preview, event_id, now)
        return self.get(identifier)

    def _apply(self, operation, preview, event_id, now):
        library = self.library
        for target in self._targets(preview):
            entry = library.target_entry(target)
            if "id" not in entry:
                resources = {}
                # Removal must also work for unfinished or broken-image drafts. Keep every
                # readable declared resource; earlier immutable bindings are never altered.
                for image in entry["content"]["guidance"]["images"]:
                    if image["status"] != "available":
                        continue
                    try:
                        data = library._read_image(entry, image)
                    except (OSError, ValueError, KeyError):
                        continue
                    library.assets.publish(data, image["sha256"])
                    resources[image["path"]] = (image["sha256"], len(data))
                library.user.retain(entry, "bundled", {"catalog_version": library.catalog.version},
                                    resources, now)
            reference_id = library.user.reference_id(target.exercise, now)
            self.repository.tombstone(
                reference_id, "removed" if operation == "remove" else "restored", event_id,
            )
            library.user.set_enabled(target.exercise, False)
            if operation == "remove":
                self.repository.invalidate_plans(reference_id, event_id)
