"""应用组装：ApplicationContext 持有数据根目录、数据库连接并负责播种与关闭。"""

from __future__ import annotations

from pathlib import Path

from .application import TrainingApplicationService
from .data.data_root import DataRoot, create_new, open_existing
from .data.database import Database
from .data.locator import Locator
from .domain.clock import SystemClock


class ApplicationContext:
    def __init__(self, data_root: DataRoot, database: Database, locator: Locator):
        self.data_root = data_root
        self.database = database
        self.locator = locator

    @classmethod
    def open(cls, data_root: DataRoot, locator: Locator) -> "ApplicationContext":
        database = Database(data_root.database_path)
        try:
            database.__enter__()
            from .data.seed.catalog import seed_catalog
            from .data.seed.plans import seed_initial_proposal

            seed_catalog(database.connection)
            seed_initial_proposal(database.connection)
            locator.save(data_root.path)
            return cls(data_root, database, locator)
        except Exception:
            database.close()
            raise

    @classmethod
    def create(cls, path: Path, locator: Locator) -> "ApplicationContext":
        return cls.open(create_new(path), locator)

    @classmethod
    def reopen(cls, path: Path, locator: Locator) -> "ApplicationContext":
        return cls.open(open_existing(path), locator)

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
