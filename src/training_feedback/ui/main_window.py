"""主窗口：左侧导航、更新提示与按需创建的页面堆栈。"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..app import LibraryContext
from ..application.release_updates import UpdateStatus
from .labels import MAIN_WINDOW_TEXT, user_message
from .release_updates import show_release_details
from .settings_page import SettingsPage
from .sizing import bind_units, initial_window_size
from .window_icon import apply_window_icon


class _PageOpenError(QWidget):
    """页面创建失败时的可见占位：展示可反馈的错误信息，不读写任何数据。"""

    def __init__(self, name, exc, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        detail = user_message(exc, operation=f"打开页面：{name}").strip() or type(exc).__name__
        message = QLabel(MAIN_WINDOW_TEXT["page_open_failed"].format(name=name, message=detail))
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(message)
        hint = QLabel(MAIN_WINDOW_TEXT["page_open_retry"])
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        layout.addWidget(hint)
        layout.addStretch(1)


class MainWindow(QMainWindow):
    """导航切换页面，并在首次进入时创建较重的工作区。"""
    def __init__(
        self, context: LibraryContext, switch_request=None, update_coordinator=None, parent=None
    ):
        super().__init__(parent)
        apply_window_icon(self)
        self.setWindowTitle("训练反馈")
        initial_window_size(self)
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(0)
        bind_units(sidebar, "setFixedWidth", 11.5)
        sidebar_layout = QVBoxLayout(sidebar)
        bind_units(sidebar_layout, "setContentsMargins", .875, 1.5, .875, 1)
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand = QLabel("训练反馈")
        brand.setObjectName("brand")
        self.update_notice = QToolButton()
        self.update_notice.setObjectName("updateNotice")
        self.update_notice.setText("!")
        bind_units(self.update_notice, "setFixedSize", 2.5, 2.5)
        self.update_notice.setVisible(False)
        self.update_notice.clicked.connect(self._show_update)
        brand_row.addWidget(brand)
        brand_row.addStretch()
        brand_row.addWidget(self.update_notice)
        caption = QLabel("TRAINING FEEDBACK")
        caption.setObjectName("brandCaption")
        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addWidget(caption)
        spacer = QWidget()
        bind_units(spacer, "setFixedHeight", 1.875)
        sidebar_layout.addWidget(spacer)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        sidebar_layout.addWidget(self.navigation, 1)
        footer = QLabel("专注每一次练习\n本机保存 · 由你掌握")
        footer.setObjectName("brandCaption")
        sidebar_layout.addWidget(footer)
        self.pages = QStackedWidget()
        bind_units(self.pages, "setContentsMargins", 1, .875, 1, .875)
        self._page_factories = (
            lambda: context.create_session_page(self),
            lambda: context.create_library_page(self, progressive=True),
            lambda: context.create_plan_page(self),
            lambda: SettingsPage(
                context,
                switch_request=switch_request,
                update_coordinator=update_coordinator,
                parent=self,
            ),
        )
        self._built_pages = {0}
        self._page_names = ("训练", "动作库", "训练计划", "设置")
        for index, name in enumerate(self._page_names):
            self.navigation.addItem(name)
            self.pages.addWidget(self._page_factories[index]() if index == 0 else QWidget())
        self.navigation.setCurrentRow(0)
        self.navigation.currentRowChanged.connect(self._show_page)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(container)
        self.update_coordinator = update_coordinator
        if update_coordinator is not None:
            update_coordinator.set_exit_guard(
                self.prepare_update_exit,
                self.cancel_prepared_update_exit,
            )
        self._update_start_scheduled = False
        if update_coordinator is not None:
            update_coordinator.result_changed.connect(self._update_release_notice)
            self._update_release_notice(update_coordinator.result)

    def showEvent(self, event):
        super().showEvent(event)
        if self.update_coordinator is not None and not self._update_start_scheduled:
            self._update_start_scheduled = True
            QTimer.singleShot(0, self.update_coordinator.start_once)

    def _update_release_notice(self, result) -> None:
        available = result.status == UpdateStatus.AVAILABLE
        self.update_notice.setVisible(available)
        if available and result.release is not None:
            self.update_notice.setToolTip(f"发现新版本 v{result.release.version}")

    def _show_update(self) -> None:
        if self.update_coordinator is None:
            return
        result = self.update_coordinator.result
        if result.status == UpdateStatus.AVAILABLE and result.release is not None:
            show_release_details(self.update_coordinator, self)

    def _show_page(self, index: int) -> None:
        if index < 0:
            return
        current = self.pages.currentWidget()
        if current is not None:
            cancel = getattr(current, "cancel_loading", None)
            if cancel is not None:
                cancel()
        created = index not in self._built_pages
        if created:
            try:
                page = self._page_factories[index]()
            except Exception as exc:
                # 创建失败也必须切换到与导航一致的可见页面并给出信息；
                # 不登记为已构建，下次进入该页时重试创建。
                page = _PageOpenError(self._page_names[index], exc, self)
            else:
                self._built_pages.add(index)
            placeholder = self.pages.widget(index)
            self.pages.insertWidget(index, page)
            self.pages.removeWidget(placeholder)
            placeholder.deleteLater()
        self.pages.setCurrentIndex(index)
        # Newly created pages populate themselves in their constructor.
        if created:
            return
        refresh = getattr(self.pages.currentWidget(), "refresh", None)
        if refresh is not None:
            refresh()

    def prepare_update_exit(self) -> bool:
        """Resolve edit windows before an external update watchdog is started."""
        if any(
            getattr(self.pages.widget(index), "backup_active", False)
            for index in range(self.pages.count())
        ):
            QMessageBox.information(
                self,
                "更新暂缓",
                "完整备份仍在进行。请等待完成或在设置中取消备份后，再次点击安装。",
            )
            return False
        for widget in QApplication.topLevelWidgets():
            if (
                widget is self
                or not widget.isVisible()
                or widget.property("updateHandoffExempt")
            ):
                continue
            prepare = getattr(widget, "prepare_update_exit", None)
            if prepare is not None:
                if not prepare():
                    return False
                continue
            if widget.isModal():
                QMessageBox.information(
                    widget,
                    "更新暂缓",
                    "还有编辑或确认窗口尚未处理。请先完成或关闭该窗口，再次点击安装。",
                )
                widget.raise_()
                widget.activateWindow()
                return False
        self.setEnabled(False)
        return True

    def cancel_prepared_update_exit(self) -> None:
        """Restore editing only after a not-yet-armed launcher is known to be stopped."""
        self.setEnabled(True)
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if any(
            getattr(self.pages.widget(index), "backup_active", False)
            for index in range(self.pages.count())
        ):
            QMessageBox.information(
                self,
                "备份仍在进行",
                "请等待完整备份完成，或在设置中点击“取消备份”，再关闭应用。",
            )
            event.ignore()
            return
        for index in range(self.pages.count()):
            cancel = getattr(self.pages.widget(index), "cancel_loading", None)
            if cancel is not None:
                cancel()
        super().closeEvent(event)
