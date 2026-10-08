"""New-model start/resume, frozen history and next-day feedback composition."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .group_training_page import ExecutionPreview, FrozenGuidanceDialog
from .labels import EXECUTION_TEXT as T
from .labels import (
    FEEDBACK_VALUE_LABELS,
    SESSION_STATUS_LABELS,
    localize_dialog_buttons,
    occurrence_prescription,
    occurrence_title,
    session_history_text,
    user_message,
)
from .sizing import initial_size


class GroupFeedbackDialog(QDialog):
    def __init__(self, service, session, parent=None):
        super().__init__(parent)
        self.service, self.session = service, session
        self.setWindowTitle(T["feedback"])
        initial_size(self, 35, 27.5)
        layout = QVBoxLayout(self)
        content = QWidget()
        form = QFormLayout(content)
        hint = QLabel(T["feedback_hint"])
        hint.setWordWrap(True)
        form.addRow(hint)
        self.areas = {}
        for area in service.feedback_areas(session):
            choice = QComboBox()
            for value, text in FEEDBACK_VALUE_LABELS.items():
                choice.addItem(text, value.value)
            choice.setCurrentIndex(-1)
            choice.setPlaceholderText(T["unknown_feedback"])
            self.areas[area] = choice
            form.addRow(area, choice)
        self.note = QPlainTextEdit()
        form.addRow(T["overall_note"], self.note)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        try:
            self.service.submit_feedback(self.session["id"],
                                         {name: widget.currentData()
                                          for name, widget in self.areas.items()},
                                         self.note.toPlainText())
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        self.accept()


class GroupSessionPage(QWidget):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self.service = context.sessions
        self.training_window = None
        self.setWindowTitle(T["hub"])
        layout = QVBoxLayout(self)
        self.active_label = QLabel()
        self.active_label.setTextFormat(Qt.TextFormat.PlainText)
        self.active_label.setWordWrap(True)
        layout.addWidget(self.active_label)
        self.plan = QComboBox()
        layout.addWidget(QLabel("选择训练计划"))
        layout.addWidget(self.plan)
        row = QHBoxLayout()
        self.start_button = QPushButton(T["start"])
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start)
        self.resume_button = QPushButton(T["resume"])
        self.resume_button.clicked.connect(self.resume)
        refresh = QPushButton(T["refresh"])
        refresh.clicked.connect(self.refresh)
        for button in (self.start_button, self.resume_button, refresh):
            row.addWidget(button)
        layout.addLayout(row)
        layout.addWidget(QLabel(T["history"]))
        self.history = QComboBox()
        self.history.currentIndexChanged.connect(self.show_history)
        layout.addWidget(self.history)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        layout.addWidget(self.detail, 1)
        row = QHBoxLayout()
        self.export_button = QPushButton(T["export"])
        self.export_button.clicked.connect(self.export)
        self.feedback_button = QPushButton(T["feedback"])
        self.feedback_button.clicked.connect(self.feedback)
        self.correct_button = QPushButton(T["correct"])
        self.correct_button.clicked.connect(self.correct_note)
        for button in (self.export_button, self.feedback_button, self.correct_button):
            row.addWidget(button)
        layout.addLayout(row)
        self.guidance_button = QPushButton(T["guidance"])
        self.guidance_button.clicked.connect(self.show_guidance)
        layout.addWidget(self.guidance_button)
        self.refresh()

    def refresh(self):
        active = self.service.active()
        previous = T["previous_day"] + " · " if active and self.service.previous_day(active) else ""
        self.active_label.setText(previous + (
            f"{active['training_date']} · {SESSION_STATUS_LABELS[active['status']]}"
            if active else T["no_sessions"]
        ))
        choice = self.plan.currentData()
        self.plan.clear()
        for revision in self.context.plans.active_revisions():
            self.plan.addItem(f"{revision['name']} · {revision['plan_code']}", revision["id"])
        index = self.plan.findData(choice)
        if index >= 0:
            self.plan.setCurrentIndex(index)
        self.start_button.setEnabled(active is None and self.plan.count() > 0)
        self.resume_button.setEnabled(active is not None)
        selected = self.history.currentData()
        self.history.blockSignals(True)
        self.history.clear()
        for session in self.service.history():
            self.history.addItem(f"{session['training_date']} · "
                                  f"{SESSION_STATUS_LABELS[session['status']]} · "
                                  f"{session['snapshot']['revision']['name']}", session["id"])
        index = self.history.findData(selected)
        self.history.setCurrentIndex(max(0, index))
        self.history.blockSignals(False)
        self.show_history()

    def show_history(self):
        identifier = self.history.currentData()
        self.export_button.setEnabled(identifier is not None)
        self.guidance_button.setEnabled(identifier is not None)
        self.feedback_button.setEnabled(False)
        self.correct_button.setEnabled(False)
        if identifier is None:
            self.detail.setPlainText(T["no_sessions"])
            return
        session = self.service.get(identifier)
        self.detail.setPlainText(session_history_text(session))
        self.feedback_button.setEnabled(any(row["id"] == identifier
                                             for row in self.service.pending_feedback()))
        self.correct_button.setEnabled(session["status"] not in ("open", "paused"))

    def open_training(self, controller):
        self.training_window = self.context.create_training_page(controller, self)
        self.training_window.session_changed.connect(self.refresh)
        self.training_window.session_ended.connect(self.refresh)
        self.training_window.show()
        self.refresh()

    def start(self):
        revision = self.plan.currentData()
        if revision is None:
            return
        try:
            preview = self.service.preview_start(revision)
            text = (preview["revision"]["name"] + "\n" +
                    preview["training_date"] + "\n" + T["unreviewed"] +
                    ("、".join(preview["unreviewed"]) or T["none"]) + "\n\n" +
                    "\n\n".join(occurrence_title(row) + "\n" + occurrence_prescription(row)
                                 for row in preview["occurrences"]))
            if not ExecutionPreview(T["start_preview"], text, self).exec():
                return
            controller = self.context.session_controller()
            controller.start(revision, expected_preview=preview["token"], user_confirmed=True)
            self.open_training(controller)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))

    def resume(self):
        if self.training_window and self.training_window.isVisible():
            self.training_window.raise_()
            self.training_window.activateWindow()
            return
        try:
            controller = self.context.session_controller()
            controller.resume()
            self.open_training(controller)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))

    def export(self):
        identifier = self.history.currentData()
        if identifier is None:
            return
        try:
            path = self.context.session_handoff.export(identifier)
            QMessageBox.information(self, T["export"], T["exported"] + str(path))
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))

    def feedback(self):
        identifier = self.history.currentData()
        if identifier is not None:
            GroupFeedbackDialog(self.service, self.service.get(identifier), self).exec()
            self.refresh()

    def show_guidance(self):
        identifier = self.history.currentData()
        if identifier is not None:
            FrozenGuidanceDialog(self.service, self.service.get(identifier), self).exec()

    def correct_note(self):
        identifier = self.history.currentData()
        if identifier is None:
            return
        session = self.service.get(identifier)
        targets = [(occurrence_title(row), row["id"], row["note"])
                   for row in session["occurrences"] if row["result"] is not None]
        if session["feedback"]:
            targets.insert(0, (T["overall_note"], "overall_note",
                               session["feedback"]["overall_note"]))
        if not targets:
            return
        title, accepted = QInputDialog.getItem(self, T["correct"], T["choose_note"],
                                               [row[0] for row in targets], editable=False)
        if not accepted:
            return
        _, target, old_value = next(row for row in targets if row[0] == title)
        dialog = QDialog(self)
        dialog.setWindowTitle(T["correct"])
        layout = QVBoxLayout(dialog)
        edit = QPlainTextEdit()
        edit.setPlainText(old_value or "")
        initial_text = edit.toPlainText()
        layout.addWidget(edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec():
            try:
                if edit.toPlainText() == initial_text:
                    return
                self.service.correct_note(identifier, target,
                                          edit.toPlainText(), expected_value=old_value)
                self.refresh()
            except (ValueError, OSError) as exc:
                QMessageBox.warning(self, T["error"], user_message(str(exc)))
