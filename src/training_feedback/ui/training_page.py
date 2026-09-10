"""训练执行页：逐动作记录结果（含实际剂量两步录入）、暂停/中止/完成。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
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
        self.result_button_by_value = {}
        self.setWindowTitle("训练")
        self.title = QLabel()
        self.status = QLabel()
        self.progress = QLabel()
        self.action_selector = QComboBox()
        self.action_selector.currentIndexChanged.connect(self._select_action)
        self.planned = QLabel()
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
        content_layout.addWidget(self.title)
        content_layout.addWidget(self.status)
        content_layout.addWidget(self.progress)
        content_layout.addWidget(self.action_selector)
        content_layout.addWidget(self.planned)
        content_layout.addWidget(self.actual_hint)
        content_layout.addWidget(self.values)
        content_layout.addWidget(self.add_actual_set_button)
        content_layout.addWidget(self.note)
        for result_label, result_value in (
            (label(RESULT_LABELS, result), result)
            for result in (
                ExerciseResult.EXCEEDED,
                ExerciseResult.COMPLETED,
                ExerciseResult.PARTIAL,
                ExerciseResult.NOT_COMPLETED,
            )
        ):
            button = QPushButton(result_label)
            button.clicked.connect(lambda _checked=False, result=result_value: self._record(result))
            content_layout.addWidget(button)
            self.result_button_by_value[result_value] = button
        content_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidget(content)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area, 1)
        session_controls = QWidget()
        controls_layout = QHBoxLayout(session_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        pause = QPushButton("暂停训练")
        pause.clicked.connect(self._pause)
        abort = QPushButton("中止训练")
        abort.clicked.connect(self._abort)
        finish = QPushButton("完成训练")
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
        self.action_index = self.controller.first_unfinished_index()
        self.action_selector.setCurrentIndex(self.action_index)
        self._render()

    def _populate_action_selector(self):
        self.action_selector.blockSignals(True)
        self.action_selector.clear()
        for index, action in enumerate(self.controller.session["actions"]):
            self.action_selector.addItem(
                f"第 {action['plan_day_order']} 天 / 第 {action['plan_action_order']} 项："
                f"{action['exercise_name_snapshot']}",
                index,
            )
        self.action_selector.setCurrentIndex(self.action_index)
        self.action_selector.blockSignals(False)

    def _select_action(self, index):
        if index >= 0:
            self.action_index = index
            self._render()

    def _current_action(self):
        return self.controller.session["actions"][self.action_index]

    def _render(self):
        session = self.controller.session
        action = self._current_action()
        self.pending_actual_result = None
        self.values.setVisible(False)
        self.actual_hint.setVisible(False)
        self.add_actual_set_button.setVisible(False)
        self._set_result_button_labels()
        for button in self.result_button_by_value.values():
            button.setEnabled(action["result"] is None)
        completed_count = sum(item["result"] is not None for item in session["actions"])
        ready_to_finish = completed_count == len(session["actions"])
        self.finish_button.setEnabled(ready_to_finish)
        self.finish_button.setText(
            "完成训练" if ready_to_finish else "完成训练（请先记录全部动作）"
        )
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
        self.planned.setText(
            "计划剂量："
            + ", ".join(
                f"{item['planned_value']} {label(DOSE_UNIT_LABELS, item['planned_unit'])}"
                + (" / 每侧" if item["planned_per_side"] else "")
                for item in action["sets"]
            )
        )
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
        row_layout = QFormLayout(row)
        row_layout.addRow("剂量", edit)
        row_layout.addRow("单位", unit)
        row_layout.addRow("范围", per_side)
        self.values_layout.addRow(title, row)
        self.value_edits.append(edit)
        self.actual_unit_selectors.append(unit)
        self.actual_side_checks.append(per_side)

    def _record(self, result):
        values = ()
        if result in (ExerciseResult.EXCEEDED, ExerciseResult.PARTIAL):
            if self.values.isHidden() or self.pending_actual_result != result:
                self.pending_actual_result = result
                self.values.setVisible(True)
                self.actual_hint.setVisible(True)
                result_name = label(RESULT_LABELS, result)
                self.actual_hint.setText(f"填写每组实际剂量后，点击“保存{result_name}结果”。")
                self._set_result_button_labels(result)
                self.add_actual_set_button.setVisible(True)
                return
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
        self.pending_actual_result = None
        if self.action_index + 1 < len(self.controller.session["actions"]):
            self.action_index += 1
            self.action_selector.blockSignals(True)
            self.action_selector.setCurrentIndex(self.action_index)
            self.action_selector.blockSignals(False)
        self._render()
        self.session_changed.emit()

    def _pause(self):
        try:
            self.controller.pause()
        except ValueError as exc:
            QMessageBox.warning(self, "无法暂停训练", user_message(str(exc)))
            return
        self.session_ended.emit()

    def _abort(self):
        dialog = AbortDialog(self)
        if not dialog.exec():
            return
        try:
            reason = AbortReason(dialog.reason.currentData())
            self.controller.abort(reason, dialog.note.text())
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "无法中止训练", user_message(str(exc)))
            return
        self.session_ended.emit()

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
        self.session_ended.emit()
