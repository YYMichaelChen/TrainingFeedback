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
    report_error: Callable[[DataRootError], None] | None = None,
) -> ApplicationContext | None:
    """反复尝试打开所选数据根，直到成功或用户取消。

    只有 choose() 返回 None（用户取消）时才返回 None；失败经 report_error
    反馈后继续重选。未提供 report_error 时失败直接抛出，不静默吞错。
    """
    while True:
        selection = choose()
        if selection is None:
            return None
        path, create = selection
        try:
            if create:
                return ApplicationContext.create(path, locator)
            return ApplicationContext.reopen(path, locator)
        except DataRootError as exc:
            if report_error is None:
                raise
            report_error(exc)
