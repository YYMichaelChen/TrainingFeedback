from training_feedback.app import ApplicationContext
from training_feedback.application.exercise_service import ExerciseService
from training_feedback.data.data_root import create_new
from training_feedback.data.exercise_repositories import ExerciseRepository
from training_feedback.data.locator import Locator
from training_feedback.ui.data_root_dialog import DataRootDialog
from training_feedback.ui.main_window import MainWindow


def test_first_launch_suggests_creating_the_default_data_root(qt_app, tmp_path):
    suggestion = tmp_path / "Documents" / "TrainingFeedbackData"

    dialog = DataRootDialog(suggested_path=suggestion)

    assert dialog.selected_path() == suggestion
    assert dialog.creates_new_root() is True
    assert str(suggestion) in dialog.suggestion_label.text()
    dialog.close()


def test_first_launch_suggests_opening_an_existing_default_root(qt_app, tmp_path):
    suggestion = tmp_path / "Documents" / "TrainingFeedbackData"
    create_new(suggestion)

    dialog = DataRootDialog(suggested_path=suggestion)

    assert dialog.selected_path() == suggestion
    assert dialog.creates_new_root() is False
    dialog.close()


def test_first_launch_does_not_suggest_an_occupied_directory(qt_app, tmp_path):
    suggestion = tmp_path / "Documents" / "TrainingFeedbackData"
    suggestion.mkdir(parents=True)
    (suggestion / "unrelated.txt").write_text("keep", encoding="utf-8")

    dialog = DataRootDialog(suggested_path=suggestion)

    assert dialog.path_edit.text() == ""
    assert dialog.suggestion_label.text() == ""
    assert (suggestion / "unrelated.txt").read_text(encoding="utf-8") == "keep"
    dialog.close()


def test_data_root_switch_dialog_has_no_prefilled_suggestion(qt_app):
    dialog = DataRootDialog()

    assert dialog.path_edit.text() == ""
    assert dialog.creates_new_root() is False
    dialog.close()


def test_main_window_has_explicit_navigation(qt_app, tmp_path):
    root = create_new(tmp_path / "data")
    context = ApplicationContext.open(root, Locator(tmp_path / "locator.json"))
    window = MainWindow(context)
    assert [window.navigation.item(i).text() for i in range(window.navigation.count())] == [
        "首页",
        "动作库",
        "训练计划",
        "训练历史",
        "设置",
    ]
    window.navigation.setCurrentRow(4)
    assert window.pages.currentWidget().windowTitle() == ""
    window.close()
    context.close()


def test_plans_navigation_uses_plan_page(qt_app, tmp_path):
    root = create_new(tmp_path / "data")
    context = ApplicationContext.open(root, Locator(tmp_path / "locator.json"))
    window = MainWindow(context)
    window.navigation.setCurrentRow(2)
    assert window.pages.currentWidget().__class__.__name__ == "PlanPage"
    assert window.pages.currentWidget().plan_list.count() == 1
    window.close()
    context.close()


def test_history_navigation_uses_history_page(qt_app, tmp_path):
    root = create_new(tmp_path / "data")
    context = ApplicationContext.open(root, Locator(tmp_path / "locator.json"))
    window = MainWindow(context)
    window.navigation.setCurrentRow(3)
    assert window.pages.currentWidget().__class__.__name__ == "HistoryPage"
    window.close()
    context.close()


def test_ui_uses_chinese_display_labels_without_changing_internal_values(qt_app, tmp_path):
    root = create_new(tmp_path / "data")
    context = ApplicationContext.open(root, Locator(tmp_path / "locator.json"))
    window = MainWindow(context)
    assert window.windowTitle() == "训练反馈"
    training = window.pages.widget(0)
    assert training.start_button.text() == "开始今天的训练"
    window.close()
    context.close()


def test_guidance_review_dialog_approves_and_activates(qt_app, tmp_path, monkeypatch):
    """回归：审核对话框一次完成批准并启用，不再弹出误报错误。"""
    from PySide6.QtWidgets import QMessageBox

    from training_feedback.ui.guidance_review_page import GuidanceReviewDialog

    def fail_on_warning(*args, **kwargs):
        raise AssertionError("unexpected warning dialog")

    monkeypatch.setattr(QMessageBox, "warning", fail_on_warning)
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("臀桥")["id"]
    exercise = repository.get(exercise_id)
    revision = exercise["guidance"][0]
    dialog = GuidanceReviewDialog(service, exercise, selected_revision_id=revision["id"])
    dialog.source_edit.setText("review-1")
    dialog.reviewed_at_edit.setText("2026-09-01")
    dialog.approved.setChecked(True)
    dialog._approve()
    current = repository.get(exercise_id)
    assert current["active_guidance_revision_id"] == revision["id"]
    assert current["guidance"][0]["guidance"]["review"]["status"] == "active"
    context.close()
