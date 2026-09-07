"""动作详情页：展示元数据与指导文本，启停动作、发起指导审核。"""

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from .guidance_review_page import GuidanceReviewDialog
from .labels import CATEGORY_LABELS, GUIDANCE_STATUS_LABELS, label


class ExerciseDetailPage(QWidget):
    """动作详情页：展示元数据与最新/启用版本指导。"""
    def __init__(self, exercise: dict, service, parent=None):
        super().__init__(parent)
        self.exercise = exercise
        self.service = service
        layout = QVBoxLayout(self)
        title = QLabel(exercise["canonical_name"])
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"类别：{label(CATEGORY_LABELS, exercise['category'])}"))
        layout.addWidget(QLabel(f"器材：{exercise['equipment_summary'] or '无'}"))
        layout.addWidget(QLabel(f"别名：{', '.join(exercise['aliases']) or '无'}"))
        areas = ", ".join(area["name"] for area in exercise["body_areas"])
        layout.addWidget(QLabel(f"训练区域：{areas or '无'}"))
        status = "已启用" if exercise["active"] else "未启用"
        self.status_label = QLabel(f"状态：{status}")
        layout.addWidget(self.status_label)
        self.guidance = QPlainTextEdit()
        self.guidance.setReadOnly(True)
        active_id = exercise.get("active_guidance_revision_id")
        selected = next((item for item in exercise["guidance"] if item["id"] == active_id), None)
        latest = (selected or (exercise["guidance"][-1] if exercise["guidance"] else {})).get(
            "guidance", {}
        )
        self.guidance.setPlainText(self._guidance_text(latest))
        layout.addWidget(self.guidance)
        self.toggle_button = QPushButton("停用" if exercise["active"] else "启用")
        self.toggle_button.clicked.connect(self._toggle_active)
        layout.addWidget(self.toggle_button)
        self.review_button = QPushButton("审核动作指导")
        self.review_button.clicked.connect(self._review_guidance)
        layout.addWidget(self.review_button)

    @staticmethod
    def _guidance_text(guidance: dict) -> str:
        if not guidance:
            return "暂无动作指导版本。"
        image_status = guidance.get("images", [{}])[0].get("status", "missing")
        steps = "; ".join(step.get("text", "") for step in guidance.get("steps", []))
        stop_criteria = "; ".join(guidance.get("stop_criteria", []))
        return "\n\n".join(
            [
                f"训练目的：{guidance.get('purpose', '')}",
                f"起始姿势：{guidance.get('starting_position', '')}",
                f"动作步骤：{steps}",
                f"呼吸：{guidance.get('breathing', '')}",
                f"节奏：{guidance.get('tempo_or_pacing', '')}",
                f"停止条件：{stop_criteria}",
                f"图片状态：{label(GUIDANCE_STATUS_LABELS, image_status)}",
            ]
        )

    def _toggle_active(self) -> None:
        self.service.set_active(self.exercise["id"], not bool(self.exercise["active"]))
        # 重新读取而不是手工翻转本地字典，保证界面与数据库一致。
        self.exercise = self.service.repository.get(self.exercise["id"])
        active = bool(self.exercise["active"])
        self.status_label.setText(f"状态：{'已启用' if active else '未启用'}")
        self.toggle_button.setText("停用" if active else "启用")

    def _review_guidance(self) -> None:
        if not self.exercise["guidance"]:
            return
        revision = next(
            (
                item
                for item in reversed(self.exercise["guidance"])
                if item["guidance"].get("review", {}).get("status")
                in {"draft", "pending_review", "rejected"}
            ),
            None,
        )
        if revision is None:
            return
        dialog = GuidanceReviewDialog(self.service, revision["id"], revision["guidance"], self)
        if dialog.exec():
            refreshed = self.service.repository.get(self.exercise["id"])
            self.exercise = refreshed
            self.guidance.setPlainText(
                self._guidance_text(
                    next(
                        (
                            r["guidance"]
                            for r in refreshed["guidance"]
                            if r["id"] == refreshed.get("active_guidance_revision_id")
                        ),
                        refreshed["guidance"][-1]["guidance"],
                    )
                )
            )
