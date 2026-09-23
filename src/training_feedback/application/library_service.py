"""Compose read-only catalog content with one root's local drafts and retained evidence."""

from __future__ import annotations

import uuid
from copy import deepcopy

from ..data.catalog_resources import CatalogError, checked_bytes
from ..data.database import transaction
from ..domain.catalog import (
    ExerciseReference,
    ExerciseSource,
    content_sha256,
    require_content_envelope,
)
from ..domain.clock import SystemClock
from ..domain.exercises import normalize_name


class LibraryService:
    def __init__(self, catalog, user, assets, data_root, clock=None):
        self.catalog = catalog
        self.user = user
        self.assets = assets
        self.data_root = data_root
        self.clock = clock or SystemClock()

    def get(self, reference: ExerciseReference) -> dict | None:
        bundled = (
            self.catalog.get(reference.key) if reference.source == ExerciseSource.BUNDLED else None
        )
        drafts = self.user.contents(reference)
        if bundled is None and not drafts:
            return None
        state = self.user.state(reference)
        selected = self.user.content(state["selected_content_id"])
        return {"exercise": {"source": reference.source.value, "key": reference.key},
                "bundled": bundled, "local_contents": drafts, "selected": selected,
                "enabled": bool(state["enabled"]), "catalog_version": self.catalog.version}

    def list(self) -> list[dict]:
        references = {
            ExerciseReference(**row["content"]["exercise"]) for row in self.catalog.list()
        }
        references.update(self.user.references())
        return [row for reference in sorted(
            references, key=lambda reference: (reference.source, reference.key)
        ) if (row := self.get(reference)) is not None]

    def removal_state(self, reference: ExerciseReference) -> dict:
        local = self.user.disposition(reference)
        publisher = None
        if reference.source == ExerciseSource.BUNDLED:
            bundled = self.catalog.get(reference.key)
            publisher = ("missing" if bundled is None else
                         ("withdrawn" if bundled["withdrawn"] else "available"))
        return {"local": local, "publisher": publisher,
                "removed": bool(local and local["disposition"] == "removed")
                or publisher in {"missing", "withdrawn"}}

    def resolve(self, reference: ExerciseReference, name: str, content_reference: dict) -> dict:
        if self.removal_state(reference)["removed"]:
            raise CatalogError("Exercise is removed or withdrawn; edit the plan explicitly.")
        exercise = self.get(reference)
        if exercise is None:
            raise CatalogError("Unknown exercise identity.")
        candidates = [*exercise["local_contents"]]
        if exercise["bundled"]:
            if exercise["bundled"]["withdrawn"]:
                raise CatalogError("Exercise was withdrawn from the catalog.")
            candidates.append(exercise["bundled"])
        for entry in candidates:
            if entry["reference"] == content_reference:
                content = entry["content"]
                if normalize_name(name) not in {
                    normalize_name(value)
                    for value in (content["canonical_name"], *content["aliases"])
                }:
                    raise CatalogError("Exercise key and name conflict.")
                return entry
        raise CatalogError("Exact exercise content was not found.")

    def retain_bundled(self, reference: ExerciseReference, expected: dict) -> int:
        if reference.source != ExerciseSource.BUNDLED:
            raise CatalogError("Expected bundled content.")
        entry = self.catalog.get(reference.key)
        if entry is None or entry["reference"] != expected:
            raise CatalogError("The catalog content changed; refresh the displayed target.")
        if entry["withdrawn"]:
            raise CatalogError("Exercise was withdrawn from the catalog.")
        return self._retain(entry, "bundled", {"catalog_version": self.catalog.version},
                            self.catalog.image_bytes)

    def save_override(self, reference: ExerciseReference, content: dict, expected: dict) -> int:
        exercise = self.get(reference)
        if exercise is None:
            raise CatalogError("Unknown exercise identity.")
        candidates = [*exercise["local_contents"]]
        if exercise["bundled"]:
            candidates.append(exercise["bundled"])
        target = next((entry for entry in candidates if entry["reference"] == expected), None)
        if target is None:
            raise CatalogError("The displayed content changed.")
        if content["exercise"] != {"source": reference.source.value, "key": reference.key}:
            raise CatalogError("An override cannot change exercise identity.")
        entry = self._local_entry(content)

        def read_image(image):
            if image["path"].startswith("custom-exercise-images/"):
                return checked_bytes(self.data_root, image["path"], image["sha256"])
            if not any(
                (previous.get("path"), previous.get("sha256")) == (image["path"], image["sha256"])
                for previous in target["content"]["guidance"]["images"]
            ):
                raise CatalogError("Override images must be originals or managed local images.")
            if target is exercise["bundled"]:
                return self.catalog.image_bytes(image)
            return self.assets.read(target["assets"][image["path"]])

        return self._retain(entry, "override", {"based_on": target["reference"]}, read_image)

    def copy_to_custom(self, reference: ExerciseReference, expected: dict, name: str) -> int:
        exercise = self.get(reference)
        if exercise is None:
            raise CatalogError("Unknown exercise identity.")
        entries = [*exercise["local_contents"]]
        if exercise["bundled"]:
            entries.append(exercise["bundled"])
        source = next((entry for entry in entries if entry["reference"] == expected), None)
        if source is None:
            raise CatalogError("The displayed content changed.")
        content = deepcopy(source["content"])
        content["exercise"] = {"source": "custom", "key": uuid.uuid4().hex}
        content["canonical_name"] = name
        content["aliases"] = []
        entry = self._local_entry(content)
        read_image = self.catalog.image_bytes if source is exercise["bundled"] else (
            lambda image: self.assets.read(source["assets"][image["path"]])
        )
        return self._retain(entry, "custom", {"copied_from": source["reference"]}, read_image)

    def _local_entry(self, content: dict) -> dict:
        content = deepcopy(content)
        ExerciseReference(**content["exercise"])
        if not isinstance(content["canonical_name"], str) or not content["canonical_name"].strip():
            raise CatalogError("Custom content requires a name.")
        content["guidance"].pop("review", None)
        require_content_envelope(content)
        return {"reference": {"id": f"user.{uuid.uuid4().hex}", "version": 1,
                              "sha256": content_sha256(content)}, "content": content}

    def create_custom(self, content: dict) -> int:
        content = deepcopy(content)
        content["exercise"] = {"source": "custom", "key": uuid.uuid4().hex}

        def read_image(image):
            if not image["path"].startswith("custom-exercise-images/"):
                raise CatalogError("New custom images require a managed custom-image path.")
            return checked_bytes(self.data_root, image["path"], image["sha256"])

        return self._retain(self._local_entry(content), "custom", {}, read_image)

    def _retain(self, entry, origin, provenance, read_image):
        connection = self.user.connection
        try:
            with transaction(connection, immediate=True):
                return self._retain_in_transaction(entry, origin, provenance, read_image)
        except Exception:
            # A crash leaves unreferenced bytes only; reopen performs the same cleanup.
            with transaction(connection, immediate=True):
                self.assets.recover_unreferenced(self.user.asset_hashes())
            raise

    def _retain_in_transaction(self, entry, origin, provenance, read_image):
        resources = {}
        for image in entry["content"]["guidance"]["images"]:
            if image["status"] == "available":
                try:
                    data = read_image(image)
                except (OSError, ValueError, KeyError):
                    if image["required"]:
                        raise
                    continue
                self.assets.publish(data, image["sha256"])
                resources[image["path"]] = (image["sha256"], len(data))
        return self.user.retain(entry, origin, provenance, resources,
                                self.clock.now().isoformat())
