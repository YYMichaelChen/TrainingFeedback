from copy import deepcopy

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QWidget

from tests.guidance_fixtures import complete_guidance as starter_guidance
from training_feedback.domain.exercises import GuidanceStatus
from training_feedback.ui.exercise_detail_page import ExerciseDetailPage
from training_feedback.ui.exercise_editor import ExerciseEditor
from training_feedback.ui.guidance_review_page import GuidanceReviewDialog
from training_feedback.ui.guidance_widgets import GuidanceForm, GuidanceStepsEditor, GuidanceView
from training_feedback.ui.plan_detail_page import PlanDetailPage


def _revision(revision_id: int, number: int, guidance: dict) -> dict:
    return {
        "id": revision_id,
        "revision_number": number,
        "created_at": f"2026-09-0{number}T00:00:00+00:00",
        "guidance": guidance,
    }


def _exercise_with_revisions() -> dict:
    active = starter_guidance("测试动作")
    active["purpose"] = "当前版本目的"
    active["review"] = {
        "status": GuidanceStatus.ACTIVE.value,
        "reviewer_type": "external_ai_expert",
        "review_source": "专家记录 A",
        "review_note": "保持动作稳定。",
        "reviewed_at": "2026-09-01T00:00:00+00:00",
        "user_approved_at": "2026-09-01T00:00:00+00:00",
    }
    draft = starter_guidance("测试动作")
    draft["purpose"] = "待复核的新目的"
    draft["intended_sensations"] = ["第一处感受", "第二处感受"]
    pending = deepcopy(draft)
    pending["purpose"] = "明确选择的第三版"
    pending["review"] = {
        **pending["review"],
        "status": GuidanceStatus.PENDING_REVIEW.value,
        "reviewer_type": "external_ai_expert",
        "review_source": "待复核来源",
        "review_note": "待复核备注",
    }
    return {
        "id": 7,
        "canonical_name": "测试动作",
        "category": "main",
        "equipment_summary": "瑜伽垫",
        "aliases": ["测试别名"],
        "body_areas": [
            {"name": "核心", "is_primary": 1},
            {"name": "髋部", "is_primary": 0},
        ],
        "active": 1,
        "active_guidance_revision_id": 11,
        "guidance": [
            _revision(11, 1, active),
            _revision(12, 2, draft),
            _revision(13, 3, pending),
        ],
    }


def test_guidance_view_covers_every_required_field_without_raw_json(qt_app):
    guidance = starter_guidance("长内容动作")
    guidance["intended_sensations"] = ["目标区域稳定发力", "呼吸保持顺畅"]
    guidance["common_compensations"] = ["耸肩", "屏息"]
    guidance["equipment"] = ["瑜伽垫"]
    view = GuidanceView(guidance)

    text = view.toPlainText()

    for heading in (
        "训练目的",
        "起始姿势",
        "动作步骤",
        "呼吸",
        "节奏或保持",
        "应有感受",
        "常见代偿",
        "停止条件",
        "退阶方式",
        "进阶方式",
        "所需器械",
        "适用情况",
        "注意事项",
        "图片",
        "审核状态",
        "审核来源",
    ):
        assert heading in text
    assert "1. 目标区域稳定发力" in text
    assert "2. 呼吸保持顺畅" in text
    assert "暂无可用图片" in text
    assert "'purpose'" not in text
    assert '"purpose"' not in text


def test_guidance_form_round_trip_preserves_verbatim_text_and_unknown_data(qt_app):
    guidance = starter_guidance("逐字动作")
    guidance["purpose"] = "  保留两侧空格\n以及换行  "
    guidance["steps"] = [{"order": 7, "text": "  第一步\n仍是同一步  ", "source": "保留"}]
    guidance["intended_sensations"] = ["  感受一  ", "感受二\n续行"]
    guidance["images"] = [
        {"status": "missing", "path": None, "caption": "  暂无图片  ", "credit": "保留"}
    ]
    guidance["extension"] = {"author_text": "不能丢失"}
    form = GuidanceForm(guidance)

    assert form.guidance() == guidance

    edited = "\n 用户修改后的目的，空白也保留。 \n"
    form.scalar_edits["purpose"].setPlainText(edited)
    saved = form.guidance()
    assert saved["purpose"] == edited
    assert saved["steps"] == guidance["steps"]
    assert saved["intended_sensations"] == guidance["intended_sensations"]
    assert saved["images"] == guidance["images"]
    assert saved["extension"] == guidance["extension"]


