"""New-model catalog UI. All content/state decisions go through LibraryWorkflowService."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
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
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..application.library_workflow import LibraryTarget
from .exercise_reading import ExerciseReading, show_readonly_text
from .guidance_widgets import GuidanceForm
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
from .sizing import bind_units, initial_size


def buttons(parent, save, cancel):
    box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                          QDialogButtonBox.StandardButton.Cancel, parent)
    localize_dialog_buttons(box)
    box.accepted.connect(save)
    box.rejected.connect(cancel)
    return box


def show_library_reading(reading, service, target, status=None):
    """Bind every declared image position to the service's exact checked target."""
    if target is None:
        reading.set_content(None, None, lambda index: b"")
        return
    target = deepcopy(target)
    entry = service.target_entry(target)
    checks = (status or service.eligibility(target)).image_checks

    def load(index):
        check = checks[index]
        if not check.valid:
            raise ValueError(LIBRARY_REASON_LABELS.get(check.reason, check.reason))
        return service.checked_image(target, index)

    reading.set_content(target, entry["content"]["guidance"], load)


def card_icon(service, target, status, cache=None):
    """Make a consistent thumbnail from an actual checked illustration."""
    check = next((item for item in status.image_checks if item.valid), None)
    if check is not None and cache is not None and check.sha256 in cache:
        return cache[check.sha256]
    screen = QApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen is not None else 1.0
    canvas = QPixmap(round(208 * dpr), round(144 * dpr))
    canvas.setDevicePixelRatio(dpr)
    canvas.fill(QColor("#e9f2f5"))
    painter = QPainter(canvas)
    if check is not None:
        try:
            source = QPixmap()
            if source.loadFromData(service.display_image(target, check)):
                scaled = source.scaled(
                    round(200 * dpr), round(136 * dpr), Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                scaled.setDevicePixelRatio(dpr)
                logical_width = round(scaled.width() / dpr)
                logical_height = round(scaled.height() / dpr)
                painter.drawPixmap((208 - logical_width) // 2,
                                   (144 - logical_height) // 2, scaled)
                painter.end()
                icon = QIcon(canvas)
                if cache is not None:
                    cache[check.sha256] = icon
                return icon
        except (ValueError, OSError):
            pass
    painter.setPen(QColor("#64788a"))
    painter.drawText(canvas.rect(), Qt.AlignmentFlag.AlignCenter, "暂无可用示意图")
    painter.end()
    return QIcon(canvas)


class CatalogReviewDialog(QDialog):
    def __init__(self, service, targets, parent=None):
        super().__init__(parent)
        self.service, self.targets = service, deepcopy(targets)
        self.answer_file = None
        self.setWindowTitle(T["review_title"])
        initial_size(self, 65, 50)
        layout = QVBoxLayout(self)
        self.targets_combo = QComboBox()
        for target in self.targets:
            entry = service.target_entry(target)
            self.targets_combo.addItem(entry["content"]["canonical_name"], target)
        layout.addWidget(self.targets_combo)
        self.reading = ExerciseReading()
        layout.addWidget(self.reading, 1)
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
        bind_units(self.note, "setMaximumHeight", 5)
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
            show_library_reading(self.reading, self.service, target)

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
        initial_size(self, 47.5, 43.75)
        content = QWidget()
        fields = QVBoxLayout(content)
        form = QFormLayout()
        self.name = QLineEdit(self.original["canonical_name"])
        self.aliases = QPlainTextEdit("\n".join(self.original["aliases"]))
        bind_units(self.aliases, "setMaximumHeight", 4.375)
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
    def __init__(self, service, parent=None, *, removals=None, progressive=False):
        super().__init__(parent)
        self.service = service
        self.removals = removals
        self.target = None
        self.dialog = None
        self._icon_cache = {}
        self._progressive = progressive
        self._first_load_started = False
        self._first_load_complete = False
        self._load_generation = 0
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        gallery = QWidget()
        gallery_layout = QVBoxLayout(gallery)
        title = QLabel(T["title"])
        title.setObjectName("pageTitle")
        gallery_layout.addWidget(title)
        self.version_label = QLabel(f"{T['catalog']}：{service.catalog.version}")
        self.version_label.setObjectName("muted")
        gallery_layout.addWidget(self.version_label)
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
        refresh.clicked.connect(self._refresh_with_feedback)
        filters.addWidget(refresh)
        gallery_layout.addLayout(filters)
        self.gallery_count = QLabel()
        self.gallery_count.setObjectName("muted")
        gallery_layout.addWidget(self.gallery_count)
        self.cards = QListWidget()
        self.cards.setViewMode(QListView.ViewMode.IconMode)
        self.cards.setResizeMode(QListView.ResizeMode.Adjust)
        self.cards.setMovement(QListView.Movement.Static)
        self.cards.setFlow(QListView.Flow.LeftToRight)
        self.cards.setWrapping(True)
        self.cards.setWordWrap(True)
        self.cards.setUniformItemSizes(True)
        bind_units(self.cards, "setIconSize", 13, 9, kind="size")
        bind_units(self.cards, "setGridSize", 14.75, 14.125, kind="size")
        bind_units(self.cards, "setSpacing", 0.625)
        bind_units(self.cards, "setStyleSheet", """
            QListWidget { background: transparent; border: none; }
            QListWidget::item { background: white; border: 1px solid #dce5ef;
                               border-radius: 0.75u; padding: 0.5u; color: #233249; }
            QListWidget::item:hover { border-color: #0f8175; background: #f5fbf9; }
            QListWidget::item:selected { border: 0.125u solid #0f8175;
                                        background: #e8f5f1; color: #115e59; }
        """, kind="style")
        gallery_layout.addWidget(self.cards, 1)
        batch_row = QHBoxLayout()
        self.batch_toggle = QCheckBox(T["batch_mode"])
        batch_row.addWidget(self.batch_toggle)
        self.batch_review_button = QPushButton(T["batch_review"])
        self.batch_review_button.clicked.connect(self._batch_review)
        batch_row.addWidget(self.batch_review_button)
        if removals is not None:
            self.batch_removal_button = QPushButton(T["removal"])
            self.batch_removal_button.clicked.connect(
                lambda: self._open_removals(self._selected_targets()))
            batch_row.addWidget(self.batch_removal_button)
        batch_row.addStretch()
        gallery_layout.addLayout(batch_row)
        self.stack.addWidget(gallery)
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        heading = QHBoxLayout()
        back = QPushButton(T["back_to_gallery"])
        back.clicked.connect(self._show_gallery)
        heading.addWidget(back)
        self.detail_title = QLabel()
        self.detail_title.setObjectName("sectionTitle")
        self.detail_title.setTextFormat(Qt.TextFormat.PlainText)
        self.detail_title.setWordWrap(True)
        heading.addWidget(self.detail_title, 1)
        self.more = QToolButton()
        self.more.setText("更多操作")
        self.more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu = QMenu(self.more)
        self.menu.aboutToShow.connect(self._prepare_menu)
        self.more.setMenu(self.menu)
        heading.addWidget(self.more)
        detail_layout.addLayout(heading)
        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        detail_layout.addWidget(self.status)
        self.reading = ExerciseReading()
        detail_layout.addWidget(self.reading, 1)
        self.actions = {}
        self.stack.addWidget(detail)
        layout.addWidget(self.stack, 1)
        self.search.textChanged.connect(self._filter_changed)
        self.position.currentIndexChanged.connect(self._filter_changed)
        self.cards.itemClicked.connect(self._card_clicked)
        self.cards.itemSelectionChanged.connect(self._update_batch_buttons)
        self.batch_toggle.toggled.connect(self._toggle_batch_mode)
        if progressive:
            self.gallery_count.setText(T["loading"])
            # 首次读取在页面第一次绘制之后再安排：直接 singleShot(0) 可能先于
            # 绘制执行，加载提示从未可见，重负载下用户看到的仍是上一个页面。
        else:
            self._refresh_with_feedback()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._progressive and not self._first_load_started:
            self._first_load_started = True
            QTimer.singleShot(0, self._refresh_with_feedback)

    def _refresh_with_feedback(self):
        try:
            self.refresh()
        except Exception as exc:
            self.cancel_loading()
            self.cards.clear()
            self.target = None
            self._show_gallery()
            self._show_version()
            message = user_message(str(exc)).strip() or type(exc).__name__
            self.gallery_count.setText(T["load_failed"].format(message=message))

    def _selected_targets(self):
        return [item.data(Qt.ItemDataRole.UserRole) for item in self.cards.selectedItems()]

    def _update_batch_buttons(self):
        enabled = self.batch_toggle.isChecked() and bool(self.cards.selectedItems())
        self.batch_review_button.setEnabled(enabled)
        if self.removals is not None:
            self.batch_removal_button.setEnabled(enabled)

    def _toggle_batch_mode(self, enabled):
        self.cards.clearSelection()
        self.cards.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection if enabled
            else QListWidget.SelectionMode.SingleSelection
        )
        self._update_batch_buttons()

    def _filter_changed(self):
        self._show_gallery()
        self._refresh_with_feedback()

    def _show_gallery(self):
        self.stack.setCurrentIndex(0)

    def _card_clicked(self, item):
        if not self.batch_toggle.isChecked():
            self._open_detail(item.data(Qt.ItemDataRole.UserRole))

    def _open_detail(self, target):
        self.target = target
        self._show_version()
        self.stack.setCurrentIndex(1)

    def _batch_review(self):
        targets = self._selected_targets()
        if not targets:
            return
        self.dialog = CatalogReviewDialog(self.service, targets, self)
        self.dialog.exec()
        self._refresh_with_feedback()

    def _open_removals(self, targets=None):
        from .library_lifecycle_page import LibraryLifecyclePage

        if isinstance(targets, bool) or targets is None:
            targets = [self.target] if self.target else []
        if not targets:
            return
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle(T["removal"])
        initial_size(self.dialog, 65, 48.75)
        layout = QVBoxLayout(self.dialog)
        layout.addWidget(LibraryLifecyclePage(self.removals, self.dialog, targets=targets))
        close = QPushButton(T["close"])
        close.clicked.connect(self.dialog.accept)
        layout.addWidget(close)
        self.dialog.exec()
        self._refresh_with_feedback()

    def _set_card(self, item, row, status):
        content = row["display"]["content"]
        family = content["classification"]["family_key"]
        family_name = self._family_names.get(family, T["standalone"])
        position = POSITION_LABELS[content["classification"]["starting_position_class"]]
        readiness = T["checking"] if status is None else (
            T["removed"] if status.removed else T["ready"] if status.eligible else T["draft"]
        )
        item.setText(f"{content['canonical_name']}\n{family_name} · {position}\n{readiness}")
        item.setData(Qt.ItemDataRole.UserRole, row["target"])
        if status is None:
            item.setIcon(QIcon())
            return
        item.setIcon(card_icon(self.service, row["target"], status, self._icon_cache))
        item.setToolTip(f"{content['canonical_name']}\n{family_name} · {position}\n"
                        f"{readiness} · {REVIEW_STATE_LABELS[status.reviewed]} · "
                        f"{EXERCISE_ENABLED_LABELS[row['enabled']]}")

    def _load_next_card(self, generation, pending, complete_catalog, index=0):
        if generation != self._load_generation:
            return
        if index == len(pending):
            self._first_load_complete = complete_catalog
            return
        row, item = pending[index]
        self._set_card(item, row, self.service.display_eligibility(row["target"]))
        QTimer.singleShot(
            0, lambda: self._load_next_card(generation, pending, complete_catalog, index + 1),
        )

    def cancel_loading(self):
        self._load_generation += 1

    def refresh(self):
        self._load_generation += 1
        generation = self._load_generation
        progressive = self._progressive and not self._first_load_complete
        previous_target = self.target
        detail_open = self.stack.currentIndex() == 1
        selected = {target.exercise for target in self._selected_targets()}
        self.cards.clear()
        self._family_names = {
            family["key"]: family["name"] for family in self.service.catalog.families()
        }
        matching = None
        pending = []
        rows = self.service.browse(
            self.search.text(), self.position.currentData(), latest=True,
            for_display=True, defer_checks=progressive,
        )
        for row in rows:
            item = QListWidgetItem()
            item.setSizeHint(self.cards.gridSize())
            self._set_card(item, row, row["eligibility"])
            self.cards.addItem(item)
            if progressive:
                pending.append((row, item))
            if row["target"].exercise in selected and self.batch_toggle.isChecked():
                item.setSelected(True)
            if previous_target and row["target"].exercise == previous_target.exercise:
                matching = row["target"]
        self.gallery_count.setText(T["gallery_count"].format(count=self.cards.count()))
        self.target = matching
        if detail_open and matching:
            self._show_version()
        else:
            self._show_gallery()
            if matching is None:
                self._show_version()
        self._update_batch_buttons()
        if progressive:
            complete_catalog = not self.search.text() and self.position.currentData() is None
            QTimer.singleShot(
                0, lambda: self._load_next_card(generation, pending, complete_catalog),
            )

    def _show_version(self):
        self.more.setEnabled(self.target is not None)
        if self.target is None:
            show_library_reading(self.reading, self.service, None)
            self.status.clear()
            self.detail_title.clear()
            return
        entry = self.service.target_entry(self.target)
        status = self.service.eligibility(self.target)
        exercise = self.service.get(self.target.exercise)
        self.detail_title.setText(entry["content"]["canonical_name"])
        show_library_reading(self.reading, self.service, self.target, status)
        selected = exercise["selected"]
        if selected is None:
            state = T["state_none"]
        elif selected["reference"] == entry["reference"]:
            state = T["state_latest"]
        else:
            state = T["state_stale"]
        self.status.setText(
            f"{state} · "
            f"{REVIEW_STATE_LABELS[status.reviewed]} · "
            f"{EXERCISE_ENABLED_LABELS[exercise['enabled']]}\n"
            + "；".join(LIBRARY_REASON_LABELS.get(reason, reason) for reason in status.reasons)
        )

    def _prepare_menu(self):
        self.menu.clear()
        self.actions.clear()
        if self.target is None:
            return
        target = deepcopy(self.target)
        try:
            self._show_version()
            enabled = self.service.get(target.exercise)["enabled"]
        except (ValueError, OSError) as exc:
            self.menu.addAction(user_message(str(exc))).setEnabled(False)
            return
        groups = (
            (("select", T["select"]),
             ("disable" if enabled else "enable", T["disable" if enabled else "enable"])),
            tuple((key, T[key]) for key in ("edit", "copy", "image")),
            (("review_events", "审核事件…"), ("record_review", T["record_review"]),
             ("withdraw", T["withdraw"])),
            (("removal", "移除与恢复审核…"),) if self.removals is not None else (),
            (("info", "内容信息…"),),
        )
        for group in groups:
            if not group:
                continue
            if self.actions:
                self.menu.addSeparator()
            for name, text in group:
                action = self.menu.addAction(text)
                self.actions[name] = action
                action.triggered.connect(
                    lambda checked=False, name=name, target=target: self._action(name, target))

    def _show_review_events(self, target):
        entry = self.service.target_entry(target)
        events = self.service.review_events(target)
        records = []

        def recorded_time(event):
            try:
                return datetime.fromisoformat(event["confirmed_at"]).timestamp(), event["id"]
            except (ValueError, TypeError, OSError, OverflowError):
                return float("-inf"), event["id"]

        for event in sorted(events, key=recorded_time, reverse=True):
            attachment = event["attachment"]
            reviewer = {**REVIEWER_TYPE_LABELS, "user": "用户"}.get(
                event["reviewer_type"], "未记录")
            answer = (f"答复原件：{attachment['original_name']}\n"
                      f"保存位置：{attachment.get('path') or '未记录'}\n"
                      f"原件 SHA-256：{attachment.get('sha256') or '未记录'}"
                      if attachment else "答复原件：未附原件")
            records.append(
                f"{T[event['event_type']]}\n"
                f"记录时间：{event['confirmed_at'] or '未知'}\n"
                f"实际审核时间：{event['reviewed_at'] or '未知'}\n"
                f"审核者：{reviewer}\n"
                f"来源：{event['review_source']}\n原始备注：\n{event['note']}\n{answer}")
        reference = entry["reference"]
        title = (f"审核事件 · {entry['content']['canonical_name']} · "
                 f"{reference['id']} v{reference['version']}")
        text = "\n\n".join(records) if records else "当前内容版本暂无审核事件"
        show_readonly_text(self, title, text)

    def _show_content_info(self, target):
        entry = self.service.target_entry(target)
        exercise = self.service.get(target.exercise)
        status = self.service.eligibility(target)
        classification = entry["content"]["classification"]
        family = classification["family_key"]
        family_names = {row["key"]: row["name"] for row in self.service.catalog.families()}

        def identity(reference):
            return (f"{reference['id']} · v{reference['version']}\nSHA-256：{reference['sha256']}"
                    if reference else "尚未选择内容")

        origin = {"bundled": "程序内置", "override": "本地覆盖", "custom": "自定义"}
        selected_reference = exercise["selected"]["reference"] if exercise["selected"] else None
        lines = [
            f"来源：{origin.get(entry.get('origin', 'bundled'), '本地保存内容')}",
            f"动作族：{family_names.get(family, family or T['standalone'])}",
            f"变体：{VARIANT_LABELS[classification['variant_role']]}",
            f"当前显示内容：{identity(entry['reference'])}",
            f"已选内容：{identity(selected_reference)}",
            f"程序目录版本：{self.service.catalog.version}",
        ]
        retained_catalog = entry.get("provenance", {}).get("catalog_version")
        if retained_catalog:
            lines.append(f"内容保留时目录版本：{retained_catalog}")
        for check in status.image_checks:
            reason = ("校验可用" if check.valid
                      else LIBRARY_REASON_LABELS.get(check.reason, check.reason))
            lines.append(f"图片 {check.index + 1}：{reason}")
        if not status.image_checks:
            lines.append("图片资格：未声明图片")
        show_readonly_text(self, f"内容信息 · {entry['content']['canonical_name']}",
                           "\n\n".join(lines))

    def _confirm(self, text):
        answer = QMessageBox.question(self, T["confirm_title"], text)
        return answer == QMessageBox.StandardButton.Yes

    def _action(self, action, bound_target=None):
        if not self.target:
            return
        target = deepcopy(bound_target if bound_target is not None else self.target)
        try:
            if target != self.target:
                raise ValueError("The displayed content changed.")
            self.service.target_entry(target)
            if action == "review_events":
                self._show_review_events(target)
                return
            if action == "info":
                self._show_content_info(target)
                return
            if action == "removal":
                self._open_removals([target])
                return
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
            elif action == "record_review":
                self.dialog = CatalogReviewDialog(self.service, [target], self)
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
            self._refresh_with_feedback()
            return
        self._refresh_with_feedback()
