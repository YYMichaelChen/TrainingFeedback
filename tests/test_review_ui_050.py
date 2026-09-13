"""0.5.0 界面：批量审核对话框与内置动作导入选项。

对话框在成功和失败路径都会弹模态提示，测试统一打桩为无操作，只断言写入结果。
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from training_feedback.app import ApplicationContext
from training_feedback.data.data_root import create_new
from training_feedback.data.locator import Locator
from training_feedback.data.review_attachments import REVIEWS_DIRECTORY
from training_feedback.ui.bundled_guidance_update_dialog import (
    IMPORT_AS_NEW,
    BundledGuidanceUpdateDialog,
)
from training_feedback.ui.guidance_batch_review_page import GuidanceBatchReviewDialog


@pytest.fixture(autouse=True)
def _silent_message_boxes(monkeypatch):
    for name in ("information", "warning", "critical"):
        monkeypatch.setattr(QMessageBox, name, lambda *_args, **_kwargs: None)


def _context(tmp_path):
    return ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )


def _row_of(dialog, exercise_name):
    for row in range(dialog.revision_list.count()):
        if dialog.items[row]["exercise_name"] == exercise_name:
            return row
    raise AssertionError(f"{exercise_name} is not listed")


def test_batch_dialog_starts_with_nothing_checked_and_save_disabled(qt_app, tmp_path):
    context = _context(tmp_path)
    dialog = GuidanceBatchReviewDialog(context.exercise_service())

    assert dialog.revision_list.count() == 14
    assert dialog.selected_revision_ids() == []
    assert dialog.button_box.button(dialog.button_box.StandardButton.Save).isEnabled() is False
    assert "已勾选 0 / 14" in dialog.summary_label.text()
    dialog.close()
    context.close()


def test_batch_dialog_approves_only_checked_rows_with_shared_evidence(qt_app, tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    dialog = GuidanceBatchReviewDialog(service)
    answer = tmp_path / "answer.md"
    answer.write_text("逐项结论", encoding="utf-8")
    for name in ("臀桥", "死虫式"):
        dialog.revision_list.item(_row_of(dialog, name)).setCheckState(Qt.CheckState.Checked)
    dialog.source_edit.setText("外部 AI 会话 B")
    dialog.reviewed_at_edit.setText("2026-09-13")
    dialog.note_edit.setPlainText("原始答复见受管原件")
    dialog.answer_file = answer
    dialog.approved.setChecked(True)

    dialog._approve()

    assert dialog.approved_count == 2
    approved_names = {
        exercise["canonical_name"]
        for exercise in service.list(include_inactive=True)
        if service.get(exercise["id"])["active_guidance_revision_id"] is not None
    }
    assert approved_names == {"臀桥", "死虫式"}
    stored = list((context.data_root.path / REVIEWS_DIRECTORY).iterdir())
    assert len(stored) == 1
    context.close()


def test_batch_dialog_requires_the_explicit_approval_checkbox(qt_app, tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    dialog = GuidanceBatchReviewDialog(service)
    dialog.revision_list.item(_row_of(dialog, "臀桥")).setCheckState(Qt.CheckState.Checked)
    dialog.source_edit.setText("外部 AI")
    dialog.reviewed_at_edit.setText("2026-09-13")

    dialog._approve()

    assert dialog.approved_count == 0
    assert all(
        service.get(exercise["id"])["active_guidance_revision_id"] is None
        for exercise in service.list(include_inactive=True)
    )
    dialog.close()
    context.close()


def test_batch_dialog_keeps_inputs_when_the_occurrence_is_invalid(qt_app, tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    dialog = GuidanceBatchReviewDialog(service)
    dialog.revision_list.item(_row_of(dialog, "臀桥")).setCheckState(Qt.CheckState.Checked)
    dialog.source_edit.setText("外部 AI")
    dialog.reviewed_at_edit.setText("昨天")
    dialog.approved.setChecked(True)

    dialog._approve()

    assert dialog.approved_count == 0
    assert dialog.source_edit.text() == "外部 AI"
    assert dialog.selected_revision_ids() != []
    assert not (context.data_root.path / REVIEWS_DIRECTORY).exists()
    dialog.close()
    context.close()


def test_bundled_dialog_offers_import_for_missing_exercises_only(qt_app, tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    bridge = service.repository.get_by_bundled_key("launch.glute-bridge")
    with service.repository.transaction():
        service.repository.connection.execute(
            "DELETE FROM training_plan_set WHERE action_id IN "
            "(SELECT id FROM training_plan_action WHERE exercise_id = ?)",
            (bridge["id"],),
        )
        for table in (
            "training_plan_action",
            "exercise_guidance_revision",
            "exercise_body_area",
            "exercise_alias",
        ):
            service.repository.connection.execute(
                f"DELETE FROM {table} WHERE exercise_id = ?", (bridge["id"],)
            )
        service.repository.connection.execute(
            "DELETE FROM exercise WHERE id = ?", (bridge["id"],)
        )

    dialog = BundledGuidanceUpdateDialog(service)
    missing_row = next(
        row
        for row in range(dialog.bundle_list.count())
        if dialog.bundle_list.item(row).data(Qt.ItemDataRole.UserRole)
        == "launch.glute-bridge"
    )
    dialog.bundle_list.setCurrentRow(missing_row)
    assert dialog.target_combo.findData(IMPORT_AS_NEW) >= 0

    other_row = next(
        row
        for row in range(dialog.bundle_list.count())
        if dialog.bundle_list.item(row).data(Qt.ItemDataRole.UserRole)
        != "launch.glute-bridge"
    )
    dialog.bundle_list.setCurrentRow(other_row)
    assert dialog.target_combo.findData(IMPORT_AS_NEW) == -1

    dialog.bundle_list.setCurrentRow(missing_row)
    dialog.target_combo.setCurrentIndex(dialog.target_combo.findData(IMPORT_AS_NEW))
    dialog.accept_checkbox.setChecked(True)
    dialog._apply()

    imported = service.repository.get_by_bundled_key("launch.glute-bridge")
    assert imported is not None
    detail = service.get(imported["id"])
    assert detail["canonical_name"] == "臀桥"
    assert detail["active_guidance_revision_id"] is None
    context.close()
