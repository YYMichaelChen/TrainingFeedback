from training_feedback.app import ApplicationContext
from training_feedback.application.exercise_service import ExerciseService
from training_feedback.data.data_root import create_new
from training_feedback.data.exercise_repositories import ExerciseRepository
from training_feedback.data.locator import Locator
from training_feedback.ui.main_window import MainWindow


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
    revision = repository.get(exercise_id)["guidance"][0]
    dialog = GuidanceReviewDialog(service, revision["id"], revision["guidance"])
    dialog.source_edit.setText("review-1")
    dialog.approved.setChecked(True)
    dialog._approve()
    current = repository.get(exercise_id)
    assert current["active_guidance_revision_id"] == revision["id"]
    assert current["guidance"][0]["guidance"]["review"]["status"] == "active"
    context.close()
