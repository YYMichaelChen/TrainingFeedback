"""Only the two root-opening risks introduced by schema25; no feature checks."""

import sqlite3
from pathlib import Path

from training_feedback.app import LibraryContext
from training_feedback.data.database import Database
from training_feedback.ui.chinese import install_chinese


def test_new_root_initialization_has_required_edit_storage(tmp_path, qt_app):
    install_chinese(qt_app)
    with LibraryContext.create(tmp_path / "synthetic-new") as context:
        connection = context.database.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 25
        assert connection.execute("SELECT COUNT(*) FROM plan_edit_document").fetchone()[0] == 0


def test_schema24_root_open_installs_edit_storage(tmp_path):
    path = tmp_path / "synthetic-schema24.sqlite3"
    schema = Path("src/training_feedback/data/schema24.sql").read_text(encoding="utf-8")
    with sqlite3.connect(path) as connection:
        connection.executescript(schema)
        connection.execute(
            "INSERT INTO schema_migration(version,applied_at) VALUES (24,'synthetic')")
    with Database(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 25
        assert connection.execute("SELECT COUNT(*) FROM plan_edit_document").fetchone()[0] == 0
