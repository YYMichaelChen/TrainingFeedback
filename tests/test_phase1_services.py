import json

import pytest

from training_feedback.bootstrap import choose_data_root, open_from_locator
from training_feedback.data.backup import BackupError, create_backup
from training_feedback.data.data_root import create_new
from training_feedback.data.locator import Locator


def test_locator_round_trip_and_invalid_locator(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    root = tmp_path / "data"
    locator.save(root)
    assert locator.load() == root

    (tmp_path / "locator.json").write_text("not json", encoding="utf-8")
    assert locator.load() is None


def test_open_from_invalid_locator_returns_none(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    locator.save(tmp_path / "missing")
    assert open_from_locator(locator) is None


def test_choose_data_root_can_create_and_cancel(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    root = tmp_path / "data"
    context = choose_data_root(locator, lambda: (root, True))
    assert context is not None
    context.close()
    assert locator.load() == root

    assert choose_data_root(locator, lambda: None) is None


def test_backup_copies_complete_root_and_rejects_unsafe_destinations(tmp_path):
    source = tmp_path / "source"
    create_new(source)
    (source / "exports" / "evidence.txt").write_text("original", encoding="utf-8")
    destination = tmp_path / "backup"
    create_backup(source, destination)
    assert (destination / "training_feedback.sqlite3").is_file()
    assert (destination / "exports" / "evidence.txt").read_text(encoding="utf-8") == "original"

    with pytest.raises(BackupError):
        create_backup(source, source / "nested")
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep").write_text("keep", encoding="utf-8")
    with pytest.raises(BackupError):
        create_backup(source, occupied)


def test_locator_contains_only_data_root(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    locator.save(tmp_path / "data")
    assert json.loads((tmp_path / "locator.json").read_text(encoding="utf-8")) == {
        "data_root": str(tmp_path / "data")
    }


def test_backup_uses_online_backup_for_open_database(tmp_path):
    """带活动连接时数据库文件走 SQLite 在线备份，且备份库可正常打开。"""
    import sqlite3

    from training_feedback.app import ApplicationContext
    from training_feedback.data.data_root import DATABASE_FILENAME

    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    destination = tmp_path / "backup"
    create_backup(context.data_root.path, destination, context.database.connection)
    context.close()
    backup_connection = sqlite3.connect(destination / DATABASE_FILENAME)
    try:
        version = backup_connection.execute(
            "SELECT MAX(version) FROM schema_migration"
        ).fetchone()[0]
        assert version >= 1
        assert backup_connection.execute("SELECT COUNT(*) FROM exercise").fetchone()[0] == 14
    finally:
        backup_connection.close()
