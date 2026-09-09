"""启动选择数据根的取消/失败语义：全部使用临时目录与临时 locator。"""

import pytest

from training_feedback.app import ApplicationContext
from training_feedback.bootstrap import choose_data_root
from training_feedback.data.data_root import DataRootAccessError, DataRootError
from training_feedback.data.locator import Locator


def test_invalid_selection_is_reported_and_retry_succeeds(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    bad = tmp_path / "missing"
    good = tmp_path / "data"
    selections = iter([(bad, False), (good, True)])
    errors = []

    context = choose_data_root(locator, lambda: next(selections), errors.append)

    assert context is not None
    context.close()
    assert len(errors) == 1
    assert isinstance(errors[0], DataRootError)
    assert locator.load() == good


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


def test_immediate_cancel_returns_none_without_side_effects(tmp_path):
    locator = Locator(tmp_path / "locator.json")

    assert choose_data_root(locator, lambda: None, lambda error: None) is None
    assert locator.load() is None
    assert list(tmp_path.iterdir()) == []


def test_failure_without_error_handler_raises(tmp_path):
    locator = Locator(tmp_path / "locator.json")

    with pytest.raises(DataRootError):
        choose_data_root(locator, lambda: (tmp_path / "missing", False))


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
        ApplicationContext.create(root, bad_locator)

    good_locator = Locator(tmp_path / "locator.json")
    context = choose_data_root(good_locator, lambda: (root, False))

    assert context is not None
    context.close()
    assert good_locator.load() == root
