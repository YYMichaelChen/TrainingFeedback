"""A new data root is one validated Windows child of a selected parent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOT_DIRECTORY_NAME = "TrainingFeedbackData"
_INVALID = set('<>:"/\\|?*')
_RESERVED = {"CON", "PRN", "AUX", "NUL"}
_RESERVED.update(f"{prefix}{suffix}" for prefix in ("COM", "LPT")
                 for suffix in "123456789¹²³")


class InvalidRootNameError(ValueError):
    """The proposed child is not one valid Windows directory component."""


def validate_child_name(name: str) -> str:
    """Return the original text; never trim or rewrite a user's chosen name."""
    if (not isinstance(name, str) or not name or name in {".", ".."}
            or name[-1] in {".", " "}
            or any(character in _INVALID or ord(character) < 32 for character in name)
            or len(name.encode("utf-16-le")) // 2 > 255
            or name.split(".", 1)[0].upper() in _RESERVED):
        raise InvalidRootNameError("Choose one valid Windows directory name.")
    return name


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
