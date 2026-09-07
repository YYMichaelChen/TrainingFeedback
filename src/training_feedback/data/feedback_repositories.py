"""次日反馈的 SQLite 仓储；备注修正走审计表，不改写历史。"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Any

from ..domain.enums import FeedbackValue
from ..domain.next_day import (
    can_submit_feedback,
    validate_feedback_values,
)
from ..domain.training import TERMINAL_STATUSES
from .database import transaction
from .session_repositories import SessionRepository


class FeedbackRepository:
    """次日反馈仓储：提交、查询与备注修正审计。"""

    def __init__(self, connection: sqlite3.Connection, execute=None):
        self.connection = connection
        self._execute = execute or connection.execute
        self.sessions = SessionRepository(connection)

    def get(self, session_id: int) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM next_day_feedback WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["areas"] = [
            dict(area)
            for area in self.connection.execute(
                "SELECT * FROM next_day_feedback_area WHERE feedback_id = ? ORDER BY id",
                (row["id"],),
            )
        ]
        result["audit"] = [
            dict(audit)
            for audit in self.connection.execute(
                "SELECT * FROM note_correction_audit WHERE feedback_id = ? ORDER BY id",
                (row["id"],),
            )
        ]
        return result

    def list_pending(self, current_date: date) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT s.id FROM training_session s "
            "LEFT JOIN next_day_feedback f ON f.session_id = s.id "
            "WHERE s.status IN (?, ?, ?) AND s.training_date < ? AND f.id IS NULL "
            "ORDER BY s.training_date DESC, s.id DESC",
            (
                *TERMINAL_STATUSES,
                current_date.isoformat(),
            ),
        ).fetchall()
        result = []
        for row in rows:
            session = self.sessions.get(row["id"])
            if session is not None and can_submit_feedback(session, current_date):
                result.append(session)
        return result

    def list_submitted(self, current_date: date) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT s.id FROM training_session s "
            "JOIN next_day_feedback f ON f.session_id = s.id "
            "WHERE s.training_date < ? ORDER BY s.training_date DESC, s.id DESC",
            (current_date.isoformat(),),
        ).fetchall()
        result = []
        for row in rows:
            session = self.sessions.get(row["id"])
            if session is not None:
                session["feedback"] = self.get(row["id"])
                result.append(session)
        return result

    def submit(
        self,
        session_id: int,
        values: dict[str, FeedbackValue | str | None],
        overall_note: str,
        current_date: date,
        submitted_at: datetime,
    ) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if session is None or not can_submit_feedback(session, current_date):
            raise ValueError("This session is not eligible for next-day feedback.")
        normalized = validate_feedback_values(session, values)
        if self.get(session_id) is not None:
            raise ValueError("Next-day feedback has already been submitted.")
        try:
            with transaction(self.connection):
                cursor = self._execute(
                    "INSERT INTO next_day_feedback(session_id, overall_note, submitted_at) "
                    "VALUES (?, ?, ?)",
                    (session_id, overall_note, submitted_at.isoformat()),
                )
                for area, value in normalized.items():
                    self._execute(
                        "INSERT INTO next_day_feedback_area("
                        "feedback_id, body_area_name_snapshot, value) "
                        "VALUES (?, ?, ?)",
                        (cursor.lastrowid, area, value.value if value is not None else None),
                    )
        except sqlite3.IntegrityError as exc:
            if "next_day_feedback.session_id" in str(exc):
                raise ValueError("Next-day feedback has already been submitted.") from exc
            raise
        return self.get(session_id)

    def history(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT id FROM training_session ORDER BY training_date DESC, id DESC"
        ).fetchall()
        result = []
        for row in rows:
            session = self.sessions.get(row["id"])
            if session is None:
                continue
            session["events"] = [
                dict(event)
                for event in self.connection.execute(
                    "SELECT * FROM session_event WHERE session_id = ? ORDER BY id",
                    (row["id"],),
                )
            ]
            session["feedback"] = self.get(row["id"])
            result.append(session)
        return result

    def correct_note(
        self,
        session_id: int,
        target: str,
        new_value: str,
        corrected_at: datetime,
    ) -> None:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError("Session was not found.")
        if target != "overall_note" and not target.startswith("action_note:"):
            raise ValueError("Only supported note fields can be corrected.")
        feedback = self.get(session_id)
        if feedback is None:
            raise ValueError("Feedback must be submitted before its note is corrected.")
        feedback_id = feedback["id"]
        action_id = None
        with transaction(self.connection):
            if target == "overall_note":
                old_value = feedback["overall_note"] or ""
                self._execute(
                    "UPDATE next_day_feedback SET overall_note = ? WHERE session_id = ?",
                    (new_value, session_id),
                )
            else:
                try:
                    action_id = int(target.split(":", 1)[1])
                except ValueError as exc:
                    raise ValueError("Invalid action note target.") from exc
                action = next(
                    (item for item in session["actions"] if item["id"] == action_id), None
                )
                if action is None:
                    raise ValueError("Session action was not found.")
                old_value = action.get("note") or ""
                self._execute(
                    "UPDATE training_session_action SET note = ? WHERE id = ?",
                    (new_value, action_id),
                )
            self._execute(
                "INSERT INTO note_correction_audit(session_id, feedback_id, session_action_id, "
                "target, old_value, new_value, corrected_at, operation) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    feedback_id,
                    action_id,
                    target,
                    old_value,
                    new_value,
                    corrected_at.isoformat(),
                    "note_correction",
                ),
            )
