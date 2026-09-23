"""Internal staged upgrades with verified online snapshots and restartable rollback.

The converter writes only its disposable work root. Until a verified publication
is journaled complete, recovery restores the previous complete root. These
snapshots intentionally omit backups and are not ordinary whole-root backups.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from .catalog_repository import CatalogRepository
from .catalog_resources import CatalogError, managed_path
from .data_root import DATABASE_FILENAME, DataRootError, inspect_existing
from .root_lock import (
    JOURNAL_FILENAME,
    LOCK_FILENAME,
    RECOVERY_FORMAT,
    RECOVERY_VERSION,
    RootLease,
)

SIDECARS = {DATABASE_FILENAME + suffix for suffix in ("-journal", "-wal", "-shm")}
INTERNAL = {"backups", LOCK_FILENAME, JOURNAL_FILENAME, *SIDECARS}
TEMP_PREFIX = ".training-feedback-publish-"


class UpgradeRecoveryError(DataRootError):
    pass


def _digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _atomic_bytes(path, data):
    staged = path.parent / (TEMP_PREFIX + uuid.uuid4().hex)
    try:
        with staged.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def _atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.parent / (TEMP_PREFIX + uuid.uuid4().hex)
    try:
        with source.open("rb") as incoming, staged.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        os.replace(staged, destination)
    finally:
        staged.unlink(missing_ok=True)


def _write_json(path, value):
    _atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Expected an object.")
        return value
    except (OSError, ValueError) as exc:
        raise UpgradeRecoveryError(
            "The upgrade recovery journal or manifest is unreadable."
        ) from exc


def _inventory(root):
    files, directories = {}, []

    def visit(directory):
        for path in sorted(directory.iterdir()):
            relative = path.relative_to(root).as_posix()
            if directory == root and path.name in INTERNAL:
                continue
            if path.name.startswith(TEMP_PREFIX):
                continue
            if path.is_symlink() or path.is_junction():
                raise UpgradeRecoveryError("Upgrade resources cannot contain linked paths.")
            if path.is_dir():
                directories.append(relative)
                visit(path)
            elif path.is_file():
                files[relative] = {"sha256": _digest(path), "bytes": path.stat().st_size}
            else:
                raise UpgradeRecoveryError("An upgrade resource is not a regular file.")

    visit(root)
    return {"files": files, "directories": sorted(directories)}


def _verify(root, inventory):
    if _inventory(root) != inventory:
        raise UpgradeRecoveryError("Upgrade resource hashes or inventory do not match.")
    inspect_existing(root)


def _copy_inventory(source, destination, inventory):
    destination.mkdir(parents=True, exist_ok=True)
    for relative in inventory["directories"]:
        managed_path(destination, relative).mkdir(parents=True, exist_ok=True)
    for relative in inventory["files"]:
        _atomic_copy(managed_path(source, relative), managed_path(destination, relative))


class UpgradeRecovery:
    """Caller supplies a one-time converter and a new-model validator, both off-root.

    Every callback must close its database handles before returning. The validator
    is read-only. The root lease must precede any normal composition-root open.
    """

    def __init__(self, root: Path, *, catalog_path: Path | None = None, checkpoint=None):
        self.root = Path(root).resolve()
        self.catalog_path = catalog_path
        self.checkpoint = checkpoint or (lambda _phase: None)

    def _journal(self, value):
        _write_json(self.root / JOURNAL_FILENAME, value)

    def _load_journal(self):
        path = self.root / JOURNAL_FILENAME
        if not path.exists():
            return None
        value = _read_json(path)
        if (value.get("format") != RECOVERY_FORMAT or value.get("version") != RECOVERY_VERSION
                or value.get("phase") not in {
                    "prepared", "publishing", "restoring", "complete", "rolled_back",
                }
                or not isinstance(value.get("operation"), str)
                or not re.fullmatch(r"backups/upgrade-v1-[a-f0-9]{32}", value.get("recovery", ""))):
            raise UpgradeRecoveryError("The upgrade recovery journal is invalid.")
        return value

    def _recovery(self, journal):
        base = managed_path(self.root, journal["recovery"])
        manifest_path = base / "manifest.json"
        if _digest(manifest_path) != journal.get("manifest_sha256"):
            raise UpgradeRecoveryError("The upgrade recovery manifest hash does not match.")
        manifest = _read_json(manifest_path)
        if (manifest.get("format") != RECOVERY_FORMAT
                or manifest.get("version") != RECOVERY_VERSION):
            raise UpgradeRecoveryError("The upgrade recovery manifest format is invalid.")
        _verify(base / "snapshot", manifest["inventory"])
        return base, manifest

    def _space(self, byte_count):
        # Snapshot + work + atomic publication/rollback margin; backups never recurse.
        if shutil.disk_usage(self.root).free < byte_count * 3 + 16 * 1024 * 1024:
            raise UpgradeRecoveryError("There is not enough free space for a recoverable upgrade.")

    def _snapshot(self, operation, catalog):
        before = _inventory(self.root)
        required = sum(value["bytes"] for value in before["files"].values())
        wal = self.root / (DATABASE_FILENAME + "-wal")
        if wal.exists():
            required += wal.stat().st_size
        self._space(required)
        if (self.root / "backups").is_symlink() or (self.root / "backups").is_junction():
            raise UpgradeRecoveryError("Upgrade resources cannot contain linked paths.")
        backups = managed_path(self.root, "backups")
        base = backups / ("upgrade-v1-" + uuid.uuid4().hex)
        snapshot = base / "snapshot"
        snapshot.mkdir(parents=True)
        try:
            # Block writers that use SQLite directly while the online snapshot is taken.
            with closing(sqlite3.connect(self.root / DATABASE_FILENAME, timeout=0)) as guard:
                guard.execute("BEGIN IMMEDIATE")
                uri = (self.root / DATABASE_FILENAME).as_uri() + "?mode=ro"
                with closing(sqlite3.connect(uri, uri=True)) as source:
                    with closing(sqlite3.connect(snapshot / DATABASE_FILENAME)) as target:
                        source.backup(target)
                        # Online backup inherits WAL mode. Seal a standalone snapshot so
                        # read-only verification does not create new WAL/SHM companions.
                        target.execute("PRAGMA journal_mode=DELETE")
                resources = {"directories": before["directories"], "files": {
                    key: value for key, value in before["files"].items()
                    if key != DATABASE_FILENAME
                }}
                _copy_inventory(self.root, snapshot, resources)
                self.checkpoint("resources_copied")
                after = _inventory(self.root)
                if {k: v for k, v in after["files"].items() if k != DATABASE_FILENAME} != (
                        resources["files"]) or after["directories"] != before["directories"]:
                    raise UpgradeRecoveryError("Data-root resources changed during upgrade backup.")
                guard.rollback()
            inventory = _inventory(snapshot)
            if {key: value for key, value in inventory["files"].items()
                    if key != DATABASE_FILENAME} != resources["files"]:
                raise UpgradeRecoveryError("Upgrade resource hashes or inventory do not match.")
            _verify(snapshot, inventory)
            manifest = {
                "format": RECOVERY_FORMAT, "version": RECOVERY_VERSION,
                "operation": operation, "catalog_version": catalog.version,
                "catalog_manifest_sha256": _digest(catalog.directory / "catalog-manifest.json"),
                "inventory": inventory,
            }
            _write_json(base / "manifest.json", manifest)
            self.checkpoint("snapshot_verified")
            journal = {
                "format": RECOVERY_FORMAT, "version": RECOVERY_VERSION,
                "operation": operation, "phase": "prepared",
                "recovery": base.relative_to(self.root).as_posix(),
                "manifest_sha256": _digest(base / "manifest.json"),
            }
            self._journal(journal)
            return journal
        except Exception:
            # If the journal write reached disk, keep the only snapshot it references.
            if not (self.root / JOURNAL_FILENAME).exists():
                shutil.rmtree(base)
            raise

    def _remove_sidecars(self):
        for name in SIDECARS:
            (self.root / name).unlink(missing_ok=True)

    def _publish(self, source, inventory, previous):
        # Journal is already durable, readers are excluded and all SQL handles are closed.
        # Remove old paths first so file↔directory changes can also be rolled back.
        self._remove_obsolete(previous, inventory)
        self._remove_sidecars()
        _atomic_copy(source / DATABASE_FILENAME, self.root / DATABASE_FILENAME)
        self.checkpoint("database_published")
        resources = {"directories": inventory["directories"], "files": {
            key: value for key, value in inventory["files"].items() if key != DATABASE_FILENAME
        }}
        _copy_inventory(source, self.root, resources)
        self.checkpoint("assets_published")

    def _remove_obsolete(self, previous, current):
        for relative in previous["files"].keys() - current["files"].keys():
            path = managed_path(self.root, relative)
            if path.is_file():
                path.unlink()
        for relative in sorted(set(previous["directories"]) - set(current["directories"]),
                               key=lambda path: path.count("/"), reverse=True):
            path = managed_path(self.root, relative)
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
        # Reserved atomic-write files can survive process termination.
        for path in self.root.rglob(TEMP_PREFIX + "*"):
            if "backups" not in path.relative_to(self.root).parts and path.is_file():
                path.unlink()

    def _recover(self, journal):
        base, manifest = self._recovery(journal)
        before = manifest["inventory"]
        output = journal.get("output_inventory", before)
        journal["phase"] = "restoring"
        self._journal(journal)
        self._publish(base / "snapshot", before, output)
        _verify(self.root, before)
        self.checkpoint("restored")
        journal["phase"] = "rolled_back"
        self._journal(journal)
        shutil.rmtree(base / "work", ignore_errors=True)

    def recover(self) -> bool:
        """Recover a pending publication before any normal root/database validation."""
        if not self.root.is_dir():
            raise UpgradeRecoveryError("The upgrade data root does not exist.")
        try:
            with RootLease(self.root, exclusive=True):
                journal = self._load_journal()
                if journal is None or journal["phase"] in {"complete", "rolled_back"}:
                    return False
                self._recover(journal)
                return True
        except (OSError, sqlite3.Error, CatalogError) as exc:
            raise UpgradeRecoveryError(
                f"The interrupted upgrade could not be recovered: {exc}"
            ) from exc

    def run(self, operation: str, convert, validate) -> bool:
        """Return False for an already completed operation; failures stay recoverable.

        Ordinary exceptions and abrupt process exits both leave a pending journal.
        The next invocation restores first, then retries from the original facts.
        """
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", operation):
            raise ValueError("Upgrade operation requires a stable identifier.")
        if not self.root.is_dir():
            raise UpgradeRecoveryError("The upgrade data root does not exist.")
        try:
            with CatalogRepository(self.catalog_path) as catalog:
                if not (self.root / JOURNAL_FILENAME).exists():
                    inspect_existing(self.root)
                with RootLease(self.root, exclusive=True):
                    journal = self._load_journal()
                    if journal and journal["phase"] not in {"complete", "rolled_back"}:
                        self._recover(journal)
                    inspect_existing(self.root)
                    if journal and journal["phase"] == "complete" and (
                            journal["operation"] == operation):
                        return False
                    journal = self._snapshot(operation, catalog)
                    base, manifest = self._recovery(journal)
                    work = base / "work"
                    _copy_inventory(base / "snapshot", work, manifest["inventory"])
                    convert(work, catalog)
                    inspect_existing(work)
                    validate(work, catalog)
                    output = _inventory(work)
                    _verify(work, output)
                    self.checkpoint("staged")
                    journal.update(phase="publishing", output_inventory=output)
                    self._journal(journal)
                    self.checkpoint("publication_started")
                    self._publish(work, output, manifest["inventory"])
                    _verify(self.root, output)
                    validate(self.root, catalog)
                    self.checkpoint("publication_verified")
                    shutil.rmtree(work)
                    self.checkpoint("cleanup")
                    journal["phase"] = "complete"
                    self._journal(journal)
                    return True
        except (OSError, sqlite3.Error, CatalogError) as exc:
            raise UpgradeRecoveryError(
                f"The data-root upgrade could not be completed: {exc}"
            ) from exc
