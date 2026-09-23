"""User-root references, overrides and immutable evidence; never writes the catalog."""

from __future__ import annotations

import json

from ..domain.catalog import ExerciseReference, content_sha256, require_content_envelope
from .catalog_resources import CatalogError


class LibraryRepository:
    def __init__(self, connection):
        self.connection = connection

    def reference_id(self, reference: ExerciseReference, now: str) -> int:
        self.connection.execute(
            "INSERT INTO library_reference(source, stable_key, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(source,stable_key) DO NOTHING", (reference.source, reference.key, now),
        )
        identifier = self.connection.execute(
            "SELECT id FROM library_reference WHERE source=? AND stable_key=?",
            (reference.source, reference.key),
        ).fetchone()[0]
        self.connection.execute(
            "INSERT INTO library_state(reference_id) VALUES (?) ON CONFLICT DO NOTHING",
            (identifier,),
        )
        return identifier

    def references(self) -> list[ExerciseReference]:
        return [ExerciseReference(row["source"], row["stable_key"])
                for row in self.connection.execute("SELECT * FROM library_reference ORDER BY id")]

    def state(self, reference: ExerciseReference) -> dict:
        row = self.connection.execute(
            "SELECT s.* FROM library_state s JOIN library_reference r ON r.id=s.reference_id "
            "WHERE r.source=? AND r.stable_key=?", (reference.source, reference.key),
        ).fetchone()
        return dict(row) if row else {"selected_content_id": None, "enabled": False}

    def disposition(self, reference: ExerciseReference) -> dict | None:
        row = self.connection.execute(
            "SELECT t.disposition,t.event_id FROM library_tombstone t "
            "JOIN library_reference r ON r.id=t.reference_id WHERE r.source=? AND r.stable_key=?",
            (reference.source, reference.key),
        ).fetchone()
        return dict(row) if row else None

    def plan_invalidated(self, revision_id):
        return self.connection.execute(
            "SELECT 1 FROM library_plan_invalidation WHERE revision_id=?", (revision_id,),
        ).fetchone() is not None

    def contents(self, reference: ExerciseReference) -> list[dict]:
        entries = [self.content(row[0]) for row in self.connection.execute(
            "SELECT c.id FROM library_content c JOIN library_reference r ON r.id=c.reference_id "
            "WHERE r.source=? AND r.stable_key=? ORDER BY c.id", (reference.source, reference.key),
        )]
        return [entry for entry in entries if entry["provenance"].get("kind") != "stored_session"]

    def content(self, identifier: int) -> dict | None:
        row = self.connection.execute(
            "SELECT c.*, s.content_json FROM library_content c "
            "JOIN content_snapshot s ON s.sha256=c.snapshot_sha256 WHERE c.id=?", (identifier,),
        ).fetchone()
        if row is None:
            return None
        content = json.loads(row["content_json"])
        if content_sha256(content) != row["snapshot_sha256"]:
            raise CatalogError("Retained content hash does not match.")
        assets = {
            asset["original_path"]: asset["asset_sha256"]
            for asset in self.connection.execute(
                "SELECT * FROM content_snapshot_asset WHERE snapshot_sha256=?",
                (row["snapshot_sha256"],),
            )
        }
        return {"id": row["id"], "content": content,
                "reference": {"id": row["content_id"], "version": row["version"],
                              "sha256": row["snapshot_sha256"]},
                "origin": row["origin"], "provenance": json.loads(row["provenance_json"]),
                "assets": assets}

    def retain(self, entry: dict, origin: str, provenance: dict, assets: dict, now: str) -> int:
        content = entry["content"]
        require_content_envelope(content)
        reference = ExerciseReference(**content["exercise"])
        reference_id = self.reference_id(reference, now)
        digest = content_sha256(content)
        if digest != entry["reference"]["sha256"]:
            raise CatalogError("Content identity does not match its bytes.")
        self.connection.execute(
            "INSERT INTO content_snapshot VALUES (?, ?) ON CONFLICT DO NOTHING",
            (digest, json.dumps(
                content, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            )),
        )
        for path, (asset_hash, byte_count) in assets.items():
            self.connection.execute(
                "INSERT INTO snapshot_asset VALUES (?, ?) ON CONFLICT DO NOTHING",
                (asset_hash, byte_count),
            )
            self.connection.execute(
                "INSERT INTO content_snapshot_asset VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                (digest, path, asset_hash),
            )
        identity = entry["reference"]
        existing = self.connection.execute(
            "SELECT id,snapshot_sha256 FROM library_content "
            "WHERE reference_id=? AND content_id=? AND version=?",
            (reference_id, identity["id"], identity["version"]),
        ).fetchone()
        if existing:
            if existing["snapshot_sha256"] != digest:
                raise CatalogError("Existing content identity has different bytes.")
            return existing["id"]
        cursor = self.connection.execute(
            "INSERT INTO library_content(reference_id,content_id,version,snapshot_sha256,origin,"
            "provenance_json,created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (reference_id, identity["id"], identity["version"], digest, origin,
             json.dumps(provenance, ensure_ascii=False), now),
        )
        return cursor.lastrowid

    def asset_hashes(self) -> set[str]:
        return {row[0] for row in self.connection.execute("SELECT sha256 FROM snapshot_asset")}

    def select(self, reference: ExerciseReference, content_id: int) -> None:
        self.connection.execute(
            "UPDATE library_state SET selected_content_id=? WHERE reference_id="
            "(SELECT id FROM library_reference WHERE source=? AND stable_key=?)",
            (content_id, reference.source, reference.key),
        )

    def set_enabled(self, reference: ExerciseReference, enabled: bool) -> None:
        cursor = self.connection.execute(
            "UPDATE library_state SET enabled=? WHERE reference_id="
            "(SELECT id FROM library_reference WHERE source=? AND stable_key=?)",
            (int(enabled), reference.source, reference.key),
        )
        if cursor.rowcount != 1:
            raise CatalogError("Select a content revision before enabling.")

    def review_events(self, content_id: int) -> list[dict]:
        result = []
        for row in self.connection.execute(
            "SELECT * FROM library_review_event WHERE content_id=? ORDER BY id", (content_id,),
        ):
            event = dict(row)
            event["image_hashes"] = json.loads(event.pop("image_hashes_json"))
            event["attachment"] = json.loads(event.pop("attachment_json") or "null")
            result.append(event)
        return result

    def append_review(self, content_id: int, event: dict) -> int:
        cursor = self.connection.execute(
            "INSERT INTO library_review_event(content_id,event_type,content_sha256,"
            "image_hashes_json,"
            "reviewer_type,review_source,reviewed_at,confirmed_at,note,attachment_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (content_id, event["event_type"], event["content_sha256"],
             json.dumps(event["image_hashes"]), event["reviewer_type"], event["review_source"],
             event["reviewed_at"], event["confirmed_at"], event["note"],
             json.dumps(event.get("attachment"), ensure_ascii=False)),
        )
        return cursor.lastrowid
