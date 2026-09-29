"""设置页切换数据根：同进程重建窗口与服务的生命周期回归（全部临时根）。"""

import sqlite3

import pytest
from image_fixtures import png_bytes
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QWidget

from training_feedback.app import DataRootSwitcher, LibraryContext
from training_feedback.data.catalog_builder import build_catalog, source_content
from training_feedback.data.data_root import (
    DataRootAccessError,
    DataRootError,
    ExpiredDataRootError,
    create_new,
)
from training_feedback.data.locator import Locator
from training_feedback.domain.catalog import content_sha256
from training_feedback.ui.main_window import MainWindow
from training_feedback.ui.settings_page import SettingsPage


def _catalog(tmp_path):
    import hashlib

    entries = source_content()
    digest = hashlib.sha256(png_bytes()).hexdigest()
    for entry in entries:
        entry["content"]["guidance"]["images"] = [
            {
                "path": "images/synthetic.png",
                "sha256": digest,
                "status": "available",
                "required": True,
                "caption": "【合成切换测试】非训练图片",
            }
        ]
        entry["sha256"] = content_sha256(entry["content"])
    return build_catalog(
        tmp_path / "program" / "catalog",
        entries=entries,
        assets={"images/synthetic.png": png_bytes()},
    )


def _started(tmp_path, name="A", catalog_path=None):
    locator = Locator(tmp_path / "locator.json")
    context = LibraryContext.create(tmp_path / name, catalog_path=catalog_path)
    locator.save(context.data_root.path)
    switcher = DataRootSwitcher(context, locator)
    switcher.attach(MainWindow(context))
    return switcher


def _build(context):
    return MainWindow(context)


def test_switch_round_trip_keeps_datasets_separate(qt_app, tmp_path):
    switcher = _started(tmp_path)
    old_context = switcher.context
    old_window = switcher.window

    assert switcher.switch(tmp_path / "B", True, _build) is True

    assert switcher.context.data_root.path == tmp_path / "B"
    assert switcher.locator.load() == tmp_path / "B"
    # B 只看到自己的数据集：没有 A 的会话与计划。
    assert switcher.context.sessions.active() is None
    assert switcher.context.plans.active_revisions() == []
    # 旧窗口与旧上下文不再可操作。
    assert switcher.window is not old_window
    assert old_context.database.connection is None
    with pytest.raises(sqlite3.ProgrammingError):
        old_context.sessions.active()

    assert switcher.switch(tmp_path / "A", False, _build) is True
    assert switcher.context.data_root.path == tmp_path / "A"
    switcher.context.close()


def test_switch_rejects_expired_target_without_changing_current_root(qt_app, tmp_path):
    switcher = _started(tmp_path)
    expired = tmp_path / "old"
    create_new(expired)
    with sqlite3.connect(expired / "training_feedback.sqlite3") as connection:
        connection.execute("UPDATE schema_migration SET version=21 WHERE version=23")
    before = (expired / "training_feedback.sqlite3").read_bytes()

    with pytest.raises(ExpiredDataRootError):
        switcher.switch(expired, False, _build)

    assert switcher.context.data_root.path == tmp_path / "A"
    assert switcher.locator.load() == tmp_path / "A"
    assert (expired / "training_feedback.sqlite3").read_bytes() == before
    switcher.context.close()


def test_invalid_target_keeps_current_root_usable(qt_app, tmp_path):
    switcher = _started(tmp_path)
    window = switcher.window

    with pytest.raises(DataRootError):
        switcher.switch(tmp_path / "missing", False, _build)

    assert switcher.window is window
    assert switcher.context.sessions.active() is None
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
    assert switcher.context.sessions.active() is None
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
    assert switcher.context.sessions.active() is None
    assert switcher.locator.load() == tmp_path / "A"
    # 新建候选的所有受管产物已回滚。
    assert not (tmp_path / "B").exists()
    switcher.context.close()


def test_open_session_blocks_switch_until_paused(qt_app, tmp_path):
    catalog = _catalog(tmp_path)
    switcher = _started(tmp_path, catalog_path=catalog)
    from test_070_group_plans import activate, enable

    payload = _payload(switcher.context)
    enable(switcher.context, payload)
    revision = switcher.context.plans.create(payload)
    activate(switcher.context, revision)
    controller = switcher.context.session_controller()
    preview = switcher.context.sessions.preview_start(revision, 1)
    controller.start(revision, 1, expected_preview=preview["token"], user_confirmed=True)

    with pytest.raises(ValueError, match="Pause the active training session"):
        switcher.switch(tmp_path / "B", True, _build)

    controller.pause()
    assert switcher.switch(tmp_path / "B", True, _build) is True
    switcher.context.close()


def _payload(context):
    import json
    from pathlib import Path

    from training_feedback.domain.group_plans import plan_actions

    value = json.loads(
        (Path(__file__).resolve().parents[1] / "docs/contracts/plan-v3.example.json")
        .read_text(encoding="utf-8")
    )
    value["plan"].pop("target_plan_name", None)
    for _day, _item, action in plan_actions(value["plan"]):
        entry = context.catalog.get(action["exercise"]["key"])
        action["content"] = entry["reference"]
        action["classification"] = entry["content"]["classification"]
    return value


def _hide_all_windows():
    for widget in QApplication.topLevelWidgets():
        widget.hide()


def test_settings_switch_cancel_and_failure_feedback(qt_app, tmp_path, monkeypatch):
    _hide_all_windows()
    context = LibraryContext.create(tmp_path / "A")
    calls = []
    page = SettingsPage(context, switch_request=lambda path, create: calls.append(path) or True)
    assert page.switch_button.text() == "切换到其他数据目录…"

    from training_feedback.ui import settings_page

    class CancelDialog:
        def __init__(self, parent=None, **_kwargs):
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
    context = LibraryContext.create(tmp_path / "A")
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
