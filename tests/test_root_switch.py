"""设置页切换数据根：同进程重建窗口与服务的生命周期回归（全部临时根）。"""

import sqlite3

import pytest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QWidget

from training_feedback.app import ApplicationContext, DataRootSwitcher
from training_feedback.bootstrap import open_from_locator
from training_feedback.data.data_root import DataRootAccessError, InvalidDataRootError
from training_feedback.data.locator import Locator
from training_feedback.domain.enums import DoseUnit
from training_feedback.domain.plans import PlanAction, PlanDay, PlannedSet, PlanPhase, PlanRevision
from training_feedback.ui.main_window import MainWindow
from training_feedback.ui.settings_page import SettingsPage


def _active_plan(context):
    """批准一个动作的指导并创建已启用计划，返回 plan_id（与 phase4 测试同法）。"""
    exercises = context.exercise_service()
    exercise = exercises.repository.resolve("臀桥")
    guidance_id = exercises.repository.get(exercise["id"])["guidance"][0]["id"]
    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": "root-switch-test",
        "reviewed_at": "2026-09-09T00:00:00+00:00",
        "user_approved_at": "2026-09-09T00:00:00+00:00",
    }
    exercises.submit_for_review(guidance_id)
    exercises.approve_guidance(guidance_id, review)
    exercises.activate_guidance(guidance_id)
    plans = context.plan_repository()
    revision = PlanRevision(
        "切换测试计划",
        "切换生命周期回归",
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(
                        1,
                        exercise["id"],
                        PlanPhase.MAIN,
                        (PlannedSet(1, DoseUnit.REPS, 12),),
                        rest_seconds=45,
                    ),
                ),
            ),
        ),
    )
    plan_id, revision_id = plans.create_plan(revision)
    plans.activate_revision(plan_id, revision_id)
    return plan_id


def _started(tmp_path, name="A"):
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.create(tmp_path / name, locator)
    switcher = DataRootSwitcher(context, locator)
    switcher.attach(MainWindow(context))
    return switcher


def _build(context):
    return MainWindow(context)


def test_switch_round_trip_keeps_datasets_separate(qt_app, tmp_path):
    switcher = _started(tmp_path)
    plan_id = _active_plan(switcher.context)
    service = switcher.context.training_service()
    paused = service.start(plan_id)
    service.pause()
    old_context = switcher.context
    old_window = switcher.window
    stale_repository = old_context.session_repository()

    assert switcher.switch(tmp_path / "B", True, _build) is True

    assert switcher.context.data_root.path == tmp_path / "B"
    assert switcher.locator.load() == tmp_path / "B"
    # B 只看到自己的数据集：没有 A 的暂停会话，A 的计划启用也不串库。
    assert switcher.context.session_repository().get_active() is None
    assert switcher.context.plan_repository().list_plans()[0]["active_revision_id"] is None
    # 旧窗口与旧服务不再可操作。
    assert switcher.window is not old_window
    assert old_context.database.connection is None
    with pytest.raises(sqlite3.ProgrammingError):
        stale_repository.get_active()

    assert switcher.switch(tmp_path / "A", False, _build) is True

    active = switcher.context.session_repository().get_active()
    assert active["id"] == paused["id"]
    assert active["status"] == "paused"
    resumed = switcher.context.training_service().resume()
    assert resumed["id"] == paused["id"]
    switcher.context.close()


def test_restart_remembers_last_successful_root(qt_app, tmp_path):
    switcher = _started(tmp_path)
    switcher.switch(tmp_path / "B", True, _build)
    current = switcher.context

    reopened = open_from_locator(switcher.locator)

    assert reopened is not None
    assert reopened.data_root.path == current.data_root.path
    reopened.close()
    switcher.context.close()


def test_same_path_is_noop(qt_app, tmp_path):
    switcher = _started(tmp_path)
    locator_bytes = (tmp_path / "locator.json").read_bytes()

    def forbidden_build(context):
        raise AssertionError("same path must not rebuild the window")

    assert switcher.switch(tmp_path / "A", False, forbidden_build) is False
    assert (tmp_path / "locator.json").read_bytes() == locator_bytes
    switcher.context.close()


