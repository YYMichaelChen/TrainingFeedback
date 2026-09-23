"""G1 recovery protocol, independently counted publication failure boundaries."""

import json
import sqlite3
import subprocess
import sys
from contextlib import closing
from types import SimpleNamespace

import pytest
from migration_070_fixtures import logical_baseline

from training_feedback.data.data_root import (
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    create_new,
    inspect_existing,
)
from training_feedback.data.database import Database
from training_feedback.data.root_lock import JOURNAL_FILENAME, RootBusyError
from training_feedback.data.upgrade_recovery import UpgradeRecovery, UpgradeRecoveryError


@pytest.fixture
def root(tmp_path):
    path = tmp_path / "用户 数据"
    create_new(path)
    (path / "exercise-images" / "原始.bin").write_bytes(b"image-original\x00")
    (path / "imports" / "answer.txt").write_bytes("  答复\t\r\n原文  ".encode())
    (path / "backups" / "previous.bin").write_bytes(b"previous backup")
    return path


def convert(work, _catalog):
    with Database(work / DATABASE_FILENAME) as db:
        with db:
            db.execute("INSERT INTO body_area(name) VALUES ('synthetic conversion')")
    (work / "exercise-images" / "原始.bin").unlink()
    # The publisher must handle file-to-directory replacement and its reverse on rollback.
    (work / "exercise-images" / "原始.bin").mkdir()
    (work / "exercise-images" / "原始.bin" / "new.txt").write_bytes(b"replacement")
    (work / "snapshot-assets").mkdir()
    (work / "snapshot-assets" / "new.bin").write_bytes(b"new managed asset")
    config = json.loads((work / CONFIG_FILENAME).read_text(encoding="utf-8"))
    config["synthetic-conversion"] = True
    (work / CONFIG_FILENAME).write_text(json.dumps(config), encoding="utf-8")


def validate(work, _catalog):
    inspect_existing(work)
    assert (work / "snapshot-assets" / "new.bin").read_bytes() == b"new managed asset"


def facts(root):
    value = logical_baseline(root)
    value["resources"] = {key: digest for key, digest in value["resources"].items()
                          if not key.startswith("backups/") and key != JOURNAL_FILENAME}
    return value


@pytest.mark.parametrize("phase", ["staged", "database_published", "cleanup"])
def test_crash_restores_previous_complete_root_and_retries(root, phase):
    before = facts(root)

    class ProcessExit(BaseException):
        pass

    def interrupt(current):
        if current == phase:
            raise ProcessExit()

    with pytest.raises(ProcessExit):
        UpgradeRecovery(root, checkpoint=interrupt).run("synthetic", convert, validate)
    with pytest.raises(RootBusyError, match="recovered"):
        with Database(root / DATABASE_FILENAME):
            pass
    recovery = UpgradeRecovery(root)
    if phase == "cleanup":
        with pytest.raises(ProcessExit):
            UpgradeRecovery(root, checkpoint=lambda current: interrupt(
                "cleanup" if current == "database_published" else current
            )).recover()
    assert recovery.recover()
    assert facts(root) == before
    assert (root / "backups" / "previous.bin").read_bytes() == b"previous backup"
    assert not recovery.recover()
    assert recovery.run("synthetic", convert, validate)
    after = facts(root)
    assert not recovery.run("synthetic", convert, validate)
    assert facts(root) == after


def test_snapshot_copy_failure_never_calls_converter_or_changes_facts(root):
    before = facts(root)

    def fail(phase):
        if phase == "resources_copied":
            raise OSError("injected disk failure")

    with pytest.raises(UpgradeRecoveryError, match="disk failure"):
        UpgradeRecovery(root, checkpoint=fail).run("synthetic", convert, validate)
    assert facts(root) == before
    assert not (root / JOURNAL_FILENAME).exists()
    assert not list((root / "backups").glob("upgrade-*"))


def test_corrupt_recovery_snapshot_blocks_restore_without_touching_live_files(root):
    def fail(phase):
        if phase == "database_published":
            raise OSError("interrupt")

    with pytest.raises(UpgradeRecoveryError):
        UpgradeRecovery(root, checkpoint=fail).run("synthetic", convert, validate)
    before = facts(root)
    snapshot = next((root / "backups").glob("upgrade-*/snapshot"))
    image = snapshot / "exercise-images" / "原始.bin"
    image.write_bytes(b"corrupt")
    with pytest.raises(UpgradeRecoveryError, match="hashes"):
        UpgradeRecovery(root).recover()
    assert facts(root) == before
    image.write_bytes(b"image-original\x00")
    assert UpgradeRecovery(root).recover()


def test_root_lease_excludes_other_process_and_releases_after_exit(root):
    code = (
        "import sys; from pathlib import Path; "
        "from training_feedback.data.root_lock import RootLease; "
        "RootLease(Path(sys.argv[1]), exclusive=True).__enter__()"
    )
    with Database(root / DATABASE_FILENAME):
        with Database(root / DATABASE_FILENAME):  # Shared readers/writers remain supported.
            blocked = subprocess.run([sys.executable, "-c", code, str(root)], capture_output=True)
            assert blocked.returncode != 0
            assert b"RootBusyError" in blocked.stderr
        with pytest.raises(UpgradeRecoveryError, match="in use"):
            UpgradeRecovery(root).run("synthetic", convert, validate)
    released = subprocess.run([sys.executable, "-c", code, str(root)], capture_output=True)
    assert released.returncode == 0
    assert UpgradeRecovery(root).run("synthetic", convert, validate)


def test_space_preflight_rejects_before_snapshot_or_conversion(root, monkeypatch):
    before = facts(root)
    monkeypatch.setattr("training_feedback.data.upgrade_recovery.shutil.disk_usage",
                        lambda _: SimpleNamespace(free=0))
    with pytest.raises(UpgradeRecoveryError, match="free space"):
        UpgradeRecovery(root).run("synthetic", convert, validate)
    assert facts(root) == before
    assert not list((root / "backups").glob("upgrade-*"))
    with closing(sqlite3.connect(root / DATABASE_FILENAME)) as db:
        assert db.execute("SELECT COUNT(*) FROM body_area").fetchone()[0] == 0


def test_online_snapshot_contains_committed_wal_and_restores_without_sidecars(root):
    writer = sqlite3.connect(root / DATABASE_FILENAME)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO body_area(name) VALUES ('committed WAL fact')")
        writer.commit()
        assert (root / (DATABASE_FILENAME + "-wal")).stat().st_size > 0

        def interrupt(phase):
            if phase == "snapshot_verified":
                writer.close()
            if phase == "database_published":
                raise OSError("WAL publication interrupt")

        with pytest.raises(UpgradeRecoveryError):
            UpgradeRecovery(root, checkpoint=interrupt).run("wal-facts", convert, validate)
        recovery = UpgradeRecovery(root)
        assert recovery.recover()
        with closing(sqlite3.connect(root / DATABASE_FILENAME)) as db:
            assert db.execute("SELECT name FROM body_area").fetchall() == [("committed WAL fact",)]
        snapshot = next((root / "backups").glob("upgrade-*/snapshot"))
        assert not list(snapshot.glob("*-wal"))
        assert not list(snapshot.glob("*-shm"))
    finally:
        writer.close()
