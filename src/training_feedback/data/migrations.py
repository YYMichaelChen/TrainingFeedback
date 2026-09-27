"""Schema22 fresh initialization and retained-version migration boundary."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

LATEST_SCHEMA_VERSION = 22
OLDEST_SUPPORTED_SCHEMA_VERSION = 22
SUPPORTED_SCHEMA_APPLICATIONS = {22: "0.7.2/0.7.3/0.7.4"}

# Add a versioned body here when a later application version raises the schema.
# Existing schema22 roots are never reinitialized or rewritten by a patch update.
_MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {}


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
    schema = Path(__file__).with_name("schema22.sql").read_text(encoding="utf-8")
    try:
        connection.executescript("BEGIN;\n" + schema)
        connection.execute(
            "INSERT INTO schema_migration(version, applied_at) VALUES (?, ?)",
            (LATEST_SCHEMA_VERSION, datetime.now(UTC).isoformat()),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _apply(connection: sqlite3.Connection, version: int,
           body: Callable[[sqlite3.Connection], None]) -> None:
    try:
        connection.execute("BEGIN")
        body(connection)
        connection.execute(
            "INSERT INTO schema_migration(version, applied_at) VALUES (?, ?)",
            (version, datetime.now(UTC).isoformat()),
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
    for version in range(current + 1, LATEST_SCHEMA_VERSION + 1):
        body = _MIGRATIONS.get(version)
        if body is None:
            raise sqlite3.DatabaseError(f"Schema migration {version} is missing.")
        _apply(connection, version, body)
