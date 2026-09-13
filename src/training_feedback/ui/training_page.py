"""训练执行页：逐动作记录结果（含实际剂量两步录入）、暂停/中止/完成。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..domain.enums import AbortReason, ExerciseResult
from ..domain.models import ActualSet
from .labels import (
    ABORT_REASON_LABELS,
    DOSE_UNIT_LABELS,
    RESULT_LABELS,
    SESSION_STATUS_LABELS,
    label,
    localize_dialog_buttons,
    make_unit_combo,
    session_prescription_text,
    user_message,
)


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


class TrainingPage(QWidget):
    """训练执行页：状态由 SessionController 拥有，本页只做展示与录入。"""

    session_changed = Signal()
    session_ended = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.controller = controller
        self.action_index = 0
        self.value_edits = []
        self.actual_unit_selectors = []
        self.actual_side_checks = []
        self.pending_actual_result = None
        self._draft_notes = {}
        self._leaving = False
        self.result_button_by_value = {}
        self.setWindowTitle("训练")
        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        self.status = QLabel()
        self.status.setObjectName("muted")
        self.progress = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.action_selector = QComboBox()
        self.action_selector.currentIndexChanged.connect(self._select_action)
        self.planned = QLabel()
        self.planned.setObjectName("statusBadge")
        self.planned.setTextFormat(Qt.TextFormat.PlainText)
        self.actual_hint = QLabel("填写每组实际剂量后，再次点击结果按钮保存。")
        self.actual_hint.setVisible(False)
        for text_label in (
            self.title,
            self.status,
            self.progress,
            self.planned,
            self.actual_hint,
        ):
            text_label.setWordWrap(True)
        self.note = QLineEdit()
        self.note.setPlaceholderText("可选备注")
        self.values = QWidget()
        self.values.setVisible(False)
        self.values_layout = QFormLayout(self.values)
        self.add_actual_set_button = QPushButton("增加实际完成组")
        self.add_actual_set_button.setVisible(False)
        self.add_actual_set_button.clicked.connect(self._add_actual_set)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        content_layout.addWidget(self.title)
        content_layout.addWidget(self.status)
        content_layout.addWidget(self.progress)
        content_layout.addWidget(self.progress_bar)
        content_layout.addWidget(self.action_selector)
        content_layout.addWidget(self.planned)
        content_layout.addWidget(self.actual_hint)
        content_layout.addWidget(self.values)
        content_layout.addWidget(self.add_actual_set_button)
        content_layout.addWidget(self.note)
        self.result_choices = QFrame()
        self.result_choices.setObjectName("card")
        choices_layout = QVBoxLayout(self.result_choices)
        choices_title = QLabel("这个动作完成得怎么样？")
        choices_title.setObjectName("sectionTitle")
        choices_layout.addWidget(choices_title)
        choices_hint = QLabel("按计划完成可直接记录。结束整次训练前，可以撤回误点的结果。")
        choices_hint.setWordWrap(True)
        choices_hint.setObjectName("muted")
        choices_layout.addWidget(choices_hint)
        for result_label, result_value in (
            (label(RESULT_LABELS, result), result)
            for result in (
                ExerciseResult.COMPLETED,
                ExerciseResult.EXCEEDED,
                ExerciseResult.PARTIAL,
                ExerciseResult.NOT_COMPLETED,
            )
        ):
            button = QPushButton(result_label)
            if result_value == ExerciseResult.COMPLETED:
                button.setObjectName("primaryButton")
            elif result_value == ExerciseResult.NOT_COMPLETED:
                button.setObjectName("dangerButton")
            else:
                button.setObjectName("secondaryButton")
            button.clicked.connect(lambda _checked=False, result=result_value: self._record(result))
            choices_layout.addWidget(button)
            self.result_button_by_value[result_value] = button
        content_layout.addWidget(self.result_choices)
        self.saved_summary = QLabel()
        self.saved_summary.setObjectName("statusBadge")
        self.saved_summary.setWordWrap(True)
        content_layout.addWidget(self.saved_summary)
        self.retract_button = QPushButton("点错了？撤回这个动作的结果")
        self.retract_button.clicked.connect(self._retract)
        content_layout.addWidget(self.retract_button)
        self.next_button = QPushButton("下一个未记录动作 →")
        self.next_button.setObjectName("primaryButton")
        self.next_button.clicked.connect(self.go_to_first_unfinished)
        content_layout.addWidget(self.next_button)
        content_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.addWidget(self.scroll_area, 1)
        self.pending_controls = QWidget()
        pending_layout = QHBoxLayout(self.pending_controls)
        pending_layout.setContentsMargins(0, 0, 0, 0)
        self.cancel_result_button = QPushButton("取消，重新选择")
        self.cancel_result_button.clicked.connect(self._cancel_result)
        self.save_result_button = QPushButton()
        self.save_result_button.setObjectName("primaryButton")
        self.save_result_button.clicked.connect(
            lambda: self._record(self.pending_actual_result)
        )
        pending_layout.addWidget(self.cancel_result_button)
        pending_layout.addWidget(self.save_result_button, 1)
        layout.addWidget(self.pending_controls)
        session_controls = QWidget()
        controls_layout = QHBoxLayout(session_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        pause = QPushButton("暂停训练")
        pause.clicked.connect(self._pause)
        abort = QPushButton("中止训练")
        abort.setObjectName("dangerButton")
        abort.clicked.connect(self._abort)
        finish = QPushButton("完成训练")
        finish.setObjectName("primaryButton")
        finish.clicked.connect(self._finish)
        for button in (pause, abort, finish):
            controls_layout.addWidget(button)
        layout.addWidget(session_controls)
        self.session_controls = session_controls
        self.pause_button = pause
        self.abort_button = abort
        self.finish_button = finish
        self._populate_action_selector()
        self._render()

    def go_to_first_unfinished(self) -> None:
        """定位到第一个未记录结果的动作；全部完成时停在最后一项。"""
        self.action_selector.setCurrentIndex(self.controller.first_unfinished_index())
        self._render()

    def _populate_action_selector(self):
        self.action_selector.blockSignals(True)
        self.action_selector.clear()
        for index, action in enumerate(self.controller.session["actions"]):
            self.action_selector.addItem(
                f"第 {action['plan_day_order']} 天 / 第 {action['plan_action_order']} 项："
                f"{action['exercise_name_snapshot']} · "
                f"{label(RESULT_LABELS, action['result']) if action['result'] else '未记录'}",
                index,
            )
        self.action_selector.setCurrentIndex(self.action_index)
        self.action_selector.blockSignals(False)

    def _select_action(self, index):
        if index >= 0:
            self._draft_notes[self.action_index] = self.note.text()
            self.action_index = index
            self._render()

    def _current_action(self):
        return self.controller.session["actions"][self.action_index]

    def _render(self):
        session = self.controller.session
        action = self._current_action()
        self.pending_actual_result = None
        self.pending_controls.hide()
        self.action_selector.setEnabled(True)
        recorded = action["result"] is not None
        self.result_choices.setVisible(not recorded)
        self.saved_summary.setVisible(recorded)
        self.retract_button.setVisible(recorded)
        self.note.setReadOnly(recorded)
        self.note.setText(
            (action.get("note") or "") if recorded else self._draft_notes.get(self.action_index, "")
        )
        if recorded:
            actual = "、".join(
                f"{item['value']:g} {label(DOSE_UNIT_LABELS, item['unit'])}"
                + (" / 每侧" if item['per_side'] else "")
                for item in action.get("actual_sets", [])
            )
            self.saved_summary.setText(
                f"已保存 · {label(RESULT_LABELS, action['result'])}"
                + (f"\n实际剂量：{actual}" if actual else "")
            )
        self.values.setVisible(False)
        self.actual_hint.setVisible(False)
        self.add_actual_set_button.setVisible(False)
        self._set_result_button_labels()
        for button in self.result_button_by_value.values():
            button.setEnabled(action["result"] is None)
        completed_count = sum(item["result"] is not None for item in session["actions"])
        ready_to_finish = completed_count == len(session["actions"])
        self.next_button.setVisible(recorded and not ready_to_finish)
        self.progress_bar.setRange(0, len(session["actions"]))
        self.progress_bar.setValue(completed_count)
        self.finish_button.setEnabled(ready_to_finish)
        self.finish_button.setText("完成训练")
        self.finish_button.setToolTip("所有动作记录后即可完成训练")
        self.progress.setText(
            f"动作进度：已记录 {completed_count}/{len(session['actions'])} 项；"
            f"当前第 {self.action_index + 1} 项："
            f"{label(RESULT_LABELS, action['result']) if action['result'] else '未记录'}"
        )
        self.title.setText(
            f"第 {action['plan_day_order']} 天 / 第 {action['plan_action_order']} 项："
            f"{action['exercise_name_snapshot']}"
        )
        self.status.setText(
            f"训练日期：{session['training_date']} | 状态："
            f"{label(SESSION_STATUS_LABELS, session['status'])}"
        )
        self.planned.setText("计划剂量：\n" + session_prescription_text(action))
        while self.values_layout.rowCount():
            self.values_layout.removeRow(0)
        self.value_edits = []
        self.actual_unit_selectors = []
        self.actual_side_checks = []
        for index, item in enumerate(action["sets"], 1):
            self._add_actual_set_row(f"第 {index} 组", item)

    def _add_actual_set(self) -> None:
        action = self._current_action()
        self._add_actual_set_row(f"实际第 {len(self.value_edits) + 1} 组", action["sets"][-1])

    def _set_result_button_labels(self, pending_result=None) -> None:
        for result, button in self.result_button_by_value.items():
            result_name = label(RESULT_LABELS, result)
            button.setText(f"保存{result_name}结果" if result == pending_result else result_name)

    def _add_actual_set_row(self, title: str, planned_set: dict) -> None:
        """按计划组的默认值追加一行实际剂量录入控件（剂量/单位/每侧）。"""
        edit = QLineEdit()
        edit.setPlaceholderText(f"实际{label(DOSE_UNIT_LABELS, planned_set['planned_unit'])}")
        unit = make_unit_combo(planned_set["planned_unit"])
        per_side = QCheckBox("每侧")
        per_side.setChecked(bool(planned_set["planned_per_side"]))
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(edit, 1)
        row_layout.addWidget(unit)
        row_layout.addWidget(per_side)
        self.values_layout.addRow(title, row)
        self.value_edits.append(edit)
        self.actual_unit_selectors.append(unit)
        self.actual_side_checks.append(per_side)

    def _record(self, result):
        if result is None or self._current_action()["result"] is not None:
            return
        if self.pending_actual_result is not None and self.pending_actual_result != result:
            return
        values = ()
        needs_actual = result in (ExerciseResult.EXCEEDED, ExerciseResult.PARTIAL)
        if result != ExerciseResult.COMPLETED and self.pending_actual_result is None:
            self.pending_actual_result = result
            self.values.setVisible(needs_actual)
            self.actual_hint.setVisible(True)
            result_name = label(RESULT_LABELS, result)
            self.actual_hint.setText(
                f"已选择：{result_name}。"
                + ("填写实际完成的组；未做的末尾组留空。" if needs_actual else "确认后保存此结果。")
            )
            self.save_result_button.setText(f"保存{result_name}结果")
            self.result_choices.hide()
            self.pending_controls.show()
            self.action_selector.setEnabled(False)
            self.add_actual_set_button.setVisible(needs_actual)
            return
        if result in (ExerciseResult.EXCEEDED, ExerciseResult.PARTIAL):
            self.values.setVisible(True)
            try:
                entered = [edit.text().strip() for edit in self.value_edits]
                first_empty = next(
                    (index for index, value in enumerate(entered) if not value),
                    len(entered),
                )
                if any(entered[first_empty:]):
                    QMessageBox.warning(
                        self, "需要填写实际剂量", "实际剂量必须按顺序填写，空白组只能放在最后。"
                    )
                    return
                actual_sets = tuple(
                    ActualSet(float(text), unit.currentData(), side.isChecked())
                    for text, unit, side in zip(
                        entered[:first_empty],
                        self.actual_unit_selectors[:first_empty],
                        self.actual_side_checks[:first_empty],
                        strict=True,
                    )
                )
            except ValueError:
                QMessageBox.warning(self, "需要填写实际剂量", "请为每一组填写数字。")
                return
        try:
            self.controller.record_result(
                self._current_action()["id"],
                result,
                values,
                self.note.text(),
                actual_sets if result in (ExerciseResult.EXCEEDED, ExerciseResult.PARTIAL) else (),
            )
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "无法记录结果", user_message(str(exc)))
            return
        self.note.clear()
        self._draft_notes.pop(self.action_index, None)
        self.pending_actual_result = None
        self._populate_action_selector()
        self._render()
        self.session_changed.emit()

    def _cancel_result(self):
        self._draft_notes[self.action_index] = self.note.text()
        self._render()

    def _retract(self):
        action = self._current_action()
        answer = QMessageBox.question(
            self, "撤回这个动作的结果？",
            f"“{action['exercise_name_snapshot']}”将恢复为未记录，可重新填写。原记录会保留在历史中。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.retract_result(action["id"])
        except ValueError as exc:
            QMessageBox.warning(self, "无法撤回", user_message(str(exc)))
            return
        self._draft_notes[self.action_index] = action.get("note") or ""
        self._populate_action_selector()
        self._render()
        self.session_changed.emit()

    def _pause(self):
        if not self._confirm_leave():
            return
        try:
            self.controller.pause()
        except ValueError as exc:
            QMessageBox.warning(self, "无法暂停训练", user_message(str(exc)))
            return
        self._leaving = True
        self.session_ended.emit()

    def _abort(self):
        if not self._confirm_leave():
            return
        dialog = AbortDialog(self)
        if not dialog.exec():
            return
        if dialog.reason.currentData() is None:
            QMessageBox.warning(self, "需要中止原因", "请明确选择一个中止原因。")
            return
        try:
            reason = AbortReason(dialog.reason.currentData())
            self.controller.abort(reason, dialog.note.text())
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "无法中止训练", user_message(str(exc)))
            return
        self._leaving = True
        self.session_ended.emit()

    def _confirm_leave(self):
        if self._leaving:
            return True
        unsaved_note = (
            self._current_action()["result"] is None and bool(self.note.text())
        ) or any(self._draft_notes.values())
        if self.pending_actual_result is None and not unsaved_note:
            return True
        return QMessageBox.question(
            self, "放弃尚未保存的录入？",
            "当前录入的结果或备注尚未保存。离开将放弃这些输入，已保存的动作会保留。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def closeEvent(self, event):
        if self._confirm_leave():
            event.accept()
        else:
            event.ignore()

    def _finish(self):
        answer = QMessageBox.question(
            self,
            "确认完成训练",
            "确认保存本次训练的最终结果吗？保存后不能继续记录动作。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.finish()
        except ValueError as exc:
            QMessageBox.warning(self, "无法完成训练", user_message(str(exc)))
            return
        self._leaving = True
        self.session_ended.emit()
