"""启动选择数据根的取消/失败语义：全部使用临时目录与临时 locator。"""

import sqlite3

import pytest

from training_feedback.bootstrap import (
    choose_data_root,
    create_root,
    open_from_locator,
    open_root,
)
from training_feedback.data.data_root import DataRootAccessError, ExpiredDataRootError, create_new
from training_feedback.data.library_root import initialize_library_root
from training_feedback.data.locator import Locator


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


def test_locator_write_failure_rolls_back_new_root(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    bad_locator = Locator(blocker / "locator.json")
    root = tmp_path / "data"

    with pytest.raises(DataRootAccessError):
        create_root(root, bad_locator)

    assert not root.exists()


def test_open_root_refuses_out_of_window_root_and_never_records_locator(tmp_path):
    root = tmp_path / "expired"
    create_new(root)
    initialize_library_root(root)
    with sqlite3.connect(root / "training_feedback.sqlite3") as connection:
        connection.execute("UPDATE schema_migration SET version=21 WHERE version=23")
    before = (root / "training_feedback.sqlite3").read_bytes()
    locator = Locator(tmp_path / "locator.json")

    with pytest.raises(ExpiredDataRootError):
        open_root(root, locator)

    assert locator.load() is None
    assert not (tmp_path / "locator.json").exists()
    assert (root / "training_feedback.sqlite3").read_bytes() == before


def test_open_from_locator_reopens_current_root_and_is_idempotent(tmp_path):
    locator = Locator(tmp_path / "locator.json")
    root = tmp_path / "current"
    context = create_root(root, locator)
    context.close()
    errors = []

    context = open_from_locator(locator, errors.append)
    assert context is not None
    assert errors == []
    assert context.data_root.path == root
    context.close()

    reopened = open_from_locator(locator, errors.append)
    assert reopened is not None
    assert errors == []
    reopened.close()
