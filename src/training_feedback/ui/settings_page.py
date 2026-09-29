"""设置页：数据目录信息、切换数据目录、打开目录、手动备份。"""

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

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
        parent=None,
    ):
        super().__init__(parent)
        self.context = context
        self.backup_picker = backup_picker
        self.switch_request = switch_request
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
        layout.addStretch()

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
