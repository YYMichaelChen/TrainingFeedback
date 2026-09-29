"""Finish committed 0.7.5 cleanup journals in retained schema-23 roots."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .root_lock import RootLease, require_no_pending_upgrade

_RESET_DIRECTORIES = ("backups", "exports", "imports")
_JOURNAL_TABLE = "one_time_reset_journal"


class ResetRecoveryError(OSError):
    """The one-time reset is pending or its managed cleanup cannot be completed."""


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


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


def _version(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()
    if row is None or type(row[0]) is not int:
        raise sqlite3.DatabaseError("Invalid schema version.")
    return row[0]


def _readonly_version_and_check(database_path: Path) -> tuple[int, bool]:
    uri = database_path.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            version = _version(connection)
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise sqlite3.DatabaseError("Invalid database integrity.")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise sqlite3.DatabaseError("Invalid database references.")
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
        raise sqlite3.DatabaseError("The TrainingFeedback database is invalid.") from exc


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
    """Finish a committed schema-23 journal before the root is usable."""
    root = Path(root)
    database_path = root / "training_feedback.sqlite3"
    version, pending = _readonly_version_and_check(database_path)
    if version != 23 or not pending:
        return

    with RootLease(root, exclusive=True):
        require_no_pending_upgrade(root)
        if _is_link(root) or _is_link(database_path):
            raise ResetRecoveryError("The selected data root or database is a link.")
        # Recheck metadata under the exclusive lease before any database or file write.
        from .data_root import _validate_metadata

        _validate_metadata(root)
        current, pending = _readonly_version_and_check(database_path)
        if current == 23 and pending:
            _finish_cleanup(root, database_path)
