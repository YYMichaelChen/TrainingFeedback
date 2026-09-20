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

LATEST_SCHEMA_VERSION = 22

# Section 13 retention window: retained application endpoints and their database
# baselines are 0.6.0/schema14, 0.6.1/schema16 and 0.7.0/schema22.
# Intermediate development schemas 15 and 17-21 keep their historic numbers; roots
# at those versions step forward through the normal migration chain and are not
# independent supported releases. Schemas below 14 are outside the window: their
# roots are refused read-only before any write (Section 13.2). Fresh creation
# (current == 0) always runs the full 1..LATEST chain, so migration bodies 1-13
# remain required dependency steps even though no in-window root upgrades from them.
OLDEST_SUPPORTED_SCHEMA_VERSION = 14
SUPPORTED_SCHEMA_APPLICATIONS = {14: "0.6.0", 16: "0.6.1", 22: "0.7.0"}


class FutureSchemaError(sqlite3.DatabaseError):
    """Raised when the database schema is newer than this application."""


class ExpiredSchemaError(sqlite3.DatabaseError):
    """Raised when the database schema is older than the supported window."""


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


def _migration_14(connection: sqlite3.Connection) -> None:
    """Keep explicit result retractions without rewriting finished session facts."""
    connection.execute(
        "CREATE TABLE session_result_retraction ("
        "id INTEGER PRIMARY KEY, "
        "session_id INTEGER NOT NULL REFERENCES training_session(id), "
        "session_action_id INTEGER NOT NULL REFERENCES training_session_action(id), "
        "previous_action_json TEXT NOT NULL, retracted_at TEXT NOT NULL)"
    )


def _migration_15(connection: sqlite3.Connection) -> None:
    """去掉指导审核状态字段：已审核改由审核证据派生，使用版本由指针单独表示。

    只删除 review.status 这一个键，审核人、来源、审核时间、用户确认时间与受管原件引用
    原样保留，因此历史审核事实不受影响；旧的 draft/pending_review/approved/active/rejected
    取值不再有任何含义。
    """
    for row in connection.execute(
        "SELECT id, guidance_json FROM exercise_guidance_revision"
    ).fetchall():
        payload = json.loads(row[1])
        review = payload.get("review")
        if not isinstance(review, dict) or "status" not in review:
            continue
        del review["status"]
        connection.execute(
            "UPDATE exercise_guidance_revision SET guidance_json = ? WHERE id = ?",
            (json.dumps(payload, ensure_ascii=False, separators=(",", ":")), row[0]),
        )


def _migration_16(connection: sqlite3.Connection) -> None:
    """冻结训练当时的指导审核状态。

    未审核的指导现在也可以用于训练，事后补记审核会让旧会话看起来是在已审核指导下完成的。
    该列记录执行时的事实：1 已审核、0 未审核、NULL 表示这一列出现之前的历史会话未记录。
    """
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(training_session_action)")
    }
    if "guidance_reviewed_snapshot" not in columns:
        connection.execute(
            "ALTER TABLE training_session_action ADD COLUMN guidance_reviewed_snapshot INTEGER"
        )


