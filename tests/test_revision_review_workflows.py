import json
from copy import deepcopy
from datetime import datetime, timezone

import pytest
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from tests.test_phase4_sessions import FixedClock, _active_plan
from tests.test_phase6_handoff import _context, _import_payload
from tests.test_w2_guidance_ui import _clock_service, _exercise_with_revisions
from training_feedback.domain.plans import revision_from_snapshot
from training_feedback.ui.guidance_review_page import GuidanceReviewDialog
from training_feedback.ui.plan_activation_preview import PlanActivationPreview
from training_feedback.ui.plan_detail_page import PlanDetailPage
from training_feedback.ui.plan_page import PlanPage


@pytest.fixture(autouse=True)
def no_blocking_message_boxes(monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: None)


@pytest.mark.parametrize("reviewed_at", ["2026-09-01", "2026-09-01T09:30+08:00"])
def test_review_records_occurrence_precision_and_application_approval_clock(tmp_path, reviewed_at):
    context = _context(tmp_path)
    now = datetime(2026, 9, 12, 8, 30, tzinfo=timezone.utc)
    service = context.exercise_service(FixedClock(now))
    exercise = service.repository.get(service.repository.resolve("臀桥")["id"])
    revision_id = exercise["guidance"][0]["id"]
    source, note = "  外审原始来源  ", "原答复\r\n发生时间见原文  "
    service.confirm_guidance_review(revision_id, review_source=source,
                                    reviewed_at=reviewed_at, review_note=note, user_confirmed=True)
    saved = service.get(exercise["id"])["guidance"][0]["guidance"]["review"]
    assert saved["reviewed_at"] == reviewed_at
    assert saved["user_approved_at"] == now.isoformat()
    assert saved["review_source"] == source and saved["review_note"] == note
    assert saved["status"] == "active"
    root = context.data_root
    from training_feedback.data.locator import Locator

    locator = Locator(tmp_path / "locator.json")
    context.close()
    from training_feedback.app import ApplicationContext

    reopened = ApplicationContext.open(root, locator)
    reopened_guide = reopened.exercise_service().get(exercise["id"])["guidance"][0]
    assert reopened_guide["guidance"]["review"] == saved
    reopened.close()


@pytest.mark.parametrize("overrides", [
    {"reviewed_at": ""}, {"reviewed_at": "2026-02-30"},
    {"reviewed_at": "2026-09-01T09:30"}, {"reviewed_at": "yesterday"},
    {"reviewed_at": "2026-09-01T09:30+99:00"}, {"reviewed_at": None},
    {"reviewed_at": "2026-09-01T09:30+08:99"},
    {"review_source": "  "}, {"user_confirmed": False}, {"user_confirmed": 1},
])
def test_invalid_or_unconfirmed_review_writes_nothing(tmp_path, overrides):
    context = _context(tmp_path)
    service = context.exercise_service()
    exercise_id = service.repository.resolve("臀桥")["id"]
    before = service.get(exercise_id)
    values = dict(review_source="外审", reviewed_at="2026-09-01",
                  review_note="备注", user_confirmed=True)
    values.update(overrides)
    with pytest.raises(ValueError):
        service.confirm_guidance_review(before["guidance"][0]["id"], **values)
    assert service.get(exercise_id) == before
    context.close()


def test_confirmation_failure_rolls_back_old_and_new_guidance(tmp_path):
    context = _context(tmp_path)
    _, exercises, _ = _active_plan(context)
    service = context.exercise_service()
    exercise_id = exercises.resolve("臀桥")["id"]
    guidance = deepcopy(service.get(exercise_id)["guidance"][0]["guidance"])
    revision_id = service.add_guidance_draft(exercise_id, guidance)
    before = service.get(exercise_id)
    context.database.connection.execute(
        "CREATE TEMP TRIGGER reject_activation BEFORE UPDATE OF active_guidance_revision_id "
        "ON exercise BEGIN SELECT RAISE(ABORT, 'injected activation failure'); END"
    )
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError, match="injected"):
        service.confirm_guidance_review(revision_id, review_source="实际外审",
                                        reviewed_at="2026-09-01", user_confirmed=True)
    assert service.get(exercise_id) == before
    context.close()