def test_invalid_target_keeps_current_root_usable(qt_app, tmp_path):
    switcher = _started(tmp_path)
    window = switcher.window

    with pytest.raises(InvalidDataRootError):
        switcher.switch(tmp_path / "missing", False, _build)

    assert switcher.window is window
    assert switcher.context.session_repository().get_active() is None
    assert switcher.locator.load() == tmp_path / "A"
    switcher.context.close()


def test_candidate_window_failure_rolls_back(qt_app, tmp_path):
    switcher = _started(tmp_path)
    window = switcher.window

    def failing_build(context):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        switcher.switch(tmp_path / "B", True, failing_build)

    assert switcher.window is window
    assert switcher.context.session_repository().get_active() is None
    assert switcher.locator.load() == tmp_path / "A"
    switcher.context.close()


def test_locator_failure_rolls_back_and_candidate_is_released(qt_app, tmp_path, monkeypatch):
    switcher = _started(tmp_path)
    window = switcher.window

    def failing_save(path):
        raise OSError("disk full")

    monkeypatch.setattr(switcher.locator, "save", failing_save)
    with pytest.raises(DataRootAccessError):
        switcher.switch(tmp_path / "B", True, _build)

    assert switcher.window is window
    assert switcher.context.session_repository().get_active() is None
    assert switcher.locator.load() == tmp_path / "A"
    # 候选上下文已关闭：B 可以立即被重新打开使用。
    candidate = ApplicationContext.prepare_candidate(tmp_path / "B", False)
    candidate.close()
    switcher.context.close()


def test_open_session_blocks_switch_until_paused(qt_app, tmp_path):
    switcher = _started(tmp_path)
    plan_id = _active_plan(switcher.context)
    service = switcher.context.training_service()
    service.start(plan_id)

    with pytest.raises(ValueError, match="Pause the active training session"):
        switcher.switch(tmp_path / "B", True, _build)

    service.pause()
    assert switcher.switch(tmp_path / "B", True, _build) is True
    switcher.context.close()


def _hide_all_windows():
    for widget in QApplication.topLevelWidgets():
        widget.hide()


def test_settings_switch_cancel_and_failure_feedback(qt_app, tmp_path, monkeypatch):
    _hide_all_windows()
    context = ApplicationContext.create(tmp_path / "A", Locator(tmp_path / "locator.json"))
    calls = []
    page = SettingsPage(context, switch_request=lambda path, create: calls.append(path) or True)
    assert page.switch_button.text() == "切换到其他数据目录…"

    from training_feedback.ui import settings_page

    class CancelDialog:
        def __init__(self, parent=None):
            pass

        def exec(self):
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(settings_page, "DataRootDialog", CancelDialog)
    page._switch_root()
    assert calls == []

    class AcceptDialog(CancelDialog):
        def exec(self):
            return QDialog.DialogCode.Accepted

        def selected_path(self):
            return tmp_path / "B"

        def creates_new_root(self):
            return True

    monkeypatch.setattr(settings_page, "DataRootDialog", AcceptDialog)

    def failing_request(path, create):
        raise ValueError("Pause the active training session before switching data roots.")

    page.switch_request = failing_request
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    page._switch_root()
    assert warnings and "请先暂停当前训练" in warnings[0][2]
    context.close()


def test_settings_switch_blocked_while_other_window_visible(qt_app, tmp_path, monkeypatch):
    _hide_all_windows()
    context = ApplicationContext.create(tmp_path / "A", Locator(tmp_path / "locator.json"))
    calls = []
    page = SettingsPage(context, switch_request=lambda path, create: calls.append(path) or True)
    other = QWidget()
    other.show()
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    page._switch_root()

    assert calls == []
    assert warnings and "请先保存或关闭其他打开的窗口" in warnings[0][2]
    other.close()
    context.close()
