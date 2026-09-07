from datetime import datetime, timezone

from PySide6.QtWidgets import QMessageBox

from tests.test_phase4_sessions import FixedClock, _active_plan
from tests.test_phase5_feedback import _completed_session
from training_feedback.app import ApplicationContext
from training_feedback.data.data_root import create_new
from training_feedback.data.locator import Locator
from training_feedback.data.session_repositories import SessionRepository
from training_feedback.domain.enums import ExerciseResult
from training_feedback.domain.session_controller import SessionController
from training_feedback.ui.home_page import HomePage
from training_feedback.ui.next_day_page import NextDayPage
from training_feedback.ui.training_page import TrainingPage


def test_actual_dose_second_step_and_finish_state_are_explicit(qt_app, tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    controller = SessionController(
        SessionRepository(context.database.connection),
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 8, 10, 15, tzinfo=timezone.utc)),
    )
    controller.start(plan_id)
    page = TrainingPage(controller)

    assert not page.finish_button.isEnabled()
    assert "请先记录全部动作" in page.finish_button.text()

    page._record(ExerciseResult.EXCEEDED)

    assert page.result_button_by_value[ExerciseResult.EXCEEDED].text() == "保存超额完成结果"
    assert "保存超额完成结果" in page.actual_hint.text()

    page.value_edits[0].setText("14")
    page._record(ExerciseResult.EXCEEDED)

    assert page.finish_button.isEnabled()
    assert page.finish_button.text() == "完成训练"
    page.close()
    context.close()


def test_finish_requires_confirmation_before_persisting(qt_app, tmp_path, monkeypatch):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    controller = SessionController(
        SessionRepository(context.database.connection),
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 8, 10, 15, tzinfo=timezone.utc)),
    )
    session = controller.start(plan_id)
    controller.record_result(session["actions"][0]["id"], ExerciseResult.COMPLETED)
    page = TrainingPage(controller)
    ended = []
    page.session_ended.connect(lambda: ended.append(True))

    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.No
    )
    page._finish()
    assert controller.session["status"] == "open"
    assert not ended

    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    page._finish()
    assert controller.session["status"] == "completed"
    assert ended == [True]
    page.close()
    context.close()


def test_starting_training_immediately_updates_home_state(qt_app, tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    _active_plan(context)
    page = HomePage(
        context,
        clock=FixedClock(datetime(2026, 9, 8, 10, 15, tzinfo=timezone.utc)),
    )

    page._start()

    assert not page.start_button.isEnabled()
    assert page.refresh_button.isEnabled()
    assert "未完成的训练" in page.status.text()
    page.training_page.close()
    page.close()
    context.close()


def test_feedback_page_states_unknown_and_submitted_status(qt_app, tmp_path):
    context, session = _completed_session(tmp_path)
    clock = FixedClock(datetime(2026, 9, 8, 12, tzinfo=timezone.utc))
    page = NextDayPage(context, session, clock)

    assert "未选择的部位将保留为未知" in page.submission_status.text()

    page._submit()

    assert "反馈已提交" in page.submission_status.text()
    assert "只读" in page.submission_status.text()
    page.close()
    context.close()
