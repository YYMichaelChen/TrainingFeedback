import json
import sqlite3
from copy import deepcopy

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

from tests.guidance_fixtures import complete_guidance
from tests.test_phase4_sessions import _active_plan
from training_feedback.app import ApplicationContext
from training_feedback.application.exercise_service import ExerciseService
from training_feedback.data import migrations
from training_feedback.data.backup import create_backup
from training_feedback.data.data_root import create_new
from training_feedback.data.exercise_repositories import ExerciseRepository
from training_feedback.data.handoff import HandoffService
from training_feedback.data.locator import Locator
from training_feedback.data.seed.catalog import CATALOG, bundled_catalog
from training_feedback.domain.enums import ExerciseResult
from training_feedback.domain.exercises import custom_guidance_draft, validate_guidance
from training_feedback.domain.next_day import feedback_areas
from training_feedback.ui.bundled_guidance_update_dialog import BundledGuidanceUpdateDialog
from training_feedback.ui.exercise_editor import ExerciseEditor


def _context(tmp_path):
    return ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )


def _clear_bundled_provenance(connection) -> None:
    connection.execute("UPDATE exercise SET bundled_exercise_key = NULL")
    connection.execute(
        "UPDATE exercise_guidance_revision SET bundled_content_id = NULL, "
        "bundled_content_version = NULL"
    )
    connection.commit()


def _bundle(name: str) -> dict:
    return next(item for item in bundled_catalog() if item["canonical_name"] == name)


def test_new_root_has_14_exercise_specific_unreviewed_bundled_drafts(tmp_path):
    context = _context(tmp_path)
    repository = ExerciseRepository(context.database.connection)
    bundled = bundled_catalog()

    assert len(bundled) == len(CATALOG) == 14
    assert len({item["exercise_key"] for item in bundled}) == 14
    assert len({item["content_id"] for item in bundled}) == 14
    assert len({item["guidance"]["purpose"] for item in bundled}) == 14
    step_sets = {
        tuple(step["text"] for step in item["guidance"]["steps"])
        for item in bundled
    }
    assert len(step_sets) == 14

    for item in bundled:
        validation = validate_guidance(item["guidance"], require_body_areas=True)
        assert validation.complete, (item["canonical_name"], validation.errors)
        assert item["guidance"]["review"] == {
            "status": "draft",
            "reviewer_type": None,
            "review_source": None,
            "review_note": "",
            "reviewed_at": None,
            "user_approved_at": None,
        }
        assert item["guidance"]["images"] == [
            {"path": None, "caption": "暂无动作示意图", "status": "missing"}
        ]
        assert item["guidance"]["primary_body_areas"] == item["primary_areas"]
        assert item["guidance"]["secondary_body_areas"] == item[
            "secondary_areas"
        ]
        exercise = repository.get_by_bundled_key(item["exercise_key"])
        assert exercise is not None
        stored = repository.get(exercise["id"])
        assert {(area["name"], bool(area["is_primary"])) for area in stored["body_areas"]} == set(
            item["body_areas"]
        )
        assert any(primary for _name, primary in item["body_areas"])
        assert any(not primary for _name, primary in item["body_areas"])
        assert stored["active_guidance_revision_id"] is None
        assert len(stored["guidance"]) == 1
        revision = stored["guidance"][0]
        assert revision["bundled_content_id"] == item["content_id"]
        assert revision["bundled_content_version"] == item["content_version"]
        assert revision["guidance"] == item["guidance"]

    assert "保持稳定、舒适且可以自然呼吸的起始姿势" not in {
        item["guidance"]["starting_position"] for item in bundled
    }
    context.close()


def test_supporting_primary_areas_do_not_create_next_day_prompts():
    session = {
        "actions": [
            {
                "result": "completed",
                "phase_snapshot": "preparation",
                "body_area_snapshots": [
                    {"name": "背部", "is_primary": True},
                    {"name": "核心", "is_primary": False},
                ],
            }
        ]
    }

    assert feedback_areas(session) == ()


def test_custom_exercise_default_is_separate_from_bundled_launch_content():
    custom = custom_guidance_draft("用户自定义动作")
    bundled = bundled_catalog()

    assert custom["purpose"] == ""
    assert not validate_guidance(custom).complete
    assert all(custom != item["guidance"] for item in bundled)
    assert custom["review"]["status"] == "draft"


def test_new_custom_exercise_form_starts_without_invented_guidance_facts(qt_app):
    editor = ExerciseEditor(object())

    value = editor.guidance_form.guidance()

    assert value["purpose"] == ""
    assert value["steps"] == []
    assert value["primary_body_areas"] == []
    assert not validate_guidance(value).complete
    editor.close()


