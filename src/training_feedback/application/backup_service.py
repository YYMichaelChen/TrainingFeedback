"""Application use case for one complete, staged data-root backup."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..data.backup import create_backup


class BackupService:
    def __init__(self, source_root: Path):
        self.source_root = Path(source_root)

    def create(
        self,
        destination: Path,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> Path:
        return create_backup(self.source_root, destination, cancelled=cancelled)
