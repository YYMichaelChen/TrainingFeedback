"""0.5.1：审核发生时间的一键填入，且字段绝不自动预填。"""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from training_feedback.app import ApplicationContext
from training_feedback.data.data_root import create_new
from training_feedback.data.locator import Locator
from training_feedback.domain.exercises import require_review_occurrence
from training_feedback.ui import review_occurrence
from training_feedback.ui.guidance_batch_review_page import GuidanceBatchReviewDialog
from training_feedback.ui.guidance_review_page import GuidanceReviewDialog
from training_feedback.ui.review_occurrence import now_text, today_text


class _FixedClock:
    def __init__(self, moment: datetime):
        self.moment = moment

    def now(self) -> datetime:
        return self.moment


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    review_occurrence.clear_remembered_occurrence()
    for name in ("information", "warning", "critical"):
        monkeypatch.setattr(QMessageBox, name, lambda *_args, **_kwargs: None)
    yield
    review_occurrence.clear_remembered_occurrence()


def _context(tmp_path, clock=None):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    return context, context.exercise_service(clock)


def test_quick_fill_values_are_accepted_occurrences():
    moment = datetime(2026, 9, 13, 20, 31, 47, 123456, tzinfo=timezone(timedelta(hours=8)))

    assert today_text(moment) == "2026-09-13"
    assert now_text(moment) == "2026-09-13T20:31+08:00"
    require_review_occurrence(today_text(moment))
    require_review_occurrence(now_text(moment))


def test_utc_moment_is_converted_to_local_before_filling():
    # 本机时区决定「今天」是哪一天；UTC 值必须先转本地再取日期。
    moment = datetime(2026, 9, 13, 23, 30, tzinfo=UTC)
    local = moment.astimezone()

    assert today_text(moment) == local.date().isoformat()
    require_review_occurrence(now_text(moment))


def test_batch_dialog_never_prefills_the_occurrence(qt_app, tmp_path):
    context, service = _context(tmp_path)
    dialog = GuidanceBatchReviewDialog(service)

    assert dialog.reviewed_at_edit.text() == ""
    assert dialog.occurrence_quick_fill.reuse_button.isEnabled() is False
    dialog.close()
    context.close()


def test_quick_fill_buttons_write_into_the_field(qt_app, tmp_path):
    clock = _FixedClock(
        datetime(2026, 9, 13, 20, 31, tzinfo=timezone(timedelta(hours=8)))
    )
    context, service = _context(tmp_path, clock)
    dialog = GuidanceBatchReviewDialog(service)

    dialog.occurrence_quick_fill.fill_today()
    assert dialog.reviewed_at_edit.text() == "2026-09-13"

    dialog.occurrence_quick_fill.fill_now()
    assert dialog.reviewed_at_edit.text() == "2026-09-13T20:31+08:00"

    dialog.reviewed_at_edit.setText("2026-09-11")
    assert dialog.reviewed_at_edit.text() == "2026-09-11"
    dialog.close()
    context.close()


def test_previous_occurrence_is_offered_only_after_an_actual_approval(qt_app, tmp_path):
    clock = _FixedClock(
        datetime(2026, 9, 13, 20, 31, tzinfo=timezone(timedelta(hours=8)))
    )
    context, service = _context(tmp_path, clock)
    first = GuidanceBatchReviewDialog(service)
    row = next(
        index
        for index in range(first.revision_list.count())
        if first.items[index]["exercise_name"] == "臀桥"
    )
    first.revision_list.item(row).setCheckState(Qt.CheckState.Checked)
    first.source_edit.setText("外部 AI 会话 C")
    first.reviewed_at_edit.setText("2026-09-12")
    first.approved.setChecked(True)
    first._approve()
    assert first.approved_count == 1

    second = GuidanceBatchReviewDialog(service)
    assert second.reviewed_at_edit.text() == ""
    assert second.occurrence_quick_fill.reuse_button.isEnabled() is True

    second.occurrence_quick_fill.fill_previous()
    assert second.reviewed_at_edit.text() == "2026-09-12"
    second.close()
    context.close()


def test_failed_approval_does_not_remember_an_occurrence(qt_app, tmp_path):
    context, service = _context(tmp_path)
    dialog = GuidanceBatchReviewDialog(service)
    row = next(
        index
        for index in range(dialog.revision_list.count())
        if dialog.items[index]["exercise_name"] == "臀桥"
    )
    dialog.revision_list.item(row).setCheckState(Qt.CheckState.Checked)
    dialog.source_edit.setText("外部 AI")
    dialog.reviewed_at_edit.setText("昨天")
    dialog.approved.setChecked(True)

    dialog._approve()

    assert dialog.approved_count == 0
    assert review_occurrence.last_occurrence() is None
    dialog.close()
    context.close()


def test_single_review_dialog_offers_quick_fill_without_prefilling(qt_app, tmp_path):
    clock = _FixedClock(
        datetime(2026, 9, 13, 20, 31, tzinfo=timezone(timedelta(hours=8)))
    )
    context, service = _context(tmp_path, clock)
    exercise = service.repository.get(
        service.repository.get_by_canonical_name("臀桥")["id"]
    )
    dialog = GuidanceReviewDialog(service, exercise)

    assert dialog.reviewed_at_edit.text() == ""
    dialog.occurrence_quick_fill.fill_today()
    assert dialog.reviewed_at_edit.text() == "2026-09-13"
    dialog.close()
    context.close()
