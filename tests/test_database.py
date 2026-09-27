import sqlite3
from pathlib import Path

import pytest

from training_feedback.data.database import Database
from training_feedback.data.migrations import ExpiredSchemaError


def test_transaction_commits_and_rolls_back(tmp_path):
    database = Database(tmp_path / "test.sqlite3")
    with database as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        with database.transaction():
            connection.execute("INSERT INTO sample(value) VALUES ('committed')")
        values = [tuple(row) for row in connection.execute("SELECT value FROM sample").fetchall()]
        assert values == [("committed",)]

        with pytest.raises(RuntimeError):
            with database.transaction():
                connection.execute("INSERT INTO sample(value) VALUES ('rolled back')")
                raise RuntimeError("test failure")
        values = [tuple(row) for row in connection.execute("SELECT value FROM sample").fetchall()]
        assert values == [("committed",)]


def test_database_prevents_multiple_active_sessions(tmp_path):
    database = Database(tmp_path / "test.sqlite3")
    with database as connection:
        connection.execute(
            "INSERT INTO training_plan(name, created_at) VALUES ('test-plan', 'now')"
        )
        plan_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        connection.execute(
            "INSERT INTO training_plan_revision(plan_id, revision_number, status, created_at) "
            "VALUES (?, 1, 'active', 'now')",
            (plan_id,),
        )
        revision_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        values = (revision_id, "2026-09-07", "open", "now", "now")
        connection.execute(
            "INSERT INTO training_session(plan_revision_id, training_date, status, "
            "started_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            values,
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO training_session(plan_revision_id, training_date, status, "
                "started_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                values,
            )


def test_below_window_root_is_refused_without_remigration(tmp_path):
    """Tampering a root below schema 22 must fail closed at the migration entry."""
    path = tmp_path / "test.sqlite3"
    with Database(path) as connection:
        connection.execute(
            "INSERT INTO training_plan(name, created_at) VALUES ('legacy', 'now')"
        )
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE schema_migration SET version=21 WHERE version=23")
        connection.commit()
    database_bytes = Path(path).read_bytes()

    with pytest.raises(ExpiredSchemaError, match="older than the supported window"):
        with Database(path):
            pass

    assert Path(path).read_bytes() == database_bytes
