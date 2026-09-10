from datetime import datetime, timezone

import pytest

from training_feedback.app import ApplicationContext
from training_feedback.application.exercise_service import ExerciseService
from training_feedback.data.data_root import create_new
from training_feedback.data.exercise_repositories import ExerciseRepository
from training_feedback.data.locator import Locator
from training_feedback.data.plan_repositories import PlanRepository
from training_feedback.data.session_repositories import SessionRepository
from training_feedback.domain.enums import AbortReason, DoseUnit, ExerciseResult, SessionStatus
from training_feedback.domain.models import ActualSet
from training_feedback.domain.plans import PlanAction, PlanDay, PlannedSet, PlanPhase, PlanRevision
from training_feedback.domain.session_controller import SessionController
from training_feedback.ui.home_page import HomePage
from training_feedback.ui.training_page import TrainingPage


class FixedClock:
    def __init__(self, current):
        self.current = current

    def now(self):
        return self.current

    def today(self):
        return self.current.date()


def _active_plan(context):
    exercises = ExerciseRepository(context.database.connection)
    service = ExerciseService(exercises)
    exercise = exercises.resolve("臀桥")
    guidance_id = exercises.get(exercise["id"])["guidance"][0]["id"]
    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": "phase-4-test",
        "reviewed_at": "2026-09-06T00:00:00+00:00",
        "user_approved_at": "2026-09-06T00:00:00+00:00",
    }
    service.submit_for_review(guidance_id)
    service.approve_guidance(guidance_id, review)
    service.activate_guidance(guidance_id)
    plans = PlanRepository(context.database.connection, exercises)
    revision = PlanRevision(
        "执行测试计划",
        "快照测试",
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(
                        1,
                        exercise["id"],
                        PlanPhase.MAIN,
                        (PlannedSet(1, DoseUnit.REPS, 12, per_side=True),),
                        rest_seconds=45,
                    ),
                ),
            ),
        ),
    )
    plan_id, revision_id = plans.create_plan(revision)
    plans.activate_revision(plan_id, revision_id)
    return plans, exercises, plan_id


def test_start_snapshots_plan_and_exercise_facts(tmp_path):
    root = create_new(tmp_path / "data")
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.open(root, locator)
    plans, exercises, plan_id = _active_plan(context)
    clock = FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc))
    sessions = SessionRepository(context.database.connection)
    controller = SessionController(sessions, plans, exercises, clock)

    session = controller.start(plan_id)
    action = session["actions"][0]
    assert session["status"] == "open"
    assert session["training_date"] == "2026-09-06"
    assert action["exercise_name_snapshot"] == "臀桥"
    assert action["body_areas"] == ["臀部", "大腿后侧", "核心"]
    assert action["body_area_snapshots"] == [
        {"name": "臀部", "is_primary": True},
        {"name": "大腿后侧", "is_primary": False},
        {"name": "核心", "is_primary": False},
    ]
    assert action["guidance_revision_id"] is not None
    assert action["sets"][0]["planned_value"] == 12
    assert action["sets"][0]["planned_per_side"] == 1

    exercises.update_metadata(action["exercise_id"], "已改名", "main", "")
    reopened = sessions.get(session["id"])
    assert reopened["actions"][0]["exercise_name_snapshot"] == "臀桥"
    context.close()


def test_only_one_open_or_paused_session_can_exist_and_resume(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    sessions = SessionRepository(context.database.connection)
    controller = SessionController(
        sessions,
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc)),
    )
    first = controller.start(plan_id)
    with pytest.raises(ValueError, match="already exists"):
        controller.start(plan_id)
    resumed = SessionController(
        sessions,
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 7, 1, 59, tzinfo=timezone.utc)),
    ).resume()
    assert resumed["id"] == first["id"]
    assert resumed["training_date"] == "2026-09-06"
    sessions.change_status(
        first["id"],
        SessionStatus.PAUSED,
        datetime(2026, 9, 7, 1, 59, tzinfo=timezone.utc),
    )
    resumed = SessionController(
        sessions,
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 7, 2, 0, tzinfo=timezone.utc)),
    ).resume()
    assert resumed["status"] == "open"
    assert context.database.connection.execute(
        "SELECT event_type FROM session_event WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (first["id"],),
    ).fetchone()[0] == "resume"
    context.close()


