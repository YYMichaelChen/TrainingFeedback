from datetime import datetime, timezone

import pytest

from training_feedback.domain.enums import SessionStatus
from training_feedback.domain.training import has_previous_day_label, transition_status


class FixedClock:
    def __init__(self, current):
        self.current = current

    def now(self):
        return self.current


@pytest.mark.parametrize("target", list(SessionStatus))
def test_open_can_transition_to_any_defined_status(target):
    transition_status(SessionStatus.OPEN, target)


def test_terminal_sessions_cannot_be_reopened():
    with pytest.raises(ValueError):
        transition_status(SessionStatus.COMPLETED, SessionStatus.OPEN)
    with pytest.raises(ValueError):
        transition_status(SessionStatus.ABORTED, SessionStatus.PAUSED)


def test_previous_day_label_uses_two_am_boundary():
    training_date = datetime(2026, 9, 3).date()
    before = FixedClock(datetime(2026, 9, 4, 1, 59, tzinfo=timezone.utc))
    at = FixedClock(datetime(2026, 9, 4, 2, 0, tzinfo=timezone.utc))
    after = FixedClock(datetime(2026, 9, 4, 2, 1, tzinfo=timezone.utc))

    assert not has_previous_day_label(training_date, SessionStatus.OPEN, before)
    assert has_previous_day_label(training_date, SessionStatus.OPEN, at)
    assert has_previous_day_label(training_date, SessionStatus.PAUSED, after)
    assert not has_previous_day_label(training_date, SessionStatus.COMPLETED, after)
