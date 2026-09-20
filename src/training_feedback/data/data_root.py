"""应用自有数据根目录的创建、校验与打开；永不触碰旧应用的目录。"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import migrations
from .database import Database
from .migrations import OLDEST_SUPPORTED_SCHEMA_VERSION, FutureSchemaError
from .root_lock import RootBusyError

APPLICATION_NAME = "TrainingFeedback"
DATA_FORMAT_VERSION = 1
CONFIG_VERSION = 1
MARKER_FILENAME = "training_feedback.marker.json"
CONFIG_FILENAME = "app_config.json"
DATABASE_FILENAME = "training_feedback.sqlite3"
# exercise-images 保存动作指导引用的受管图片；数据库仅保存相对数据根的引用。
MANAGED_DIRECTORIES = ("backups", "exercise-images", "exports", "imports")


class DataRootError(Exception):
    """Base class for data-root failures."""


class DataRootNotEmptyError(DataRootError):
    pass


class InvalidDataRootError(DataRootError):
    pass


class UnsupportedDataFormatError(DataRootError):
    pass


class ExpiredDataRootError(DataRootError):
    """Section 13.2: the root predates the retention window; refuse before writes."""


class DataRootAccessError(DataRootError):
    pass


CANDIDATE_EXISTING = "existing"
CANDIDATE_NEW = "new"
CANDIDATE_OCCUPIED = "occupied"


@dataclass(frozen=True)
class DataRoot:
    path: Path
    database_path: Path


def describe_candidate(root_path: Path) -> str:
    """判断一个确切路径可用于打开还是新建；只读文件系统，不打开数据库、不做目录扫描。

    `existing` 表示该目录带有本应用的标记文件，`new` 表示路径不存在或是空目录，
    `occupied` 表示目录里有其他内容。无法读取时按 `occupied` 处理，不建议在此新建。
    """
    root = Path(root_path)
    try:
        if (root / MARKER_FILENAME).is_file():
            return CANDIDATE_EXISTING
        if not root.exists():
            return CANDIDATE_NEW
        if root.is_dir() and not any(root.iterdir()):
            return CANDIDATE_NEW
    except OSError:
        return CANDIDATE_OCCUPIED
    return CANDIDATE_OCCUPIED


def _read_json(path: Path, *, missing_message: str) -> dict[str, Any]:
    """读取数据目录元数据。消息保持固定字面量，UI 才能给出中文提示而不漏出文件名。"""
    try:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
    except FileNotFoundError as exc:
        raise InvalidDataRootError(missing_message) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidDataRootError("The data-root metadata cannot be read.") from exc
    if not isinstance(value, dict):
        raise InvalidDataRootError("The data-root metadata cannot be read.")
    return value


def _checked_version(metadata: dict[str, Any], key: str, supported: int) -> None:
    """版本字段必须是整数；缺失、类型错误或低于当前版本视为无效，更高版本视为未来格式。"""
    value = metadata.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidDataRootError("The data-root metadata is incomplete or invalid.")
    if value > supported:
        raise UnsupportedDataFormatError(
            "The data root requires a newer version of TrainingFeedback."
        )
    if value != supported:
        raise InvalidDataRootError("The data-root metadata is incomplete or invalid.")


def _validate_metadata(root: Path) -> None:
    marker = _read_json(
        root / MARKER_FILENAME,
        missing_message="The directory is not a TrainingFeedback data root.",
    )
    if marker.get("application") != APPLICATION_NAME:
        raise InvalidDataRootError("The directory is not a TrainingFeedback data root.")
    _checked_version(marker, "data_format_version", DATA_FORMAT_VERSION)

    config = _read_json(
        root / CONFIG_FILENAME,
        missing_message="The data-root metadata is incomplete or invalid.",
    )
    if config.get("application") != APPLICATION_NAME:
        raise InvalidDataRootError("The data-root configuration belongs to another application.")
    _checked_version(config, "config_version", CONFIG_VERSION)
    _checked_version(config, "data_format_version", DATA_FORMAT_VERSION)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as file:
            json.dump(value, file, ensure_ascii=True, indent=2)
            file.write("\n")
    except OSError as exc:
        raise DataRootAccessError("Cannot create the data root.") from exc


def create_new(root_path: Path) -> DataRoot:
    """Create a new data root without touching an unknown non-empty directory."""
    root = Path(root_path)
    try:
        if root.exists():
            if not root.is_dir():
                raise DataRootNotEmptyError("The selected path is not an empty directory.")
            if any(root.iterdir()):
                raise DataRootNotEmptyError("The selected directory is not empty.")
        else:
            root.mkdir(parents=True)
        for directory in MANAGED_DIRECTORIES:
            (root / directory).mkdir()
        _write_json(
            root / MARKER_FILENAME,
            {
                "application": APPLICATION_NAME,
                "data_format_version": DATA_FORMAT_VERSION,
            },
        )
        _write_json(
            root / CONFIG_FILENAME,
            {
                "application": APPLICATION_NAME,
                "config_version": CONFIG_VERSION,
                "data_format_version": DATA_FORMAT_VERSION,
            },
        )
        database_path = root / DATABASE_FILENAME
        with Database(database_path):
            pass
        return DataRoot(root, database_path)
    except DataRootError:
        raise
    except OSError as exc:
        raise DataRootAccessError("Cannot create the data root.") from exc


def inspect_existing(root_path: Path) -> DataRoot:
    """Validate without migrating or creating files; usable before a recovery snapshot."""
    root = Path(root_path)
    if not root.is_dir():
        raise InvalidDataRootError("The selected path is not a directory.")
    # 空目录是首次启动最常见的误选：报缺少标记文件无法帮助用户，明确指向创建流程。
    try:
        selected_is_empty = not any(root.iterdir())
    except OSError:
        selected_is_empty = False
    if selected_is_empty:
        raise InvalidDataRootError(
            "The selected directory is empty. Create a new data root instead."
        )
    _validate_metadata(root)
    database_path = root / DATABASE_FILENAME
    if not database_path.is_file():
        raise InvalidDataRootError("The data root does not contain its database.")
    try:
        uri = database_path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            version = connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0]
            if type(version) is not int or version < 1:
                raise sqlite3.DatabaseError("Invalid schema version.")
            if version > migrations.LATEST_SCHEMA_VERSION:
                raise UnsupportedDataFormatError(
                    "The database requires a newer version of TrainingFeedback."
                )
            if version < OLDEST_SUPPORTED_SCHEMA_VERSION:
                raise ExpiredDataRootError(
                    "This development data version is outside the support window. "
                    "Reinstall the current application version and create a new data "
                    "directory; the original data directory is preserved and will not "
                    "be deleted or reset."
                )
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise sqlite3.DatabaseError("Invalid database integrity.")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise sqlite3.DatabaseError("Invalid database references.")
    except sqlite3.Error as exc:
        raise InvalidDataRootError("The TrainingFeedback database is invalid.") from exc
    return DataRoot(root, database_path)


def open_existing(root_path: Path) -> DataRoot:
    """Validate and open an existing application-owned data root."""
    root = inspect_existing(root_path)
    try:
        with Database(root.database_path):
            pass
    except FutureSchemaError as exc:
        raise UnsupportedDataFormatError(
            "The database requires a newer version of TrainingFeedback."
        ) from exc
    except RootBusyError as exc:
        raise DataRootAccessError(str(exc)) from exc
    except Exception as exc:
        raise InvalidDataRootError("The TrainingFeedback database is invalid.") from exc
    return root