def test_v13_migration_adds_nullable_identity_without_fabricating_history(
    tmp_path, monkeypatch
):
    path = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    monkeypatch.setattr(migrations, "LATEST_SCHEMA_VERSION", 12)
    migrations.apply_migrations(connection)
    connection.execute(
        "INSERT INTO exercise(canonical_name, category, equipment_summary, created_at, "
        "updated_at) VALUES ('旧动作', 'main', '', 'now', 'now')"
    )
    exercise_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    connection.execute(
        "INSERT INTO exercise_guidance_revision(exercise_id, revision_number, guidance_json, "
        "created_at) VALUES (?, 1, '{}', 'now')",
        (exercise_id,),
    )
    connection.commit()

    monkeypatch.setattr(migrations, "LATEST_SCHEMA_VERSION", 13)
    migrations.apply_migrations(connection)

    exercise = connection.execute(
        "SELECT bundled_exercise_key FROM exercise WHERE id = ?", (exercise_id,)
    ).fetchone()
    revision = connection.execute(
        "SELECT bundled_content_id, bundled_content_version "
        "FROM exercise_guidance_revision WHERE exercise_id = ?",
        (exercise_id,),
    ).fetchone()
    assert exercise["bundled_exercise_key"] is None
    assert tuple(revision) == (None, None)
    assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 13
    connection.close()


def test_existing_root_receives_only_selected_drafts_idempotently(tmp_path):
    context = _context(tmp_path)
    connection = context.database.connection
    repository = ExerciseRepository(connection)
    service = ExerciseService(repository)
    _clear_bundled_provenance(connection)

    bridge_id = repository.resolve("臀桥")["id"]
    clam_id = repository.resolve("蚌式开合")["id"]
    bridge = repository.get(bridge_id)
    bridge_revision_id = bridge["guidance"][0]["id"]
    repository.replace_primary_body_areas(bridge_id, ["用户自定义区域"])
    user_text = deepcopy(complete_guidance("臀桥"))
    user_text["purpose"] = "  用户自己的臀桥说明\n保持原样  "
    connection.execute(
        "UPDATE exercise_guidance_revision SET guidance_json = ? WHERE id = ?",
        (json.dumps(user_text, ensure_ascii=False), bridge_revision_id),
    )
    connection.commit()

    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": "synthetic-w3-test",
        "reviewed_at": "2026-09-11T00:00:00+00:00",
        "user_approved_at": "2026-09-11T00:00:00+00:00",
    }
    service.review_and_activate_guidance(bridge_revision_id, review)
    active_id = repository.get(bridge_id)["active_guidance_revision_id"]
    before_clam_count = len(repository.get(clam_id)["guidance"])

    preview = {item["canonical_name"]: item for item in service.preview_bundled_guidance()}
    assert preview["臀桥"]["match_status"] == "name_match"
    assert preview["臀桥"]["target_exercise_id"] == bridge_id
    assert preview["蚌式开合"]["target_exercise_id"] == clam_id

    created = service.accept_bundled_guidance(
        {
            preview["臀桥"]["exercise_key"]: bridge_id,
            preview["蚌式开合"]["exercise_key"]: clam_id,
        }
    )
    assert len(created) == 2

    bridge_after = repository.get(bridge_id)
    clam_after = repository.get(clam_id)
    assert bridge_after["active_guidance_revision_id"] == active_id
    assert bridge_after["guidance"][0]["guidance"]["purpose"] == user_text["purpose"]
    assert [
        area["name"] for area in bridge_after["body_areas"] if area["is_primary"]
    ] == ["用户自定义区域"]
    assert bridge_after["guidance"][-1]["guidance"]["primary_body_areas"] == [
        "臀部"
    ]
    assert bridge_after["guidance"][-1]["guidance"]["review"]["status"] == "draft"
    assert len(clam_after["guidance"]) == before_clam_count + 1
    counts = {
        bridge_id: len(bridge_after["guidance"]),
        clam_id: len(clam_after["guidance"]),
    }

    assert service.accept_bundled_guidance(
        {
            preview["臀桥"]["exercise_key"]: bridge_id,
            preview["蚌式开合"]["exercise_key"]: clam_id,
        }
    ) == []
    assert len(repository.get(bridge_id)["guidance"]) == counts[bridge_id]
    assert len(repository.get(clam_id)["guidance"]) == counts[clam_id]
    refreshed = {
        item["canonical_name"]: item for item in service.preview_bundled_guidance()
    }
    assert refreshed["臀桥"]["match_status"] == "up_to_date"
    assert refreshed["蚌式开合"]["match_status"] == "up_to_date"
    context.close()


