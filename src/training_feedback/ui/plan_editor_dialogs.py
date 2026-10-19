"""Problem and source-difference presentation for plan editing."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from ..domain.execution_modes import ALTERNATING_START_LABELS, EXECUTION_MODE_LABELS
from ..error_messages import issue_text
from .compact_widgets import CardList
from .labels import (
    DOSE_UNIT_LABELS,
    EXERCISE_SOURCE_LABELS,
    PLAN_PHASE_LABELS,
    POSITION_LABELS,
    VARIANT_LABELS,
    localize_dialog_buttons,
)
from .labels import GROUP_PLAN_TEXT as T
from .sizing import bind_units, fit_dialog, initial_size


def dialog_buttons(dialog, save):
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    localize_dialog_buttons(buttons)
    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    return buttons


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
    """Show raw-input changes and issues without moving the footer into scrolling."""

    def __init__(self, title, summary, changes, parent=None, *, issues=()):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.changes = tuple(changes)
        self.issues = tuple(issues)
        self._details_loaded = False
        self.layout_body = QVBoxLayout(self)
        summary_label = QLabel(summary)
        summary_label.setTextFormat(Qt.TextFormat.PlainText)
        summary_label.setWordWrap(True)
        self.layout_body.addWidget(summary_label)
        self.toggle = QPushButton("查看本次修改与待完善内容" if self.issues else "查看本次修改")
        self.toggle.setCheckable(True)
        self.toggle.setVisible(bool(self.issues or self.changes))
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

    def _detail_text(self):
        sections = []
        if self.changes:
            sections.append("本次修改（按可保存的原始输入）\n\n" + render_changes(self.changes))
        elif self.issues:
            sections.append("本次修改（按可保存的原始输入）\n\n无")
        if self.issues:
            issue_rows = "\n\n".join(
                f"{index}. {issue_text(issue)}" for index, issue in enumerate(self.issues, 1)
            )
            sections.append("待完善内容\n\n" + issue_rows)
        return "\n\n────────\n\n".join(sections)

    def _toggle_details(self, expanded):
        if expanded and not self._details_loaded:
            self.details.setPlainText(self._detail_text())
            self._details_loaded = True
        self.details.setVisible(expanded)
        subject = "本次修改与待完善内容" if self.issues else "本次修改"
        self.toggle.setText(("收起" if expanded else "查看") + subject)
        self.layout_body.setStretch(3, 0 if expanded else 1)
        initial_size(self, 44, 32 if expanded else 12)
