"""SQLite 版本化 schema 迁移。

约定：
- 每个 ``_migration_N`` 只描述该版本的变更内容，不含事务代码；
  事务边界与版本登记由 ``_apply`` 统一处理（失败整体回滚）。
- 迁移只追加新版本、绝不修改历史版本，保证已有用户数据库可顺序升级。
- 例外：v1 用 executescript 执行整段建表脚本（executescript 会先隐式提交，
  无法放进外层事务），其事务边界由脚本内的 BEGIN 与调用方的 commit 控制。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Callable

LATEST_SCHEMA_VERSION = 13


class FutureSchemaError(sqlite3.DatabaseError):
    """Raised when the database schema is newer than this application."""


def _migration_1(connection: sqlite3.Connection) -> None:
    connection.executescript("""
    BEGIN;
    CREATE TABLE exercise (
        id INTEGER PRIMARY KEY,
        canonical_name TEXT NOT NULL UNIQUE,
        active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE exercise_alias (
        id INTEGER PRIMARY KEY,
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        alias TEXT NOT NULL UNIQUE
    );
    CREATE TABLE exercise_guidance_revision (
        id INTEGER PRIMARY KEY,
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        revision_number INTEGER NOT NULL,
        guidance_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (exercise_id, revision_number)
    );
    CREATE TABLE body_area (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
    );
    CREATE TABLE exercise_body_area (
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        body_area_id INTEGER NOT NULL REFERENCES body_area(id),
        is_primary INTEGER NOT NULL CHECK (is_primary IN (0, 1)),
        PRIMARY KEY (exercise_id, body_area_id)
    );
    CREATE TABLE training_plan (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        -- 故意不加 REFERENCES：training_plan 与 training_plan_revision 互相引用，
        -- 循环外键无法在建表时表达，由激活流程保证指向有效版本。
        active_revision_id INTEGER,
        created_at TEXT NOT NULL
    );
    CREATE TABLE training_plan_revision (
        id INTEGER PRIMARY KEY,
        plan_id INTEGER NOT NULL REFERENCES training_plan(id),
        revision_number INTEGER NOT NULL,
        status TEXT NOT NULL,
        purpose TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        UNIQUE (plan_id, revision_number)
    );
    CREATE TABLE training_plan_day (
        id INTEGER PRIMARY KEY,
        revision_id INTEGER NOT NULL REFERENCES training_plan_revision(id),
        day_order INTEGER NOT NULL,
        name TEXT NOT NULL,
        UNIQUE (revision_id, day_order)
    );
    CREATE TABLE training_plan_action (
        id INTEGER PRIMARY KEY,
        day_id INTEGER NOT NULL REFERENCES training_plan_day(id),
        exercise_id INTEGER NOT NULL REFERENCES exercise(id),
        action_order INTEGER NOT NULL,
        phase TEXT NOT NULL,
        rest_seconds INTEGER,
        note TEXT NOT NULL DEFAULT '',
        UNIQUE (day_id, action_order)
    );
    CREATE TABLE training_plan_set (
        id INTEGER PRIMARY KEY,
        action_id INTEGER NOT NULL REFERENCES training_plan_action(id),
        set_order INTEGER NOT NULL,
        value REAL,
        unit TEXT NOT NULL,
        per_side INTEGER NOT NULL DEFAULT 0 CHECK (per_side IN (0, 1)),
        UNIQUE (action_id, set_order)
    );
    CREATE TABLE training_session (
        id INTEGER PRIMARY KEY,
        plan_revision_id INTEGER NOT NULL REFERENCES training_plan_revision(id),
        training_date TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        finished_at TEXT,
        abort_reason TEXT,
        abort_note TEXT
    );
    CREATE TABLE training_session_action (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES training_session(id),
        action_order INTEGER NOT NULL,
        exercise_name_snapshot TEXT NOT NULL,
        body_areas_snapshot_json TEXT NOT NULL,
        guidance_revision_id INTEGER,
        result TEXT,
        note TEXT,
        UNIQUE (session_id, action_order)
    );
    CREATE TABLE training_session_set (
        id INTEGER PRIMARY KEY,
        session_action_id INTEGER NOT NULL REFERENCES training_session_action(id),
        set_order INTEGER NOT NULL,
        planned_value REAL,
        planned_unit TEXT NOT NULL,
        planned_per_side INTEGER NOT NULL CHECK (planned_per_side IN (0, 1)),
        actual_value REAL,
        actual_unit TEXT,
        actual_per_side INTEGER,
        UNIQUE (session_action_id, set_order)
    );
    CREATE TABLE session_event (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES training_session(id),
        event_type TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        reason TEXT,
        note TEXT
    );
    CREATE TABLE next_day_feedback (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL UNIQUE REFERENCES training_session(id),
        overall_note TEXT,
        submitted_at TEXT NOT NULL
    );
    CREATE TABLE next_day_feedback_area (
        id INTEGER PRIMARY KEY,
        feedback_id INTEGER NOT NULL REFERENCES next_day_feedback(id),
        body_area_name_snapshot TEXT NOT NULL,
        value TEXT,
        UNIQUE (feedback_id, body_area_name_snapshot)
    );
    CREATE TABLE ai_export (
        id INTEGER PRIMARY KEY,
        session_id INTEGER REFERENCES training_session(id),
        format TEXT NOT NULL,
        file_path TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE plan_import (
        id INTEGER PRIMARY KEY,
        source_path TEXT NOT NULL,
        rationale TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)


def _migration_2(connection: sqlite3.Connection) -> None:
    connection.execute("ALTER TABLE exercise ADD COLUMN category TEXT NOT NULL DEFAULT 'general'")
    connection.execute("ALTER TABLE exercise ADD COLUMN equipment_summary TEXT NOT NULL DEFAULT ''")


def _migration_3(connection: sqlite3.Connection) -> None:
    connection.execute(
        "ALTER TABLE exercise ADD COLUMN active_guidance_revision_id INTEGER "
        "REFERENCES exercise_guidance_revision(id)"
    )


def _migration_4(connection: sqlite3.Connection) -> None:
    connection.execute("ALTER TABLE training_plan_set ADD COLUMN note TEXT NOT NULL DEFAULT ''")


def _migration_5(connection: sqlite3.Connection) -> None:
    connection.execute(
        "ALTER TABLE training_session_action ADD COLUMN exercise_id INTEGER "
        "REFERENCES exercise(id)"
    )


def _migration_6(connection: sqlite3.Connection) -> None:
    connection.execute(
        "ALTER TABLE training_session_action ADD COLUMN plan_day_order INTEGER "
        "NOT NULL DEFAULT 1"
    )
    connection.execute(
        "CREATE UNIQUE INDEX training_session_action_session_day_order "
        "ON training_session_action(session_id, plan_day_order, action_order)"
    )


def _migration_7(connection: sqlite3.Connection) -> None:
    connection.execute(
        "ALTER TABLE training_session_action ADD COLUMN plan_action_order INTEGER "
        "NOT NULL DEFAULT 1"
    )
    connection.execute(
        "UPDATE training_session_action SET plan_action_order = action_order"
    )
    connection.execute(
        "CREATE UNIQUE INDEX training_session_action_plan_position "
        "ON training_session_action(session_id, plan_day_order, plan_action_order)"
    )


def _migration_8(connection: sqlite3.Connection) -> None:
    """把旧的纯文本部位快照升级为结构化快照，并创建备注修正审计表。"""
    rows = connection.execute(
        "SELECT id, body_areas_snapshot_json FROM training_session_action"
    ).fetchall()
    for row in rows:
        snapshot = json.loads(row["body_areas_snapshot_json"])
        if not isinstance(snapshot, list):
            raise sqlite3.DatabaseError("Invalid session body-area snapshot.")
        if all(isinstance(item, dict) for item in snapshot):
            continue
        if not all(isinstance(item, str) for item in snapshot):
            raise sqlite3.DatabaseError("Invalid session body-area snapshot.")
        migrated = [{"name": item, "is_primary": None} for item in snapshot]
        connection.execute(
            "UPDATE training_session_action SET body_areas_snapshot_json = ? WHERE id = ?",
            (json.dumps(migrated, ensure_ascii=False), row["id"]),
        )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS note_correction_audit (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES training_session(id),
            feedback_id INTEGER REFERENCES next_day_feedback(id),
            session_action_id INTEGER REFERENCES training_session_action(id),
            target TEXT NOT NULL,
            old_value TEXT NOT NULL,
            new_value TEXT NOT NULL,
            corrected_at TEXT NOT NULL,
            operation TEXT NOT NULL
        )
        """
    )


def _migration_9(connection: sqlite3.Connection) -> None:
    """把外部导入记录关联到来源会话、草稿版本与确认信息。"""
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(plan_import)")
    }
    additions = {
        "plan_id": "INTEGER REFERENCES training_plan(id)",
        "revision_id": "INTEGER REFERENCES training_plan_revision(id)",
        "previous_revision_id": "INTEGER REFERENCES training_plan_revision(id)",
        "source_session_id": "INTEGER REFERENCES training_session(id)",
        "source_export_id": "INTEGER REFERENCES ai_export(id)",
        "confirmed_at": "TEXT",
    }
    for name, definition in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE plan_import ADD COLUMN {name} {definition}")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS plan_import_revision ON plan_import(revision_id) "
        "WHERE revision_id IS NOT NULL"
    )


def _migration_10(connection: sqlite3.Connection) -> None:
    """在会话中冻结所选训练日与处方事实（之后的目录/计划编辑不影响历史）。"""
    additions = {
        "training_session": {
            "plan_day_order": "INTEGER NOT NULL DEFAULT 1",
            "plan_day_name_snapshot": "TEXT NOT NULL DEFAULT ''",
        },
        "training_session_action": {
            "phase_snapshot": "TEXT NOT NULL DEFAULT 'main'",
            # 领域层允许小数休息秒数，因此快照用 REAL（计划侧仍是 INTEGER）。
            "rest_seconds_snapshot": "REAL NOT NULL DEFAULT 0",
            "plan_note_snapshot": "TEXT NOT NULL DEFAULT ''",
        },
        "training_session_set": {
            "plan_note_snapshot": "TEXT NOT NULL DEFAULT ''",
        },
    }
    for table, table_additions in additions.items():
        columns = {
            row["name"] for row in connection.execute(f"PRAGMA table_info({table})")
        }
        for name, definition in table_additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def _migration_11(connection: sqlite3.Connection) -> None:
    """约束同时只有一个活跃会话，并用触发器保证已发布计划版本不可变。"""
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS one_active_training_session "
        "ON training_session((1)) WHERE status IN ('open', 'paused')"
    )
    connection.executescript(
        """
        CREATE TRIGGER IF NOT EXISTS immutable_plan_revision_content
        BEFORE UPDATE ON training_plan_revision
        WHEN OLD.status != 'draft' AND (
            NEW.plan_id != OLD.plan_id OR
            NEW.revision_number != OLD.revision_number OR
            NEW.purpose != OLD.purpose OR
            NEW.created_at != OLD.created_at
        )
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_plan_revision_delete
        BEFORE DELETE ON training_plan_revision
        WHEN OLD.status != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS draft_plan_day_only
        BEFORE INSERT ON training_plan_day
        WHEN (SELECT status FROM training_plan_revision WHERE id = NEW.revision_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS draft_plan_action_only
        BEFORE INSERT ON training_plan_action
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              WHERE d.id = NEW.day_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS draft_plan_set_only
        BEFORE INSERT ON training_plan_set
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              JOIN training_plan_action a ON a.day_id = d.id
              WHERE a.id = NEW.action_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_plan_day_update
        BEFORE UPDATE ON training_plan_day
        WHEN (SELECT status FROM training_plan_revision WHERE id = OLD.revision_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_plan_action_update
        BEFORE UPDATE ON training_plan_action
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              WHERE d.id = OLD.day_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_plan_set_update
        BEFORE UPDATE ON training_plan_set
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              JOIN training_plan_action a ON a.day_id = d.id
              WHERE a.id = OLD.action_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_plan_day_delete
        BEFORE DELETE ON training_plan_day
        WHEN (SELECT status FROM training_plan_revision WHERE id = OLD.revision_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_plan_action_delete
        BEFORE DELETE ON training_plan_action
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              WHERE d.id = OLD.day_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_plan_set_delete
        BEFORE DELETE ON training_plan_set
        WHEN (SELECT r.status FROM training_plan_revision r
              JOIN training_plan_day d ON d.revision_id = r.id
              JOIN training_plan_action a ON a.day_id = d.id
              WHERE a.id = OLD.action_id) != 'draft'
        BEGIN
            SELECT RAISE(ABORT, 'Published plan revisions are immutable.');
        END;
        """
    )


def _migration_12(connection: sqlite3.Connection) -> None:
    """新增独立存放实际完成组的表，不再挤占计划组行。"""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS training_session_actual_set (
            id INTEGER PRIMARY KEY,
            session_action_id INTEGER NOT NULL
                REFERENCES training_session_action(id),
            actual_order INTEGER NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            per_side INTEGER NOT NULL CHECK (per_side IN (0, 1)),
            UNIQUE (session_action_id, actual_order)
        )
        """
    )


def _migration_13(connection: sqlite3.Connection) -> None:
    """Persist future bundled-content identity without inventing it for old rows."""
    exercise_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(exercise)")
    }
    if "bundled_exercise_key" not in exercise_columns:
        connection.execute("ALTER TABLE exercise ADD COLUMN bundled_exercise_key TEXT")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS bundled_exercise_identity "
        "ON exercise(bundled_exercise_key) WHERE bundled_exercise_key IS NOT NULL"
    )
    revision_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(exercise_guidance_revision)")
    }
    if "bundled_content_id" not in revision_columns:
        connection.execute(
            "ALTER TABLE exercise_guidance_revision ADD COLUMN bundled_content_id TEXT"
        )
    if "bundled_content_version" not in revision_columns:
        connection.execute(
            "ALTER TABLE exercise_guidance_revision ADD COLUMN bundled_content_version INTEGER "
            "CHECK (bundled_content_version IS NULL OR bundled_content_version > 0)"
        )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS bundled_guidance_delivery "
        "ON exercise_guidance_revision("
        "exercise_id, bundled_content_id, bundled_content_version) "
        "WHERE bundled_content_id IS NOT NULL AND bundled_content_version IS NOT NULL"
    )


