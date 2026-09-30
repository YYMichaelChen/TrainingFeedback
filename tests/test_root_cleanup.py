"""Deletion tests use only owned synthetic roots; no client or installed app is operated."""

import json
import os
import sqlite3
import subprocess
import sys

import pytest

from training_feedback.application import uninstall_cli
from training_feedback.data import root_cleanup as cleanup
from training_feedback.data.data_root import (
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    MARKER_FILENAME,
    DataRootAccessError,
    create_new,
    inspect_existing,
)
from training_feedback.data.database import Database
from training_feedback.data.library_root import initialize_library_root
from training_feedback.data.locator import Locator
from training_feedback.data.windows_files import BoundTree, FileSafetyError


@pytest.fixture
def policy(tmp_path):
    root = tmp_path / "synthetic-data"
    create_new(root)
    initialize_library_root(root)
    (root / "exports/text.txt").write_bytes(b"  synthetic text\t\r\n  ")
    locator = tmp_path / "profile/locator.json"
    Locator(locator).save(root)
    return cleanup.CleanupPolicy(locator, tmp_path / "program", tmp_path / "home",
                                 (tmp_path / "Windows", tmp_path / "Program Files"))


def root(policy):
    return Locator(policy.locator).load()


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


def test_complete_deletes_exact_root_locator_and_not_external_backup(policy, tmp_path):
    target = root(policy)
    external = tmp_path / "external-backup"
    external.mkdir()
    (external / "keep.txt").write_bytes(b"external untouched")
    other = tmp_path / "other-historical-root"
    other.mkdir()
    (other / "keep.txt").write_bytes(b"not discovered")
    offered = cleanup.offer(policy)
    assert target.exists() and not policy.journal.exists()
    result = cleanup.commit(policy, offered, user_confirmed=True)
    assert result["status"] == "complete"
    assert not target.exists() and not policy.locator.exists() and not policy.journal.exists()
    assert (external / "keep.txt").read_bytes() == b"external untouched"
    assert (other / "keep.txt").read_bytes() == b"not discovered"


def test_cancel_does_not_write_root_locator_or_recovery(policy):
    target = root(policy)
    before, pointer = snapshot(target), policy.locator.read_bytes()
    offered = cleanup.offer(policy)
    assert cleanup.commit(policy, offered, user_confirmed=False)["status"] == "cancelled"
    assert snapshot(target) == before and policy.locator.read_bytes() == pointer
    assert not policy.journal.exists()


@pytest.mark.parametrize("mutation", ["wrong-application", "future-schema", "future-config"])
def test_invalid_or_future_root_is_refused_unchanged(policy, mutation):
    target = root(policy)
    if mutation == "future-schema":
        connection = sqlite3.connect(target / DATABASE_FILENAME)
        with connection:
            connection.execute("INSERT INTO schema_migration VALUES (999, 'synthetic')")
        connection.close()
    else:
        path = target / (MARKER_FILENAME if mutation == "wrong-application" else CONFIG_FILENAME)
        value = json.loads(path.read_text(encoding="utf-8"))
        value["application" if mutation == "wrong-application" else "config_version"] = (
            "foreign" if mutation == "wrong-application" else 999
        )
        path.write_text(json.dumps(value), encoding="utf-8")
    before = snapshot(target)
    with pytest.raises(cleanup.CleanupError):
        cleanup.offer(policy)
    assert snapshot(target) == before and not policy.journal.exists()


def test_foreign_marker_never_enumerates_database_files(policy, monkeypatch):
    target = root(policy)
    (target / MARKER_FILENAME).write_text('{"application":"foreign"}', encoding="utf-8")
    monkeypatch.setattr(
        cleanup, "BoundTree", lambda *_a, **_kw: pytest.fail("Foreign root scanned"),
    )
    with pytest.raises(cleanup.CleanupError, match="not a TrainingFeedback"):
        cleanup.offer(policy)


def test_open_connection_prevents_cleanup_without_writes(policy):
    target = root(policy)
    with Database(target / DATABASE_FILENAME):
        before = snapshot(target)
        with pytest.raises(FileSafetyError, match="in use"):
            cleanup.offer(policy)
        assert snapshot(target) == before
    assert not policy.journal.exists()


