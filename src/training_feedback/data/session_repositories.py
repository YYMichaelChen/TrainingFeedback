"""训练会话的 SQLite 仓储；会话创建时冻结计划与动作快照。"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..domain.enums import ExerciseResult, SessionStatus
from ..domain.models import SessionActionResult, derive_final_status
from ..domain.training import (
    ACTIVE_STATUSES,
    is_active_session,
    is_terminal_session,
    transition_status,
)
from .database import transaction


class SessionRepository:
    """会话仓储：从计划修订创建快照会话，记录结果与状态流转。"""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get_active(self) -> dict[str, Any] | None:
        rows = self.connection.execute(
            "SELECT * FROM training_session WHERE status IN (?, ?) ORDER BY id",
            tuple(ACTIVE_STATUSES),
        ).fetchall()
        if len(rows) > 1:
            raise ValueError("Multiple open or paused sessions were found.")
        return self.get(rows[0]["id"]) if rows else None

    def get(self, session_id: int) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM training_session WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["actions"] = []
        for action in self.connection.execute(
            "SELECT * FROM training_session_action WHERE session_id = ? "
            "ORDER BY plan_day_order, plan_action_order",
            (session_id,),
        ):
            item = dict(action)
            item["body_area_snapshots"] = json.loads(item.pop("body_areas_snapshot_json"))
            item["body_areas"] = [area["name"] for area in item["body_area_snapshots"]]
            item["sets"] = [
                dict(planned_set)
                for planned_set in self.connection.execute(
                    "SELECT * FROM training_session_set WHERE session_action_id = ? "
                    "ORDER BY set_order",
                    (action["id"],),
                )
            ]
            item["actual_sets"] = [
                dict(actual_set)
                for actual_set in self.connection.execute(
                    "SELECT * FROM training_session_actual_set WHERE session_action_id = ? "
                    "ORDER BY actual_order",
                    (action["id"],),
                )
            ]
            if not item["actual_sets"]:
                # 兼容 v12 之前的旧数据：当时实际剂量只写在计划组的 actual_* 列上。
                item["actual_sets"] = [
                    {
                        "actual_order": planned_set["set_order"],
                        "value": planned_set["actual_value"],
                        "unit": planned_set["actual_unit"],
                        "per_side": planned_set["actual_per_side"],
                    }
                    for planned_set in item["sets"]
                    if planned_set["actual_value"] is not None
                ]
            result["actions"].append(item)
        result["result_retractions"] = [
            {
                "id": audit["id"],
                "session_action_id": audit["session_action_id"],
                "previous_action": json.loads(audit["previous_action_json"]),
                "retracted_at": audit["retracted_at"],
            }
            for audit in self.connection.execute(
                "SELECT * FROM session_result_retraction WHERE session_id = ? ORDER BY id",
                (session_id,),
            )
        ]
        return result

    def create_from_plan(
        self,
        revision: dict[str, Any],
        exercises,
        training_date,
        now,
        day_order: int | None = None,
    ) -> int:
        if day_order is None:
            if len(revision["days"]) != 1:
                raise ValueError("A plan day must be selected before starting training.")
            selected_day = revision["days"][0]
        else:
            selected_day = next(
                (day for day in revision["days"] if day["day_order"] == day_order), None
            )
            if selected_day is None:
                raise ValueError("The selected plan day was not found.")
        with transaction(self.connection, immediate=True):
            if self.get_active() is not None:
                raise ValueError("An open or paused session already exists.")
            cursor = self.connection.execute(
                "INSERT INTO training_session(plan_revision_id, training_date, status, "
                "started_at, updated_at, plan_day_order, plan_day_name_snapshot) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    revision["id"],
                    training_date.isoformat(),
                    SessionStatus.OPEN,
                    now.isoformat(),
                    now.isoformat(),
                    selected_day["day_order"],
                    selected_day["name"],
                ),
            )
            session_id = cursor.lastrowid
            for session_action_order, action in enumerate(selected_day["actions"], 1):
                exercise = exercises.get(action["exercise_id"])
                if exercise is None:
                    raise ValueError(f"Exercise {action['exercise_id']} was not found.")
                areas = [
                    {"name": area["name"], "is_primary": bool(area["is_primary"])}
                    for area in exercise["body_areas"]
                ]
                action_cursor = self.connection.execute(
                    "INSERT INTO training_session_action(session_id, action_order, "
                    "plan_day_order, exercise_id, plan_action_order, exercise_name_snapshot, "
                    "body_areas_snapshot_json, guidance_revision_id, note, phase_snapshot, "
                    "rest_seconds_snapshot, plan_note_snapshot) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        session_id,
                        session_action_order,
                        selected_day["day_order"],
                        action["exercise_id"],
                        action["action_order"],
                        exercise["canonical_name"],
                        json.dumps(areas, ensure_ascii=False),
                        exercise.get("active_guidance_revision_id"),
                        None,
                        action["phase"],
                        action["rest_seconds"],
                        action["note"],
                    ),
                )
                for planned_set in action["sets"]:
                    self.connection.execute(
                        "INSERT INTO training_session_set(session_action_id, set_order, "
                        "planned_value, planned_unit, planned_per_side, actual_value, "
                        "actual_unit, actual_per_side, plan_note_snapshot) "
                        "VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?)",
                        (
                            action_cursor.lastrowid,
                            planned_set["set_order"],
                            planned_set["value"],
                            planned_set["unit"],
                            planned_set["per_side"],
                            planned_set["note"],
                        ),
                    )
            return session_id

    def record_action_result(
        self, session_id: int, action_id: int, result: SessionActionResult, now
    ) -> None:
        session = self.get(session_id)
        if session is None or not is_active_session(session["status"]):
            raise ValueError("Only an open or paused session can record results.")
        action = next((item for item in session["actions"] if item["id"] == action_id), None)
        if action is None:
            raise ValueError("Session action was not found.")
        if action["result"] is not None:
            raise ValueError("A recorded action result cannot be changed.")
        # 预检：最终一致性由事务内 UPDATE 的 WHERE result IS NULL 兜底。
        actual_sets = result.actual_sets
        with transaction(self.connection):
            cursor = self.connection.execute(
                "UPDATE training_session_action SET result = ?, note = ? "
                "WHERE id = ? AND result IS NULL AND session_id IN "
                "(SELECT id FROM training_session WHERE status IN (?, ?))",
                (result.result, result.note, action_id, SessionStatus.OPEN, SessionStatus.PAUSED),
            )
            if cursor.rowcount != 1:
                raise ValueError("A recorded action result cannot be changed.")
            values = (
                tuple(actual_set.value for actual_set in actual_sets)
                if actual_sets
                else result.actual_values
            )
            aligned_values = values if len(values) == len(action["sets"]) else ()
            for index, planned_set in enumerate(action["sets"]):
                value = aligned_values[index] if aligned_values else None
                actual_set = actual_sets[index] if aligned_values and actual_sets else None
                self.connection.execute(
                    "UPDATE training_session_set SET actual_value = ?, actual_unit = ?, "
                    "actual_per_side = ? WHERE id = ?",
                    (
                        value,
                        actual_set.unit
                        if actual_set
                        else planned_set["planned_unit"]
                        if value is not None
                        else None,
                        actual_set.per_side
                        if actual_set
                        else planned_set["planned_per_side"]
                        if value is not None
                        else None,
                        planned_set["id"],
                    ),
                )
            for actual_order, value in enumerate(values, 1):
                planned_set = action["sets"][min(actual_order - 1, len(action["sets"]) - 1)]
                actual_set = actual_sets[actual_order - 1] if actual_sets else None
                self.connection.execute(
                    "INSERT INTO training_session_actual_set(session_action_id, actual_order, "
                    "value, unit, per_side) VALUES (?, ?, ?, ?, ?)",
                    (
                        action_id,
                        actual_order,
                        value,
                        actual_set.unit if actual_set else planned_set["planned_unit"],
                        actual_set.per_side if actual_set else planned_set["planned_per_side"],
                    ),
                )
            self.connection.execute(
                "UPDATE training_session SET updated_at = ? WHERE id = ?",
                (now.isoformat(), session_id),
            )

    def retract_action_result(self, session_id: int, action_id: int, now) -> None:
        """Reset a selected result and audit its complete previous values atomically."""
        with transaction(self.connection, immediate=True):
            session = self.get(session_id)
            if session is None or not is_active_session(session["status"]):
                raise ValueError("Only an open or paused session can retract results.")
            action = next((item for item in session["actions"] if item["id"] == action_id), None)
            if action is None or action["result"] is None:
                raise ValueError("Select a recorded action to retract.")
            self.connection.execute(
                "INSERT INTO session_result_retraction(session_id, session_action_id, "
                "previous_action_json, retracted_at) VALUES (?, ?, ?, ?)",
                (session_id, action_id, json.dumps(action, ensure_ascii=False), now.isoformat()),
            )
            self.connection.execute(
                "DELETE FROM training_session_actual_set WHERE session_action_id = ?",
                (action_id,),
            )
            self.connection.execute(
                "UPDATE training_session_set SET actual_value = NULL, actual_unit = NULL, "
                "actual_per_side = NULL WHERE session_action_id = ?", (action_id,),
            )
            self.connection.execute(
                "UPDATE training_session_action SET result = NULL, note = NULL WHERE id = ?",
                (action_id,),
            )
            self.connection.execute(
                "UPDATE training_session SET updated_at = ? WHERE id = ?",
                (now.isoformat(), session_id),
            )

    def change_status(
        self, session_id: int, target: SessionStatus, now, reason=None, note=None
    ) -> None:
        session = self.get(session_id)
        if session is None:
            raise ValueError("Session was not found.")
        current = SessionStatus(session["status"])
        transition_status(current, target)
        if target is SessionStatus.ABORTED and not reason:
            raise ValueError("An abort reason is required.")
        with transaction(self.connection, immediate=True):
            if target in (SessionStatus.COMPLETED, SessionStatus.PARTIAL):
                latest = self.get(session_id)
                if any(action["result"] is None for action in latest["actions"]):
                    raise ValueError("Every exercise must have a result before finishing.")
                results = tuple(ExerciseResult(action["result"]) for action in latest["actions"])
                if derive_final_status(results) != target:
                    raise ValueError("The session changed before it could be updated.")
            finished_at = now.isoformat() if is_terminal_session(target) else None
            # 带上读取时的当前状态做乐观校验，避免并发下覆盖他人已改的状态。
            cursor = self.connection.execute(
                "UPDATE training_session SET status = ?, updated_at = ?, finished_at = ?, "
                "abort_reason = ?, abort_note = ? WHERE id = ? AND status = ?",
                (target, now.isoformat(), finished_at, reason, note, session_id, current),
            )
            if cursor.rowcount != 1:
                raise ValueError("The session changed before it could be updated.")
            # 事件类型用动词记录动作（pause/resume），其余直接用目标状态值。
            event_type = "pause" if target is SessionStatus.PAUSED else target.value
            self.connection.execute(
                "INSERT INTO session_event(session_id, event_type, occurred_at, reason, note) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, event_type, now.isoformat(), reason, note),
            )

    def resume(self, session_id: int, now) -> None:
        session = self.get(session_id)
        if session is None:
            raise ValueError("Session was not found.")
        if session["status"] != SessionStatus.PAUSED:
            raise ValueError("Only a paused session can be resumed.")
        with transaction(self.connection):
            cursor = self.connection.execute(
                "UPDATE training_session SET status = ?, updated_at = ? "
                "WHERE id = ? AND status = ?",
                (SessionStatus.OPEN, now.isoformat(), session_id, SessionStatus.PAUSED),
            )
            if cursor.rowcount != 1:
                raise ValueError("The session changed before it could be resumed.")
            self.connection.execute(
                "INSERT INTO session_event(session_id, event_type, occurred_at) VALUES (?, ?, ?)",
                (session_id, "resume", now.isoformat()),
            )

    def finish(self, session_id: int, now) -> SessionStatus:
        session = self.get(session_id)
        if session is None or not is_active_session(session["status"]):
            raise ValueError("Only an open or paused session can finish.")
        results = tuple(
            ExerciseResult(action["result"])
            for action in session["actions"]
            if action["result"] is not None
        )
        if len(results) != len(session["actions"]):
            raise ValueError("Every exercise must have a result before finishing.")
        status = derive_final_status(results)
        self.change_status(session_id, status, now)
        return status
