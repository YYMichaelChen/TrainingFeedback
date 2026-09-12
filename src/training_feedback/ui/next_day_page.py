"""次日反馈页：按身体区域选择酸痛程度并提交；提交后支持修正备注（留审计）。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QGroupBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..domain.enums import FeedbackValue
from .labels import FEEDBACK_VALUE_LABELS, SESSION_STATUS_LABELS, label, user_message


class NextDayPage(QWidget):
    """次日反馈页：对推导出的主要训练部位逐项评价。"""

    submitted = Signal()

    def __init__(self, context, session, clock=None, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.session = session
        self.service = context.feedback_service(clock)
        self.groups: dict[str, QButtonGroup] = {}
        self.action_note_buttons: dict[int, QPushButton] = {}
        self.setWindowTitle("次日反馈")
        content = QWidget()
        layout = QVBoxLayout(content)
        title = QLabel(f"次日反馈：{session['training_date']}")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"训练状态：{label(SESSION_STATUS_LABELS, session['status'])}"))
        self.submission_status = QLabel("尚未提交；未选择的部位将保留为未知。")
        self.submission_status.setWordWrap(True)
        for area in self.service.areas(session):
            box = QGroupBox(area)
            box_layout = QVBoxLayout(box)
            group = QButtonGroup(box)
            for value, option_label in FEEDBACK_VALUE_LABELS.items():
                button = QRadioButton(option_label)
                button.setProperty("feedback_value", value.value)
                group.addButton(button)
                box_layout.addWidget(button)
            self.groups[area] = group
            layout.addWidget(box)
        self.overall_note = QLineEdit()
        self.overall_note.setPlaceholderText("可选的总体备注")
        form = QFormLayout()
        form.addRow("总体备注", self.overall_note)
        layout.addLayout(form)
        self.action_notes = QVBoxLayout()
        for action in session["actions"]:
            if action.get("result") is None:
                continue
            row = QVBoxLayout()
            action_label = QLabel(f"动作备注：{action['exercise_name_snapshot']}")
            action_label.setTextFormat(Qt.TextFormat.PlainText)
            action_label.setWordWrap(True)
            row.addWidget(action_label)
            button = QPushButton("修正动作备注")
            button.setVisible(False)
            button.clicked.connect(
                lambda _checked=False, action_id=action["id"]: self._correct_action_note(action_id)
            )
            row.addWidget(button)
            self.action_note_buttons[action["id"]] = button
            self.action_notes.addLayout(row)
        layout.addLayout(self.action_notes)
        self.submit_button = QPushButton("提交反馈")
        self.submit_button.clicked.connect(self._submit)
        self.correct_note_button = QPushButton("修正总体备注")
        self.correct_note_button.clicked.connect(self._correct_note)
        self.correct_note_button.setVisible(False)
        layout.addWidget(self.correct_note_button)
        layout.addStretch()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.addWidget(self.scroll_area, 1)
        outer.addWidget(self.submission_status)
        outer.addWidget(self.submit_button)
        available = self.screen().availableGeometry()
        self.resize(min(520, available.width() - 40), min(600, available.height() - 60))
        existing = self.service.get(session["id"])
        if existing is not None:
            self._render_existing(existing)

    def _submit(self) -> None:
        values = {}
        for area, group in self.groups.items():
            selected = group.checkedButton()
            values[area] = FeedbackValue(selected.property("feedback_value")) if selected else None
        try:
            self.service.submit(
                self.session["id"],
                values,
                self.overall_note.text(),
            )
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "无法提交反馈", user_message(str(exc)))
            return
        self._set_read_only()
        self.submitted.emit()

    def _render_existing(self, feedback: dict) -> None:
        for item in feedback["areas"]:
            group = self.groups.get(item["body_area_name_snapshot"])
            if group is None or item["value"] is None:
                continue
            for button in group.buttons():
                if button.property("feedback_value") == item["value"]:
                    button.setChecked(True)
                    break
        self.overall_note.setText(feedback["overall_note"] or "")
        self._set_read_only()

    def _set_read_only(self) -> None:
        for group in self.groups.values():
            for button in group.buttons():
                button.setEnabled(False)
        self.overall_note.setReadOnly(True)
        self.submit_button.setEnabled(False)
        self.submission_status.setText("反馈已提交；当前内容为只读，仅备注可以审计式修正。")
        self.correct_note_button.setVisible(True)
        for button in self.action_note_buttons.values():
            button.setVisible(True)

    def _correct_note(self) -> None:
        current = self.overall_note.text()
        value, accepted = QInputDialog.getText(self, "修正总体备注", "总体备注", text=current)
        if not accepted:
            return
        try:
            self.service.correct_note(self.session["id"], "overall_note", value)
        except ValueError as exc:
            QMessageBox.warning(self, "无法修正备注", user_message(str(exc)))
            return
        self.overall_note.setText(value)

    def _correct_action_note(self, action_id: int) -> None:
        action = next(item for item in self.session["actions"] if item["id"] == action_id)
        value, accepted = QInputDialog.getText(
            self,
            "修正动作备注",
            action["exercise_name_snapshot"],
            text=action.get("note") or "",
        )
        if not accepted:
            return
        try:
            self.service.correct_note(self.session["id"], f"action_note:{action_id}", value)
        except ValueError as exc:
            QMessageBox.warning(self, "无法修正备注", user_message(str(exc)))
            return
        action["note"] = value
