from copy import deepcopy
from datetime import datetime, timezone

import pytest
from PySide6.QtCore import QPoint

from tests.test_phase4_sessions import FixedClock, _active_plan
from training_feedback.app import ApplicationContext
from training_feedback.data.handoff import HandoffService, render_markdown
from training_feedback.data.locator import Locator
from training_feedback.domain.enums import DoseUnit, ExerciseResult
from training_feedback.domain.plans import PlanAction, PlanDay, PlannedSet, PlanPhase, PlanRevision
from training_feedback.ui.history_page import HistoryPage
from training_feedback.ui.main_window import MainWindow
from training_feedback.ui.next_day_page import NextDayPage
from training_feedback.ui.plan_revision_diff import render_revision
from training_feedback.ui.training_page import TrainingPage


@pytest.mark.parametrize("values", [(12, 12), (12, 8), (None, None)])
def test_plan_render_keeps_all_set_notes_and_side_without_mutating(values):
    revision = {
        "revision_number": 1, "status": "draft", "purpose": "目的",
        "days": [{"day_order": 1, "name": "训练日", "actions": [{
            "action_order": 1, "exercise_name": "动作", "phase": "main",
            "rest_seconds": 30, "note": "动作原文",
            "sets": [{"set_order": n, "value": value,
                      "unit": "free" if value is None else "reps", "per_side": True,
                      "note": f"  第{n}组原文\r\n保留行尾  "}
                     for n, value in enumerate(values, 1)],
        }]}],
    }
    before = deepcopy(revision)
    text = render_revision(revision)
    for item in revision["days"][0]["actions"][0]["sets"]:
        assert item["note"] in text
        assert f"第 {item['set_order']} 组" in text
    assert text.count("每侧") == 2
    assert "None" not in text
    assert revision == before


def _snapshot_session(tmp_path, *, many_actions=False):
    context = ApplicationContext.create(tmp_path / "data", Locator(tmp_path / "locator.json"))
    plans, exercises, _ = _active_plan(context)
    exercise = exercises.resolve("臀桥")
    if many_actions:
        with context.database.transaction():
            exercises.replace_primary_body_areas(
                exercise["id"], ["臀部", "大腿前侧", "大腿后侧", "核心"]
            )
    actions = tuple(
        PlanAction(n, exercise["id"], PlanPhase.MAIN,
                   (PlannedSet(1, DoseUnit.REPS, 8, True, "数值组原文\n第二行"),),
                   35, "处方动作原文")
        for n in range(1, 12 if many_actions else 2)
    )
    if not many_actions:
        actions += (PlanAction(2, exercise["id"], PlanPhase.COOLDOWN,
                               (PlannedSet(1, DoseUnit.FREE, None, True,
                                           "自由组原文\n按说明执行"),)),)
    plan_id, revision_id = plans.create_plan(PlanRevision(
        "显示验证", "原快照", (PlanDay(1, "一天", actions),)
    ))
    plans.activate_revision(plan_id, revision_id)
    service = context.training_service()
    session = service.start(plan_id)
    return context, service, session, exercise["id"], plan_id, revision_id


def test_session_views_and_markdown_use_frozen_notes_after_reopen(qt_app, tmp_path):
    context, service, session, exercise_id, plan_id, revision_id = _snapshot_session(tmp_path)
    service.record_result(session["actions"][0]["id"], ExerciseResult.COMPLETED)
    service.pause()
    context.exercise_service().update_metadata(exercise_id, "后来的名字", "main", "")
    context.plan_repository().clone_revision(plan_id, revision_id)
    root = context.data_root
    context.close()
    context = ApplicationContext.open(root, Locator(tmp_path / "locator.json"))
    service = context.training_service()
    service.resume()
    page = TrainingPage(service)
    assert "数值组原文\n第二行" in page.planned.text()
    assert "处方动作原文" in page.planned.text()
    page.action_selector.setCurrentIndex(1)
    assert "自由组原文\n按说明执行" in page.planned.text()
    assert "None" not in page.planned.text()
    service.record_result(session["actions"][1]["id"], ExerciseResult.NOT_COMPLETED)
    service.finish()
    evidence = HandoffService(context.database.connection, context.data_root.path).build_evidence()
    original = deepcopy(evidence["sessions"])
    history = HistoryPage(context)
    text = history.details.toPlainText()
    assert "自由组原文\n按说明执行" in text
    assert "数值组原文\n第二行" in text
    assert "处方动作原文" in text
    assert "每侧" in text
    assert "后来的名字" not in text
    markdown = render_markdown(evidence)
    session_markdown = markdown[markdown.index("### 会话"):]
    assert "自由组原文\n按说明执行" in session_markdown
    assert "处方动作原文" in session_markdown
    assert evidence["sessions"] == original
    history.close()
    page.close()
    context.close()


def test_feedback_window_scroll_submit_reopen_and_history_actions(qt_app, tmp_path):
    context, service, session, *_ = _snapshot_session(tmp_path, many_actions=True)
    for action in session["actions"]:
        service.record_result(action["id"], ExerciseResult.COMPLETED)
    session = service.finish()
    clock = FixedClock(datetime(2030, 1, 1, tzinfo=timezone.utc))
    window = MainWindow(context)
    window.show()
    home = window.pages.widget(0)
    home.feedback_service = context.feedback_service(clock)
    home.clock = clock
    home.refresh()
    home._open_feedback()
    page = home.feedback_page
    page.resize(520, 440)
    qt_app.processEvents()
    assert page.isWindow() and page.parent() is home
    assert len(page.groups) == 4
    assert page.height() == 440
    assert page.scroll_area.verticalScrollBar().maximum() > 0
    point = page.submit_button.mapToGlobal(QPoint(0, 0))
    page.scroll_area.verticalScrollBar().setValue(page.scroll_area.verticalScrollBar().maximum())
    qt_app.processEvents()
    assert page.submit_button.mapToGlobal(QPoint(0, 0)) == point
    assert not page.submit_button.visibleRegion().isEmpty()
    page.overall_note.setText("原文" * 100)
    page._submit()
    assert not page.submit_button.isEnabled()
    assert all(group.checkedButton() is None for group in page.groups.values())
    page.close()
    reopened = NextDayPage(context, session, clock, home)
    assert reopened.overall_note.text() == "原文" * 100
    assert reopened.overall_note.isReadOnly()
    assert len(reopened.action_note_buttons) == 11
    history = HistoryPage(context)
    history.resize(520, 440)
    history.show()
    qt_app.processEvents()
    assert not history.export_button.visibleRegion().isEmpty()
    assert history.details.verticalScrollBar().maximum() > 0
    history.close()
    reopened.close()
    window.close()
    context.close()
