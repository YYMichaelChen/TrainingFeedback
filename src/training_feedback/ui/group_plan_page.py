"""Native editor for versioned single/group plans; all saves use the new-model service."""

from __future__ import annotations

from copy import deepcopy
from itertools import islice
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..domain.group_plans import (
    PlanDocument,
    action_from_choice,
    blank_group,
    group_from_item,
    migration_validation_projection,
    validate_action,
)
from .labels import (
    DOSE_UNIT_LABELS,
    EXERCISE_SOURCE_LABELS,
    PLAN_PHASE_LABELS,
    PLAN_STATUS_LABELS,
    POSITION_LABELS,
    VARIANT_LABELS,
    confirm,
    localize_dialog_buttons,
    make_unit_combo,
    user_message,
)
from .labels import (
    GROUP_PLAN_TEXT as T,
)
from .plan_presentation import plan_presentation


def combo(mapping, selected):
    widget = QComboBox()
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


def number(edit):
    return float(edit.text())


class ActionPrescriptionDialog(QDialog):
    def __init__(self, choices, action=None, *, member=False, parent=None):
        super().__init__(parent)
        self.member, self.source, self.value = member, deepcopy(action), None
        self.setWindowTitle(T["action"])
        self.resize(820, 640)
        body = QWidget()
        fields = QVBoxLayout(body)
        form = QFormLayout()
        self.exercise = QComboBox()
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
            str(action.get("rest_between_sides_seconds", 0) if action else 0)
        )
        rest_key = "rest_after_member_seconds" if member else "rest_after_action_seconds"
        self.rest = QLineEdit(str(action.get(rest_key, 0) if action else 0))
        for edit in (self.side_rest, self.rest):
            if edit.text() == "None":
                edit.clear()
                edit.setPlaceholderText(T["unknown"])
        if not member:
            form.addRow(T["phase"], self.phase)
            form.addRow(T["first_side"], self.side)
            form.addRow(T["side_rest"], self.side_rest)
        form.addRow(T["member_rest"] if member else T["exit_rest"], self.rest)
        self.note = QPlainTextEdit(action["note"] if action else "")
        self.note.setMaximumHeight(75)
        form.addRow(T["note"], self.note)
        fields.addLayout(form)
        fields.addWidget(QLabel(T["sets"]))
        self.sets = QTableWidget(0, 5)
        self.sets.setHorizontalHeaderLabels(
            [T[key] for key in ("value", "unit", "per_side", "set_rest", "note")]
        )
        self.sets.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for dose in action["sets"] if action else []:
            self.add_set(dose)
        fields.addWidget(self.sets, 1)
        controls = QHBoxLayout()
        add = QPushButton(T["add_set"])
        add.clicked.connect(lambda: self.add_set())
        remove = QPushButton(T["remove_set"])
        remove.clicked.connect(lambda: self.sets.removeRow(self.sets.currentRow()))
        controls.addWidget(add)
        controls.addWidget(remove)
        fields.addLayout(controls)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        layout = QVBoxLayout(self)
        layout.addWidget(scroll, 1)
        self.buttons = dialog_buttons(self, self.save)
        layout.addWidget(self.buttons)

    def add_set(self, dose=None):
        row = self.sets.rowCount()
        self.sets.insertRow(row)
        dose = dose or {
            "value": None,
            "unit": "reps",
            "per_side": False,
            "rest_after_set_seconds": 0,
            "note": "",
        }
        self.sets.setItem(
            row, 0, QTableWidgetItem("" if dose["value"] is None else str(dose["value"]))
        )
        self.sets.setCellWidget(row, 1, make_unit_combo(dose["unit"]))
        check = QCheckBox()
        check.setChecked(dose["per_side"])
        self.sets.setCellWidget(row, 2, check)
        self.sets.setItem(row, 3, QTableWidgetItem(
            "" if dose["rest_after_set_seconds"] is None else str(dose["rest_after_set_seconds"])))
        note = QTableWidgetItem(dose["note"])
        note.setData(Qt.ItemDataRole.UserRole, dose["note"])
        self.sets.setItem(row, 4, note)

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
                value = self.sets.item(row, 0).text()
                doses.append(
                    {
                        "order": row + 1,
                        "value": float(value) if value else None,
                        "unit": self.sets.cellWidget(row, 1).currentData(),
                        "per_side": self.sets.cellWidget(row, 2).isChecked(),
                        "rest_after_set_seconds": (
                            None if "provenance" in action and not self.sets.item(row, 3).text()
                            else float(self.sets.item(row, 3).text())),
                        "note": self.sets.item(row, 4).text(),
                    }
                )
            action["sets"] = doses
            action["note"] = text(self.note, self.source["note"] if self.source else "")
            action["rest_after_member_seconds" if self.member else "rest_after_action_seconds"] = (
                None if "provenance" in action and not self.rest.text() else number(self.rest)
            )
            if not self.member:
                action.update(
                    phase=self.phase.currentData(),
                    first_side=self.side.currentData(),
                    rest_between_sides_seconds=(None if "provenance" in action
                                               and not self.side_rest.text()
                                               else number(self.side_rest)),
                )
            validate_action(migration_validation_projection(action)
                            if "provenance" in action else action)
            self.value = action
        except (ValueError, TypeError) as exc:
            error(self, exc)
            return
        self.accept()


