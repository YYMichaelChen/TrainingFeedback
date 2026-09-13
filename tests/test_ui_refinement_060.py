import json
import sqlite3

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialogButtonBox, QMessageBox

from tests.test_phase4_sessions import _active_plan
from training_feedback.app import ApplicationContext
from training_feedback.data.data_root import create_new
from training_feedback.data.handoff import HandoffService, render_markdown
from training_feedback.data.locator import Locator
from training_feedback.domain.enums import DoseUnit, ExerciseResult
from training_feedback.domain.models import ActualSet
from training_feedback.ui.main_window import MainWindow
from training_feedback.ui.plan_editor import PlanEditor
from training_feedback.ui.theme import apply_theme
from training_feedback.ui.training_page import TrainingPage


@pytest.fixture
def training(tmp_path):
    context = ApplicationContext.open(create_new(tmp_path / "data"), Locator(tmp_path / "locator"))
    _, _, plan_id = _active_plan(context)
    service = context.training_service()
    service.start(plan_id)
    yield context, service
    context.close()


def test_retraction_keeps_audit_and_prescription_through_reopen_and_export(training):
    context, service = training
    action = service.session["actions"][0]
    service.record_result(action["id"], ExerciseResult.EXCEEDED, note="  原文\r\n备注  ",
                          actual_sets=(ActualSet(20, DoseUnit.REPS, True),) * 2)
    previous = service.session["actions"][0]
    service.pause()
    service.retract_result(action["id"])
    reset = service.session["actions"][0]
    assert reset["result"] is None and reset["note"] is None
    assert reset["actual_sets"] == []
    assert all(item["actual_value"] is None for item in reset["sets"])
    assert reset["sets"][0]["planned_value"] == action["sets"][0]["planned_value"]
    assert service.session["result_retractions"][0]["previous_action"] == previous
    root, locator = context.data_root, context.locator
    context.close()
    reopened = ApplicationContext.open(root, locator)
    try:
        resumed = reopened.training_service()
        resumed.resume()
        assert resumed.session["result_retractions"][0]["previous_action"] == previous
        resumed.record_result(action["id"], ExerciseResult.PARTIAL, actual_values=(7,))
        resumed.finish()
        evidence = HandoffService(reopened.database.connection, root.path).build_evidence()
        assert evidence["sessions"][0]["actions"][0]["result"] == "partial"
        assert "结果撤回" in render_markdown(evidence)
        assert "20.0 reps" in render_markdown(evidence)
        assert json.loads(json.dumps(evidence))["sessions"][0]["result_retractions"]
        with pytest.raises(ValueError, match="Only an open"):
            resumed.retract_result(action["id"])
    finally:
        reopened.close()


def test_retraction_rolls_back_audit_and_result_if_any_write_fails(training):
    context, service = training
    action_id = service.session["actions"][0]["id"]
    service.record_result(action_id, ExerciseResult.EXCEEDED, actual_values=(15,))
    before = service.session
    context.database.connection.execute(
        "CREATE TRIGGER reject_reset BEFORE UPDATE OF result ON training_session_action "
        "WHEN NEW.result IS NULL BEGIN SELECT RAISE(ABORT, 'injected reset failure'); END"
    )
    with pytest.raises(sqlite3.IntegrityError, match="injected reset"):
        service.retract_result(action_id)
    assert context.session_repository().get(before["id"]) == before


def test_cannot_retract_another_session_or_unrecorded_action(training):
    context, service = training
    action_id = service.session["actions"][0]["id"]
    with pytest.raises(ValueError, match="Select a recorded"):
        service.retract_result(action_id)
    service.record_result(action_id, ExerciseResult.COMPLETED)
    with pytest.raises(ValueError, match="Select a recorded"):
        service.retract_result(action_id + 100)
    assert context.session_repository().get(service.session["id"])["result_retractions"] == []


def test_finish_rechecks_results_when_retraction_races_final_save(training, monkeypatch):
    context, service = training
    action_id = service.session["actions"][0]["id"]
    session_id = service.session["id"]
    service.record_result(action_id, ExerciseResult.COMPLETED)
    get = service.sessions.get
    first = True

    def race_get(identifier):
        nonlocal first
        snapshot = get(identifier)
        if first:
            first = False
            service.sessions.retract_action_result(session_id, action_id, service.clock.now())
        return snapshot

    monkeypatch.setattr(service.sessions, "get", race_get)
    with pytest.raises(ValueError, match="Every exercise"):
        service.finish()
    assert context.session_repository().get(session_id)["status"] == "open"
    assert context.session_repository().get(session_id)["actions"][0]["result"] is None


