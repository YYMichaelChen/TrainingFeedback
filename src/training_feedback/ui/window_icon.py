"""Owned application icon loading for Qt windows."""

from functools import lru_cache
from pathlib import Path

from PySide6.QtGui import QIcon


@lru_cache(maxsize=1)
def application_icon() -> QIcon:
    """Load the required runtime icon once and reject a missing/invalid resource."""
    path = Path(__file__).with_name("TrainingFeedback.ico")
    icon = QIcon(str(path))
    if icon.isNull():
        raise RuntimeError(f"Application icon resource is unavailable: {path}")
    return icon


def apply_application_icon(application) -> QIcon:
    """Set and return the process-wide icon used by parentless Qt dialogs."""
    icon = application_icon()
    application.setWindowIcon(icon)
    return icon


def apply_window_icon(window) -> None:
    """Explicitly set the owned icon on a top-level application window."""
    window.setWindowIcon(application_icon())