def test_confirmed_locator_change_is_refused_and_new_pointer_kept(policy, tmp_path):
    offered = cleanup.offer(policy)
    target = root(policy)
    before = snapshot(target)
    Locator(policy.locator).save(tmp_path / "another-root")
    with pytest.raises(cleanup.CleanupError, match="locator changed"):
        cleanup.commit(policy, offered, user_confirmed=True)
    assert snapshot(target) == before and root(policy) == tmp_path / "another-root"


def test_confirmed_root_replacement_preserves_both_directories(policy, tmp_path):
    offered = cleanup.offer(policy)
    target = root(policy)
    original = tmp_path / "original-root"
    assert target.resolve().is_relative_to(tmp_path) and original.resolve().is_relative_to(tmp_path)
    target.rename(original)
    create_new(target)
    initialize_library_root(target)
    before = snapshot(target)
    with pytest.raises(cleanup.CleanupError, match="changed"):
        cleanup.commit(policy, offered, user_confirmed=True)
    assert snapshot(target) == before and (original / DATABASE_FILENAME).exists()
    assert not policy.journal.exists()


def test_file_added_after_confirmation_is_preserved(policy):
    offered = cleanup.offer(policy)
    target = root(policy)
    (target / "new-user-file.txt").write_bytes(b"not confirmed")
    with pytest.raises(cleanup.CleanupError, match="changed"):
        cleanup.commit(policy, offered, user_confirmed=True)
    assert (target / "new-user-file.txt").read_bytes() == b"not confirmed"


@pytest.mark.parametrize("failure", [
    "exports/text.txt", DATABASE_FILENAME, ".training-feedback.lock", "",
])
def test_partial_failure_reports_and_retries_same_bound_root(policy, failure):
    offered = cleanup.offer(policy)
    target = root(policy)

    def fail(name, stage):
        if name == failure and stage == "before":
            raise OSError("synthetic injected interruption")

    result = cleanup.commit(policy, offered, user_confirmed=True, checkpoint=fail)
    assert result["status"] == "partial"
    assert policy.journal.exists() and policy.locator.exists()
    if (target / cleanup.CLEANUP_MARKER).exists():
        with pytest.raises(DataRootAccessError, match="interrupted uninstall"):
            inspect_existing(target)
    retry = cleanup.offer(policy)
    assert retry["retry"]
    assert cleanup.commit(policy, retry, user_confirmed=True)["status"] == "complete"
    assert not target.exists() and not policy.locator.exists() and not policy.journal.exists()


@pytest.mark.parametrize("failure", ["locator", "recovery"])
def test_after_root_removal_remaining_locator_or_journal_can_retry(policy, failure):
    offered = cleanup.offer(policy)
    target = root(policy)

    def fail(name, stage):
        if name == failure and stage == "before":
            raise OSError("synthetic finalization failure")

    result = cleanup.commit(policy, offered, user_confirmed=True, checkpoint=fail)
    assert not target.exists() and policy.journal.exists()
    assert result["status"] == (
        "root_removed_locator_retained" if failure == "locator"
        else "root_removed_recovery_retained"
    )
    result = cleanup.commit(policy, cleanup.offer(policy), user_confirmed=True)
    assert result["status"] == "complete"


def test_retry_never_deletes_replacement_remaining_file(policy):
    offered = cleanup.offer(policy)
    target = root(policy)

    def fail(name, stage):
        if name == "exports/text.txt" and stage == "before":
            raise OSError("synthetic")

    cleanup.commit(policy, offered, user_confirmed=True, checkpoint=fail)
    (target / "exports/text.txt").write_bytes(b"changed after interruption")
    with pytest.raises(cleanup.CleanupError, match="changed"):
        cleanup.offer(policy)
    assert (target / "exports/text.txt").read_bytes() == b"changed after interruption"


