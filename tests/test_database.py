import sqlite3

import pytest

from training_feedback.data.database import Database


def test_database_enables_foreign_keys_and_migrates(tmp_path):
    database = Database(tmp_path / "test.sqlite3")
    with database as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 13
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'exercise'"
        ).fetchone()


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


def test_immediate_transaction_commits(tmp_path):
    database = Database(tmp_path / "test.sqlite3")
    with database as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        with database.transaction(immediate=True):
            connection.execute("INSERT INTO sample(value) VALUES ('immediate')")
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "immediate"


def test_foreign_keys_are_enforced(tmp_path):
    database = Database(tmp_path / "test.sqlite3")
    with database as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO exercise_alias(exercise_id, alias) VALUES (999, 'alias')"
            )


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


def test_migrations_are_idempotent_after_reopen(tmp_path):
    path = tmp_path / "test.sqlite3"
    with Database(path):
        pass
    with Database(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migration").fetchone()[0] == 13


def test_legacy_area_snapshot_migration_does_not_infer_roles(tmp_path):
    path = tmp_path / "test.sqlite3"
    with Database(path) as connection:
        connection.execute(
            "INSERT INTO training_plan(name, created_at) VALUES ('legacy', 'now')"
        )
        plan_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        connection.execute(
            "INSERT INTO training_plan_revision(plan_id, revision_number, status, created_at) "
            "VALUES (?, 1, 'active', 'now')",
            (plan_id,),
        )
        revision_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        connection.execute(
            "INSERT INTO training_session(plan_revision_id, training_date, status, "
            "started_at, updated_at) VALUES (?, '2026-09-05', 'completed', "
            "'2026-09-05T10:00:00+00:00', '2026-09-05T10:00:00+00:00')",
            (revision_id,),
        )
        session_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        connection.execute(
            "INSERT INTO training_session_action(session_id, action_order, plan_day_order, "
            "plan_action_order, exercise_name_snapshot, body_areas_snapshot_json) "
            "VALUES (?, 1, 1, 1, 'legacy', ?)",
            (session_id, '["臀部", "核心"]'),
        )
        connection.execute(
            "DELETE FROM schema_migration WHERE version IN (8, 9, 10, 11, 12, 13)"
        )
        connection.commit()
    with Database(path) as connection:
        snapshot = connection.execute(
            "SELECT body_areas_snapshot_json FROM training_session_action"
        ).fetchone()[0]
        assert snapshot == (
            '[{"name": "臀部", "is_primary": null}, '
            '{"name": "核心", "is_primary": null}]'
        )
