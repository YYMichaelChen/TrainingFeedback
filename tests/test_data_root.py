import json
import sqlite3

import pytest

from training_feedback.data.data_root import (
    CANDIDATE_EXISTING,
    CANDIDATE_NEW,
    CANDIDATE_OCCUPIED,
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    MARKER_FILENAME,
    DataRootNotEmptyError,
    InvalidDataRootError,
    UnsupportedDataFormatError,
    create_new,
    describe_candidate,
    open_existing,
)
from training_feedback.ui.labels import user_message


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


def test_describe_candidate_reads_one_path_without_opening_the_database(data_path, tmp_path):
    assert describe_candidate(data_path) == CANDIDATE_NEW
    data_path.mkdir()
    assert describe_candidate(data_path) == CANDIDATE_NEW

    (data_path / "unrelated.txt").write_text("keep", encoding="utf-8")
    assert describe_candidate(data_path) == CANDIDATE_OCCUPIED

    existing = tmp_path / "existing"
    create_new(existing)
    database_bytes = (existing / DATABASE_FILENAME).read_bytes()
    assert describe_candidate(existing) == CANDIDATE_EXISTING
    assert (existing / DATABASE_FILENAME).read_bytes() == database_bytes

    file_path = tmp_path / "plain.txt"
    file_path.write_text("not a directory", encoding="utf-8")
    assert describe_candidate(file_path) == CANDIDATE_OCCUPIED


def test_open_rejects_empty_directory_and_points_at_creation(data_path):
    data_path.mkdir()

    with pytest.raises(InvalidDataRootError) as failure:
        open_existing(data_path)
    assert "Create a new data root" in str(failure.value)
    assert user_message(str(failure.value)) != str(failure.value)


def test_open_rejects_unreadable_marker_without_leaking_the_filename(data_path):
    data_path.mkdir()
    (data_path / MARKER_FILENAME).write_text("{not json", encoding="utf-8")
    (data_path / CONFIG_FILENAME).write_text("{}", encoding="utf-8")

    with pytest.raises(InvalidDataRootError) as failure:
        open_existing(data_path)
    assert MARKER_FILENAME not in str(failure.value)
    assert user_message(str(failure.value)) != str(failure.value)


def test_data_root_failures_have_chinese_user_messages(data_path):
    data_path.mkdir()
    (data_path / "unrelated.txt").write_text("keep", encoding="utf-8")
    failures = []

    with pytest.raises(InvalidDataRootError) as missing_marker:
        open_existing(data_path)
    failures.append(str(missing_marker.value))

    _write_metadata(data_path, MARKER_FILENAME)
    with pytest.raises(InvalidDataRootError) as missing_config:
        open_existing(data_path)
    failures.append(str(missing_config.value))

    for message in failures:
        assert user_message(message) != message, message


def test_open_rejects_wrong_application_marker(data_path):
    data_path.mkdir()
    (data_path / MARKER_FILENAME).write_text(
        json.dumps({"application": "Other", "data_format_version": 1}), encoding="utf-8"
    )

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)


def _write_metadata(root, filename, **overrides):
    metadata = {
        "application": "TrainingFeedback",
        "config_version": 1,
        "data_format_version": 1,
    }
    metadata.update(overrides)
    (root / filename).write_text(json.dumps(metadata), encoding="utf-8")


def test_open_rejects_future_marker_format_version(data_path):
    create_new(data_path)
    _write_metadata(data_path, MARKER_FILENAME, data_format_version=999)
    marker_bytes = (data_path / MARKER_FILENAME).read_bytes()

    with pytest.raises(UnsupportedDataFormatError):
        open_existing(data_path)
    assert (data_path / MARKER_FILENAME).read_bytes() == marker_bytes


def test_open_rejects_invalid_marker_format_version(data_path):
    create_new(data_path)
    _write_metadata(data_path, MARKER_FILENAME, data_format_version="1")

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)


def test_open_rejects_missing_config(data_path):
    data_path.mkdir()
    _write_metadata(data_path, MARKER_FILENAME)

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)


def test_open_rejects_missing_config_version(data_path):
    create_new(data_path)
    config = json.loads((data_path / CONFIG_FILENAME).read_text(encoding="utf-8"))
    del config["config_version"]
    (data_path / CONFIG_FILENAME).write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)


def test_open_rejects_wrong_type_config_version(data_path):
    create_new(data_path)
    _write_metadata(data_path, CONFIG_FILENAME, config_version="1")

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)


def test_open_rejects_future_config_version(data_path):
    create_new(data_path)
    _write_metadata(data_path, CONFIG_FILENAME, config_version=999)
    config_bytes = (data_path / CONFIG_FILENAME).read_bytes()

    with pytest.raises(UnsupportedDataFormatError):
        open_existing(data_path)
    assert (data_path / CONFIG_FILENAME).read_bytes() == config_bytes


def test_open_rejects_corrupt_database(data_path):
    create_new(data_path)
    (data_path / DATABASE_FILENAME).write_bytes(b"not a sqlite database")

    with pytest.raises(InvalidDataRootError):
        open_existing(data_path)


def test_open_rejects_future_schema_without_modifying_database(data_path):
    create_new(data_path)
    connection = sqlite3.connect(data_path / DATABASE_FILENAME)
    try:
        connection.execute(
            "INSERT INTO schema_migration(version, applied_at) VALUES (999, 'future')"
        )
        connection.commit()
    finally:
        connection.close()
    database_bytes = (data_path / DATABASE_FILENAME).read_bytes()

    with pytest.raises(UnsupportedDataFormatError):
        open_existing(data_path)
    assert (data_path / DATABASE_FILENAME).read_bytes() == database_bytes
