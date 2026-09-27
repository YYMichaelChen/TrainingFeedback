"""主窗口：左侧导航 + 按需创建的页面堆栈。"""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..app import LibraryContext
from .settings_page import SettingsPage


class MainWindow(QMainWindow):
    """导航切换页面，并在首次进入时创建较重的工作区。"""
    def __init__(self, context: LibraryContext, switch_request=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("训练反馈")
        self.resize(1100, 740)
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 28, 18, 22)
        brand = QLabel("训练反馈")
        brand.setObjectName("brand")
        caption = QLabel("TRAINING FEEDBACK")
        caption.setObjectName("brandCaption")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(caption)
        sidebar_layout.addSpacing(30)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        sidebar_layout.addWidget(self.navigation, 1)
        footer = QLabel("专注每一次练习\n本机保存 · 由你掌握")
        footer.setObjectName("brandCaption")
        sidebar_layout.addWidget(footer)
        self.pages = QStackedWidget()
        self.pages.setContentsMargins(24, 20, 24, 20)
        self._page_factories = (
            lambda: context.create_session_page(self),
            lambda: context.create_library_page(self, progressive=True),
            lambda: context.create_plan_page(self),
            lambda: SettingsPage(context, switch_request=switch_request, parent=self),
        )
        self._built_pages = {0}
        for index, name in enumerate(("训练", "动作库", "训练计划", "设置")):
            self.navigation.addItem(name)
            self.pages.addWidget(self._page_factories[index]() if index == 0 else QWidget())
        self.navigation.setCurrentRow(0)
        self.navigation.currentRowChanged.connect(self._show_page)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(container)

    def _show_page(self, index: int) -> None:
        if index < 0:
            return
        current = self.pages.currentWidget()
        if current is not None:
            cancel = getattr(current, "cancel_loading", None)
            if cancel is not None:
                cancel()
        page = self.pages.widget(index)
        created = index not in self._built_pages
        if created:
            self.pages.insertWidget(index, self._page_factories[index]())
            self.pages.removeWidget(page)
            page.deleteLater()
            self._built_pages.add(index)
        self.pages.setCurrentIndex(index)
        page = self.pages.currentWidget()
        # Newly created pages populate themselves in their constructor.
        if created:
            return
        refresh = getattr(page, "refresh", None)
        if refresh is not None:
            refresh()

    def closeEvent(self, event):
        for index in range(self.pages.count()):
            cancel = getattr(self.pages.widget(index), "cancel_loading", None)
            if cancel is not None:
                cancel()
        super().closeEvent(event)
