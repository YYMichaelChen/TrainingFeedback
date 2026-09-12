import sqlite3
from datetime import datetime, timezone

import pytest

from tests.test_phase4_sessions import FixedClock, _active_plan
from training_feedback.app import ApplicationContext
from training_feedback.application.feedback_service import FeedbackApplicationService
from training_feedback.data.data_root import create_new
from training_feedback.data.feedback_repositories import FeedbackRepository
from training_feedback.data.locator import Locator
from training_feedback.data.session_repositories import SessionRepository
from training_feedback.domain.enums import ExerciseResult, FeedbackValue
from training_feedback.domain.next_day import (
    can_submit_feedback,
    feedback_areas,
    validate_feedback_values,
)
from training_feedback.domain.session_controller import SessionController
from training_feedback.ui.history_page import HistoryPage
from training_feedback.ui.home_page import HomePage
from training_feedback.ui.next_day_page import NextDayPage


def _completed_session(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    clock = FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc))
    sessions = SessionRepository(context.database.connection)
    controller = SessionController(sessions, plans, exercises, clock)
    session = controller.start(plan_id)
    action = session["actions"][0]
    controller.record_result(action["id"], ExerciseResult.COMPLETED)
    session = controller.finish()
    return context, session


def test_feedback_areas_use_performed_primary_snapshot_only():
    session = {
        "status": "partial",
        "training_date": "2026-09-05",
        "actions": [
            {
                "result": "completed",
                "body_area_snapshots": [
                    {"name": "臀部", "is_primary": True},
                    {"name": "核心", "is_primary": False},
                ],
            },
            {
                "result": "partial",
                "body_area_snapshots": [{"name": "臀部", "is_primary": True}],
            },
            {
                "result": "not_completed",
                "body_area_snapshots": [{"name": "大腿前侧", "is_primary": True}],
            },
            {
                "result": "completed",
                "body_area_snapshots": [{"name": "核心", "is_primary": None}],
            },
        ],
    }
    assert feedback_areas(session) == ("臀部",)
    assert can_submit_feedback(session, datetime(2026, 9, 6).date())
    assert not can_submit_feedback(session, datetime(2026, 9, 5).date())


@pytest.mark.parametrize("status", ["partial", "aborted"])
def test_partial_and_aborted_sessions_allow_feedback_for_performed_work(status):
    session = {
        "status": status,
        "training_date": "2026-09-05",
        "actions": [
            {
                "result": "partial",
                "body_area_snapshots": [{"name": "核心", "is_primary": True}],
            }
        ],
    }
    assert can_submit_feedback(session, datetime(2026, 9, 6).date())
    session["actions"][0]["result"] = "not_completed"
    assert not can_submit_feedback(session, datetime(2026, 9, 6).date())


@pytest.mark.parametrize("value", list(FeedbackValue) + [None])
def test_all_feedback_values_and_unknown_are_valid(value):
    session = {
        "status": "completed",
        "training_date": "2026-09-05",
        "actions": [
            {
                "result": "completed",
                "body_area_snapshots": [{"name": "臀部", "is_primary": True}],
            }
        ],
    }
    assert validate_feedback_values(session, {"臀部": value}) == {"臀部": value}
    with pytest.raises(ValueError, match="exactly"):
        validate_feedback_values(session, {"核心": value})


def test_feedback_submission_is_late_allowed_unique_and_reopenable(tmp_path):
    context, session = _completed_session(tmp_path)
    repository = FeedbackRepository(context.database.connection)
    # Session date is the previous calendar date, not a 24-hour duration.
    pending = repository.list_pending(datetime(2026, 9, 7).date())
    assert [item["id"] for item in pending] == [session["id"]]
    saved = repository.submit(
        session["id"],
        {"臀部": FeedbackValue.SOME_SORENESS},
        "第二天有些酸。",
        datetime(2026, 9, 9).date(),
        datetime(2026, 9, 9, 10, 30, tzinfo=timezone.utc),
    )
    assert saved["overall_note"] == "第二天有些酸。"
    assert saved["areas"][0]["value"] == FeedbackValue.SOME_SORENESS
    assert repository.list_pending(datetime(2026, 9, 10).date()) == []
    with pytest.raises(ValueError, match="already been submitted"):
        repository.submit(
            session["id"],
            {"臀部": FeedbackValue.NO_OBVIOUS_SENSATION},
            "重复提交",
            datetime(2026, 9, 10).date(),
            datetime(2026, 9, 10, tzinfo=timezone.utc),
        )
    reopened = FeedbackRepository(context.database.connection).get(session["id"])
    assert reopened["submitted_at"] == "2026-09-09T10:30:00+00:00"
    context.close()