class GroupPrescriptionDialog(QDialog):
    def __init__(self, choices, group=None, parent=None):
        super().__init__(parent)
        self.choices = choices
        self.value = None
        self.group = deepcopy(group) if group else blank_group()
        self.setWindowTitle(T["group"])
        self.resize(820, 660)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(self.group["name"])
        self.phase = combo(PLAN_PHASE_LABELS, self.group["phase"])
        self.rounds = QSpinBox()
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
            self.fields[key] = QLineEdit(str(self.group[key]))
            form.addRow(T[label], self.fields[key])
        self.transition = QPlainTextEdit(self.group["transition"])
        self.note = QPlainTextEdit(self.group["note"])
        for edit in (self.transition, self.note):
            edit.setMaximumHeight(60)
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
        layout.addLayout(form)
        self.members = QListWidget()
        layout.addWidget(self.members, 1)
        controls = QHBoxLayout()
        for name, function in (
            ("add_member", self.add_member),
            ("edit_item", self.edit_member),
            ("up", lambda: self.move(-1)),
            ("down", lambda: self.move(1)),
            ("remove", self.remove),
        ):
            button = QPushButton(T[name])
            button.clicked.connect(function)
            controls.addWidget(button)
        layout.addLayout(controls)
        self.buttons = dialog_buttons(self, self.save)
        layout.addWidget(self.buttons)
        self.refresh()

    def refresh(self):
        self.members.clear()
        for member in self.group["members"]:
            self.members.addItem(f"{member['order']}. {member['exercise_name']}")

    def add_member(self):
        dialog = ActionPrescriptionDialog(self.choices, member=True, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.group["members"].append(dialog.value)
            PlanDocument.reorder(self.group["members"])
            self.refresh()

    def edit_member(self):
        index = self.members.currentRow()
        if index < 0:
            return
        dialog = ActionPrescriptionDialog(
            self.choices, self.group["members"][index], member=True, parent=self
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
            group.update({key: number(edit) for key, edit in self.fields.items()})
            if not group["name"].strip():
                raise ValueError("Group name cannot be empty.")
            group_from_item(group)
            self.value = group
        except ValueError as exc:
            error(self, exc)
            return
        self.accept()


class GroupPlanEditor(QDialog):
    def __init__(self, service, revision=None, parent=None):
        super().__init__(parent)
        self.service, self.revision, self.saved_id = service, revision, None
        self.source = (
            deepcopy(revision["payload"])
            if revision
            else {
                "schema": "training_feedback.plan",
                "schema_version": 2,
                "rationale": "",
                "plan": {"name": "", "purpose": "", "days": []},
            }
        )
        self.document = PlanDocument(self.source["plan"])
        self.setWindowTitle(T["edit"])
        self.resize(950, 740)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(self.source["plan"]["name"])
        self.purpose = QPlainTextEdit(self.source["plan"]["purpose"])
        self.rationale = QPlainTextEdit(self.source["rationale"])
        self.purpose.setMaximumHeight(70)
        self.rationale.setMaximumHeight(70)
        for name, widget in (
            ("name", self.name),
            ("purpose", self.purpose),
            ("rationale", self.rationale),
        ):
            form.addRow(T[name], widget)
        layout.addLayout(form)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([T["day"]])
        layout.addWidget(self.tree, 1)
        layout.addWidget(QLabel(T["day_hint"]))
        for names in (
            ("add_day", "rename_day", "add_action", "add_group", "edit_item"),
            ("remove", "up", "down", "move_day", "move_member"),
        ):
            row = QHBoxLayout()
            for name in names:
                button = QPushButton(T[name])
                button.clicked.connect(lambda checked=False, command=name: self.command(command))
                row.addWidget(button)
            layout.addLayout(row)
        self.buttons = dialog_buttons(self, self.save)
        layout.addWidget(self.buttons)
        self.refresh()

    def refresh(self, selection=None):
        self.tree.clear()
        for d, day in enumerate(self.document.plan["days"]):
            parent = QTreeWidgetItem([f"{day['order']}. {day['name']}"])
            parent.setData(0, Qt.ItemDataRole.UserRole, (d, None, None))
            self.tree.addTopLevelItem(parent)
            for i, item in enumerate(day["items"]):
                child = QTreeWidgetItem(
                    [f"{item['order']}. {item.get('name', item.get('exercise_name'))}"]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, (d, i, None))
                parent.addChild(child)
                for m, member in enumerate(item.get("members", [])):
                    leaf = QTreeWidgetItem(
                        [f"{member['order']}. {member['exercise_name']}"]
                    )
                    leaf.setData(0, Qt.ItemDataRole.UserRole, (d, i, m))
                    child.addChild(leaf)
        self.tree.expandAll()
        if self.tree.topLevelItemCount():
            d, i, m = selection if selection is not None else (0, None, None)
            item = self.tree.topLevelItem(min(d, self.tree.topLevelItemCount() - 1))
            if i is not None and i < item.childCount():
                item = item.child(i)
                if m is not None and m < item.childCount():
                    item = item.child(m)
            self.tree.setCurrentItem(item)

    def command(self, command):
        selected = self.tree.currentItem()
        d, i, m = selected.data(0, Qt.ItemDataRole.UserRole) if selected else (None, None, None)
        selection = (d, i, m) if d is not None else None
        try:
            if command == "add_day":
                name, accepted = QInputDialog.getText(self, T[command], T["day"])
                if accepted:
                    self.document.add_day(name)
                    selection = (len(self.document.plan["days"]) - 1, None, None)
            elif d is None:
                if command in ("add_action", "add_group"):
                    QMessageBox.information(self, T["error"], T["select_day_first"])
                return
            elif command == "rename_day":
                name, accepted = QInputDialog.getText(
                    self, T[command], T["day"], text=self.document.plan["days"][d]["name"]
                )
                if accepted and name.strip():
                    self.document.plan["days"][d]["name"] = name
            elif command in ("add_action", "add_group", "edit_item"):
                self.edit_item(command, d, i, m)
            elif command in ("up", "down"):
                rows = (
                    self.document.plan["days"]
                    if i is None
                    else self.document.plan["days"][d]["items"]
                    if m is None
                    else self.document.plan["days"][d]["items"][i]["members"]
                )
                self.document.move(
                    rows, d if i is None else i if m is None else m, -1 if command == "up" else 1
                )
            elif command == "remove":
                self.remove(d, i, m)
            elif command in ("move_day", "move_member"):
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
        if source and m is not None:
            dialog = ActionPrescriptionDialog(
                choices, source["members"][m], member=True, parent=self
            )
        elif command == "add_group" or (source and source["kind"] == "group"):
            dialog = GroupPrescriptionDialog(choices, source, self)
        else:
            dialog = ActionPrescriptionDialog(choices, source, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if source is None:
                items.append(dialog.value)
                PlanDocument.reorder(items)
            elif m is not None:
                source["members"][m] = dialog.value
            else:
                items[i] = dialog.value

    def remove(self, d, i, m):
        if m is not None:
            group = self.document.plan["days"][d]["items"][i]
            dissolve = len(group["members"]) == 2
            if confirm(self, T["remove"], T["dissolve"] if dissolve else T["remove_confirm"]):
                self.document.remove_member(d, i, m, dissolve=dissolve)
        elif confirm(self, T["remove"], T["remove_confirm"]):
            rows = (
                self.document.plan["days"] if i is None else self.document.plan["days"][d]["items"]
            )
            del rows[d if i is None else i]
            PlanDocument.reorder(rows)

    def transfer(self, command, d, i, m):
        if i is None:
            return
        options, targets = [], []
        for day_index, day in enumerate(self.document.plan["days"]):
            if command == "move_day" and day_index != d:
                options.append(day["name"])
                targets.append(day_index)
            if command == "move_member" and m is not None:
                for group_index, group in enumerate(day["items"]):
                    if group["kind"] == "group" and (day_index, group_index) != (d, i):
                        options.append(f"{day['order']}/{group['order']} {group['name']}")
                        targets.append(group)
        if not targets:
            return
        value, accepted = QInputDialog.getItem(
            self, T[command], T["select_destination"], options, editable=False
        )
        if accepted:
            destination = targets[options.index(value)]
            if command == "move_day":
                self.document.move_item_to_day(d, i, destination)
            else:
                self.document.move_member(self.document.plan["days"][d]["items"][i], m, destination)

    def save(self):
        payload = deepcopy(self.source)
        payload["plan"] = deepcopy(self.document.plan)
        payload["plan"].update(
            name=self.name.text(), purpose=text(self.purpose, self.source["plan"]["purpose"])
        )
        payload["rationale"] = text(self.rationale, self.source["rationale"])
        try:
            if self.revision:
                self.service.save(
                    self.revision["id"], payload, expected_token=self.revision["edit_token"]
                )
                self.saved_id = self.revision["id"]
            else:
                self.saved_id = self.service.create(payload)
        except (ValueError, OSError) as exc:
            error(self, exc)
            return
        self.accept()


_SKIP_FIELDS = {"item_id", "group_id", "sha256", "key", "revision_id", "session_id",
                "content_id", "content", "provenance", "source_id", "dose_scope",
                "side_order_recorded", "set_rest_recorded"}


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


def render_plan(plan, adjustment=None):
    lines = [plan["name"], plan["purpose"]]
    if adjustment:
        lines.append(f"{T['rationale']}：{adjustment}")
    for day in plan["days"]:
        lines.append(f"\n{T['day']} {day['order']}: {day['name']}")
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
        self.resize(900, 700)
        layout = QVBoxLayout(self)
        view = QPlainTextEdit()
        view.setReadOnly(True)
        view.setPlainText(
            render_plan(
                self.preview["revision"]["payload"]["plan"],
                self.preview["revision"]["rationale"],
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
        self.revisions.setMinimumWidth(260)
        self.revisions.setMaximumWidth(320)
        self.revisions.setSpacing(4)
        self.revisions.setWordWrap(True)
        splitter.addWidget(self.revisions)

        self.detail_panel = QWidget()
        detail_layout = QVBoxLayout(self.detail_panel)
        detail_layout.setContentsMargins(14, 0, 0, 0)
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
        self.day_navigation = QComboBox()
        self.day_navigation.setObjectName("planDayNavigation")
        self.day_navigation.currentIndexChanged.connect(self._jump_to_day)
        detail_layout.addWidget(self.day_navigation)
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.detail_host = QWidget()
        self.detail_host.setMinimumWidth(0)
        self.detail_rows = QVBoxLayout(self.detail_host)
        self.detail_rows.setContentsMargins(0, 8, 8, 8)
        self.detail_rows.setSpacing(12)
        self.detail_rows.addStretch(1)
        self.detail_scroll.setWidget(self.detail_host)
        detail_layout.addWidget(self.detail_scroll, 1)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([288, 1000])
        layout.addWidget(splitter, 1)
        row = QHBoxLayout()
        self.buttons = {}
        for name in ("new", "edit", "clone", "activate", "import", "export"):
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
                    f"{revision['name']}\nv{revision['revision_number']} · "
                    + PLAN_STATUS_LABELS[revision["status"]]
                )
                metrics = QFontMetrics(self.revisions.font())
                height = metrics.boundingRect(
                    0,
                    0,
                    self.revisions.width() - 30,
                    2000,
                    Qt.TextFlag.TextWordWrap,
                    item.text(),
                ).height()
                item.setSizeHint(QSize(self.revisions.width() - 12, height + 14))
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
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(5)
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

    def _jump_to_day(self, index):
        if 0 <= index < len(self.day_cards):
            self.detail_scroll.ensureWidgetVisible(self.day_cards[index])

    def show_revision(self, item, previous=None):
        if item:
            revision = self.service.get(item.data(Qt.ItemDataRole.UserRole))
            self.presentation = plan_presentation(
                revision, self.service.content_issues(revision["id"])
            )
            self.revision_title.setText(self.presentation["name"])
            self.revision_meta.setText(
                f"v{self.presentation['version']} · {self.presentation['status']}"
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
            self.day_navigation.show()
            self.detail_scroll.show()
            self._clear_rows()
            self.day_navigation.blockSignals(True)
            self.day_navigation.clear()
            self.day_cards = []
            for day in self.presentation["days"]:
                day_card, day_box = self._card(f"{T['day']} {day['order']} · {day['name']}")
                for plan_item in day["items"]:
                    widget = (
                        self._group_card(plan_item)
                        if plan_item["kind"] == "group"
                        else self._action_card(plan_item)
                    )
                    day_box.addWidget(widget)
                self.detail_rows.insertWidget(self.detail_rows.count() - 1, day_card)
                self.day_cards.append(day_card)
                self.day_navigation.addItem(f"{T['day']} {day['order']} · {day['name']}")
            self.day_navigation.setCurrentIndex(0 if self.day_cards else -1)
            self.day_navigation.blockSignals(False)
            self._set_command_state(self.presentation["status_key"])
        else:
            self.presentation = None
            self.revision_title.clear()
            self.revision_meta.clear()
            self.purpose_label.clear()
            self.adjustment_label.clear()
            self.issues_label.clear()
            self.issues_label.hide()
            self._clear_rows()
            self.day_navigation.clear()
            self.day_navigation.hide()
            self.detail_scroll.hide()
            self.empty_label.show()
            self._set_command_state(None)

    def _set_command_state(self, status):
        available = status is not None
        self.buttons["edit"].setEnabled(status == "draft")
        self.buttons["clone"].setEnabled(available)
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
                identifier = self.service.clone(identifier)
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
