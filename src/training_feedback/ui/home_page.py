"""首页：数据目录与未完成训练状态，开始/恢复训练与次日反馈入口。"""

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..app import ApplicationContext
from ..application import TrainingApplicationService
from ..domain.clock import SystemClock
from ..domain.training import has_previous_day_label
from .labels import SESSION_STATUS_LABELS, label, user_message
from .training_page import TrainingPage


class HomePage(QWidget):
    """首页：聚合当日训练入口与次日反馈入口。"""

    def __init__(self, context: ApplicationContext, parent=None, clock=None):
        super().__init__(parent)
        self.context = context
        self.clock = clock or SystemClock()
        self.feedback_service = context.feedback_service(self.clock)
        layout = QVBoxLayout(self)
        title = QLabel("今天的训练")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel("按自己的节奏练习，留下准确的记录。")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(26, 24, 26, 24)
        self.eyebrow = QLabel("准备开始")
        self.eyebrow.setObjectName("eyebrow")
        hero_layout.addWidget(self.eyebrow)
        self.plan_summary = QLabel()
        self.plan_summary.setTextFormat(Qt.TextFormat.PlainText)
        self.plan_summary.setWordWrap(True)
        self.plan_summary.setObjectName("sectionTitle")
        hero_layout.addWidget(self.plan_summary)
        self.status = QLabel()
        self.status.setWordWrap(True)
        hero_layout.addWidget(self.status)
        hero_layout.addSpacing(12)
        self.start_button = QPushButton("开始今天的训练")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self._start)
        hero_layout.addWidget(self.start_button)
        self.refresh_button = QPushButton("恢复未完成的训练")
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_button.clicked.connect(self._resume)
        hero_layout.addWidget(self.refresh_button)
        layout.addWidget(hero)
        layout.addSpacing(12)
        feedback_card = QFrame()
        feedback_card.setObjectName("card")
        feedback_layout = QVBoxLayout(feedback_card)
        feedback_layout.setContentsMargins(26, 22, 26, 22)
        feedback_title = QLabel("练习之后，听听身体的反馈")
        feedback_title.setObjectName("sectionTitle")
        feedback_title.setWordWrap(True)
        feedback_layout.addWidget(feedback_title)
        feedback_hint = QLabel("次日记录相关部位的感受。没有填写的内容会保留为未知。")
        feedback_hint.setObjectName("muted")
        feedback_hint.setWordWrap(True)
        feedback_layout.addWidget(feedback_hint)
        self.feedback_button = QPushButton("填写次日反馈")
        self.feedback_button.clicked.connect(self._open_feedback)
        self.feedback_selector = QComboBox()
        self.feedback_selector.setVisible(False)
        feedback_layout.addWidget(self.feedback_selector)
        feedback_layout.addWidget(self.feedback_button)
        layout.addWidget(feedback_card)
        self.refresh()
        layout.addStretch()

    def refresh(self):
        plans = self.context.plan_repository().list_plans()
        active_plans = [plan for plan in plans if plan["active_revision_id"]]
        self.plan_summary.setText(
            active_plans[0]["name"] if active_plans else "先准备一份训练计划"
        )
        active = self.context.session_repository().get_active()
        if active:
            self.eyebrow.setText("继续练习")
            state_label = "未完成的训练"
            training_date = date.fromisoformat(active["training_date"])
            if has_previous_day_label(training_date, active["status"], self.clock):
                state_label = "前一天的训练尚未完成"
            self.status.setText(
                f"{state_label}：{active['training_date']}（"
                f"{label(SESSION_STATUS_LABELS, active['status'])}）"
            )
            self.start_button.setEnabled(False)
            self.refresh_button.setEnabled(True)
            self.refresh_button.setVisible(True)
            self.start_button.setVisible(False)
        else:
            self.eyebrow.setText("准备开始")
            self.status.setText("没有未完成的训练。")
            self.start_button.setEnabled(True)
            self.refresh_button.setEnabled(False)
            self.refresh_button.setVisible(False)
            self.start_button.setVisible(True)
        pending, submitted = self._feedback_choices()
        choices = pending or submitted
        self.feedback_selector.blockSignals(True)
        self.feedback_selector.clear()
        for session in choices:
            state = "填写" if pending else "查看"
            self.feedback_selector.addItem(
                f"{state} {session['training_date']}（"
                f"{label(SESSION_STATUS_LABELS, session['status'])}）",
                session["id"],
            )
        self.feedback_selector.blockSignals(False)
        self.feedback_selector.setVisible(len(choices) > 1)
        self.feedback_button.setEnabled(bool(choices))
        if pending:
            self.feedback_button.setText("填写次日反馈")
        elif submitted:
            self.feedback_button.setText("查看已提交反馈")
        else:
            self.feedback_button.setText("填写次日反馈")

    def _feedback_choices(self) -> tuple[list, list]:
        """返回（待填写, 已提交）的反馈会话；有待填写的会话时不查已提交的。"""
        pending = self.feedback_service.list_pending()
        submitted = [] if pending else self.feedback_service.list_submitted()
        return pending, submitted

    def _start(self):
        plans = self.context.plan_repository()
        active_plans = [item for item in plans.list_plans() if item["active_revision_id"]]
        if not active_plans:
            self.status.setText("请先启用一个训练计划。")
            return
        if len(active_plans) == 1:
            plan = active_plans[0]
        else:
            names = [item["name"] for item in active_plans]
            name, accepted = QInputDialog.getItem(self, "选择训练计划", "训练计划", names, 0, False)
            if not accepted:
                return
            plan = next(item for item in active_plans if item["name"] == name)
        revision = plans.get_revision(plan["id"], plan["active_revision_id"])
        if revision is None:
            self.status.setText("当前训练计划版本不存在。")
            return
        days = revision["days"]
        if len(days) == 1:
            day_order = days[0]["day_order"]
        else:
            choices = [f"第 {day['day_order']} 天：{day['name']}" for day in days]
            choice, accepted = QInputDialog.getItem(
                self, "选择训练日", "今天执行哪个训练日？", choices, 0, False
            )
            if not accepted:
                return
            day_order = days[choices.index(choice)]["day_order"]
        try:
            service = self.context.training_service()
            session = service.start(plan["id"], day_order)
        except ValueError as exc:
            self.status.setText(user_message(str(exc)))
            return
        self._open_training(session, service)

    def _resume(self):
        service = self.context.training_service()
        try:
            session = service.resume()
        except ValueError as exc:
            self.status.setText(user_message(str(exc)))
            return
        self._open_training(session, service)

    def _open_training(self, session, service: TrainingApplicationService | None = None):
        service = service or self.context.training_service()
        service.load(session)
        self.refresh()
        self.training_page = TrainingPage(service, self)
        page = self.training_page
        page.go_to_first_unfinished()
        page.session_ended.connect(self.refresh)
        page.session_ended.connect(page.close)
        available = page.screen().availableGeometry()
        page.resize(
            max(360, min(840, available.width() - 80)),
            max(400, min(760, available.height() - 80)),
        )
        page.show()

    def _open_feedback(self):
        from .next_day_page import NextDayPage

        pending, submitted = self._feedback_choices()
        choices = pending or submitted
        if not choices:
            self.refresh()
            return
        session_id = self.feedback_selector.currentData()
        session = next((item for item in choices if item["id"] == session_id), choices[0])
        self.feedback_page = NextDayPage(self.context, session, clock=self.clock, parent=self)
        self.feedback_page.submitted.connect(self.refresh)
        self.feedback_page.show()
