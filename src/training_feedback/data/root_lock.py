"""OS-held root leases: shared connections, exclusive upgrade, automatic crash release."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

LOCK_FILENAME = ".training-feedback.lock"
MUTATION_LOCK_FILENAME = ".training-feedback.mutation.lock"
CLEANUP_MARKER_FILENAME = ".training-feedback-cleanup.json"
JOURNAL_FILENAME = ".training-feedback-upgrade.json"
RECOVERY_FORMAT = "training_feedback.upgrade-recovery"
RECOVERY_VERSION = 1


class RootBusyError(OSError):
    pass


def require_no_pending_upgrade(root: Path) -> None:
    path = root / JOURNAL_FILENAME
    if not path.exists():
        return
    try:
        journal = json.loads(path.read_text(encoding="utf-8"))
        ready = (journal["format"] == RECOVERY_FORMAT
                 and journal["version"] == RECOVERY_VERSION
                 and journal["phase"] in {"complete", "rolled_back"})
    except (OSError, ValueError, KeyError, TypeError):
        ready = False
    if not ready:
        raise RootBusyError(
            "An unfinished historical upgrade is unsupported. Create a new empty "
            "data root; the original root and files are preserved."
        )


class RootLease:
    def __init__(
        self,
        root: Path,
        *,
        exclusive: bool = False,
        filename: str = LOCK_FILENAME,
        busy_message: str = "The data root is in use; close it before upgrading.",
    ):
        self.path = Path(root) / filename
        self.exclusive = exclusive
        self.busy_message = busy_message
        self.stream = None
        self.overlapped = None

    def __enter__(self):
        if self.path.is_symlink() or self.path.is_junction():
            raise RootBusyError("The data-root lock path is invalid.")
        self.stream = self.path.open("a+b")
        try:
            if os.name == "nt":
                import ctypes
                import msvcrt
                from ctypes import wintypes

                class Overlapped(ctypes.Structure):
                    _fields_ = [("Internal", ctypes.c_size_t), ("InternalHigh", ctypes.c_size_t),
                                ("Offset", wintypes.DWORD), ("OffsetHigh", wintypes.DWORD),
                                ("hEvent", wintypes.HANDLE)]

                self.overlapped = Overlapped()
                self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                self.kernel.LockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                  wintypes.DWORD, wintypes.DWORD,
                                                  wintypes.DWORD, ctypes.c_void_p]
                self.kernel.LockFileEx.restype = wintypes.BOOL
                self.kernel.UnlockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                    wintypes.DWORD, wintypes.DWORD,
                                                    ctypes.c_void_p]
                self.kernel.UnlockFileEx.restype = wintypes.BOOL
                self.handle = msvcrt.get_osfhandle(self.stream.fileno())
                flags = 1 | (2 if self.exclusive else 0)  # fail immediately; optional exclusive
                if not self.kernel.LockFileEx(self.handle, flags, 0, 1, 0,
                                               ctypes.byref(self.overlapped)):
                    raise ctypes.WinError(ctypes.get_last_error())
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_NB |
                            (fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH))
        except OSError as exc:
            self.stream.close()
            self.stream = None
            raise RootBusyError(self.busy_message) from exc
        return self

    def close(self):
        if self.stream is None:
            return
        try:
            if os.name == "nt":
                import ctypes

                self.kernel.UnlockFileEx(self.handle, 0, 1, 0, ctypes.byref(self.overlapped))
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        finally:
            self.stream.close()
            self.stream = None

    def __exit__(self, *_):
        self.close()


class _MutationState:
    def __init__(self):
        self.lock = threading.RLock()
        self.depth = 0
        self.lease = None


_MUTATION_STATES: dict[Path, _MutationState] = {}
_MUTATION_STATES_LOCK = threading.Lock()


class RootMutationLease:
    """Serialize one root's writes and complete backup across threads/processes.

    The process-local re-entrant lock lets a file operation wrap a nested SQLite
    transaction. The separate OS-held lock gives other current application
    processes the same boundary without disturbing the root-open lease.
    """

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.state = None
        self.entered = False

    def __enter__(self):
        with _MUTATION_STATES_LOCK:
            state = _MUTATION_STATES.setdefault(self.root, _MutationState())
        if not state.lock.acquire(blocking=False):
            raise RootBusyError(
                "The data root is busy with another save or backup; retry when it finishes."
            )
        self.state = state
        try:
            if state.depth == 0:
                state.lease = RootLease(
                    self.root,
                    exclusive=True,
                    filename=MUTATION_LOCK_FILENAME,
                    busy_message=(
                        "The data root is busy with another save or backup; "
                        "retry when it finishes."
                    ),
                )
                state.lease.__enter__()
            state.depth += 1
            self.entered = True
            return self
        except Exception:
            state.lock.release()
            raise

    def close(self):
        if not self.entered or self.state is None:
            return
        state = self.state
        self.entered = False
        try:
            state.depth -= 1
            if state.depth == 0 and state.lease is not None:
                state.lease.close()
                state.lease = None
        finally:
            state.lock.release()

    def __exit__(self, *_):
        self.close()
