"""New-model catalog UI. All content/state decisions go through LibraryWorkflowService."""

from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..application.library_workflow import LibraryTarget
from .guidance_widgets import GuidanceChangesView, GuidanceForm, GuidanceView
from .labels import (
    CATEGORY_LABELS,
    EXERCISE_ENABLED_LABELS,
    LIBRARY_REASON_LABELS,
    POSITION_LABELS,
    REVIEW_STATE_LABELS,
    REVIEWER_TYPE_LABELS,
    VARIANT_LABELS,
    localize_dialog_buttons,
    user_message,
)
from .labels import (
    LIBRARY_TEXT as T,
)
from .review_occurrence import OccurrenceQuickFill, remember_occurrence


def buttons(parent, save, cancel):
    box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                          QDialogButtonBox.StandardButton.Cancel, parent)
    localize_dialog_buttons(box)
    box.accepted.connect(save)
    box.rejected.connect(cancel)
    return box


def show_images(layout, service, target):
    while layout.count():
        widget = layout.takeAt(0).widget()
        widget.deleteLater()
    if target is None:
        return
    entry = service.target_entry(target)
    for check in service.eligibility(target).image_checks:
        label = QLabel()
        label.setWordWrap(True)
        if check.valid:
            try:
                pixmap = QPixmap()
                pixmap.loadFromData(service.checked_image(target, check.index))
                label.setPixmap(pixmap.scaledToWidth(
                    420, Qt.TransformationMode.SmoothTransformation,
                ))
            except (ValueError, OSError):
                label.setText(T["invalid_image"])
        else:
            label.setText(LIBRARY_REASON_LABELS[check.reason])
        layout.addWidget(label)
        caption = QLabel(entry["content"]["guidance"]["images"][check.index].get("caption", ""))
        caption.setWordWrap(True)
        caption.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(caption)


class CatalogReviewDialog(QDialog):
    def __init__(self, service, targets, parent=None):
        super().__init__(parent)
        self.service, self.targets = service, deepcopy(targets)
        self.answer_file = None
        self.setWindowTitle(T["review_title"])
        self.resize(700, 650)
        layout = QVBoxLayout(self)
        self.targets_combo = QComboBox()
        for target in self.targets:
            entry = service.target_entry(target)
            self.targets_combo.addItem(
                f"{entry['content']['canonical_name']} · {target.content['sha256'][:12]}", target,
            )
        layout.addWidget(self.targets_combo)
        tabs = QTabWidget()
        self.view = GuidanceView(include_review=False)
        tabs.addTab(self.view, T["details"])
        self.image_panel = QWidget()
        self.image_layout = QVBoxLayout(self.image_panel)
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_scroll.setWidget(self.image_panel)
        tabs.addTab(image_scroll, T["image"])
        self.changes = GuidanceChangesView()
        tabs.addTab(self.changes, T["comparison"])
        layout.addWidget(tabs, 1)
        self.targets_combo.currentIndexChanged.connect(self._show_target)
        form = QFormLayout()
        self.reviewer = QComboBox()
        for key in ("external_ai_expert", "human_expert"):
            self.reviewer.addItem(REVIEWER_TYPE_LABELS[key], key)
        self.source = QLineEdit()
        self.occurred = QLineEdit()
        self.occurred.setPlaceholderText(T["occurrence_hint"])
        self.quick_fill = OccurrenceQuickFill(self.occurred, service.clock)
        self.note = QPlainTextEdit()
        self.note.setMaximumHeight(80)
        form.addRow(T["reviewer"], self.reviewer)
        form.addRow(T["review_source"], self.source)
        form.addRow(T["occurred"], self.occurred)
        form.addRow("", self.quick_fill)
        form.addRow(T["note"], self.note)
        layout.addLayout(form)
        self.answer = QPushButton(T["answer"])
        self.answer.clicked.connect(self._choose_answer)
        layout.addWidget(self.answer)
        self.confirm = QCheckBox(T["review_confirm"])
        layout.addWidget(self.confirm)
        self.button_box = buttons(self, self._save, self.reject)
        layout.addWidget(self.button_box)
        self._show_target()

    def _show_target(self):
        target = self.targets_combo.currentData()
        if target:
            entry = self.service.target_entry(target)
            self.view.set_guidance(entry["content"]["guidance"])
            show_images(self.image_layout, self.service, target)
            selected = self.service.get(target.exercise)["selected"]
            self.changes.set_revisions(
                {"id": selected["reference"]["id"], "guidance": selected["content"]["guidance"]}
                if selected else None,
                {"id": entry["reference"]["id"], "guidance": entry["content"]["guidance"]},
            )

    def _choose_answer(self):
        from pathlib import Path
        path, _ = QFileDialog.getOpenFileName(self, T["answer"])
        if path:
            self.answer_file = Path(path)
            self.answer.setText(self.answer_file.name)

    def _save(self):
        try:
            self.service.record_review(
                self.targets, reviewer_type=self.reviewer.currentData(), source=self.source.text(),
                occurred_at=self.occurred.text(), note=self.note.toPlainText(),
                user_confirmed=self.confirm.isChecked(), answer_file=self.answer_file,
            )
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        remember_occurrence(self.occurred.text())
        self.accept()


