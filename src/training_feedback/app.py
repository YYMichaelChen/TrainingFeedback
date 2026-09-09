"""应用组装：ApplicationContext 持有数据根目录、数据库连接并负责播种与关闭。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .application import TrainingApplicationService
from .data.data_root import DataRoot, DataRootAccessError, create_new, open_existing
from .data.database import Database
from .data.locator import Locator
from .domain.clock import SystemClock
from .domain.enums import SessionStatus


class ApplicationContext:
    def __init__(self, data_root: DataRoot, database: Database, locator: Locator | None = None):
        self.data_root = data_root
        self.database = database
        self.locator = locator

    @classmethod
    def _connect(cls, data_root: DataRoot) -> "ApplicationContext":
        """连接、迁移并播种；不写 locator，失败时释放连接。"""
        database = Database(data_root.database_path)
        try:
            database.__enter__()
            from .data.seed.catalog import seed_catalog
            from .data.seed.plans import seed_initial_proposal

            seed_catalog(database.connection)
            seed_initial_proposal(database.connection)
            return cls(data_root, database)
        except Exception:
            database.close()
            raise

    @classmethod
    def open(cls, data_root: DataRoot, locator: Locator) -> "ApplicationContext":
        context = cls._connect(data_root)
        try:
            locator.save(data_root.path)
        except OSError as exc:
            context.close()
            raise DataRootAccessError("Cannot record the data-root location.") from exc
        context.locator = locator
        return context

    @classmethod
    def create(cls, path: Path, locator: Locator) -> "ApplicationContext":
        return cls.open(create_new(path), locator)

    @classmethod
    def reopen(cls, path: Path, locator: Locator) -> "ApplicationContext":
        return cls.open(open_existing(path), locator)

    @classmethod
    def prepare_candidate(cls, path: Path, create: bool = False) -> "ApplicationContext":
        """为切换准备候选上下文：校验、连接并播种，但不写 locator。"""
        data_root = create_new(path) if create else open_existing(path)
        return cls._connect(data_root)

    def close(self) -> None:
        self.database.close()

    def training_service(self) -> TrainingApplicationService:
        """Build the application workflow with repositories from this context."""
        from .data.exercise_repositories import ExerciseRepository
        from .data.plan_repositories import PlanRepository
        from .data.session_repositories import SessionRepository

        exercises = ExerciseRepository(self.database.connection)
        return TrainingApplicationService(
            SessionRepository(self.database.connection),
            PlanRepository(self.database.connection, exercises),
            exercises,
            SystemClock(),
        )

    # 以下为 UI 统一使用的仓储/服务工厂，避免各页面自行组装连接。

    def session_repository(self):
        from .data.session_repositories import SessionRepository

        return SessionRepository(self.database.connection)

    def feedback_repository(self):
        from .data.feedback_repositories import FeedbackRepository

        return FeedbackRepository(self.database.connection)

    def feedback_service(self, clock=None):
        from .application.feedback_service import FeedbackApplicationService

        return FeedbackApplicationService(self.feedback_repository(), clock or SystemClock())

    def plan_repository(self):
        from .data.exercise_repositories import ExerciseRepository
        from .data.plan_repositories import PlanRepository

        return PlanRepository(
            self.database.connection, ExerciseRepository(self.database.connection)
        )

    def exercise_service(self):
        from .application.exercise_service import ExerciseService
        from .data.exercise_repositories import ExerciseRepository

        return ExerciseService(ExerciseRepository(self.database.connection))


class DataRootSwitcher:
    """数据根切换协调：准备候选 → 构建窗口 → 提交 locator → 替换窗口 → 关闭旧上下文。

    任一步失败都保留原窗口、原 locator 和原数据库可用，并关闭候选资源；
    同一路径视为无操作。UI 窗口通过注入的 build_window 工厂创建，
    本类不依赖 Qt。
    """

    def __init__(self, context: ApplicationContext, locator: Locator):
        self.context = context
        self.locator = locator
        self.window = None

    def attach(self, window) -> None:
        """登记当前主窗口（启动时与每次成功切换后调用）。"""
        self.window = window

    def switch(self, path: Path, create: bool, build_window: Callable) -> bool:
        """切换到指定数据根；同路径无操作返回 False，成功切换返回 True。"""
        target = Path(path).resolve()
        if target == Path(self.context.data_root.path).resolve():
            return False
        active = self.context.session_repository().get_active()
        if active and active["status"] == SessionStatus.OPEN:
            raise ValueError("Pause the active training session before switching data roots.")
        candidate = ApplicationContext.prepare_candidate(target, create)
        try:
            new_window = build_window(candidate)
        except Exception:
            candidate.close()
            raise
        try:
            self.locator.save(candidate.data_root.path)
        except OSError as exc:
            new_window.close()
            new_window.deleteLater()
            candidate.close()
            raise DataRootAccessError("Cannot record the data-root location.") from exc
        candidate.locator = self.locator
        old_window, old_context = self.window, self.context
        self.context = candidate
        self.window = new_window
        new_window.show()
        if old_window is not None:
            old_window.close()
            old_window.deleteLater()
        old_context.close()
        return True
