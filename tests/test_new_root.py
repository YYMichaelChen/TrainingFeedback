"""0.7.7 parent/name proposal and owned creation lifecycle (synthetic roots only)."""

import sqlite3

import pytest

from training_feedback.app import LibraryContext, RootCreation
from training_feedback.application.new_root import (
    InvalidRootNameError,
    NewRootProposal,
    validate_child_name,
)
from training_feedback.bootstrap import create_root
from training_feedback.data.data_root import (
    DataRootAccessError,
    ExistingDataRootError,
    ExpiredDataRootError,
    InvalidDataRootError,
    UnsupportedDataFormatError,
)
from training_feedback.data.locator import Locator
from training_feedback.ui.data_root_dialog import DataRootDialog, suggested_data_root


@pytest.mark.parametrize("name", [
    "", ".", "..", "bad/name", "bad\\name", "C:child", "\\root",
    "CON", "con.txt", "LPT9", "COM¹", "bad?name", "bad:name", "a\x01b",
    "trailing.", "trailing ", "x" * 256,
])
def test_invalid_windows_child_names(name):
    with pytest.raises(InvalidRootNameError):
        validate_child_name(name)


def test_proposal_retains_exact_name_and_previews_child(tmp_path):
    proposal = NewRootProposal(tmp_path, "训练 数据")
    assert proposal.name == "训练 数据"
    assert proposal.target == tmp_path / "训练 数据"
    assert proposal.preview == str(proposal.target)
    assert not proposal.target.exists()
    with pytest.raises(ValueError):
        NewRootProposal(tmp_path / "missing", "valid")


def test_documents_suggestion_uses_system_location(qt_app, tmp_path, monkeypatch):
    from training_feedback.ui import data_root_dialog

    documents = tmp_path / "redirected Documents"
    documents.mkdir()
    monkeypatch.setattr(
        data_root_dialog.QStandardPaths, "writableLocation", lambda _: str(documents)
    )
    assert suggested_data_root() == documents
    dialog = DataRootDialog(suggested_path=suggested_data_root())
    assert dialog.selected_path() == documents / "TrainingFeedbackData"
    assert str(documents / "TrainingFeedbackData") in dialog.preview_label.text()
    assert not (documents / "TrainingFeedbackData").exists()


def test_dialog_preserves_modes_and_cancellation_writes_nothing(qt_app, tmp_path):
    dialog = DataRootDialog(suggested_path=tmp_path)
    dialog.name_edit.setText("custom")
    assert dialog.selected_path() == tmp_path / "custom"
    dialog.open_mode.setChecked(True)
    dialog.path_edit.setText(str(tmp_path))
    assert dialog.selected_path() == tmp_path
    dialog.create_mode.setChecked(True)
    assert dialog.path_edit.text() == str(tmp_path)
    assert dialog.name_edit.text() == "custom"
    dialog.name_edit.setText("CON")
    assert not dialog.ok_button.isEnabled()
    dialog.reject()
    assert not (tmp_path / "custom").exists()


def test_creation_states_and_catalog(tmp_path):
    parent = tmp_path
    target = NewRootProposal(parent, "fresh").target
    creation = RootCreation(target)
    context = creation.prepare()
    try:
        assert context.catalog.list()
        assert context.data_root.path == target
    finally:
        context.close()
    with pytest.raises(ExistingDataRootError):
        RootCreation(target).prepare()
    assert (target / "training_feedback.sqlite3").exists()

    occupied = parent / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(InvalidDataRootError):
        RootCreation(occupied).prepare()
    assert (occupied / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_preexisting_empty_child_is_kept_on_failed_creation(tmp_path, monkeypatch):
    target = tmp_path / "empty"
    target.mkdir()
    def fail_create(cls, path):
        (path / "training_feedback.marker.json").write_text("partial", encoding="utf-8")
        raise OSError("injected")
    monkeypatch.setattr(LibraryContext, "create", classmethod(fail_create))
    with pytest.raises(DataRootAccessError):
        RootCreation(target).prepare()
    assert target.is_dir() and list(target.iterdir()) == []


def test_missing_child_removed_on_failed_creation(tmp_path, monkeypatch):
    target = tmp_path / "created"
    def fail_create(cls, path):
        path.mkdir()
        (path / "training_feedback.marker.json").write_text("partial", encoding="utf-8")
        raise OSError("injected")
    monkeypatch.setattr(LibraryContext, "create", classmethod(fail_create))
    with pytest.raises(DataRootAccessError):
        RootCreation(target).prepare()
    assert not target.exists()


def test_creation_rollback_after_library_initialization_failure(tmp_path, monkeypatch):
    from training_feedback.data import library_root

    target = tmp_path / "library-failure"
    original = library_root.initialize_library_root

    def fail_after_initialize(path):
        original(path)
        raise OSError("injected library failure")

    monkeypatch.setattr(library_root, "initialize_library_root", fail_after_initialize)
    with pytest.raises(DataRootAccessError):
        RootCreation(target).prepare()
    assert not target.exists()


def test_creation_rollback_after_context_construction_failure(tmp_path, monkeypatch):
    target = tmp_path / "context-failure"

    def fail_connect(cls, root, catalog):
        raise RuntimeError("injected context failure")

    monkeypatch.setattr(LibraryContext, "_connect", classmethod(fail_connect))
    with pytest.raises(RuntimeError):
        RootCreation(target).prepare()
    assert not target.exists()


def test_create_locator_failure_restores_empty_child(tmp_path):
    target = tmp_path / "preexisting"
    target.mkdir()
    blocker = tmp_path / "blocker"
    blocker.write_text("no directory", encoding="utf-8")
    locator = Locator(blocker / "locator.json")
    with pytest.raises(Exception):
        create_root(target, locator)
    assert target.is_dir() and list(target.iterdir()) == []


def test_create_rejects_expired_and_future_existing_roots_unchanged(tmp_path):
    for name, version, error in (
        ("expired", 22, ExpiredDataRootError),
        ("future", 999, UnsupportedDataFormatError),
    ):
        target = tmp_path / name
        with LibraryContext.create(target):
            pass
        database = target / "training_feedback.sqlite3"
        with sqlite3.connect(database) as connection:
            connection.execute("UPDATE schema_migration SET version=? WHERE version=23", (version,))
        before = database.read_bytes()
        with pytest.raises(error):
            RootCreation(target).prepare()
        assert database.read_bytes() == before
