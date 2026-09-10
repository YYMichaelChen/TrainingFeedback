"""动作新增/编辑对话框：元数据与完整指导字段表单。"""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..domain.exercises import custom_guidance_draft
from .guidance_widgets import (
    GuidanceChangesView,
    GuidanceForm,
    GuidanceRevisionCombo,
    active_revision,
    active_revision_text,
    draft_revisions_text,
    revision_review_text,
)
from .labels import CATEGORY_LABELS, localize_dialog_buttons, user_message


class ExerciseEditor(QDialog):
    """保存完整动作字段，并从用户显式选择的版本创建新指导草稿。"""

    def __init__(
        self, service, exercise: dict | None = None, parent=None,
        *, selected_revision_id: int | None = None,
    ):
        super().__init__(parent)
        self.service = service
        self.exercise = exercise
        self.setWindowTitle("编辑动作" if exercise else "添加动作")
        self.resize(720, 760)

        self.name_edit = QLineEdit(exercise["canonical_name"] if exercise else "")
        self.category_edit = QComboBox()
        for value, text in CATEGORY_LABELS.items():
            self.category_edit.addItem(text, value)
        category = exercise["category"] if exercise else "main"
        self.category_edit.setCurrentIndex(self.category_edit.findData(category))
        self.equipment_edit = QLineEdit(exercise["equipment_summary"] if exercise else "")
        aliases = ", ".join(exercise.get("aliases", [])) if exercise else ""
        self.aliases_edit = QLineEdit(aliases)
        self.areas_edit = QLineEdit()
        self.areas_edit.setPlaceholderText("请输入主要训练区域，多个区域用逗号分隔")
        secondary_areas = []
        if exercise:
            self.areas_edit.setText(
                ", ".join(
                    area["name"]
                    for area in exercise.get("body_areas", [])
                    if area["is_primary"]
                )
            )
            secondary_areas = [
                area["name"]
                for area in exercise.get("body_areas", [])
                if not area["is_primary"]
            ]
        self.secondary_areas_label = QLabel("、".join(secondary_areas) or "无")
        self.secondary_areas_label.setWordWrap(True)

        self.active_revision_label = QLabel(
            active_revision_text(exercise) if exercise else "当前启用指导：无"
        )
        self.draft_revisions_label = QLabel(
            draft_revisions_text(exercise) if exercise else "可复核草稿：保存后创建版本 1"
        )
        self.active_revision_label.setWordWrap(True)
        self.draft_revisions_label.setWordWrap(True)
        self.guidance_selector = (
            GuidanceRevisionCombo(exercise, selected_revision_id=selected_revision_id)
            if exercise else GuidanceRevisionCombo()
        )
        if self.guidance_selector.count() == 0:
            self.guidance_selector.addItem("新动作的初始指导草稿", None)
            self.guidance_selector.setEnabled(False)
        selected = self.guidance_selector.selected_revision()
        self.selected_review_label = QLabel(revision_review_text(selected))
        self.selected_review_label.setWordWrap(True)
        self.guidance_changes = GuidanceChangesView()
        guidance = (
            selected["guidance"]
            if selected is not None
            else custom_guidance_draft(self.name_edit.text() or "新动作")
        )
        self.guidance_form = GuidanceForm(guidance)

        metadata = QFormLayout()
        metadata.addRow("标准名称", self.name_edit)
        metadata.addRow("类别", self.category_edit)
        metadata.addRow("器材概述", self.equipment_edit)
        metadata.addRow("别名", self.aliases_edit)
        metadata.addRow("主要训练区域", self.areas_edit)
        metadata.addRow("保留的次要训练区域", self.secondary_areas_label)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addLayout(metadata)
        content_layout.addWidget(QLabel("指导版本身份"))
        content_layout.addWidget(self.active_revision_label)
        content_layout.addWidget(self.draft_revisions_label)
        content_layout.addWidget(QLabel("选择要作为新草稿来源的指导版本"))
        content_layout.addWidget(self.guidance_selector)
        content_layout.addWidget(self.selected_review_label)
        content_layout.addWidget(QLabel("所选来源版本相对当前启用版本的内容变化"))
        self.guidance_changes.set_revisions(active_revision(exercise or {}), selected)
        content_layout.addWidget(self.guidance_changes)
        guidance_note = QLabel(
            "下方字段来自当前明确选择的版本。保存会创建一个新的未批准草稿，"
            "不会改写或自动批准所选版本。"
        )
        guidance_note.setWordWrap(True)
        content_layout.addWidget(guidance_note)
        content_layout.addWidget(self.guidance_form)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(content)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(self.button_box)
        self.button_box.accepted.connect(self._save)
        self.button_box.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.button_box)
        self.guidance_selector.currentIndexChanged.connect(self._guidance_revision_changed)

    def _guidance_revision_changed(self) -> None:
        revision = self.guidance_selector.selected_revision()
        self.selected_review_label.setText(revision_review_text(revision))
        self.guidance_changes.set_revisions(active_revision(self.exercise or {}), revision)
        if revision is not None:
            self.guidance_form.set_guidance(revision["guidance"])

    def _save(self) -> None:
        try:
            guidance = self.guidance_form.guidance()
            if self.exercise is None:
                exercise_id = self.service.create_exercise(
                    self.name_edit.text(),
                    self.category_edit.currentData(),
                    self.equipment_edit.text(),
                    [
                        (area.strip(), True)
                        for area in self.areas_edit.text().split(",")
                        if area.strip()
                    ],
                    [
                        alias.strip()
                        for alias in self.aliases_edit.text().split(",")
                        if alias.strip()
                    ],
                    guidance,
                )
                self.exercise = self.service.repository.get(exercise_id)
            else:
                self.service.edit_exercise(
                    self.exercise["id"],
                    self.name_edit.text(),
                    self.category_edit.currentData(),
                    self.equipment_edit.text(),
                    [
                        area.strip()
                        for area in self.areas_edit.text().split(",")
                        if area.strip()
                    ],
                    [
                        alias.strip()
                        for alias in self.aliases_edit.text().split(",")
                        if alias.strip()
                    ],
                    guidance,
                )
        except (KeyError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "无法保存动作", user_message(str(exc)))
            return
        self.accept()