def test_editor_uses_explicit_selected_revision_as_new_draft_source(qt_app):
    calls = []

    class RecordingService:
        def edit_exercise(self, *args):
            calls.append(args)

    exercise = _exercise_with_revisions()
    editor = ExerciseEditor(RecordingService(), exercise)

    assert "版本 1" in editor.active_revision_label.text()
    assert "版本 2" in editor.draft_revisions_label.text()
    assert "版本 3" in editor.draft_revisions_label.text()
    editor.guidance_selector.setCurrentIndex(editor.guidance_selector.findData(13))
    assert "待复核来源" in editor.selected_review_label.text()
    assert "当前版本目的" in editor.guidance_changes.toPlainText()
    assert "明确选择的第三版" in editor.guidance_changes.toPlainText()
    editor.guidance_selector.setCurrentIndex(editor.guidance_selector.findData(12))
    assert editor.guidance_form.scalar_edits["purpose"].toPlainText() == "待复核的新目的"
    editor.guidance_form.scalar_edits["purpose"].setPlainText("  逐字保存的新草稿  ")

    editor._save()

    assert editor.result() == QDialog.DialogCode.Accepted
    assert calls[0][0] == exercise["id"]
    assert calls[0][6]["purpose"] == "  逐字保存的新草稿  "
    editor.close()


def test_detail_selection_shows_revision_identity_review_source_and_changes(qt_app):
    exercise = _exercise_with_revisions()

    class Repository:
        def get(self, _exercise_id):
            return exercise

    class Service:
        repository = Repository()

    page = ExerciseDetailPage(exercise, Service())

    assert "版本 1" in page.active_revision_label.text()
    assert "版本 2" in page.draft_revisions_label.text()
    assert page.primary_areas_label.text() == "主要训练区域：核心"
    assert page.secondary_areas_label.text() == "次要训练区域：髋部"
    page.guidance_selector.setCurrentIndex(page.guidance_selector.findData(13))
    content = page.guidance_view.toPlainText()
    changes = page.guidance_changes.toPlainText()
    assert "明确选择的第三版" in content
    assert "待复核来源" in content
    assert "当前版本目的" in changes
    assert "明确选择的第三版" in changes
    assert page.review_button.isEnabled()
    page.close()


def test_review_dialog_cancel_is_read_only_and_approval_targets_visible_revision(qt_app):
    calls = []

    class RecordingService:
        def review_and_activate_guidance(self, revision_id, review):
            calls.append((revision_id, review))

    exercise = _exercise_with_revisions()
    cancelled = GuidanceReviewDialog(RecordingService(), exercise, selected_revision_id=12)
    assert cancelled.revision_selector.currentData() == 12
    assert "待复核的新目的" in cancelled.guidance_view.toPlainText()
    cancelled.reject()
    assert calls == []

    dialog = GuidanceReviewDialog(RecordingService(), exercise, selected_revision_id=13)
    assert "待复核来源" in dialog.guidance_view.toPlainText()
    dialog.source_edit.setText("  本次审核来源  ")
    dialog.note_edit.setPlainText("  本次审核备注  ")
    dialog.approved.setChecked(True)
    dialog._approve()

    assert calls[0][0] == 13
    assert calls[0][1]["review_source"] == "  本次审核来源  "
    assert calls[0][1]["review_note"] == "  本次审核备注  "
    assert dialog.result() == QDialog.DialogCode.Accepted
    dialog.close()


def test_review_dialog_never_approves_without_explicit_checkbox(qt_app, monkeypatch):
    calls = []
    warnings = []

    class RecordingService:
        def review_and_activate_guidance(self, *args):
            calls.append(args)

    monkeypatch.setattr(
        "training_feedback.ui.guidance_review_page.QMessageBox.warning",
        lambda *args: warnings.append(args),
    )
    dialog = GuidanceReviewDialog(
        RecordingService(), _exercise_with_revisions(), selected_revision_id=12
    )
    dialog.source_edit.setText("审核来源")

    dialog._approve()

    assert calls == []
    assert warnings
    assert dialog.result() != QDialog.DialogCode.Accepted
    dialog.close()