def test_process_crash_releases_handles_and_same_root_recovers(policy):
    offered = cleanup.offer(policy)
    token = policy.locator.parent / "synthetic-offer.json"
    token.write_text(json.dumps(offered), encoding="utf-8")
    script = (
        "import os,json; from pathlib import Path; "
        "from training_feedback.data.root_cleanup import CleanupPolicy,commit; "
        f"p=CleanupPolicy(Path({str(policy.locator)!r}),Path({str(policy.program_directory)!r}),"
        f"Path({str(policy.home)!r}),()); "
        f"e=json.loads(Path({str(token)!r}).read_text(encoding='utf-8')); "
        "commit(p,e,user_confirmed=True,checkpoint=lambda n,s: "
        "os._exit(17) if n=='exports/text.txt' and s=='after' else None)"
    )
    process = subprocess.run([sys.executable, "-c", script], capture_output=True)
    assert process.returncode == 17
    result = cleanup.commit(policy, cleanup.offer(policy), user_confirmed=True)
    assert result["status"] == "complete"


def test_bound_tree_prevents_directory_replacement(policy, tmp_path):
    target = root(policy)
    with BoundTree(target):
        with pytest.raises(OSError):
            target.rename(tmp_path / "replacement")
    assert target.exists()


def test_linked_root_contents_refused_external_sentinel_unchanged(policy, tmp_path):
    target = root(policy)
    outside = tmp_path / "external"
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"preserve")
    subprocess.run(["cmd", "/c", "mklink", "/J", str(target / "linked"), str(outside)],
                   check=True, capture_output=True)
    with pytest.raises(FileSafetyError, match="reparse"):
        cleanup.offer(policy)
    assert (outside / "sentinel").read_bytes() == b"preserve"


def test_hardlink_and_readonly_files_refuse_before_mutation(policy, tmp_path):
    target = root(policy)
    os.link(target / "exports/text.txt", tmp_path / "external.txt")
    with pytest.raises(FileSafetyError, match="hard links"):
        cleanup.offer(policy)
    assert not policy.journal.exists() and (tmp_path / "external.txt").exists()


def test_foreign_owner_refuses_before_mutation(policy, monkeypatch):
    monkeypatch.setattr(cleanup, "current_sid", lambda: "S-1-5-21-synthetic-other-user")
    with pytest.raises(FileSafetyError, match="current user"):
        cleanup.offer(policy)
    assert root(policy).exists() and not policy.journal.exists()


def test_cli_probe_then_no_confirmation_preserves_every_byte(policy, monkeypatch, tmp_path):
    monkeypatch.setattr(uninstall_cli, "system_policy", lambda: policy)
    offered = tmp_path / "offer.json"
    result = tmp_path / "probe.txt"
    target = root(policy)
    before = snapshot(target)
    assert uninstall_cli.main([
        "probe", "--offer", str(offered), "--result", str(result),
    ]) == 0
    assert result.read_text(encoding="utf-8").startswith("READY\n")
    assert uninstall_cli.main([
        "commit", "--offer", str(offered), "--result", str(tmp_path / "cancel.txt"),
    ]) == 0
    assert snapshot(target) == before and policy.locator.exists() and not policy.journal.exists()


def test_cli_confirmed_cleanup_returns_actual_complete(policy, monkeypatch, tmp_path):
    monkeypatch.setattr(uninstall_cli, "system_policy", lambda: policy)
    offered = tmp_path / "offer.json"
    target = root(policy)
    assert uninstall_cli.main([
        "probe", "--offer", str(offered), "--result", str(tmp_path / "probe.txt"),
    ]) == 0
    result = tmp_path / "commit.txt"
    assert uninstall_cli.main([
        "commit", "--offer", str(offered), "--result", str(result), "--confirmed",
    ]) == 0
    assert result.read_text(encoding="utf-8").startswith("complete\n")
    assert not target.exists() and not policy.locator.exists()


def test_readonly_file_refuses_without_changing_attributes(policy):
    target = root(policy)
    path = target / "exports/text.txt"
    path.chmod(0o444)
    try:
        with pytest.raises(FileSafetyError, match="Read-only"):
            cleanup.offer(policy)
        assert not policy.journal.exists() and path.read_bytes().startswith(b"  synthetic")
    finally:
        path.chmod(0o666)


def test_unknown_recovery_record_is_refused_without_root_changes(policy):
    before = snapshot(root(policy))
    policy.journal.write_text('{"format":"unknown","version":999}', encoding="utf-8")
    with pytest.raises(cleanup.CleanupError, match="invalid"):
        cleanup.offer(policy)
    assert snapshot(root(policy)) == before and policy.journal.exists()
