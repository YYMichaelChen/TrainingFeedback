"""The explicit schema22 reset is atomic and resumes managed-file cleanup."""

import json
import sqlite3
from pathlib import Path

import pytest

from training_feedback.data.data_root import (
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    DataRootAccessError,
    InvalidDataRootError,
    create_new,
    open_existing,
)
from training_feedback.data.library_root import initialize_library_root
from training_feedback.data.one_time_reset import ResetRecoveryError


def _schema22_root(path):
    create_new(path)
    database = path / DATABASE_FILENAME
    database.unlink()
    with sqlite3.connect(database) as connection:
        schema = Path(__file__).resolve().parents[1] / "src/training_feedback/data/schema22.sql"
        connection.executescript(schema.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO schema_migration(version,applied_at) VALUES (22,'unknown')"
        )
    initialize_library_root(path)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO body_area(id,name,active) VALUES (1,'保留区域',1)"
        )
        connection.execute(
            "INSERT INTO library_reference VALUES (1,'custom','保留动作','unknown')"
        )
        connection.execute(
            "INSERT INTO training_plan(id,name,created_at) VALUES (1,'旧计划','unknown')"
        )
        connection.execute("INSERT INTO group_plan(id,name,created_at) "
                           "VALUES (1,'旧分组计划','unknown')")
        connection.execute(
            "INSERT INTO group_plan_revision(id,plan_id,revision_number,status,name,purpose,"
            "rationale,source_json,created_at) "
            "VALUES (1,1,1,'draft','旧分组计划','','','null','unknown')"
        )

    (path / "backups").mkdir(exist_ok=True)
    (path / "backups" / "whole-root.zip").write_bytes(b"synthetic backup")
    (path / "exports" / "export.json").write_text("synthetic export", encoding="utf-8")
    (path / "imports" / "source.json").write_text("synthetic import", encoding="utf-8")
    (path / "exercise-images" / "keep.png").write_bytes(b"library image")
    (path / "reviews").mkdir()
    (path / "reviews" / "keep.json").write_text("review evidence", encoding="utf-8")
    return database


def test_schema22_open_resets_plans_and_training_and_retains_library(tmp_path):
    root = tmp_path / "reset root"
    database = _schema22_root(root)

    opened = open_existing(root)

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 23
        for table in (
            "training_plan", "training_plan_revision", "group_plan", "group_plan_revision",
            "group_session", "training_session", "plan_import", "ai_export",
        ):
            assert connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0
        assert (
            connection.execute("SELECT name FROM body_area WHERE id=1").fetchone()[0]
            == "保留区域"
        )
        assert connection.execute(
            "SELECT stable_key FROM library_reference WHERE id=1"
        ).fetchone()[0] == "保留动作"
        assert connection.execute("SELECT COUNT(*) FROM one_time_reset_journal").fetchone()[0] == 0

    assert opened.path == root
    assert not (root / "backups" / "whole-root.zip").exists()
    assert not (root / "exports" / "export.json").exists()
    assert not (root / "imports" / "source.json").exists()
    assert (root / "exercise-images" / "keep.png").read_bytes() == b"library image"
    assert (root / "reviews" / "keep.json").read_text(encoding="utf-8") == "review evidence"
    assert json.loads((root / CONFIG_FILENAME).read_text(encoding="utf-8"))["library_model"]


def test_schema22_reset_rolls_back_before_commit(tmp_path, monkeypatch):
    from training_feedback.data import one_time_reset

    root = tmp_path / "reset root"
    database = _schema22_root(root)
    before = database.read_bytes()

    def fail_script(_script):
        raise RuntimeError("injected before commit")

    monkeypatch.setattr(one_time_reset, "_sql_statements", fail_script)
    with pytest.raises(Exception):
        open_existing(root)

    assert database.read_bytes() == before
    assert (root / "backups" / "whole-root.zip").read_bytes() == b"synthetic backup"
    with sqlite3.connect(database) as connection:
        assert (
            connection.execute("SELECT name FROM training_plan WHERE id=1").fetchone()[0]
            == "旧计划"
        )


def test_incomplete_schema22_root_is_rejected_unchanged_before_file_cleanup(tmp_path):
    root = tmp_path / "incomplete root"
    database = _schema22_root(root)
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("DROP TABLE training_session")
    before = database.read_bytes()
    backup = (root / "backups" / "whole-root.zip").read_bytes()

    with pytest.raises(InvalidDataRootError):
        open_existing(root)

    assert database.read_bytes() == before
    assert (root / "backups" / "whole-root.zip").read_bytes() == backup


def test_schema22_reset_resumes_file_cleanup_after_commit(tmp_path, monkeypatch):
    from training_feedback.data import one_time_reset

    root = tmp_path / "reset root"
    database = _schema22_root(root)
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
        assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 23
        assert connection.execute("SELECT COUNT(*) FROM training_plan").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM one_time_reset_journal").fetchone()[0] == 1

    monkeypatch.setattr(one_time_reset, "_delete_path", delete_path)
    assert open_existing(root).path == root
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM one_time_reset_journal").fetchone()[0] == 0
    assert not any(
        any((root / name).rglob("*")) for name in ("backups", "exports", "imports")
    )