def _migration_17(connection: sqlite3.Connection) -> None:
    """Add new-model user references and immutable snapshots without changing old facts."""
    statements = (
        "CREATE TABLE library_reference (id INTEGER PRIMARY KEY, source TEXT NOT NULL "
        "CHECK(source IN ('bundled','custom')), stable_key TEXT NOT NULL, "
        "created_at TEXT NOT NULL, UNIQUE(source, stable_key))",
        "CREATE TABLE content_snapshot (sha256 TEXT PRIMARY KEY, content_json TEXT NOT NULL)",
        "CREATE TABLE snapshot_asset (sha256 TEXT PRIMARY KEY, byte_count INTEGER NOT NULL)",
        "CREATE TABLE content_snapshot_asset (snapshot_sha256 TEXT NOT NULL "
        "REFERENCES content_snapshot(sha256), original_path TEXT NOT NULL, "
        "asset_sha256 TEXT NOT NULL REFERENCES snapshot_asset(sha256), "
        "PRIMARY KEY(snapshot_sha256, original_path))",
        "CREATE TABLE library_content (id INTEGER PRIMARY KEY, "
        "reference_id INTEGER NOT NULL REFERENCES library_reference(id), "
        "content_id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>0), "
        "snapshot_sha256 TEXT NOT NULL REFERENCES content_snapshot(sha256), "
        "origin TEXT NOT NULL CHECK(origin IN ('bundled','custom','override')), "
        "provenance_json TEXT NOT NULL, created_at TEXT NOT NULL, "
        "UNIQUE(reference_id, content_id, version), UNIQUE(id, reference_id))",
        "CREATE TABLE library_state (reference_id INTEGER PRIMARY KEY "
        "REFERENCES library_reference(id), selected_content_id INTEGER, "
        "enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)), "
        "FOREIGN KEY(selected_content_id, reference_id) "
        "REFERENCES library_content(id,reference_id))",
    )
    for statement in statements:
        connection.execute(statement)
    for table in (
        "content_snapshot", "snapshot_asset", "content_snapshot_asset", "library_content",
    ):
        for operation in ("UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER immutable_{table}_{operation.lower()} "
                f"BEFORE {operation} ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'Retained catalog evidence is immutable.'); END"
            )


def _migration_18(connection: sqlite3.Connection) -> None:
    """Append exact-content review facts; withdrawing never erases an earlier event."""
    connection.execute(
        "CREATE TABLE library_review_event (id INTEGER PRIMARY KEY, "
        "content_id INTEGER NOT NULL REFERENCES library_content(id), "
        "event_type TEXT NOT NULL CHECK(event_type IN ('approved','withdrawn')), "
        "content_sha256 TEXT NOT NULL REFERENCES content_snapshot(sha256), "
        "image_hashes_json TEXT NOT NULL, reviewer_type TEXT NOT NULL, "
        "review_source TEXT NOT NULL, reviewed_at TEXT, confirmed_at TEXT NOT NULL, "
        "note TEXT NOT NULL, attachment_json TEXT)"
    )
    for operation in ("UPDATE", "DELETE"):
        connection.execute(
            f"CREATE TRIGGER immutable_library_review_{operation.lower()} "
            f"BEFORE {operation} ON library_review_event "
            "BEGIN SELECT RAISE(ABORT, 'Review events are immutable.'); END"
        )


