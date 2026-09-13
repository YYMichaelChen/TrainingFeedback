"""批量复核对话框：一次真实外部审核，逐项独立勾选批准。

共享的是这一次审核的来源、发生时间、备注和可选原件；每一项仍然是独立勾选的用户批准，
默认全不勾选。选中的行显示该版本完整正文与相对当前启用版本的差异，读过再批。
"""

from pathlib import Path

from PySide6.QtCore import Qt
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
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .guidance_widgets import GuidanceChangesView, GuidanceView
from .labels import GUIDANCE_STATUS_LABELS, label, localize_dialog_buttons, user_message


class GuidanceBatchReviewDialog(QDialog):
    """在一次审核里批准多个明确勾选的指导版本。"""

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.items = service.list_reviewable_guidance()
        self.answer_file: Path | None = None
        self.approved_count = 0
        self.setWindowTitle("批量复核并批准动作指导")
        self.resize(900, 720)

        self.revision_list = QListWidget()
        self.revision_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        for item in self.items:
            status = label(GUIDANCE_STATUS_LABELS, item["guidance"].get("review", {}).get("status"))
            entry = QListWidgetItem(
                f"{item['exercise_name']}　第 {item['revision_number']} 版　{status}"
            )
            entry.setFlags(entry.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            entry.setCheckState(Qt.CheckState.Unchecked)
            entry.setData(Qt.ItemDataRole.UserRole, item["revision_id"])
            self.revision_list.addItem(entry)

        self.guidance_view = GuidanceView()
        self.guidance_changes = GuidanceChangesView()
        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.addWidget(QLabel("所选行的完整指导"))
        preview_layout.addWidget(self.guidance_view, 3)
        preview_layout.addWidget(QLabel("相对当前启用版本的内容变化"))
        preview_layout.addWidget(self.guidance_changes, 2)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        selection = QWidget()
        selection_layout = QVBoxLayout(selection)
        selection_layout.addWidget(QLabel("勾选本次实际复核并批准的版本"))
        selection_layout.addWidget(self.revision_list)
        splitter.addWidget(selection)
        splitter.addWidget(preview)
        splitter.setStretchFactor(1, 1)

        self.source_edit = QLineEdit()
        self.reviewed_at_edit = QLineEdit()
        self.reviewed_at_edit.setPlaceholderText("2026-09-13 或 2026-09-13T09:30+08:00")
        self.note_edit = QPlainTextEdit()
        self.note_edit.setMaximumHeight(60)
        self.answer_label = QLabel("未选择原件")
        answer_row = QHBoxLayout()
        answer_button = QPushButton("选择审核答复原件…")
        answer_button.clicked.connect(self._choose_answer_file)
        clear_button = QPushButton("清除")
        clear_button.clicked.connect(self._clear_answer_file)
        answer_row.addWidget(answer_button)
        answer_row.addWidget(clear_button)
        answer_row.addWidget(self.answer_label, 1)
        answer_widget = QWidget()
        answer_widget.setLayout(answer_row)

        form = QFormLayout()
        form.addRow("本次外部 AI 审核来源", self.source_edit)
        form.addRow("外部审核发生时间", self.reviewed_at_edit)
        form.addRow("本次审核备注", self.note_edit)
        form.addRow("审核答复原件（可选）", answer_widget)

        self.approved = QCheckBox("我已阅读所勾选版本的完整指导，并明确批准这些版本")
        self.summary_label = QLabel("")
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(self.button_box)
        self.button_box.accepted.connect(self._approve)
        self.button_box.rejected.connect(self.reject)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout = QVBoxLayout(self)
        if not self.items:
            layout.addWidget(QLabel("当前没有可复核的指导版本。"))
        layout.addWidget(splitter, 1)
        layout.addWidget(separator)
        layout.addLayout(form)
        layout.addWidget(self.approved)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.button_box)

        self.revision_list.currentRowChanged.connect(self._row_changed)
        self.revision_list.itemChanged.connect(lambda _item: self._update_summary())
        if self.items:
            self.revision_list.setCurrentRow(0)
        self._update_summary()

    def _row_changed(self) -> None:
        item = self._current_item()
        self.guidance_view.set_guidance(item["guidance"] if item else None)
        current = None
        if item and item["active_guidance"] is not None:
            current = {"id": item["active_revision_id"], "guidance": item["active_guidance"]}
        selected = None
        if item:
            selected = {"id": item["revision_id"], "guidance": item["guidance"]}
        self.guidance_changes.set_revisions(current, selected)

    def _current_item(self) -> dict | None:
        row = self.revision_list.currentRow()
        if row < 0 or row >= len(self.items):
            return None
        return self.items[row]

    def selected_revision_ids(self) -> list[int]:
        return [
            self.revision_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.revision_list.count())
            if self.revision_list.item(row).checkState() == Qt.CheckState.Checked
        ]

    def _update_summary(self) -> None:
        count = len(self.selected_revision_ids())
        self.summary_label.setText(f"已勾选 {count} / {len(self.items)} 项")
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        save_button.setEnabled(count > 0)

    def _choose_answer_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "选择外部审核答复原件")
        if selected:
            self.answer_file = Path(selected)
            self.answer_label.setText(str(self.answer_file))

    def _clear_answer_file(self) -> None:
        self.answer_file = None
        self.answer_label.setText("未选择原件")

    def _approve(self) -> None:
        selected = self.selected_revision_ids()
        if not selected:
            QMessageBox.warning(self, "没有勾选版本", "请先勾选本次要批准的指导版本。")
            return
        if not self.approved.isChecked():
            QMessageBox.warning(self, "需要批准", "必须明确勾选批准后才能继续。")
            return
        try:
            self.approved_count = self.service.confirm_guidance_reviews(
                selected,
                review_source=self.source_edit.text(),
                reviewed_at=self.reviewed_at_edit.text(),
                review_note=self.note_edit.toPlainText(),
                user_confirmed=self.approved.isChecked(),
                answer_file=self.answer_file,
            )
        except Exception as exc:  # 领域/数据校验失败：整批未写入，保留当前输入以便修正
            QMessageBox.warning(self, "无法批准", user_message(str(exc)))
            return
        QMessageBox.information(
            self, "已批准", f"本次已批准并启用 {self.approved_count} 个指导版本。"
        )
        self.accept()
