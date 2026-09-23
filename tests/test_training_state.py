from datetime import datetime, timezone

from training_feedback.domain.enums import SessionStatus
from training_feedback.domain.training import has_previous_day_label


class FixedClock:
    def __init__(self, current):
        self.current = current

    def now(self):
        return self.current


def test_previous_day_label_uses_two_am_boundary():
    training_date = datetime(2026, 9, 3).date()
    before = FixedClock(datetime(2026, 9, 4, 1, 59, tzinfo=timezone.utc))
    at = FixedClock(datetime(2026, 9, 4, 2, 0, tzinfo=timezone.utc))
    after = FixedClock(datetime(2026, 9, 4, 2, 1, tzinfo=timezone.utc))

    assert not has_previous_day_label(training_date, SessionStatus.OPEN, before)
    assert has_previous_day_label(training_date, SessionStatus.OPEN, at)
    assert has_previous_day_label(training_date, SessionStatus.PAUSED, after)
    assert not has_previous_day_label(training_date, SessionStatus.COMPLETED, after)
