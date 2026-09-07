import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def data_path(tmp_path: Path) -> Path:
    return tmp_path / "training-data"
