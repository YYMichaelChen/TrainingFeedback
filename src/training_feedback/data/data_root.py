"""应用自有数据根目录的创建、校验与打开；永不触碰旧应用的目录。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database import Database

APPLICATION_NAME = "TrainingFeedback"
DATA_FORMAT_VERSION = 1
MARKER_FILENAME = "training_feedback.marker.json"
CONFIG_FILENAME = "app_config.json"
DATABASE_FILENAME = "training_feedback.sqlite3"
# exercise-images 为动作指导图片预留；当前版本尚无代码读写该目录。
MANAGED_DIRECTORIES = ("backups", "exercise-images", "exports", "imports")


class DataRootError(Exception):
    """Base class for data-root failures."""


class DataRootNotEmptyError(DataRootError):
    pass


class InvalidDataRootError(DataRootError):
    pass


class UnsupportedDataFormatError(DataRootError):
    pass


class DataRootAccessError(DataRootError):
    pass


@dataclass(frozen=True)
class DataRoot:
    path: Path
    database_path: Path


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidDataRootError(f"Cannot read {path.name}.") from exc
    if not isinstance(value, dict):
        raise InvalidDataRootError(f"{path.name} must contain a JSON object.")
    return value


def _validate_metadata(root: Path) -> None:
    marker = _read_json(root / MARKER_FILENAME)
    if marker.get("application") != APPLICATION_NAME:
        raise InvalidDataRootError("The directory is not a TrainingFeedback data root.")
    version = marker.get("data_format_version")
    if version != DATA_FORMAT_VERSION:
        raise UnsupportedDataFormatError(f"Unsupported data format version: {version!r}.")

    config = _read_json(root / CONFIG_FILENAME)
    if config.get("application") != APPLICATION_NAME:
        raise InvalidDataRootError("The data-root configuration belongs to another application.")
    if config.get("data_format_version") != DATA_FORMAT_VERSION:
        raise UnsupportedDataFormatError("The configuration uses an unsupported data format.")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as file:
            json.dump(value, file, ensure_ascii=True, indent=2)
            file.write("\n")
    except OSError as exc:
        raise DataRootAccessError(f"Cannot write {path.name}.") from exc


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
                "config_version": 1,
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
        raise DataRootAccessError(f"Cannot create data root at {root}.") from exc


def open_existing(root_path: Path) -> DataRoot:
    """Validate and open an existing application-owned data root."""
    root = Path(root_path)
    if not root.is_dir():
        raise InvalidDataRootError("The selected path is not a directory.")
    _validate_metadata(root)
    database_path = root / DATABASE_FILENAME
    if not database_path.is_file():
        raise InvalidDataRootError("The data root does not contain its database.")
    try:
        with Database(database_path):
            pass
    except Exception as exc:
        if isinstance(exc, DataRootError):
            raise
        raise InvalidDataRootError("The TrainingFeedback database is invalid.") from exc
    return DataRoot(root, database_path)
