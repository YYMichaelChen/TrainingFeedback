"""设置页：数据目录信息、切换数据目录、打开目录、手动备份。"""

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..application.release_updates import UpdateStatus
from ..data.backup import BackupError, create_backup
from ..data.data_root import DataRootError
from .data_root_dialog import DataRootDialog, suggested_data_root
from .labels import user_message


class SettingsPage(QWidget):
    """设置页：数据目录与备份。"""
    def __init__(
        self,
        context,
        backup_picker: Callable[[], str] | None = None,
        switch_request: Callable[[Path, bool], bool] | None = None,
        update_coordinator=None,
        parent=None,
    ):
        super().__init__(parent)
        self.context = context
        self.backup_picker = backup_picker
        self.switch_request = switch_request
        self.update_coordinator = update_coordinator
        layout = QVBoxLayout(self)
        title = QLabel("设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"当前数据目录：{context.data_root.path}"))
        open_button = QPushButton("打开数据目录位置")
        open_button.clicked.connect(lambda: self._open_location())
        layout.addWidget(open_button)
        if switch_request is not None:
            self.switch_button = QPushButton("切换到其他数据目录…")
            self.switch_button.clicked.connect(self._switch_root)
            layout.addWidget(self.switch_button)
        backup_button = QPushButton("立即创建备份")
        backup_button.clicked.connect(self._create_backup)
        layout.addWidget(backup_button)
        update_group = QGroupBox("应用更新")
        update_layout = QVBoxLayout(update_group)
        update_layout.addWidget(QLabel(f"当前版本：{__version__}"))
        status_row = QHBoxLayout()
        self.update_status = QLabel("尚未检查")
        self.update_status.setObjectName("muted")
        self.update_button = QPushButton("重新检查")
        self.update_button.clicked.connect(self._check_updates)
        status_row.addWidget(self.update_status, 1)
        status_row.addWidget(self.update_button)
        update_layout.addLayout(status_row)
        layout.addWidget(update_group)
        if update_coordinator is None:
            self.update_button.setEnabled(False)
            self.update_status.setText("更新检查不可用")
        else:
            update_coordinator.result_changed.connect(self._show_update_status)
            self._show_update_status(update_coordinator.result)
        layout.addStretch()

    def _check_updates(self) -> None:
        if self.update_coordinator is not None:
            self.update_coordinator.check()

    def _show_update_status(self, result) -> None:
        texts = {
            UpdateStatus.IDLE: "尚未检查",
            UpdateStatus.CHECKING: "正在检查…",
            UpdateStatus.CURRENT: "已是最新版本",
            UpdateStatus.AHEAD: "当前版本高于 GitHub 已发布版本",
            UpdateStatus.FAILED: "暂时无法检查更新",
        }
        if result.status == UpdateStatus.AVAILABLE and result.release is not None:
            text = f"发现新版本 v{result.release.version}，请点击侧栏感叹号查看。"
        else:
            text = texts.get(result.status, "暂时无法检查更新")
        self.update_status.setText(text)
        self.update_button.setEnabled(result.status != UpdateStatus.CHECKING)

    def _has_other_windows(self) -> bool:
        """存在其他可见顶层窗口时阻止切换，确保未提交的表单先被保存或关闭。"""
        application = QApplication.instance()
        main_window = self.window()
        return any(
            widget is not main_window and widget.isVisible()
            for widget in application.topLevelWidgets()
        )

    def _switch_root(self) -> None:
        if self._has_other_windows():
            QMessageBox.warning(
                self, "无法切换数据目录", "请先保存或关闭其他打开的窗口，再切换数据目录。"
            )
            return
        dialog = DataRootDialog(self, suggested_path=suggested_data_root())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            switched = self.switch_request(dialog.selected_path(), dialog.creates_new_root())
        except (DataRootError, ValueError) as exc:
            QMessageBox.warning(self, "无法切换数据目录", user_message(str(exc)))
            return
        if not switched:
            QMessageBox.information(self, "数据目录未变化", "所选目录已是当前数据目录。")

    def _open_location(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.context.data_root.path)))

    def _create_backup(self) -> None:
        destination = (
            self.backup_picker()
            if self.backup_picker
            else QFileDialog.getExistingDirectory(self, "选择空的备份目录")
        )
        if not destination:
            return
        try:
            create_backup(
                self.context.data_root.path,
                Path(destination),
                self.context.database.connection,
            )
        except BackupError as exc:
            QMessageBox.warning(self, "备份失败", user_message(str(exc)))
        else:
            QMessageBox.information(
                self, "备份完成", "完整的数据目录已成功备份。"
            )