def _migration_19(connection: sqlite3.Connection) -> None:
    """Normalized new-model plans and immutable activation pins/provenance."""
    statements = (
        "CREATE TABLE group_plan (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, "
        "active_revision_id INTEGER, created_at TEXT NOT NULL)",
        "CREATE TABLE group_plan_revision (id INTEGER PRIMARY KEY, plan_id INTEGER NOT NULL "
        "REFERENCES group_plan(id), revision_number INTEGER NOT NULL, status TEXT NOT NULL "
        "CHECK(status IN ('draft','active','superseded')), name TEXT NOT NULL, "
        "purpose TEXT NOT NULL, "
        "target_plan_name TEXT, rationale TEXT NOT NULL, source_json TEXT NOT NULL, "
        "created_at TEXT NOT NULL, activated_at TEXT, edit_token INTEGER NOT NULL DEFAULT 1, "
        "UNIQUE(plan_id,revision_number))",
        "CREATE TABLE group_plan_day (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL "
        "REFERENCES group_plan_revision(id), day_order INTEGER NOT NULL, name TEXT NOT NULL, "
        "UNIQUE(revision_id,day_order))",
        "CREATE TABLE group_plan_item (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL "
        "REFERENCES group_plan_revision(id), day_id INTEGER NOT NULL "
        "REFERENCES group_plan_day(id), "
        "parent_id INTEGER REFERENCES group_plan_item(id), item_key TEXT NOT NULL, "
        "item_order INTEGER NOT NULL, kind TEXT NOT NULL "
        "CHECK(kind IN ('action','group','member')), "
        "fields_json TEXT NOT NULL, UNIQUE(revision_id,item_key))",
        "CREATE TABLE group_plan_set (id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL "
        "REFERENCES group_plan_item(id), set_order INTEGER NOT NULL, value REAL, "
        "unit TEXT NOT NULL, "
        "per_side INTEGER NOT NULL CHECK(per_side IN (0,1)), note TEXT NOT NULL, "
        "rest_after_set_seconds REAL NOT NULL, UNIQUE(item_id,set_order))",
        "CREATE TABLE group_plan_pin (item_id INTEGER PRIMARY KEY REFERENCES group_plan_item(id), "
        "content_id INTEGER NOT NULL REFERENCES library_content(id), review_json TEXT NOT NULL, "
        "pinned_at TEXT NOT NULL)",
        "CREATE TABLE group_plan_import (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL "
        "UNIQUE REFERENCES group_plan_revision(id), source_path TEXT NOT NULL, "
        "sha256 TEXT NOT NULL, "
        "original_payload TEXT NOT NULL, imported_at TEXT NOT NULL)",
        "CREATE TABLE group_plan_export (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL "
        "REFERENCES group_plan_revision(id), directory TEXT NOT NULL, created_at TEXT NOT NULL)",
    )
    for statement in statements:
        connection.execute(statement)
    # Child triggers guard both old and new parents so published rows cannot be moved out.
    connection.execute(
        "CREATE UNIQUE INDEX one_active_group_plan_revision "
        "ON group_plan_revision(plan_id) WHERE status='active'"
    )
    expressions = {
        "group_plan_day": "SELECT status FROM group_plan_revision WHERE id={row}.revision_id",
        "group_plan_item": "SELECT status FROM group_plan_revision WHERE id={row}.revision_id",
        "group_plan_set": "SELECT r.status FROM group_plan_revision r JOIN group_plan_item i "
                          "ON i.revision_id=r.id WHERE i.id={row}.item_id",
    }
    for table, query in expressions.items():
        for operation, rows in (("INSERT", ("NEW",)), ("UPDATE", ("OLD", "NEW")),
                                ("DELETE", ("OLD",))):
            condition = " OR ".join(f"({query.format(row=row)}) != 'draft'" for row in rows)
            connection.execute(
                f"CREATE TRIGGER guard_{table}_{operation.lower()} BEFORE {operation} ON {table} "
                f"WHEN {condition} BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END"
            )
    for table in ("group_plan_pin", "group_plan_import", "group_plan_export"):
        for operation in ("UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER immutable_{table}_{operation.lower()} "
                f"BEFORE {operation} ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'Plan evidence is immutable.'); END"
            )
    connection.execute(
        "CREATE TRIGGER draft_only_group_plan_pin BEFORE INSERT ON group_plan_pin "
        "WHEN (SELECT r.status FROM group_plan_revision r JOIN group_plan_item i "
        "ON i.revision_id=r.id WHERE i.id=NEW.item_id)!='draft' "
        "BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END"
    )
    connection.execute(
        "CREATE TRIGGER immutable_group_plan_revision BEFORE UPDATE ON group_plan_revision "
        "WHEN OLD.status!='draft' AND (NEW.plan_id!=OLD.plan_id OR "
        "NEW.revision_number!=OLD.revision_number OR NEW.name!=OLD.name OR "
        "NEW.purpose!=OLD.purpose OR NEW.target_plan_name IS NOT OLD.target_plan_name OR "
        "NEW.rationale!=OLD.rationale OR NEW.source_json!=OLD.source_json OR "
        "NEW.created_at!=OLD.created_at OR NEW.activated_at IS NOT OLD.activated_at OR "
        "NEW.edit_token!=OLD.edit_token OR "
        "NOT (OLD.status='active' AND NEW.status='superseded')) "
        "BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END"
    )
    connection.execute(
        "CREATE TRIGGER immutable_group_plan_revision_delete BEFORE DELETE ON group_plan_revision "
        "WHEN OLD.status!='draft' BEGIN SELECT RAISE(ABORT, 'Published plan is immutable.'); END"
    )


