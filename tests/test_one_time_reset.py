"""Unsupported schema and unfinished historical reset are refused unchanged."""

import json
import sqlite3
from contextlib import closing

import pytest

from training_feedback.data.data_root import (
    DATABASE_FILENAME,
    DataRootAccessError,
    ExpiredDataRootError,
    create_new,
    open_existing,
)
from training_feedback.data.library_root import initialize_library_root


def _root(path):
    create_new(path)
    initialize_library_root(path)
    return path / DATABASE_FILENAME


def test_schema22_root_is_refused_without_writes(tmp_path):
    root = tmp_path / "expired"
    database = _root(root)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("UPDATE schema_migration SET version=22 WHERE version=23")
        connection.commit()
    before = database.read_bytes()
    lock_before = (root / ".training-feedback.lock").read_bytes()
    with pytest.raises(ExpiredDataRootError):
        open_existing(root)
    assert database.read_bytes() == before
    assert (root / ".training-feedback.lock").read_bytes() == lock_before


def test_pending_historical_reset_is_refused_without_writes(tmp_path):
    root = tmp_path / "pending"
    database = _root(root)
    (root / "backups" / "obsolete.zip").write_bytes(b"synthetic")
    (root / "exports" / "obsolete.json").write_text("synthetic", encoding="utf-8")
    inventory = ["backups/obsolete.zip", "exports/obsolete.json"]
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO one_time_reset_journal(id,operation,path_inventory_json,created_at) "
            "VALUES (1,'reset-v0.7.5',?,'synthetic')", (json.dumps(inventory),),
        )
        connection.commit()
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with pytest.raises(DataRootAccessError, match="unfinished historical reset"):
        open_existing(root)
    after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert after == before


@pytest.mark.parametrize("journal", ["invalid", '{"version":999}',
    '{"format":"training_feedback.upgrade-recovery","version":1,"phase":"converting"}'])
def test_unfinished_or_unknown_upgrade_is_refused_unchanged(tmp_path, journal):
    root = tmp_path / "unfinished"
    _root(root)
    (root / ".training-feedback-upgrade.json").write_text(journal, encoding="utf-8")
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with pytest.raises(DataRootAccessError, match="unfinished historical upgrade"):
        open_existing(root)
    assert {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
