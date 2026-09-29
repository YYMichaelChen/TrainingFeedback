"""Shared first-launch and Settings data-root chooser."""

from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from ..application.new_root import DEFAULT_ROOT_DIRECTORY_NAME, NewRootProposal
from .labels import localize_dialog_buttons


def suggested_data_root() -> Path | None:
    """Use Windows' known Documents location, including folder redirection."""
    documents = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    return Path(documents) if documents else None


class DataRootDialog(QDialog):
    """Create from parent/name or open the exact selected root directory."""

    def __init__(self, parent=None, *, suggested_path: Path | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择训练反馈数据目录")
        self._create_text = str(suggested_path or suggested_data_root() or "")
        self._open_text = ""
        self._current_create = True
        self._selected = None
        self.open_mode = QRadioButton("打开已有数据目录")
        self.create_mode = QRadioButton("创建新的数据目录")
        self.create_mode.setChecked(True)
        self.path_label = QLabel("父目录")
        self.path_edit = QLineEdit(self._create_text)
        self.name_label = QLabel("新目录名称")
        self.name_edit = QLineEdit(DEFAULT_ROOT_DIRECTORY_NAME)
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.browse_button = QPushButton("浏览…")
        self.browse_button.clicked.connect(self._browse)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(buttons)
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("请选择已有数据目录，或在所选父目录下创建新数据目录。"))
        for widget in (self.open_mode, self.create_mode, self.path_label,
                       self.path_edit, self.name_label, self.name_edit,
                       self.preview_label, self.browse_button, buttons):
            layout.addWidget(widget)
        self.create_mode.toggled.connect(self._mode_changed)
        self.path_edit.textChanged.connect(self._refresh)
        self.name_edit.textChanged.connect(self._refresh)
        self._refresh()

    def _mode_changed(self, checked: bool) -> None:
        if checked == self._current_create:
            return
        if self._current_create:
            self._create_text = self.path_edit.text()
            self.path_edit.setText(self._open_text)
        else:
            self._open_text = self.path_edit.text()
            self.path_edit.setText(self._create_text)
        self._current_create = checked
        self.path_label.setText("父目录" if checked else "已有数据目录")
        self.name_label.setVisible(checked)
        self.name_edit.setVisible(checked)
        self._refresh()

    def _browse(self) -> None:
        title = "选择父目录" if self.creates_new_root() else "选择已有数据目录"
        selected = QFileDialog.getExistingDirectory(self, title)
        if selected:
            self.path_edit.setText(selected)

    def _refresh(self) -> None:
        if self.creates_new_root():
            try:
                if not self.path_edit.text():
                    raise ValueError("Choose an existing parent directory.")
                proposal = NewRootProposal(Path(self.path_edit.text()), self.name_edit.text())
            except ValueError as exc:
                self._selected = None
                self.preview_label.setText(str(exc))
            else:
                self._selected = proposal.target
                self.preview_label.setText(f"将创建：{proposal.preview}")
        else:
            path_text = self.path_edit.text()
            self._selected = Path(path_text) if path_text and Path(path_text).is_dir() else None
            self.preview_label.setText(
                f"将打开：{path_text}" if path_text else "请选择已有数据目录"
            )
        self.ok_button.setEnabled(self._selected is not None)

    def accept(self) -> None:
        self._refresh()
        if self._selected is not None:
            super().accept()

    def selected_path(self) -> Path:
        if self._selected is None:
            raise ValueError("Choose a valid data-root location.")
        return self._selected

    def creates_new_root(self) -> bool:
        return self.create_mode.isChecked()