def test_feedback_submission_rolls_back_header_and_area_rows(tmp_path):
    context, session = _completed_session(tmp_path)
    original = context.database.connection.execute
    calls = 0

    def fail_after_header(sql, parameters=()):
        nonlocal calls
        if "INSERT INTO next_day_feedback_area" in sql:
            calls += 1
            raise RuntimeError("injected feedback failure")
        return original(sql, parameters)

    repository = FeedbackRepository(context.database.connection, execute=fail_after_header)
    with pytest.raises(RuntimeError, match="injected feedback failure"):
        repository.submit(
            session["id"],
            {"臀部": FeedbackValue.SOME_SORENESS},
            "note",
            datetime(2026, 9, 7).date(),
            datetime(2026, 9, 7, tzinfo=timezone.utc),
        )
    assert calls == 1
    assert repository.get(session["id"]) is None
    assert (
        context.database.connection.execute(
            "SELECT COUNT(*) FROM next_day_feedback_area"
        ).fetchone()[0]
        == 0
    )
    context.close()


def test_feedback_unique_race_is_reported_as_duplicate_and_rolled_back(tmp_path):
    context, session = _completed_session(tmp_path)
    original = context.database.connection.execute

    def fail_duplicate(sql, parameters=()):
        if "INSERT INTO next_day_feedback(session_id" in sql:
            raise sqlite3.IntegrityError("UNIQUE constraint failed: next_day_feedback.session_id")
        return original(sql, parameters)

    repository = FeedbackRepository(context.database.connection, execute=fail_duplicate)
    with pytest.raises(ValueError, match="already been submitted"):
        repository.submit(
            session["id"],
            {"臀部": FeedbackValue.SOME_SORENESS},
            "竞态提交",
            datetime(2026, 9, 7).date(),
            datetime(2026, 9, 7, tzinfo=timezone.utc),
        )
    assert repository.get(session["id"]) is None
    assert (
        context.database.connection.execute(
            "SELECT COUNT(*) FROM next_day_feedback_area"
        ).fetchone()[0]
        == 0
    )
    context.close()


def test_feedback_application_service_owns_clock_for_submission(tmp_path):
    context, session = _completed_session(tmp_path)
    clock = FixedClock(datetime(2026, 9, 9, 10, 30, tzinfo=timezone.utc))
    service = FeedbackApplicationService(context.feedback_repository(), clock)

    saved = service.submit(session["id"], {"臀部": None}, "通过服务提交")

    assert saved["submitted_at"] == "2026-09-09T10:30:00+00:00"
    assert saved["areas"][0]["value"] is None
    context.close()


def test_note_correction_requires_feedback_for_each_supported_target(tmp_path):
    context, session = _completed_session(tmp_path)
    repository = FeedbackRepository(context.database.connection)
    action_id = session["actions"][0]["id"]

    for target in ("overall_note", f"action_note:{action_id}"):
        with pytest.raises(ValueError, match="before its note is corrected"):
            repository.correct_note(
                session["id"], target, "尚未提交", datetime(2026, 9, 7, tzinfo=timezone.utc)
            )
    with pytest.raises(ValueError, match="supported note"):
        repository.correct_note(
            session["id"], "status", "partial", datetime(2026, 9, 7, tzinfo=timezone.utc)
        )
    context.close()


