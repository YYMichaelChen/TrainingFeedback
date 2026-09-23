"""0.5.1：审核发生时间的一键填入，且字段绝不自动预填。"""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from PySide6.QtWidgets import QLineEdit

from training_feedback.domain.exercises import require_review_occurrence
from training_feedback.ui import review_occurrence
from training_feedback.ui.review_occurrence import OccurrenceQuickFill, now_text, today_text


class _FixedClock:
    def __init__(self, moment: datetime):
        self.moment = moment

    def now(self) -> datetime:
        return self.moment


@pytest.fixture(autouse=True)
def _clean_state():
    review_occurrence.clear_remembered_occurrence()
    yield
    review_occurrence.clear_remembered_occurrence()


def test_utc_moment_is_converted_to_local_before_filling():
    # 本机时区决定「今天」是哪一天；UTC 值必须先转本地再取日期。
    moment = datetime(2026, 9, 13, 23, 30, tzinfo=UTC)
    local = moment.astimezone()

    assert today_text(moment) == local.date().isoformat()
    require_review_occurrence(now_text(moment))


def test_previous_occurrence_is_offered_only_after_an_actual_approval(qt_app):
    clock = _FixedClock(datetime(2026, 9, 13, 20, 31, tzinfo=timezone(timedelta(hours=8))))
    target = QLineEdit()
    quick_fill = OccurrenceQuickFill(target, clock)
    # 输入框保持空白；没有批准过的发生时间时「沿用上次」不可用。
    assert target.text() == ""
    assert not quick_fill.reuse_button.isEnabled()

    quick_fill.fill_today()
    assert target.text() == "2026-09-13"
    # 仅填入不算批准：仍未记住可沿用的值。
    assert review_occurrence.last_occurrence() is None

    review_occurrence.remember_occurrence("2026-09-12")
    second_target = QLineEdit()
    second = OccurrenceQuickFill(second_target, clock)
    assert second_target.text() == ""
    assert second.reuse_button.isEnabled()
    second.fill_previous()
    assert second_target.text() == "2026-09-12"
