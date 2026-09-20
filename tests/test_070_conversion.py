"""End-to-end fact mapping, resumable current execution and conversion rollback."""

import json
import sqlite3
from contextlib import closing
from unittest.mock import patch

import pytest
from migration_070_fixtures import create_schema16_baseline, logical_baseline

from training_feedback.app import LibraryContext
from training_feedback.data import migrations
from training_feedback.data.backup import create_backup
from training_feedback.data.catalog_conversion import (
    convert_catalog_root,
    validate_catalog_conversion,
)
from training_feedback.data.data_root import (
    DATABASE_FILENAME,
    ExpiredDataRootError,
    create_new,
)
from training_feedback.data.database import Database
from training_feedback.data.migrations import ExpiredSchemaError
from training_feedback.data.root_lock import JOURNAL_FILENAME, RootBusyError
from training_feedback.data.upgrade_recovery import UpgradeRecovery, UpgradeRecoveryError
from training_feedback.domain.catalog import ExerciseReference
from training_feedback.ui.group_plan_page import ActionPrescriptionDialog
from training_feedback.ui.group_training_page import GroupTrainingPage
from training_feedback.ui.labels import session_history_text, user_message


def test_converted_pause_resumes_aggregate_zero_retracts_and_finishes(qt_app, tmp_path):
    baseline = create_schema16_baseline(tmp_path / "old")
    root = baseline["data_root"]
    assert convert_catalog_root(root)
    with LibraryContext.reopen(root) as context:
        controller = context.session_controller()
        controller.resume()
        original = controller.session
        assert original["id"] == baseline["sessions"]["paused"]
        first = original["occurrences"][0]
        assert first["dose_scope"] == "per_side_aggregate"
        assert first["actual_sets"][0]["value"] == 0
        assert first["actual_sets"][0]["per_side"] is True
        assert len(original["occurrences"]) == 3
        page = GroupTrainingPage(controller)
        assert "未知（未记录）" in page.prescription.text()
        controller.navigate(0)
        controller.retract(user_confirmed=True)
        with pytest.raises(ValueError, match="explicit side"):
            controller.record(
                "partial", actual=[{"value": 0, "unit": "reps", "side": None, "note": ""}]
            )
        controller.record(
            "partial",
            actual=[
                {"value": 0, "unit": "reps", "side": None, "per_side": True, "note": "  保留\r\n  "}
            ],
        )
        controller.next_unfinished()
        controller.record("completed")
        controller.finish(user_confirmed=True)
        final = context.sessions.get(original["id"])
        assert final["status"] == "partial"
        assert len(final["occurrences"]) == 3
        assert final["events"][-2]["kind"] == "result_retracted"
        assert "每侧汇总" in session_history_text(final)
        page.close()
        active = context.plans.active_revisions()[0]
        # Missing required pictures block new starts, not frozen work above.
        with pytest.raises(ValueError, match="eligible|enabled"):
            context.sessions.preview_start(active["id"], 1)
        assert context.plans.content_issues(active["id"])
        restored = create_backup(root, tmp_path / "restored", context.database.connection)
    with LibraryContext.reopen(restored) as context:
        assert context.sessions.get(original["id"])["status"] == "partial"
        assert context.sessions.active() is None
    assert not convert_catalog_root(restored)


@pytest.mark.parametrize("failure", ["conversion_before_commit", "database_published"])
def test_conversion_failure_restores_original_and_retry_is_deterministic(tmp_path, failure):
    baseline = create_schema16_baseline(tmp_path / "old")
    root = baseline["data_root"]
    staged_identities = []

    def fail(phase):
        if phase == failure:
            if phase == "database_published":
                with closing(sqlite3.connect(root / DATABASE_FILENAME)) as db:
                    staged_identities.extend(db.execute(
                        "SELECT source,stable_key FROM library_reference ORDER BY id").fetchall())
            raise RuntimeError("synthetic conversion interruption")

    with pytest.raises(RuntimeError, match="interruption"):
        convert_catalog_root(root, checkpoint=fail)
    with pytest.raises(RootBusyError):
        with Database(root / DATABASE_FILENAME):
            pass
    assert UpgradeRecovery(root).recover()
    restored = logical_baseline(root)
    assert restored["tables"] == baseline["baseline"]["tables"]
    for relative, digest in baseline["baseline"]["resources"].items():
        assert restored["resources"][relative] == digest
    assert convert_catalog_root(root)
    with LibraryContext.reopen(root) as context:
        expected = context.user_library.references()
        if staged_identities:
            assert [(item.source.value, item.key) for item in expected] == staged_identities
        assert context.sessions.active()["status"] == "paused"
    assert not convert_catalog_root(root)
    with LibraryContext.reopen(root) as context:
        assert context.user_library.references() == expected


