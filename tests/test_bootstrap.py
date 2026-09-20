"""启动选择数据根的取消/失败语义与旧根自动转换：全部使用临时目录与临时 locator。"""

from unittest.mock import patch

import pytest
from migration_070_fixtures import create_schema16_baseline

from training_feedback.bootstrap import (
    choose_data_root,
    create_root,
    open_from_locator,
    open_root,
)
from training_feedback.data import migrations
from training_feedback.data.data_root import DataRootAccessError, ExpiredDataRootError, create_new
from training_feedback.data.locator import Locator
from training_feedback.data.root_lock import JOURNAL_FILENAME


def test_cancel_after_failure_creates_nothing_and_keeps_locator(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    selections = iter([(blocked, True), None])
    errors = []

    assert choose_data_root(locator, lambda: next(selections), errors.append) is None
    assert len(errors) == 1
    assert blocked.read_text(encoding="utf-8") == "not a directory"
    assert locator.load() is None


def test_create_in_occupied_directory_is_reported_then_retry_succeeds(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("do not touch", encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    selections = iter([(occupied, True), (empty, True)])
    errors = []

    context = choose_data_root(locator, lambda: next(selections), errors.append)

    assert context is not None
    context.close()
    assert len(errors) == 1
    assert (occupied / "keep.txt").read_text(encoding="utf-8") == "do not touch"
    assert locator.load() == empty


def test_locator_write_failure_is_reported_and_root_remains_openable(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    bad_locator = Locator(blocker / "locator.json")
    root = tmp_path / "data"

    with pytest.raises(DataRootAccessError):
        create_root(root, bad_locator)

    good_locator = Locator(tmp_path / "locator.json")
    context = choose_data_root(good_locator, lambda: (root, False))

    assert context is not None
    context.close()
    assert good_locator.load() == root


def test_open_root_refuses_out_of_window_root_and_never_records_locator(tmp_path):
    root = tmp_path / "expired"
    with patch.object(migrations, "LATEST_SCHEMA_VERSION", 9):
        create_new(root)
    locator = Locator(tmp_path / "locator.json")

    with pytest.raises(ExpiredDataRootError):
        open_root(root, locator)

    assert locator.load() is None
    assert not (tmp_path / "locator.json").exists()
    assert (root / "training_feedback.sqlite3").exists()


def test_open_from_locator_converts_unconverted_root_and_is_idempotent(tmp_path):
    baseline = create_schema16_baseline(tmp_path / "old")
    locator = Locator(tmp_path / "locator.json")
    locator.save(baseline["data_root"])
    errors = []

    context = open_from_locator(locator, errors.append)
    assert context is not None
    assert errors == []
    assert [row["status"] for row in context.sessions.history()] == [
        "paused", "partial", "completed",
    ]
    context.close()

    reopened = open_from_locator(locator, errors.append)
    assert reopened is not None
    assert errors == []
    reopened.close()


def test_open_from_locator_reports_unrecoverable_journal_and_lets_user_choose(tmp_path):
    baseline = create_schema16_baseline(tmp_path / "old")
    root = baseline["data_root"]
    (root / JOURNAL_FILENAME).write_text('{"format": "bogus"}', encoding="utf-8")
    locator = Locator(tmp_path / "locator.json")
    locator.save(root)
    errors = []

    assert open_from_locator(locator, errors.append) is None
    assert len(errors) == 1
    assert "recovery journal" in str(errors[0])
    # 旧根保持原样，用户可改选其他目录。
    assert (root / "training_feedback.sqlite3").exists()
    fresh = tmp_path / "fresh"
    context = choose_data_root(locator, lambda: (fresh, True), errors.append)
    assert context is not None
    context.close()
    assert locator.load() == fresh
