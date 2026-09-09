"""完整备份恢复回归：合成数据 → 在线备份 → 关闭 → 普通打开流程使用副本。

全部使用临时根与临时 locator；恢复通过选择备份副本实现，不做覆盖式恢复。
"""

import sqlite3
from datetime import date, datetime, timezone

import pytest

from tests.test_phase4_sessions import FixedClock, _active_plan
from training_feedback.app import ApplicationContext
from training_feedback.data import backup as backup_module
from training_feedback.data.backup import BackupError, create_backup
from training_feedback.data.data_root import DATABASE_FILENAME, open_existing
from training_feedback.data.feedback_repositories import FeedbackRepository
from training_feedback.data.handoff import HandoffService
from training_feedback.data.locator import Locator
from training_feedback.data.session_repositories import SessionRepository
from training_feedback.domain.enums import ExerciseResult, FeedbackValue
from training_feedback.domain.session_controller import SessionController

VERBATIM_NOTE = "  保留 原文\t不变  "
VERBATIM_FEEDBACK = "第二天有点酸：右侧更明显。"


def _build_source(tmp_path):
    """构造含计划、已完成/暂停训练、次日反馈、备注原文、占位图与交接文件的源根。"""
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.create(tmp_path / "A", locator)
    plans, exercises, plan_id = _active_plan(context)
    sessions = SessionRepository(context.database.connection)

    clock = FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc))
    controller = SessionController(sessions, plans, exercises, clock)
    completed = controller.start(plan_id)
    action = completed["actions"][0]
    controller.record_result(action["id"], ExerciseResult.COMPLETED, note=VERBATIM_NOTE)
    completed = controller.finish()

    FeedbackRepository(context.database.connection).submit(
        completed["id"],
        {"臀部": FeedbackValue.SOME_SORENESS},
        VERBATIM_FEEDBACK,
        date(2026, 9, 7),
        datetime(2026, 9, 7, 8, 0, tzinfo=timezone.utc),
    )

    later = FixedClock(datetime(2026, 9, 8, 10, 15, tzinfo=timezone.utc))
    paused_controller = SessionController(sessions, plans, exercises, later)
    paused = paused_controller.start(plan_id)
    paused_controller.pause()

    image = context.data_root.path / "exercise-images" / "placeholder.txt"
    image.write_text("动作指导图片占位", encoding="utf-8")
    json_path, markdown_path = HandoffService(
        context.database.connection, context.data_root.path
    ).export()
    return context, plan_id, completed, paused, (json_path, markdown_path)


def test_backup_restores_complete_dataset_through_normal_open(qt_app, tmp_path):
    context, plan_id, completed, paused, exports = _build_source(tmp_path)
    source = context.data_root.path
    destination = tmp_path / "backup"

    # 源库保持打开时走 SQLite 在线备份，备份到明确选择的空目录。
    create_backup(source, destination, context.database.connection)
    context.close()

    # 恢复 = 通过普通“打开”流程选择备份副本。
    restored = ApplicationContext.reopen(destination, Locator(tmp_path / "locator2.json"))

    try:
        sessions = SessionRepository(restored.database.connection)
        # 训练快照与备注原文完整。
        snapshot = sessions.get(completed["id"])
        assert snapshot["status"] == "completed"
        restored_action = snapshot["actions"][0]
        assert restored_action["exercise_name_snapshot"] == "臀桥"
        assert restored_action["note"] == VERBATIM_NOTE
        assert restored_action["sets"][0]["planned_value"] == 12
        # 暂停会话可恢复。
        active = sessions.get_active()
        assert active["id"] == paused["id"] and active["status"] == "paused"
        assert restored.training_service().resume()["id"] == paused["id"]
        # 次日反馈原文完整。
        feedback = FeedbackRepository(restored.database.connection).get(completed["id"])
        assert feedback["overall_note"] == VERBATIM_FEEDBACK
        assert feedback["areas"][0]["value"] == FeedbackValue.SOME_SORENESS
        # 计划版本保持启用且内容不变。
        plans = restored.plan_repository().list_plans()
        custom = next(item for item in plans if item["name"] == "执行测试计划")
        assert custom["active_revision_id"] is not None
        # 资源文件逐字节一致。
        assert (destination / "exercise-images" / "placeholder.txt").read_bytes() == (
            source / "exercise-images" / "placeholder.txt"
        ).read_bytes()
        for exported in exports:
            assert (destination / "exports" / exported.name).read_bytes() == exported.read_bytes()
        # 证据可从副本再次导出。
        again = HandoffService(restored.database.connection, destination).export()
        assert all(path.is_file() for path in again)
    finally:
        restored.close()


def test_backup_file_copy_failure_reports_and_cleans_up(tmp_path, monkeypatch):
    source = tmp_path / "source"
    context = ApplicationContext.create(source, Locator(tmp_path / "locator.json"))
    database_bytes = (source / DATABASE_FILENAME).read_bytes()
    destination = tmp_path / "backup"

    def failing_copy(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(backup_module.shutil, "copy2", failing_copy)
    with pytest.raises(BackupError, match="could not be completed"):
        create_backup(source, destination, context.database.connection)

    # 报告失败、不留半成品、源数据完好。
    assert not destination.exists()
    assert (source / DATABASE_FILENAME).read_bytes() == database_bytes
    context.close()
    open_existing(source)


def test_backup_database_failure_reports_and_source_stays_usable(tmp_path, monkeypatch):
    source = tmp_path / "source"
    context = ApplicationContext.create(source, Locator(tmp_path / "locator.json"))
    destination = tmp_path / "backup"

    def failing_backup(connection, target):
        raise sqlite3.Error("backup io error")

    monkeypatch.setattr(backup_module, "_backup_database", failing_backup)
    with pytest.raises(BackupError, match="could not be completed"):
        create_backup(source, destination, context.database.connection)

    assert not destination.exists()
    # 源连接未被失败备份影响，仍可正常读写。
    assert context.session_repository().get_active() is None
    context.close()
    open_existing(source)
