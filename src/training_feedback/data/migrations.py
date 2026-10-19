"""Schema26 initialization and the retained-version migration boundary."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from ..domain.execution_modes import upgrade_payload

LATEST_SCHEMA_VERSION = 26
OLDEST_SUPPORTED_SCHEMA_VERSION = 23
SUPPORTED_SCHEMA_APPLICATIONS = {23: "0.8.1", 24: "0.8.2-0.8.18", 25: "0.8.19-0.8.20",
                                 26: "0.8.21-0.8.24"}


def _install26(connection, *, old_documents=False):
    connection.execute("ALTER TABLE group_plan_revision ADD COLUMN format_version INTEGER "
                       "NOT NULL DEFAULT 4 CHECK(format_version IN (4,5))")
    connection.execute("ALTER TABLE group_actual_set ADD COLUMN planned_set_order INTEGER")
    connection.execute("ALTER TABLE group_actual_set ADD COLUMN recording_scope TEXT "
                       "CHECK(recording_scope IN ('total','sides'))")
    if old_documents:
        # The source revisions, imports and session snapshots are never rewritten.
        rows = connection.execute("SELECT * FROM plan_edit_document").fetchall()
        columns = [row[1] for row in connection.execute("PRAGMA table_info(plan_edit_document)")]
        connection.execute("DROP INDEX one_edit_upgrade_source")
        connection.execute("ALTER TABLE plan_edit_document RENAME TO old_edit_document")
        script = Path(__file__).with_name("draft_documents.sql").read_text(encoding="utf-8")
        for statement in script.split(";"):
            if statement.strip():
                connection.execute(statement)
        for row in rows:
            document = dict(zip(columns, row))
            if document["format_version"] != 1:
                raise sqlite3.DatabaseError("Unsupported edit document format.")
            document["format_version"] = 2
            document["payload_json"] = json.dumps(upgrade_payload(
                json.loads(document["payload_json"])), ensure_ascii=False, allow_nan=False)
            connection.execute("INSERT INTO plan_edit_document (" + ",".join(columns)
                               + ") VALUES (" + ",".join("?" for _ in columns) + ")",
                               tuple(document[column] for column in columns))
        connection.execute("DROP TABLE old_edit_document")

class FutureSchemaError(sqlite3.DatabaseError):
    """The database belongs to a newer application version."""


class ExpiredSchemaError(sqlite3.DatabaseError):
    """The database predates the retained application window."""


def _current_version(connection: sqlite3.Connection) -> int:
    has_migrations = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migration'"
    ).fetchone()
    if not has_migrations:
        occupied = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1"
        ).fetchone()
        if occupied:
            raise sqlite3.DatabaseError("An existing database has no schema version.")
        return 0
    version = connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0]
    if type(version) is not int or version < 1:
        raise sqlite3.DatabaseError("Invalid schema version.")
    return version


def _initialize(connection: sqlite3.Connection) -> None:
    schema = Path(__file__).with_name("schema24.sql").read_text(encoding="utf-8")
    try:
        edits = Path(__file__).with_name("draft_documents.sql").read_text(encoding="utf-8")
        connection.executescript("BEGIN;\n" + schema + "\n" + edits)
        _install26(connection)
        connection.execute(
            "INSERT INTO schema_migration(version, applied_at) VALUES (?, ?)",
            (LATEST_SCHEMA_VERSION, datetime.now(UTC).isoformat()),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Inspect existing roots read-only before any schema write."""
    current = _current_version(connection)
    if current > LATEST_SCHEMA_VERSION:
        raise FutureSchemaError("Database schema is newer than this application.")
    if 0 < current < OLDEST_SUPPORTED_SCHEMA_VERSION:
        raise ExpiredSchemaError("Database schema is older than the supported window.")
    if current == 0:
        _initialize(connection)
        return
    if current in (23, 24):
        script = Path(__file__).with_name("draft_documents.sql").read_text(encoding="utf-8")
        if current == 23:
            script = (
                "ALTER TABLE group_plan_day DROP COLUMN name;\n"
                "ALTER TABLE training_plan_day DROP COLUMN name;\n"
                "ALTER TABLE training_session DROP COLUMN plan_day_name_snapshot;\n" + script
            )
        try:
            connection.executescript("BEGIN IMMEDIATE;\n" + script)
            if current == 23:
                connection.execute(
                    "INSERT INTO schema_migration(version, applied_at) VALUES (?, ?)",
                    (24, datetime.now(UTC).isoformat()),
                )
            connection.execute(
                "INSERT INTO schema_migration(version, applied_at) VALUES (?, ?)",
                (25, datetime.now(UTC).isoformat()),
            )
            _install26(connection)
            connection.execute("INSERT INTO schema_migration(version,applied_at) VALUES (?,?)",
                               (26, datetime.now(UTC).isoformat()))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    elif current == 25:
        try:
            connection.execute("BEGIN IMMEDIATE")
            _install26(connection, old_documents=True)
            connection.execute("INSERT INTO schema_migration(version,applied_at) VALUES (?,?)",
                               (26, datetime.now(UTC).isoformat()))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