# 版本号从 1 开始连续递增；新增迁移时追加条目并同步 LATEST_SCHEMA_VERSION。
_MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {
    2: _migration_2,
    3: _migration_3,
    4: _migration_4,
    5: _migration_5,
    6: _migration_6,
    7: _migration_7,
    8: _migration_8,
    9: _migration_9,
    10: _migration_10,
    11: _migration_11,
    12: _migration_12,
    13: _migration_13,
}


def _record_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(
        "INSERT INTO schema_migration(version, applied_at) VALUES (?, ?)",
        (version, datetime.now(UTC).isoformat()),
    )


def _apply(
    connection: sqlite3.Connection,
    version: int,
    body: Callable[[sqlite3.Connection], None],
) -> None:
    """统一的事务边界：执行单个版本变更、登记版本，失败整体回滚。"""
    try:
        connection.execute("BEGIN")
        body(connection)
        _record_version(connection, version)
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def apply_migrations(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migration "
        "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    connection.commit()
    current = connection.execute(
        "SELECT COALESCE(MAX(version), 0) FROM schema_migration"
    ).fetchone()[0]
    if current > LATEST_SCHEMA_VERSION:
        raise FutureSchemaError("Database schema is newer than this application.")
    if current == 0:
        # v1 的 executescript 自带 BEGIN，版本登记并入同一事务后统一提交。
        try:
            _migration_1(connection)
            _record_version(connection, 1)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        current = 1
    for version in range(current + 1, LATEST_SCHEMA_VERSION + 1):
        _apply(connection, version, _MIGRATIONS[version])