def test_review_switch_clears_only_new_inputs_and_keeps_saved_evidence(qt_app):
    exercise = _exercise_with_revisions()
    before = deepcopy(exercise)
    dialog = GuidanceReviewDialog(_clock_service(), exercise, selected_revision_id=13)
    assert not dialog.source_edit.text() and not dialog.reviewed_at_edit.text()
    assert not dialog.note_edit.toPlainText()
    assert "待复核来源" in dialog.guidance_view.toPlainText()
    dialog.source_edit.setText("本次来源")
    dialog.reviewed_at_edit.setText("2026-09-01")
    dialog.note_edit.setPlainText("本次备注")
    dialog.approved.setChecked(True)
    dialog.revision_selector.setCurrentIndex(dialog.revision_selector.findData(12))
    assert not dialog.source_edit.text() and not dialog.reviewed_at_edit.text()
    assert not dialog.note_edit.toPlainText() and not dialog.approved.isChecked()
    assert exercise == before
    dialog.close()


def _multi_draft_context(tmp_path):
    context = _context(tmp_path)
    plans, _, plan_id = _active_plan(context)
    active = plans.get_plan(plan_id)["active_revision_id"]
    first = plans.clone_revision(plan_id, active)
    second = plans.clone_revision(plan_id, active)
    return context, plans, plan_id, active, first, second


def test_plan_selection_targets_older_draft_and_clones_selected_published(qt_app, tmp_path,
                                                                       monkeypatch):
    context, plans, plan_id, active, first, second = _multi_draft_context(tmp_path)
    page = PlanDetailPage(plans.get_plan(plan_id), plans, context.exercise_service())
    assert page.revision_selector.currentData() == active
    assert not page.edit_button.isEnabled() and not page.preview_button.isEnabled()
    page.revision_selector.setCurrentIndex(page.revision_selector.findData(first))
    opened = []

    class CancelledEditor:
        def __init__(self, repository, plan, revision, parent):
            opened.append(revision["id"])

        def exec(self):
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr("training_feedback.ui.plan_detail_page.PlanEditor", CancelledEditor)
    before = plans.get_plan(plan_id)
    page._edit_draft()
    assert opened == [first]
    assert plans.get_plan(plan_id) == before
    assert page.revision_selector.currentData() == first
    page.revision_selector.setCurrentIndex(page.revision_selector.findData(active))
    page._clone_selected_revision()
    created = page.revision_selector.currentData()
    assert created not in {active, first, second}
    assert plans.get_revision(plan_id, created)["status"] == "draft"
    page.close()
    context.close()


def test_stale_plan_target_is_refreshed_without_editing_another_draft(qt_app, tmp_path,
                                                                   monkeypatch):
    context, plans, plan_id, active, first, second = _multi_draft_context(tmp_path)
    page = PlanDetailPage(plans.get_plan(plan_id), plans, context.exercise_service(),
                          selected_revision_id=first)
    plans.activate_revision(plan_id, first)
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: warnings.append(a))
    page._edit_draft()
    assert warnings
    assert page.revision_selector.currentData() == first
    assert not page.edit_button.isEnabled()
    assert plans.get_revision(plan_id, second)["status"] == "draft"
    page.close()
    context.close()


def test_activation_preview_cancel_and_changed_draft_do_not_activate(qt_app, tmp_path,
                                                                  monkeypatch):
    context, plans, plan_id, active, first, _ = _multi_draft_context(tmp_path)
    draft = plans.get_revision(plan_id, first)
    dialog = PlanActivationPreview(plans, plans.get_plan(plan_id), draft)
    monkeypatch.setattr("training_feedback.ui.plan_activation_preview.confirm", lambda *a: False)
    dialog._confirm_activation()
    assert plans.get_plan(plan_id)["active_revision_id"] == active
    changed = deepcopy(draft)
    changed["purpose"] = "另一个窗口修改的未预览内容"
    plans.replace_draft_revision(plan_id, first, revision_from_snapshot(changed))
    monkeypatch.setattr("training_feedback.ui.plan_activation_preview.confirm", lambda *a: True)
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: warnings.append(a))
    dialog._confirm_activation()
    assert warnings and plans.get_plan(plan_id)["active_revision_id"] == active
    dialog.close()
    context.close()


