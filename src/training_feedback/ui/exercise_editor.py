"""动作新增/编辑对话框：元数据表单 + 指导 JSON 编辑（保存生成新草稿版本）。"""

import json

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from ..data.seed.catalog import starter_guidance
from .labels import CATEGORY_LABELS, localize_dialog_buttons, user_message


class ExerciseEditor(QDialog):
    """动作新增/编辑对话框；保存指导时会创建新的草稿版本，而不是原地修改。"""

    def __init__(self, service, exercise: dict | None = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.exercise = exercise
        self.setWindowTitle("编辑动作" if exercise else "添加动作")
        self.name_edit = QLineEdit(exercise["canonical_name"] if exercise else "")
        # 类别是受控取值，用下拉框避免自由文本写入非法类别。
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
        if exercise:
            self.areas_edit.setText(
                ", ".join(area["name"] for area in exercise.get("body_areas", []))
            )
        self.guidance_edit = QPlainTextEdit()
        guidance = (
            exercise["guidance"][-1]["guidance"]
            if exercise and exercise.get("guidance")
            else starter_guidance(self.name_edit.text() or "新动作")
        )
        self.guidance_edit.setPlainText(json.dumps(guidance, ensure_ascii=False, indent=2))
        form = QFormLayout()
        form.addRow("标准名称", self.name_edit)
        form.addRow("类别", self.category_edit)
        form.addRow("器材", self.equipment_edit)
        form.addRow("别名", self.aliases_edit)
        form.addRow("主要训练区域", self.areas_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("动作指导 JSON（保存后会创建新的草稿版本）"))
        layout.addWidget(self.guidance_edit)
        layout.addWidget(buttons)

    def _save(self) -> None:
        try:
            guidance = json.loads(self.guidance_edit.toPlainText())
            if not isinstance(guidance, dict):
                raise ValueError("Guidance JSON must be an object.")
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
                self.service.update_metadata(
                    self.exercise["id"],
                    self.name_edit.text(),
                    self.category_edit.currentData(),
                    self.equipment_edit.text(),
                )
                self.service.add_guidance_draft(self.exercise["id"], guidance)
        except (ValueError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "无法保存动作", user_message(str(exc)))
            return
        self.accept()
