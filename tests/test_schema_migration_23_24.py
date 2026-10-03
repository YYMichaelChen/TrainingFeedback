"""Focused synthetic checks for the in-place schema 23 to 24 migration."""

import sqlite3

import pytest

from training_feedback.data.migrations import apply_migrations


def _schema23_connection():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE schema_migration(version INTEGER NOT NULL, applied_at TEXT NOT NULL);
        INSERT INTO schema_migration VALUES (23, 'synthetic');
        CREATE TABLE group_plan_day(id INTEGER PRIMARY KEY, day_order INTEGER, name TEXT);
        CREATE TABLE training_plan_day(id INTEGER PRIMARY KEY, day_order INTEGER, name TEXT);
        CREATE TABLE training_session(id INTEGER PRIMARY KEY, plan_day_order INTEGER,
                                      plan_day_name_snapshot TEXT);
        CREATE TABLE group_plan(id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE group_session_feedback(id INTEGER PRIMARY KEY, note TEXT);
        CREATE TABLE library_review_event(id INTEGER PRIMARY KEY, note TEXT);
        CREATE TABLE conversion_original(id INTEGER PRIMARY KEY, evidence_json TEXT);
        INSERT INTO group_plan_day VALUES (1, 1, 'synthetic day');
        INSERT INTO training_plan_day VALUES (2, 2, 'synthetic day');
        INSERT INTO training_session VALUES (3, 2, 'synthetic day');
        INSERT INTO group_plan VALUES (4, 'synthetic plan');
        INSERT INTO group_session_feedback VALUES (5, 'verbatim feedback');
        INSERT INTO library_review_event VALUES (6, 'verbatim review');
        INSERT INTO conversion_original VALUES (7, '{"synthetic":"evidence"}');
        """
    )
    return connection


def test_schema23_upgrade_drops_only_training_day_name_columns_and_preserves_rows():
    connection = _schema23_connection()

    apply_migrations(connection)

    assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 24
    for table, expected in (
        ("group_plan_day", (1, 1)),
        ("training_plan_day", (2, 2)),
        ("training_session", (3, 2)),
    ):
        columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
        assert "name" not in columns
        assert "plan_day_name_snapshot" not in columns
        assert connection.execute(f"SELECT * FROM {table}").fetchone()[:2] == expected
    assert connection.execute("SELECT * FROM group_plan").fetchone() == (4, "synthetic plan")
    assert connection.execute("SELECT * FROM group_session_feedback").fetchone() == (
        5, "verbatim feedback",
    )
    assert connection.execute("SELECT * FROM library_review_event").fetchone() == (
        6, "verbatim review",
    )
    assert connection.execute("SELECT evidence_json FROM conversion_original").fetchone()[0] == (
        '{"synthetic":"evidence"}'
    )


def test_schema23_upgrade_rolls_back_all_column_changes_when_version_write_fails():
    connection = _schema23_connection()
    connection.executescript(
        """CREATE TRIGGER fail_schema24 BEFORE INSERT ON schema_migration
           WHEN NEW.version = 24 BEGIN SELECT RAISE(ABORT, 'synthetic migration failure'); END;"""
    )

    with pytest.raises(sqlite3.IntegrityError, match="synthetic migration failure"):
        apply_migrations(connection)

    assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 23
    assert "name" in [row[1] for row in connection.execute("PRAGMA table_info(group_plan_day)")]
    assert "name" in [row[1] for row in connection.execute("PRAGMA table_info(training_plan_day)")]
    assert "plan_day_name_snapshot" in [
        row[1] for row in connection.execute("PRAGMA table_info(training_session)")
    ]
