"""训练计划列表页：查看计划详情、导入外部计划 JSON。"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..data.handoff import HandoffError, HandoffService
from .labels import user_message
from .plan_detail_page import PlanDetailPage


class PlanPage(QWidget):
    """训练计划列表页。"""

    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self.repository = context.plan_repository()
        self.exercise_service = context.exercise_service()
        self.detail_page = None
        layout = QVBoxLayout(self)
        title = QLabel("训练计划")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("查看计划版本及其结构化训练安排。"))
        self.plan_list = QListWidget()
        self.plan_list.itemDoubleClicked.connect(self.show_detail)
        layout.addWidget(self.plan_list)
        controls = QHBoxLayout()
        self.open_button = QPushButton("打开选中的计划")
        self.open_button.clicked.connect(self.open_selected)
        controls.addWidget(self.open_button)
        self.import_button = QPushButton("导入外部计划 JSON")
        self.import_button.clicked.connect(self._import_plan)
        controls.addWidget(self.import_button)
        controls.addStretch()
        layout.addLayout(controls)
        self.refresh()

    def refresh(self) -> None:
        self.plan_list.clear()
        for plan in self.repository.list_plans():
            active = plan["active_revision_id"]
            revision = self.repository.get_revision(plan["id"], active) if active else None
            status = f"启用版本 {revision['revision_number']}" if revision else "没有启用版本"
            item = QListWidgetItem(f"{plan['name']} | {status}")
            item.setData(Qt.ItemDataRole.UserRole, plan["id"])
            self.plan_list.addItem(item)

    def open_selected(self) -> None:
        item = self.plan_list.currentItem()
        if item is not None:
            self.show_detail(item)

    def show_detail(self, item: QListWidgetItem) -> None:
        self.open_plan(item.data(Qt.ItemDataRole.UserRole))

    def open_plan(self, plan_id: int, selected_revision_id: int | None = None) -> None:
        plan = self.repository.get_plan(plan_id)
        if plan is None:
            return
        if self.detail_page is not None:
            self.detail_page.close()
        self.detail_page = PlanDetailPage(
            plan, self.repository, self.exercise_service, self,
            selected_revision_id=selected_revision_id,
        )
        self.detail_page.plan_changed.connect(self.refresh)
        self.detail_page.setWindowTitle(plan["name"])
        self.detail_page.show()

    def _import_plan(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self, "选择外部计划 JSON", "", "JSON 文件 (*.json)"
        )
        if not source:
            return
        try:
            plan_id, revision_id = HandoffService(
                self.context.database.connection, self.context.data_root.path
            ).import_plan_file(Path(source))
        except (HandoffError, OSError) as exc:
            QMessageBox.warning(self, "导入失败", user_message(str(exc)))
            return
        self.refresh()
        self.open_plan(plan_id, selected_revision_id=revision_id)
        QMessageBox.information(
            self,
            "导入完成",
            "外部计划已保存为草稿，并已打开该版本。请检查完整处方、差异和导入时依据，"
            "再明确启用。",
        )
