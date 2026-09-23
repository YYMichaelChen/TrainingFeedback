import os
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

pytest_plugins = ["budget_plugin"]


@pytest.fixture(scope="session")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def destroy_test_windows():
    """每个用例结束后交给 Qt 销毁窗口，避免遗留窗口在 Python 垃圾回收时崩溃解释器。"""
    yield
    application = QApplication.instance()
    if application is None:
        return
    for window in application.topLevelWidgets():
        window.close()
        window.deleteLater()
    application.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture
def data_path(tmp_path: Path) -> Path:
    return tmp_path / "training-data"
