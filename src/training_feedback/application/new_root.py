"""A new data root is one validated Windows child of a selected parent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..domain.windows_paths import InvalidRootNameError, validate_child_name  # noqa: F401

DEFAULT_ROOT_DIRECTORY_NAME = "TrainingFeedbackData"


@dataclass(frozen=True)
class NewRootProposal:
    parent: Path
    name: str

    def __post_init__(self) -> None:
        validate_child_name(self.name)
        if not self.parent.is_absolute() or not self.parent.is_dir():
            raise ValueError("Choose an existing parent directory.")

    @property
    def target(self) -> Path:
        return self.parent / self.name

    @property
    def preview(self) -> str:
        return str(self.target)
