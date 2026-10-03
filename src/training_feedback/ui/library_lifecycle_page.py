"""Native root-local lifecycle review. Services own all transitions and impact rules."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .labels import EXERCISE_SOURCE_LABELS, user_message
from .labels import LIFECYCLE_TEXT as T
from .review_occurrence import OccurrenceQuickFill


def render_impact(preview):
    lines = [T[preview["operation"]], T["consequence"],
             f"{T['batch_targets']}（{len(preview['targets'])}）："
             + "、".join(target["name"] for target in preview["targets"]), ""]
    for target, impact in zip(preview["targets"], preview["impacts"], strict=True):
        source = target["exercise"]["source"]
        lines.extend([target["name"],
                      f"{T['source']}：{EXERCISE_SOURCE_LABELS.get(source, source)}"])
        removal = target["removal"]
        local = removal["local"]
        lines.append(T["local"] + "：" + (T[local["disposition"]] if local else T["no_decision"]))
        if removal["publisher"]:
            lines.append(T["publisher"] + "：" + T[removal["publisher"]])
        lines.append(T["enabled"] if impact["enabled"] else T["disabled"])
        for kind in ("plans", "groups", "sessions", "reviews", "variants", "exports"):
            lines.append(f"{T[kind]}（{len(impact[kind])}）")
            for index, row in enumerate(impact[kind], 1):
                if kind == "plans":
                    text = (f"{index}. {row['name']} · {T['plan_revision']} "
                            f"v{row['revision_number']} · " + T[row['status']])
                    text += "\n    " + "；".join(
                        f"训练日 {item['day_order']}" for item in row["items"]
                    )
                elif kind == "groups":
                    text = f"{index}. 训练日 {row['day_order']} · 动作组「{row['name']}」"
                elif kind == "sessions":
                    text = f"{index}. {row['training_date']} · {T[row['status']]}"
                elif kind == "reviews":
                    text = f"{index}. {T[row['event_type']]} · {row['confirmed_at']}"
                elif kind == "variants":
                    text = f"{index}. {row['name']}"
                else:
                    text = (f"{index}. {row.get('created_at') or '—'} · "
                            f"{T[row['availability']]}")
                lines.append("  - " + text)
        lines.append("")
    return "\n".join(lines)


class LifecycleRequestDialog(QDialog):
    def __init__(self, service, targets=(), parent=None):
        super().__init__(parent)
        self.service, self.preview, self.saved_id = service, None, None
        self.setWindowTitle(T["new_request"])
        self.resize(940, 720)
        layout = QVBoxLayout(self)
        body = QWidget()
        content = QVBoxLayout(body)
        self.operation = QComboBox()
        for operation in ("remove", "restore"):
            self.operation.addItem(T[operation], operation)
        content.addWidget(self.operation)
        self.targets = QTreeWidget()
        self.targets.setHeaderLabels([T["target"], T["disposition"]])
        self.targets.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.targets.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        chosen = {target.exercise: target for target in targets}
        for row in service.library.browse():
            target = chosen.get(row["target"].exercise, row["target"])
            entry = service.library.target_entry(target)
            item = QTreeWidgetItem([entry["content"]["canonical_name"],
                                   T["removed"] if row["eligibility"].removed else T["available"]])
            item.setData(0, Qt.ItemDataRole.UserRole, target)
            self.targets.addTopLevelItem(item)
            item.setSelected(target.exercise in chosen)
        self.targets.setMinimumHeight(160)
        content.addWidget(self.targets)
        content.addWidget(QLabel(T["reason"]))
        self.reason = QPlainTextEdit()
        self.reason.setMaximumHeight(90)
        content.addWidget(self.reason)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(220)
        content.addWidget(self.details, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)
        self.confirmed = QCheckBox(T["confirm_request"])
        layout.addWidget(self.confirmed)
        row = QHBoxLayout()
        self.preview_button = QPushButton(T["preview"])
        self.submit = QPushButton(T["submit"])
        self.cancel = QPushButton(T["close"])
        for button in (self.preview_button, self.submit, self.cancel):
            row.addWidget(button)
        layout.addLayout(row)
        self.preview_button.clicked.connect(self._preview)
        self.submit.clicked.connect(self._submit)
        self.cancel.clicked.connect(self.reject)
        self.targets.itemSelectionChanged.connect(self._invalidate)
        self.operation.currentIndexChanged.connect(self._invalidate)
        self._invalidate()

    def _invalidate(self):
        self.preview = None
        self.submit.setEnabled(False)
        self.confirmed.setChecked(False)
        self.details.clear()

    def _selected(self):
        return [item.data(0, Qt.ItemDataRole.UserRole) for item in self.targets.selectedItems()]

    def _preview(self):
        self._invalidate()
        try:
            self.preview = self.service.preview(self._selected(), self.operation.currentData())
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        self.details.setPlainText(render_impact(self.preview))
        self.submit.setEnabled(True)

    def _submit(self):
        if self.preview is None:
            return
        try:
            self.saved_id = self.service.request(
                self._selected(), operation=self.operation.currentData(),
                reason=self.reason.toPlainText(), expected_preview=self.preview["token"],
                user_confirmed=self.confirmed.isChecked(),
            )
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        self.accept()


class LibraryLifecyclePage(QWidget):
    def __init__(self, service, parent=None, *, targets=()):
        super().__init__(parent)
        self.service, self.targets = service, targets
        self.request, self.preview, self.dialog = None, None, None
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.new_button = QPushButton(T["new_request"])
        self.reload_button = QPushButton(T["reload"])
        top.addWidget(self.new_button)
        top.addWidget(self.reload_button)
        layout.addLayout(top)
        self.tabs = QTabWidget()
        splitter = QSplitter()
        self.requests = QTreeWidget()
        self.requests.setHeaderLabels([T["request"], T["target"], T["status"]])
        self.requests.header().setStretchLastSection(False)
        for column in (0, 2):
            self.requests.header().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents,
            )
        self.requests.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        splitter.addWidget(self.requests)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(1, 2)
        self.tabs.addTab(splitter, T["local"])
        self.publisher = QPlainTextEdit()
        self.publisher.setReadOnly(True)
        self.tabs.addTab(self.publisher, T["publisher"])
        layout.addWidget(self.tabs, 1)
        fields = QWidget()
        form = QFormLayout(fields)
        self.source = QLineEdit()
        source_row = QHBoxLayout()
        source_row.addWidget(self.source)
        self.self_source = QPushButton(T["self"])
        self.self_source.clicked.connect(lambda: self.source.setText(T["self_source"]))
        source_row.addWidget(self.self_source)
        form.addRow(T["source"], source_row)
        self.occurred = QLineEdit()
        occurred_row = QHBoxLayout()
        occurred_row.addWidget(self.occurred)
        self.quick_fill = OccurrenceQuickFill(self.occurred, service.library.clock)
        occurred_row.addWidget(self.quick_fill)
        form.addRow(T["occurred"], occurred_row)
        self.note = QPlainTextEdit()
        self.note.setMaximumHeight(70)
        form.addRow(T["note"], self.note)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(fields)
        scroll.setMaximumHeight(205)
        layout.addWidget(scroll)
        self.confirmed = QCheckBox(T["confirm_decision"])
        layout.addWidget(self.confirmed)
        self.actions = {}
        for names in (("preview", "under_review", "approved", "approve_apply"),
                      ("applied", "rejected", "cancelled")):
            row = QHBoxLayout()
            for name in names:
                button = QPushButton(T["button_" + name])
                button.clicked.connect(lambda checked=False, action=name: self._action(action))
                self.actions[name] = button
                row.addWidget(button)
            layout.addLayout(row)
        self.new_button.clicked.connect(self._new)
        self.reload_button.clicked.connect(self.reload)
        self.requests.currentItemChanged.connect(self._choose)
        self.reload()

    def _new(self):
        self.dialog = LifecycleRequestDialog(self.service, self.targets, self)
        self.dialog.exec()
        if self.dialog.saved_id is not None:
            self.reload(self.dialog.saved_id)

    def reload(self, selected=None):
        if not isinstance(selected, int) or isinstance(selected, bool):
            selected = self.request["id"] if self.request else None
        self.requests.clear()
        for request in self.service.requests():
            names = "、".join(target["name"] for target in request["preview"]["targets"])
            item = QTreeWidgetItem([f"{T[request['operation']]} · {request['requested_at']}",
                                   names, T[request["status"]]])
            item.setToolTip(1, names)
            item.setData(0, Qt.ItemDataRole.UserRole, request)
            self.requests.addTopLevelItem(item)
            if request["id"] == selected:
                self.requests.setCurrentItem(item)
        if self.requests.currentItem() is None and self.requests.topLevelItemCount():
            self.requests.setCurrentItem(self.requests.topLevelItem(0))
        self._choose(self.requests.currentItem())
        self.publisher.setPlainText(T["publisher_note"] + "\n\n" + "\n\n".join(
            f"{self._publisher_name(row)} · {T[row['disposition']]}\n"
            f"{T['catalog_version']}：{row['catalog_version']} · {row['observed_at']}"
            for row in self.service.publisher_events()
        ))

    def _publisher_name(self, row):
        entry = self.service.library.catalog.get(row["stable_key"])
        return entry["content"]["canonical_name"] if entry else row["stable_key"]

    def _choose(self, item, previous=None):
        self.request = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        self.preview = None
        self.confirmed.setChecked(False)
        allowed = self.service.available_actions(self.request) if self.request else set()
        for action, button in self.actions.items():
            command = "approved" if action == "approve_apply" else action
            button.setEnabled(bool(allowed) if action == "preview" else command in allowed)
        if not self.request:
            self.details.clear()
            return
        request = self.request
        self.history_text = (
            f"{T['reason']}：{request['reason']}\n{T['requested']}：{request['requested_at']}\n\n"
            + "\n\n".join(f"{T[event['kind']]} · {event['confirmed_at']}\n"
                            f"{T['source']}：{event['source']}\n"
                            f"{T['occurred']}：{event['occurred_at']}\n{event['note']}"
                            for event in request["events"])
        )
        seen = {request["events"][-1]["preview"]["token"]}
        for event in request["events"]:
            if event["preview"]["token"] not in seen:
                seen.add(event["preview"]["token"])
                self.history_text += ("\n\n" + T["prior_impact"] + " · " + event["confirmed_at"]
                                      + "\n" + render_impact(event["preview"]))
        self.details.setPlainText(render_impact(request["events"][-1]["preview"])
                                  + "\n" + self.history_text)

    def _action(self, action):
        if self.request is None:
            return
        try:
            if action == "preview":
                self.preview = None
                self.confirmed.setChecked(False)
                self.preview = self.service.preview_request(self.request["id"])
                self.details.setPlainText(render_impact(self.preview) + "\n" + self.history_text)
                return
            result = self.service.transition(
                self.request["id"], "approved" if action == "approve_apply" else action,
                expected_event_id=self.request["events"][-1]["id"],
                expected_preview=self.preview["token"] if self.preview else None,
                source=self.source.text(), occurred_at=self.occurred.text(),
                note=self.note.toPlainText(), user_confirmed=self.confirmed.isChecked(),
                apply=action == "approve_apply",
            )
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        self.reload(result["id"])
