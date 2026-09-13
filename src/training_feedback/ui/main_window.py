"""主窗口：左侧导航 + 页面堆栈；页面切换时调用其 refresh()（若存在）。"""

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

from ..app import ApplicationContext
from .exercise_library_page import ExerciseLibraryPage
from .history_page import HistoryPage
from .home_page import HomePage
from .plan_page import PlanPage
from .settings_page import SettingsPage


class MainWindow(QMainWindow):
    """主窗口：导航切换页面，页面按约定可提供 refresh() 用于进入时刷新。"""
    def __init__(self, context: ApplicationContext, switch_request=None, parent=None):
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
        home = HomePage(context, self)
        entries = [
            ("首页", home),
            ("动作库", ExerciseLibraryPage(context, self)),
            ("训练计划", PlanPage(context, self)),
            ("训练历史", HistoryPage(context, self)),
            ("设置", SettingsPage(context, switch_request=switch_request, parent=self)),
        ]
        for name, page in entries:
            self.navigation.addItem(name)
            self.pages.addWidget(page)
        self.navigation.currentRowChanged.connect(self._show_page)
        self.navigation.setCurrentRow(0)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(container)

    def _show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        page = self.pages.currentWidget()
        # 约定：需要"进入时刷新"的页面实现 refresh()，这里按鸭子类型调用。
        refresh = getattr(page, "refresh", None)
        if refresh is not None:
            refresh()