def test_renamed_or_ambiguous_legacy_matches_are_explicit_and_preview_is_read_only(tmp_path):
    context = _context(tmp_path)
    connection = context.database.connection
    repository = ExerciseRepository(connection)
    service = ExerciseService(repository)
    _clear_bundled_provenance(connection)
    bridge_id = repository.resolve("臀桥")["id"]
    repository.replace_aliases(bridge_id, [])
    repository.update_metadata(bridge_id, "用户重命名的臀桥", "main", "")
    connection.commit()
    before = connection.total_changes

    renamed = {item["canonical_name"]: item for item in service.preview_bundled_guidance()}[
        "臀桥"
    ]
    assert renamed["match_status"] == "missing"
    assert renamed["target_exercise_id"] is None
    assert connection.total_changes == before

    created = service.accept_bundled_guidance({renamed["exercise_key"]: bridge_id})
    assert len(created) == 1
    assert repository.get(bridge_id)["bundled_exercise_key"] == renamed["exercise_key"]

    _clear_bundled_provenance(connection)
    connection.execute(
        "INSERT INTO exercise(canonical_name, category, equipment_summary, created_at, "
        "updated_at) VALUES ('常规臀桥', 'main', '', 'now', 'now')"
    )
    connection.execute(
        "UPDATE exercise SET canonical_name = '臀桥' WHERE id = ?", (bridge_id,)
    )
    connection.execute(
        "INSERT INTO exercise_alias(exercise_id, alias) VALUES (?, '常规臀桥')", (bridge_id,)
    )
    connection.commit()
    revisions_before = connection.execute(
        "SELECT COUNT(*) FROM exercise_guidance_revision"
    ).fetchone()[0]

    ambiguous = {item["canonical_name"]: item for item in service.preview_bundled_guidance()}[
        "臀桥"
    ]
    assert ambiguous["match_status"] == "ambiguous"
    assert ambiguous["target_exercise_id"] is None
    assert {item["canonical_name"] for item in ambiguous["candidate_exercises"]} == {
        "臀桥",
        "常规臀桥",
    }
    assert service.accept_bundled_guidance({}) == []
    assert connection.execute(
        "SELECT COUNT(*) FROM exercise_guidance_revision"
    ).fetchone()[0] == revisions_before
    context.close()


def test_selected_bundled_batch_rolls_back_every_write_on_failure(tmp_path, monkeypatch):
    context = _context(tmp_path)
    connection = context.database.connection
    repository = ExerciseRepository(connection)
    service = ExerciseService(repository)
    _clear_bundled_provenance(connection)
    bridge_id = repository.resolve("臀桥")["id"]
    clam_id = repository.resolve("蚌式开合")["id"]
    bridge_bundle = _bundle("臀桥")
    clam_bundle = _bundle("蚌式开合")
    before = {
        exercise_id: len(repository.get(exercise_id)["guidance"])
        for exercise_id in (bridge_id, clam_id)
    }
    original = repository.add_guidance_revision
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected bundled write failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(repository, "add_guidance_revision", fail_second)
    with pytest.raises(RuntimeError, match="injected bundled write failure"):
        service.accept_bundled_guidance(
            {
                bridge_bundle["exercise_key"]: bridge_id,
                clam_bundle["exercise_key"]: clam_id,
            }
        )

    assert repository.get(bridge_id)["bundled_exercise_key"] is None
    assert repository.get(clam_id)["bundled_exercise_key"] is None
    assert len(repository.get(bridge_id)["guidance"]) == before[bridge_id]
    assert len(repository.get(clam_id)["guidance"]) == before[clam_id]
    context.close()


