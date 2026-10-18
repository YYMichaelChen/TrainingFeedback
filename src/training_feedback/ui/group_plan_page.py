"""Native editor for versioned single/group plans; all saves use the new-model service."""

from __future__ import annotations

from copy import deepcopy
from itertools import islice
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..domain.execution_modes import (
    ALTERNATING_START_LABELS,
    EXECUTION_MODE_LABELS,
    alternating_explanation,
    execution_mode,
    upgrade_payload,
)
from ..domain.group_plans import (
    PlanDocument,
    action_from_choice,
    blank_group,
    continuous_plan_day,
    diff_plans,
    group_from_item,
    normalize_group_side_fields,
    normalize_inapplicable_rest,
    prescription_rest_applicability,
)
from ..domain.plan_editing import PlanIssues
from ..error_messages import issue_text
from .compact_widgets import ActionBar, CardList, frame_combo_popup
from .exercise_reading import PlanGuidance
from .labels import (
    DOSE_UNIT_LABELS,
    EXERCISE_SOURCE_LABELS,
    OPERATION_ERRORS,
    PLAN_PHASE_LABELS,
    PLAN_STATUS_LABELS,
    POSITION_LABELS,
    VARIANT_LABELS,
    confirm,
    localize_dialog_buttons,
    user_message,
)
from .labels import (
    GROUP_PLAN_TEXT as T,
)
from .plan_layout import PlanActionTree, PlanPanes
from .plan_presentation import plan_presentation
from .relative_widgets import AdaptiveFields, LocalScrollArea, RelativeTable, ResizableTextEdit
from .sizing import bind_units, fit_dialog, initial_size, scale_manager, u


