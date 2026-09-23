"""One-time source capture, immutable provenance and retirement of accounted-for tables."""

from __future__ import annotations

import json

from ..domain.catalog import content_sha256

OLD_TABLES = (
    "exercise",
    "exercise_alias",
    "exercise_guidance_revision",
    "body_area",
    "exercise_body_area",
    "training_plan",
    "training_plan_revision",
    "training_plan_day",
    "training_plan_action",
    "training_plan_set",
    "training_session",
    "training_session_action",
    "training_session_set",
    "training_session_actual_set",
    "session_event",
    "next_day_feedback",
    "next_day_feedback_area",
    "ai_export",
    "plan_import",
    "note_correction_audit",
    "session_result_retraction",
)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def rows(connection, table):
    return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]


def source_facts(connection, config):
    tables = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    return {
        "schema": connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0],
        "config": config,
        "tables": {name: rows(connection, name) for name in OLD_TABLES if name in tables},
    }


class ConversionRepository:
    def __init__(self, connection):
        self.connection = connection

    def archive(self, original):
        for table, records in original["tables"].items():
            for index, row in enumerate(records):
                key = str(row["id"]) if "id" in row else f"row.{index}"
                self.connection.execute(
                    "INSERT INTO conversion_original VALUES (?,?,?)", (table, key, encode(row))
                )
        self.connection.execute(
            "INSERT INTO conversion_original VALUES (?,?,?)",
            ("app_config", "1", encode(original["config"])),
        )

    def map(self, table, key, kind, target):
        self.connection.execute(
            "INSERT INTO conversion_mapping VALUES (?,?,?,?)",
            (table, str(key), kind, encode(target)),
        )

    def complete(self, original, now, manifest):
        self.connection.execute(
            "INSERT INTO conversion_run VALUES (1,?,?,?,?)",
            (original["schema"], content_sha256(original), now, encode(manifest)),
        )

    def retire(self):
        # Historical immutable triggers cannot prevent retirement of their already archived tables.
        for row in self.connection.execute(
            "SELECT name,tbl_name FROM sqlite_master WHERE type='trigger'"
        ).fetchall():
            if row[1] in OLD_TABLES:
                name = row[0].replace('"', '""')
                self.connection.execute(f'DROP TRIGGER "{name}"')
        # FK enforcement is disabled by the converter before its single transaction. New-model
        # foreign_key_check is mandatory before commit and again at read-only validation.
        for table in reversed(OLD_TABLES):
            self.connection.execute(f'DROP TABLE IF EXISTS "{table}"')

    def registrations(self, revision_id=None, session_id=None):
        result = []
        for row in self.connection.execute(
            "SELECT * FROM conversion_registration ORDER BY kind,id"
        ):
            if (
                (revision_id is not None and row["revision_id"] == revision_id)
                or (session_id is not None and row["session_id"] == session_id)
                or (row["revision_id"] is None and row["session_id"] is None)
            ):
                result.append({**dict(row), "facts": json.loads(row["facts_json"])})
        return result
