"""计划详情页：版本文本展示、草稿编辑/克隆、指导审核与启用预览。"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from .guidance_review_page import GuidanceReviewDialog
from .plan_activation_preview import PlanActivationPreview
from .plan_editor import PlanEditor
from .plan_revision_diff import render_revision


class PlanDetailPage(QWidget):
    """单个计划的详情页：版本展示、草稿编辑、指导审核与启用。"""
    plan_changed = Signal()

    def __init__(self, plan: dict, repository, exercise_service=None, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.repository = repository
        self.exercise_service = exercise_service
        layout = QVBoxLayout(self)
        title = QLabel(plan["name"])
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        active = plan["active_revision_id"]
        self.active_label = QLabel(
            f"当前版本：{active if active is not None else '无（当前只有草稿）'}"
        )
        layout.addWidget(self.active_label)
        self.content = QPlainTextEdit()
        self.content.setReadOnly(True)
        self.content.setPlainText(self._render(plan))
        layout.addWidget(self.content)
        edit = QPushButton("编辑计划草稿版本")
        edit.clicked.connect(self._edit_draft)
        layout.addWidget(edit)
        clone = QPushButton("从当前版本创建草稿")
        clone.clicked.connect(self._clone_active_revision)
        layout.addWidget(clone)
        review = QPushButton("审核所需的动作指导")
        review.clicked.connect(self._review_required_guidance)
        layout.addWidget(review)
        self.review_status = QLabel(self._guidance_status_text())
        layout.addWidget(self.review_status)
        preview = QPushButton("预览并启用草稿版本")
        preview.clicked.connect(self._preview_draft)
        layout.addWidget(preview)

    def _edit_draft(self) -> None:
        draft = self._latest_draft()
        if draft is None:
            QMessageBox.information(self, "没有草稿", "请先创建计划草稿版本，再进行编辑。")
            return
        dialog = PlanEditor(self.repository, self.plan, draft, self)
        if dialog.exec():
            self._refresh_plan()

    def _preview_draft(self) -> None:
        draft = self._latest_draft()
        if draft is None:
            QMessageBox.information(self, "没有草稿", "请先创建计划草稿版本，再进行预览。")
            return
        dialog = PlanActivationPreview(self.repository, self.plan, draft, self)
        if dialog.exec():
            self._refresh_plan()

    def _clone_active_revision(self) -> None:
        active = next(
            (revision for revision in self.plan["revisions"] if revision["status"] == "active"),
            None,
        )
        if active is None:
            QMessageBox.information(
                self, "没有当前版本", "请先启用一个草稿版本，再从中创建新草稿。"
            )
            return
        self.repository.clone_revision(self.plan["id"], active["id"])
        self._refresh_plan()

    def _review_required_guidance(self) -> None:
        if self.exercise_service is None:
            QMessageBox.warning(self, "功能不可用", "当前无法审核动作指导。")
            return
        draft = self._latest_draft()
        if draft is None:
            QMessageBox.information(
                self, "没有草稿", "请先创建计划草稿版本，再审核动作指导。"
            )
            return
        reviewed = set()
        for day in draft["days"]:
            for action in day["actions"]:
                exercise = self.exercise_service.repository.get(action["exercise_id"])
                if exercise is None or action["exercise_id"] in reviewed:
                    continue
                reviewable = [
                    item
                    for item in exercise["guidance"]
                    if item["guidance"].get("review", {}).get("status")
                    in {"draft", "pending_review", "rejected"}
                ]
                if not reviewable:
                    reviewed.add(action["exercise_id"])
                    continue
                dialog = GuidanceReviewDialog(
                    self.exercise_service,
                    exercise,
                    selected_revision_id=reviewable[-1]["id"],
                    parent=self,
                )
                if not dialog.exec():
                    return
                reviewed.add(action["exercise_id"])
        self._refresh_plan()

    def _refresh_plan(self) -> None:
        self.plan = self.repository.get_plan(self.plan["id"])
        active = self.plan["active_revision_id"]
        self.active_label.setText(
            f"当前版本：{active if active is not None else '无（当前只有草稿）'}"
        )
        self.content.setPlainText(self._render(self.plan))
        self.review_status.setText(self._guidance_status_text())
        self.plan_changed.emit()

    def _guidance_status_text(self) -> str:
        if self.exercise_service is None:
            return "动作指导审核不可用"
        draft = self._latest_draft()
        if draft is None:
            return "动作指导审核：没有草稿版本"
        exercise_ids = {
            action["exercise_id"]
            for day in draft["days"]
            for action in day["actions"]
        }
        active = sum(
            (exercise := self.exercise_service.repository.get(exercise_id)) is not None
            and exercise.get("active_guidance_revision_id") is not None
            for exercise_id in exercise_ids
        )
        return f"动作指导审核：{active}/{len(exercise_ids)} 个动作已批准并启用"

    def _latest_draft(self) -> dict | None:
        return next(
            (
                revision
                for revision in reversed(self.plan["revisions"])
                if revision["status"] == "draft"
            ),
            None,
        )

    @staticmethod
    def _render(plan: dict) -> str:
        return "\n\n".join(render_revision(revision) for revision in plan["revisions"])
