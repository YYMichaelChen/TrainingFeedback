"""可复用的动作指导字段、版本选择与差异展示组件。"""

from __future__ import annotations

from copy import deepcopy
from html import escape
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .labels import (
    GUIDANCE_STATUS_LABELS,
    IMAGE_STATUS_LABELS,
    REVIEWER_TYPE_LABELS,
    label,
)

SCALAR_FIELDS = (
    ("purpose", "训练目的"),
    ("starting_position", "起始姿势"),
    ("breathing", "呼吸"),
    ("tempo_or_pacing", "节奏或保持"),
    ("applicability", "适用情况"),
    ("cautions", "注意事项"),
)

LIST_FIELDS = (
    ("primary_body_areas", "指导主要身体部位"),
    ("secondary_body_areas", "指导次要身体部位"),
    ("intended_sensations", "应有感受"),
    ("common_compensations", "常见代偿"),
    ("stop_criteria", "停止条件"),
    ("regressions", "退阶方式"),
    ("progressions", "进阶方式"),
    ("equipment", "所需器械"),
)

CONTENT_FIELDS = (
    ("purpose", "训练目的"),
    ("starting_position", "起始姿势"),
    ("steps", "动作步骤"),
    ("breathing", "呼吸"),
    ("tempo_or_pacing", "节奏或保持"),
    *LIST_FIELDS,
    ("applicability", "适用情况"),
    ("cautions", "注意事项"),
    ("images", "图片"),
)

REVIEWABLE_STATUSES = {"draft", "pending_review", "rejected"}
_SOURCE_ROLE = int(Qt.ItemDataRole.UserRole)
_SOURCE_TEXT_ROLE = _SOURCE_ROLE + 1


def _text_html(value: Any, empty: str = "未填写") -> str:
    if value is None or value == "":
        return f"<span style='color:#666'>{escape(empty)}</span>"
    return escape(str(value)).replace("\n", "<br>")


def _mapping_text(value: dict[str, Any]) -> str:
    visible = [item for item in value.values() if item not in (None, "")]
    return "；".join(str(item) for item in visible) or "未填写"


def _ordered_html(values: Any, empty: str = "未填写") -> str:
    if not isinstance(values, list) or not values:
        return f"<div style='color:#666'>{escape(empty)}</div>"
    rows = []
    for index, value in enumerate(values, start=1):
        text = _mapping_text(value) if isinstance(value, dict) else value
        rows.append(f"<div>{index}. {_text_html(text)}</div>")
    return "".join(rows)


def _steps_html(steps: Any) -> str:
    if not isinstance(steps, list) or not steps:
        return "<div style='color:#666'>未填写</div>"
    rows = []
    for index, step in enumerate(steps, start=1):
        if isinstance(step, dict):
            order = step.get("order", index)
            text = step.get("text", "")
        else:
            order, text = index, step
        rows.append(f"<div>{escape(str(order))}. {_text_html(text)}</div>")
    return "".join(rows)


def _images_html(images: Any) -> str:
    if not isinstance(images, list) or not images:
        return "<div style='color:#666'>未说明图片状态</div>"
    rows = []
    for index, image in enumerate(images, start=1):
        if not isinstance(image, dict):
            rows.append(f"<div>{index}. {_text_html(image)}</div>")
            continue
        status = image.get("status", "missing")
        if status == "missing":
            summary = "暂无可用图片"
        else:
            summary = label(IMAGE_STATUS_LABELS, status)
        details = [summary]
        if image.get("caption"):
            details.append(str(image["caption"]))
        if image.get("path"):
            details.append(str(image["path"]))
        rows.append(f"<div>{index}. {_text_html(' · '.join(details))}</div>")
    return "".join(rows)


def _field_value_html(field: str, value: Any) -> str:
    if field == "steps":
        return _steps_html(value)
    if field == "images":
        return _images_html(value)
    if field in dict(LIST_FIELDS):
        return _ordered_html(value)
    return _text_html(value)


def _review_answer_html(review: dict[str, Any]) -> str:
    """显示受管的审核答复原件位置；旧记录没有该字段时明确说明未保存。"""
    relative = review.get("review_answer_file")
    if not relative:
        return _text_html(None, "未保存原件")
    original = review.get("review_answer_original_name") or ""
    digest = (review.get("review_answer_sha256") or "")[:12]
    parts = [f"数据目录内 {relative}"]
    if original:
        parts.append(f"原始文件名 {original}")
    if digest:
        parts.append(f"SHA-256 {digest}…")
    return _text_html("；".join(parts))


