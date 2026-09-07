"""设置页：数据目录信息、打开目录、手动备份、导出全部训练证据。"""

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ..app import ApplicationContext
from ..data.backup import BackupError, create_backup
from ..data.handoff import HandoffError, HandoffService
from .labels import user_message


class SettingsPage(QWidget):
    """设置页：数据目录、备份与证据导出。"""
    def __init__(
        self,
        context: ApplicationContext,
        backup_picker: Callable[[], str] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.context = context
        self.backup_picker = backup_picker
        layout = QVBoxLayout(self)
        title = QLabel("设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"当前数据目录：{context.data_root.path}"))
        open_button = QPushButton("打开数据目录位置")
        open_button.clicked.connect(lambda: self._open_location())
        layout.addWidget(open_button)
        backup_button = QPushButton("立即创建备份")
        backup_button.clicked.connect(self._create_backup)
        layout.addWidget(backup_button)
        self.export_button = QPushButton("导出全部训练证据")
        self.export_button.clicked.connect(self._export_evidence)
        layout.addWidget(self.export_button)
        layout.addStretch()

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

    def _export_evidence(self) -> None:
        try:
            json_path, markdown_path = HandoffService(
                self.context.database.connection, self.context.data_root.path
            ).export()
        except (HandoffError, OSError) as exc:
            QMessageBox.warning(self, "导出失败", user_message(str(exc)))
            return
        QMessageBox.information(
            self,
            "导出完成",
            f"已生成 JSON 和 Markdown 证据：\n{json_path.name}\n{markdown_path.name}",
        )
