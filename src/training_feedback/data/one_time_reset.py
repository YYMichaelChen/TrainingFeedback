"""Read-only refusal of unfinished historical reset operations."""

import sqlite3
from contextlib import closing
from pathlib import Path


class ResetRecoveryError(OSError):
    """A historical operation remains unfinished and cannot be resumed."""


def prepare_existing_root(root: Path) -> None:
    """Reject pending historical cleanup without changing the root or files."""
    uri = (Path(root) / "training_feedback.sqlite3").resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='one_time_reset_journal'"
        ).fetchone()
        if present and connection.execute(
            "SELECT 1 FROM one_time_reset_journal LIMIT 1"
        ).fetchone():
            raise ResetRecoveryError(
                "An unfinished historical reset is unsupported. Create a new empty "
                "data root; the original root and files are preserved."
            )
