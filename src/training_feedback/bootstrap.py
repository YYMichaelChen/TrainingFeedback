"""启动协调：定位/选择数据根目录。与 Qt 入口解耦，便于无界面测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .app import ApplicationContext
from .data.data_root import DataRootError
from .data.locator import Locator


def open_from_locator(locator: Locator) -> ApplicationContext | None:
    root = locator.load()
    if root is None:
        return None
    try:
        return ApplicationContext.reopen(root, locator)
    except DataRootError:
        return None


def choose_data_root(
    locator: Locator,
    choose: Callable[[], tuple[Path, bool] | None],
) -> ApplicationContext | None:
    selection = choose()
    if selection is None:
        return None
    path, create = selection
    try:
        if create:
            return ApplicationContext.create(path, locator)
        return ApplicationContext.reopen(path, locator)
    except DataRootError:
        return None
