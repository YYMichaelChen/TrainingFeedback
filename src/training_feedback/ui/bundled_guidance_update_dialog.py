"""Preview and explicitly deliver application-owned guidance drafts."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .guidance_widgets import GuidanceChangesView, GuidanceView, active_revision
from .labels import localize_dialog_buttons, user_message

_MATCH_LABELS = {
    "bound": "已按稳定内容身份匹配，可创建新版草稿",
    "name_match": "仅按名称找到候选，请确认目标动作",
    "ambiguous": "名称对应多个候选，未自动选择目标",
    "missing": "没有名称候选，请手动选择目标动作",
    "conflict": "名称候选已绑定其他内置动作，未自动选择目标",
    "up_to_date": "此目标已接收同一内置内容版本",
}


class BundledGuidanceUpdateDialog(QDialog):
    """Show every bundled guide while keeping mapping and acceptance explicit."""

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.items = service.preview_bundled_guidance()
        self.items_by_key = {item["exercise_key"]: item for item in self.items}
        self.target_selections = {
            item["exercise_key"]: item.get("target_exercise_id") for item in self.items
        }
        self.accepted_keys: set[str] = set()
        self._rendering = False
        self.setWindowTitle("接收内置动作指导草稿")
        self.resize(860, 680)

        explanation = QLabel(
            "这里仅创建所选内置内容的新草稿，不会覆盖现有指导、改变启用版本或"
            "代表专家审核。未绑定的名称候选和手动映射都需要你在此确认。"
        )
        explanation.setWordWrap(True)

        self.bundle_list = QListWidget()
        self.bundle_list.setMinimumWidth(245)
        for item in self.items:
            status = _MATCH_LABELS.get(item["match_status"], item["match_status"])
            row = QListWidgetItem(
                f"{item['canonical_name']} · 内容 v{item['content_version']}\n{status}"
            )
            row.setData(Qt.ItemDataRole.UserRole, item["exercise_key"])
            self.bundle_list.addItem(row)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        self.identity_label = QLabel()
        self.identity_label.setWordWrap(True)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.target_combo = QComboBox()
        self.target_combo.setMinimumContentsLength(24)
        target_form = QFormLayout()
        target_form.addRow("内置内容身份", self.identity_label)
        target_form.addRow("匹配状态", self.status_label)
        target_form.addRow("本地目标动作", self.target_combo)
        details_layout.addLayout(target_form)

        self.accept_checkbox = QCheckBox("为这个目标动作创建所示内容的新草稿")
        details_layout.addWidget(self.accept_checkbox)
        self.preview_tabs = QTabWidget()
        self.guidance_view = GuidanceView()
        self.changes_view = GuidanceChangesView()
        self.preview_tabs.addTab(self.guidance_view, "内置指导完整预览（未审核）")
        self.preview_tabs.addTab(self.changes_view, "相对当前启用版本的变化")
        details_layout.addWidget(self.preview_tabs, 1)

        splitter = QSplitter()
        splitter.addWidget(self.bundle_list)
        splitter.addWidget(details)
        splitter.setStretchFactor(1, 1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(self.button_box)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(
            "创建所选草稿"
        )
        self.button_box.accepted.connect(self._apply)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.button_box)

        self.bundle_list.currentRowChanged.connect(self._render_current)
        self.target_combo.currentIndexChanged.connect(self._target_changed)
        self.accept_checkbox.toggled.connect(self._acceptance_changed)
        if self.items:
            self.bundle_list.setCurrentRow(0)
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Save).setEnabled(
                False
            )

    def _current_item(self):
        row = self.bundle_list.currentItem()
        if row is None:
            return None
        return self.items_by_key.get(row.data(Qt.ItemDataRole.UserRole))

    def _render_current(self) -> None:
        item = self._current_item()
        if item is None:
            return
        self._rendering = True
        self.identity_label.setText(
            f"{item['content_id']} · 版本 {item['content_version']}"
        )
        self.status_label.setText(
            _MATCH_LABELS.get(item["match_status"], item["match_status"])
        )
        self.guidance_view.set_guidance(item["guidance"])
        self.target_combo.clear()
        self.target_combo.addItem("请选择本地目标动作", None)
        for option in item["target_options"]:
            inactive = "（未启用）" if not option.get("active", True) else ""
            self.target_combo.addItem(
                f"{option['canonical_name']}{inactive}", option["id"]
            )
        target_id = self.target_selections.get(item["exercise_key"])
        index = self.target_combo.findData(target_id)
        self.target_combo.setCurrentIndex(index if index >= 0 else 0)
        up_to_date = item["match_status"] == "up_to_date"
        self.target_combo.setEnabled(not up_to_date)
        self.accept_checkbox.setChecked(item["exercise_key"] in self.accepted_keys)
        self.accept_checkbox.setEnabled(target_id is not None and not up_to_date)
        self._rendering = False
        self._update_changes()

    def _target_changed(self) -> None:
        if self._rendering:
            return
        item = self._current_item()
        if item is None:
            return
        target_id = self.target_combo.currentData()
        self.target_selections[item["exercise_key"]] = target_id
        self.accept_checkbox.setEnabled(target_id is not None)
        if target_id is None:
            self.accepted_keys.discard(item["exercise_key"])
            self._rendering = True
            self.accept_checkbox.setChecked(False)
            self._rendering = False
        self._update_changes()

    def _acceptance_changed(self, checked: bool) -> None:
        if self._rendering:
            return
        item = self._current_item()
        if item is None:
            return
        if checked and self.target_combo.currentData() is not None:
            self.accepted_keys.add(item["exercise_key"])
        else:
            self.accepted_keys.discard(item["exercise_key"])

    def _update_changes(self) -> None:
        item = self._current_item()
        if item is None:
            return
        target_id = self.target_selections.get(item["exercise_key"])
        target = self.service.get(target_id) if target_id is not None else None
        selected = {"id": None, "guidance": item["guidance"]}
        self.changes_view.set_revisions(active_revision(target or {}), selected)

    def _apply(self) -> None:
        selections = {
            key: self.target_selections[key]
            for key in self.accepted_keys
            if self.target_selections.get(key) is not None
        }
        if not selections:
            QMessageBox.information(
                self, "尚未选择", "请勾选至少一个已确认目标的内置指导草稿。"
            )
            return
        try:
            created = self.service.accept_bundled_guidance(selections)
        except ValueError as exc:
            QMessageBox.warning(self, "无法创建草稿", user_message(str(exc)))
            return
        QMessageBox.information(
            self,
            "草稿已创建",
            f"已创建 {len(created)} 个新草稿；现有启用版本和审核事实均未改变。",
        )
        self.accept()
