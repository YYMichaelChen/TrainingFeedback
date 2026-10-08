"""设置页：数据目录信息、切换数据目录、打开目录、手动备份。"""

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..application.release_updates import UpdateStatus
from ..data.backup import BackupError, create_backup
from ..data.data_root import DataRootError
from .compact_widgets import ActionBar
from .data_root_dialog import DataRootDialog, suggested_data_root
from .labels import user_message
from .relative_widgets import AdaptiveFields, LocalScrollArea
from .sizing import bind_units, scale_manager


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
        outer = QVBoxLayout(self)
        scroll = LocalScrollArea()
        body = QWidget()
        bind_units(body, "setMaximumWidth", 84)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(body)
        scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        outer.addWidget(scroll)
        title = QLabel("设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        location = QLabel(f"当前数据目录：{context.data_root.path}")
        location.setWordWrap(True)
        layout.addWidget(location)
        layout.addWidget(self._scale_group())
        open_button = QPushButton("打开数据目录位置")
        open_button.clicked.connect(lambda: self._open_location())
        root_actions = ActionBar()
        root_actions.addWidget(open_button)
        if switch_request is not None:
            self.switch_button = QPushButton("切换到其他数据目录…")
            self.switch_button.clicked.connect(self._switch_root)
            root_actions.addWidget(self.switch_button)
        backup_button = QPushButton("立即创建备份")
        backup_button.clicked.connect(self._create_backup)
        root_actions.addWidget(backup_button)
        layout.addWidget(root_actions)
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

    def _scale_group(self):
        group = QGroupBox("界面缩放")
        layout = QVBoxLayout(group)
        self.scale_system = QRadioButton("跟随系统")
        self.scale_custom = QRadioButton("自定义")
        modes = QHBoxLayout()
        modes.addWidget(self.scale_system)
        modes.addWidget(self.scale_custom)
        modes.addStretch()
        layout.addLayout(modes)
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(80, 200)
        self.scale_slider.setSingleStep(10)
        self.scale_slider.setPageStep(10)
        self.scale_slider.setTickInterval(10)
        self.scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.scale_value = QLabel()
        self.scale_value.setWordWrap(True)
        layout.addWidget(QLabel("80% — 200%（每次 10%）"))
        layout.addWidget(self.scale_slider)
        layout.addWidget(self.scale_value)
        reference = QLabel("4K 屏幕默认窗口为 2560×1440、16:9；可独立调整文字和控件大小。")
        reference.setWordWrap(True)
        reference.setObjectName("muted")
        layout.addWidget(reference)
        preview = AdaptiveFields()
        preview.addRow("预览", QLabel("正文文字"))
        preview.addRow("按钮", QPushButton("示例按钮"))
        preview.addRow("输入框", QLineEdit("示例输入"))
        layout.addWidget(preview)
        hint = QLabel("立即生效，保存在本机。Ctrl/Cmd + 加号、减号调整；0 恢复跟随系统。")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        manager = scale_manager()
        self.scale_slider.setEnabled(manager is not None)
        self.scale_custom.setEnabled(manager is not None)
        if manager is not None:
            manager.changed.connect(self._refresh_scale)
            self._refresh_scale()
            self.scale_system.clicked.connect(lambda: manager.set_scale(False, manager.percent))
            self.scale_custom.clicked.connect(lambda: manager.set_scale(True, manager.percent))
            self.scale_slider.valueChanged.connect(lambda value: manager.set_scale(True, value))
        else:
            self.scale_system.setChecked(True)
            self.scale_value.setText("当前 100%（跟随系统）")
        return group

    def _refresh_scale(self):
        manager = scale_manager()
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(manager.percent)
        self.scale_slider.blockSignals(False)
        self.scale_system.setChecked(not manager.custom)
        self.scale_custom.setChecked(manager.custom)
        percent = manager.percent if manager.custom else 100
        self.scale_value.setText(f"当前 {percent}%" + ("" if manager.custom else "（跟随系统）"))

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
