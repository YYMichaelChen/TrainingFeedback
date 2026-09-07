"""训练会话状态机，以及"跨凌晨 2 点仍算前一天"的日期边界规则。"""

from datetime import date, datetime, time

from .clock import Clock
from .enums import SessionStatus

ACTIVE_STATUSES = frozenset((SessionStatus.OPEN, SessionStatus.PAUSED))
TERMINAL_STATUSES = frozenset(
    (SessionStatus.COMPLETED, SessionStatus.PARTIAL, SessionStatus.ABORTED)
)


def transition_status(current: SessionStatus, target: SessionStatus) -> None:
    allowed = {
        SessionStatus.OPEN: ACTIVE_STATUSES | TERMINAL_STATUSES,
        SessionStatus.PAUSED: ACTIVE_STATUSES | TERMINAL_STATUSES,
    }
    if current not in allowed or target not in allowed[current]:
        raise ValueError(f"Invalid session transition: {current} -> {target}.")


def is_active_session(status: SessionStatus | str) -> bool:
    return SessionStatus(status) in ACTIVE_STATUSES


def is_terminal_session(status: SessionStatus | str) -> bool:
    return SessionStatus(status) in TERMINAL_STATUSES


def has_previous_day_label(training_date: date, status: SessionStatus, clock: Clock) -> bool:
    if status not in ACTIVE_STATUSES:
        return False
    current = clock.now()
    boundary = datetime.combine(current.date(), time(2, 0), tzinfo=current.tzinfo)
    return current >= boundary and training_date < current.date()
