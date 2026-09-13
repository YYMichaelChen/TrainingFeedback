"""计划草稿编辑对话框：编辑训练目的、动作元数据与组数表格。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..domain.plans import PlanAction, PlanDay, PlannedSet, PlanPhase, PlanRevision
from .labels import (
    PLAN_PHASE_LABELS,
    confirm,
    label,
    localize_dialog_buttons,
    make_unit_combo,
    user_message,
)


class PlanEditor(QDialog):
    """Edit any action in a draft revision without rewriting untouched doses."""

    def __init__(self, repository, plan: dict, revision: dict, parent=None):
        super().__init__(parent)
        self.repository, self.plan, self.revision = repository, plan, revision
        self.dirty = False
        self._loading_table = False
        self._loading_action = False
        self._set_overrides = {}
        self._action_overrides = {}
        self.setWindowTitle("编辑计划草稿版本")
        self.purpose = QLineEdit(revision["purpose"])
        self.action_selector = QListWidget()
        self.action_selector.setMinimumWidth(190)
        self.action_selector.setWordWrap(True)
        for day_index, day in enumerate(revision["days"]):
            for action_index, action in enumerate(day["actions"]):
                action_label = (
                    f"第 {day['day_order']} 天 · 第 {action['action_order']} 项："
                    f"{action.get('exercise_name', action['exercise_id'])}"
                )
                item = QListWidgetItem(action_label)
                item.setData(Qt.ItemDataRole.UserRole, (day_index, action_index))
                self.action_selector.addItem(item)
        self.action_selector.setCurrentRow(0)
        self.phase = QComboBox()
        for phase in PlanPhase:
            self.phase.addItem(label(PLAN_PHASE_LABELS, phase), phase.value)
        self.rest = QDoubleSpinBox()
        self.rest.setRange(0, 100000)
        self.rest.setDecimals(2)
        self.action_note = QLineEdit()
        self.count = QSpinBox()
        self.count.setRange(1, 99)
        self.value = QDoubleSpinBox()
        self.value.setRange(0, 100000)
        self.value.setDecimals(2)
        self.unit = make_unit_combo()
        self.per_side = QCheckBox("每侧执行")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["组次", "数值", "单位", "每侧", "备注"])
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(170)
        self._load_action_defaults()
        self.action_title = QLabel()
        self.action_title.setTextFormat(Qt.TextFormat.PlainText)
        self.action_title.setObjectName("sectionTitle")
        self.action_title.setWordWrap(True)
        form = QFormLayout()
        for field_label, widget in (
            ("动作阶段", self.phase),
            ("休息秒数", self.rest),
            ("动作备注", self.action_note),
        ):
            form.addRow(field_label, widget)
        group = QGroupBox("逐组剂量 · 直接在表格中修改")
        group_layout = QVBoxLayout(group)
        group_layout.addWidget(self.table)
        row_tools = QHBoxLayout()
        self.add_set_button = QPushButton("＋ 添加一组")
        self.add_set_button.clicked.connect(self._add_set)
        self.remove_set_button = QPushButton("删除选中组")
        self.remove_set_button.clicked.connect(self._remove_set)
        self.equal_toggle = QPushButton("批量填入相同剂量…")
        self.equal_toggle.setCheckable(True)
        row_tools.addWidget(self.add_set_button)
        row_tools.addWidget(self.remove_set_button)
        row_tools.addWidget(self.equal_toggle)
        group_layout.addLayout(row_tools)
        self.equal_panel = QWidget()
        equal_layout = QFormLayout(self.equal_panel)
        equal_layout.addRow("组数", self.count)
        dose_row = QWidget()
        dose_layout = QHBoxLayout(dose_row)
        dose_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.value, self.unit, self.per_side):
            dose_layout.addWidget(widget)
        equal_layout.addRow("每组剂量", dose_row)
        apply_equal = QPushButton("填入当前动作的表格")
        apply_equal.setObjectName("secondaryButton")
        apply_equal.clicked.connect(self._apply_equal_sets)
        equal_layout.addRow(apply_equal)
        group_layout.addWidget(self.equal_panel)
        self.equal_panel.hide()
        self.equal_toggle.toggled.connect(self.equal_panel.setVisible)
        self.validation_message = QLabel()
        self.validation_message.setWordWrap(True)
        group_layout.addWidget(self.validation_message)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        title = QLabel("编辑训练计划")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        hint = QLabel("选择左侧动作，再编辑右侧的安排。保存后仍为草稿。")
        hint.setObjectName("muted")
        layout.addWidget(hint)
        purpose_form = QFormLayout()
        purpose_form.addRow("训练目的", self.purpose)
        layout.addLayout(purpose_form)
        self.splitter = QSplitter()
        self.splitter.addWidget(self.action_selector)
        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        editor_layout.addWidget(self.action_title)
        editor_layout.addLayout(form)
        editor_layout.addWidget(group, 1)
        self.editor_scroll = QScrollArea()
        self.editor_scroll.setWidgetResizable(True)
        self.editor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor_scroll.setWidget(editor_panel)
        self.splitter.addWidget(self.editor_scroll)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([240, 640])
        layout.addWidget(self.splitter, 1)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(buttons)
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("primaryButton")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.action_selector.currentRowChanged.connect(self._action_changed)
        self.phase.currentTextChanged.connect(self._action_metadata_changed)
        self.rest.valueChanged.connect(self._action_metadata_changed)
        self.action_note.textChanged.connect(self._action_metadata_changed)
        self.table.itemChanged.connect(self._table_changed)
        self._render_sets()
        self._displayed_key = self._selected_key()
        self.action_title.setText(self._selected_action().get("exercise_name", "训练动作"))
        self.resize(1000, 760)
        available = self.screen().availableGeometry()
        self.resize(min(self.width(), available.width() - 60),
                    min(self.height(), available.height() - 60))

    def _selected_key(self):
        return self.action_selector.currentItem().data(Qt.ItemDataRole.UserRole)

    def _selected_action(self):
        day_index, action_index = self._selected_key()
        return self.revision["days"][day_index]["actions"][action_index]

    def _sets_for_selected_action(self):
        key = self._selected_key()
        if key in self._set_overrides:
            return self._set_overrides[key]
        return tuple(
            PlannedSet(
                item["set_order"],
                item["unit"],
                item["value"],
                bool(item["per_side"]),
                item.get("note", ""),
            )
            for item in self._selected_action()["sets"]
        )

    def _load_action_defaults(self):
        self._loading_action = True
        action = self._selected_action()
        override = self._action_overrides.get(self._selected_key())
        phase = override[0] if override else action["phase"]
        rest = override[1] if override else action["rest_seconds"] or 0
        note = override[2] if override else action["note"]
        self.phase.setCurrentIndex(self.phase.findData(phase))
        self.rest.setValue(rest)
        self.action_note.setText(note)
        sets = self._sets_for_selected_action()
        first = sets[0]
        self.value.setValue(first.value or 0)
        self.unit.setCurrentIndex(self.unit.findData(first.unit.value))
        self.per_side.setChecked(first.per_side)
        self.count.setValue(len(sets))
        self._loading_action = False

    def _action_changed(self):
        try:
            self._store_current_table(self._displayed_key)
        except (AttributeError, ValueError) as exc:
            self.validation_message.setText("请先修正当前动作：" + user_message(str(exc)))
            self.action_selector.blockSignals(True)
            for row in range(self.action_selector.count()):
                key = self.action_selector.item(row).data(Qt.ItemDataRole.UserRole)
                if key == self._displayed_key:
                    self.action_selector.setCurrentRow(row)
                    break
            self.action_selector.blockSignals(False)
            return
        self._store_current_action(self._displayed_key)
        self._load_action_defaults()
        self._render_sets()
        self._displayed_key = self._selected_key()
        self.action_title.setText(self._selected_action().get("exercise_name", "训练动作"))
        self.equal_toggle.setChecked(False)
        self.validation_message.clear()

    def _action_metadata_changed(self):
        if not self._loading_action:
            self._store_current_action()
            self.dirty = True

    def _store_current_action(self, key=None):
        key = key or self._selected_key()
        if key is None or self._loading_action:
            return
        self._action_overrides[key] = (
            self.phase.currentData(),
            self.rest.value(),
            self.action_note.text(),
        )

    def _apply_equal_sets(self):
        if not confirm(
            self, "替换当前动作的组数？", "将替换当前表格的剂量和组备注。其他动作不变。"
        ):
            return
        self._loading_table = True
        self.table.setRowCount(self.count.value())
        for row in range(self.count.value()):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(str(self.value.value())))
            self._set_unit_cell(row, self.unit.currentData())
            self._set_side_cell(row, self.per_side.isChecked())
            self.table.setItem(row, 4, QTableWidgetItem(""))
        self._loading_table = False
        self._store_current_table()
        self.dirty = True
        self._render_sets()
        self.equal_toggle.setChecked(False)

    def _add_set(self):
        try:
            sets = self._table_sets()
            last = sets[-1]
            self._set_overrides[self._selected_key()] = sets + (
                PlannedSet(len(sets) + 1, last.unit, last.value, last.per_side),
            )
        except ValueError as exc:
            self.validation_message.setText(user_message(str(exc)))
            return
        self.dirty = True
        self._render_sets()

    def _remove_set(self):
        row = self.table.currentRow()
        if row < 0 or self.table.rowCount() <= 1:
            self.validation_message.setText("先选择要删除的组；每个动作至少保留一组。")
            return
        self._loading_table = True
        self.table.removeRow(row)
        for index in range(self.table.rowCount()):
            self.table.item(index, 0).setText(str(index + 1))
        self._loading_table = False
        self._table_changed(None)

    def _render_sets(self):
        self._loading_table = True
        sets = self._sets_for_selected_action()
        self.table.setRowCount(len(sets))
        for row, item in enumerate(sets):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.order)))
            self.table.item(row, 0).setFlags(
                self.table.item(row, 0).flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            self.table.setItem(
                row, 1, QTableWidgetItem("" if item.value is None else str(item.value))
            )
            self._set_unit_cell(row, item.unit.value)
            self._set_side_cell(row, item.per_side)
            self.table.setItem(row, 4, QTableWidgetItem(item.note))
        self._loading_table = False

    def _set_unit_cell(self, row, value):
        combo = make_unit_combo(value)
        combo.currentTextChanged.connect(lambda _value: self._table_changed(None))
        self.table.setCellWidget(row, 2, combo)

    def _set_side_cell(self, row, value):
        checkbox = QCheckBox()
        checkbox.setChecked(value)
        checkbox.stateChanged.connect(lambda _value: self._table_changed(None))
        self.table.setCellWidget(row, 3, checkbox)

    def _table_changed(self, _item):
        if not self._loading_table:
            self.dirty = True
            try:
                self._store_current_table()
                self.validation_message.clear()
            except (AttributeError, ValueError) as exc:
                self.validation_message.setText("请修正剂量：" + user_message(str(exc)))

    def _store_current_table(self, key=None):
        if self._loading_table or not self.table.rowCount():
            return
        self._set_overrides[key or self._selected_key()] = self._table_sets()

    def _table_sets(self):
        result = []
        for row in range(self.table.rowCount()):
            value = self.table.item(row, 1).text().strip()
            try:
                numeric_value = None if not value else float(value)
            except ValueError as exc:
                raise ValueError("Numeric dose values must be finite and non-negative.") from exc
            result.append(
                PlannedSet(
                    int(self.table.item(row, 0).text()),
                    self.table.cellWidget(row, 2).currentData(),
                    numeric_value,
                    self.table.cellWidget(row, 3).isChecked(),
                    self.table.item(row, 4).text(),
                )
            )
        return tuple(result)

    def _save(self):
        try:
            self._store_current_table()
            self._store_current_action()
            self.repository.replace_draft_revision(
                self.plan["id"], self.revision["id"], self._build_revision()
            )
        except (AttributeError, ValueError, KeyError) as exc:
            QMessageBox.warning(self, "无法保存草稿", user_message(str(exc)))
            return
        self.accept()

    def _build_revision(self):
        days = []
        for day_index, day in enumerate(self.revision["days"]):
            actions = []
            for action_index, action in enumerate(day["actions"]):
                sets = self._set_overrides.get(
                    (day_index, action_index),
                    tuple(
                        PlannedSet(
                            item["set_order"],
                            item["unit"],
                            item["value"],
                            bool(item["per_side"]),
                            item.get("note", ""),
                        )
                        for item in action["sets"]
                    ),
                )
                phase, rest, note = self._action_overrides.get(
                    (day_index, action_index),
                    (action["phase"], action["rest_seconds"] or 0, action["note"]),
                )
                actions.append(
                    PlanAction(
                        action["action_order"],
                        action["exercise_id"],
                        PlanPhase(phase),
                        sets,
                        rest,
                        note,
                    )
                )
            days.append(PlanDay(day["day_order"], day["name"], tuple(actions)))
        return PlanRevision(self.revision["name"], self.purpose.text(), tuple(days))