def test_plan_review_does_not_skip_new_draft_when_active_exists(qt_app, monkeypatch):
    exercise = _exercise_with_revisions()
    plan = {
        "id": 5,
        "name": "测试计划",
        "active_revision_id": None,
        "revisions": [
            {
                "id": 21,
                "revision_number": 1,
                "status": "draft",
                "name": "测试计划",
                "purpose": "测试计划复核入口",
                "days": [
                    {
                        "day_order": 1,
                        "name": "第一天",
                        "actions": [
                            {
                                "action_order": 1,
                                "exercise_id": exercise["id"],
                                "exercise_name": exercise["canonical_name"],
                                "phase": "main",
                                "rest_seconds": 0,
                                "note": "",
                                "sets": [
                                    {
                                        "set_order": 1,
                                        "unit": "reps",
                                        "value": 8,
                                        "per_side": 0,
                                        "note": "",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }

    class PlanRepository:
        def get_plan(self, _plan_id):
            return plan

    class ExerciseRepository:
        def get(self, _exercise_id):
            return exercise

    class ExerciseService:
        repository = ExerciseRepository()

    opened = []

    class RecordingDialog:
        def __init__(self, service, selected_exercise, selected_revision_id=None, parent=None):
            opened.append((service, selected_exercise, selected_revision_id, parent))

        def exec(self):
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "training_feedback.ui.plan_detail_page.GuidanceReviewDialog", RecordingDialog
    )
    page = PlanDetailPage(plan, PlanRepository(), ExerciseService())

    page._review_required_guidance()

    assert opened
    assert opened[0][1] is exercise
    assert opened[0][2] == 13
    page.close()


def test_editor_keeps_save_and_cancel_reachable_in_small_window(qt_app):
    editor = ExerciseEditor(object())
    editor.resize(360, 280)
    editor.show()
    qt_app.processEvents()

    assert editor.scroll_area.isVisible()
    assert editor.button_box.isVisible()
    assert editor.button_box.button(QDialogButtonBox.StandardButton.Save).isVisible()
    assert editor.button_box.button(QDialogButtonBox.StandardButton.Cancel).isVisible()
    assert editor.scroll_area.geometry().bottom() < editor.button_box.geometry().top()
    assert editor.button_box.geometry().bottom() <= editor.contentsRect().bottom()
    editor.close()


def test_review_dialog_keeps_approval_controls_reachable_in_small_window(qt_app):
    dialog = GuidanceReviewDialog(object(), _exercise_with_revisions(), selected_revision_id=12)
    dialog.resize(380, 320)
    dialog.show()
    qt_app.processEvents()

    assert dialog.scroll_area.isVisible()
    assert dialog.approved.isVisible()
    assert dialog.button_box.isVisible()
    assert dialog.button_box.button(QDialogButtonBox.StandardButton.Save).isVisible()
    assert dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel).isVisible()
    assert dialog.approved.geometry().bottom() < dialog.button_box.geometry().top()
    assert dialog.button_box.geometry().bottom() <= dialog.contentsRect().bottom()
    dialog.close()


def test_long_revision_identity_does_not_force_guidance_content_sideways(qt_app):
    exercise = _exercise_with_revisions()
    for revision in exercise["guidance"]:
        revision["bundled_content_id"] = (
            "training-feedback.launch.supine-360-diaphragmatic-breathing.zh-CN"
        )
        revision["bundled_content_version"] = 1
    windows = [ExerciseEditor(object(), exercise), GuidanceReviewDialog(object(), exercise)]
    for window in windows:
        window.resize(685, 520)
        window.show()
        qt_app.processEvents()
        assert window.scroll_area.widget().width() <= window.scroll_area.viewport().width()
        window.close()


def test_guidance_form_preserves_untouched_crlf_and_unicode_separators(qt_app):
    guidance = starter_guidance("原文动作")
    guidance["purpose"] = "  第一行\r\n第二行\r第三行\u2028第四行\u2029最后一行  "
    form = GuidanceForm(guidance)
    form.scalar_edits["breathing"].setPlainText("修改另一字段")

    assert form.guidance()["purpose"] == guidance["purpose"]


def test_steps_add_after_removal_and_reorder_keep_unique_sequence(qt_app):
    editor = GuidanceStepsEditor([
        {"order": 1, "text": "步骤一", "source": "保留一"},
        {"order": 2, "text": "步骤二"},
        {"order": 3, "text": "步骤三", "source": "保留三"},
    ])
    editor.table.setCurrentCell(1, 1)
    editor._remove()
    editor._add()
    editor.table.item(2, 1).setText("新增步骤")
    assert len({step["order"] for step in editor.steps()}) == 3
    editor.table.setCurrentCell(1, 1)
    editor._move(-1)

    assert editor.steps() == [
        {"order": 1, "text": "步骤三", "source": "保留三"},
        {"order": 2, "text": "步骤一", "source": "保留一"},
        {"order": 3, "text": "新增步骤"},
    ]


def test_detail_opens_as_window_and_keeps_controls_inside_small_viewport(qt_app):
    parent = QWidget()
    parent.resize(700, 550)
    parent.show()
    exercise = _exercise_with_revisions()
    exercise["equipment_summary"] = "很长的器材说明与注意事项。" * 50
    page = ExerciseDetailPage(exercise, object(), parent)
    page.resize(600, 500)
    page.show()
    qt_app.processEvents()

    assert page.isWindow()
    assert page.height() <= 500
    for button in (page.edit_button, page.toggle_button, page.review_button):
        assert page.contentsRect().contains(button.geometry())
    page.close()
    parent.close()


def test_detail_edit_keeps_the_displayed_revision_as_source(qt_app, monkeypatch):
    selected_sources = []

    class RecordingEditor:
        def __init__(self, service, exercise, parent=None, *, selected_revision_id=None):
            selected_sources.append(selected_revision_id)

        def exec(self):
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr("training_feedback.ui.exercise_detail_page.ExerciseEditor", RecordingEditor)
    page = ExerciseDetailPage(_exercise_with_revisions(), object())
    page.guidance_selector.setCurrentIndex(page.guidance_selector.findData(12))
    page._edit_exercise()

    assert selected_sources == [12]
    page.close()
