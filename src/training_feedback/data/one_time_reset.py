"""The explicit 0.7.5 schema22 plan/training reset and resumable file cleanup."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .root_lock import RootLease, require_no_pending_upgrade

_RESET_DIRECTORIES = ("backups", "exports", "imports")
_RETAINED_TABLES = (
    "body_area",
    "content_snapshot",
    "content_snapshot_asset",
    "exercise",
    "exercise_alias",
    "exercise_body_area",
    "exercise_guidance_revision",
    "library_content",
    "library_lifecycle_event",
    "library_lifecycle_request",
    "library_publisher_event",
    "library_reference",
    "library_review_event",
    "library_state",
    "library_tombstone",
    "snapshot_asset",
)
_JOURNAL_TABLE = "one_time_reset_journal"


class ResetRecoveryError(OSError):
    """The one-time reset is pending or its managed cleanup cannot be completed."""


class InvalidResetRootError(sqlite3.DatabaseError):
    """The schema22 database is not a complete, supported reset source."""


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _inventory_directory(root: Path) -> list[str]:
    inventory: list[str] = []

    def visit(directory: Path, relative: str) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda item: item.name)
        except FileNotFoundError:
            return
        for child in entries:
            child_relative = f"{relative}/{child.name}"
            if _is_link(child):
                inventory.append(child_relative)
            elif child.is_dir():
                visit(child, child_relative)
                inventory.append(child_relative)
            elif child.is_file():
                inventory.append(child_relative)
            else:
                raise ResetRecoveryError("A managed cleanup path cannot be inspected.")

    for name in _RESET_DIRECTORIES:
        base = root / name
        if _is_link(base):
            raise ResetRecoveryError("A managed cleanup directory is a link.")
        if base.exists():
            if not base.is_dir():
                raise ResetRecoveryError("A managed cleanup directory is invalid.")
            visit(base, name)
    return inventory


def _checked_inventory(value: object) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ResetRecoveryError("The one-time reset journal is invalid.")
    result: list[str] = []
    for item in value:
        parts = item.split("/")
        if (
            len(parts) < 2
            or parts[0] not in _RESET_DIRECTORIES
            or any(part in ("", ".", "..") or "\\" in part or ":" in part for part in parts)
        ):
            raise ResetRecoveryError("The one-time reset journal is invalid.")
        result.append(item)
    if len(set(result)) != len(result):
        raise ResetRecoveryError("The one-time reset journal is invalid.")
    return result


def _delete_path(root: Path, relative: str) -> None:
    parts = relative.split("/")
    path = root / parts[0]
    for part in parts[1:]:
        if _is_link(path):
            raise ResetRecoveryError("A managed cleanup parent became a link.")
        path = path / part
    if not path.exists() and not _is_link(path):
        return
    if _is_link(path):
        try:
            path.rmdir() if path.is_dir() else path.unlink()
        except OSError as exc:
            raise ResetRecoveryError("A managed file could not be removed.") from exc
        return
    try:
        path.rmdir() if path.is_dir() else path.unlink()
    except OSError as exc:
        raise ResetRecoveryError("A managed file could not be removed.") from exc


def _sql_statements(script: str):
    pending = ""
    for line in script.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            statement = pending.strip()
            if statement:
                yield statement
            pending = ""
    if pending.strip():
        raise sqlite3.DatabaseError("Schema script contains an incomplete statement.")


def _version(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()
    if row is None or type(row[0]) is not int:
        raise sqlite3.DatabaseError("Invalid schema version.")
    return row[0]


def _schema_signature(connection: sqlite3.Connection) -> dict[tuple[str, str], str]:
    return {
        (row[0], row[1]): " ".join((row[2] or "").casefold().split())
        for row in connection.execute(
            "SELECT type,name,sql FROM sqlite_master WHERE type IN "
            "('table','index','view','trigger') AND name NOT LIKE 'sqlite_%'"
        )
    }


def _validate_schema22_shape(connection: sqlite3.Connection) -> None:
    schema = Path(__file__).with_name("schema22.sql").read_text(encoding="utf-8")
    with sqlite3.connect(":memory:") as expected:
        expected.executescript(schema)
        if _schema_signature(connection) != _schema_signature(expected):
            raise sqlite3.DatabaseError("The schema22 root is incomplete or modified.")


def _readonly_version_and_check(database_path: Path) -> tuple[int, bool]:
    uri = database_path.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            version = _version(connection)
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise sqlite3.DatabaseError("Invalid database integrity.")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise sqlite3.DatabaseError("Invalid database references.")
            if version == 22:
                _validate_schema22_shape(connection)
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            pending = False
            if _JOURNAL_TABLE in tables:
                pending = connection.execute(
                    f"SELECT 1 FROM {_JOURNAL_TABLE} WHERE id=1"
                ).fetchone() is not None
            return version, pending
    except sqlite3.Error as exc:
        raise InvalidResetRootError("The TrainingFeedback database is invalid.") from exc


def _rebuild_schema23(connection: sqlite3.Connection, inventory: list[str]) -> None:
    retained: dict[str, tuple[list[str], list[tuple]]] = {}
    for table in _RETAINED_TABLES:
        columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
        if not columns:
            raise sqlite3.DatabaseError(f"Retained table {table} is missing.")
        rows = [tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')]
        retained[table] = (columns, rows)

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("BEGIN IMMEDIATE")
    try:
        objects = connection.execute(
            "SELECT type, name FROM sqlite_master WHERE type IN ('trigger','view','table') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'trigger' THEN 0 "
            "WHEN 'view' THEN 1 ELSE 2 END, name"
        ).fetchall()
        for object_type, name in objects:
            quoted = '"' + name.replace('"', '""') + '"'
            connection.execute(f"DROP {object_type.upper()} {quoted}")

        schema = Path(__file__).with_name("schema23.sql").read_text(encoding="utf-8")
        for statement in _sql_statements(schema):
            connection.execute(statement)

        for table, (columns, rows) in retained.items():
            quoted_columns = ",".join('"' + column.replace('"', '""') + '"' for column in columns)
            placeholders = ",".join("?" for _ in columns)
            connection.executemany(
                f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})', rows
            )

        now = datetime.now(UTC).isoformat()
        connection.execute(
            "INSERT INTO schema_migration(version, applied_at) VALUES (23, ?)", (now,)
        )
        if inventory:
            connection.execute(
                f"INSERT INTO {_JOURNAL_TABLE}(id,operation,path_inventory_json,created_at) "
                "VALUES (1,'reset-v0.7.5',?,?)",
                (json.dumps(inventory, ensure_ascii=True), now),
            )
        violation = connection.execute("PRAGMA foreign_key_check").fetchone()
        if violation is not None:
            raise sqlite3.IntegrityError("The reset produced invalid database references.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def _finish_cleanup(root: Path, database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            f"SELECT operation,path_inventory_json FROM {_JOURNAL_TABLE} WHERE id=1"
        ).fetchone()
    if row is None:
        return
    operation, raw_inventory = row
    if operation != "reset-v0.7.5":
        raise ResetRecoveryError("The one-time reset journal is invalid.")
    try:
        inventory = _checked_inventory(json.loads(raw_inventory))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ResetRecoveryError("The one-time reset journal is invalid.") from exc
    for relative in inventory:
        _delete_path(root, relative)
    with sqlite3.connect(database_path) as connection:
        connection.execute("DELETE FROM one_time_reset_journal WHERE id=1")
        connection.commit()


def prepare_existing_root(root: Path) -> None:
    """Reset schema22 once or finish committed cleanup before the root is usable."""
    root = Path(root)
    database_path = root / "training_feedback.sqlite3"
    version, pending = _readonly_version_and_check(database_path)
    if version != 22 and not pending:
        return

    with RootLease(root, exclusive=True):
        require_no_pending_upgrade(root)
        if _is_link(root) or _is_link(database_path):
            raise ResetRecoveryError("The selected data root or database is a link.")
        # Recheck metadata under the exclusive lease before any database or file write.
        from .data_root import _validate_metadata

        _validate_metadata(root)
        current, pending = _readonly_version_and_check(database_path)
        if current == 22:
            inventory = _inventory_directory(root)
            try:
                with sqlite3.connect(database_path) as connection:
                    _rebuild_schema23(connection, inventory)
            except Exception:
                raise
            pending = bool(inventory)
        elif current != 23:
            return
        if pending:
            _finish_cleanup(root, database_path)
