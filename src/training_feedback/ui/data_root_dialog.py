"""启动时的数据目录选择对话框：打开已有目录或创建新目录。"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

from .labels import localize_dialog_buttons


class DataRootDialog(QDialog):
    """Explicitly chooses whether to create or open a data root."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择训练反馈数据目录")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择数据目录")
        self.open_mode = QRadioButton("打开已有数据目录")
        self.create_mode = QRadioButton("创建新的数据目录")
        self.open_mode.setChecked(True)
        browse = QFileDialog.getExistingDirectory
        browse_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Open)
        localize_dialog_buttons(browse_button)
        browse_button.clicked.connect(lambda checked=False: self._browse(browse))
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("请选择已有的训练反馈数据目录，或选择空目录创建新的数据目录。")
        )
        layout.addWidget(self.open_mode)
        layout.addWidget(self.create_mode)
        layout.addWidget(self.path_edit)
        layout.addWidget(browse_button)
        layout.addWidget(buttons)

    def _browse(self, picker) -> None:
        selected = picker(self, "选择数据目录")
        if selected:
            self.path_edit.setText(selected)

    def selected_path(self) -> Path:
        return Path(self.path_edit.text().strip())

    def creates_new_root(self) -> bool:
        return self.create_mode.isChecked()
