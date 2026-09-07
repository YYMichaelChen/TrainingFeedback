"""时钟抽象：让日期边界行为在测试中可替换、可复现。"""

from datetime import date, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now().astimezone()

    def today(self) -> date:
        return self.now().date()
