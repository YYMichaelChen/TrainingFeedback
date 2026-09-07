"""动作库页：搜索/筛选动作、查看详情、新增动作。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .exercise_detail_page import ExerciseDetailPage
from .exercise_editor import ExerciseEditor
from .labels import GUIDANCE_STATUS_LABELS, label


class ExerciseLibraryPage(QWidget):
    """动作库页：搜索、筛选与新增动作。"""

    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.service = context.exercise_service()
        layout = QVBoxLayout(self)
        title = QLabel("动作库")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        controls = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("按动作名称或别名搜索")
        self.include_inactive = QCheckBox("显示未启用动作")
        controls.addWidget(self.search_edit)
        controls.addWidget(self.include_inactive)
        add_button = QPushButton("添加动作")
        add_button.clicked.connect(self.add_exercise)
        controls.addWidget(add_button)
        layout.addLayout(controls)
        self.exercise_list = QListWidget()
        layout.addWidget(self.exercise_list)
        self.detail_page = None
        self.search_edit.textChanged.connect(self.refresh)
        self.include_inactive.stateChanged.connect(self.refresh)
        self.exercise_list.itemDoubleClicked.connect(self.show_detail)
        self.refresh()

    def refresh(self) -> None:
        self.exercise_list.clear()
        exercises = self.service.list(self.search_edit.text(), self.include_inactive.isChecked())
        for exercise in exercises:
            areas = ", ".join(exercise["primary_areas"])
            completeness = "完整" if exercise["guidance_complete"] else "不完整"
            item = QListWidgetItem(
                f"{exercise['canonical_name']} | {areas or '-'} | "
                f"{completeness} | {label(GUIDANCE_STATUS_LABELS, exercise['guidance_status'])}"
            )
            item.setData(Qt.ItemDataRole.UserRole, exercise["id"])
            self.exercise_list.addItem(item)

    def show_detail(self, item: QListWidgetItem) -> None:
        exercise = self.service.repository.get(item.data(Qt.ItemDataRole.UserRole))
        if exercise is None:
            return
        self.detail_page = ExerciseDetailPage(exercise, self.service, self)
        self.detail_page.setWindowTitle(exercise["canonical_name"])
        self.detail_page.resize(600, 500)
        self.detail_page.show()

    def add_exercise(self) -> None:
        editor = ExerciseEditor(self.service, parent=self)
        if editor.exec() == editor.DialogCode.Accepted:
            self.refresh()
