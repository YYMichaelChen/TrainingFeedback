"""训练执行工作流的应用服务入口：SessionController 的惰性工厂与透传。"""

from __future__ import annotations

from dataclasses import dataclass

from ..data.exercise_repositories import ExerciseRepository
from ..data.plan_repositories import PlanRepository
from ..data.session_repositories import SessionRepository
from ..domain.clock import Clock
from ..domain.enums import AbortReason, ExerciseResult
from ..domain.models import ActualSet
from ..domain.session_controller import SessionController


@dataclass
class TrainingApplicationService:
    """Coordinate one mutable training execution through a session controller."""

    sessions: SessionRepository
    plans: PlanRepository
    exercises: ExerciseRepository
    clock: Clock
    controller: SessionController | None = None

    def _controller(self) -> SessionController:
        if self.controller is None:
            self.controller = SessionController(
                self.sessions, self.plans, self.exercises, self.clock
            )
        return self.controller

    @property
    def session(self) -> dict | None:
        return self._controller().session

    def load(self, session: dict) -> dict:
        self._controller().session = session
        return session

    def start(self, plan_id: int, day_order: int | None = None) -> dict:
        return self._controller().start(plan_id, day_order)

    def resume(self, session_id: int | None = None) -> dict:
        return self._controller().resume(session_id)

    def first_unfinished_index(self) -> int:
        return self._controller().first_unfinished_index()

    def record_result(
        self,
        action_id: int,
        result: ExerciseResult,
        actual_values: tuple[float | None, ...] = (),
        note: str = "",
        actual_sets: tuple[ActualSet, ...] = (),
    ) -> dict:
        return self._controller().record_result(
            action_id, result, actual_values, note, actual_sets
        )

    def retract_result(self, action_id: int) -> dict:
        return self._controller().retract_result(action_id)

    def pause(self) -> dict:
        return self._controller().pause()

    def abort(self, reason: AbortReason, note: str = "") -> dict:
        return self._controller().abort(reason, note)

    def finish(self) -> dict:
        return self._controller().finish()
