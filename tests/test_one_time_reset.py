"""Expired schema-22 refusal and retained schema-23 cleanup recovery."""

import json
import sqlite3

import pytest

from training_feedback.data.data_root import (
    DATABASE_FILENAME,
    DataRootAccessError,
    ExpiredDataRootError,
    create_new,
    open_existing,
)
from training_feedback.data.library_root import initialize_library_root
from training_feedback.data.one_time_reset import ResetRecoveryError


def _root(path):
    create_new(path)
    initialize_library_root(path)
    return path / DATABASE_FILENAME


def test_schema22_root_is_refused_without_writes(tmp_path):
    root = tmp_path / "expired"
    database = _root(root)
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE schema_migration SET version=22 WHERE version=23")
    before = database.read_bytes()
    lock_before = (root / ".training-feedback.lock").read_bytes()
    with pytest.raises(ExpiredDataRootError):
        open_existing(root)
    assert database.read_bytes() == before
    assert (root / ".training-feedback.lock").read_bytes() == lock_before


def test_schema23_pending_reset_cleanup_resumes(tmp_path, monkeypatch):
    from training_feedback.data import one_time_reset

    root = tmp_path / "pending"
    database = _root(root)
    (root / "backups" / "obsolete.zip").write_bytes(b"synthetic")
    (root / "exports" / "obsolete.json").write_text("synthetic", encoding="utf-8")
    inventory = ["backups/obsolete.zip", "exports/obsolete.json"]
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO one_time_reset_journal(id,operation,path_inventory_json,created_at) "
            "VALUES (1,'reset-v0.7.5',?,'synthetic')", (json.dumps(inventory),),
        )
    delete_path = one_time_reset._delete_path
    calls = 0

    def fail_after_one(root_path, relative):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ResetRecoveryError("injected cleanup failure")
        delete_path(root_path, relative)

    monkeypatch.setattr(one_time_reset, "_delete_path", fail_after_one)
    with pytest.raises(DataRootAccessError):
        open_existing(root)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM one_time_reset_journal").fetchone()[0] == 1
    monkeypatch.setattr(one_time_reset, "_delete_path", delete_path)
    assert open_existing(root).path == root
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM one_time_reset_journal").fetchone()[0] == 0
    assert not (root / "backups" / "obsolete.zip").exists()
    assert not (root / "exports" / "obsolete.json").exists()
