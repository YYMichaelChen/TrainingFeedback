"""Native grouped execution view; the controller owns navigation and all saved state."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..domain.enums import AbortReason
from .guidance_widgets import GuidanceView
from .illustrations import IllustrationLabel
from .labels import (
    ABORT_REASON_LABELS,
    RESULT_LABELS,
    SESSION_STATUS_LABELS,
    confirm,
    label,
    localize_dialog_buttons,
    make_unit_combo,
    occurrence_prescription,
    occurrence_result_text,
    occurrence_side_text,
    occurrence_title,
    user_message,
)
from .labels import EXECUTION_TEXT as T


class AbortDialog(QDialog):
    """中止训练对话框：选择原因并可填写说明。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("中止训练")
        self.reason = QComboBox()
        for reason in AbortReason:
            self.reason.addItem(label(ABORT_REASON_LABELS, reason), reason.value)
        self.reason.setCurrentIndex(-1)
        self.reason.setPlaceholderText("请选择中止原因")
        self.note = QLineEdit()
        form = QFormLayout(self)
        form.addRow("原因", self.reason)
        form.addRow("说明", self.note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class ExecutionPreview(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 540)
        layout = QVBoxLayout(self)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(text)
        layout.addWidget(self.text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def show_frozen_images(layout, service, occurrence):
    while layout.count():
        layout.takeAt(0).widget().deleteLater()
    for index, declaration in enumerate(occurrence["content"]["guidance"]["images"]):
        try:
            pixmap = QPixmap()
            if not pixmap.loadFromData(service.image(occurrence, index)):
                raise ValueError("Image is unavailable or invalid.")
            image = IllustrationLabel(pixmap)
        except (OSError, ValueError, KeyError):
            image = QLabel()
            image.setText(T["invalid_image"])
        image.setWordWrap(True)
        image.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(image)
        caption = QLabel(declaration.get("caption", ""))
        caption.setTextFormat(Qt.TextFormat.PlainText)
        caption.setWordWrap(True)
        layout.addWidget(caption)


class FrozenGuidanceDialog(QDialog):
    def __init__(self, service, session, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T["guidance"])
        self.resize(700, 600)
        layout = QVBoxLayout(self)
        self.selector = QComboBox()
        self.selector.setMinimumContentsLength(24)
        self.selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        for row in session["occurrences"]:
            self.selector.addItem(occurrence_title(row), row)
        layout.addWidget(self.selector)
        self.guidance = GuidanceView(include_review=False)
        layout.addWidget(self.guidance, 1)
        panel = QWidget()
        images = QVBoxLayout(panel)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        layout.addWidget(scroll, 1)

        def show_current():
            row = self.selector.currentData()
            self.guidance.set_guidance(row["content"]["guidance"])
            show_frozen_images(images, service, row)

        self.selector.currentIndexChanged.connect(show_current)
        show_current()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        localize_dialog_buttons(buttons)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class GroupTrainingPage(QWidget):
    session_changed = Signal()
    session_ended = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.controller = controller
        self.pending = None
        self.busy = False
        self.leaving = False
        self.setWindowTitle(T["title"])
        self.resize(800, 740)
        outer = QVBoxLayout(self)
        content = QWidget()
        layout = QVBoxLayout(content)
        self.status = QLabel()
        self.selector = QComboBox()
        self.selector.setMinimumContentsLength(24)
        self.selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.selector.currentIndexChanged.connect(self.navigate)
        self.title = QLabel()
        self.title.setObjectName("sectionTitle")
        self.status.setObjectName("muted")
        self.next_label = QLabel()
        self.prescription = QLabel()
        self.prescription.setObjectName("statusBadge")
        self.saved = QLabel()
        for widget in (self.status, self.title, self.next_label, self.prescription, self.saved):
            widget.setWordWrap(True)
            widget.setTextFormat(Qt.TextFormat.PlainText)
        for widget in (self.status, self.selector, self.title, self.next_label, self.prescription):
            layout.addWidget(widget)
        self.note = QPlainTextEdit()
        self.note.setPlaceholderText(T["note"])
        self.note.setMaximumHeight(85)
        layout.addWidget(self.note)
        self.results = QWidget()
        buttons = QHBoxLayout(self.results)
        self.result_buttons = {}
        for result in ("completed", "exceeded", "partial", "not_completed"):
            button = QPushButton(RESULT_LABELS[result])
            button.setObjectName("primaryButton" if result == "completed" else "secondaryButton")
            button.clicked.connect(lambda _=False, value=result: self.choose_result(value))
            buttons.addWidget(button)
            self.result_buttons[result] = button
        layout.addWidget(self.results)
        self.actual_panel = QWidget()
        actual_layout = QVBoxLayout(self.actual_panel)
        actual_layout.addWidget(QLabel(T["actual"]))
        self.actual = QTableWidget(0, 4)
        self.actual.setHorizontalHeaderLabels([T[key] for key in
                                               ("value", "unit", "side_column", "set_note")])
        self.actual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.actual.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        actual_layout.addWidget(self.actual)
        row = QHBoxLayout()
        add = QPushButton(T["add_set"])
        add.clicked.connect(self.add_actual)
        remove = QPushButton(T["remove_set"])
        remove.clicked.connect(lambda: self.actual.removeRow(self.actual.currentRow()))
        row.addWidget(add)
        row.addWidget(remove)
        actual_layout.addLayout(row)
        layout.addWidget(self.actual_panel)
        self.pending_controls = QWidget()
        row = QHBoxLayout(self.pending_controls)
        self.save_result = QPushButton(T["save_result"])
        self.save_result.clicked.connect(self.save_pending)
        self.cancel_result = QPushButton(T["cancel"])
        self.cancel_result.clicked.connect(self.cancel_pending)
        row.addWidget(self.cancel_result)
        row.addWidget(self.save_result)
        layout.addWidget(self.saved)
        self.round_button = QPushButton(T["round_complete"])
        self.round_button.clicked.connect(self.complete_round)
        self.retract_button = QPushButton(T["retract"])
        self.retract_button.clicked.connect(self.retract)
        self.next_button = QPushButton(T["next"])
        self.next_button.clicked.connect(self.next_unfinished)
        for widget in (self.round_button, self.retract_button, self.next_button):
            layout.addWidget(widget)
        layout.addWidget(QLabel(T["guidance"]))
        self.guidance = GuidanceView(include_review=False)
        layout.addWidget(self.guidance)
        self.images = QVBoxLayout()
        layout.addLayout(self.images)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(content)
        outer.addWidget(self.scroll, 1)
        outer.addWidget(self.pending_controls)
        self.reload_button = QPushButton(T["reload"])
        self.reload_button.clicked.connect(self.reload)
        outer.addWidget(self.reload_button)
        self.controls = QWidget()
        controls = QHBoxLayout(self.controls)
        self.pause_button = QPushButton(T["pause"])
        self.pause_button.clicked.connect(self.pause)
        self.abort_button = QPushButton(T["abort"])
        self.abort_button.clicked.connect(self.abort)
        self.finish_button = QPushButton(T["finish"])
        self.finish_button.setObjectName("primaryButton")
        self.abort_button.setObjectName("dangerButton")
        self.finish_button.clicked.connect(self.finish)
        for button in (self.pause_button, self.abort_button, self.finish_button):
            controls.addWidget(button)
        outer.addWidget(self.controls)
        self.render()

    def render(self):
        session, row = self.controller.session, self.controller.current
        self.pending = None
        self.selector.blockSignals(True)
        self.selector.clear()
        for occurrence in session["occurrences"]:
            self.selector.addItem(occurrence_title(occurrence) + " · " +
                                  RESULT_LABELS.get(occurrence["result"], T["unknown"]))
        self.selector.setCurrentIndex(session["position"])
        self.selector.blockSignals(False)
        self.title.setText(occurrence_title(row))
        self.status.setText(f"{session['training_date']} · "
                            f"{SESSION_STATUS_LABELS[session['status']]} · "
                            + T["progress"].format(
                                done=len(session['occurrences']) - len(self.controller.unfinished),
                                total=len(session['occurrences'])))
        following = self.controller.next_occurrence
        self.next_label.setText(T["next_label"] + occurrence_title(following)
                                if following else T["no_next"])
        self.prescription.setText(occurrence_prescription(row))
        self.note.setPlainText(row["note"] or "")
        saved = row["result"] is not None
        opened = session["status"] == "open"
        self.note.setReadOnly(saved or not opened)
        self.saved.setText(occurrence_result_text(row) if saved else "")
        self.results.setVisible(not saved and opened)
        self.actual_panel.hide()
        self.pending_controls.hide()
        self.selector.setEnabled(opened)
        self.round_button.setVisible(row["group_id"] is not None and opened)
        self.retract_button.setVisible(saved and opened)
        self.retract_button.setText(T["retract_batch"] if row["batch_id"] else T["retract"])
        self.next_button.setEnabled(bool(self.controller.unfinished) and opened)
        self.controls.setEnabled(opened)
        self.finish_button.setEnabled(opened and not self.controller.unfinished)
        self.guidance.set_guidance(row["content"]["guidance"])
        show_frozen_images(self.images, self.controller.service, row)

    def discard(self):
        if self.leaving:
            return True
        if self.pending is None and (self.controller.current["result"] is not None
                                     or not self.note.toPlainText()):
            return True
        return confirm(self, T["discard"], T["discard_hint"])

    def run(self, action, *, end=False):
        if self.busy:
            return False
        self.busy = True
        self.setEnabled(False)
        try:
            action()
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return False
        else:
            self.render()
            self.session_changed.emit()
            if end:
                self.leaving = True
                self.session_ended.emit()
                self.close()
            return True
        finally:
            self.setEnabled(True)
            self.busy = False

    def navigate(self, position):
        if position < 0 or self.busy:
            return
        if self.discard() and self.run(lambda: self.controller.navigate(position)):
            return
        self.selector.blockSignals(True)
        self.selector.setCurrentIndex(self.controller.session["position"])
        self.selector.blockSignals(False)

    def next_unfinished(self):
        if self.discard():
            self.run(self.controller.next_unfinished)

    def reload(self):
        if self.discard():
            self.run(self.controller.reload)

    def choose_result(self, result):
        if self.busy or self.pending or self.controller.current["result"] is not None:
            return
        if result == "completed":
            self.run(lambda: self.controller.record(result, note=self.note.toPlainText()))
            return
        self.pending = result
        self.results.hide()
        self.round_button.hide()
        self.next_button.setEnabled(False)
        self.selector.setEnabled(False)
        self.pending_controls.show()
        self.save_result.setText(T["save_result"] + " · " + RESULT_LABELS[result])
        needs_actual = result in ("partial", "exceeded")
        self.actual_panel.setVisible(needs_actual)
        self.actual.setRowCount(0)
        if needs_actual:
            self.add_actual()

    def add_actual(self):
        row = self.actual.rowCount()
        self.actual.insertRow(row)
        self.actual.setItem(row, 0, QTableWidgetItem(""))
        unit = self.controller.current["action"]["sets"][0]["unit"]
        self.actual.setCellWidget(row, 1, make_unit_combo(unit))
        if self.controller.current.get("dose_scope") == "per_side_aggregate":
            side = QComboBox()
            side.addItem(T["per_side_aggregate"], True)
            side.addItem(T["both"], False)
            side.setCurrentIndex(-1)
            self.actual.setCellWidget(row, 2, side)
        else:
            side = QTableWidgetItem(occurrence_side_text(self.controller.current))
            side.setFlags(side.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.actual.setItem(row, 2, side)
        self.actual.setItem(row, 3, QTableWidgetItem(""))

    def save_pending(self):
        if not self.pending:
            return
        actual = []
        try:
            for index in range(self.actual.rowCount()):
                value = self.actual.item(index, 0).text()
                actual.append({"value": float(value) if value.strip() else None,
                               "unit": self.actual.cellWidget(index, 1).currentData(),
                               "side": self.controller.current["side"],
                                "note": self.actual.item(index, 3).text()})
                if self.controller.current.get("dose_scope") == "per_side_aggregate":
                    actual[-1]["per_side"] = self.actual.cellWidget(index, 2).currentData()
        except ValueError:
            QMessageBox.warning(self, T["error"], user_message(
                "Actual dose must be finite and non-negative."))
            return
        self.run(lambda: self.controller.record(self.pending, actual=actual,
                                                note=self.note.toPlainText()))

    def cancel_pending(self):
        note = self.note.toPlainText()
        self.render()
        self.note.setPlainText(note)

    def complete_round(self):
        if self.busy or not self.discard():
            return
        try:
            preview = self.controller.preview_round()
        except ValueError as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        text = T["round_hint"] + "\n\n" + "\n\n".join(
            occurrence_title(row) + "\n" + occurrence_prescription(row)
            for row in preview["members"]
        )
        if ExecutionPreview(T["round_preview"], text, self).exec():
            self.run(lambda: self.controller.complete_round(preview, user_confirmed=True))

    def retract(self):
        row = self.controller.current
        members = [row] if row["batch_id"] is None else [
            member for member in self.controller.session["occurrences"]
            if member["batch_id"] == row["batch_id"]
        ]
        text = T["retract_hint"] + "\n\n" + "\n\n".join(
            occurrence_title(member) + "\n" + occurrence_result_text(member) for member in members
        )
        if ExecutionPreview(self.retract_button.text(), text, self).exec():
            self.run(lambda: self.controller.retract(user_confirmed=True))

    def pause(self):
        if self.discard():
            self.run(self.controller.pause, end=True)

    def abort(self):
        if not self.discard():
            return
        dialog = AbortDialog(self)
        if dialog.exec():
            self.run(lambda: self.controller.abort(dialog.reason.currentData(), dialog.note.text(),
                                                   user_confirmed=True), end=True)

    def finish(self):
        try:
            status = self.controller.service.proposed_status(self.controller.session["id"])
        except ValueError as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        if confirm(self, T["finish"], T["finish_hint"] + SESSION_STATUS_LABELS[status]):
            self.run(lambda: self.controller.finish(user_confirmed=True), end=True)

    def closeEvent(self, event):
        event.accept() if self.discard() else event.ignore()