def test_note_correction_keeps_audit_and_evidence_scope(tmp_path):
    context, session = _completed_session(tmp_path)
    repository = FeedbackRepository(context.database.connection)
    repository.submit(
        session["id"],
        {"臀部": None},
        "原始备注",
        datetime(2026, 9, 7).date(),
        datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    repository.correct_note(
        session["id"],
        "overall_note",
        "修正备注",
        datetime(2026, 9, 8, tzinfo=timezone.utc),
    )
    feedback = repository.get(session["id"])
    assert feedback["overall_note"] == "修正备注"
    assert feedback["audit"][0]["old_value"] == "原始备注"
    assert feedback["audit"][0]["new_value"] == "修正备注"
    action_id = session["actions"][0]["id"]
    repository.correct_note(
        session["id"],
        f"action_note:{action_id}",
        "动作修正备注",
        datetime(2026, 9, 8, 1, tzinfo=timezone.utc),
    )
    history = repository.history()[0]
    assert history["actions"][0]["note"] == "动作修正备注"
    assert history["feedback"]["audit"][1]["target"] == f"action_note:{action_id}"
    with pytest.raises(ValueError, match="supported note"):
        repository.correct_note(
            session["id"], "status", "partial", datetime(2026, 9, 8, tzinfo=timezone.utc)
        )
    context.close()


def test_home_feedback_entry_is_gated_by_calendar_date(qt_app, tmp_path):
    context, _session = _completed_session(tmp_path)

    class FeedbackClock:
        current_date = datetime(2026, 9, 6).date()

        def today(self):
            return self.current_date

        def now(self):
            return datetime.combine(self.current_date, datetime.min.time(), timezone.utc)

    clock = FeedbackClock()
    page = HomePage(context, clock=clock)
    assert not page.feedback_button.isEnabled()
    assert not page.feedback_selector.isVisible()

    clock.current_date = datetime(2026, 9, 7).date()
    page.refresh()
    assert page.feedback_button.isEnabled()
    page.close()
    context.close()


def test_next_day_page_submits_and_then_becomes_read_only(qt_app, tmp_path):
    context, session = _completed_session(tmp_path)

    class FeedbackClock:
        def today(self):
            return datetime(2026, 9, 7).date()

        def now(self):
            return datetime(2026, 9, 7, 12, tzinfo=timezone.utc)

    page = NextDayPage(context, session, FeedbackClock())
    assert set(page.groups) == {"臀部"}
    assert page.submit_button.isEnabled()
    assert not next(iter(page.action_note_buttons.values())).isVisible()
    page._submit()
    assert not page.submit_button.isEnabled()
    assert page.overall_note.isReadOnly()
    assert not next(iter(page.action_note_buttons.values())).isHidden()
    assert (
        context.database.connection.execute("SELECT COUNT(*) FROM next_day_feedback").fetchone()[0]
        == 1
    )
    page.close()
    context.close()


def test_history_page_renders_session_details(qt_app, tmp_path):
    context, _session = _completed_session(tmp_path)
    page = HistoryPage(context)
    assert page.history_list.count() == 2
    assert "2026-09-06" in page.history_list.item(0).text()
    assert "臀桥" in page.history_list.item(1).text()
    assert "训练日期：2026-09-06" in page.details.toPlainText()
    page.close()
    context.close()


def test_history_details_use_refresh_snapshot_without_reloading_history(qt_app, tmp_path):
    context, _session = _completed_session(tmp_path)
    page = HistoryPage(context)
    page.service.history = lambda: pytest.fail("history should not reload on selection")

    page.history_list.setCurrentRow(1)

    assert "臀桥" in page.details.toPlainText()
    page.close()
    context.close()


def test_history_uses_session_snapshots_after_catalog_change(tmp_path):
    context, session = _completed_session(tmp_path)
    action = session["actions"][0]
    context.database.connection.execute(
        "UPDATE exercise SET canonical_name = '已改名' WHERE id = ?", (action["exercise_id"],)
    )
    context.database.connection.execute(
        "UPDATE exercise_body_area SET is_primary = 0 WHERE exercise_id = ?",
        (action["exercise_id"],),
    )
    context.database.connection.commit()
    saved = FeedbackRepository(context.database.connection).history()[0]
    assert saved["actions"][0]["exercise_name_snapshot"] == "臀桥"
    assert saved["actions"][0]["body_area_snapshots"] == [
        {"name": "臀部", "is_primary": True},
        {"name": "大腿后侧", "is_primary": False},
        {"name": "核心", "is_primary": False},
    ]
    context.close()
