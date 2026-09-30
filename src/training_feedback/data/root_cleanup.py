"""Current-locator-only cleanup with immutable offers and durable partial progress."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

from .data_root import (
    APPLICATION_NAME,
    CONFIG_FILENAME,
    CONFIG_VERSION,
    DATA_FORMAT_VERSION,
    DATABASE_FILENAME,
    MARKER_FILENAME,
)
from .installation import checked_components, local_path, overlaps
from .library_root import LIBRARY_MODEL
from .migrations import LATEST_SCHEMA_VERSION
from .root_lock import CLEANUP_MARKER_FILENAME as CLEANUP_MARKER
from .root_lock import JOURNAL_FILENAME, LOCK_FILENAME
from .windows_files import BoundFile, BoundTree, current_sid

RECOVERY_NAME = "uninstall-cleanup.json"
FORMAT = "training_feedback.uninstall-cleanup"


class CleanupError(ValueError):
    pass


def digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


@dataclass(frozen=True)
class CleanupPolicy:
    locator: Path
    program_directory: Path
    home: Path
    protected: tuple[Path, ...]

    @property
    def journal(self):
        return self.locator.parent / RECOVERY_NAME


def pin_parents(stack: ExitStack, path: Path):
    for part in reversed(path.parents):
        stack.enter_context(BoundFile(part, directory=True))


def validate_path(path: Path, policy: CleanupPolicy):
    path = local_path(str(path))
    home = local_path(str(policy.home))
    if path == path.parent or path == home or path in home.parents:
        raise CleanupError("The selected root is a dangerous directory.")
    for boundary in (*policy.protected, policy.program_directory, policy.locator.parent):
        if overlaps(path, boundary):
            raise CleanupError("The selected root overlaps program, system or locator files.")
    checked_components(path)
    return path


def validate_current(tree: BoundTree):
    def metadata(name):
        if name not in tree.objects:
            raise CleanupError("The root metadata is incomplete.")
        return json.loads(tree.objects[name].read_bytes())

    marker, config = metadata(MARKER_FILENAME), metadata(CONFIG_FILENAME)
    if (not isinstance(marker, dict) or not isinstance(config, dict)
            or marker.get("application") != APPLICATION_NAME
            or config.get("application") != APPLICATION_NAME):
        raise CleanupError("The directory is not a TrainingFeedback root.")
    for value, key, expected in ((marker, "data_format_version", DATA_FORMAT_VERSION),
                                 (config, "data_format_version", DATA_FORMAT_VERSION),
                                 (config, "config_version", CONFIG_VERSION)):
        if type(value.get(key)) is not int or value[key] != expected:
            raise CleanupError("Unknown or unsupported data format; retain this root.")
    if config.get("library_model") != LIBRARY_MODEL or CLEANUP_MARKER in tree.objects:
        raise CleanupError("The root model is unsupported or cleanup is incomplete.")
    if JOURNAL_FILENAME in tree.objects:
        raise CleanupError("Upgrade recovery state must be resolved before deleting this root.")
    if any(DATABASE_FILENAME + suffix in tree.objects for suffix in ("-wal", "-shm", "-journal")):
        raise CleanupError("Database recovery or active sidecars prevent data deletion.")
    database = tree.objects.get(DATABASE_FILENAME)
    if database is None:
        raise CleanupError("The current database is missing.")
    # Inspect the pinned bytes in memory. No writable connection or recovery touches the root.
    with sqlite3.connect(":memory:") as connection:
        connection.deserialize(database.read_bytes())
        connection.execute("PRAGMA query_only=ON")
        version = connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0]
        if type(version) is not int or version != LATEST_SCHEMA_VERSION:
            raise CleanupError("Unsupported database schema; retain this root.")
        if (connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
                or connection.execute("PRAGMA foreign_key_check").fetchone() is not None):
            raise CleanupError("The database is invalid; retain this root.")
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='one_time_reset_journal'",
        ).fetchone():
            if connection.execute("SELECT 1 FROM one_time_reset_journal LIMIT 1").fetchone():
                raise CleanupError("Pending reset recovery prevents data deletion.")


def check_state(value, policy, owner):
    if (not isinstance(value, dict) or value.get("format") != FORMAT
            or type(value.get("version")) is not int or value["version"] != 1
            or value.get("owner") != owner or not isinstance(value.get("objects"), dict)
            or not isinstance(value.get("deleted"), list)
            or value.get("stage") not in {
                "prepared", "marking", "deleting", "root_removed", "locator_removed",
            }
            or not isinstance(value.get("nonce"), str) or len(value["nonce"]) != 32):
        raise CleanupError("The cleanup recovery record is invalid; retain the remaining files.")
    validate_path(local_path(value["root"]), policy)
    if ("" not in value["objects"] or not isinstance(value["objects"][""], dict)
            or value["objects"][""].get("directory") is not True):
        raise CleanupError("Cleanup root identity is missing.")
    from .installation import relative_file

    for name, identity in value["objects"].items():
        if name:
            relative_file(Path(value["root"]), name)
        if (not isinstance(identity, dict) or type(identity.get("volume")) is not int
                or type(identity.get("file_id")) is not int
                or type(identity.get("directory")) is not bool):
            raise CleanupError("Cleanup object identity is invalid.")
    if not set(value["deleted"]).issubset(value["objects"]):
        raise CleanupError("Cleanup progress is invalid.")
    if value.get("inflight") is not None and value["inflight"] not in value["objects"]:
        raise CleanupError("Cleanup intent is invalid.")
    if value["stage"] in {"deleting", "root_removed", "locator_removed"}:
        if CLEANUP_MARKER not in value["objects"]:
            raise CleanupError("Cleanup completion has no marker evidence.")
    return value


def load_state(policy, owner):
    checked_components(policy.journal)
    with ExitStack() as stack:
        pin_parents(stack, policy.journal)
        source = stack.enter_context(BoundFile(policy.journal, owner=owner))
        return check_state(json.loads(source.read_bytes()), policy, owner)


def save_state(policy, value):
    checked_components(policy.journal)
    temporary = policy.journal.with_name(f".uninstall-{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(policy.journal)
    finally:
        temporary.unlink(missing_ok=True)


def claimed_root(root, owner):
    """Verify application metadata before enumerating or opening any database files."""
    with ExitStack() as stack:
        pin_parents(stack, root / MARKER_FILENAME)
        marker_file = stack.enter_context(BoundFile(root / MARKER_FILENAME, owner=owner))
        marker = json.loads(marker_file.read_bytes())
        if not isinstance(marker, dict) or marker.get("application") != APPLICATION_NAME:
            raise CleanupError("The directory is not a TrainingFeedback root.")
        config_file = stack.enter_context(BoundFile(root / CONFIG_FILENAME, owner=owner))
        config = json.loads(config_file.read_bytes())
        if not isinstance(config, dict) or config.get("application") != APPLICATION_NAME:
            raise CleanupError("The root configuration belongs to another application.")


def verify_remaining(tree, state):
    current = tree.inventory()
    missing = set(state["objects"]) - set(current) - set(state["deleted"])
    if missing - {state.get("inflight")}:
        raise CleanupError("Confirmed remaining objects disappeared unexpectedly.")
    remaining = {name: row for name, row in state["objects"].items()
                 if name not in state["deleted"] and name not in missing}
    if (state["stage"] == "marking" and CLEANUP_MARKER in current
            and CLEANUP_MARKER not in remaining):
        marker = json.loads(tree.objects[CLEANUP_MARKER].read_bytes())
        if marker != {"format": FORMAT, "version": 1, "nonce": state["nonce"]}:
            raise CleanupError("Cleanup marker identity is invalid.")
        remaining[CLEANUP_MARKER] = current[CLEANUP_MARKER]
    if current != remaining:
        raise CleanupError("Remaining identities changed; cleanup stopped.")
    if state["stage"] == "prepared" and CLEANUP_MARKER not in current:
        validate_current(tree)
    return current, missing


def offer(policy: CleanupPolicy) -> dict:
    owner = current_sid()
    with ExitStack() as stack:
        pin_parents(stack, policy.locator)
        if policy.journal.exists() and not policy.locator.exists():
            state = load_state(policy, owner)
            if (state["stage"] not in {"root_removed", "locator_removed"}
                    or Path(state["root"]).exists()):
                raise CleanupError("The locator is missing and cleanup completion is uncertain.")
            return {"root": state["root"], "locator_sha256": state["locator_sha256"],
                    "retry": True, "state_sha256": digest(state), "objects": state["objects"],
                    "token": digest(state)}
        pointer = stack.enter_context(BoundFile(policy.locator, owner=owner))
        original = pointer.read_bytes()
        if policy.journal.exists():
            state = load_state(policy, owner)
            root = local_path(state["root"])
            if hashlib.sha256(original).hexdigest() != state["locator_sha256"]:
                raise CleanupError("The locator changed; retain the remaining cleanup files.")
            if root.exists():
                with BoundTree(root, owner=owner) as tree:
                    verify_remaining(tree, state)
            elif "" not in state["deleted"] and state.get("inflight") != "":
                raise CleanupError("Cleanup root disappeared before its deletion was recorded.")
            # A retry offer does not reinterpret a partially removed database as a valid root.
            return {"root": str(root), "locator_sha256": state["locator_sha256"],
                    "retry": True, "state_sha256": digest(state), "objects": state["objects"],
                    "token": digest(state)}
        value = json.loads(original)
        root = validate_path(local_path(value["data_root"]), policy)
        claimed_root(root, owner)
        with BoundTree(root, owner=owner) as tree:
            validate_current(tree)
            inventory = tree.inventory()
            if LOCK_FILENAME not in inventory:
                raise CleanupError("The existing root lock is missing; data deletion is disabled.")
        result = {"root": str(root), "locator_sha256": hashlib.sha256(original).hexdigest(),
                  "retry": False, "objects": inventory}
        return {**result, "token": digest(result)}


def commit(policy: CleanupPolicy, expected: dict, *, user_confirmed: bool, checkpoint=None) -> dict:
    """Require a fresh bound offer. Partial deletion is explicitly reported and resumable."""
    if user_confirmed is not True:
        return {"status": "cancelled", "root": expected.get("root")}
    owner = current_sid()
    state = None
    root = validate_path(local_path(expected["root"]), policy)
    with ExitStack() as stack:
        pin_parents(stack, policy.locator)
        if not policy.locator.exists() and expected.get("retry"):
            state = load_state(policy, owner)
            if (digest(state) != expected.get("state_sha256") or root.exists()
                    or state["stage"] not in {"root_removed", "locator_removed"}):
                raise CleanupError("The cleanup record cannot certify completion.")
            with BoundFile(policy.journal, delete=True, owner=owner) as journal:
                journal.delete()
            return {"status": "complete", "root": str(root), "remaining": []}
        pointer = stack.enter_context(BoundFile(policy.locator, delete=True, owner=owner))
        if pointer.digest() != expected["locator_sha256"]:
            raise CleanupError("The locator changed after confirmation; no data was deleted.")
        if expected.get("retry"):
            state = load_state(policy, owner)
            if digest(state) != expected.get("state_sha256"):
                raise CleanupError("Cleanup recovery state changed after confirmation.")
        elif policy.journal.exists():
            raise CleanupError("An existing cleanup must be resolved first.")
        try:
            if root.exists():
                tree = stack.enter_context(BoundTree(root, owner=owner))
                current = tree.inventory()
                if state is None:
                    result = {"root": str(root), "locator_sha256": pointer.digest(),
                              "retry": False, "objects": current}
                    if digest(result) != expected.get("token"):
                        raise CleanupError("The confirmed directory or files changed; no deletion.")
                    validate_current(tree)
                    state = {"format": FORMAT, "version": 1, "owner": owner,
                             "nonce": uuid.uuid4().hex, "root": str(root),
                             "locator_sha256": pointer.digest(), "objects": current,
                             "deleted": [], "inflight": None, "stage": "prepared"}
                    save_state(policy, state)
                else:
                    current, missing = verify_remaining(tree, state)
                    if missing:
                        state["deleted"].extend(missing)
                    remaining = {name: identity for name, identity in state["objects"].items()
                                 if name not in state["deleted"]}
                    # A crash may occur after writing the marker, before recording its identity.
                    if (state["stage"] == "marking" and CLEANUP_MARKER in current
                            and CLEANUP_MARKER not in remaining):
                        marker = json.loads(tree.objects[CLEANUP_MARKER].read_bytes())
                        if marker != {"format": FORMAT, "version": 1, "nonce": state["nonce"]}:
                            raise CleanupError("Cleanup marker identity is invalid.")
                        state["objects"][CLEANUP_MARKER] = current[CLEANUP_MARKER]
                        remaining[CLEANUP_MARKER] = current[CLEANUP_MARKER]
                    if current != remaining:
                        raise CleanupError("Remaining identities changed; cleanup stopped.")
                if CLEANUP_MARKER not in state["objects"]:
                    state["stage"] = "marking"
                    save_state(policy, state)
                    marker_path = root / CLEANUP_MARKER
                    with marker_path.open("x", encoding="utf-8") as stream:
                        json.dump({"format": FORMAT, "version": 1, "nonce": state["nonce"]}, stream)
                        stream.flush()
                        os.fsync(stream.fileno())
                    tree.objects[CLEANUP_MARKER] = BoundFile(marker_path, delete=True, owner=owner)
                    state["objects"][CLEANUP_MARKER] = tree.inventory()[CLEANUP_MARKER]
                state["stage"] = "deleting"
                save_state(policy, state)
                critical = {MARKER_FILENAME: 1, CONFIG_FILENAME: 1, DATABASE_FILENAME: 1,
                            CLEANUP_MARKER: 2, LOCK_FILENAME: 3}
                files = [name for name, obj in current.items() if not obj["directory"]]
                if CLEANUP_MARKER not in files and CLEANUP_MARKER not in state["deleted"]:
                    files.append(CLEANUP_MARKER)
                directories = [name for name, obj in current.items() if obj["directory"] and name]
                order = sorted(files, key=lambda name: (critical.get(name, 0), name))
                # Keep the marker + root lease until all other files/directories are gone.
                late = [name for name in order if name in {CLEANUP_MARKER, LOCK_FILENAME}]
                order = [name for name in order if name not in late]
                order += sorted(directories, key=lambda name: name.count("/"), reverse=True)
                order += late + [""]
                for name in order:
                    if name in state["deleted"]:
                        continue
                    state["inflight"] = name
                    save_state(policy, state)
                    if checkpoint:
                        checkpoint(name, "before")
                    tree.objects[name].delete()
                    if checkpoint:
                        checkpoint(name, "after")
                    state["deleted"].append(name)
                    state["inflight"] = None
                    save_state(policy, state)
                state["stage"] = "root_removed"
                save_state(policy, state)
            elif state is None or ("" not in state["deleted"] and state.get("inflight") != ""):
                raise CleanupError("The confirmed root disappeared; no locator deletion.")
            else:
                if "" not in state["deleted"]:
                    state["deleted"].append("")
                state["stage"] = "root_removed"
                save_state(policy, state)
            if checkpoint:
                checkpoint("locator", "before")
            pointer.delete()
            state["stage"] = "locator_removed"
            save_state(policy, state)
            if checkpoint:
                checkpoint("recovery", "before")
            # Parent handles remain pinned; remove only this confirmed recovery record.
            with BoundFile(policy.journal, delete=True, owner=owner) as journal:
                journal.delete()
            return {"status": "complete", "root": str(root), "remaining": []}
        except (OSError, ValueError, sqlite3.Error) as exc:
            if state is None:
                raise
            status = ("partial" if root.exists() else "root_removed_locator_retained"
                      if policy.locator.exists() else "root_removed_recovery_retained")
            return {"status": status,
                    "root": str(root), "remaining": [name for name in state["objects"]
                    if name not in state["deleted"]], "reason": str(exc),
                    "recovery": str(policy.journal)}
