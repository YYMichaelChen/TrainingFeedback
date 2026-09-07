"""动作指导审核对话框：展示指导全文，用户明确勾选批准后审核并启用。"""

from datetime import UTC, datetime

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from .labels import localize_dialog_buttons, user_message


class GuidanceReviewDialog(QDialog):
    """指导审核对话框：必须明确勾选批准，批准后原子启用。"""
    def __init__(self, service, revision_id: int, guidance: dict, parent=None):
        super().__init__(parent)
        self.service = service
        self.revision_id = revision_id
        self.setWindowTitle("审核并批准动作指导")
        content = QPlainTextEdit()
        content.setReadOnly(True)
        content.setPlainText(str(guidance))
        self.source_edit = QLineEdit()
        self.note_edit = QPlainTextEdit()
        self.approved = QCheckBox("我明确批准这份已审核的动作指导")
        form = QFormLayout()
        form.addRow("外部 AI 审核来源", self.source_edit)
        form.addRow("审核备注", self.note_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(self._approve)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("完整动作指导"))
        layout.addWidget(content)
        layout.addLayout(form)
        layout.addWidget(self.approved)
        layout.addWidget(buttons)

    def _approve(self) -> None:
        if not self.approved.isChecked():
            QMessageBox.warning(self, "需要批准", "必须明确勾选批准后才能继续。")
            return
        now = datetime.now(UTC).isoformat()
        try:
            # 审核、批准与启用是一次原子用户动作，由仓储在单个事务中完成。
            self.service.review_and_activate_guidance(
                self.revision_id,
                {
                    "reviewer_type": "external_ai_expert",
                    "review_source": self.source_edit.text().strip(),
                    "review_note": self.note_edit.toPlainText(),
                    "reviewed_at": now,
                    "user_approved_at": now,
                },
            )
        except ValueError as exc:
            QMessageBox.warning(self, "无法批准动作指导", user_message(str(exc)))
            return
        self.accept()
