"""应用组装：LibraryContext 持有数据根、数据库与当前模型服务；DataRootSwitcher 协调切换。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .application.new_root import validate_child_name
from .data.data_root import (
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    MANAGED_DIRECTORIES,
    MARKER_FILENAME,
    DataRootAccessError,
    DataRootNotEmptyError,
    ExistingDataRootError,
    create_new,
    inspect_existing,
    open_existing,
)
from .data.database import Database
from .data.locator import Locator


class LibraryContext:
    """当前模型的桌面组合根：打开根目录不播种，服务/页面工厂集中在这里。"""

    def __init__(self, data_root, database, catalog):
        from .application.group_plan_service import GroupPlanService
        from .application.group_session_service import GroupSessionService
        from .application.library_lifecycle_service import LibraryLifecycleService
        from .application.library_workflow import LibraryWorkflowService
        from .data.database import transaction
        from .data.group_plan_handoff import GroupPlanHandoff
        from .data.group_plan_repository import GroupPlanRepository
        from .data.group_session_handoff import GroupSessionHandoff
        from .data.group_session_repository import GroupSessionRepository
        from .data.library_lifecycle_repository import LibraryLifecycleRepository
        from .data.library_repository import LibraryRepository
        from .data.snapshot_assets import SnapshotAssets

        self.data_root = data_root
        self.database = database
        self.catalog = catalog
        self.user_library = LibraryRepository(database.connection)
        self.snapshot_assets = SnapshotAssets(data_root.path)
        with transaction(database.connection, immediate=True):
            self.snapshot_assets.recover_unreferenced(self.user_library.asset_hashes())
        self.library = LibraryWorkflowService(
            catalog, self.user_library, self.snapshot_assets, data_root.path,
        )
        self.removals = LibraryLifecycleService(
            self.library, LibraryLifecycleRepository(database.connection, data_root.path),
        )
        self.removals.sync_publisher()
        self.plans = GroupPlanService(GroupPlanRepository(database.connection), self.library)
        self.plan_handoff = GroupPlanHandoff(self.plans, data_root.path)
        self.sessions = GroupSessionService(GroupSessionRepository(database.connection), self.plans)
        self.session_handoff = GroupSessionHandoff(self.sessions, self.plan_handoff)

    @classmethod
    def create(cls, path: Path, *, catalog_path: Path | None = None):
        from .data.catalog_repository import CatalogRepository
        from .data.library_root import initialize_library_root

        catalog = CatalogRepository(catalog_path)
        try:
            root = create_new(path)
            initialize_library_root(root.path)
            return cls._connect(root, catalog)
        except Exception:
            catalog.close()
            raise

    @classmethod
    def reopen(cls, path: Path, *, catalog_path: Path | None = None):
        """打开当前模型根；过期数据库在只读检查阶段被拒绝。"""
        from .data.catalog_repository import CatalogRepository
        from .data.library_root import require_library_root

        inspect_existing(path)
        require_library_root(path)
        catalog = CatalogRepository(catalog_path)
        try:
            return cls._connect(open_existing(path), catalog)
        except Exception:
            catalog.close()
            raise

    @classmethod
    def _connect(cls, root, catalog):
        database = Database(root.database_path)
        try:
            database.__enter__()
            return cls(root, database, catalog)
        except Exception:
            database.close()
            raise

    def close(self):
        try:
            self.catalog.close()
        finally:
            self.database.close()

    def switch(self, path: Path):
        """Prepare a different library root fully before releasing this context."""
        if Path(path).resolve() == self.data_root.path.resolve():
            return self
        active = self.sessions.active()
        if active and active["status"] == "open":
            raise ValueError("Pause the active training session before switching data roots.")
        candidate = type(self).reopen(path, catalog_path=self.catalog.directory)
        self.close()
        return candidate

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def create_library_page(self, parent=None, *, progressive=False):
        from .ui.catalog_library_page import CatalogLibraryPage

        return CatalogLibraryPage(
            self.library, parent, removals=self.removals, progressive=progressive,
        )


    def create_removal_page(self, parent=None):
        from .ui.library_lifecycle_page import LibraryLifecyclePage

        return LibraryLifecyclePage(self.removals, parent)

    def create_plan_page(self, parent=None):
        from .ui.group_plan_page import GroupPlanPage

        return GroupPlanPage(self.plans, self.plan_handoff, parent)

    def session_controller(self):
        from .domain.session_controller import GroupSessionController

        return GroupSessionController(self.sessions)

    def create_training_page(self, controller, parent=None):
        from .ui.group_training_page import GroupTrainingPage

        return GroupTrainingPage(controller, parent)

    def create_session_page(self, parent=None):
        from .ui.group_session_page import GroupSessionPage

        return GroupSessionPage(self, parent)


class RootCreation:
    """Own a new root until context and locator/window commit have succeeded."""

    def __init__(self, target: Path):
        self.target = Path(target)
        self.created_child = False
        self.owns_artifacts = False
        self.context = None

    def prepare(self) -> LibraryContext:
        from .data.library_root import require_library_root

        target = self.target
        validate_child_name(target.name)
        try:
            if target.is_symlink():
                raise DataRootNotEmptyError("The selected path is not an empty directory.")
            exists = target.exists()
            if exists:
                if not target.is_dir():
                    raise DataRootNotEmptyError("The selected path is not an empty directory.")
                if any(target.iterdir()):
                    inspect_existing(target)
                    require_library_root(target)
                    raise ExistingDataRootError("This is already a data root. Open it explicitly.")
            elif not target.parent.is_dir():
                raise DataRootAccessError("Cannot create the data root.")
            self.created_child = not exists
            self.owns_artifacts = True
            self.context = LibraryContext.create(target)
            return self.context
        except OSError as exc:
            self.rollback()
            raise DataRootAccessError("Cannot create the data root.") from exc
        except Exception:
            self.rollback()
            raise

    def rollback(self) -> None:
        if not self.owns_artifacts:
            return
        if self.context is not None:
            self.context.close()
            self.context = None
        # Only remove names created by root initialization. Never sweep unknown files.
        for name in (MARKER_FILENAME, DATABASE_FILENAME + "-shm", DATABASE_FILENAME + "-wal",
                     DATABASE_FILENAME + "-journal", ".training-feedback.lock",
                     DATABASE_FILENAME, CONFIG_FILENAME):
            path = self.target / name
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
        for name in (*MANAGED_DIRECTORIES, "custom-exercise-images", "snapshot-assets"):
            path = self.target / name
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        if self.created_child:
            try:
                self.target.rmdir()
            except OSError:
                pass


class DataRootSwitcher:
    """数据根切换协调：准备候选 → 构建窗口 → 提交 locator → 替换窗口 → 关闭旧上下文。

    任一步失败都保留原窗口、原 locator 和原数据库可用，并关闭候选资源；
    同一路径视为无操作。UI 窗口通过注入的 build_window 工厂创建，
    本类不依赖 Qt。过期根在只读检查阶段被拒绝。
    """

    def __init__(self, context: LibraryContext, locator: Locator):
        self.context = context
        self.locator = locator
        self.window = None

    def attach(self, window) -> None:
        """登记当前主窗口（启动时与每次成功切换后调用）。"""
        self.window = window

    @staticmethod
    def prepare(path: Path, create: bool) -> LibraryContext:
        """准备候选上下文：新建或打开当前模型根；不写 locator。"""
        target = Path(path)
        if create:
            return RootCreation(target).prepare()
        return LibraryContext.reopen(target)

    def switch(self, path: Path, create: bool, build_window: Callable) -> bool:
        """切换到指定数据根；同路径无操作返回 False，成功切换返回 True。"""
        target = Path(path)
        if target.resolve() == Path(self.context.data_root.path).resolve():
            return False
        active = self.context.sessions.active()
        if active and active["status"] == "open":
            raise ValueError("Pause the active training session before switching data roots.")
        creation = RootCreation(target) if create else None
        candidate = creation.prepare() if creation else self.prepare(target, False)
        try:
            new_window = build_window(candidate)
        except Exception:
            if creation:
                creation.rollback()
            else:
                candidate.close()
            raise
        try:
            self.locator.save(candidate.data_root.path)
        except OSError as exc:
            new_window.close()
            new_window.deleteLater()
            if creation:
                creation.rollback()
            else:
                candidate.close()
            raise DataRootAccessError("Cannot record the data-root location.") from exc
        old_window, old_context = self.window, self.context
        self.context = candidate
        self.window = new_window
        new_window.show()
        if old_window is not None:
            old_window.close()
            old_window.deleteLater()
        old_context.close()
        return True
