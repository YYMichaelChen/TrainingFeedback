"""启动时的数据目录选择对话框：打开已有目录或创建新目录。"""

from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

from ..data.data_root import CANDIDATE_EXISTING, CANDIDATE_NEW, describe_candidate
from .labels import localize_dialog_buttons

DEFAULT_ROOT_DIRECTORY_NAME = "TrainingFeedbackData"


def suggested_data_root() -> Path | None:
    """首启建议路径：用户文档目录下的固定子目录。用 Qt 取文档位置以尊重系统重定向。"""
    documents = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    if not documents:
        return None
    return Path(documents) / DEFAULT_ROOT_DIRECTORY_NAME


class DataRootDialog(QDialog):
    """Explicitly chooses whether to create or open a data root."""

    def __init__(self, parent=None, *, suggested_path: Path | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择训练反馈数据目录")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择数据目录")
        self.open_mode = QRadioButton("打开已有数据目录")
        self.create_mode = QRadioButton("创建新的数据目录")
        self.open_mode.setChecked(True)
        self.suggestion_label = QLabel("")
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
        layout.addWidget(self.suggestion_label)
        layout.addWidget(browse_button)
        layout.addWidget(buttons)
        self._apply_suggestion(suggested_path)

    def _apply_suggestion(self, suggested_path: Path | None) -> None:
        """预填建议路径并按该路径的实际状态预选模式；仍需用户确认才会创建或打开。

        只检查这一个确切路径，不扫描目录；无法使用的路径不预填，避免给出行不通的建议。
        """
        if suggested_path is None:
            return
        candidate = describe_candidate(suggested_path)
        if candidate == CANDIDATE_EXISTING:
            self.open_mode.setChecked(True)
        elif candidate == CANDIDATE_NEW:
            self.create_mode.setChecked(True)
        else:
            return
        self.path_edit.setText(str(suggested_path))
        self.suggestion_label.setText(
            f"默认位置：{suggested_path}（可改为其他位置）"
        )

    def _browse(self, picker) -> None:
        selected = picker(self, "选择数据目录")
        if selected:
            self.path_edit.setText(selected)

    def selected_path(self) -> Path:
        return Path(self.path_edit.text().strip())

    def creates_new_root(self) -> bool:
        return self.create_mode.isChecked()
