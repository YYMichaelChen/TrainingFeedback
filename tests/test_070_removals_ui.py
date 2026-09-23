"""Lifecycle UI keeps user input on failure and exposes exact batch impact/history."""

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox
from test_070_group_plans import context, payload
from test_070_removals import decide, remove, request, targets

from training_feedback.ui.library_lifecycle_page import LifecycleRequestDialog

__all__ = ["context", "payload"]


@pytest.fixture
def warnings(monkeypatch):
    result = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: result.append(args[-1]))
    return result


def test_request_lists_batch_impact_and_preserves_reason_on_stale_save(
    qt_app, context, payload, warnings,
):
    selected = targets(context, payload)
    dialog = LifecycleRequestDialog(context.removals, selected)
    dialog.show()
    dialog.reason.setPlainText("  原因\t\n保留  ")
    assert dialog.confirmed.isChecked() is False
    dialog.preview_button.click()
    for target in selected:
        assert target.content["sha256"] in dialog.details.toPlainText()
    context.plans.create(payload)
    dialog.confirmed.setChecked(True)
    dialog.submit.click()
    assert warnings and context.removals.requests() == []
    assert dialog.reason.toPlainText() == "  原因\t\n保留  "
    assert dialog.result() != QDialog.DialogCode.Accepted
    dialog.preview_button.click()
    assert not dialog.confirmed.isChecked()
    assert "引用组合" in dialog.details.toPlainText()
    dialog.confirmed.setChecked(True)
    dialog.submit.click()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert context.removals.get(dialog.saved_id)["reason"] == "  原因\t\n保留  "


def test_decision_flow_requires_source_time_and_explicit_confirmation(
    qt_app, context, payload, warnings,
):
    identifier = request(context, targets(context, payload)[:1])
    page = context.create_removal_page()
    page.resize(960, 700)
    page.show()
    qt_app.processEvents()
    assert page.source.text() == page.occurred.text() == ""
    assert not page.confirmed.isChecked()
    assert not page.actions["approved"].isEnabled()
    page.actions["preview"].click()
    page.confirmed.setChecked(True)
    page.actions["under_review"].click()
    assert warnings and context.removals.get(identifier)["status"] == "requested"
    page.self_source.click()
    page.occurred.setText("2026-09-20")
    page.note.setPlainText("  保留审核备注  ")
    page.actions["under_review"].click()
    assert context.removals.get(identifier)["status"] == "under_review"
    assert not page.confirmed.isChecked()
    page.actions["preview"].click()
    page.confirmed.setChecked(True)
    page.actions["approve_apply"].click()
    assert context.removals.get(identifier)["status"] == "applied"
    assert "保留审核备注" in page.details.toPlainText()
    assert not page.actions["applied"].isEnabled()
    for button in page.actions.values():
        assert button.isVisible()
        assert button.mapTo(page, button.rect().bottomRight()).y() < page.height()


def test_stale_request_rejected_without_losing_note(qt_app, context, payload, warnings):
    identifier = request(context, targets(context, payload)[:1])
    page = context.create_removal_page()
    page.note.setPlainText("尚未保存")
    page.source.setText("本人")
    page.occurred.setText("2026-09-20")
    page.actions["preview"].click()
    decide(context, identifier, "under_review")
    page.confirmed.setChecked(True)
    page.actions["under_review"].click()
    assert warnings and page.note.toPlainText() == "尚未保存"
    assert len(context.removals.get(identifier)["events"]) == 2


def test_restore_picker_invalidates_previous_confirmation(qt_app, context, payload, warnings):
    selected = targets(context, payload)[:1]
    remove(context, selected)
    dialog = LifecycleRequestDialog(context.removals, selected)
    dialog.operation.setCurrentIndex(dialog.operation.findData("restore"))
    dialog.preview_button.click()
    assert dialog.preview["operation"] == "restore"
    dialog.confirmed.setChecked(True)
    dialog.operation.setCurrentIndex(0)
    assert dialog.preview is None and not dialog.submit.isEnabled()
    assert not dialog.confirmed.isChecked()
    dialog.operation.setCurrentIndex(1)
    dialog.preview_button.click()
    dialog.reason.setPlainText("当前版本已重新核对")
    dialog.confirmed.setChecked(True)
    dialog.submit.click()
    assert context.removals.get(dialog.saved_id)["operation"] == "restore"
