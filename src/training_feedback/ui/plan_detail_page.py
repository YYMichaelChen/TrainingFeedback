"""计划详情：明确选择版本，核对完整处方、差异及导入时依据。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .guidance_review_page import GuidanceReviewDialog
from .labels import PLAN_STATUS_LABELS, label, user_message
from .plan_activation_preview import PlanActivationPreview
from .plan_editor import PlanEditor
from .plan_revision_diff import render_diff, render_revision


class PlanDetailPage(QWidget):
    """每个操作绑定所选版本；刷新不隐式改为操作最新草稿。"""

    plan_changed = Signal()

    def __init__(
        self, plan: dict, repository, exercise_service=None, parent=None, *,
        selected_revision_id: int | None = None,
    ):
        super().__init__(parent, Qt.WindowType.Window)
        self.plan = plan
        self.repository = repository
        self.exercise_service = exercise_service
        self.setWindowTitle(plan["name"])
        layout = QVBoxLayout(self)
        self.title = QLabel(plan["name"])
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.title.setWordWrap(True)
        self.title.setObjectName("pageTitle")
        layout.addWidget(self.title)
        self.active_label = QLabel()
        self.active_label.setWordWrap(True)
        layout.addWidget(self.active_label)
        self.revision_selector = QComboBox()
        self.revision_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.revision_selector.setMinimumContentsLength(14)
        layout.addWidget(self.revision_selector)
        tabs = QTabWidget()
        self.content = QPlainTextEdit()
        self.difference = QPlainTextEdit()
        self.import_basis = QPlainTextEdit()
        for title, widget in (
            ("完整处方", self.content), ("与启用版本的差异", self.difference),
            ("导入时依据", self.import_basis),
        ):
            widget.setReadOnly(True)
            tabs.addTab(widget, title)
        layout.addWidget(tabs, 1)
        self.edit_button = QPushButton("编辑所选草稿")
        self.edit_button.clicked.connect(self._edit_draft)
        layout.addWidget(self.edit_button)
        self.clone_button = QPushButton("从所选版本创建草稿")
        self.clone_button.clicked.connect(self._clone_selected_revision)
        layout.addWidget(self.clone_button)
        self.review_status = QLabel()
        self.review_status.setWordWrap(True)
        layout.addWidget(self.review_status)
        self.review_button = QPushButton("审核所选草稿的动作指导")
        self.review_button.clicked.connect(self._review_required_guidance)
        layout.addWidget(self.review_button)
        self.preview_button = QPushButton("预览并启用所选草稿")
        self.preview_button.clicked.connect(self._preview_draft)
        layout.addWidget(self.preview_button)
        self.revision_selector.currentIndexChanged.connect(self._revision_changed)
        if selected_revision_id is None:
            selected_revision_id = plan["active_revision_id"]
            if selected_revision_id is None:
                drafts = [item for item in plan["revisions"] if item["status"] == "draft"]
                if drafts:
                    newest = max(drafts, key=lambda item: item["revision_number"])
                    selected_revision_id = newest["id"]
        self._rebuild_selector(selected_revision_id)
        available = self.screen().availableGeometry()
        self.resize(min(760, available.width() - 40), min(640, available.height() - 60))

    def _selected_revision(self) -> dict | None:
        revision_id = self.revision_selector.currentData()
        return next(
            (item for item in self.plan["revisions"] if item["id"] == revision_id), None
        )

    def _rebuild_selector(self, selected_revision_id: int | None) -> None:
        self.revision_selector.blockSignals(True)
        self.revision_selector.clear()
        for revision in reversed(self.plan["revisions"]):
            self.revision_selector.addItem(
                f"版本 {revision['revision_number']}【"
                f"{label(PLAN_STATUS_LABELS, revision['status'])}】", revision["id"]
            )
        self.revision_selector.setCurrentIndex(
            self.revision_selector.findData(selected_revision_id)
        )
        self.revision_selector.blockSignals(False)
        self._revision_changed()

    def _revision_changed(self) -> None:
        revision = self._selected_revision()
        active = next(
            (item for item in self.plan["revisions"]
             if item["id"] == self.plan["active_revision_id"]), None
        )
        self.active_label.setText(
            f"启用版本：版本 {active['revision_number']}" if active else "启用版本：无"
        )
        is_draft = revision is not None and revision["status"] == "draft"
        self.edit_button.setEnabled(is_draft)
        self.preview_button.setEnabled(is_draft)
        self.review_button.setEnabled(is_draft and self.exercise_service is not None)
        self.clone_button.setEnabled(
            revision is not None and revision["status"] in {"active", "superseded"}
        )
        self.content.setPlainText(render_revision(revision) if revision else "请选择计划版本。")
        self.difference.setPlainText(render_diff(active, revision) if revision else "")
        self.review_status.setText(self._guidance_status_text(revision))
        provenance = (
            self.repository.get_import_for_revision(self.plan["id"], revision["id"])
            if revision else None
        )
        if provenance is None:
            self.import_basis.setPlainText("此版本没有外部导入记录。")
        else:
            session_source = provenance["source_session_id"]
            export_source = provenance["source_export_id"]
            self.import_basis.setPlainText(
                "导入时依据（原文；后续草稿编辑不会改写原始答复）\n"
                f"原始理由：{provenance['rationale']}\n"
                f"来源会话：{session_source if session_source is not None else '未记录'}\n"
                f"来源导出：{export_source if export_source is not None else '未记录'}\n"
                f"托管原文件（相对于当前数据目录）：{provenance['source_path']}"
            )

    def _current_target(self, allowed_statuses: set[str]) -> dict | None:
        displayed = self._selected_revision()
        if displayed is None:
            QMessageBox.information(self, "没有选择版本", "请先选择要操作的计划版本。")
            return None
        current = self.repository.get_revision(self.plan["id"], displayed["id"])
        if current != displayed or current["status"] not in allowed_statuses:
            QMessageBox.warning(
                self, "所选版本不可操作", "所选版本已变化或不支持此操作，请重新核对。"
            )
            self._refresh_plan()
            return None
        return current

    def _edit_draft(self) -> None:
        draft = self._current_target({"draft"})
        if draft is None:
            return
        PlanEditor(self.repository, self.plan, draft, self).exec()
        self._refresh_plan()

    def _preview_draft(self) -> None:
        draft = self._current_target({"draft"})
        if draft is None:
            return
        PlanActivationPreview(self.repository, self.plan, draft, self).exec()
        self._refresh_plan()

    def _clone_selected_revision(self) -> None:
        source = self._current_target({"active", "superseded"})
        if source is None:
            return
        try:
            revision_id = self.repository.clone_revision(self.plan["id"], source["id"])
        except ValueError as exc:
            QMessageBox.warning(self, "无法创建草稿", user_message(str(exc)))
            self._refresh_plan()
            return
        self._refresh_plan(selected_revision_id=revision_id)

    def _review_required_guidance(self) -> None:
        draft = self._current_target({"draft"})
        if draft is None or self.exercise_service is None:
            return
        reviewed = set()
        try:
            for day in draft["days"]:
                for action in day["actions"]:
                    if action["exercise_id"] in reviewed:
                        continue
                    reviewed.add(action["exercise_id"])
                    exercise = self.exercise_service.repository.get(action["exercise_id"])
                    if exercise is None:
                        continue
                    reviewable = [
                        item for item in exercise["guidance"]
                        if item["guidance"].get("review", {}).get("status")
                        in {"draft", "pending_review", "rejected"}
                    ]
                    if not reviewable:
                        continue
                    dialog = GuidanceReviewDialog(
                        self.exercise_service, exercise,
                        selected_revision_id=reviewable[-1]["id"], parent=self,
                    )
                    if not dialog.exec():
                        return
        finally:
            self._refresh_plan()

    def _refresh_plan(self, *, selected_revision_id: int | None = None) -> None:
        if selected_revision_id is None:
            selected_revision_id = self.revision_selector.currentData()
        plan = self.repository.get_plan(self.plan["id"])
        if plan is None:
            self.plan = {**self.plan, "revisions": [], "active_revision_id": None}
        else:
            self.plan = plan
        self.title.setText(self.plan["name"])
        self._rebuild_selector(selected_revision_id)
        self.plan_changed.emit()

    def _guidance_status_text(self, revision: dict | None) -> str:
        if revision is None:
            return "动作指导：未选择计划版本"
        if self.exercise_service is None:
            return "动作指导审核不可用"
        exercise_ids = {
            action["exercise_id"] for day in revision["days"] for action in day["actions"]
        }
        active = sum(
            (exercise := self.exercise_service.repository.get(exercise_id)) is not None
            and exercise.get("active_guidance_revision_id") is not None
            for exercise_id in exercise_ids
        )
        return f"所选版本的动作指导：{active}/{len(exercise_ids)} 个动作已批准并启用"