def test_pending_entry_cannot_be_closed_or_paused_without_explicit_discard(
    qt_app, training, monkeypatch,
):
    _, service = training
    page = TrainingPage(service)
    page.show()
    page._record(ExerciseResult.PARTIAL)
    page.value_edits[0].setText("4")
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.No)
    assert not page.close()
    page._pause()
    assert service.session["status"] == "open"
    assert page.value_edits[0].text() == "4"
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.Yes)
    page._pause()
    assert service.session["status"] == "paused"
    assert service.session["actions"][0]["result"] is None
    page.close()


def test_actual_entry_cannot_accidentally_record_other_result(qt_app, training):
    _, service = training
    page = TrainingPage(service)
    page.result_button_by_value[ExerciseResult.PARTIAL].click()
    page.value_edits[0].setText("7")
    assert page.result_choices.isHidden()
    assert not page.action_selector.isEnabled()
    page._record(ExerciseResult.COMPLETED)
    assert service.session["actions"][0]["result"] is None
    page.cancel_result_button.click()
    assert not page.result_choices.isHidden()
    assert service.session["actions"][0]["result"] is None
    page.result_button_by_value[ExerciseResult.EXCEEDED].click()
    assert page.value_edits[0].text() == ""
    page.value_edits[0].setText("16")
    page.save_result_button.click()
    assert service.session["actions"][0]["result"] == "exceeded"
    assert page.result_choices.isHidden()
    assert not page.retract_button.isHidden()
    page.close()


def test_saved_result_stays_visible_and_retraction_requires_confirmation(
    qt_app, training, monkeypatch,
):
    _, service = training
    page = TrainingPage(service)
    page.result_button_by_value[ExerciseResult.COMPLETED].click()
    page.result_button_by_value[ExerciseResult.NOT_COMPLETED].click()
    assert service.session["actions"][0]["result"] == "completed"
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.No)
    page.retract_button.click()
    assert service.session["actions"][0]["result"] == "completed"
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.Yes)
    page.retract_button.click()
    assert service.session["actions"][0]["result"] is None
    assert len(service.session["result_retractions"]) == 1
    assert not page.finish_button.isEnabled()
    page.close()


def test_invalid_plan_dose_blocks_switch_and_save_without_losing_text(
    qt_app, training, monkeypatch,
):
    context, _ = training
    repository = context.plan_repository()
    plan = repository.get_plan(repository.list_plans()[0]["id"])
    revision = plan["revisions"][0]
    editor = PlanEditor(repository, plan, revision)
    editor.table.item(0, 1).setText("不是数字")
    editor.action_selector.setCurrentRow(3)
    assert editor.action_selector.currentRow() == 0
    assert editor.table.item(0, 1).text() == "不是数字"
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: warnings.append(a))
    editor._save()
    assert warnings
    assert repository.get_revision(plan["id"], revision["id"]) == revision
    editor.table.item(0, 1).setText("9")
    editor.action_selector.setCurrentRow(3)
    editor.action_selector.setCurrentRow(0)
    assert float(editor.table.item(0, 1).text()) == 9
    editor.close()


def test_plan_batch_panel_scrolls_without_hiding_dialog_save(qt_app, training):
    context, _ = training
    repo = context.plan_repository()
    plan = repo.get_plan(repo.list_plans()[0]["id"])
    editor = PlanEditor(repo, plan, plan["revisions"][0])
    editor.resize(860, 620)
    editor.show()
    editor.equal_toggle.setChecked(True)
    QTest.qWait(50)
    save = editor.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save)
    assert editor.height() == 620
    assert save.isVisible() and not save.visibleRegion().isEmpty()
    assert editor.editor_scroll.verticalScrollBar().maximum() > 0
    editor.close()


def test_themed_small_training_window_keeps_save_and_session_controls_fixed(qt_app, training):
    context, service = training
    old_style, old_palette, old_font = qt_app.styleSheet(), qt_app.palette(), qt_app.font()
    apply_theme(qt_app)
    window = MainWindow(context)
    page = TrainingPage(service)
    try:
        window.show()
        page.resize(520, 440)
        page.show()
        page._record(ExerciseResult.PARTIAL)
        for _ in range(10):
            page._add_actual_set()
        QTest.qWait(50)
        controls = (page.save_result_button, page.cancel_result_button,
                    page.pause_button, page.abort_button, page.finish_button)
        assert page.width() == 520 and page.height() == 440
        assert page.scroll_area.verticalScrollBar().maximum() > 0
        assert all(
            button.isVisible() and not button.visibleRegion().isEmpty() for button in controls
        )
        positions = [button.mapToGlobal(QPoint()) for button in controls]
        page.scroll_area.verticalScrollBar().setValue(99999)
        QTest.qWait(20)
        assert [button.mapToGlobal(QPoint()) for button in controls] == positions
    finally:
        page._cancel_result()
        page.close()
        window.close()
        qt_app.setStyleSheet(old_style)
        qt_app.setPalette(old_palette)
        qt_app.setFont(old_font)
