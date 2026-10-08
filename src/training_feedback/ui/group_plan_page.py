"""Native editor for versioned single/group plans; all saves use the new-model service."""

from __future__ import annotations

from copy import deepcopy
from itertools import islice
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFontMetrics
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
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..domain.group_plans import (
    PlanDocument,
    action_from_choice,
    blank_group,
    continuous_plan_day,
    diff_plans,
    group_from_item,
    migration_validation_projection,
    normalize_inapplicable_rest,
    prescription_rest_applicability,
    validate_action,
)
from .exercise_reading import PlanGuidance
from .labels import (
    DOSE_UNIT_LABELS,
    EXERCISE_SOURCE_LABELS,
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


def error(parent, exc):
    QMessageBox.warning(parent, T["error"], user_message(str(exc)))


def dialog_buttons(dialog, save):
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    localize_dialog_buttons(buttons)
    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    return buttons


def number(edit, label, *, optional=False):
    value = edit.text().strip()
    if not value:
        if optional:
            return None
        raise ValueError(f"请填写{label}；空白表示未知，若不休息请明确填写 0。")
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{label}必须填写数字，当前输入为「{edit.text()}」。") from None


class ActionPrescriptionDialog(QDialog):
    def __init__(self, choices, action=None, *, member=False, parent=None, service=None,
                 embedded=False):
        super().__init__(parent)
        self.member, self.source, self.value = member, deepcopy(action), None
        self.service = service
        self.setWindowTitle(T["action"])
        fit_dialog(self)
        body = QWidget()
        fields = QVBoxLayout(body)
        form = AdaptiveFields()
        self.exercise = _ScrollCombo()
        self.exercise.setEditable(True)
        self.exercise.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.exercise.setMinimumContentsLength(18)
        self.exercise.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        available = list(choices)
        if action and not any(
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
        self.sets = RelativeTable([5, 4, 3, 6, 4, 4, 4, 2])
        self.sets.setHorizontalHeaderLabels(
            [T[key] for key in ("value", "unit", "per_side", "set_rest", "note")]
            + ["组次", "操作", "#"]
        )
        self.sets.horizontalHeader().setSectionsMovable(False)
        self.sets.horizontalHeader().moveSection(5, 0)
        self.sets.horizontalHeader().moveSection(7, 0)
        self.exercise.currentIndexChanged.connect(self.refresh_rest_fields)
        for dose in action["sets"] if action else []:
            self.add_set(dose)
        self.refresh_rest_fields()
        fields.addWidget(self.sets)
        controls = AdaptiveFields(minimum=8)
        add = QPushButton(T["add_set"])
        add.clicked.connect(lambda: self.add_set())
        remove = QPushButton(T["remove_set"])
        remove.clicked.connect(self.remove_set)
        fill = QPushButton(T["fill_equal_sets"])
        fill.clicked.connect(self.fill_equal_sets)
        controls.addRow("", add)
        controls.addRow("", remove)
        controls.addRow("", fill)
        fields.addWidget(controls)
        fields.addStretch()
        scroll = LocalScrollArea()
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "panes"):
            self.panes.reflow()

    def show_guidance(self):
        choice = self.exercise.currentData()
        if choice is None:
            self.reading.set_content(None, None, lambda index: b"")
            return
        try:
            entry = self.service.action_content(choice)
            self.reading.set_content(
                entry["reference"], entry["content"]["guidance"],
                lambda index, action=deepcopy(choice): self.service.action_image(action, index),
            )
        except (ValueError, OSError) as exc:
            self.reading.set_content(None, None, lambda index: b"")
            self.reading.setToolTip(user_message(str(exc)))

    def add_set(self, dose=None):
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
        check = QCheckBox()
        check.setChecked(dose["per_side"])
        check.stateChanged.connect(self.refresh_rest_fields)
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
        self.refresh_rest_fields()

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
        choice = self.exercise.currentData()
        aggregate = bool(self.source and "provenance" in self.source and choice
                         and choice["exercise"] == self.source["exercise"])
        applicability = prescription_rest_applicability(
            [{"per_side": self.sets.cellWidget(row, 2).isChecked()}
             for row in range(self.sets.rowCount())],
            aggregate=aggregate,
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
        per_side = self.sets.cellWidget(source, 2).isChecked()
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
            self.sets.cellWidget(row, 2).setChecked(per_side)
            target_rest = self.sets.item(row, 3)
            if rest is not None and target_rest.flags() & Qt.ItemFlag.ItemIsEditable:
                target_rest.setText(rest)
            self.sets.item(row, 4).setText(note)
        self.refresh_rest_fields()

    def save(self):
        try:
            choice = self.exercise.currentData()
            if choice is None:
                raise ValueError("Select an exercise content revision.")
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
                        "per_side": self.sets.cellWidget(row, 2).isChecked(),
                        "rest_after_set_seconds": (
                            number(self.sets.item(row, 3), f"第 {row + 1} 组的组间休息秒",
                                   optional="provenance" in action)
                            if self.sets.item(row, 3).flags() & Qt.ItemFlag.ItemIsEditable else None
                        ),
                        "note": self.sets.item(row, 4).text(),
                    }
                )
            action["sets"] = doses
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
            validate_action(migration_validation_projection(action)
                            if "provenance" in action else action)
            self.value = action
        except (ValueError, TypeError) as exc:
            error(self, exc)
            return
        self.accept()


