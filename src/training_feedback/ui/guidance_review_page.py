"""动作指导复核对话框：所见版本就是被批准和启用的版本。"""

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..data.data_root import DataRootError
from .guidance_widgets import (
    REVIEWABLE_STATUSES,
    GuidanceChangesView,
    GuidanceRevisionCombo,
    GuidanceView,
    active_revision,
    active_revision_text,
    draft_revisions_text,
)
from .labels import localize_dialog_buttons, user_message


class GuidanceReviewDialog(QDialog):
    """显式选择、阅读并批准一个可复核的指导版本。"""

    def __init__(
        self,
        service,
        exercise: dict,
        selected_revision_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.service = service
        self.exercise = exercise
        self.revision_id: int | None = None
        self.setWindowTitle("复核并批准动作指导")
        self.resize(720, 700)

        self.active_revision_label = QLabel(active_revision_text(exercise))
        self.draft_revisions_label = QLabel(draft_revisions_text(exercise))
        self.active_revision_label.setWordWrap(True)
        self.draft_revisions_label.setWordWrap(True)
        self.revision_selector = GuidanceRevisionCombo(
            exercise,
            allowed_statuses=REVIEWABLE_STATUSES,
            selected_revision_id=selected_revision_id,
        )
        self.guidance_view = GuidanceView()
        self.guidance_changes = GuidanceChangesView()

        primary = "、".join(
            area["name"] for area in exercise.get("body_areas", []) if area["is_primary"]
        )
        secondary = "、".join(
            area["name"] for area in exercise.get("body_areas", []) if not area["is_primary"]
        )
        content = QWidget()
        content_layout = QVBoxLayout(content)
        exercise_name = QLabel(f"动作：{exercise.get('canonical_name', '未命名动作')}")
        exercise_name.setObjectName("pageTitle")
        content_layout.addWidget(exercise_name)
        content_layout.addWidget(QLabel(f"主要训练区域：{primary or '无'}"))
        content_layout.addWidget(QLabel(f"次要训练区域：{secondary or '无'}"))
        content_layout.addWidget(self.active_revision_label)
        content_layout.addWidget(self.draft_revisions_label)
        content_layout.addWidget(QLabel("选择本次实际复核并批准的版本"))
        content_layout.addWidget(self.revision_selector)
        content_layout.addWidget(QLabel("所选版本的完整指导与既有复核记录"))
        content_layout.addWidget(self.guidance_view)
        content_layout.addWidget(QLabel("所选版本相对当前启用版本的内容变化"))
        content_layout.addWidget(self.guidance_changes)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(content)

        self.source_edit = QLineEdit()
        self.reviewed_at_edit = QLineEdit()
        self.reviewed_at_edit.setPlaceholderText("2026-09-12 或 2026-09-12T09:30+08:00")
        self.note_edit = QPlainTextEdit()
        self.note_edit.setMaximumHeight(80)
        self.approved = QCheckBox("我明确批准当前显示的这个指导版本")
        self.answer_file: Path | None = None
        self.answer_label = QLabel("未选择原件")
        answer_row = QHBoxLayout()
        choose_answer = QPushButton("选择审核答复原件…")
        choose_answer.clicked.connect(self._choose_answer_file)
        clear_answer = QPushButton("清除")
        clear_answer.clicked.connect(self._clear_answer_file)
        answer_row.addWidget(choose_answer)
        answer_row.addWidget(clear_answer)
        answer_row.addWidget(self.answer_label, 1)
        answer_widget = QWidget()
        answer_widget.setLayout(answer_row)
        review_form = QFormLayout()
        review_form.addRow("本次外部 AI 审核来源", self.source_edit)
        review_form.addRow("外部审核发生时间", self.reviewed_at_edit)
        review_form.addRow("本次审核备注", self.note_edit)
        review_form.addRow("审核答复原件（可选）", answer_widget)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(self.button_box)
        self.button_box.accepted.connect(self._approve)
        self.button_box.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area, 1)
        layout.addLayout(review_form)
        layout.addWidget(self.approved)
        layout.addWidget(self.button_box)
        self.revision_selector.currentIndexChanged.connect(self._revision_changed)
        self._revision_changed()

    def _choose_answer_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "选择外部审核答复原件")
        if selected:
            self.answer_file = Path(selected)
            self.answer_label.setText(str(self.answer_file))

    def _clear_answer_file(self) -> None:
        self.answer_file = None
        self.answer_label.setText("未选择原件")

    def _revision_changed(self) -> None:
        revision = self.revision_selector.selected_revision()
        self.revision_id = revision["id"] if revision else None
        self.guidance_view.set_guidance(revision["guidance"] if revision else None)
        self.guidance_changes.set_revisions(active_revision(self.exercise), revision)
        self.source_edit.clear()
        self.reviewed_at_edit.clear()
        self.note_edit.clear()
        self.approved.setChecked(False)
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        save_button.setEnabled(revision is not None)

    def _approve(self) -> None:
        if self.revision_id is None:
            QMessageBox.warning(
                self,
                "没有可复核版本",
                user_message("No reviewable guidance revision is selected."),
            )
            return
        if not self.approved.isChecked():
            QMessageBox.warning(self, "需要批准", "必须明确勾选批准后才能继续。")
            return
        try:
            self.service.confirm_guidance_review(
                self.revision_id,
                review_source=self.source_edit.text(),
                reviewed_at=self.reviewed_at_edit.text(),
                review_note=self.note_edit.toPlainText(),
                user_confirmed=self.approved.isChecked(),
                answer_file=self.answer_file,
            )
        except (ValueError, DataRootError) as exc:
            QMessageBox.warning(self, "无法批准动作指导", user_message(str(exc)))
            return
        self.accept()