def render_guidance_html(guidance: dict[str, Any] | None) -> str:
    """Render every supported guidance field without exposing raw JSON syntax."""
    if not guidance:
        return "<p>暂无动作指导版本。</p>"
    sections = []
    for field, field_label in CONTENT_FIELDS:
        sections.append(
            f"<h3>{escape(field_label)}</h3>"
            f"<div>{_field_value_html(field, guidance.get(field))}</div>"
        )
    review = guidance.get("review", {})
    if not isinstance(review, dict):
        review = {}
    status = label(GUIDANCE_STATUS_LABELS, review.get("status", "draft"))
    reviewer = label(REVIEWER_TYPE_LABELS, review.get("reviewer_type"))
    sections.extend(
        [
            "<h3>复核记录</h3>",
            f"<div><b>审核状态：</b>{_text_html(status)}</div>",
            f"<div><b>审核人类型：</b>{_text_html(reviewer, '未记录')}</div>",
            f"<div><b>审核来源：</b>{_text_html(review.get('review_source'), '未记录')}</div>",
            f"<div><b>审核备注：</b>{_text_html(review.get('review_note'), '未记录')}</div>",
            f"<div><b>记录的审核时间：</b>{_text_html(review.get('reviewed_at'), '未记录')}</div>",
            "<div><b>用户批准时间：</b>"
            f"{_text_html(review.get('user_approved_at'), '未批准')}</div>",
            "<div><b>审核答复原件：</b>"
            f"{_review_answer_html(review)}</div>",
        ]
    )
    return "".join(sections)