def _migration_20(connection: sqlite3.Connection) -> None:
    statements = (
        "CREATE TABLE group_session (id INTEGER PRIMARY KEY, revision_id INTEGER NOT NULL "
        "REFERENCES group_plan_revision(id), training_date TEXT NOT NULL, "
        "status TEXT NOT NULL CHECK(status IN ('open','paused','completed','partial','aborted')), "
        "position INTEGER NOT NULL DEFAULT 0 CHECK(position>=0), version INTEGER NOT NULL "
        "DEFAULT 1, snapshot_json TEXT NOT NULL, started_at TEXT NOT NULL, paused_at TEXT, "
        "ended_at TEXT, abort_reason TEXT, abort_note TEXT)",
        "CREATE UNIQUE INDEX one_active_group_session ON group_session((1)) "
        "WHERE status IN ('open','paused')",
        "CREATE TABLE group_session_occurrence (id INTEGER PRIMARY KEY, session_id INTEGER "
        "NOT NULL REFERENCES group_session(id), position INTEGER NOT NULL, content_id INTEGER "
        "NOT NULL REFERENCES library_content(id), snapshot_json TEXT NOT NULL, "
        "UNIQUE(session_id,position))",
        "CREATE TABLE group_session_batch (id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL "
        "REFERENCES group_session(id), preview_token TEXT NOT NULL UNIQUE, members_json TEXT "
        "NOT NULL, created_at TEXT NOT NULL)",
        "CREATE TABLE group_occurrence_result (occurrence_id INTEGER PRIMARY KEY "
        "REFERENCES group_session_occurrence(id), result TEXT NOT NULL "
        "CHECK(result IN ('completed','exceeded','partial','not_completed')), "
        "note TEXT NOT NULL, recorded_at TEXT NOT NULL, batch_id INTEGER "
        "REFERENCES group_session_batch(id))",
        "CREATE TABLE group_actual_set (occurrence_id INTEGER NOT NULL "
        "REFERENCES group_occurrence_result(occurrence_id), set_order INTEGER NOT NULL, "
        "value REAL, unit TEXT NOT NULL, side TEXT CHECK(side IN ('left','right')), "
        "note TEXT NOT NULL, provenance TEXT NOT NULL, PRIMARY KEY(occurrence_id,set_order))",
        "CREATE TABLE group_session_event (id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL "
        "REFERENCES group_session(id), kind TEXT NOT NULL, occurred_at TEXT NOT NULL, "
        "facts_json TEXT NOT NULL)",
        "CREATE TABLE group_session_feedback (session_id INTEGER PRIMARY KEY "
        "REFERENCES group_session(id), overall_note TEXT NOT NULL, submitted_at TEXT NOT NULL)",
        "CREATE TABLE group_session_feedback_area (session_id INTEGER NOT NULL "
        "REFERENCES group_session_feedback(session_id), name TEXT NOT NULL, value TEXT, "
        "PRIMARY KEY(session_id,name))",
        "CREATE TABLE group_session_export (export_id INTEGER PRIMARY KEY "
        "REFERENCES group_plan_export(id), session_id INTEGER NOT NULL "
        "REFERENCES group_session(id))",
    )
    for statement in statements:
        connection.execute(statement)
    for table in (
        "group_session_occurrence", "group_session_batch", "group_session_event",
        "group_session_feedback", "group_session_feedback_area", "group_session_export",
    ):
        for operation in ("UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER immutable_{table}_{operation.lower()} BEFORE {operation} "
                f"ON {table} BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END"
            )
    connection.execute(
        "CREATE TRIGGER immutable_group_session_snapshot BEFORE UPDATE ON group_session "
        "WHEN NEW.revision_id!=OLD.revision_id OR NEW.training_date!=OLD.training_date "
        "OR NEW.snapshot_json!=OLD.snapshot_json OR NEW.started_at!=OLD.started_at "
        "OR OLD.status NOT IN ('open','paused') "
        "BEGIN SELECT RAISE(ABORT, 'Session snapshot or terminal state is immutable.'); END"
    )
    connection.execute(
        "CREATE TRIGGER immutable_group_session_delete BEFORE DELETE ON group_session "
        "BEGIN SELECT RAISE(ABORT, 'Session evidence is immutable.'); END"
    )
    for table in ("group_occurrence_result", "group_actual_set"):
        for operation, rows in (("INSERT", ("NEW",)), ("UPDATE", ("OLD", "NEW")),
                                ("DELETE", ("OLD",))):
            condition = " OR ".join(
                "(SELECT s.status FROM group_session s JOIN group_session_occurrence o "
                f"ON s.id=o.session_id WHERE o.id={row}.occurrence_id)!='open'"
                for row in rows
            )
            connection.execute(
                f"CREATE TRIGGER guard_{table}_{operation.lower()} BEFORE {operation} "
                f"ON {table} WHEN {condition} "
                "BEGIN SELECT RAISE(ABORT, 'Only open sessions accept result changes.'); END"
            )


