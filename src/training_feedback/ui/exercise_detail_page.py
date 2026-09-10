"""动作详情页：显式选择并完整展示指导版本。"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .exercise_editor import ExerciseEditor
from .guidance_review_page import GuidanceReviewDialog
from .guidance_widgets import (
    REVIEWABLE_STATUSES,
    GuidanceChangesView,
    GuidanceRevisionCombo,
    GuidanceView,
    active_revision,
    active_revision_text,
    draft_revisions_text,
)
from .labels import CATEGORY_LABELS, label


class ExerciseDetailPage(QDialog):
    """展示动作元数据、版本身份、完整指导、变更与复核入口。"""

    exercise_changed = Signal()

    def __init__(self, exercise: dict, service, parent=None):
        super().__init__(parent)
        self.exercise = exercise
        self.service = service
        content = QWidget()
        layout = QVBoxLayout(content)
        self.title = QLabel(exercise["canonical_name"])
        self.title.setWordWrap(True)
        self.title.setObjectName("pageTitle")
        layout.addWidget(self.title)
        self.category_label = QLabel()
        self.equipment_label = QLabel()
        self.aliases_label = QLabel()
        self.primary_areas_label = QLabel()
        self.secondary_areas_label = QLabel()
        self.status_label = QLabel()
        for metadata_label in (
            self.category_label,
            self.equipment_label,
            self.aliases_label,
            self.primary_areas_label,
            self.secondary_areas_label,
            self.status_label,
        ):
            metadata_label.setWordWrap(True)
            layout.addWidget(metadata_label)

        self.active_revision_label = QLabel()
        self.draft_revisions_label = QLabel()
        self.active_revision_label.setWordWrap(True)
        self.draft_revisions_label.setWordWrap(True)
        layout.addWidget(self.active_revision_label)
        layout.addWidget(self.draft_revisions_label)
        layout.addWidget(QLabel("选择要查看的指导版本"))
        self.guidance_selector = GuidanceRevisionCombo()
        layout.addWidget(self.guidance_selector)
        layout.addWidget(QLabel("所选版本的完整指导与真实复核记录"))
        self.guidance_view = GuidanceView()
        layout.addWidget(self.guidance_view, 3)
        layout.addWidget(QLabel("所选版本相对当前启用版本的内容变化"))
        self.guidance_changes = GuidanceChangesView()
        layout.addWidget(self.guidance_changes, 2)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(content)
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area, 1)

        self.edit_button = QPushButton("编辑动作并创建指导草稿")
        self.edit_button.clicked.connect(self._edit_exercise)
        layout.addWidget(self.edit_button)
        self.toggle_button = QPushButton()
        self.toggle_button.clicked.connect(self._toggle_active)
        layout.addWidget(self.toggle_button)
        self.review_button = QPushButton("复核并批准所选指导版本")
        self.review_button.clicked.connect(self._review_guidance)
        layout.addWidget(self.review_button)
        self.guidance_selector.currentIndexChanged.connect(self._revision_changed)
        self._render_exercise()

    def _render_exercise(self, selected_revision_id: int | None = None) -> None:
        exercise = self.exercise
        self.title.setText(exercise["canonical_name"])
        self.category_label.setText(f"类别：{label(CATEGORY_LABELS, exercise['category'])}")
        self.equipment_label.setText(f"器材概述：{exercise['equipment_summary'] or '无'}")
        self.aliases_label.setText(f"别名：{'、'.join(exercise['aliases']) or '无'}")
        primary = "、".join(
            area["name"] for area in exercise["body_areas"] if area["is_primary"]
        )
        secondary = "、".join(
            area["name"] for area in exercise["body_areas"] if not area["is_primary"]
        )
        self.primary_areas_label.setText(f"主要训练区域：{primary or '无'}")
        self.secondary_areas_label.setText(f"次要训练区域：{secondary or '无'}")
        is_active = bool(exercise["active"])
        self.status_label.setText(f"动作状态：{'已启用' if is_active else '未启用'}")
        self.toggle_button.setText("停用动作" if is_active else "启用动作")
        self.active_revision_label.setText(active_revision_text(exercise))
        self.draft_revisions_label.setText(draft_revisions_text(exercise))
        self.guidance_selector.set_revisions(
            exercise,
            selected_revision_id=selected_revision_id,
        )
        self._revision_changed()

    def _revision_changed(self) -> None:
        selected = self.guidance_selector.selected_revision()
        self.guidance_view.set_guidance(selected["guidance"] if selected else None)
        self.guidance_changes.set_revisions(active_revision(self.exercise), selected)
        status = (
            selected.get("guidance", {}).get("review", {}).get("status", "draft")
            if selected
            else None
        )
        self.review_button.setEnabled(status in REVIEWABLE_STATUSES)

    def _refresh(self, selected_revision_id: int | None = None) -> None:
        refreshed = self.service.repository.get(self.exercise["id"])
        if refreshed is None:
            QMessageBox.warning(self, "动作不存在", "没有找到指定的训练动作。")
            self.close()
            return
        self.exercise = refreshed
        self._render_exercise(selected_revision_id)
        self.exercise_changed.emit()

    def _toggle_active(self) -> None:
        selected_id = self.guidance_selector.currentData()
        self.service.set_active(self.exercise["id"], not bool(self.exercise["active"]))
        self._refresh(selected_id)

    def _edit_exercise(self) -> None:
        dialog = ExerciseEditor(
            self.service, self.exercise, self,
            selected_revision_id=self.guidance_selector.currentData(),
        )
        if dialog.exec():
            self._refresh()

    def _review_guidance(self) -> None:
        selected = self.guidance_selector.selected_revision()
        if selected is None:
            QMessageBox.information(self, "没有指导版本", "请选择一个可复核的指导版本。")
            return
        status = selected.get("guidance", {}).get("review", {}).get("status", "draft")
        if status not in REVIEWABLE_STATUSES:
            QMessageBox.information(
                self,
                "当前版本不可复核",
                "请选择草稿、待审核或已拒绝的指导版本。",
            )
            return
        dialog = GuidanceReviewDialog(
            self.service,
            self.exercise,
            selected_revision_id=selected["id"],
            parent=self,
        )
        if dialog.exec():
            self._refresh(selected["id"])