class CatalogEditor(QDialog):
    def __init__(self, service, target, parent=None):
        super().__init__(parent)
        self.service, self.target = service, deepcopy(target)
        self.original = deepcopy(service.target_entry(target)["content"])
        self.saved_id = None
        self.setWindowTitle(T["edit_title"])
        self.resize(760, 700)
        content = QWidget()
        fields = QVBoxLayout(content)
        form = QFormLayout()
        self.name = QLineEdit(self.original["canonical_name"])
        self.aliases = QPlainTextEdit("\n".join(self.original["aliases"]))
        self.aliases.setMaximumHeight(70)
        self.category = QComboBox()
        for value, label in CATEGORY_LABELS.items():
            self.category.addItem(label, value)
        self.category.setCurrentIndex(self.category.findData(self.original["category"]))
        self.equipment = QLineEdit(self.original["equipment_summary"])
        self.family = QComboBox()
        self.family.addItem(T["standalone"], None)
        for family in service.catalog.families():
            self.family.addItem(family["name"], family["key"])
        self.role = QComboBox()
        for value, label in VARIANT_LABELS.items():
            self.role.addItem(label, value)
        self.position = QComboBox()
        for value, label in POSITION_LABELS.items():
            self.position.addItem(label, value)
        self.order = QSpinBox()
        self.order.setRange(1, 1000000)
        self.parent_combo = QComboBox()
        self.parent_combo.addItem(T["none"], None)
        for row in service.parent_choices():
            name = row["name"] + (T["parent_missing"] if row["missing"] else "")
            self.parent_combo.addItem(name, row["exercise"])
        classification = self.original["classification"]
        self.family.setCurrentIndex(self.family.findData(classification["family_key"]))
        self.role.setCurrentIndex(self.role.findData(classification["variant_role"]))
        self.position.setCurrentIndex(self.position.findData(classification["starting_position_class"]))
        self.order.setValue(classification["variant_order"])
        self.parent_combo.setCurrentIndex(self.parent_combo.findData(classification["parent_exercise_key"]))
        for text, widget in (("name", self.name), ("aliases", self.aliases),
                             ("category", self.category), ("equipment", self.equipment),
                             ("family", self.family), ("role", self.role),
                             ("position", self.position), ("order", self.order),
                             ("parent", self.parent_combo)):
            form.addRow(T[text], widget)
        fields.addLayout(form)
        self.membership = QCheckBox(T["membership"])
        fields.addWidget(self.membership)
        self.guidance = GuidanceForm(self.original["guidance"])
        # Image declarations/hashes come from the explicit file-association action.
        self.guidance.images_editor.setEnabled(False)
        fields.addWidget(self.guidance)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        layout = QVBoxLayout(self)
        layout.addWidget(scroll, 1)
        self.button_box = buttons(self, self._save, self.reject)
        layout.addWidget(self.button_box)

    def _save(self):
        content = deepcopy(self.original)
        content.update(canonical_name=self.name.text(), category=self.category.currentData(),
                       equipment_summary=self.equipment.text(), guidance=self.guidance.guidance())
        if self.aliases.toPlainText() != "\n".join(self.original["aliases"]):
            content["aliases"] = self.aliases.toPlainText().splitlines()
        classification = {
            "family_key": self.family.currentData(), "variant_role": self.role.currentData(),
            "variant_order": self.order.value(),
            "parent_exercise_key": self.parent_combo.currentData(),
            "starting_position_class": self.position.currentData(),
        }
        if classification != self.original["classification"] and not self.membership.isChecked():
            QMessageBox.warning(self, T["error"], T["membership"])
            return
        content["classification"] = classification
        try:
            self.saved_id = self.service.save_override(
                self.target.exercise, content, self.target.content,
            )
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        self.accept()


