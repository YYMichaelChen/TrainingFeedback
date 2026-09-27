"""主窗口导航组合：当前模型的工作区页面与中文标签（临时根）。"""

import time

from PySide6.QtWidgets import QWidget

from training_feedback.app import LibraryContext
from training_feedback.ui.illustrations import IllustrationLabel
from training_feedback.ui.main_window import MainWindow


def test_main_window_navigation_and_chinese_labels(qt_app, tmp_path):
    context = LibraryContext.create(tmp_path / "data")
    window = MainWindow(context)
    try:
        window.show()
        assert [window.navigation.item(i).text() for i in range(window.navigation.count())] == [
            "训练",
            "动作库",
            "训练计划",
            "设置",
        ]
        assert window.pages.widget(0).__class__.__name__ == "GroupSessionPage"
        assert all(type(window.pages.widget(i)) is QWidget for i in range(1, 4))
        window.navigation.setCurrentRow(1)
        library = window.pages.currentWidget()
        assert library.__class__.__name__ == "CatalogLibraryPage"
        assert library.cards.count() == 36
        assert "校验中" in library.cards.item(0).text()
        window.navigation.setCurrentRow(3)
        assert window.pages.currentWidget().__class__.__name__ == "SettingsPage"
        window.navigation.setCurrentRow(1)
        assert window.pages.currentWidget() is library
        deadline = time.monotonic() + 10
        while not library._first_load_complete and time.monotonic() < deadline:
            qt_app.processEvents()
        assert library._first_load_complete
        assert not library.cards.item(0).icon().isNull()
        library.cards.itemClicked.emit(library.cards.item(0))
        preview = library.images_layout.itemAt(0).widget()
        assert isinstance(preview, IllustrationLabel)
        assert preview.source.width() == 1254
        assert preview.pixmap().width() == 760
        window.navigation.setCurrentRow(3)
        assert window.pages.currentWidget().__class__.__name__ == "SettingsPage"
        window.navigation.setCurrentRow(1)
        assert window.pages.currentWidget() is library
        window.navigation.setCurrentRow(0)
        hub = window.pages.currentWidget()
        assert hub.start_button.text() == "预览并开始训练…"
        assert window.windowTitle() == "训练反馈"
    finally:
        window.close()
        context.close()
