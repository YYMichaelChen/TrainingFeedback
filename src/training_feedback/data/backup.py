"""数据根目录的完整备份。

直接复制打开中的 SQLite 文件可能拷出不一致的库，因此传入活动连接时
数据库文件走 SQLite 在线备份 API，其余文件照原样复制。
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from .data_root import DATABASE_FILENAME, DataRootError


class BackupError(DataRootError):
    pass


def create_backup(
    source: Path, destination: Path, connection: sqlite3.Connection | None = None
) -> Path:
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_dir():
        raise BackupError("The source data root does not exist.")
    if destination == source or source in destination.parents:
        raise BackupError("A backup destination cannot be inside the source data root.")
    if destination.exists():
        if not destination.is_dir() or any(destination.iterdir()):
            raise BackupError("The backup destination must be empty.")
    else:
        try:
            destination.mkdir(parents=True)
        except OSError as exc:
            raise BackupError("Cannot create the backup destination.") from exc
    try:
        for item in source.iterdir():
            target = destination / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            elif connection is not None and item.name == DATABASE_FILENAME:
                _backup_database(connection, target)
            else:
                shutil.copy2(item, target)
    except (OSError, sqlite3.Error) as exc:
        raise BackupError("The data-root backup could not be completed.") from exc
    return destination


def _backup_database(connection: sqlite3.Connection, target: Path) -> None:
    """用 SQLite 在线备份 API 一致地复制处于打开状态的数据库。"""
    target_connection = sqlite3.connect(target)
    try:
        connection.backup(target_connection)
    finally:
        target_connection.close()