def test_results_require_actual_dose_and_finish_transactionally(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    clock = FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc))
    sessions = SessionRepository(context.database.connection)
    controller = SessionController(sessions, plans, exercises, clock)
    session = controller.start(plan_id)
    action = session["actions"][0]
    with pytest.raises(ValueError):
        controller.record_result(action["id"], ExerciseResult.PARTIAL, (None,))
    controller.record_result(action["id"], ExerciseResult.EXCEEDED, (14,), "完成备注")
    with pytest.raises(ValueError, match="cannot be changed"):
        controller.record_result(action["id"], ExerciseResult.COMPLETED)
    finished = controller.finish()
    assert finished["status"] == "completed"
    saved = sessions.get(session["id"])
    assert saved["actions"][0]["result"] == "exceeded"
    assert saved["actions"][0]["note"] == "完成备注"
    assert saved["actions"][0]["sets"][0]["actual_value"] == 14
    context.close()


def test_actual_sets_can_be_fewer_or_more_than_planned_sets(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    source = plans.get_revision(plan_id, plans.get_plan(plan_id)["active_revision_id"])
    revision = PlanRevision(
        source["name"],
        source["purpose"],
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(
                        1,
                        1,
                        PlanPhase.MAIN,
                        (
                            PlannedSet(1, DoseUnit.REPS, 12),
                            PlannedSet(2, DoseUnit.REPS, 12),
                        ),
                    ),
                ),
            ),
        ),
    )
    draft_id = plans.create_draft_revision(plan_id, revision)
    plans.activate_revision(plan_id, draft_id)
    sessions = SessionRepository(context.database.connection)
    controller = SessionController(
        sessions,
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc)),
    )
    session = controller.start(plan_id)
    action = session["actions"][0]
    controller.record_result(action["id"], ExerciseResult.PARTIAL, (10,))
    saved = sessions.get(session["id"])
    assert [
        (item["actual_order"], item["value"], item["unit"], item["per_side"])
        for item in saved["actions"][0]["actual_sets"]
    ] == [(1, 10, "reps", 0)]
    context.close()


def test_actual_set_metadata_is_consistent_in_legacy_projection(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    sessions = SessionRepository(context.database.connection)
    controller = SessionController(
        sessions,
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc)),
    )
    session = controller.start(plan_id)
    action = session["actions"][0]
    controller.record_result(
        action["id"],
        ExerciseResult.PARTIAL,
        actual_sets=(ActualSet(10, DoseUnit.SECONDS, per_side=True),),
    )
    saved = sessions.get(session["id"])
    assert saved["actions"][0]["actual_sets"][0]["unit"] == "seconds"
    assert saved["actions"][0]["actual_sets"][0]["per_side"] == 1
    assert saved["actions"][0]["sets"][0]["actual_unit"] == "seconds"
    assert saved["actions"][0]["sets"][0]["actual_per_side"] == 1
    context.close()


def test_not_completed_keeps_actual_dose_unknown_and_abort_requires_reason(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    clock = FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc))
    sessions = SessionRepository(context.database.connection)
    controller = SessionController(sessions, plans, exercises, clock)
    session = controller.start(plan_id)
    action = session["actions"][0]
    controller.record_result(action["id"], ExerciseResult.NOT_COMPLETED, note="未完成")
    saved = sessions.get(session["id"])
    assert saved["actions"][0]["sets"][0]["actual_value"] is None
    with pytest.raises(ValueError, match="abort reason"):
        controller.abort(None)
    aborted = controller.abort(AbortReason.INSUFFICIENT_TIME, "时间不足")
    assert aborted["status"] == "aborted"
    assert aborted["abort_reason"] == "insufficient_time"
    assert aborted["abort_note"] == "时间不足"
    context.close()


