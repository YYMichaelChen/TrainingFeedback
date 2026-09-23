"""启动协调：定位/选择数据根目录，打开旧格式根之前先完成一次性转换。与 Qt 入口解耦。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .app import LibraryContext
from .data.catalog_conversion import convert_catalog_root
from .data.data_root import DataRootAccessError, DataRootError
from .data.locator import Locator


def _record_locator(context: LibraryContext, locator: Locator) -> LibraryContext:
    """打开成功后才记录数据根位置；记录失败时释放上下文，不留下半开状态。"""
    try:
        locator.save(context.data_root.path)
    except OSError as exc:
        context.close()
        raise DataRootAccessError("Cannot record the data-root location.") from exc
    return context


def open_root(path: Path, locator: Locator) -> LibraryContext:
    """打开现有数据根：先恢复挂起的升级并完成一次性转换，再以当前模型打开。"""
    convert_catalog_root(path)
    return _record_locator(LibraryContext.reopen(path), locator)


def create_root(path: Path, locator: Locator) -> LibraryContext:
    """新建当前模型数据根并记录位置。"""
    return _record_locator(LibraryContext.create(path), locator)


def open_from_locator(
    locator: Locator,
    report_error: Callable[[DataRootError], None] | None = None,
) -> LibraryContext | None:
    """按 locator 打开上次的数据根；失败经 report_error 反馈后返回 None 以便重选。"""
    root = locator.load()
    if root is None:
        return None
    try:
        return open_root(root, locator)
    except DataRootError as exc:
        if report_error is None:
            raise
        report_error(exc)
        return None


def choose_data_root(
    locator: Locator,
    choose: Callable[[], tuple[Path, bool] | None],
    report_error: Callable[[DataRootError], None] | None = None,
) -> LibraryContext | None:
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
                return create_root(path, locator)
            return open_root(path, locator)
        except DataRootError as exc:
            if report_error is None:
                raise
            report_error(exc)