def test_import_opens_exact_draft_and_keeps_original_basis_after_edit(qt_app, tmp_path,
                                                                  monkeypatch):
    context, plans, plan_id, *_ = _multi_draft_context(tmp_path)
    payload = _import_payload(target_plan_name=plans.get_plan(plan_id)["name"])
    payload["rationale"] = "  外部原始理由\n第二行  "
    source = tmp_path / "response.json"
    original_bytes = json.dumps(payload, ensure_ascii=False).encode()
    source.write_bytes(original_bytes)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a: (str(source), ""))
    monkeypatch.setattr(QMessageBox, "information", lambda *a: None)
    page = PlanPage(context)
    page._import_plan()
    detail = page.detail_page
    revision_id = detail.revision_selector.currentData()
    provenance = plans.get_import_for_revision(plan_id, revision_id)
    assert provenance["rationale"] == payload["rationale"]
    assert payload["rationale"] in detail.import_basis.toPlainText()
    assert detail.isWindow()
    changed = plans.get_revision(plan_id, revision_id)
    changed["purpose"] = "本地另作调整"
    plans.replace_draft_revision(plan_id, revision_id, revision_from_snapshot(changed))
    detail._refresh_plan()
    assert payload["rationale"] in detail.import_basis.toPlainText()
    assert (context.data_root.path / provenance["source_path"]).read_bytes() == original_bytes
    assert plans.get_import_for_revision(plan_id + 999, revision_id) is None
    detail.close()
    page.close()
    context.close()


def test_no_active_defaults_newest_draft_and_missing_explicit_target_stays_unselected(qt_app,
                                                                                  tmp_path):
    context = _context(tmp_path)
    plans = context.plan_repository()
    plan = plans.get_plan(plans.list_plans()[0]["id"])
    newest = plans.clone_revision(plan["id"], plan["revisions"][0]["id"])
    page = PlanDetailPage(plans.get_plan(plan["id"]), plans)
    assert page.revision_selector.currentData() == newest
    missing = PlanDetailPage(plans.get_plan(plan["id"]), plans, selected_revision_id=-1)
    assert missing.revision_selector.currentIndex() == -1
    assert not missing.edit_button.isEnabled() and not missing.preview_button.isEnabled()
    missing.close()
    page.close()
    context.close()


def test_older_selected_draft_preview_activates_only_that_version(qt_app, tmp_path, monkeypatch):
    context, plans, plan_id, active, first, second = _multi_draft_context(tmp_path)
    page = PlanDetailPage(plans.get_plan(plan_id), plans, context.exercise_service(),
                          selected_revision_id=first)
    monkeypatch.setattr("training_feedback.ui.plan_activation_preview.confirm", lambda *a: True)

    def activate(dialog):
        dialog._confirm_activation()
        return dialog.result()

    monkeypatch.setattr(PlanActivationPreview, "exec", activate)
    page._preview_draft()
    assert plans.get_plan(plan_id)["active_revision_id"] == first
    assert plans.get_revision(plan_id, second)["status"] == "draft"
    page.revision_selector.setCurrentIndex(page.revision_selector.findData(active))
    assert page.clone_button.isEnabled() and not page.edit_button.isEnabled()
    page.resize(520, 440)
    page.show()
    qt_app.processEvents()
    assert page.height() == 440
    for button in (page.clone_button, page.preview_button, page.review_button, page.edit_button):
        assert not button.visibleRegion().isEmpty()
    page.close()
    context.close()