class _ScrollCombo(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class _ScrollSpin(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


def combo(mapping, selected):
    widget = _ScrollCombo()
    for key, value in mapping.items():
        widget.addItem(value, key)
    widget.setCurrentIndex(widget.findData(selected))
    return widget


def text(edit, original):
    """Qt may normalize CRLF; leave untouched source text verbatim."""
    current = edit.toPlainText()
    return original if current == original.replace("\r\n", "\n").replace("\r", "\n") else current


def error(parent, exc, *, issue_summary=None):
    if isinstance(exc, PlanIssues):
        dialog = PlanProblemDialog(exc.issues, parent=parent, summary=issue_summary)
        dialog.exec()
        return
    QMessageBox.warning(parent, T["error"], user_message(exc))


def dialog_buttons(dialog, save):
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    localize_dialog_buttons(buttons)
    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    return buttons


def number(edit, label, *, optional=False):
    # Draft collection preserves invalid and unfinished input, including whitespace.
    return edit.text()


def action_editor_state(dialog):
    return (
        dialog.exercise.currentData(), dialog.exercise.currentText(),
        dialog.mode.currentData(), dialog.alternating_start.currentData(),
        dialog.phase.currentData(), dialog.side.currentData(),
        dialog.side_rest.text(), dialog.rest.text(), dialog.note.toPlainText(),
        [(dialog.sets.item(row, 0).text(),
          dialog.sets.cellWidget(row, 1).currentData(),
          dialog.sets.cellWidget(row, 2).currentData(),
          dialog.sets.item(row, 3).text(), dialog.sets.item(row, 4).text())
         for row in range(dialog.sets.rowCount())],
    )


def hide_editor_buttons(dialog):
    dialog.buttons.hide()
    for button in dialog.buttons.buttons():
        button.setAutoDefault(False)
        button.setDefault(False)
        button.setEnabled(False)


class ActionPrescriptionDialog(QDialog):
    def __init__(self, choices, action=None, *, member=False, parent=None, service=None,
                 embedded=False):
        super().__init__(parent)
        self.member, self.source, self.value = member, deepcopy(action), None
        self.service = service
        self.setWindowTitle(T["action"])
        if not embedded:
            fit_dialog(self)
        body = QWidget()
        fields = QVBoxLayout(body)
        form = AdaptiveFields()
        self.exercise = _ScrollCombo()
        frame_combo_popup(self.exercise)
        self.exercise.setEditable(True)
        self.exercise.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.exercise.setMinimumContentsLength(18)
        self.exercise.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        available = list(choices)
        if action and action.get("exercise") and not any(
            choice["content"] == action["content"] and choice["exercise"] == action["exercise"]
            for choice in available
        ):
            available.insert(
                0,
                {
                    key: action[key]
                    for key in ("exercise", "exercise_name", "content", "classification")
                },
            )
        self.exercise.addItem(T["choose"], None)
        for choice in available:
            self.exercise.addItem(
                f"{choice['exercise_name']} · "
                f"{POSITION_LABELS[choice['classification']['starting_position_class']]}",
                choice,
            )
        if action:
            for i in range(1, self.exercise.count()):
                choice = self.exercise.itemData(i)
                if (
                    choice["exercise"] == action["exercise"]
                    and choice["content"] == action["content"]
                ):
                    self.exercise.setCurrentIndex(i)
                    break
        form.addRow(T["choose"], self.exercise)
        self.mode = combo({None: "未选择", **EXECUTION_MODE_LABELS},
                          execution_mode(action) if action else "whole")
        self.alternating_start = combo(ALTERNATING_START_LABELS,
                                       action.get("alternating_start") if action else None)
        if action and "provenance" in action:
            self.mode.setEnabled(False)
        form.addRow("执行方式", self.mode)
        form.addRow("每组先到哪一侧", self.alternating_start)
        self.phase = combo(PLAN_PHASE_LABELS, action.get("phase", "main") if action else "main")
        self.side = combo(
            {None: T["none"], "left": T["left"], "right": T["right"]},
            action.get("first_side") if action else None,
        )
        if action and "provenance" in action:
            self.side.setEnabled(False)
        self.side_rest = QLineEdit(
            str(action.get("rest_between_sides_seconds", "") if action else "")
        )
        rest_key = "rest_after_member_seconds" if member else "rest_after_action_seconds"
        self.rest = QLineEdit(str(action.get(rest_key, "") if action else ""))
        for edit in (self.side_rest, self.rest):
            if edit.text() == "None":
                edit.clear()
                edit.setPlaceholderText(T["unknown"])
        if not member:
            form.addRow(T["phase"], self.phase)
            form.addRow(T["first_side"], self.side)
            form.addRow(T["side_rest"], self.side_rest)
        form.addRow(T["member_rest"] if member else T["exit_rest"], self.rest)
        self.note = ResizableTextEdit(action["note"] if action else "")
        form.addRow(T["note"], self.note)
        fields.addWidget(form)
        fields.addWidget(QLabel(T["sets"]))
        self.sets = RelativeTable([5, 4, 3, 6, 4, 4, 4, 2],
                                  compact_columns=(0, 1, 2, 3, 5, 6, 7))
        self.sets.setHorizontalHeaderLabels(
            [T["value"], T["unit"], "计量口径", T["set_rest"], T["note"]]
            + [T["set_order"], "操作", "#"]
        )
        self.sets.horizontalHeader().setSectionsMovable(False)
        self.sets.horizontalHeader().moveSection(5, 0)
        self.sets.horizontalHeader().moveSection(7, 0)
        self.exercise.currentIndexChanged.connect(self.refresh_rest_fields)
        self.mode.currentIndexChanged.connect(self.refresh_rest_fields)
        self.alternating_start.currentIndexChanged.connect(self.refresh_rest_fields)
        with self.sets.batch_metrics():
            for dose in action["sets"] if action else []:
                self._append_set(dose)
            self.refresh_rest_fields()
        fields.addWidget(self.sets)
        self.counting_hint = QLabel()
        self.counting_hint.setWordWrap(True)
        fields.addWidget(self.counting_hint)
        self.sets.itemChanged.connect(self.refresh_counting_hint)
        self.refresh_counting_hint()
        controls = ActionBar()
        add = QPushButton(T["add_set"])
        add.clicked.connect(lambda: self.add_set())
        remove = QPushButton(T["remove_set"])
        remove.clicked.connect(self.remove_set)
        fill = QPushButton(T["fill_equal_sets"])
        fill.clicked.connect(self.fill_equal_sets)
        controls.addWidget(add)
        controls.addWidget(remove)
        controls.addWidget(fill)
        fields.addWidget(controls)
        fields.addStretch()
        scroll = LocalScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body)
        self.sets.height_budget = lambda: scroll.viewport().height()
        bind_units(fields, "setContentsMargins", 1.5, 1.5, 1.5, 1.5)
        layout = QVBoxLayout(self)
        if service is not None and not embedded:
            center = QWidget()
            center_layout = QVBoxLayout(center)
            center_layout.setContentsMargins(0, 0, 0, 0)
            center_layout.addWidget(scroll, 1)
            self.reading = PlanGuidance()
            self.panes = PlanPanes(QWidget(), center, self.reading, None, self)
            self.exercise.currentIndexChanged.connect(self.show_guidance)
            self.show_guidance()
            layout.addWidget(self.panes, 1)
        else:
            layout.addWidget(scroll, 1)
        self.buttons = dialog_buttons(self, self.save)
        layout.addWidget(self.buttons)
        if action and action.get("_input"):
            cache = action["_input"]
            if "exercise_search" in cache:
                self.exercise.setEditText(cache["exercise_search"])
            self.side_rest.setProperty("applicableText", cache.get("side_rest", ""))
            self.side.setProperty("applicableSide", cache.get("side"))
            if action.get("execution_mode") != "alternating":
                self.alternating_start.setCurrentIndex(
                    self.alternating_start.findData(cache.get("alternating_start")))
            for row, raw in enumerate(cache.get("set_rests", [])):
                if row < self.sets.rowCount():
                    self.sets.item(row, 3).setData(Qt.ItemDataRole.UserRole, raw)
            for row, raw in enumerate(cache.get("alternating_measures", [])):
                if row < self.sets.rowCount():
                    self.sets.cellWidget(row, 2).setProperty("alternatingMeasure", raw)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "panes"):
            self.panes.reflow()

    def show_guidance(self):
        if hasattr(self, "guidance_visible") and not self.guidance_visible():
            return
        choice = self.exercise.currentData()
        if choice is None:
            self.reading.set_content(None, None, lambda index: b"")
            return
        try:
            if choice != getattr(self, "_guidance_choice", None):
                self._guidance_entry = self.service.action_content(choice)
                self._guidance_choice = deepcopy(choice)
            entry = self._guidance_entry
            if self.reading.identity == entry["reference"]:
                return
            self.reading.set_content(
                entry["reference"], entry["content"]["guidance"],
                lambda index, action=deepcopy(choice): self.service.action_image(action, index),
            )
        except OPERATION_ERRORS as exc:
            self.reading.set_content(None, None, lambda index: b"")
            self.reading.setToolTip(user_message(exc))

    def add_set(self, dose=None):
        with self.sets.batch_metrics():
            self._append_set(dose)
            self.refresh_rest_fields()

    def _append_set(self, dose=None):
        row = self.sets.rowCount()
        self.sets.insertRow(row)
        dose = dose or {
            "value": None,
            "unit": "reps",
            "per_side": False,
            "rest_after_set_seconds": None,
            "note": "",
        }
        self.sets.setItem(
            row, 0, QTableWidgetItem("" if dose["value"] is None else str(dose["value"]))
        )
        self.sets.setCellWidget(row, 1, combo(
            {unit.value: label for unit, label in DOSE_UNIT_LABELS.items()}, dose["unit"]
        ))
        self.sets.cellWidget(row, 1).currentIndexChanged.connect(self.refresh_counting_hint)
        alternating = self.mode.currentData() == "alternating"
        check = combo({False: "总次数" if alternating else "整体剂量",
                       True: "每侧次数" if alternating else "每侧剂量"},
                      dose["per_side"])
        check.currentIndexChanged.connect(self.refresh_rest_fields)
        self.sets.setCellWidget(row, 2, check)
        self.sets.setItem(row, 3, QTableWidgetItem(
            "" if dose["rest_after_set_seconds"] is None else str(dose["rest_after_set_seconds"])))
        note = QTableWidgetItem(dose["note"])
        note.setData(Qt.ItemDataRole.UserRole, dose["note"])
        self.sets.setItem(row, 4, note)
        order = QTableWidgetItem(str(row + 1))
        order.setFlags(order.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.sets.setItem(row, 5, order)
        ordinal = QTableWidgetItem(str(row + 1))
        ordinal.setFlags(ordinal.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.sets.setItem(row, 7, ordinal)
        remove = QPushButton("删除")
        remove.setObjectName("tableActionButton")
        remove.clicked.connect(lambda checked=False, button=remove: self._remove_set_button(button))
        self.sets.setCellWidget(row, 6, remove)

    def _remove_set_button(self, button):
        for row in range(self.sets.rowCount()):
            if self.sets.cellWidget(row, 6) is button:
                self.sets.setCurrentCell(row, 0)
                self.remove_set()
                break

    def remove_set(self):
        if self.sets.currentRow() >= 0:
            self.sets.removeRow(self.sets.currentRow())
            for row in range(self.sets.rowCount()):
                self.sets.item(row, 5).setText(str(row + 1))
                self.sets.item(row, 7).setText(str(row + 1))
            self.refresh_rest_fields()

    def refresh_rest_fields(self):
        with self.sets.batch_metrics():
            self._refresh_rest_fields()

    def _refresh_rest_fields(self):
        mode = self.mode.currentData()
        self.alternating_start.setEnabled(mode == "alternating")
        for row in range(self.sets.rowCount()):
            measure = self.sets.cellWidget(row, 2)
            with QSignalBlocker(measure):
                if getattr(self, "_previous_mode", None) == "alternating" and mode != "alternating":
                    measure.setProperty("alternatingMeasure", measure.currentData())
                elif (getattr(self, "_previous_mode", None) != "alternating"
                      and mode == "alternating"):
                    cached = measure.property("alternatingMeasure")
                    if cached is not None:
                        measure.setCurrentIndex(measure.findData(cached))
                measure.setItemText(0, "总次数" if mode == "alternating" else "整体剂量")
                measure.setItemText(1, "每侧次数" if mode == "alternating" else "每侧剂量")
                if mode in ("whole", "separate_sides"):
                    measure.setCurrentIndex(measure.findData(mode == "separate_sides"))
                measure.setEnabled(mode == "alternating")
        self._previous_mode = mode
        choice = self.exercise.currentData()
        aggregate = bool(self.source and "provenance" in self.source and choice
                         and choice["exercise"] == self.source["exercise"])
        applicability = prescription_rest_applicability(
            [{"per_side": self.sets.cellWidget(row, 2).currentData()}
             for row in range(self.sets.rowCount())],
            aggregate=aggregate,
            mode=mode,
        )
        for row, applicable in enumerate(applicability["set_rests"]):
            item = self.sets.item(row, 3)
            if item is None:
                continue
            if applicable:
                if not item.flags() & Qt.ItemFlag.ItemIsEditable:
                    item.setText(item.data(Qt.ItemDataRole.UserRole) or "")
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setToolTip("空白表示未知；不休息请填写 0。")
            else:
                if item.flags() & Qt.ItemFlag.ItemIsEditable:
                    # The terminal zero is structural, not a prescribed rest for a new set.
                    raw = item.text()
                    item.setData(Qt.ItemDataRole.UserRole, "" if raw in ("0", "0.0") else raw)
                item.setText(T["none"])
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip("最后一组之后使用动作或成员后的休息，无额外组间休息。")
        if not self.member:
            applicable = applicability["side_rest"]
            was_enabled = self.side_rest.isEnabled()
            if was_enabled and not applicable:
                raw = self.side_rest.text()
                if not getattr(self, "_side_rest_initialized", False) and raw in ("0", "0.0"):
                    raw = ""
                self.side_rest.setProperty("applicableText", raw)
                self.side_rest.setText(T["none"])
                self.side.setProperty("applicableSide", self.side.currentData())
                self.side.setCurrentIndex(self.side.findData(None))
            elif not was_enabled and applicable:
                self.side_rest.setText(self.side_rest.property("applicableText") or "")
                self.side.setCurrentIndex(self.side.findData(self.side.property("applicableSide")))
            self._side_rest_initialized = True
            self.side_rest.setEnabled(applicable)
            self.side.setEnabled(applicable and not aggregate)
            self.side_rest.setPlaceholderText(T["unknown"] if applicable else T["none"])
        self.sets.update_metrics()
        self.refresh_counting_hint()

    def refresh_counting_hint(self):
        if not hasattr(self, "counting_hint"):
            return
        alternating = self.mode.currentData() == "alternating"
        self.counting_hint.setVisible(alternating)
        if alternating:
            action = {"alternating_start": self.alternating_start.currentData()}
            self.counting_hint.setText("\n".join(
                f"第 {row + 1} 组：" + alternating_explanation(action, {
                    "value": self.sets.item(row, 0).text(),
                    "unit": self.sets.cellWidget(row, 1).currentData(),
                    "per_side": self.sets.cellWidget(row, 2).currentData()})
                for row in range(self.sets.rowCount())
                if self.sets.item(row, 0) and self.sets.cellWidget(row, 2)))

    def fill_equal_sets(self):
        source = self.sets.currentRow()
        if source < 0 or self.sets.rowCount() < 2:
            return
        answer = QMessageBox.question(
            self,
            T["fill_equal_sets"],
            T["fill_equal_sets_confirm"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        value = self.sets.item(source, 0).text()
        unit = self.sets.cellWidget(source, 1).currentData()
        per_side = self.sets.cellWidget(source, 2).currentData()
        rest_item = self.sets.item(source, 3)
        rest = rest_item.text() if rest_item.flags() & Qt.ItemFlag.ItemIsEditable else None
        note = self.sets.item(source, 4).text()
        for row in range(self.sets.rowCount()):
            if row == source:
                continue
            self.sets.item(row, 0).setText(value)
            self.sets.cellWidget(row, 1).setCurrentIndex(
                self.sets.cellWidget(row, 1).findData(unit)
            )
            self.sets.cellWidget(row, 2).setCurrentIndex(
                self.sets.cellWidget(row, 2).findData(per_side))
            target_rest = self.sets.item(row, 3)
            if rest is not None and target_rest.flags() & Qt.ItemFlag.ItemIsEditable:
                target_rest.setText(rest)
            self.sets.item(row, 4).setText(note)
        self.refresh_rest_fields()

    def save(self, *, accept=True):
        try:
            choice = self.exercise.currentData()
            if choice is None:
                choice = {"exercise": {}, "content": {}, "exercise_name": "",
                          "classification": {"starting_position_class": "unknown"}}
            action = (
                deepcopy(self.source)
                if self.source
                else action_from_choice(choice, member=self.member)
            )
            if self.source and choice["exercise"] != self.source["exercise"]:
                action = action_from_choice(choice, member=self.member)
                action["order"] = self.source["order"]
            action.update(deepcopy(choice))
            doses = []
            for row in range(self.sets.rowCount()):
                doses.append(
                    {
                        "order": row + 1,
                        "value": number(self.sets.item(row, 0), f"第 {row + 1} 组数值",
                                        optional=True),
                        "unit": self.sets.cellWidget(row, 1).currentData(),
                        "per_side": self.sets.cellWidget(row, 2).currentData(),
                        "rest_after_set_seconds": (
                            number(self.sets.item(row, 3), f"第 {row + 1} 组的组间休息秒",
                                   optional="provenance" in action)
                            if self.sets.item(row, 3).flags() & Qt.ItemFlag.ItemIsEditable else None
                        ),
                        "note": self.sets.item(row, 4).text(),
                    }
                )
            action["sets"] = doses
            action["execution_mode"] = self.mode.currentData()
            action["alternating_start"] = (self.alternating_start.currentData()
                if self.mode.currentData() == "alternating" else None)
            action["note"] = text(self.note, self.source["note"] if self.source else "")
            action["rest_after_member_seconds" if self.member else "rest_after_action_seconds"] = (
                number(self.rest, T["member_rest"] if self.member else T["exit_rest"],
                       optional="provenance" in action)
            )
            if not self.member:
                action.update(
                    phase=self.phase.currentData(),
                    first_side=self.side.currentData(),
                    rest_between_sides_seconds=(
                        number(self.side_rest, T["side_rest"], optional="provenance" in action)
                        if self.side_rest.isEnabled() else None
                    ),
                )
            action = normalize_inapplicable_rest(action)
            action["_input"] = {
                "alternating_measures": [self.sets.cellWidget(row, 2).currentData()
                    if self.mode.currentData() == "alternating"
                    else self.sets.cellWidget(row, 2).property("alternatingMeasure")
                    for row in range(self.sets.rowCount())],
                "alternating_start": self.alternating_start.currentData(),
                "side_rest": (self.side_rest.text() if self.side_rest.isEnabled()
                              else self.side_rest.property("applicableText") or ""),
                "side": (self.side.currentData() if self.side.isEnabled()
                         else self.side.property("applicableSide")),
                "exercise_search": self.exercise.currentText(),
                "set_rests": [self.sets.item(row, 3).data(Qt.ItemDataRole.UserRole) or ""
                              for row in range(self.sets.rowCount())],
            }
            self.value = action
        except (ValueError, TypeError) as exc:
            error(self, exc)
            return False
        if accept:
            self.accept()
        return True


class GroupPrescriptionDialog(QDialog):
    members_changed = Signal()
    selection_changed = Signal(int)

    def __init__(self, choices, group=None, parent=None, *, service=None):
        super().__init__(parent)
        self.choices = choices
        self.service = service
        self.member_editors = {}
        self.member_states = {}
        self.value = None
        self.group = deepcopy(group) if group else blank_group()
        if group is None:
            for key in (
                "rest_between_sides_seconds",
                "rest_between_rounds_seconds",
                "rest_after_group_seconds",
            ):
                self.group[key] = None
        self.setWindowTitle(T["group"])
        initial_size(self, 51.25, 41.25)
        outer = QVBoxLayout(self)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)
        body = QWidget()
        layout = QVBoxLayout(body)
        form = AdaptiveFields()
        self.name = QLineEdit(self.group["name"])
        self.phase = combo(PLAN_PHASE_LABELS, self.group["phase"])
        self.rounds = QLineEdit(str(self.group["round_count"]))
        self.side = combo(
            {None: T["none"], "left": T["left"], "right": T["right"]}, self.group["first_side"]
        )
        self.sequence = combo(
            {
                key: T[key]
                for key in ("member_each_side", "same_side_then_switch", "all_rounds_then_switch")
            },
            self.group["side_sequence"],
        )
        self.fields = {}
        for key, label in (
            ("rest_between_sides_seconds", "side_rest"),
            ("rest_between_rounds_seconds", "round_rest"),
            ("rest_after_group_seconds", "rest_after_group_seconds"),
        ):
            self.fields[key] = QLineEdit(
                "" if self.group[key] is None else str(self.group[key])
            )
            form.addRow(T[label], self.fields[key])
        cache = self.group.get("_input", {})
        self.side.setProperty("applicableSide", cache.get("side", self.group["first_side"]))
        self.fields["rest_between_sides_seconds"].setProperty(
            "applicableText", cache.get(
                "side_rest", self.fields["rest_between_sides_seconds"].text()))
        self.transition = ResizableTextEdit(self.group["transition"])
        self.note = ResizableTextEdit(self.group["note"])
        for label, widget in (
            ("group_name", self.name),
            ("phase", self.phase),
            ("rounds", self.rounds),
            ("sequence", self.sequence),
            ("first_side", self.side),
            ("transition", self.transition),
            ("note", self.note),
        ):
            form.addRow(T[label], widget)
        layout.addWidget(form)
        layout.addStretch()
        scroll = LocalScrollArea()
        scroll.setWidget(body)
        self.tabs.addTab(scroll, "动作组设置")
        member_page = QWidget()
        member_layout = QVBoxLayout(member_page)
        hint = QLabel("每轮按顺序完成以下成员。例如：驴踢 1 次 + 消防栓 1 次为一轮；"
                      "分别将两个成员的剂量填为 1 次，在「动作组设置」填写轮数和换侧顺序。")
        hint.setWordWrap(True)
        member_layout.addWidget(hint)
        self.members = _ScrollCombo()
        frame_combo_popup(self.members)
        self.members.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.members.currentIndexChanged.connect(self.edit_member)
        member_layout.addWidget(self.members)
        controls = ActionBar()
        for name, function in (
            ("add_member", self.add_member),
            ("up", lambda: self.move(-1)),
            ("down", lambda: self.move(1)),
            ("remove", self.remove),
        ):
            button = QPushButton(T[name])
            button.clicked.connect(function)
            controls.addWidget(button)
        member_layout.addWidget(controls)
        self.member_stack = QStackedWidget()
        self.no_member = QLabel("添加成员后，在这里填写每轮剂量。")
        self.member_stack.addWidget(self.no_member)
        member_layout.addWidget(self.member_stack, 1)
        self.tabs.addTab(member_page, "成员与每轮剂量")
        self.tabs.currentChanged.connect(self._tab_changed)
        self.buttons = dialog_buttons(self, self.save)
        outer.addWidget(self.buttons)
        self.refresh()
        self.tabs.setCurrentIndex(1)

    def refresh(self, selected_id=None):
        selected_id = selected_id or self.members.currentData()
        blocker = QSignalBlocker(self.members)
        self.members.clear()
        for member in self.group["members"]:
            self.members.addItem(f"{member['order']}. {member['exercise_name']}", member["item_id"])
        index = self.members.findData(selected_id)
        self.members.setCurrentIndex(max(0, index) if self.members.count() else -1)
        del blocker
        self.edit_member()
        self.refresh_side_fields()
        self.members_changed.emit()

    def refresh_side_fields(self):
        separate = any((self.member_editors[member["item_id"]].mode.currentData()
                        if member["item_id"] in self.member_editors else execution_mode(member))
                       == "separate_sides" for member in self.group["members"])
        rest = self.fields["rest_between_sides_seconds"]
        if rest.isEnabled() and not separate:
            rest.setProperty("applicableText", rest.text())
            self.side.setProperty("applicableSide", self.side.currentData())
            rest.setText("不适用")
            self.side.setCurrentIndex(self.side.findData(None))
        elif not rest.isEnabled() and separate:
            rest.setText(rest.property("applicableText") or "")
            self.side.setCurrentIndex(self.side.findData(self.side.property("applicableSide")))
        rest.setEnabled(separate)
        self.side.setEnabled(separate)

    def add_member(self):
        dialog = ActionPrescriptionDialog(self.choices, member=True, parent=self,
                                          service=self.service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.group["members"].append(dialog.value)
            PlanDocument.reorder(self.group["members"])
            self.refresh(dialog.value["item_id"])

    def edit_member(self, *_):
        index = self.members.currentIndex()
        if index < 0:
            self.member_stack.setCurrentWidget(self.no_member)
            return
        member = self.group["members"][index]
        key = member["item_id"]
        if key not in self.member_editors:
            dialog = ActionPrescriptionDialog(
                self.choices, member, member=True, parent=self, service=self.service,
                embedded=True,
            )
            dialog.setWindowFlags(Qt.WindowType.Widget)
            dialog.setMinimumSize(0, 0)
            hide_editor_buttons(dialog)
            dialog.rejected.connect(self.reject)
            self.member_stack.addWidget(dialog)
            self.member_editors[key] = dialog
            self.member_states[key] = action_editor_state(dialog)
            dialog.exercise.currentIndexChanged.connect(self.show_guidance)
            dialog.mode.currentIndexChanged.connect(self.refresh_side_fields)
        self.member_stack.setCurrentWidget(self.member_editors[key])
        if self.tabs.currentIndex() == 1:
            self.selection_changed.emit(index)
        self.show_guidance()

    def _tab_changed(self, index):
        self.selection_changed.emit(self.members.currentIndex() if index == 1 else -1)
        self.show_guidance()

    def select_member(self, index):
        self.members.setCurrentIndex(index)
        self.tabs.setCurrentIndex(1)

    def adopt_value(self, group):
        """Rebase saved form snapshots without rebuilding the member controls."""
        previous = self.group["members"]
        self.group = deepcopy(group)
        for old, member in zip(previous, group["members"], strict=True):
            editor = self.member_editors.pop(old["item_id"], None)
            self.member_states.pop(old["item_id"], None)
            if editor is not None:
                editor.source = deepcopy(member)
                self.member_editors[member["item_id"]] = editor
                self.member_states[member["item_id"]] = action_editor_state(editor)
        with QSignalBlocker(self):
            self.refresh()

    def show_guidance(self, *_):
        if not hasattr(self, "reading") or not self.guidance_visible():
            return
        dialog = self.member_stack.currentWidget()
        if self.tabs.currentIndex() == 1 and isinstance(dialog, ActionPrescriptionDialog):
            dialog.reading = self.reading
            dialog.show_guidance()
        else:
            self.reading.set_content(None, None, lambda index: b"")

    def move(self, offset):
        if self.members.currentIndex() >= 0:
            PlanDocument({"days": []}).move(
                self.group["members"], self.members.currentIndex(), offset
            )
            self.refresh()

    def remove(self):
        index = self.members.currentIndex()
        if index >= 0:
            if len(self.group["members"]) <= 2:
                error(
                    self,
                    ValueError("Keep two members or remove/dissolve the group in the plan tree."),
                )
                return
            member = self.group["members"].pop(index)
            editor = self.member_editors.pop(member["item_id"], None)
            self.member_states.pop(member["item_id"], None)
            if editor is not None:
                self.member_stack.removeWidget(editor)
                editor.deleteLater()
            PlanDocument.reorder(self.group["members"])
            self.refresh()

    def save(self, *, accept=True):
        try:
            members = deepcopy(self.group["members"])
            for index, member in enumerate(members):
                key = member["item_id"]
                editor = self.member_editors.get(key)
                if editor is None:
                    continue
                self.select_member(index)
                if not editor.save(accept=False):
                    return False
                members[index] = {**deepcopy(editor.value), "order": member["order"]}
            group = {
                **self.group,
                "members": members,
                "name": self.name.text(),
                "phase": self.phase.currentData(),
                "round_count": self.rounds.text(),
                "side_sequence": self.sequence.currentData(),
                "first_side": self.side.currentData(),
                "transition": text(self.transition, self.group["transition"]),
                "note": text(self.note, self.group["note"]),
            }
            group.update({key: number(edit, T[key]) if edit.isEnabled() else 0
                          for key, edit in self.fields.items()})
            group["_input"] = {
                "side": self.side.currentData() if self.side.isEnabled()
                        else self.side.property("applicableSide"),
                "side_rest": self.fields["rest_between_sides_seconds"].text()
                    if self.fields["rest_between_sides_seconds"].isEnabled()
                    else self.fields["rest_between_sides_seconds"].property("applicableText") or ""}
            self.value = normalize_group_side_fields(group)
        except OPERATION_ERRORS as exc:
            self.tabs.setCurrentIndex(0)
            error(self, exc)
            return False
        if accept:
            self.accept()
        return True


class MultiExerciseSelectionDialog(QDialog):
    """Searchable multi-pick that inserts unfinished actions into the plan tree."""

    def __init__(self, choices, parent=None):
        super().__init__(parent)
        self.value = None
        self.setWindowTitle(T["add_action"])
        self.search = QLineEdit()
        self.search.setPlaceholderText(T["search_exercises"])
        self.exercise_list = CardList()
        self.exercise_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for choice in choices:
            item = QListWidgetItem(
                f"{choice['exercise_name']} · "
                f"{POSITION_LABELS[choice['classification']['starting_position_class']]}"
            )
            item.setData(Qt.ItemDataRole.UserRole, choice)
            self.exercise_list.addItem(item)
        self.search.textChanged.connect(self.filter_choices)
        layout = QVBoxLayout(self)
        layout.addWidget(self.search)
        layout.addWidget(self.exercise_list, 1)
        self.buttons = dialog_buttons(self, self.save)
        layout.addWidget(self.buttons)

    def filter_choices(self, value):
        query = value.casefold().strip()
        for index in range(self.exercise_list.count()):
            item = self.exercise_list.item(index)
            item.setHidden(query not in item.text().casefold())

    def save(self):
        self.value = [
            item.data(Qt.ItemDataRole.UserRole) for item in self.exercise_list.selectedItems()
        ]
        if not self.value:
            self.value = [{"exercise": {}, "content": {}, "exercise_name": "",
                           "classification": {"starting_position_class": "unknown"}}]
        self.accept()


class GroupPlanEditor(QDialog):
    def __init__(self, service, revision=None, parent=None, *, upgrade_source=None,
                 clone_source=None, clone_base_number=None, clone_name=None,
                 change_description=None):
        super().__init__(parent)
        self.service, self.revision, self.saved_id = service, revision, None
        self.clone_source = clone_source
        self.clone_base_number = clone_base_number
        doc = revision.get("edit_document") if revision else None
        if doc and doc["purpose"] == "clone":
            self.clone_base_number = doc["requested_base_number"]
        self.clone_name = clone_name
        if revision and revision.get("upgrade_source_revision_id") is not None:
            upgrade_source = service.get(revision["upgrade_source_revision_id"])
        self.upgrade_source = upgrade_source
        self.source = (
            deepcopy(revision["payload"])
            if revision
            else deepcopy(clone_source["payload"])
            if clone_source
            else deepcopy(upgrade_source["payload"])
            if upgrade_source
            else {
                "schema": "training_feedback.plan",
                "schema_version": 5,
                "intent": "new",
                "rationale": "",
                "change_description": "",
                "plan": {"name": "", "purpose": "", "days": []},
            }
        )
        self.source = upgrade_payload(self.source)
        self.source.setdefault("intent", "new")
        self.source.setdefault("change_description", "")
        if self.upgrade_source:
            self.source["intent"] = "upgrade"
            self.source["target_base_number"] = self.upgrade_source["base_number"]
        if self.clone_name is not None:
            self.source["plan"]["name"] = self.clone_name
        if clone_source:
            self.source["intent"] = "new"
            self.source.pop("target_base_number", None)
            self.source.pop("plan_code", None)
        if change_description is not None:
            self.source["change_description"] = change_description
        self.document = PlanDocument(self.source["plan"])
        self.document.plan["days"] = [continuous_plan_day(self.document.plan)]
        self.setWindowTitle(T["edit"])
        fit_dialog(self)
        layout = QVBoxLayout(self)
        bind_units(layout, "setContentsMargins", 1.5, 1, 1.5, 1)
        header = QHBoxLayout()
        title = QLabel(T["edit"])
        title.setObjectName("dialogTitle")
        title.setWordWrap(True)
        header.addWidget(title, 1)
        badge = QLabel("草稿")
        badge.setObjectName("muted")
        header.addWidget(badge)
        close = QPushButton("关闭")
        close.clicked.connect(self.reject)
        header.addWidget(close)
        layout.addLayout(header)
        self.name = QLineEdit(self.source["plan"]["name"])
        basic = QHBoxLayout()
        basic.addWidget(QLabel(T["name"]))
        basic.addWidget(self.name, 1)
        self.basic_toggle = QPushButton("展开基本信息")
        self.basic_toggle.setCheckable(True)
        basic.addWidget(self.basic_toggle)
        layout.addLayout(basic)
        self.basic_scroll = LocalScrollArea()
        self.basic_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        form = AdaptiveFields(minimum=20, max_columns=2)
        self.clone_base_input = None
        if clone_source or (doc and doc["purpose"] == "clone"):
            self.clone_base_input = QLineEdit(
                "" if self.clone_base_number is None else str(self.clone_base_number))
            self.clone_base_input.setReadOnly(bool(doc and doc["revision_id"] is not None))
            form.addRow("复制计划编号（001–999；留空自动分配）", self.clone_base_input)
        self.purpose = ResizableTextEdit(self.source["plan"]["purpose"])
        self.rationale = ResizableTextEdit(self.source["rationale"])
        self.change_description = ResizableTextEdit(self.source["change_description"])
        for name, widget in (
            ("purpose", self.purpose),
            ("rationale", self.rationale),
            ("change_description", self.change_description),
        ):
            form.addRow(T[name], widget)
        self.basic_scroll.setWidget(form)
        self.basic_scroll.hide()
        self.basic_toggle.toggled.connect(self._toggle_basic)
        layout.addWidget(self.basic_scroll)
        if self.clone_base_input:
            self.basic_toggle.setChecked(True)
        self.tree = PlanActionTree()
        self.tree.setObjectName("planActions")
        self.tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree.setWordWrap(True)
        self.tree.setHeaderLabels([T["items"]])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree.currentItemChanged.connect(self._show_selected_detail)
        self.tree.reorder_requested.connect(self._reorder_dragged)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._action_menu)
        self.detail_panel = QWidget()
        detail_layout = QVBoxLayout(self.detail_panel)
        self.detail_content_layout = detail_layout
        self.detail_reading = PlanGuidance()
        self.empty_detail = QLabel("选择左侧动作即可编辑；修改后使用底部保存。")
        self.empty_detail.setWordWrap(True)
        detail_layout.addWidget(self.empty_detail)
        bind_units(detail_layout, "setContentsMargins", 0, 0, 0, 0)
        self.inline_editor = None
        self.editors = {}
        self.editor_states = {}
        self._choices = None
        self.pending_add = False
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.tree, 1)
        add = QPushButton("+ 添加动作")
        add.clicked.connect(lambda: self.command("add_action"))
        left_layout.addWidget(add)
        self.panes = PlanPanes(left, self.detail_panel, self.detail_reading, self.tree, self)
        self.panes.guidance_visibility_changed.connect(self._refresh_guidance)
        layout.addWidget(self.panes, 1)
        commands = QHBoxLayout()
        # Keep secondary commands available without a row of overflowing buttons.
        more = QToolButton()
        more.setText("更多操作 ▾")
        more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(more)
        for name in ("add_action", "add_group", "remove", "up", "down", "move_member"):
            menu.addAction(T[name], lambda checked=False, command=name: self.command(command))
        more.setMenu(menu)
        commands.addWidget(more)
        check = QPushButton("检查待完善项")
        check.clicked.connect(self.check_for_activation)
        commands.addWidget(check)
        commands.addStretch()
        self.add_to_plan_button = QPushButton("添加到计划")
        self.add_to_plan_button.setAutoDefault(False)
        self.add_to_plan_button.setToolTip("仅加入左侧计划动作列表，继续编辑；不会保存草稿。")
        self.add_to_plan_button.clicked.connect(self._complete_add)
        commands.addWidget(self.add_to_plan_button)
        self.buttons = dialog_buttons(self, self.save)
        self.buttons.rejected.disconnect(self.reject)
        self.buttons.rejected.connect(self._cancel_editing)
        commands.addWidget(self.buttons)
        self._update_footer()
        layout.addLayout(commands)
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self._update_layout)
        self.refresh()

    def _toggle_basic(self, expanded):
        self.basic_scroll.setVisible(expanded)
        self.basic_toggle.setText("收起基本信息" if expanded else "展开基本信息")
        self._update_layout()

    def _update_layout(self):
        self.basic_scroll.setMaximumHeight(max(u(3), round(self.height() * .3)))
        self.panes.reflow()

    def _refresh_guidance(self, visible=True):
        if visible and isinstance(self.inline_editor,
                                  (ActionPrescriptionDialog, GroupPrescriptionDialog)):
            self.inline_editor.show_guidance()

    def _exercise_choices(self):
        if self._choices is None:
            self._choices = self.service.exercise_choices()
        return self._choices

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "panes"):
            self._update_layout()

    def refresh(self, selection=None):
        blocker = QSignalBlocker(self.tree)
        self.tree.clear()
        for d, day in enumerate(self.document.plan["days"]):
            for i, item in enumerate(day["items"]):
                child = QTreeWidgetItem(
                    [f"≡ {item['order']}. {item.get('name', item.get('exercise_name'))}"]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, (d, i, None))
                self.tree.addTopLevelItem(child)
                for m, member in enumerate(item.get("members", [])):
                    leaf = QTreeWidgetItem(
                        [f"≡ {member['order']}. {member['exercise_name']}"]
                    )
                    leaf.setData(0, Qt.ItemDataRole.UserRole, (d, i, m))
                    child.addChild(leaf)
        self.tree.expandAll()
        if self.tree.topLevelItemCount():
            _d, i, m = selection if selection is not None else (0, 0, None)
            item = self.tree.topLevelItem(min(i or 0, self.tree.topLevelItemCount() - 1))
            if m is not None and m < item.childCount():
                item = item.child(m)
            self.tree.setCurrentItem(item)
        del blocker
        self._prune_editors()
        self._show_selected_detail(self.tree.currentItem())
        self.panes.rebuild_capsules()

    def _reorder_dragged(self, before, after):
        if self.pending_add:
            return
        d, i, m = before
        target = after[1] if m is None else after[2]
        rows = (self.document.plan["days"][d]["items"] if m is None
                else self.document.plan["days"][d]["items"][i]["members"])
        index = i if m is None else m
        self.document.move_to(rows, index, target)
        if m is not None:
            group = self.document.plan["days"][d]["items"][i]
            editor = self.editors.get((group["item_id"], None))
            if editor is not None:
                by_id = {member["item_id"]: member for member in editor.group["members"]}
                editor.group["members"] = [by_id[member["item_id"]] for member in rows]
                PlanDocument.reorder(editor.group["members"])
                # Refresh the picker without rebuilding tree rows mid-move.
                with QSignalBlocker(editor):
                    editor.refresh()
        blocker = QSignalBlocker(self.tree)
        if m is None:
            node = self.tree.takeTopLevelItem(index)
            self.tree.insertTopLevelItem(target, node)
        else:
            parent = self.tree.topLevelItem(i)
            node = parent.takeChild(index)
            parent.insertChild(target, node)
        for row, item in enumerate(self.document.plan["days"][d]["items"]):
            root = self.tree.topLevelItem(row)
            root.setText(0, f"≡ {item['order']}. {item.get('name', item.get('exercise_name'))}")
            root.setData(0, Qt.ItemDataRole.UserRole, (d, row, None))
            for member_index, member in enumerate(item.get("members", [])):
                leaf = root.child(member_index)
                leaf.setText(0, f"≡ {member['order']}. {member['exercise_name']}")
                leaf.setData(0, Qt.ItemDataRole.UserRole, (d, row, member_index))
        node.setExpanded(True)
        self.tree.setCurrentItem(node)
        del blocker
        self._show_selected_detail(node)
        self.panes.rebuild_capsules()

    def _action_menu(self, position):
        if self.pending_add:
            return
        item = self.tree.itemAt(position)
        if item is None:
            return
        self.tree.setCurrentItem(item)
        menu = QMenu(self.tree)
        for name in ("edit_item", "up", "down", "remove", "move_member"):
            menu.addAction(T[name], lambda checked=False, command=name: self.command(command))
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _show_selected_detail(self, item, _previous=None):
        if self.pending_add:
            return
        if item is None:
            self._hide_editor()
            self.empty_detail.show()
            self.detail_reading.set_content(None, None, lambda index: b"")
            return
        d, i, m = item.data(0, Qt.ItemDataRole.UserRole)
        plan_item = self.document.plan["days"][d]["items"][i]
        key = (plan_item["item_id"], None)
        dialog = self.editors.get(key)
        if dialog is not None and dialog is self.inline_editor:
            if isinstance(dialog, GroupPrescriptionDialog):
                if m is not None:
                    dialog.select_member(m)
                elif item is not _previous and _previous is not None:
                    dialog.tabs.setCurrentIndex(0)
            self.panes.update_capsule_selection()
            return
        self._hide_editor()
        if dialog is None:
            choices = self._exercise_choices()
            if plan_item["kind"] == "group":
                dialog = GroupPrescriptionDialog(choices, plan_item, self, service=self.service)
                dialog.members_changed.connect(
                    lambda editor=dialog, group_key=key:
                    self._group_members_changed(editor, group_key)
                )
                dialog.selection_changed.connect(
                    lambda index, editor=dialog, group_key=key:
                    self._group_selection_changed(editor, group_key, index)
                )
            else:
                dialog = ActionPrescriptionDialog(
                    choices, plan_item, parent=self,
                    service=self.service, embedded=True,
                )
            hide_editor_buttons(dialog)
            dialog.rejected.connect(self.reject)
            self.editors[key] = dialog
            self.editor_states[key] = self._editor_state(dialog)
        if m is not None:
            dialog.select_member(m)
        self._show_inline_editor(dialog, d, i, m, existing=True)

    def _group_selection_changed(self, dialog, key, index):
        if self.inline_editor is not dialog:
            return
        for entry, (_d, i, _m), _item in self._locations():
            if entry == key:
                root = self.tree.topLevelItem(i)
                with QSignalBlocker(self.tree):
                    self.tree.setCurrentItem(root.child(index) if index >= 0 else root)
                self.panes.update_capsule_selection()
                break

    def _group_members_changed(self, dialog, key):
        for entry, (d, i, _m), item in self._locations():
            if entry != key:
                continue
            # The group owns member forms. Project only its member list into
            # navigation; unfinished dose input stays in those forms until save.
            item["members"] = deepcopy(dialog.group["members"])
            root = self.tree.topLevelItem(i)
            with QSignalBlocker(self.tree):
                root.takeChildren()
                for m, member in enumerate(item["members"]):
                    leaf = QTreeWidgetItem([f"≡ {member['order']}. {member['exercise_name']}"])
                    leaf.setData(0, Qt.ItemDataRole.UserRole, (d, i, m))
                    root.addChild(leaf)
                index = dialog.members.currentIndex()
                self.tree.setCurrentItem(root.child(index) if index >= 0 else root)
                root.setExpanded(True)
            self.panes.rebuild_capsules()
            break

    @staticmethod
    def _editor_state(dialog):
        if isinstance(dialog, ActionPrescriptionDialog):
            return action_editor_state(dialog)
        return (
            dialog.name.text(), dialog.phase.currentData(), dialog.rounds.text(),
            dialog.side.currentData(), dialog.sequence.currentData(),
            dialog.transition.toPlainText(), dialog.note.toPlainText(),
            [edit.text() for edit in dialog.fields.values()], deepcopy(dialog.group["members"]),
            {key: action_editor_state(editor) for key, editor in dialog.member_editors.items()
             if action_editor_state(editor) != dialog.member_states[key]},
        )

    def _locations(self):
        for d, day in enumerate(self.document.plan["days"]):
            for i, item in enumerate(day["items"]):
                yield (item["item_id"], None), (d, i, None), item
                for m, member in enumerate(item.get("members", [])):
                    yield (item["item_id"], member["item_id"]), (d, i, m), member

    def _commit_editors(self, keys=None):
        locations = {key: (location, item) for key, location, item in self._locations()}
        changes = []
        for key in sorted(keys if keys is not None else self.editors,
                          key=lambda value: value[1] is not None):
            dialog = self.editors[key]
            if key not in locations or self._editor_state(dialog) == self.editor_states[key]:
                continue
            if not dialog.save(accept=False):
                location, _item = locations[key]
                blocker = QSignalBlocker(self.tree)
                node = self.tree.topLevelItem(location[1])
                if location[2] is not None:
                    node = node.child(location[2])
                self.tree.setCurrentItem(node)
                del blocker
                self._hide_editor()
                self._show_inline_editor(dialog, *location, existing=True)
                return False
            changes.append((key, deepcopy(dialog.value)))
        for key, value in changes:
            current = {entry: (location, item) for entry, location, item in self._locations()}
            if key not in current:
                continue
            (d, i, m), source = current[key]
            value["order"] = source["order"]
            rows = self.document.plan["days"][d]["items"]
            if m is not None:
                rows = rows[i]["members"]
            rows[i if m is None else m] = value
            dialog = self.editors[key]
            if isinstance(dialog, ActionPrescriptionDialog):
                dialog.source = deepcopy(value)
            else:
                dialog.adopt_value(value)
            self.editor_states[key] = self._editor_state(dialog)
            if value["item_id"] != source["item_id"]:
                new_key = ((value["item_id"], None) if m is None
                           else (key[0], value["item_id"]))
                self.editors[new_key] = self.editors.pop(key)
                self.editor_states[new_key] = self.editor_states.pop(key)
        return True

    def _discard_editor(self, key):
        if key not in self.editors:
            return
        dialog = self.editors.pop(key)
        self.editor_states.pop(key)
        if dialog is self.inline_editor:
            self._hide_editor()
        dialog.deleteLater()

    def _prune_editors(self):
        keys = {key for key, _location, _item in self._locations()}
        for key in list(self.editors):
            if key not in keys:
                self._discard_editor(key)

    def _hide_editor(self):
        if self.inline_editor is not None:
            self.detail_content_layout.removeWidget(self.inline_editor)
            self.inline_editor.hide()
            self.inline_editor = None

    def command(self, command):
        if self.pending_add:
            return
        selected = self.tree.currentItem()
        d, i, m = selected.data(0, Qt.ItemDataRole.UserRole) if selected else (0, None, None)
        selection = (d, i, m) if d is not None else None
        try:
            if command == "edit_item":
                if selected is not None:
                    self._show_selected_detail(selected)
                return
            if command in ("add_action", "add_group", "edit_item"):
                self.edit_item(command, d, None if command != "edit_item" else i,
                               None if command != "edit_item" else m)
            elif command in ("up", "down"):
                if i is None:
                    return
                rows = (self.document.plan["days"][d]["items"] if m is None
                        else self.document.plan["days"][d]["items"][i]["members"])
                index = i if m is None else m
                target = index + (-1 if command == "up" else 1)
                if 0 <= target < len(rows):
                    self._reorder_dragged((d, i, m), (d, target, None) if m is None
                                          else (d, i, target))
                return
            elif command == "remove" and i is not None:
                if m is not None:
                    group = self.document.plan["days"][d]["items"][i]
                    key = (group["item_id"], None)
                    if not self._commit_editors([key] if key in self.editors else []):
                        return
                    self._discard_editor(key)
                self.remove(d, i, m)
            elif command == "move_member":
                if not self._commit_editors():
                    return
                self.transfer(command, d, i, m)
                for key in list(self.editors):
                    if isinstance(self.editors[key], GroupPrescriptionDialog):
                        self._discard_editor(key)
        except OPERATION_ERRORS as exc:
            error(self, exc)
            return
        if not self.pending_add:
            self.refresh(selection)

    def edit_item(self, command, d, i, m):
        choices = self._exercise_choices()
        items = self.document.plan["days"][d]["items"]
        source = items[i] if command == "edit_item" and i is not None else None
        if command == "edit_item" and source is None:
            return
        if command == "add_action" and i is None:
            dialog = MultiExerciseSelectionDialog(choices, self)
        elif source and m is not None:
            dialog = ActionPrescriptionDialog(
                choices, source["members"][m], member=True, parent=self, service=self.service,
                embedded=True,
            )
        elif command == "add_group" or (source and source["kind"] == "group"):
            dialog = GroupPrescriptionDialog(choices, source, self, service=self.service)
        else:
            dialog = ActionPrescriptionDialog(choices, source, parent=self, service=self.service,
                                              embedded=True)
        self._show_inline_editor(dialog, d, i, m)

    def _show_inline_editor(self, dialog, d, i, m, *, existing=False):
        self._hide_editor()
        self.pending_add = not existing
        hide_editor_buttons(dialog)
        self._update_footer()
        self.tree.setEnabled(existing)
        self.empty_detail.hide()
        self.inline_editor = dialog
        if dialog.parentWidget() is not self.detail_panel:
            dialog.setParent(self.detail_panel)
            dialog.setWindowFlags(Qt.WindowType.Widget)
            dialog.setMinimumSize(0, 0)
        self.detail_content_layout.addWidget(dialog, 1)
        if not existing:
            dialog.accepted.connect(lambda: self._inline_saved(dialog, d, i, m))
            dialog.rejected.connect(self._inline_cancelled)
        if isinstance(dialog, (ActionPrescriptionDialog, GroupPrescriptionDialog)):
            dialog.reading = self.detail_reading
            dialog.guidance_visible = lambda: (self.inline_editor is dialog
                                               and not self.panes.right.isHidden())
            if (isinstance(dialog, ActionPrescriptionDialog)
                    and not getattr(dialog, "_guidance_connected", False)):
                dialog.exercise.currentIndexChanged.connect(dialog.show_guidance)
                dialog._guidance_connected = True
            dialog.show_guidance()
        else:
            self.detail_reading.set_content(None, None, lambda index: b"")
        dialog.show()
        if existing and isinstance(dialog, GroupPrescriptionDialog):
            key = (dialog.group["item_id"], None)
            index = dialog.members.currentIndex() if dialog.tabs.currentIndex() == 1 else -1
            self._group_selection_changed(dialog, key, index)
        self.panes.update_capsule_selection()

    def _inline_saved(self, dialog, d, i, m):
        items = self.document.plan["days"][d]["items"]
        source = items[i] if i is not None else None
        if isinstance(dialog, MultiExerciseSelectionDialog):
            selected = []
            for choice in dialog.value:
                action = action_from_choice(choice)
                action["rest_between_sides_seconds"] = None
                action["rest_after_action_seconds"] = None
                items.append(action)
                selected.append(len(items) - 1)
            PlanDocument.reorder(items)
            selection = (d, selected[0], None)
        elif source is None:
            items.append(dialog.value)
            PlanDocument.reorder(items)
            selection = (d, len(items) - 1, None)
        elif m is not None:
            source["members"][m] = dialog.value
            selection = (d, i, m)
        else:
            items[i] = dialog.value
            selection = (d, i, None)
        self._close_inline_editor()
        self.refresh(selection)

    def _inline_cancelled(self):
        self._close_inline_editor()
        self._show_selected_detail(self.tree.currentItem())

    def _cancel_editing(self):
        if self.pending_add:
            self._inline_cancelled()
        else:
            self.reject()

    def _complete_add(self):
        # Accept only the inline form. Plan persistence belongs to save().
        if self.pending_add:
            self.inline_editor.save()

    def _update_footer(self):
        self.add_to_plan_button.setVisible(self.pending_add)
        save = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        save.setText("保存草稿")
        save.setAutoDefault(not self.pending_add)
        save.setDefault(not self.pending_add)
        self.add_to_plan_button.setDefault(self.pending_add)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "放弃添加" if self.pending_add else "取消"
        )

    def _close_inline_editor(self):
        dialog, self.inline_editor = self.inline_editor, None
        if dialog is not None:
            self.detail_content_layout.removeWidget(dialog)
            dialog.hide()
            dialog.deleteLater()
        self.tree.setEnabled(True)
        self.pending_add = False
        self._update_footer()
        self.panes.rebuild_capsules()

    def remove(self, d, i, m):
        if m is not None:
            group = self.document.plan["days"][d]["items"][i]
            dissolve = len(group["members"]) == 2
            if confirm(self, T["remove"], T["dissolve"] if dissolve else T["remove_confirm"]):
                self.document.remove_member(d, i, m, dissolve=dissolve)
        elif confirm(self, T["remove"], T["remove_confirm"]):
            rows = self.document.plan["days"][d]["items"]
            del rows[i]
            PlanDocument.reorder(rows)

    def transfer(self, command, d, i, m):
        if i is None:
            return
        options, targets = [], []
        for day_index, day in enumerate(self.document.plan["days"]):
            if command == "move_member" and m is not None:
                for group_index, group in enumerate(day["items"]):
                    if group["kind"] == "group" and (day_index, group_index) != (d, i):
                        options.append(f"{group['order']}. {group['name']}")
                        targets.append(group)
        if not targets:
            return
        value, accepted = QInputDialog.getItem(
            self, T[command], T["select_destination"], options, editable=False
        )
        if accepted:
            destination = targets[options.index(value)]
            self.document.move_member(self.document.plan["days"][d]["items"][i], m, destination)

    def save(self):
        if self.pending_add:
            self._complete_add()
            if self.pending_add:
                return
        if not self._commit_editors():
            return
        payload = deepcopy(self.source)
        payload["plan"] = deepcopy(self.document.plan)
        payload["plan"].update(
            name=self.name.text(), purpose=text(self.purpose, self.source["plan"]["purpose"])
        )
        payload["rationale"] = text(self.rationale, self.source["rationale"])
        payload["change_description"] = text(
            self.change_description, self.source["change_description"]
        )
        try:
            before = self.source["plan"] if (self.revision or self.upgrade_source
                                             or self.clone_source) else None
            base = self.clone_base_input.text() if self.clone_base_input else None
            preview = self.service.preview_document(
                payload, revision=self.revision,
                purpose=("upgrade" if self.upgrade_source
                         else "clone" if self.clone_source else "new"),
                source_id=self.upgrade_source["id"] if self.upgrade_source else None, base=base,
            )
            summary = ("预计正式编号：" + preview["plan_code"] if preview["plan_code"]
                       else "正式计划编号待确定")
            summary += f"。有 {len(preview['issues'])} 处待完善，仍可保存草稿。"
            confirmation = DraftSaveConfirmation(
                T["save"], summary,
                [] if preview["issues"] else diff_plans(before, payload["plan"]),
                self, issues=preview["issues"],
            )
            if confirmation.exec() != QDialog.DialogCode.Accepted:
                return False
            result = self.service.save_document(
                payload, identifier=self.revision["id"] if self.revision else None,
                expected_token=self.revision["edit_token"] if self.revision else None,
                purpose=("upgrade" if self.upgrade_source
                         else "clone" if self.clone_source else "new"),
                source_revision_id=(self.upgrade_source["id"] if self.upgrade_source
                                    else self.clone_source.get("normalized_revision_id",
                                         self.clone_source["id"]) if self.clone_source else None),
                requested_base_number=base,
            )
            self.saved_id = result["id"]
            if result["issues"]:
                PlanProblemDialog(
                    result["issues"], parent=self, title="草稿已保存",
                    summary="草稿已保存。以下内容仍需完善后才能启用；可重新打开草稿继续编辑。",
                ).exec()
            else:
                QMessageBox.information(self, "草稿已保存", "草稿已保存，可预览并启用。")
        except OPERATION_ERRORS as exc:
            error(self, exc)
            return
        self.accept()
        return True

    def reject(self):
        box = QMessageBox(self)
        box.setWindowTitle("关闭计划编辑")
        box.setText("是否保存当前输入为草稿？")
        save = box.addButton("保存草稿", QMessageBox.ButtonRole.AcceptRole)
        discard = box.addButton("放弃修改", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("继续编辑", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is save:
            self.save()
        elif box.clickedButton() is discard:
            super().reject()

    def focus_issue(self, issue):
        path = issue.path
        def row_after(key):
            if key not in path:
                return None
            position = path.index(key) + 1
            return (path[position] if position < len(path)
                    and isinstance(path[position], int) else None)

        if path[:2] == ("plan", "name"):
            self.name.setFocus()
            return
        if path and path[0] == "requested_base_number" and self.clone_base_input:
            self.basic_toggle.setChecked(True)
            self.clone_base_input.setFocus()
            return
        if "items" not in path:
            self.basic_toggle.setChecked(True)
            field = path[-1] if path else ""
            {"purpose": self.purpose, "rationale": self.rationale,
             "change_description": self.change_description}.get(field, self.tree).setFocus()
            return
        i = row_after("items")
        if i is None:
            self.tree.setFocus()
            return
        m = row_after("members")
        if issue.node_id:
            for _key, (_d, item_index, member_index), item in self._locations():
                if item["item_id"] == issue.node_id:
                    i, m = item_index, member_index
                    break
        node = self.tree.topLevelItem(i)
        if node is None:
            return
        if m is not None:
            node = node.child(m) or node
        self.tree.setCurrentItem(node)
        dialog = self.inline_editor
        if isinstance(dialog, GroupPrescriptionDialog) and m is not None:
            dialog.select_member(m)
            dialog = dialog.member_stack.currentWidget()
        field = path[-1] if path else ""
        if isinstance(dialog, ActionPrescriptionDialog):
            row = row_after("sets")
            if "sets" in path and (row is None or row >= dialog.sets.rowCount()):
                dialog.sets.setFocus()
                return
            if row is not None:
                column = {"value": 0, "unit": 1, "per_side": 2,
                          "rest_after_set_seconds": 3, "note": 4}.get(field, 0)
                dialog.sets.setCurrentCell(row, column)
                widget = dialog.sets.cellWidget(row, column)
                if widget:
                    widget.setFocus()
                else:
                    dialog.sets.setFocus()
                    cell = dialog.sets.item(row, column)
                    if cell:
                        dialog.sets.editItem(cell)
                return
            widget = {"first_side": dialog.side, "rest_between_sides_seconds": dialog.side_rest,
                      "execution_mode": dialog.mode, "alternating_start": dialog.alternating_start,
                      "rest_after_action_seconds": dialog.rest,
                      "rest_after_member_seconds": dialog.rest, "note": dialog.note,
                      "phase": dialog.phase}.get(
                          field, dialog.exercise)
            widget.setFocus()
        elif isinstance(dialog, GroupPrescriptionDialog):
            if "members" in path:
                dialog.tabs.setCurrentIndex(1)
                dialog.members.setFocus()
                return
            dialog.tabs.setCurrentIndex(0)
            widget = {"name": dialog.name, "round_count": dialog.rounds,
                      "first_side": dialog.side, "side_sequence": dialog.sequence,
                      "transition": dialog.transition, "note": dialog.note,
                      "phase": dialog.phase, **dialog.fields}.get(field, dialog.name)
            widget.setFocus()

    def check_for_activation(self):
        if self.pending_add:
            self.inline_editor.save()
            if self.pending_add:
                return
        if not self._commit_editors():
            return
        payload = deepcopy(self.source)
        payload["plan"] = deepcopy(self.document.plan)
        payload["plan"]["name"] = self.name.text()
        payload["plan"]["purpose"] = text(self.purpose, self.source["plan"]["purpose"])
        payload["rationale"] = text(self.rationale, self.source["rationale"])
        payload["change_description"] = text(
            self.change_description, self.source["change_description"])
        try:
            preview = self.service.preview_document(
                payload, revision=self.revision,
                purpose=("upgrade" if self.upgrade_source
                         else "clone" if self.clone_source else "new"),
                source_id=self.upgrade_source["id"] if self.upgrade_source else None,
                base=self.clone_base_input.text() if self.clone_base_input else None,
            )
            _candidate, issues = self.service.input_issues(payload, raw=True, activation=True,
                                                          stored=self.revision)
        except OPERATION_ERRORS as exc:
            error(self, exc)
            return
        issues = list(dict.fromkeys([*preview["issues"], *issues]))
        if issues:
            PlanProblemDialog(issues, self.focus_issue, self).exec()
        else:
            QMessageBox.information(self, "输入检查", "输入可形成完整处方。请保存后预览并启用；"
                                    "启用时还会检查动作可用状态和最新版本。")


class PlanProblemDialog(QDialog):
    def __init__(self, issues, focus=None, parent=None, *, summary=None, title="待完善内容"):
        super().__init__(parent)
        self.setWindowTitle(title)
        fit_dialog(self)
        layout = QVBoxLayout(self)
        explanation = QLabel(summary or (
            "点击问题可定位编辑字段；修改后请重新检查。" if focus
            else "请按以下位置和原因处理；可复制问题清单。"))
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        rows = CardList()
        rows.setWordWrap(True)
        for index, issue in enumerate(issues, 1):
            item = QListWidgetItem(f"{index}. {issue_text(issue)}")
            item.setData(Qt.ItemDataRole.UserRole, issue)
            rows.addItem(item)
        if focus:
            def locate(item):
                self.accept()
                focus(item.data(Qt.ItemDataRole.UserRole))
            rows.itemClicked.connect(locate)
        layout.addWidget(rows, 1)
        copy = QPushButton("复制问题清单")
        copy.clicked.connect(lambda: self.clipboard_text(issues))
        layout.addWidget(copy)
        close = QPushButton("关闭")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    @staticmethod
    def clipboard_text(issues):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText("\n\n".join(issue_text(issue) for issue in issues))


_SKIP_FIELDS = {"_input", "item_id", "group_id", "sha256", "key", "revision_id", "session_id",
                "content_id", "content", "provenance", "source_id", "dose_scope",
                "side_order_recorded", "set_rest_recorded", "exercise", "classification",
                "kind", "order"}


def render_fields(value, indent=0, field=None):
    prefix = "  " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if key in _SKIP_FIELDS:
                continue
            if isinstance(item, (dict, list, tuple)):
                lines.append(prefix + T.get(key, key) + "：")
                lines.append(render_fields(item, indent + 1, key))
            else:
                lines.append(prefix + T.get(key, key) + "：" + render_fields(item, field=key))
        return "\n".join(lines)
    if isinstance(value, (list, tuple)):
        return "\n".join(
            prefix + f"{index}. " + render_fields(item, indent + 1, field)
            for index, item in enumerate(value, 1)
        )
    if value is None:
        return T["unknown"]
    if isinstance(value, bool):
        return T["yes"] if value else T["no"]
    mapping = {
        "unit": DOSE_UNIT_LABELS, "phase": PLAN_PHASE_LABELS,
        "starting_position_class": POSITION_LABELS, "variant_role": VARIANT_LABELS,
        "kind": T, "first_side": T, "side_sequence": T,
        "execution_mode": EXECUTION_MODE_LABELS, "alternating_start": ALTERNATING_START_LABELS,
        "source": EXERCISE_SOURCE_LABELS,
    }.get(field, {})
    return str(mapping.get(value, value))


def render_changes(changes):
    return "\n\n".join(
        f"{T.get(change['path'], change['path'])}\n"
        f"{T['before']}：\n{render_fields(change['before'], field=change['path'])}\n"
        f"{T['after']}：\n{render_fields(change['after'], field=change['path'])}"
        for change in changes
    )


class DraftSaveConfirmation(QDialog):
    """Show actionable issues first and keep save/cancel outside the scroll area."""

    def __init__(self, title, summary, changes, parent=None, *, issues=()):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.changes = changes
        self.issues = tuple(issues)
        self._details_loaded = False
        self.layout_body = QVBoxLayout(self)
        summary_label = QLabel(summary)
        summary_label.setTextFormat(Qt.TextFormat.PlainText)
        summary_label.setWordWrap(True)
        self.layout_body.addWidget(summary_label)
        self.toggle = QPushButton("查看待完善内容" if self.issues else "查看变更详情")
        self.toggle.setCheckable(True)
        self.toggle.setVisible(bool(self.issues or changes))
        self.toggle.setAutoDefault(False)
        self.toggle.toggled.connect(self._toggle_details)
        self.layout_body.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignLeft)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumSize(0, 0)
        self.details.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.details.hide()
        self.layout_body.addWidget(self.details, 1)
        self.layout_body.addStretch(1)
        self.buttons = dialog_buttons(self, self.accept)
        save = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        save.setText("保存草稿")
        save.setAutoDefault(False)
        save.setDefault(False)
        cancel = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel.setDefault(True)
        cancel.setFocus()
        self.layout_body.addWidget(self.buttons)
        bind_units(self.layout_body, "setContentsMargins", 1, 1, 1, 1)
        initial_size(self, 44, 12)
        if self.issues:
            self.toggle.setChecked(True)

    def _toggle_details(self, expanded):
        if expanded and not self._details_loaded:
            self.details.setPlainText(
                "\n\n".join(f"{index}. {issue_text(issue)}"
                            for index, issue in enumerate(self.issues, 1))
                if self.issues else render_changes(self.changes)
            )
            self._details_loaded = True
        self.details.setVisible(expanded)
        subject = "待完善内容" if self.issues else "变更详情"
        self.toggle.setText(("收起" if expanded else "查看") + subject)
        self.layout_body.setStretch(3, 0 if expanded else 1)
        initial_size(self, 44, 32 if expanded else 12)


def render_plan(plan, adjustment=None, plan_code=None):
    lines = [plan["name"], plan["purpose"]]
    if plan_code:
        lines.insert(0, plan_code)
    if adjustment:
        lines.append(f"{T['rationale']}：{adjustment}")
    for day in [continuous_plan_day(plan)]:
        for item in day["items"]:
            lines.append(f"{item['order']}. {item.get('name', item.get('exercise_name'))}")
            lines.append(render_fields(item))
            for action in item.get("members", [item]):
                if execution_mode(action) == "alternating":
                    lines.extend(f"{action['exercise_name']} · 第 {dose['order']} 组："
                                 + alternating_explanation(action, dose) for dose in action["sets"])
            if item["kind"] == "group":
                lines.append(T["expanded"])
                member_names = {member["item_id"]: member["exercise_name"]
                                for member in item.get("members", [])}
                member_modes = {member["item_id"]: execution_mode(member)
                                for member in item.get("members", [])}
                occurrences = list(islice(group_from_item(item).occurrences(), 301))
                for occurrence in occurrences[:300]:
                    side_label = ("左右交替" if member_modes[occurrence.member_id] == "alternating"
                                  else T.get(occurrence.side, T["none"]))
                    rest = occurrence.rest_after_seconds
                    rest_text = f"{rest:g}" if rest is not None else T["unknown"]
                    lines.append(
                        f"{T['rounds']} {occurrence.round_number} · "
                        f"{member_names.get(occurrence.member_id, T['unknown'])} · "
                        f"{side_label} · "
                        f"{T['rest_seconds'].format(value=rest_text)}"
                    )
                if len(occurrences) > 300:
                    lines.append(T["preview_truncated"])
    return "\n".join(lines)


class GroupPlanActivation(QDialog):
    def __init__(self, service, revision_id, parent=None):
        super().__init__(parent)
        self.service, self.revision_id = service, revision_id
        self.preview = service.preview(revision_id)
        self.setWindowTitle(T["preview"])
        initial_size(self, 56.25, 43.75)
        layout = QVBoxLayout(self)
        view = QPlainTextEdit()
        view.setReadOnly(True)
        view.setPlainText(
            render_plan(
                self.preview["revision"]["payload"]["plan"],
                self.preview["revision"]["rationale"],
                self.preview["revision"]["plan_code"],
            )
            + "\n"
            + T["diff"]
            + "\n"
            + render_changes(self.preview["changes"])
        )
        layout.addWidget(view, 1)
        self.notice = QLabel(T["unreviewed"] + "：" + "、".join(self.preview["unreviewed"]))
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        self.confirm = QCheckBox(T["confirm"])
        layout.addWidget(self.confirm)
        self.buttons = dialog_buttons(self, self.activate)
        layout.addWidget(self.buttons)

    def activate(self):
        try:
            self.service.activate(
                self.revision_id,
                expected_preview=self.preview["token"],
                user_confirmed=self.confirm.isChecked(),
            )
        except OPERATION_ERRORS as exc:
            error(self, exc)
            return
        self.accept()


class GroupPlanPage(QWidget):
    def __init__(self, service, handoff, parent=None):
        super().__init__(parent)
        self.service, self.handoff, self.dialog = service, handoff, None
        self.presentation = None
        layout = QVBoxLayout(self)
        title = QLabel(T["title"])
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.revisions = CardList()
        self.revisions.setObjectName("revisionNavigator")
        bind_units(self.revisions, "setMinimumWidth", 16.25)
        bind_units(self.revisions, "setMaximumWidth", 20)
        bind_units(self.revisions, "setSpacing", 0.25)
        self.revisions.setWordWrap(True)
        splitter.addWidget(self.revisions)

        self.detail_panel = QWidget()
        detail_layout = QVBoxLayout(self.detail_panel)
        bind_units(detail_layout, "setContentsMargins", 0.875, 0, 0, 0)
        self.revision_title = QLabel()
        self.revision_title.setObjectName("revisionTitle")
        self.revision_title.setWordWrap(True)
        self.revision_title.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        detail_layout.addWidget(self.revision_title)
        self.revision_meta = QLabel()
        detail_layout.addWidget(self.revision_meta)
        self.purpose_label = QLabel()
        self.purpose_label.setWordWrap(True)
        self.purpose_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.purpose_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_layout.addWidget(self.purpose_label)
        self.adjustment_label = QLabel()
        self.adjustment_label.setWordWrap(True)
        self.adjustment_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.adjustment_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_layout.addWidget(self.adjustment_label)
        self.issues_label = QPlainTextEdit()
        self.issues_label.setReadOnly(True)
        self.issues_label.setMinimumSize(0, 0)
        bind_units(self.issues_label, "setMaximumHeight", 12)
        self.issues_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.issues_label.setObjectName("contentIssues")
        detail_layout.addWidget(self.issues_label)
        self.empty_label = QLabel(T["empty_revision_hint"])
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_layout.addWidget(self.empty_label, 1)
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.detail_host = QWidget()
        self.detail_host.setMinimumWidth(0)
        self.detail_rows = QVBoxLayout(self.detail_host)
        bind_units(self.detail_rows, "setContentsMargins", 0, 0.5, 0.5, 0.5)
        bind_units(self.detail_rows, "setSpacing", 0.75)
        self.detail_rows.addStretch(1)
        self.detail_scroll.setWidget(self.detail_host)
        detail_layout.addWidget(self.detail_scroll, 1)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([u(18), u(62.5)])
        layout.addWidget(splitter, 1)
        row = ActionBar()
        self.buttons = {}
        for name in ("new", "edit", "clone", "upgrade", "activate", "import", "new_file",
                     "format", "export", "delete"):
            button = QPushButton({
                "new_file": "新建计划文件", "format": "导入格式说明", "delete": "删除草稿",
            }.get(name, T.get(name, name)).replace("…", ""))
            button.setObjectName(f"planCommand_{name}")
            button.clicked.connect(lambda checked=False, command=name: self.command(command))
            row.addWidget(button)
            self.buttons[name] = button
        layout.addWidget(row)
        self.revisions.currentItemChanged.connect(self.show_revision)
        self.refresh()

    def refresh(self, preferred=None):
        if preferred is None and self.revisions.currentItem() is not None:
            preferred = self.revisions.currentItem().data(Qt.ItemDataRole.UserRole)
        self.revisions.clear()
        selected = None
        for plan in self.service.list_plans():
            for revision in self.service.revisions(plan["id"]):
                item = QListWidgetItem(
                    f"{revision['name'] or '未命名草稿'}\n"
                    f"{revision['plan_code'] or '正式计划编号待确定'} · "
                    + PLAN_STATUS_LABELS[revision["status"]]
                    + (" · 编辑草稿 " + revision["edit_document"]["updated_at"]
                       if revision.get("edit_document") else "")
                )
                if not revision["plan_code"]:
                    item.setToolTip("草稿编号：" + revision["id"])
                item.setData(Qt.ItemDataRole.UserRole, revision["id"])
                self.revisions.addItem(item)
                if revision["id"] == preferred:
                    selected = item
                elif selected is None and revision["status"] == "active":
                    selected = item
        if selected is not None:
            self.revisions.setCurrentItem(selected)
        elif self.revisions.count():
            self.revisions.setCurrentRow(self.revisions.count() - 1)
        else:
            self.show_revision(None)

    def _clear_rows(self):
        while self.detail_rows.count() > 1:
            entry = self.detail_rows.takeAt(0)
            widget = entry.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

    @staticmethod
    def _label(value, *, bold=False):
        label = QLabel(str(value))
        label.setWordWrap(True)
        label.setMinimumWidth(0)
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if bold:
            label.setStyleSheet("font-weight: 600;")
        return label

    def _card(self, title, subtitle=None, *, level=0):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setObjectName("planCard" if level == 0 else "memberCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        box = QVBoxLayout(card)
        bind_units(box, "setContentsMargins", 0.75, 0.625, 0.75, 0.625)
        bind_units(box, "setSpacing", 0.3125)
        box.addWidget(self._label(title, bold=True))
        if subtitle:
            box.addWidget(self._label(subtitle))
        return card, box

    @staticmethod
    def _side_text(side, *, unilateral=True):
        if not unilateral:
            return "不适用"
        if side == "not_applicable":
            return "不适用"
        return {"left": T["left"], "right": T["right"], None: "未记录"}.get(side, "未记录")

    def _add_set_rows(self, layout, action, *, every_round=False, member_order=None):
        for dose in action["sets"]:
            prefix = f"成员 {member_order} · " if member_order is not None else ""
            repeat = "每轮 · " if every_round else ""
            suffix = " · 每侧" if dose["per_side"] else ""
            if not dose["per_side"]:
                suffix = (" · 总次数" if action.get("execution_mode") == "alternating"
                          else " · 整体")
            layout.addWidget(self._label(
                f"{prefix}{repeat}第 {dose['order']} 组  {dose['dose']}{suffix}"
            ))
            if dose.get("counting"):
                layout.addWidget(self._label(dose["counting"]))
            if dose["note"]:
                layout.addWidget(self._label(f"{T['note']}：{dose['note']}"))
            layout.addWidget(self._label(f"本组后休息：{dose['rest']}"))

    def _action_card(self, item):
        card, box = self._card(f"{item['order']}. {item['name']} · {item['phase']}")
        unilateral = item["execution_mode"] == "separate_sides"
        box.addWidget(self._label("执行方式：" + EXECUTION_MODE_LABELS[item["execution_mode"]]))
        box.addWidget(self._label(
            f"先做：{self._side_text(item['first_side'], unilateral=unilateral)} · "
            f"换侧休息：{item['rest_between_sides']}"
        ))
        if item["note"]:
            box.addWidget(self._label(f"{T['note']}：{item['note']}"))
        self._add_set_rows(box, item)
        box.addWidget(self._label(f"动作后休息：{item['rest_after']}"))
        return card

    def _group_card(self, item):
        card, box = self._card(f"{item['order']}. {item['name']} · {item['phase']}")
        box.addWidget(self._label(f"轮数：{item['round_count']} · 侧序：{item['side_sequence']}"))
        unilateral = any(
            member["execution_mode"] == "separate_sides" for member in item["members"]
        )
        box.addWidget(self._label(
            f"先做：{self._side_text(item['first_side'], unilateral=unilateral)} · "
            f"换侧休息：{item['rest_between_sides']} · 轮间休息：{item['rest_between_rounds']}"
        ))
        if item["transition"]:
            box.addWidget(self._label(f"转换：{item['transition']}"))
        if item["note"]:
            box.addWidget(self._label(f"{T['note']}：{item['note']}"))
        for member in item["members"]:
            member_card, member_box = self._card(
                f"成员 {member['order']}. {member['name']}", level=1
            )
            member_box.addWidget(self._label(
                "执行方式：" + EXECUTION_MODE_LABELS[member["execution_mode"]]))
            if member["note"]:
                member_box.addWidget(self._label(f"{T['note']}：{member['note']}"))
            self._add_set_rows(
                member_box, member, every_round=True, member_order=member["order"]
            )
            member_box.addWidget(self._label(f"成员后休息：{member['rest_after']}"))
            box.addWidget(member_card)
        box.addWidget(self._label(f"动作组结束后休息：{item['rest_after']}"))
        return card

    def show_revision(self, item, previous=None):
        if item:
            revision = self.service.get(item.data(Qt.ItemDataRole.UserRole))
            if revision.get("edit_document"):
                self._clear_rows()
                self.revision_title.setText(revision["name"] or "未命名草稿")
                self.revision_meta.setText("草稿编号：" + revision["id"] + "\n"
                    + (revision["plan_code"] or "正式计划编号待确定"))
                self.purpose_label.setText(revision["payload"]["plan"]["purpose"])
                self.adjustment_label.clear()
                doc = revision["edit_document"]
                issues = self.service.preview_document(
                    revision["payload"], revision=revision,
                    base=doc["requested_base_number"])["issues"]
                self.issues_label.setPlainText("草稿 · 待完善\n" + "\n\n".join(
                    issue_text(issue) for issue in issues) if issues else "草稿 · 可预览并启用")
                self.issues_label.show()
                self.empty_label.hide()
                self.detail_scroll.hide()
                self._set_command_state("draft")
                return
            self.presentation = plan_presentation(
                revision, self.service.content_issues(revision["id"])
            )
            self.revision_title.setText(self.presentation["name"])
            self.revision_meta.setText(
                f"{revision['plan_code']} · {self.presentation['status']}"
            )
            self.purpose_label.setText(f"训练目的：{self.presentation['purpose']}")
            self.adjustment_label.setText(
                f"{T['rationale']}：{self.presentation['adjustment']}"
                if self.presentation["adjustment"] else ""
            )
            self.issues_label.setPlainText("\n\n".join(
                issue["name"] + "：" + "、".join(issue["reasons"])
                for issue in self.presentation["issues"]
            ))
            self.issues_label.setVisible(bool(self.presentation["issues"]))
            self.empty_label.hide()
            self.detail_scroll.show()
            self._clear_rows()
            for plan_item in self.presentation["items"]:
                widget = (self._group_card(plan_item) if plan_item["kind"] == "group"
                          else self._action_card(plan_item))
                self.detail_rows.insertWidget(self.detail_rows.count() - 1, widget)
            self._set_command_state(self.presentation["status_key"])
            active = self.service.repository.active(revision["plan_id"])
            self.buttons["upgrade"].setEnabled(
                revision["status"] == "active" and active is not None
                and active["id"] == revision["id"]
            )
        else:
            self.presentation = None
            self.revision_title.clear()
            self.revision_meta.clear()
            self.purpose_label.clear()
            self.adjustment_label.clear()
            self.issues_label.clear()
            self.issues_label.hide()
            self._clear_rows()
            self.detail_scroll.hide()
            self.empty_label.show()
            self._set_command_state(None)

    def _set_command_state(self, status):
        available = status is not None
        self.buttons["edit"].setEnabled(status == "draft")
        self.buttons["clone"].setEnabled(available)
        self.buttons["upgrade"].setEnabled(False)
        self.buttons["activate"].setEnabled(status == "draft")
        self.buttons["export"].setEnabled(available)
        self.buttons["delete"].setEnabled(status == "draft")

    def _new_plan_file(self):
        import json

        from PySide6.QtCore import QIODevice, QSaveFile, QUrl
        from PySide6.QtGui import QDesktopServices

        # Keep the template in memory until the user explicitly chooses a file.
        template = json.dumps(self.handoff.example_payload(), ensure_ascii=False, indent=2)
        content = (template + "\n").encode("utf-8")
        dialog = QDialog(self)
        dialog.setWindowTitle("新建计划文件")
        fit_dialog(dialog)
        layout = QVBoxLayout(dialog)
        instructions = QLabel(
            "这是只读模板，尚未创建文件。请先点击“另存为计划文件”，保存到你自己的文件夹，"
            "再用文本编辑器修改名称、动作和训练安排。编辑完成后，回到这里点击“导入计划文件”。\n"
            "示例剂量仅供格式参考，不是训练建议；打开或另存模板都不会创建应用内计划。"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        preview = QPlainTextEdit(template)
        preview.setReadOnly(True)
        layout.addWidget(preview, 1)
        saved_path = QLabel()
        saved_path.setWordWrap(True)
        saved_path.setTextFormat(Qt.TextFormat.PlainText)
        saved_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(saved_path)
        buttons = QHBoxLayout()
        save_as = QPushButton("另存为计划文件")

        def save_template():
            target, _ = QFileDialog.getSaveFileName(
                dialog, "另存为计划文件", "新训练计划.json", T["json_filter"])
            if not target:
                return
            output = QSaveFile(target)
            if not output.open(QIODevice.OpenModeFlag.WriteOnly):
                QMessageBox.warning(dialog, "无法另存文件", "无法写入所选位置，请换一个文件夹。")
                return
            if output.write(content) != len(content):
                output.cancelWriting()
                QMessageBox.warning(dialog, "无法另存文件", "文件写入失败，请检查可用空间后重试。")
                return
            if not output.commit():
                QMessageBox.warning(dialog, "无法另存文件", "未能完成保存，请检查文件权限后重试。")
                return
            saved_path.setText("已另存：" + target + "\n请用文本编辑器修改此文件，保存后再导入。")
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(target)):
                QMessageBox.information(
                    dialog, "文件已另存", "无法自动打开，请用文本编辑器打开以下文件：\n" + target)

        save_as.clicked.connect(save_template)
        buttons.addWidget(save_as)
        buttons.addStretch()
        close = QPushButton("关闭")
        close.clicked.connect(dialog.accept)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def command(self, command):
        selected = self.revisions.currentItem()
        identifier = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        try:
            if command == "new":
                self.dialog = GroupPlanEditor(self.service, parent=self)
                self.dialog.exec()
                identifier = self.dialog.saved_id
            elif command == "new_file":
                self._new_plan_file()
                return
            elif command == "import":
                path, _ = QFileDialog.getOpenFileName(self, T["import"], "", T["json_filter"])
                if path:
                    preview = self.handoff.preview_file(Path(path))
                    warnings = "\n".join(name + "：" + "；".join(
                        user_message("Content is not eligible: " + reason) for reason in reasons)
                        for name, reasons in preview.warnings)
                    summary = (("启用前须处理：\n" + warnings + "\n\n") if warnings else "")
                    if preview.conversion_note:
                        summary += preview.conversion_note + "\n\n"
                    summary += render_plan(preview.payload["plan"])
                    summary += "\n\n变更明细：\n" + render_changes(preview.changes)
                    dialog = DraftSaveConfirmation(
                        "导入预览", "完整文件已校验；确认后仅保存为草稿。", [], self)
                    dialog.details.setPlainText(summary)
                    dialog.details.show()
                    initial_size(dialog, 50, 36)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        identifier = self.handoff.import_preview(preview)
            elif command == "format":
                dialog = QDialog(self)
                dialog.setWindowTitle("计划文件格式说明")
                fit_dialog(dialog)
                layout = QVBoxLayout(dialog)
                detail = QPlainTextEdit(self.handoff.format_help())
                detail.setReadOnly(True)
                layout.addWidget(detail, 1)
                for title, content, filename in (
                    ("保存格式说明", self.handoff.format_help(), "计划文件格式说明.txt"),
                    ("保存 JSON 示例", None, "计划格式示例.json"),
                ):
                    button = QPushButton(title)
                    def save_help(checked=False, content=content, filename=filename):
                        import json
                        try:
                            data = content if content is not None else json.dumps(
                                self.handoff.example_payload(), ensure_ascii=False, indent=2)
                            target, _ = QFileDialog.getSaveFileName(
                                dialog, "保存格式参考", filename)
                            if target:
                                Path(target).write_text(data, encoding="utf-8")
                        except OPERATION_ERRORS as exc:
                            error(dialog, exc)
                    button.clicked.connect(save_help)
                    layout.addWidget(button)
                close = QPushButton("关闭")
                close.clicked.connect(dialog.accept)
                layout.addWidget(close)
                dialog.exec()
            elif identifier is None:
                return
            elif command == "edit":
                revision = self.service.get(identifier)
                if revision["status"] != "draft":
                    raise ValueError("Only draft revisions can be edited.")
                self.dialog = GroupPlanEditor(self.service, revision, self)
                self.dialog.exec()
                identifier = self.dialog.saved_id or identifier
            elif command == "clone":
                source = self.service.get(identifier)
                name, accepted = QInputDialog.getText(
                    self, T["clone"], T["clone_name_prompt"]
                )
                if not accepted:
                    return
                base_number, accepted = QInputDialog.getText(
                    self, T["clone"], "复制计划编号（001–999；留空自动分配）"
                )
                if not accepted:
                    return
                description, accepted = QInputDialog.getText(
                    self, T["clone"], T["change_description"]
                )
                if not accepted:
                    return
                self.dialog = GroupPlanEditor(
                    self.service,
                    parent=self,
                    clone_source=source,
                    clone_base_number=base_number,
                    clone_name=name,
                    change_description=description,
                )
                self.dialog.exec()
                identifier = self.dialog.saved_id
            elif command == "upgrade":
                source = self.service.get(identifier)
                existing = self.service.upgrade_draft(identifier)
                if existing is not None:
                    self.dialog = GroupPlanEditor(self.service, existing, self)
                else:
                    description, accepted = QInputDialog.getText(
                        self, T["upgrade"], T["change_description"]
                    )
                    if not accepted:
                        return
                    self.dialog = GroupPlanEditor(
                        self.service,
                        parent=self,
                        upgrade_source=source,
                        change_description=description,
                    )
                self.dialog.exec()
                identifier = self.dialog.saved_id
            elif command == "activate":
                try:
                    self.dialog = GroupPlanActivation(self.service, identifier, self)
                    self.dialog.exec()
                    if isinstance(identifier, str):
                        identifier = None
                except PlanIssues as exc:
                    self.dialog = GroupPlanEditor(self.service, self.service.get(identifier), self)
                    self.dialog.show()
                    PlanProblemDialog(exc.issues, self.dialog.focus_issue, self.dialog).exec()
                    self.dialog.exec()
                    identifier = self.dialog.saved_id or identifier
            elif command == "export":
                path = self.handoff.export(identifier)
                QMessageBox.information(self, T["export"], T["exported"] + str(path))
            elif command == "delete":
                revision = self.service.get(identifier)
                if confirm(self, "删除草稿", "确定删除此草稿？已启用版本和训练记录会保留。"):
                    self.service.delete_draft(identifier, revision["edit_token"])
                    identifier = None
        except OPERATION_ERRORS as exc:
            error(self, exc, issue_summary={
                "import": "导入失败，尚未保存计划。请按问题清单修正文件后重新选择。",
                "export": "尚未导出文件。请打开草稿，按以下问题完善并保存后再导出。",
            }.get(command))
            return
        self.refresh(identifier)