class CatalogLibraryPage(QWidget):
    def __init__(self, service, parent=None, *, removals=None):
        super().__init__(parent)
        self.service = service
        self.removals = removals
        self.target = None
        self.dialog = None
        layout = QVBoxLayout(self)
        self.version_label = QLabel(f"{T['catalog']}：{service.catalog.version}")
        layout.addWidget(self.version_label)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(T["search"])
        self.position = QComboBox()
        self.position.addItem(T["all_positions"], None)
        for key, text in POSITION_LABELS.items():
            self.position.addItem(text, key)
        filters.addWidget(self.search)
        filters.addWidget(self.position)
        refresh = QPushButton(T["refresh"])
        refresh.clicked.connect(self.refresh)
        filters.addWidget(refresh)
        layout.addLayout(filters)
        splitter = QSplitter()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([T[key] for key in ("name", "source", "position", "readiness",
                                                     "review", "enabled")])
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        splitter.addWidget(self.tree)
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self.versions = QComboBox()
        self.versions.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.versions.setMinimumContentsLength(20)
        detail_layout.addWidget(self.versions)
        self.status = QLabel()
        self.status.setWordWrap(True)
        detail_layout.addWidget(self.status)
        self.tabs = QTabWidget()
        self.guidance = GuidanceView(include_review=False)
        self.tabs.addTab(self.guidance, T["details"])
        self.comparison = GuidanceChangesView()
        self.tabs.addTab(self.comparison, T["comparison"])
        self.images = QWidget()
        self.images_layout = QVBoxLayout(self.images)
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_scroll.setWidget(self.images)
        self.tabs.addTab(image_scroll, T["image"])
        self.review_history = QPlainTextEdit()
        self.review_history.setReadOnly(True)
        self.tabs.addTab(self.review_history, T["review_events"])
        detail_layout.addWidget(self.tabs)
        splitter.addWidget(detail)
        layout.addWidget(splitter, 1)
        self.actions = {}
        for names in (("select", "enable", "disable", "record_review", "withdraw"),
                      ("edit", "copy", "image", "batch_review")):
            row = QHBoxLayout()
            for name in names:
                button = QPushButton(T[name])
                self.actions[name] = button
                button.clicked.connect(lambda checked=False, action=name: self._action(action))
                row.addWidget(button)
            layout.addLayout(row)
        self.search.textChanged.connect(self.refresh)
        if removals is not None:
            self.removal_button = QPushButton(T["removal"])
            self.removal_button.clicked.connect(self._open_removals)
            layout.addWidget(self.removal_button)
        self.position.currentIndexChanged.connect(self.refresh)
        self.tree.currentItemChanged.connect(self._choose)
        self.versions.currentIndexChanged.connect(self._show_version)
        self.refresh()

    def _open_removals(self):
        from .library_lifecycle_page import LibraryLifecyclePage

        targets = [item.data(0, Qt.ItemDataRole.UserRole) for item in self.tree.selectedItems()
                   if item.data(0, Qt.ItemDataRole.UserRole)]
        if len(targets) == 1 and self.target and targets[0].exercise == self.target.exercise:
            targets = [self.target]
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle(T["removal"])
        self.dialog.resize(1040, 780)
        layout = QVBoxLayout(self.dialog)
        layout.addWidget(LibraryLifecyclePage(self.removals, self.dialog, targets=targets))
        close = QPushButton(T["close"])
        close.clicked.connect(self.dialog.accept)
        layout.addWidget(close)
        self.dialog.exec()
        self.refresh()

    def refresh(self):
        previous_target = self.target
        self.tree.clear()
        families = {family["key"]: family["name"] for family in self.service.catalog.families()}
        parents = {}
        for row in self.service.browse(self.search.text(), self.position.currentData()):
            content, status = row["display"]["content"], row["eligibility"]
            family = content["classification"]["family_key"]
            if family not in parents:
                parents[family] = QTreeWidgetItem([families.get(family, T["standalone"])])
                self.tree.addTopLevelItem(parents[family])
            item = QTreeWidgetItem([
                content["canonical_name"], T[row["exercise"]["source"]],
                POSITION_LABELS[content["classification"]["starting_position_class"]],
                T["removed"] if status.removed else (T["ready"] if status.eligible else T["draft"]),
                REVIEW_STATE_LABELS[status.reviewed],
                EXERCISE_ENABLED_LABELS[row["enabled"]],
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, row["target"])
            parents[family].addChild(item)
        self.tree.expandAll()
        matching = None
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                candidate = child.data(0, Qt.ItemDataRole.UserRole)
                if previous_target and candidate.exercise == previous_target.exercise:
                    matching = child
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(matching or self.tree.topLevelItem(0).child(0))
            if matching:
                for index in range(self.versions.count()):
                    if self.versions.itemData(index) == previous_target:
                        self.versions.setCurrentIndex(index)
                        break
        else:
            self._choose(None)

    def _choose(self, item, previous=None):
        self.versions.blockSignals(True)
        self.versions.clear()
        self.target = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if self.target:
            exercise = self.service.get(self.target.exercise)
            entries = list(exercise["local_contents"])
            if exercise["bundled"]:
                entries.append(exercise["bundled"])
            seen = set()
            for entry in entries:
                identity = entry["reference"]
                key = tuple(sorted(identity.items()))
                if key in seen:
                    continue
                seen.add(key)
                self.versions.addItem(
                    f"{identity['id']} · v{identity['version']} · {identity['sha256'][:12]}",
                    LibraryTarget(self.target.exercise, identity),
                )
            index = next((i for i in range(self.versions.count())
                          if self.versions.itemData(i) == self.target), 0)
            self.versions.setCurrentIndex(index)
        self.versions.blockSignals(False)
        self._show_version()

    def _show_version(self):
        self.target = self.versions.currentData()
        for action in self.actions.values():
            action.setEnabled(self.target is not None)
        show_images(self.images_layout, self.service, self.target)
        if self.target is None:
            self.guidance.set_guidance(None)
            self.status.clear()
            self.review_history.clear()
            self.comparison.clear()
            return
        entry = self.service.target_entry(self.target)
        status = self.service.eligibility(self.target)
        exercise = self.service.get(self.target.exercise)
        self.guidance.set_guidance(entry["content"]["guidance"])
        selected = exercise["selected"]
        self.status.setText(
            f"{T['selected']}：{selected['reference']['sha256'][:12] if selected else T['none']} · "
            f"{REVIEW_STATE_LABELS[status.reviewed]} · "
            f"{EXERCISE_ENABLED_LABELS[exercise['enabled']]}\n"
            + "；".join(LIBRARY_REASON_LABELS[reason] for reason in status.reasons)
        )
        base, current = self.service.compare_base(self.target)
        if base:
            self.comparison.set_revisions(
                {"id": base["reference"]["id"], "guidance": base["content"]["guidance"]},
                {"id": current["reference"]["id"], "guidance": current["content"]["guidance"]},
            )
        else:
            self.comparison.setPlainText(T["no_base"])
        events = self.service.review_events(self.target)
        self.review_history.setPlainText("\n\n".join(
            f"{T[event['event_type']]} · {event['confirmed_at']}\n"
            f"{event['review_source']} · {event['reviewed_at'] or T['none']}\n{event['note']}\n"
            f"{event['attachment'] or T['no_answer']}" for event in events
        ))

    def _confirm(self, text):
        answer = QMessageBox.question(self, T["confirm_title"], text)
        return answer == QMessageBox.StandardButton.Yes

    def _action(self, action):
        if not self.target:
            return
        target = deepcopy(self.target)
        try:
            if action == "select":
                if self._confirm(T["confirm_select"]):
                    self.service.select_content(target, user_confirmed=True)
            elif action in {"enable", "disable"}:
                if self._confirm(T["confirm_enable"]):
                    self.service.set_enabled(target, action == "enable", user_confirmed=True)
            elif action == "withdraw":
                events = self.service.review_events(target)
                if events and self._confirm(T["confirm_withdraw"]):
                    self.service.withdraw_review(
                        target, events[-1]["id"], note="", user_confirmed=True,
                    )
            elif action in {"record_review", "batch_review"}:
                targets = [target] if action == "record_review" else [
                    item.data(0, Qt.ItemDataRole.UserRole) for item in self.tree.selectedItems()
                    if item.data(0, Qt.ItemDataRole.UserRole)
                ]
                self.dialog = CatalogReviewDialog(self.service, targets, self)
                self.dialog.exec()
            elif action == "edit":
                self.dialog = CatalogEditor(self.service, target, self)
                self.dialog.exec()
                if self.dialog.saved_id is not None:
                    entry = self.service.user.content(self.dialog.saved_id)
                    self.target = LibraryTarget(target.exercise, entry["reference"])
            elif action == "copy":
                name, accepted = QInputDialog.getText(self, T["copy"], T["copy_name"])
                if accepted:
                    self.service.copy_to_custom(target.exercise, target.content, name)
            elif action == "image":
                from pathlib import Path
                path, _ = QFileDialog.getOpenFileName(self, T["pick_image"], "", T["image_filter"])
                if path:
                    identifier = self.service.attach_illustration(target, Path(path), "")
                    entry = self.service.user.content(identifier)
                    self.target = LibraryTarget(target.exercise, entry["reference"])
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, T["error"], user_message(str(exc)))
            return
        self.refresh()
