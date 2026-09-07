import json

import pytest

from training_feedback.data.data_root import (
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    MARKER_FILENAME,
    DataRootNotEmptyError,
    InvalidDataRootError,
    create_new,
    open_existing,
)


def test_create_and_reopen_data_root(data_path):
    created = create_new(data_path)

    assert created.path == data_path
    assert created.database_path == data_path / DATABASE_FILENAME
    assert (data_path / MARKER_FILENAME).is_file()
    assert (data_path / CONFIG_FILENAME).is_file()
    assert (data_path / "backups").is_dir()
    assert open_existing(data_path) == created


def test_creation_rejects_unknown_non_empty_directory(tmp_path):
    root = tmp_path / "occupied"
    root.mkdir()
    (root / "keep.txt").write_text("do not touch", encoding="utf-8")

    with pytest.raises(DataRootNotEmptyError):
        create_new(root)
    assert (root / "keep.txt").read_text(encoding="utf-8") == "do not touch"


def test_open_rejects_missing_marker(data_path):
    data_path.mkdir()
    (data_path / CONFIG_FILENAME).write_text("{}", encoding="utf-8")

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)


def test_open_rejects_wrong_application_marker(data_path):
    data_path.mkdir()
    (data_path / MARKER_FILENAME).write_text(
        json.dumps({"application": "Other", "data_format_version": 1}), encoding="utf-8"
    )

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)
