"""启用前预览对话框：只读展示草稿全文与版本差异，二次确认后启用。"""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from .labels import confirm, localize_dialog_buttons, user_message
from .plan_revision_diff import render_diff, render_revision


class PlanActivationPreview(QDialog):
    """Read-only draft preview with a separately confirmed activation action."""

    def __init__(self, repository, plan: dict, draft: dict, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.plan = plan
        self.draft = draft
        self.setWindowTitle("预览启用计划草稿")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("计划草稿版本预览"))
        preview = QPlainTextEdit()
        preview.setReadOnly(True)
        preview.setPlainText(render_revision(draft))
        layout.addWidget(preview)
        layout.addWidget(QLabel("与当前版本的差异"))
        difference = QPlainTextEdit()
        difference.setReadOnly(True)
        active = next((item for item in plan["revisions"] if item["status"] == "active"), None)
        difference.setPlainText(render_diff(active, draft))
        layout.addWidget(difference)
        self.activate_button = QPushButton("启用此草稿版本")
        self.activate_button.clicked.connect(self._confirm_activation)
        layout.addWidget(self.activate_button)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        localize_dialog_buttons(buttons)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _confirm_activation(self) -> None:
        if not confirm(
            self,
            "启用计划草稿版本？",
            "启用后，该草稿将成为当前版本，并替代现有当前版本。之前的版本仍可查看。",
        ):
            return
        try:
            self.repository.activate_revision(self.plan["id"], self.draft["id"])
        except ValueError as exc:
            QMessageBox.warning(self, "无法启用计划版本", user_message(str(exc)))
            return
        QMessageBox.information(self, "计划版本已启用", "计划草稿版本现在已成为当前版本。")
        self.accept()