class GuidanceView(QTextBrowser):
    """完整、只读且带中文标签的动作指导视图。"""

    def __init__(self, guidance: dict[str, Any] | None = None, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(False)
        self.setMinimumHeight(240)
        self.set_guidance(guidance)

    def set_guidance(self, guidance: dict[str, Any] | None) -> None:
        self.setHtml(render_guidance_html(guidance))


class GuidanceListEditor(QWidget):
    """逐项编辑字符串列表，保留未修改项目的原始值和顺序。"""

    def __init__(self, values: list[Any] | None = None, parent=None):
        super().__init__(parent)
        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["内容（每行一项，可在单项内换行）"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(105)
        add_button = QPushButton("添加")
        remove_button = QPushButton("删除")
        up_button = QPushButton("上移")
        down_button = QPushButton("下移")
        add_button.clicked.connect(self._add)
        remove_button.clicked.connect(self._remove)
        up_button.clicked.connect(lambda: self._move(-1))
        down_button.clicked.connect(lambda: self._move(1))
        controls = QHBoxLayout()
        controls.addWidget(add_button)
        controls.addWidget(remove_button)
        controls.addWidget(up_button)
        controls.addWidget(down_button)
        controls.addStretch()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        layout.addLayout(controls)
        self.set_items(values or [])

    @staticmethod
    def _display(value: Any) -> str:
        return _mapping_text(value) if isinstance(value, dict) else str(value)

    def set_items(self, values: list[Any]) -> None:
        self.table.setRowCount(0)
        for value in values:
            self._append_item(value)

    def _append_item(self, value: Any = "") -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        text = self._display(value)
        item = QTableWidgetItem(text)
        item.setData(_SOURCE_ROLE, deepcopy(value))
        item.setData(_SOURCE_TEXT_ROLE, text)
        self.table.setItem(row, 0, item)

    def items(self) -> list[Any]:
        result = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            source = item.data(_SOURCE_ROLE)
            if source is not None and item.text() == item.data(_SOURCE_TEXT_ROLE):
                result.append(deepcopy(source))
            else:
                result.append(item.text())
        return result

    def _add(self) -> None:
        self._append_item()
        self.table.setCurrentCell(self.table.rowCount() - 1, 0)
        self.table.editItem(self.table.currentItem())

    def _remove(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _move(self, offset: int) -> None:
        row = self.table.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= self.table.rowCount():
            return
        source = self.table.takeItem(row, 0)
        target_item = self.table.takeItem(target, 0)
        self.table.setItem(row, 0, target_item)
        self.table.setItem(target, 0, source)
        self.table.setCurrentCell(target, 0)


class GuidanceStepsEditor(QWidget):
    def __init__(self, steps: list[Any] | None = None, parent=None):
        super().__init__(parent)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["顺序", "步骤内容"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(125)
        add_button = QPushButton("添加步骤")
        remove_button = QPushButton("删除步骤")
        up_button = QPushButton("上移")
        down_button = QPushButton("下移")
        add_button.clicked.connect(self._add)
        remove_button.clicked.connect(self._remove)
        up_button.clicked.connect(lambda: self._move(-1))
        down_button.clicked.connect(lambda: self._move(1))
        controls = QHBoxLayout()
        for button in (add_button, remove_button, up_button, down_button):
            controls.addWidget(button)
        controls.addStretch()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        layout.addLayout(controls)
        self.set_steps(steps or [])

    def set_steps(self, steps: list[Any]) -> None:
        self.table.setRowCount(0)
        for index, source in enumerate(steps, start=1):
            step = source if isinstance(source, dict) else {"order": index, "text": source}
            row = self.table.rowCount()
            self.table.insertRow(row)
            order_item = QTableWidgetItem(str(step.get("order", index)))
            order_item.setData(_SOURCE_ROLE, deepcopy(source))
            order_item.setData(_SOURCE_TEXT_ROLE, str(step.get("order", index)))
            text_item = QTableWidgetItem(str(step.get("text", "")))
            text_item.setData(_SOURCE_TEXT_ROLE, str(step.get("text", "")))
            self.table.setItem(row, 0, order_item)
            self.table.setItem(row, 1, text_item)

    def steps(self) -> list[Any]:
        result = []
        for row in range(self.table.rowCount()):
            order_item = self.table.item(row, 0)
            text_item = self.table.item(row, 1)
            try:
                order = int(order_item.text())
            except ValueError as exc:
                raise ValueError("Step order must be a positive integer.") from exc
            if order < 1:
                raise ValueError("Step order must be a positive integer.")
            source = order_item.data(_SOURCE_ROLE)
            if (
                source is not None
                and order_item.text() == order_item.data(_SOURCE_TEXT_ROLE)
                and text_item.text() == text_item.data(_SOURCE_TEXT_ROLE)
            ):
                result.append(deepcopy(source))
                continue
            step = deepcopy(source) if isinstance(source, dict) else {}
            step.update({"order": order, "text": text_item.text()})
            result.append(step)
        return result

    def _add(self) -> None:
        self._renumber()
        self.set_steps([*self.steps(), {"order": self.table.rowCount() + 1, "text": ""}])
        self.table.setCurrentCell(self.table.rowCount() - 1, 1)
        self.table.editItem(self.table.currentItem())

    def _remove(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self._renumber()

    def _renumber(self) -> None:
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setText(str(row + 1))

    def _move(self, offset: int) -> None:
        row = self.table.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= self.table.rowCount():
            return
        for column in range(self.table.columnCount()):
            source = self.table.takeItem(row, column)
            target_item = self.table.takeItem(target, column)
            self.table.setItem(row, column, target_item)
            self.table.setItem(target, column, source)
        self._renumber()
        self.table.setCurrentCell(target, 1)


class GuidanceImagesEditor(QWidget):
    def __init__(self, images: list[Any] | None = None, parent=None):
        super().__init__(parent)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["可用状态", "本地路径", "说明"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(115)
        add_button = QPushButton("添加图片记录")
        remove_button = QPushButton("删除图片记录")
        add_button.clicked.connect(self._add)
        remove_button.clicked.connect(self._remove)
        controls = QHBoxLayout()
        controls.addWidget(add_button)
        controls.addWidget(remove_button)
        controls.addStretch()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        layout.addLayout(controls)
        self.set_images(images or [])

    def set_images(self, images: list[Any]) -> None:
        self.table.setRowCount(0)
        for source in images:
            image = source if isinstance(source, dict) else {"status": "missing", "caption": source}
            row = self.table.rowCount()
            self.table.insertRow(row)
            status = QComboBox()
            for value, text in IMAGE_STATUS_LABELS.items():
                status.addItem(text, value)
            status.setCurrentIndex(status.findData(image.get("status", "missing")))
            self.table.setCellWidget(row, 0, status)
            path = QTableWidgetItem("" if image.get("path") is None else str(image.get("path", "")))
            path.setData(_SOURCE_ROLE, deepcopy(source))
            path.setData(_SOURCE_TEXT_ROLE, path.text())
            caption = QTableWidgetItem(str(image.get("caption", "")))
            caption.setData(_SOURCE_TEXT_ROLE, caption.text())
            self.table.setItem(row, 1, path)
            self.table.setItem(row, 2, caption)

    def images(self) -> list[Any]:
        result = []
        for row in range(self.table.rowCount()):
            path_item = self.table.item(row, 1)
            caption_item = self.table.item(row, 2)
            source = path_item.data(_SOURCE_ROLE)
            status = self.table.cellWidget(row, 0).currentData()
            source_status = source.get("status") if isinstance(source, dict) else "missing"
            if (
                source is not None
                and status == source_status
                and path_item.text() == path_item.data(_SOURCE_TEXT_ROLE)
                and caption_item.text() == caption_item.data(_SOURCE_TEXT_ROLE)
            ):
                result.append(deepcopy(source))
                continue
            image = deepcopy(source) if isinstance(source, dict) else {}
            original_path = source.get("path") if isinstance(source, dict) else None
            path = (
                original_path
                if original_path is None and not path_item.text()
                else path_item.text()
            )
            image.update(
                {"status": status, "path": path, "caption": caption_item.text()}
            )
            result.append(image)
        return result

    def _add(self) -> None:
        self.set_images(
            [*self.images(), {"status": "missing", "path": None, "caption": "暂无图片"}]
        )
        self.table.setCurrentCell(self.table.rowCount() - 1, 2)

    def _remove(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)


class GuidanceForm(QWidget):
    """编辑完整 guidance；未触碰的扩展字段和逐项元数据保持原样。"""

    def __init__(self, guidance: dict[str, Any] | None = None, parent=None):
        super().__init__(parent)
        self._source: dict[str, Any] = {}
        self._loaded_scalar_text: dict[str, str] = {}
        self.scalar_edits: dict[str, QPlainTextEdit] = {}
        self.list_editors: dict[str, GuidanceListEditor] = {}
        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        for field, field_label in SCALAR_FIELDS:
            edit = QPlainTextEdit()
            edit.setMinimumHeight(70)
            edit.setMaximumHeight(105)
            self.scalar_edits[field] = edit
            form.addRow(field_label, edit)
        self.steps_editor = GuidanceStepsEditor()
        form.insertRow(2, "动作步骤", self.steps_editor)
        for field, field_label in LIST_FIELDS:
            editor = GuidanceListEditor()
            self.list_editors[field] = editor
            form.addRow(field_label, editor)
        self.images_editor = GuidanceImagesEditor()
        form.addRow("图片及可用状态", self.images_editor)
        self.set_guidance(guidance or {})

    def set_guidance(self, guidance: dict[str, Any]) -> None:
        self._source = deepcopy(guidance)
        for field, _field_label in SCALAR_FIELDS:
            value = guidance.get(field, "")
            self.scalar_edits[field].setPlainText(value if isinstance(value, str) else str(value))
            self._loaded_scalar_text[field] = self.scalar_edits[field].toPlainText()
        self.steps_editor.set_steps(guidance.get("steps", []))
        for field, _field_label in LIST_FIELDS:
            values = guidance.get(field, [])
            self.list_editors[field].set_items(values if isinstance(values, list) else [])
        images = guidance.get("images", [])
        self.images_editor.set_images(images if isinstance(images, list) else [])

    def guidance(self) -> dict[str, Any]:
        result = deepcopy(self._source)
        for field, edit in self.scalar_edits.items():
            text = edit.toPlainText()
            # Qt normalizes line separators on load; untouched fields keep their original text.
            if field not in self._source or text != self._loaded_scalar_text[field]:
                result[field] = text
        result["steps"] = self.steps_editor.steps()
        for field, editor in self.list_editors.items():
            result[field] = editor.items()
        result["images"] = self.images_editor.images()
        return result


class GuidanceRevisionCombo(QComboBox):
    """显式选择一个持久化 guidance revision，选项显示版本身份与状态。"""

    def __init__(
        self,
        exercise: dict[str, Any] | None = None,
        *,
        allowed_statuses: set[str] | None = None,
        selected_revision_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(24)
        self.currentTextChanged.connect(self.setToolTip)
        self._revisions: dict[int, dict[str, Any]] = {}
        if exercise is not None:
            self.set_revisions(exercise, allowed_statuses, selected_revision_id)

    def set_revisions(
        self,
        exercise: dict[str, Any],
        allowed_statuses: set[str] | None = None,
        selected_revision_id: int | None = None,
    ) -> None:
        self.clear()
        self._revisions = {}
        active_id = exercise.get("active_guidance_revision_id")
        for revision in exercise.get("guidance", []):
            review = revision.get("guidance", {}).get("review", {})
            status = review.get("status", "draft") if isinstance(review, dict) else "draft"
            if allowed_statuses is not None and status not in allowed_statuses:
                continue
            marker = "当前启用" if revision.get("id") == active_id else label(
                GUIDANCE_STATUS_LABELS, status
            )
            revision_id = revision["id"]
            self._revisions[revision_id] = revision
            created_at = revision.get("created_at", "时间未记录")
            provenance = ""
            if revision.get("bundled_content_id") is not None:
                provenance = (
                    f" · 内置内容 {revision['bundled_content_id']} "
                    f"v{revision.get('bundled_content_version', '?')}"
                )
            self.addItem(
                f"版本 {revision.get('revision_number', '?')} · {marker} · "
                f"{created_at}{provenance}",
                revision_id,
            )
        preferred = selected_revision_id
        if preferred is None and self.count():
            preferred = self.itemData(self.count() - 1)
        index = self.findData(preferred)
        if index >= 0:
            self.setCurrentIndex(index)

    def selected_revision(self) -> dict[str, Any] | None:
        return self._revisions.get(self.currentData())


def active_revision(exercise: dict[str, Any]) -> dict[str, Any] | None:
    active_id = exercise.get("active_guidance_revision_id")
    return next(
        (revision for revision in exercise.get("guidance", []) if revision.get("id") == active_id),
        None,
    )


def active_revision_text(exercise: dict[str, Any]) -> str:
    revision = active_revision(exercise)
    if revision is None:
        return "当前启用指导：无"
    return f"当前启用指导：版本 {revision.get('revision_number', '?')}"


def draft_revisions_text(exercise: dict[str, Any]) -> str:
    descriptions = []
    for revision in exercise.get("guidance", []):
        status = revision.get("guidance", {}).get("review", {}).get("status", "draft")
        if status in REVIEWABLE_STATUSES:
            descriptions.append(
                f"版本 {revision.get('revision_number', '?')}（"
                f"{label(GUIDANCE_STATUS_LABELS, status)}）"
            )
    return "可复核草稿：" + ("、".join(descriptions) if descriptions else "无")


def revision_review_text(revision: dict[str, Any] | None) -> str:
    if revision is None:
        return "所选版本复核记录：尚未形成持久化版本"
    review = revision.get("guidance", {}).get("review", {})
    if not isinstance(review, dict):
        review = {}
    values = (
        f"状态：{label(GUIDANCE_STATUS_LABELS, review.get('status', 'draft'))}",
        f"审核人类型：{label(REVIEWER_TYPE_LABELS, review.get('reviewer_type'))}",
        f"来源：{review.get('review_source') or '未记录'}",
        f"备注：{review.get('review_note') or '未记录'}",
        f"记录的审核时间：{review.get('reviewed_at') or '未记录'}",
        f"用户批准时间：{review.get('user_approved_at') or '未批准'}",
    )
    return "所选版本复核记录：" + "；".join(values)


class GuidanceChangesView(QTextBrowser):
    """显示所选版本相对当前 active 版本的内容变更。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)

    def set_revisions(
        self,
        current: dict[str, Any] | None,
        selected: dict[str, Any] | None,
    ) -> None:
        if selected is None:
            self.setHtml("<p>请选择一个指导版本。</p>")
            return
        if current is None:
            self.setHtml("<p>当前没有启用的指导版本；所选版本将作为首个候选版本。</p>")
            return
        if current.get("id") == selected.get("id"):
            self.setHtml("<p>当前显示的是已启用版本。</p>")
            return
        before = current.get("guidance", {})
        after = selected.get("guidance", {})
        changes = []
        for field, field_label in CONTENT_FIELDS:
            if before.get(field) == after.get(field):
                continue
            changes.append(
                f"<h3>{escape(field_label)}</h3>"
                f"<div><b>当前版本：</b><br>{_field_value_html(field, before.get(field))}</div>"
                f"<div><b>所选版本：</b><br>{_field_value_html(field, after.get(field))}</div>"
            )
        if not changes:
            self.setHtml("<p>所选版本与当前启用版本相比没有内容变化。</p>")
            return
        self.setHtml("".join(changes))