def test_training_page_records_completed_action_and_shows_planned_dose(qt_app, tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    controller = SessionController(
        SessionRepository(context.database.connection),
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc)),
    )
    controller.start(plan_id)
    page = TrainingPage(controller)
    assert "12" in page.planned.text()
    assert "已记录 0/1 项" in page.progress.text()
    page._record(ExerciseResult.COMPLETED)
    assert controller.session["actions"][0]["result"] == "completed"
    assert "已记录 1/1 项" in page.progress.text()
    page.close()
    context.close()


def test_training_page_reveals_actual_dose_before_validating(qt_app, tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    controller = SessionController(
        SessionRepository(context.database.connection),
        plans,
        exercises,
        FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc)),
    )
    controller.start(plan_id)
    page = TrainingPage(controller)

    page._record(ExerciseResult.EXCEEDED)

    assert not page.values.isHidden()
    assert not page.actual_hint.isHidden()
    assert controller.session["actions"][0]["result"] is None

    page.value_edits[0].setText("14")
    page._record(ExerciseResult.EXCEEDED)

    assert controller.session["actions"][0]["result"] == "exceeded"
    assert page.values.isHidden()
    page.close()
    context.close()


def test_home_marks_previous_day_session_after_two_am(qt_app, tmp_path, monkeypatch):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    context.database.connection.execute(
        "INSERT INTO training_session(plan_revision_id, training_date, status, "
        "started_at, updated_at) VALUES "
        "(1, '2026-09-05', 'open', '2026-09-05T23:00:00+00:00', "
        "'2026-09-05T23:00:00+00:00')"
    )
    class CurrentClock:
        def now(self):
            return datetime(2026, 9, 6, 2, 0, tzinfo=timezone.utc)

        def today(self):
            return self.now().date()

    monkeypatch.setattr("training_feedback.ui.home_page.SystemClock", CurrentClock)
    page = HomePage(context)
    assert "前一天的训练尚未完成" in page.status.text()
    page.close()
    context.close()


def test_multiday_session_snapshots_unique_day_and_action_positions(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans, exercises, plan_id = _active_plan(context)
    source = plans.get_revision(plan_id, plans.get_plan(plan_id)["active_revision_id"])
    revised = PlanRevision(
        source["name"],
        source["purpose"],
        (
            PlanDay(
                1,
                "第一天",
                (
                    PlanAction(
                        1,
                        1,
                        PlanPhase.MAIN,
                        (PlannedSet(1, DoseUnit.REPS, 12, note="第一组说明"),),
                        rest_seconds=45,
                        note="动作说明",
                    ),
                ),
            ),
            PlanDay(
                2,
                "第二天",
                (
                    PlanAction(
                        1,
                        1,
                        PlanPhase.MAIN,
                        (PlannedSet(1, DoseUnit.REPS, 8, note="第二组说明"),),
                        rest_seconds=30,
                        note="第二天动作说明",
                    ),
                ),
            ),
        ),
    )
    plans.create_draft_revision(plan_id, revised)
    draft = plans.get_plan(plan_id)["revisions"][-1]
    plans.activate_revision(plan_id, draft["id"])
    repository = SessionRepository(context.database.connection)
    with pytest.raises(ValueError, match="plan day must be selected"):
        repository.create_from_plan(
            draft,
            exercises,
            datetime(2026, 9, 6).date(),
            datetime(2026, 9, 6, tzinfo=timezone.utc),
        )
    session_id = repository.create_from_plan(
        draft,
        exercises,
        datetime(2026, 9, 6).date(),
        datetime(2026, 9, 6, tzinfo=timezone.utc),
        day_order=2,
    )
    session = repository.get(session_id)
    assert session["plan_day_order"] == 2
    assert session["plan_day_name_snapshot"] == "第二天"
    assert session["actions"][0]["phase_snapshot"] == "main"
    assert session["actions"][0]["rest_seconds_snapshot"] == 30
    assert session["actions"][0]["plan_note_snapshot"] == "第二天动作说明"
    assert session["actions"][0]["sets"][0]["plan_note_snapshot"] == "第二组说明"
    assert [(item["plan_day_order"], item["plan_action_order"]) for item in session["actions"]] == [
        (2, 1)
    ]
    context.close()
