"""Native grouped execution regression checks against actual temporary services."""

from datetime import timedelta

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox
from test_070_group_execution import controller, dose
from test_070_group_plans import context, payload

from training_feedback.ui.group_session_page import GroupFeedbackDialog
from training_feedback.ui.group_training_page import ExecutionPreview, GroupTrainingPage
from training_feedback.ui.labels import session_history_text

__all__ = ["context", "payload", "controller"]


@pytest.fixture
def page(qt_app, controller, monkeypatch):
    monkeypatch.setattr("training_feedback.ui.group_training_page.confirm", lambda *args: True)
    result = GroupTrainingPage(controller)
    yield result
    result.leaving = True


def test_ui_save_stays_at_current_and_repeated_click_does_not_spill(page, controller):
    page.result_buttons["completed"].click()
    assert controller.current["position"] == 0
    assert controller.current["result"] == "completed"
    page.choose_result("completed")
    assert controller.session["occurrences"][1]["result"] is None
    page.next_button.click()
    assert controller.current["position"] == 1
    assert controller.current["result"] is None
    assert "左侧" in page.title.text() and "第 1/2 轮" in page.title.text()


def test_actual_entry_is_blank_side_locked_invalid_preserved_and_cancel_safe(
    page, controller, monkeypatch
):
    page.resize(680, 560)
    page.show()
    assert not page.scroll.isAncestorOf(page.controls)
    assert not page.scroll.isAncestorOf(page.pending_controls)
    assert page.images.itemAt(0).widget().pixmap() is not None
    assert "停止条件" in page.guidance.toPlainText()
    errors = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: errors.append(args[2]))
    page.selector.setCurrentIndex(1)
    page.note.setPlainText("  单侧原文  ")
    page.choose_result("partial")
    assert page.actual.item(0, 0).text() == ""
    assert not (page.actual.item(0, 2).flags() & Qt.ItemFlag.ItemIsEditable)
    assert page.actual.item(0, 2).text() == "左侧"
    assert not page.selector.isEnabled()
    page.actual.item(0, 0).setText("NaN")
    page.save_pending()
    assert errors and page.pending == "partial"
    assert page.actual.item(0, 0).text() == "NaN"
    assert controller.current["result"] is None
    page.cancel_pending()
    assert page.note.toPlainText() == "  单侧原文  "
    page.choose_result("partial")
    page.actual.item(0, 0).setText("0")
    page.save_pending()
    assert controller.current["actual_sets"][0]["value"] == 0
    assert controller.current["actual_sets"][0]["side"] == "left"
    assert controller.current["note"] == "  单侧原文  "
    assert controller.session["occurrences"][3]["result"] is None


def test_declined_discard_keeps_position_pending_and_unsaved_work(page, controller, monkeypatch):
    monkeypatch.setattr("training_feedback.ui.group_training_page.confirm", lambda *args: False)
    page.note.setPlainText("尚未保存")
    page.selector.setCurrentIndex(2)
    assert page.selector.currentIndex() == 0 and controller.current["position"] == 0
    assert page.note.toPlainText() == "尚未保存"
    page.choose_result("partial")
    page.actual.item(0, 0).setText("3")
    page.pause()
    assert controller.session["status"] == "open"
    assert controller.current["result"] is None
    assert page.actual.item(0, 0).text() == "3"


def test_round_dialog_lists_both_sides_and_exact_prescription(page, controller, monkeypatch):
    previews = []

    def accepted(dialog):
        previews.append(dialog.text.toPlainText())
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(ExecutionPreview, "exec", accepted)
    page.selector.setCurrentIndex(1)
    page.round_button.click()
    assert "左侧" in previews[0] and "右侧" in previews[0]
    assert "第 1/2 轮" in previews[0] and "第 2/2 轮" not in previews[0]
    assert "组间休息 0 秒" in previews[0]
    assert controller.current["position"] == 1
    assert all(row["result"] is None for row in controller.session["occurrences"][5:])
    page.retract_button.click()
    assert controller.current["result"] is None
    assert controller.session["events"][-1]["kind"] == "result_retracted"


def test_hub_resume_and_frozen_history_feedback_do_not_infer_answers(
    qt_app, context, controller, monkeypatch, tmp_path
):
    controller.navigate(1)
    controller.record("partial", actual=[dose(controller.current, 0)], note="  原文  ")
    controller.pause()
    hub = context.create_session_page()
    hub.resize(820, 650)
    hub.show()
    qt_app.processEvents()
    assert not hub.start_button.isEnabled() and hub.resume_button.isEnabled()
    assert "左侧" in hub.detail.toPlainText() and "用户填写" in hub.detail.toPlainText()
    hub.resume()
    restored = hub.training_window.controller
    assert restored.current["position"] == 1
    restored.abort("other", "  原因  ", user_confirmed=True)
    hub.training_window.leaving = True
    hub.training_window.close()
    context.sessions.clock.value += timedelta(days=1)
    hub.refresh()
    assert hub.feedback_button.isEnabled()
    dialog = GroupFeedbackDialog(context.sessions, restored.session)
    assert all(widget.currentIndex() == -1 for widget in dialog.areas.values())
    dialog.note.setPlainText("  未选择部位值  ")
    dialog.save()
    assert dialog.result() == QDialog.DialogCode.Accepted
    saved = context.sessions.get(restored.session["id"])
    assert saved["feedback"]["areas"] == [{"name": "臀部", "value": None}]
    assert "未知（未回答）" in session_history_text(saved)
    assert "  原因  " in session_history_text(saved)
    hub.refresh()
    assert hub.correct_button.isEnabled() and not hub.feedback_button.isEnabled()
    assert hub.grab().save(str(tmp_path / "history.png"))
