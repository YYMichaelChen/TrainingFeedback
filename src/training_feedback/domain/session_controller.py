"""单次训练执行的可变状态控制器：start/resume/record/pause/abort/finish。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .clock import Clock
from .enums import AbortReason, ExerciseResult, SessionStatus
from .models import ActualSet, SessionActionResult
from .training import is_active_session


@dataclass
class SessionController:
    sessions: object
    plans: object
    exercises: object
    clock: Clock
    session: dict | None = None

    def start(self, plan_id: int, day_order: int | None = None) -> dict:
        plan = self.plans.get_plan(plan_id)
        if plan is None:
            raise ValueError("Plan was not found.")
        revision_id = plan.get("active_revision_id")
        if revision_id is None:
            raise ValueError("An active plan revision is required to start training.")
        revision = self.plans.get_revision(plan_id, revision_id)
        session_id = self.sessions.create_from_plan(
            revision, self.exercises, self.clock.today(), self.clock.now(), day_order
        )
        self.session = self.sessions.get(session_id)
        return self.session

    def resume(self, session_id: int | None = None) -> dict:
        session = (
            self.sessions.get(session_id)
            if session_id is not None
            else self.sessions.get_active()
        )
        if session is None:
            raise ValueError("No open or paused session was found.")
        if not is_active_session(session["status"]):
            raise ValueError("Only open or paused sessions can be resumed.")
        if session["status"] == SessionStatus.PAUSED:
            self.sessions.resume(session["id"], self.clock.now())
            session = self.sessions.get(session["id"])
        self.session = session
        return session

    def first_unfinished_index(self) -> int:
        """第一个未记录结果的动作下标；全部完成时返回最后一项（供 UI 定位展示）。"""
        if self.session is None:
            raise RuntimeError("No session is loaded.")
        return next(
            (
                index
                for index, action in enumerate(self.session["actions"])
                if action["result"] is None
            ),
            len(self.session["actions"]) - 1,
        )

    @property
    def training_date(self) -> date:
        if self.session is None:
            raise RuntimeError("No session is loaded.")
        return date.fromisoformat(self.session["training_date"])

    def record_result(
        self,
        action_id: int,
        result: ExerciseResult,
        actual_values: tuple[float | None, ...] = (),
        note: str = "",
        actual_sets: tuple[ActualSet, ...] = (),
    ) -> dict:
        if self.session is None:
            raise RuntimeError("No session is loaded.")
        self.sessions.record_action_result(
            self.session["id"],
            action_id,
            SessionActionResult(result, actual_values, note, actual_sets),
            self.clock.now(),
        )
        self.session = self.sessions.get(self.session["id"])
        return self.session

    def pause(self) -> dict:
        return self._change_status(SessionStatus.PAUSED)

    def abort(self, reason: AbortReason, note: str = "") -> dict:
        return self._change_status(SessionStatus.ABORTED, reason, note)

    def finish(self) -> dict:
        if self.session is None:
            raise RuntimeError("No session is loaded.")
        self.sessions.finish(self.session["id"], self.clock.now())
        self.session = self.sessions.get(self.session["id"])
        return self.session

    def _change_status(
        self,
        status: SessionStatus,
        reason: AbortReason | None = None,
        note: str | None = None,
    ) -> dict:
        if self.session is None:
            raise RuntimeError("No session is loaded.")
        self.sessions.change_status(self.session["id"], status, self.clock.now(), reason, note)
        self.session = self.sessions.get(self.session["id"])
        return self.session