def _migration_21(connection: sqlite3.Connection) -> None:
    """Reviewed lifecycle decisions never delete content or rewrite earlier evidence."""
    statements = (
        "CREATE TABLE library_lifecycle_request (id INTEGER PRIMARY KEY, "
        "operation TEXT NOT NULL CHECK(operation IN ('remove','restore')), "
        "reason TEXT NOT NULL, requested_at TEXT NOT NULL, preview_json TEXT NOT NULL)",
        "CREATE TABLE library_lifecycle_event (id INTEGER PRIMARY KEY, request_id INTEGER "
        "NOT NULL REFERENCES library_lifecycle_request(id), kind TEXT NOT NULL "
        "CHECK(kind IN ('requested','under_review','approved','applied','rejected','cancelled')), "
        "source TEXT NOT NULL, occurred_at TEXT NOT NULL, confirmed_at TEXT NOT NULL, "
        "note TEXT NOT NULL, preview_json TEXT NOT NULL)",
        "CREATE TABLE library_tombstone (reference_id INTEGER PRIMARY KEY "
        "REFERENCES library_reference(id), disposition TEXT NOT NULL "
        "CHECK(disposition IN ('removed','restored')), event_id INTEGER NOT NULL "
        "REFERENCES library_lifecycle_event(id))",
        "CREATE TABLE library_publisher_event (id INTEGER PRIMARY KEY, reference_id INTEGER "
        "NOT NULL REFERENCES library_reference(id), catalog_version TEXT NOT NULL, "
        "manifest_sha256 TEXT NOT NULL, disposition TEXT NOT NULL "
        "CHECK(disposition IN ('available','withdrawn','missing')), "
        "content_reference_json TEXT, observed_at TEXT NOT NULL)",
        "CREATE TABLE library_plan_invalidation (revision_id INTEGER NOT NULL "
        "REFERENCES group_plan_revision(id), reference_id INTEGER NOT NULL "
        "REFERENCES library_reference(id), lifecycle_event_id INTEGER "
        "REFERENCES library_lifecycle_event(id), publisher_event_id INTEGER "
        "REFERENCES library_publisher_event(id), PRIMARY KEY(revision_id,reference_id), "
        "CHECK((lifecycle_event_id IS NULL)!=(publisher_event_id IS NULL)))",
        "CREATE INDEX lifecycle_events_by_request ON library_lifecycle_event(request_id,id)",
        "CREATE INDEX publisher_events_by_reference ON library_publisher_event(reference_id,id)",
    )
    for statement in statements:
        connection.execute(statement)
    for table in ("library_lifecycle_request", "library_lifecycle_event", "library_publisher_event",
                  "library_plan_invalidation"):
        for operation in ("UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER immutable_{table}_{operation.lower()} BEFORE {operation} "
                f"ON {table} BEGIN SELECT RAISE(ABORT, 'Lifecycle evidence is immutable.'); END"
            )


