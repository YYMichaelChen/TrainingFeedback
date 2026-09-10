"""动作目录的 SQLite 仓储：动作、别名、身体部位与动作指导版本。"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from ..domain.exercises import (
    GuidanceStatus,
    can_activate_guidance,
    guidance_to_json,
    normalize_name,
    review_status,
    validate_guidance,
)
from .database import transaction as sqlite_transaction


class ExerciseRepository:
    """动作目录仓储。写方法不自带事务，由应用服务编排事务边界。"""
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def transaction(self, immediate: bool = False):
        with sqlite_transaction(self.connection, immediate):
            yield self.connection

    def list(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM exercise"
        if not include_inactive:
            query += " WHERE active = 1"
        query += " ORDER BY canonical_name"
        return [self._summary(dict(row)) for row in self.connection.execute(query)]

    def search(self, query: str, include_inactive: bool = False) -> list[dict[str, Any]]:
        # 转义 LIKE 通配符，避免用户输入的 % 和 _ 被当作模式匹配符。
        escaped = (
            normalize_name(query)
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        key = f"%{escaped}%"
        active_clause = "" if include_inactive else " AND e.active = 1"
        rows = self.connection.execute(
            "SELECT DISTINCT e.* FROM exercise e LEFT JOIN exercise_alias a "
            "ON a.exercise_id = e.id LEFT JOIN exercise_body_area eba "
            "ON eba.exercise_id = e.id LEFT JOIN body_area b ON b.id = eba.body_area_id "
            "WHERE (lower(e.canonical_name) LIKE ? ESCAPE '\\' "
            "OR lower(a.alias) LIKE ? ESCAPE '\\' "
            "OR lower(e.category) LIKE ? ESCAPE '\\' "
            "OR lower(b.name) LIKE ? ESCAPE '\\')"
            + active_clause
            + " ORDER BY e.canonical_name",
            (key, key, key, key),
        )
        return [self._summary(dict(row)) for row in rows]

    def _summary(self, exercise: dict[str, Any]) -> dict[str, Any]:
        exercise_id = exercise["id"]
        exercise["aliases"] = [
            row[0]
            for row in self.connection.execute(
                "SELECT alias FROM exercise_alias WHERE exercise_id = ? ORDER BY alias",
                (exercise_id,),
            )
        ]
        exercise["primary_areas"] = [
            row[0]
            for row in self.connection.execute(
                "SELECT b.name FROM body_area b JOIN exercise_body_area eba "
                "ON eba.body_area_id = b.id WHERE eba.exercise_id = ? "
                "AND eba.is_primary = 1 ORDER BY b.name",
                (exercise_id,),
            )
        ]
        latest = (
            self.connection.execute(
                "SELECT guidance_json FROM exercise_guidance_revision WHERE id = ?",
                (exercise.get("active_guidance_revision_id"),),
            ).fetchone()
            if exercise.get("active_guidance_revision_id")
            else None
        )
        if latest is None:
            exercise["guidance_status"] = "missing"
            exercise["guidance_complete"] = False
        else:
            guidance = json.loads(latest[0])
            exercise["guidance_status"] = review_status(guidance).value
            exercise["guidance_complete"] = validate_guidance(guidance).complete
        return exercise

    def get(self, exercise_id: int) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM exercise WHERE id = ?", (exercise_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["aliases"] = [
            r[0]
            for r in self.connection.execute(
                "SELECT alias FROM exercise_alias WHERE exercise_id = ? ORDER BY alias",
                (exercise_id,),
            )
        ]
        result["body_areas"] = [
            dict(r)
            for r in self.connection.execute(
                "SELECT b.name, eba.is_primary FROM body_area b "
                "JOIN exercise_body_area eba ON eba.body_area_id = b.id WHERE eba.exercise_id = ?",
                (exercise_id,),
            )
        ]
        result["guidance"] = [
            {**dict(r), "guidance": json.loads(r["guidance_json"])}
            for r in self.connection.execute(
                "SELECT * FROM exercise_guidance_revision "
                "WHERE exercise_id = ? ORDER BY revision_number",
                (exercise_id,),
            )
        ]
        return result

    def get_by_canonical_name(self, name: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM exercise WHERE canonical_name = ? COLLATE NOCASE",
            (name.strip(),),
        ).fetchone()
        return dict(row) if row is not None else None

    def get_by_bundled_key(self, key: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM exercise WHERE bundled_exercise_key = ?", (key,)
        ).fetchone()
        return dict(row) if row is not None else None

    def find_identity_matches(self, names: list[str]) -> list[dict[str, Any]]:
        """Return every exercise whose canonical name or alias matches a bundled name."""
        keys = {normalize_name(name) for name in names if normalize_name(name)}
        matches = []
        for row in self.connection.execute("SELECT * FROM exercise ORDER BY id"):
            aliases = [
                alias[0]
                for alias in self.connection.execute(
                    "SELECT alias FROM exercise_alias WHERE exercise_id = ? ORDER BY id",
                    (row["id"],),
                )
            ]
            if any(
                normalize_name(name) in keys
                for name in (row["canonical_name"], *aliases)
            ):
                matches.append(dict(row))
        return matches

    @staticmethod
    def _distinct_names(values: list[str], kind: str) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            stored = value.strip()
            key = normalize_name(value)
            if not key:
                raise ValueError(f"{kind} cannot be empty.")
            if key in seen:
                raise ValueError(f"Duplicate {kind.lower()} values are not allowed.")
            seen.add(key)
            result.append(stored)
        return result

    def validate_identity(
        self, exercise_id: int | None, name: str, aliases: list[str]
    ) -> tuple[str, list[str]]:
        """Validate the final canonical-name/alias set using domain normalization rules."""
        canonical_name = name.strip()
        canonical_key = normalize_name(name)
        if not canonical_key:
            raise ValueError("Canonical name cannot be empty.")
        final_aliases = self._distinct_names(aliases, "Alias")
        requested_keys = [canonical_key, *(normalize_name(alias) for alias in final_aliases)]
        if len(requested_keys) != len(set(requested_keys)):
            raise ValueError("The canonical name and aliases must be distinct.")
        if exercise_id is not None:
            exists = self.connection.execute(
                "SELECT 1 FROM exercise WHERE id = ?", (exercise_id,)
            ).fetchone()
            if exists is None:
                raise ValueError("Exercise was not found.")
        requested = set(requested_keys)
        for row in self.connection.execute("SELECT id, canonical_name FROM exercise"):
            if row["id"] != exercise_id and normalize_name(row["canonical_name"]) in requested:
                raise ValueError("The canonical name or alias is already in use.")
        for row in self.connection.execute("SELECT exercise_id, alias FROM exercise_alias"):
            if row["exercise_id"] != exercise_id and normalize_name(row["alias"]) in requested:
                raise ValueError("The canonical name or alias is already in use.")
        return canonical_name, final_aliases

    def resolve(self, name: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM exercise WHERE canonical_name = ? COLLATE NOCASE",
            (name.strip(),),
        ).fetchone()
        if row is None:
            row = self.connection.execute(
                "SELECT e.* FROM exercise e JOIN exercise_alias a ON a.exercise_id = e.id "
                "WHERE a.alias = ? COLLATE NOCASE",
                (name.strip(),),
            ).fetchone()
        if row is None or not row["active"]:
            return None
        return dict(row)

    def create(
        self,
        name: str,
        category: str,
        equipment: str,
        body_areas: list[tuple[str, bool]],
        *,
        bundled_exercise_key: str | None = None,
    ) -> int:
        name, _ = self.validate_identity(None, name, [])
        prepared_areas: list[tuple[str, bool]] = []
        seen_areas: set[str] = set()
        for area, primary in body_areas:
            stored_area = area.strip()
            key = normalize_name(area)
            if not key:
                raise ValueError("Body area cannot be empty.")
            if key in seen_areas:
                raise ValueError("Duplicate body area values are not allowed.")
            seen_areas.add(key)
            prepared_areas.append((stored_area, primary))
        now = datetime.now(UTC).isoformat()
        cursor = self.connection.execute(
            "INSERT INTO exercise(canonical_name, category, equipment_summary, "
            "created_at, updated_at, bundled_exercise_key) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, category, equipment, now, now, bundled_exercise_key),
        )
        for area, primary in prepared_areas:
            area_id = self._body_area_id(area)
            self.connection.execute(
                "INSERT INTO exercise_body_area(exercise_id, body_area_id, is_primary) "
                "VALUES (?, ?, ?)",
                (cursor.lastrowid, area_id, int(primary)),
            )
        return cursor.lastrowid

    def update_metadata(self, exercise_id: int, name: str, category: str, equipment: str) -> None:
        current_aliases = [
            row[0]
            for row in self.connection.execute(
                "SELECT alias FROM exercise_alias WHERE exercise_id = ? ORDER BY id",
                (exercise_id,),
            )
        ]
        name, _ = self.validate_identity(exercise_id, name, current_aliases)
        cursor = self.connection.execute(
            "UPDATE exercise SET canonical_name = ?, category = ?, equipment_summary = ?, "
            "updated_at = ? WHERE id = ?",
            (name, category, equipment, datetime.now(UTC).isoformat(), exercise_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Exercise was not found.")

    def add_alias(self, exercise_id: int, alias: str) -> None:
        exercise = self.connection.execute(
            "SELECT canonical_name FROM exercise WHERE id = ?", (exercise_id,)
        ).fetchone()
        if exercise is None:
            raise ValueError("Exercise was not found.")
        current_aliases = [
            row[0]
            for row in self.connection.execute(
                "SELECT alias FROM exercise_alias WHERE exercise_id = ? ORDER BY id",
                (exercise_id,),
            )
        ]
        _, aliases = self.validate_identity(
            exercise_id, exercise["canonical_name"], [*current_aliases, alias]
        )
        self.connection.execute(
            "INSERT INTO exercise_alias(exercise_id, alias) VALUES (?, ?)",
            (exercise_id, aliases[-1]),
        )

    def replace_aliases(
        self, exercise_id: int, aliases: list[str], canonical_name: str | None = None
    ) -> None:
        exercise = self.connection.execute(
            "SELECT canonical_name FROM exercise WHERE id = ?", (exercise_id,)
        ).fetchone()
        if exercise is None:
            raise ValueError("Exercise was not found.")
        _, final_aliases = self.validate_identity(
            exercise_id, canonical_name or exercise["canonical_name"], aliases
        )
        self.connection.execute("DELETE FROM exercise_alias WHERE exercise_id = ?", (exercise_id,))
        self.connection.executemany(
            "INSERT INTO exercise_alias(exercise_id, alias) VALUES (?, ?)",
            [(exercise_id, alias) for alias in final_aliases],
        )

    def replace_primary_body_areas(self, exercise_id: int, primary_areas: list[str]) -> None:
        exists = self.connection.execute(
            "SELECT 1 FROM exercise WHERE id = ?", (exercise_id,)
        ).fetchone()
        if exists is None:
            raise ValueError("Exercise was not found.")
        final_areas = self._distinct_names(primary_areas, "Body area")
        area_ids = [self._body_area_id(area) for area in final_areas]
        self.connection.execute(
            "DELETE FROM exercise_body_area WHERE exercise_id = ? AND is_primary = 1",
            (exercise_id,),
        )
        for area_id in area_ids:
            self.connection.execute(
                "INSERT INTO exercise_body_area(exercise_id, body_area_id, is_primary) "
                "VALUES (?, ?, 1) ON CONFLICT(exercise_id, body_area_id) "
                "DO UPDATE SET is_primary = 1",
                (exercise_id, area_id),
            )

    def _body_area_id(self, name: str) -> int:
        key = normalize_name(name)
        for row in self.connection.execute("SELECT id, name FROM body_area"):
            if normalize_name(row["name"]) == key:
                return row["id"]
        cursor = self.connection.execute("INSERT INTO body_area(name) VALUES (?)", (name,))
        return cursor.lastrowid

    def set_active(self, exercise_id: int, active: bool) -> None:
        cursor = self.connection.execute(
            "UPDATE exercise SET active = ?, updated_at = ? WHERE id = ?",
            (int(active), datetime.now(UTC).isoformat(), exercise_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Exercise was not found.")

    def set_bundled_exercise_key(self, exercise_id: int, key: str) -> None:
        row = self.connection.execute(
            "SELECT bundled_exercise_key FROM exercise WHERE id = ?", (exercise_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Exercise was not found.")
        current = row["bundled_exercise_key"]
        if current == key:
            return
        if current is not None:
            raise ValueError("Exercise is already linked to different bundled content.")
        existing = self.get_by_bundled_key(key)
        if existing is not None and existing["id"] != exercise_id:
            raise ValueError("Bundled exercise is already linked to another exercise.")
        self.connection.execute(
            "UPDATE exercise SET bundled_exercise_key = ? WHERE id = ?",
            (key, exercise_id),
        )

    def has_bundled_guidance(
        self, exercise_id: int, content_id: str, content_version: int
    ) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM exercise_guidance_revision "
                "WHERE exercise_id = ? AND bundled_content_id = ? "
                "AND bundled_content_version = ?",
                (exercise_id, content_id, content_version),
            ).fetchone()
            is not None
        )

    def add_guidance_revision(
        self,
        exercise_id: int,
        guidance: dict[str, Any],
        *,
        bundled_content_id: str | None = None,
        bundled_content_version: int | None = None,
    ) -> int:
        if (bundled_content_id is None) != (bundled_content_version is None):
            raise ValueError("Bundled content identity and version must be stored together.")
        if bundled_content_version is not None and (
            not isinstance(bundled_content_version, int) or bundled_content_version < 1
        ):
            raise ValueError("Bundled content version must be a positive integer.")
        payload = guidance_to_json(guidance)
        revision = self.connection.execute(
            "SELECT COALESCE(MAX(revision_number), 0) + 1 "
            "FROM exercise_guidance_revision WHERE exercise_id = ?",
            (exercise_id,),
        ).fetchone()[0]
        cursor = self.connection.execute(
            "INSERT INTO exercise_guidance_revision("
            "exercise_id, revision_number, guidance_json, created_at, "
            "bundled_content_id, bundled_content_version) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                exercise_id,
                revision,
                payload,
                datetime.now(UTC).isoformat(),
                bundled_content_id,
                bundled_content_version,
            ),
        )
        return cursor.lastrowid

    def set_guidance_status(
        self,
        revision_id: int,
        status: GuidanceStatus,
        review: dict[str, Any] | None = None,
    ) -> None:
        row = self.connection.execute(
            "SELECT guidance_json FROM exercise_guidance_revision WHERE id = ?", (revision_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Guidance revision was not found.")
        payload = json.loads(row[0])
        current_status = review_status(payload)
        allowed = {
            GuidanceStatus.DRAFT: {GuidanceStatus.PENDING_REVIEW},
            GuidanceStatus.PENDING_REVIEW: {GuidanceStatus.APPROVED},
            GuidanceStatus.REJECTED: {GuidanceStatus.PENDING_REVIEW},
        }
        if status not in allowed.get(current_status, set()):
            if current_status == GuidanceStatus.ACTIVE:
                raise ValueError("Guidance revision cannot be changed after activation.")
            raise ValueError("Guidance revision must be pending review before approval.")
        metadata = dict(payload.get("review", {}))
        metadata.update(review or {})
        metadata["status"] = status.value
        payload["review"] = metadata
        if status is GuidanceStatus.APPROVED and not can_activate_guidance(payload):
            raise ValueError("Complete guidance and explicit user approval are required.")
        self.connection.execute(
            "UPDATE exercise_guidance_revision SET guidance_json = ? WHERE id = ?",
            (guidance_to_json(payload), revision_id),
        )

    def activate_guidance(self, revision_id: int) -> None:
        row = self.connection.execute(
            "SELECT exercise_id, guidance_json FROM exercise_guidance_revision WHERE id = ?",
            (revision_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Guidance revision was not found.")
        payload = json.loads(row[1])
        if review_status(payload) != GuidanceStatus.APPROVED or not can_activate_guidance(payload):
            raise ValueError("Complete guidance and explicit user approval are required.")
        self._activate_guidance_revision(revision_id, row[0], payload)

    def review_and_activate_guidance(
        self, revision_id: int, review: dict[str, Any]
    ) -> None:
        """Complete the user-visible guidance approval action atomically."""
        with sqlite_transaction(self.connection, immediate=True):
            row = self.connection.execute(
                "SELECT exercise_id, guidance_json FROM exercise_guidance_revision WHERE id = ?",
                (revision_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Guidance revision was not found.")
            payload = json.loads(row[1])
            current_status = review_status(payload)
            if current_status == GuidanceStatus.ACTIVE:
                raise ValueError("Guidance revision cannot be changed after activation.")
            if current_status not in {
                GuidanceStatus.DRAFT,
                GuidanceStatus.PENDING_REVIEW,
                GuidanceStatus.REJECTED,
            }:
                raise ValueError("Guidance revision is already approved.")
            metadata = {
                **payload.get("review", {}),
                **review,
                "status": GuidanceStatus.APPROVED.value,
            }
            payload["review"] = metadata
            if not can_activate_guidance(payload):
                raise ValueError("Complete guidance and explicit user approval are required.")
            self._activate_guidance_revision(revision_id, row[0], payload)

    def _activate_guidance_revision(
        self, revision_id: int, exercise_id: int, payload: dict[str, Any]
    ) -> None:
        """Apply the shared active-revision writes inside the caller's transaction."""
        old_rows = self.connection.execute(
            "SELECT id, guidance_json FROM exercise_guidance_revision "
            "WHERE exercise_id = ? AND id != ?",
            (exercise_id, revision_id),
        ).fetchall()
        for old in old_rows:
            old_payload = json.loads(old[1])
            if review_status(old_payload) == GuidanceStatus.ACTIVE:
                old_payload["review"] = {
                    **old_payload.get("review", {}),
                    "status": GuidanceStatus.APPROVED.value,
                }
                self.connection.execute(
                    "UPDATE exercise_guidance_revision SET guidance_json = ? WHERE id = ?",
                    (guidance_to_json(old_payload), old[0]),
                )
        payload["review"] = {
            **payload.get("review", {}),
            "status": GuidanceStatus.ACTIVE.value,
        }
        self.connection.execute(
            "UPDATE exercise_guidance_revision SET guidance_json = ? WHERE id = ?",
            (guidance_to_json(payload), revision_id),
        )
        self.connection.execute(
            "UPDATE exercise SET active_guidance_revision_id = ? WHERE id = ?",
            (revision_id, exercise_id),
        )