class GroupPrescriptionDialog(QDialog):
    def __init__(self, choices, group=None, parent=None, *, service=None):
        super().__init__(parent)
        self.choices = choices
        self.service = service
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
        body = QWidget()
        layout = QVBoxLayout(body)
        form = AdaptiveFields()
        self.name = QLineEdit(self.group["name"])
        self.phase = combo(PLAN_PHASE_LABELS, self.group["phase"])
        self.rounds = _ScrollSpin()
        self.rounds.setRange(1, 1000000)
        self.rounds.setValue(self.group["round_count"])
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
            ("rest_after_group_seconds", "exit_rest"),
        ):
            self.fields[key] = QLineEdit(
                "" if self.group[key] is None else str(self.group[key])
            )
            form.addRow(T[label], self.fields[key])
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
        self.members = QListWidget()
        bind_units(self.members, "setMinimumHeight", 6)
        self.members.setWordWrap(True)
        self.members.setTextElideMode(Qt.TextElideMode.ElideNone)
        layout.addWidget(self.members, 1)
        controls = AdaptiveFields(minimum=8)
        for name, function in (
            ("add_member", self.add_member),
            ("edit_item", self.edit_member),
            ("up", lambda: self.move(-1)),
            ("down", lambda: self.move(1)),
            ("remove", self.remove),
        ):
            button = QPushButton(T[name])
            button.clicked.connect(function)
            controls.addRow("", button)
        layout.addWidget(controls)
        scroll = LocalScrollArea()
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        self.buttons = dialog_buttons(self, self.save)
        outer.addWidget(self.buttons)
        self.refresh()

    def refresh(self):
        self.members.clear()
        for member in self.group["members"]:
            self.members.addItem(f"{member['order']}. {member['exercise_name']}")

    def add_member(self):
        dialog = ActionPrescriptionDialog(self.choices, member=True, parent=self,
                                          service=self.service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.group["members"].append(dialog.value)
            PlanDocument.reorder(self.group["members"])
            self.refresh()

    def edit_member(self):
        index = self.members.currentRow()
        if index < 0:
            return
        dialog = ActionPrescriptionDialog(
            self.choices, self.group["members"][index], member=True, parent=self,
            service=self.service,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.group["members"][index] = dialog.value
            self.refresh()

    def move(self, offset):
        if self.members.currentRow() >= 0:
            PlanDocument({"days": []}).move(
                self.group["members"], self.members.currentRow(), offset
            )
            self.refresh()

    def remove(self):
        index = self.members.currentRow()
        if index >= 0:
            if len(self.group["members"]) <= 2:
                error(
                    self,
                    ValueError("Keep two members or remove/dissolve the group in the plan tree."),
                )
                return
            del self.group["members"][index]
            PlanDocument.reorder(self.group["members"])
            self.refresh()

    def save(self):
        try:
            group = {
                **self.group,
                "name": self.name.text(),
                "phase": self.phase.currentData(),
                "round_count": self.rounds.value(),
                "side_sequence": self.sequence.currentData(),
                "first_side": self.side.currentData(),
                "transition": text(self.transition, self.group["transition"]),
                "note": text(self.note, self.group["note"]),
            }
            group.update({key: number(edit, T[key]) for key, edit in self.fields.items()})
            if not group["name"].strip():
                raise ValueError("Group name cannot be empty.")
            group_from_item(group)
            self.value = group
        except ValueError as exc:
            error(self, exc)
            return
        self.accept()


class MultiExerciseSelectionDialog(QDialog):
    """Searchable multi-pick that inserts unfinished actions into the plan tree."""

    def __init__(self, choices, parent=None):
        super().__init__(parent)
        self.value = None
        self.setWindowTitle(T["add_action"])
        self.search = QLineEdit()
        self.search.setPlaceholderText(T["search_exercises"])
        self.exercise_list = QListWidget()
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
            QMessageBox.information(self, T["add_action"], T["choose_multiple_exercises"])
            self.value = None
            return
        self.accept()


class GroupPlanEditor(QDialog):
    def __init__(self, service, revision=None, parent=None, *, upgrade_source=None,
                 clone_source=None, clone_base_number=None, clone_name=None,
                 change_description=None):
        super().__init__(parent)
        self.service, self.revision, self.saved_id = service, revision, None
        self.clone_source = clone_source
        self.clone_base_number = clone_base_number
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
                "schema_version": 4,
                "intent": "new",
                "rationale": "",
                "change_description": "",
                "plan": {"name": "", "purpose": "", "days": []},
            }
        )
        self.source.setdefault("intent", "new")
        self.source.setdefault("change_description", "")
        if self.upgrade_source:
            self.source["intent"] = "upgrade"
            self.source["target_base_number"] = self.upgrade_source["base_number"]
        if self.clone_name is not None:
            self.source["plan"]["name"] = self.clone_name
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
        self.tree = PlanActionTree()
        self.tree.setObjectName("planActions")
        self.tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree.setWordWrap(True)
        self.tree.setHeaderLabels([T["items"]])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setStretchLastSection(False)
        self.tree.currentItemChanged.connect(self._show_selected_detail)
        self.tree.reorder_requested.connect(self._reorder_dragged)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._action_menu)
        self.detail_panel = QWidget()
        detail_layout = QVBoxLayout(self.detail_panel)
        self.detail_content_layout = detail_layout
        self.detail_summary = QWidget()
        summary_layout = QVBoxLayout(self.detail_summary)
        self.detail_title = QLabel(T["select_detail"])
        self.detail_title.setObjectName("actionTitle")
        self.detail_title.setWordWrap(True)
        summary_layout.addWidget(self.detail_title)
        self.detail_fields = ResizableTextEdit()
        self.detail_fields.setReadOnly(True)
        summary_layout.addWidget(self.detail_fields)
        self.detail_reading = PlanGuidance()
        self.detail_sets = RelativeTable([2, 4, 5, 4, 3, 6])
        self.detail_sets.setHorizontalHeaderLabels(
            [T["member"], T["set_order"], T["value"], T["unit"], T["per_side"], T["set_rest"]]
        )
        self.detail_sets.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        summary_layout.addWidget(self.detail_sets)
        summary_layout.addStretch()
        self.summary_scroll = LocalScrollArea()
        self.summary_scroll.setWidget(self.detail_summary)
        self.detail_sets.height_budget = lambda: self.summary_scroll.viewport().height()
        detail_layout.addWidget(self.summary_scroll, 1)
        bind_units(summary_layout, "setContentsMargins", 1.5, 1.5, 1.5, 1.5)
        bind_units(detail_layout, "setContentsMargins", 0, 0, 0, 0)
        self.inline_editor = None
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.tree, 1)
        add = QPushButton("+ 添加动作")
        add.clicked.connect(lambda: self.command("add_action"))
        left_layout.addWidget(add)
        self.panes = PlanPanes(left, self.detail_panel, self.detail_reading, self.tree, self)
        layout.addWidget(self.panes, 1)
        commands = QHBoxLayout()
        edit = QPushButton(T["edit_item"])
        edit.clicked.connect(lambda: self.command("edit_item"))
        commands.addWidget(edit)
        # Keep secondary commands available without a row of overflowing buttons.
        more = QToolButton()
        more.setText("更多操作 ▾")
        more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(more)
        for name in ("add_action", "add_group", "remove", "up", "down", "move_member"):
            menu.addAction(T[name], lambda checked=False, command=name: self.command(command))
        more.setMenu(menu)
        commands.addWidget(more)
        commands.addStretch()
        self.buttons = dialog_buttons(self, self.save)
        commands.addWidget(self.buttons)
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
        self.detail_sets.update_metrics()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "panes"):
            self._update_layout()

    def refresh(self, selection=None):
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
        self.panes.rebuild_capsules()

    def _reorder_dragged(self, before, after):
        if self.inline_editor is not None:
            return
        d, i, m = before
        target = after[1] if m is None else after[2]
        rows = (self.document.plan["days"][d]["items"] if m is None
                else self.document.plan["days"][d]["items"][i]["members"])
        index = i if m is None else m
        step = 1 if target > index else -1
        while index != target:
            self.document.move(rows, index, step)
            index += step
        self.refresh((d, target, None) if m is None else (d, i, target))

    def _action_menu(self, position):
        if self.inline_editor is not None:
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
        if hasattr(self, "panes"):
            self.panes.rebuild_capsules()
        self.detail_sets.setRowCount(0)
        self.detail_reading.set_content(None, None, lambda index: b"")
        if item is None:
            self.detail_title.setText(T["select_detail"])
            self.detail_fields.clear()
            return
        d, i, m = item.data(0, Qt.ItemDataRole.UserRole)
        plan_item = self.document.plan["days"][d]["items"][i]
        selected = plan_item["members"][m] if m is not None else plan_item
        title = selected.get("name", selected.get("exercise_name", T["group"]))
        self.detail_title.setText(title)
        self.detail_fields.setPlainText(render_fields({
            key: value for key, value in selected.items()
            if key not in ("sets", "members", "name", "exercise_name")
        }))
        if "exercise" in selected:
            try:
                entry = self.service.action_content(selected)
                self.detail_reading.set_content(
                    entry["reference"], entry["content"]["guidance"],
                    lambda index, action=deepcopy(selected): self.service.action_image(
                        action, index
                    ),
                )
            except (ValueError, OSError) as exc:
                self.detail_fields.appendPlainText("指导暂时无法读取：" + user_message(str(exc)))
        members = plan_item.get("members", []) if m is None else []
        if m is not None or plan_item["kind"] == "action":
            members = [{"order": "", **selected}]
        for member in members:
            doses = member.get("sets", [])
            rest_applicability = prescription_rest_applicability(
                doses, aggregate="provenance" in member
            )["set_rests"]
            for dose_index, dose in enumerate(doses):
                row = self.detail_sets.rowCount()
                self.detail_sets.insertRow(row)
                values = (
                    str(member.get("order", "")),
                    str(dose["order"]),
                    "" if dose["value"] is None else str(dose["value"]),
                    DOSE_UNIT_LABELS[dose["unit"]],
                    T["yes"] if dose["per_side"] else T["no"],
                    (T["none"] if not rest_applicability[dose_index] else
                     T["unknown"] if dose["rest_after_set_seconds"] is None
                     else str(dose["rest_after_set_seconds"])),
                )
                for column, value in enumerate(values):
                    self.detail_sets.setItem(row, column, QTableWidgetItem(value))

    def command(self, command):
        if self.inline_editor is not None:
            return
        selected = self.tree.currentItem()
        d, i, m = selected.data(0, Qt.ItemDataRole.UserRole) if selected else (0, None, None)
        selection = (d, i, m) if d is not None else None
        try:
            if command in ("add_action", "add_group", "edit_item"):
                self.edit_item(command, d, None if command != "edit_item" else i,
                               None if command != "edit_item" else m)
            elif command in ("up", "down"):
                if i is None:
                    return
                rows = (self.document.plan["days"][d]["items"] if m is None
                        else self.document.plan["days"][d]["items"][i]["members"])
                self.document.move(
                    rows, i if m is None else m, -1 if command == "up" else 1
                )
            elif command == "remove" and i is not None:
                self.remove(d, i, m)
            elif command == "move_member":
                self.transfer(command, d, i, m)
        except ValueError as exc:
            error(self, exc)
            return
        self.refresh(selection)

    def edit_item(self, command, d, i, m):
        choices = self.service.exercise_choices()
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

    def _show_inline_editor(self, dialog, d, i, m):
        self.tree.setEnabled(False)
        self.panes.rebuild_capsules()
        self.summary_scroll.hide()
        self.inline_editor = dialog
        dialog.setParent(self.detail_panel)
        dialog.setWindowFlags(Qt.WindowType.Widget)
        dialog.setMinimumSize(0, 0)
        self.detail_content_layout.addWidget(dialog, 1)
        dialog.accepted.connect(lambda: self._inline_saved(dialog, d, i, m))
        dialog.rejected.connect(self._inline_cancelled)
        if isinstance(dialog, ActionPrescriptionDialog):
            dialog.reading = self.detail_reading
            dialog.exercise.currentIndexChanged.connect(dialog.show_guidance)
            dialog.show_guidance()
        dialog.show()

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

    def _close_inline_editor(self):
        dialog, self.inline_editor = self.inline_editor, None
        if dialog is not None:
            self.detail_content_layout.removeWidget(dialog)
            dialog.hide()
            dialog.deleteLater()
        self.tree.setEnabled(True)
        self.summary_scroll.show()
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
        if self.inline_editor is not None:
            QMessageBox.information(self, T["error"], "请先保存或取消右侧正在编辑的训练安排。")
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
            if self.upgrade_source:
                preview = self.service.preview_upgrade(self.upgrade_source["id"], payload)
                details = T["upgrade_preview"].format(code=preview["plan_code"])
                if preview["changes"]:
                    details += "\n\n" + render_changes(preview["changes"])
                answer = QMessageBox.question(
                    self,
                    T["upgrade"],
                    details,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
                if self.revision:
                    self.service.save(
                        self.revision["id"], payload,
                        expected_token=self.revision["edit_token"],
                    )
                    self.saved_id = self.revision["id"]
                else:
                    self.saved_id = self.service.create_upgrade(
                        self.upgrade_source["id"], payload
                    )
            else:
                self.service.validate(
                    payload, stored=self.revision if self.revision else None
                )
                if self.clone_source:
                    base_number = self.clone_base_number
                    before = self.clone_source["payload"]["plan"]
                elif self.revision:
                    base_number = self.revision["base_number"]
                    before = self.revision["payload"]["plan"]
                else:
                    used = {plan["base_number"] for plan in self.service.list_plans()}
                    base_number = next(
                        (number for number in range(1, 1000) if number not in used), None
                    )
                    before = None
                if base_number is None:
                    raise ValueError("All plan base numbers 001–999 are in use.")
                code = (
                    self.revision["plan_code"] if self.revision
                    else f"plan-{base_number:03d}.01.00"
                )
                details = T["draft_preview"].format(code=code)
                changes = diff_plans(before, payload["plan"])
                if changes:
                    details += "\n\n" + render_changes(changes)
                answer = QMessageBox.question(
                    self,
                    T["save"],
                    details,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
                if self.clone_source:
                    self.saved_id = self.service.clone(
                        self.clone_source["id"],
                        base_number=base_number,
                        name=payload["plan"]["name"],
                        change_description=payload["change_description"],
                        payload=payload,
                    )
                elif self.revision:
                    self.service.save(
                        self.revision["id"], payload,
                        expected_token=self.revision["edit_token"],
                    )
                    self.saved_id = self.revision["id"]
                else:
                    self.saved_id = self.service.create(
                        payload,
                        base_number=base_number,
                        change_description=payload["change_description"],
                    )
        except (ValueError, OSError) as exc:
            error(self, exc)
            return
        self.accept()


_SKIP_FIELDS = {"item_id", "group_id", "sha256", "key", "revision_id", "session_id",
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
            if item["kind"] == "group":
                lines.append(T["expanded"])
                member_names = {member["item_id"]: member["exercise_name"]
                                for member in item.get("members", [])}
                occurrences = list(islice(group_from_item(item).occurrences(), 301))
                for occurrence in occurrences[:300]:
                    rest = occurrence.rest_after_seconds
                    rest_text = f"{rest:g}" if rest is not None else T["unknown"]
                    lines.append(
                        f"{T['rounds']} {occurrence.round_number} · "
                        f"{member_names.get(occurrence.member_id, T['unknown'])} · "
                        f"{T.get(occurrence.side, T['none'])} · "
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
        except ValueError as exc:
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
        self.revisions = QListWidget()
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
        self.issues_label = QLabel()
        self.issues_label.setWordWrap(True)
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
        row = QHBoxLayout()
        self.buttons = {}
        for name in ("new", "edit", "clone", "upgrade", "activate", "import", "export"):
            button = QPushButton(T[name].replace("…", ""))
            button.setObjectName(f"planCommand_{name}")
            button.clicked.connect(lambda checked=False, command=name: self.command(command))
            row.addWidget(button)
            self.buttons[name] = button
        layout.addLayout(row)
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
                    f"{revision['name']}\n{revision['plan_code']} · "
                    + PLAN_STATUS_LABELS[revision["status"]]
                )
                metrics = QFontMetrics(self.revisions.font())
                height = metrics.boundingRect(
                    0,
                    0,
                    max(u(1), self.revisions.width() - u(1.875)),
                    u(125),
                    Qt.TextFlag.TextWordWrap,
                    item.text(),
                ).height()
                item.setSizeHint(QSize(self.revisions.width() - u(.75), height + u(.875)))
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
                suffix = " · 整体"
            layout.addWidget(self._label(
                f"{prefix}{repeat}第 {dose['order']} 组  {dose['dose']}{suffix}"
            ))
            if dose["note"]:
                layout.addWidget(self._label(f"{T['note']}：{dose['note']}"))
            layout.addWidget(self._label(f"本组后休息：{dose['rest']}"))

    def _action_card(self, item):
        card, box = self._card(f"{item['order']}. {item['name']} · {item['phase']}")
        unilateral = any(dose["per_side"] for dose in item["sets"])
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
            dose["per_side"] for member in item["members"] for dose in member["sets"]
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
            self.issues_label.setText("\n".join(
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

    def command(self, command):
        selected = self.revisions.currentItem()
        identifier = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        try:
            if command == "new":
                self.dialog = GroupPlanEditor(self.service, parent=self)
                self.dialog.exec()
                identifier = self.dialog.saved_id
            elif command == "import":
                path, _ = QFileDialog.getOpenFileName(self, T["import"], "", T["json_filter"])
                if path:
                    identifier = self.handoff.import_file(Path(path))
            elif identifier is None:
                return
            elif command == "edit":
                revision = self.service.get(identifier)
                if revision["status"] != "draft":
                    raise ValueError("Only draft revisions can be edited.")
                self.dialog = GroupPlanEditor(self.service, revision, self)
                self.dialog.exec()
            elif command == "clone":
                source = self.service.get(identifier)
                name, accepted = QInputDialog.getText(
                    self, T["clone"], T["clone_name_prompt"]
                )
                if not accepted or not name.strip():
                    return
                base_number, accepted = QInputDialog.getInt(
                    self, T["clone"], T["clone_base_prompt"], 1, 1, 999
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
                self.dialog = GroupPlanActivation(self.service, identifier, self)
                self.dialog.exec()
            elif command == "export":
                path = self.handoff.export(identifier)
                QMessageBox.information(self, T["export"], T["exported"] + str(path))
        except (ValueError, OSError) as exc:
            error(self, exc)
            return
        self.refresh(identifier)