@pytest.mark.parametrize("schema", [1, 9, 13])
def test_out_of_window_root_refused_before_any_write(tmp_path, schema):
    root = tmp_path / f"schema{schema}"
    with patch.object(migrations, "LATEST_SCHEMA_VERSION", schema):
        create_new(root)
    database_bytes = (root / DATABASE_FILENAME).read_bytes()

    with pytest.raises(ExpiredDataRootError) as failure:
        convert_catalog_root(root)
    assert user_message(str(failure.value)) != str(failure.value)
    # The write-entry guard must also refuse without migrating the database.
    with pytest.raises(ExpiredSchemaError, match="older than the supported window"):
        with Database(root / DATABASE_FILENAME):
            pass

    assert (root / DATABASE_FILENAME).read_bytes() == database_bytes
    assert not (root / JOURNAL_FILENAME).exists()
    assert not list((root / "backups").glob("upgrade-*"))
    with closing(sqlite3.connect(root / DATABASE_FILENAME)) as db:
        assert db.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == schema


def test_oldest_retained_schema14_root_converts_unknown_facts(tmp_path):
    root = tmp_path / "schema14"
    with patch.object(migrations, "LATEST_SCHEMA_VERSION", 14):
        create_new(root)
    with closing(sqlite3.connect(root / DATABASE_FILENAME)) as db:
        db.executescript("""
            INSERT INTO exercise(id,canonical_name,created_at,updated_at)
                VALUES (7,'原名','old','old');
            INSERT INTO training_plan VALUES (8,'旧计划',NULL,'old');
            INSERT INTO training_plan_revision VALUES (9,8,1,'draft','目的','old');
            INSERT INTO training_plan_day VALUES (10,9,1,'原日');
            INSERT INTO training_plan_action VALUES (11,10,7,1,'cooldown',23,'原备注');
            INSERT INTO training_plan_set(id,action_id,set_order,value,unit,per_side,note)
                VALUES (12,11,1,8,'reps',1,'  原组  ');
            UPDATE training_plan_revision SET status='active' WHERE id=9;
            UPDATE training_plan SET active_revision_id=9 WHERE id=8;
            INSERT INTO training_session(id,plan_revision_id,training_date,status,
                started_at,updated_at) VALUES (13,9,'2026-01-01','paused','old','old');
            INSERT INTO training_session_action(id,session_id,action_order,
                exercise_name_snapshot,body_areas_snapshot_json,result,note)
                VALUES (14,13,1,'历史原名','[{"name":"部位","is_primary":null}]',
                        'partial',NULL);
            INSERT INTO training_session_set(id,session_action_id,set_order,planned_value,
                planned_unit,planned_per_side,actual_value,actual_unit,actual_per_side)
                VALUES (15,14,1,8,'reps',1,0,'reps',1);
        """)
    assert convert_catalog_root(root)
    with LibraryContext.reopen(root) as context:
        session = context.sessions.get(13)
        occurrence = session["occurrences"][0]
        assert occurrence["action"]["exercise_name"] == "历史原名"
        # Occurrence doses use the session snapshot (schema-14 defaults); the plan-side
        # '  原组  ' note is preserved on the converted plan item and checked by validation.
        assert occurrence["action"]["sets"][0]["note"] == ""
        assert occurrence["actual_sets"][0]["value"] == 0
        assert occurrence["actual_sets"][0]["per_side"] is True
        assert occurrence["note"] is None
        # Schema 14 records these facts with defaults instead of leaving them unknown.
        assert occurrence["rest_after_seconds"] == 0
        assert occurrence["phase"] == "main"
        assert occurrence["start_review"]["eligibility"]["reviewed"] is None
        assert occurrence["content"]["guidance"]["images"] == []
        assert context.sessions.resume(13, expected_version=session["version"])["status"] == "open"