def _migration_22(connection: sqlite3.Connection) -> None:
    """Conversion provenance and explicitly unknown historical result/rest facts."""
    statements = (
        "CREATE TABLE conversion_run (id INTEGER PRIMARY KEY CHECK(id=1), source_schema INTEGER "
        "NOT NULL, source_sha256 TEXT NOT NULL, converted_at TEXT NOT NULL, manifest_json TEXT "
        "NOT NULL)",
        "CREATE TABLE conversion_original (source_table TEXT NOT NULL, source_key TEXT NOT NULL, "
        "row_json TEXT NOT NULL, PRIMARY KEY(source_table,source_key))",
        "CREATE TABLE conversion_mapping (source_table TEXT NOT NULL, source_key TEXT NOT NULL, "
        "target_kind TEXT NOT NULL, target_json TEXT NOT NULL, "
        "PRIMARY KEY(source_table,source_key,target_kind))",
        "CREATE TABLE conversion_registration (kind TEXT NOT NULL "
        "CHECK(kind IN ('import','export')), "
        "id INTEGER NOT NULL, revision_id INTEGER REFERENCES group_plan_revision(id), "
        "session_id INTEGER REFERENCES group_session(id), facts_json TEXT NOT NULL, "
        "PRIMARY KEY(kind,id))",
        "ALTER TABLE group_plan_revision ADD COLUMN migration_json TEXT",
    )
    for statement in statements:
        connection.execute(statement)
    # Rebuild leaf/child families together; no FK points outside each rebuilt family.
    definitions = {
        "group_plan_set": "id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES "
        "group_plan_item(id), set_order INTEGER NOT NULL, value REAL, unit TEXT NOT NULL, "
        "per_side INTEGER NOT NULL CHECK(per_side IN (0,1)), note TEXT NOT NULL, "
        "rest_after_set_seconds REAL, UNIQUE(item_id,set_order)",
        "group_occurrence_result": "occurrence_id INTEGER PRIMARY KEY REFERENCES "
        "group_session_occurrence(id), result TEXT NOT NULL CHECK(result IN "
        "('completed','exceeded','partial','not_completed')), note TEXT, recorded_at TEXT, "
        "batch_id INTEGER REFERENCES group_session_batch(id)",
        "group_actual_set": "occurrence_id INTEGER NOT NULL REFERENCES "
        "group_occurrence_result(occurrence_id), set_order INTEGER NOT NULL, value REAL, "
        "unit TEXT, side TEXT CHECK(side IN ('left','right')), note TEXT NOT NULL, "
        "provenance TEXT NOT NULL, PRIMARY KEY(occurrence_id,set_order)",
        "group_session_feedback": "session_id INTEGER PRIMARY KEY REFERENCES group_session(id), "
        "overall_note TEXT, submitted_at TEXT NOT NULL",
        "group_session_feedback_area": "session_id INTEGER NOT NULL REFERENCES "
        "group_session_feedback(session_id), name TEXT NOT NULL, value TEXT, "
        "PRIMARY KEY(session_id,name)",
    }
    # Back up rows and triggers in memory; the outer migration transaction rolls back all DDL.
    saved = {}
    for table in definitions:
        columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
        saved[table] = (columns, connection.execute(f'SELECT * FROM "{table}"').fetchall(),
                        [row[0] for row in connection.execute(
                            "SELECT sql FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
                            (table,))])
    for table in reversed(definitions):
        for trigger in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,),
        ).fetchall():
            connection.execute(f'DROP TRIGGER "{trigger[0]}"')
        connection.execute(f'DROP TABLE "{table}"')
    for table, definition in definitions.items():
        connection.execute(f'CREATE TABLE "{table}" ({definition})')
        columns, rows, triggers = saved[table]
        placeholders = ",".join("?" for _ in columns)
        connection.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows)
        for sql in triggers:
            connection.execute(sql)
    connection.execute("ALTER TABLE group_actual_set ADD COLUMN per_side INTEGER "
                       "CHECK(per_side IN (0,1) OR per_side IS NULL)")
    connection.execute(
        "CREATE TRIGGER immutable_plan_migration_provenance BEFORE UPDATE ON group_plan_revision "
        "WHEN NEW.migration_json IS NOT OLD.migration_json "
        "BEGIN SELECT RAISE(ABORT, 'Conversion provenance is immutable.'); END"
    )
    for table in ("conversion_run", "conversion_original", "conversion_mapping",
                  "conversion_registration"):
        for operation in ("UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER immutable_{table}_{operation.lower()} BEFORE {operation} "
                f"ON {table} BEGIN SELECT RAISE(ABORT, 'Conversion evidence is immutable.'); END"
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
    14: _migration_14,
    15: _migration_15,
    16: _migration_16,
    17: _migration_17,
    18: _migration_18,
    19: _migration_19,
    20: _migration_20,
    21: _migration_21,
    22: _migration_22,
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
    if 0 < current < OLDEST_SUPPORTED_SCHEMA_VERSION:
        raise ExpiredSchemaError("Database schema is older than the supported window.")
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