def test_update_reopen_and_backup_keep_history_plan_and_prior_export_interpretable(
    tmp_path,
):
    context = _context(tmp_path)
    connection = context.database.connection
    _clear_bundled_provenance(connection)
    _plans, exercises, plan_id = _active_plan(context)
    bridge_id = exercises.resolve("臀桥")["id"]
    old_active_id = exercises.get(bridge_id)["active_guidance_revision_id"]
    old_active_content = deepcopy(exercises.get(bridge_id)["guidance"][0]["guidance"])

    training = context.training_service()
    completed = training.start(plan_id)
    training.record_result(completed["actions"][0]["id"], ExerciseResult.COMPLETED)
    completed = training.finish()
    paused = training.start(plan_id)
    paused = training.pause()
    prior_exports = HandoffService(connection, context.data_root.path).export()
    prior_bytes = {path.name: path.read_bytes() for path in prior_exports}

    service = ExerciseService(exercises)
    bridge_bundle = _bundle("臀桥")
    assert service.accept_bundled_guidance(
        {bridge_bundle["exercise_key"]: bridge_id}
    )
    source_root = context.data_root.path
    context.close()

    reopened = ApplicationContext.reopen(
        source_root, Locator(tmp_path / "reopen-locator.json")
    )
    reopened_exercises = ExerciseRepository(reopened.database.connection)
    bridge = reopened_exercises.get(bridge_id)
    assert bridge["active_guidance_revision_id"] == old_active_id
    assert bridge["guidance"][0]["guidance"] == old_active_content
    assert len(bridge["guidance"]) == 2
    assert reopened.session_repository().get(completed["id"])["actions"][0][
        "guidance_revision_id"
    ] == old_active_id
    assert reopened.session_repository().get_active()["id"] == paused["id"]
    assert reopened.plan_repository().get_plan(plan_id)["active_revision_id"] is not None
    for name, content in prior_bytes.items():
        assert (source_root / "exports" / name).read_bytes() == content

    backup_root = tmp_path / "backup"
    create_backup(source_root, backup_root, reopened.database.connection)
    reopened.close()
    restored = ApplicationContext.reopen(
        backup_root, Locator(tmp_path / "backup-locator.json")
    )
    restored_bridge = ExerciseRepository(restored.database.connection).get(bridge_id)
    assert restored_bridge["active_guidance_revision_id"] == old_active_id
    assert len(restored_bridge["guidance"]) == 2
    assert restored.session_repository().get(completed["id"])["actions"][0][
        "guidance_revision_id"
    ] == old_active_id
    assert restored.session_repository().get_active()["id"] == paused["id"]
    for name, content in prior_bytes.items():
        assert (backup_root / "exports" / name).read_bytes() == content
    restored.close()


class _DialogService:
    def __init__(self):
        self.accepted = []
        self.imported = []
        self.exercises = {
            7: {
                "id": 7,
                "canonical_name": "已有动作",
                "active_guidance_revision_id": None,
                "guidance": [],
            }
        }

    def preview_bundled_guidance(self):
        item = _bundle("臀桥")
        return [
            {
                **item,
                "match_status": "name_match",
                "target_exercise_id": 7,
                "target_exercise_name": "已有动作",
                "candidate_exercises": [{"id": 7, "canonical_name": "已有动作"}],
                "target_options": [{"id": 7, "canonical_name": "已有动作"}],
            }
        ]

    def get(self, exercise_id):
        return self.exercises.get(exercise_id)

    def accept_bundled_guidance(self, selections, import_keys=()):
        self.accepted.append(selections)
        self.imported.append(list(import_keys))
        return [99]


def test_update_dialog_previews_full_guidance_and_only_accepts_checked_items(
    qt_app, monkeypatch
):
    service = _DialogService()
    dialog = BundledGuidanceUpdateDialog(service)
    dialog.resize(680, 520)
    dialog.show()
    qt_app.processEvents()
    monkeypatch.setattr(QMessageBox, "information", lambda *_args: None)

    assert "强化" in dialog.guidance_view.toPlainText()
    assert "{" not in dialog.guidance_view.toPlainText()
    assert dialog.target_combo.currentData() == 7
    assert not dialog.accept_checkbox.isChecked()
    tabs_bottom = dialog.preview_tabs.mapTo(
        dialog, QPoint(0, dialog.preview_tabs.height())
    ).y()
    buttons_top = dialog.button_box.mapTo(dialog, QPoint(0, 0)).y()
    assert tabs_bottom <= buttons_top
    assert dialog.button_box.button(QDialogButtonBox.StandardButton.Save).isVisible()
    assert dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel).isVisible()

    dialog.accept_checkbox.setChecked(True)
    dialog.button_box.button(QDialogButtonBox.StandardButton.Save).click()

    assert service.accepted == [{_bundle("臀桥")["exercise_key"]: 7}]
    assert dialog.result() == QDialog.DialogCode.Accepted
    dialog.close()


def test_update_dialog_cancel_makes_no_write(qt_app):
    service = _DialogService()
    dialog = BundledGuidanceUpdateDialog(service)
    dialog.accept_checkbox.setChecked(True)

    dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel).click()

    assert service.accepted == []
    assert dialog.result() == QDialog.DialogCode.Rejected
    dialog.close()