def test_migrated_plan_binding_keeps_eligible_active_intent_and_rejects_forged_import(
    qt_app,
    tmp_path,
    monkeypatch,
):
    baseline = create_schema16_baseline(tmp_path / "old")
    root = baseline["data_root"]
    bridge_id = baseline["mapping_expectations"]["renamed_bundled"]["old_id"]
    with closing(sqlite3.connect(root / DATABASE_FILENAME)) as db:
        db.executescript("""
            INSERT INTO training_plan VALUES (900,'【合成】有图每侧计划',NULL,'original');
            INSERT INTO training_plan_revision VALUES (900,900,1,'draft','原目的','original');
            INSERT INTO training_plan_day VALUES (900,900,1,'原日');
        """)
        db.execute("INSERT INTO training_plan_action VALUES (900,900,?,1,'main',17,'  原备注  ')",
                   (bridge_id,))
        db.execute("INSERT INTO training_plan_set VALUES (900,900,1,7,'reps',1,'  原组  ')")
        db.execute("UPDATE training_plan_revision SET status='active' WHERE id=900")
        db.execute("UPDATE training_plan SET active_revision_id=900 WHERE id=900")
        db.commit()
    convert_catalog_root(root)
    with LibraryContext.reopen(root) as context:
        active = context.plans.active_revisions()[0]
        assert active["activated_at"] is None
        assert all(pin["review"]["provenance"] == "migration_time" for pin in active["pins"])
        assert all(pin["review"]["reviewed"] is None for pin in active["pins"])
        draft_id = context.plans.clone(active["id"])
        draft = context.plans.get(draft_id)
        context.plans.save(draft_id, draft["payload"], expected_token=draft["edit_token"])
        action = draft["payload"]["plan"]["days"][0]["items"][0]
        dialog = ActionPrescriptionDialog(context.plans.exercise_choices(), action)
        warnings = []
        monkeypatch.setattr(
            "training_feedback.ui.group_plan_page.error",
            lambda _widget, exc: warnings.append(str(exc)),
        )
        dialog.save()
        assert not warnings
        assert dialog.value == action
        dialog.close()
        with pytest.raises(ValueError, match="Invalid plan v2"):
            context.plans.create(draft["payload"])
        target = context.library.get(ExerciseReference("bundled", "launch.glute-bridge"))
        assert target["enabled"] is True
        assert target["selected"]["content"]["canonical_name"] == "【合成迁移数据】改名臀桥"
        export = context.plan_handoff.export(active["id"])
        evidence = json.loads((export / "evidence.json").read_text(encoding="utf-8"))
        assert evidence["contents"][0]["binding_provenance"] == "migration_time"
        paused = context.sessions.active()
        context.sessions.abort(paused["id"], "other", "合成测试结束旧训练",
                               expected_version=paused["version"], user_confirmed=True)
        preview = context.sessions.preview_start(900, 1)
        assert len(preview["occurrences"]) == 1
        assert preview["occurrences"][0]["dose_scope"] == "per_side_aggregate"
        started = context.sessions.start(900, 1, expected_preview=preview["token"],
                                         user_confirmed=True)
        assert started["snapshot"]["revision"]["activated_at"] is None
        assert started["occurrences"][0]["action"]["sets"][0]["value"] == 7


def test_conversion_validator_rejects_changed_destination_before_publication(tmp_path):
    baseline = create_schema16_baseline(tmp_path / "old")
    root = baseline["data_root"]
    convert_catalog_root(root)
    with LibraryContext.reopen(root) as context:
        validate_catalog_conversion(root, context.catalog)
        draft = next(row for plan in context.plans.list_plans()
                     for row in context.plans.revisions(plan["id"]) if row["status"] == "draft")
        db = context.database.connection
        db.execute("UPDATE group_plan_revision SET purpose='corruption' WHERE id=?", (draft["id"],))
        db.commit()
        with pytest.raises(UpgradeRecoveryError, match="facts do not match"):
            validate_catalog_conversion(root, context.catalog)


def test_schema22_preserves_populated_current_results_and_feedback(tmp_path):
    path = tmp_path / "schema21.sqlite3"
    with patch.object(migrations, "LATEST_SCHEMA_VERSION", 21):
        with Database(path) as db:
            db.executescript("""
                INSERT INTO library_reference VALUES (1,'custom','example','old');
                INSERT INTO content_snapshot VALUES ('hash','{}');
                INSERT INTO library_content VALUES (1,1,'content',1,'hash','custom','{}','old');
                INSERT INTO group_plan VALUES (1,'plan',NULL,'old');
                INSERT INTO group_plan_revision(plan_id,revision_number,status,name,purpose,
                    rationale,source_json,created_at)
                    VALUES (1,1,'draft','plan','','','null','old');
                INSERT INTO group_session(revision_id,training_date,status,snapshot_json,started_at)
                    VALUES (1,'2026-01-01','open','{}','old');
                INSERT INTO group_session_occurrence VALUES (1,1,0,1,'{}');
                INSERT INTO group_occurrence_result VALUES (1,'partial','  note\t  ','old',NULL);
                INSERT INTO group_actual_set VALUES (1,1,0,'reps','left','','user_entered');
                INSERT INTO group_session_feedback VALUES (1,'  feedback  ','old');
                INSERT INTO group_session_feedback_area VALUES (1,'area',NULL);
            """)
    with Database(path) as db:
        assert tuple(db.execute("SELECT * FROM group_actual_set").fetchone()) == (
            1,
            1,
            0,
            "reps",
            "left",
            "",
            "user_entered",
            None,
        )
        assert db.execute("SELECT note FROM group_occurrence_result").fetchone()[0] == "  note\t  "
        assert db.execute("SELECT overall_note FROM group_session_feedback").fetchone()[0] == (
            "  feedback  "
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("DELETE FROM group_session_feedback_area")
