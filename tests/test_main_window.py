"""主窗口导航组合：当前模型的工作区页面与中文标签（临时根）。"""

from training_feedback.app import LibraryContext
from training_feedback.ui.main_window import MainWindow


def test_main_window_navigation_and_chinese_labels(qt_app, tmp_path):
    context = LibraryContext.create(tmp_path / "data")
    window = MainWindow(context)
    try:
        assert [window.navigation.item(i).text() for i in range(window.navigation.count())] == [
            "训练",
            "动作库",
            "训练计划",
            "设置",
        ]
        assert [window.pages.widget(i).__class__.__name__ for i in range(window.pages.count())] == [
            "GroupSessionPage",
            "CatalogLibraryPage",
            "GroupPlanPage",
            "SettingsPage",
        ]
        window.navigation.setCurrentRow(3)
        assert window.pages.currentWidget().__class__.__name__ == "SettingsPage"
        window.navigation.setCurrentRow(0)
        hub = window.pages.currentWidget()
        assert hub.start_button.text() == "预览并开始训练…"
        assert window.windowTitle() == "训练反馈"
    finally:
        window.close()
        context.close()
