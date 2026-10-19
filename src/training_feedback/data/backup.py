"""Consistent complete-root backup with staged publication and cancellation."""

from __future__ import annotations

import os
import shutil
import sqlite3
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from .data_root import BACKUP_INCOMPLETE_FILENAME, DATABASE_FILENAME, DataRootError
from .root_lock import LOCK_FILENAME, MUTATION_LOCK_FILENAME, RootMutationLease

_COPY_CHUNK_BYTES = 1024 * 1024
_SQLITE_TRANSIENT_NAMES = {
    DATABASE_FILENAME + "-journal",
    DATABASE_FILENAME + "-shm",
    DATABASE_FILENAME + "-wal",
}
_COORDINATION_NAMES = {LOCK_FILENAME, MUTATION_LOCK_FILENAME}


class BackupError(DataRootError):
    pass


class BackupCancelled(BackupError):
    pass


def _raise_if_cancelled(cancelled: Callable[[], bool] | None) -> None:
    if cancelled is not None and cancelled():
        raise BackupCancelled("The data-root backup was cancelled.")


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def _require_empty_destination(destination: Path) -> None:
    if not destination.exists():
        return
    if _is_link(destination) or not destination.is_dir() or any(destination.iterdir()):
        raise BackupError("The backup destination must be empty.")


def _copy_file(
    source: Path,
    target: Path,
    cancelled: Callable[[], bool] | None,
) -> None:
    with source.open("rb") as input_stream, target.open("xb") as output_stream:
        while True:
            _raise_if_cancelled(cancelled)
            chunk = input_stream.read(_COPY_CHUNK_BYTES)
            if not chunk:
                break
            output_stream.write(chunk)
        output_stream.flush()
        os.fsync(output_stream.fileno())
    shutil.copystat(source, target, follow_symlinks=False)


def _copy_entry(
    source: Path,
    target: Path,
    cancelled: Callable[[], bool] | None,
) -> None:
    _raise_if_cancelled(cancelled)
    if _is_link(source):
        raise BackupError("The data root contains a linked path that cannot be backed up.")
    if source.is_dir():
        target.mkdir()
        for item in source.iterdir():
            _copy_entry(item, target / item.name, cancelled)
        shutil.copystat(source, target, follow_symlinks=False)
        return
    if not source.is_file():
        raise BackupError("The data root contains a non-file resource that cannot be backed up.")
    _copy_file(source, target, cancelled)


@contextmanager
def _locked_source_database(database_path: Path) -> Iterator[sqlite3.Connection]:
    """Hold a SQLite writer reservation while a separate read connection is backed up."""
    lock_connection = sqlite3.connect(database_path, timeout=5)
    source_connection = None
    try:
        lock_connection.execute("PRAGMA busy_timeout = 5000")
        lock_connection.execute("BEGIN IMMEDIATE")
        source_connection = sqlite3.connect(
            database_path.resolve().as_uri() + "?mode=ro",
            uri=True,
            timeout=5,
        )
        source_connection.execute("PRAGMA busy_timeout = 5000")
        yield source_connection
    finally:
        if source_connection is not None:
            source_connection.close()
        try:
            lock_connection.rollback()
        finally:
            lock_connection.close()


def _backup_database(
    connection: sqlite3.Connection,
    target: Path,
    cancelled: Callable[[], bool] | None,
) -> None:
    target_connection = sqlite3.connect(target)
    try:
        connection.backup(
            target_connection,
            pages=256,
            progress=lambda _status, _remaining, _total: _raise_if_cancelled(cancelled),
        )
        if target_connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise sqlite3.DatabaseError("The backup database failed its integrity check.")
    finally:
        target_connection.close()


def _staging_path(destination: Path) -> Path:
    return destination.parent / (
        f".{destination.name}.training-feedback-backup-{uuid.uuid4().hex}.staging"
    )


def _remove_staging(staging: Path) -> None:
    shutil.rmtree(staging, ignore_errors=True)
    if staging.exists():
        raise BackupError(
            "备份未完成；不完整副本未发布，但无法自动清理，请反馈此路径：" + str(staging)
        )


def create_backup(
    source: Path,
    destination: Path,
    connection: sqlite3.Connection | None = None,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> Path:
    """Create one recoverable backup and publish it only after every copy completes.

    ``connection`` remains accepted for existing internal callers, but is deliberately
    never used: the calling thread's SQLite connection cannot cross into the backup
    worker. This operation opens and closes all of its own SQLite connections.
    """
    del connection
    source = Path(source).resolve()
    requested_destination = Path(destination)
    if _is_link(requested_destination):
        raise BackupError("The backup destination must be empty.")
    destination = requested_destination.resolve()
    if not source.is_dir():
        raise BackupError("The source data root does not exist.")
    if destination == source or source in destination.parents:
        raise BackupError("A backup destination cannot be inside the source data root.")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        _require_empty_destination(destination)
    except BackupError:
        raise
    except OSError as exc:
        raise BackupError("Cannot create the backup destination.") from exc

    staging = _staging_path(destination)
    published = False
    try:
        staging.mkdir()
        (staging / BACKUP_INCOMPLETE_FILENAME).write_text(
            "TrainingFeedback backup incomplete\n", encoding="ascii", newline="\n"
        )
        with RootMutationLease(source):
            database_path = source / DATABASE_FILENAME
            if not database_path.is_file():
                raise BackupError("The source data root does not contain its database.")
            with _locked_source_database(database_path) as source_connection:
                _backup_database(
                    source_connection,
                    staging / DATABASE_FILENAME,
                    cancelled,
                )
                for item in source.iterdir():
                    if item.name == DATABASE_FILENAME:
                        continue
                    if item.name in _SQLITE_TRANSIENT_NAMES | _COORDINATION_NAMES:
                        continue
                    _copy_entry(item, staging / item.name, cancelled)
                shutil.copystat(source, staging, follow_symlinks=False)

        _raise_if_cancelled(cancelled)
        _require_empty_destination(destination)
        destination_existed = destination.exists()
        if destination_existed:
            destination.rmdir()
        try:
            staging.rename(destination)
        except OSError:
            if destination_existed and not destination.exists():
                try:
                    destination.mkdir()
                except OSError:
                    pass
            raise
        published = True
        try:
            (destination / BACKUP_INCOMPLETE_FILENAME).unlink()
        except OSError as exc:
            raise BackupError(
                "The completed backup could not be published and remains marked incomplete."
            ) from exc
        return destination
    except BackupCancelled:
        if not published:
            _remove_staging(staging)
        raise
    except BackupError:
        if not published:
            _remove_staging(staging)
        raise
    except (OSError, sqlite3.Error) as exc:
        if not published:
            _remove_staging(staging)
        raise BackupError("The data-root backup could not be completed.") from exc
