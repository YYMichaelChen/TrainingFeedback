"""次日反馈用例服务：为 UI 编排日期、提交与备注修正。"""

from __future__ import annotations

from dataclasses import dataclass

from ..data.feedback_repositories import FeedbackRepository
from ..domain.clock import Clock
from ..domain.enums import FeedbackValue
from ..domain.next_day import feedback_areas


@dataclass
class FeedbackApplicationService:
    """协调次日反馈用例，避免页面直接编排时间和写入操作。"""

    repository: FeedbackRepository
    clock: Clock

    def areas(self, session: dict) -> tuple[str, ...]:
        return feedback_areas(session)

    def list_pending(self) -> list[dict]:
        return self.repository.list_pending(self.clock.today())

    def list_submitted(self) -> list[dict]:
        return self.repository.list_submitted(self.clock.today())

    def get(self, session_id: int) -> dict | None:
        return self.repository.get(session_id)

    def history(self) -> list[dict]:
        return self.repository.history()

    def submit(
        self,
        session_id: int,
        values: dict[str, FeedbackValue | str | None],
        overall_note: str,
    ) -> dict:
        return self.repository.submit(
            session_id,
            values,
            overall_note,
            self.clock.today(),
            self.clock.now(),
        )

    def correct_note(self, session_id: int, target: str, new_value: str) -> None:
        self.repository.correct_note(session_id, target, new_value, self.clock.now())
