"""版本化训练计划的 SQLite 仓储；已发布版本不可变（由 v11 触发器保证）。"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from ..domain.plans import (
    PlanRevision,
    PlanStatus,
    require_valid_revision,
    revision_from_snapshot,
)
from .database import transaction


class PlanRepository:
    """计划仓储：版本化计划的读写、草稿替换与激活。"""

    def __init__(self, connection: sqlite3.Connection, exercise_repository=None):
        self.connection = connection
        self.exercise_repository = exercise_repository

    def list_plans(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.connection.execute("SELECT * FROM training_plan ORDER BY name")
        ]

    def get_plan(self, plan_id: int) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM training_plan WHERE id = ?", (plan_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["revisions"] = [
            self.get_revision(row[0], revision["id"]) for revision in self._revision_rows(plan_id)
        ]
        return result

    def get_revision(self, plan_id: int, revision_id: int) -> dict[str, Any] | None:
        revision = self.connection.execute(
            "SELECT * FROM training_plan_revision WHERE id = ? AND plan_id = ?",
            (revision_id, plan_id),
        ).fetchone()
        if revision is None:
            return None
        result = dict(revision)
        result["name"] = self.connection.execute(
            "SELECT name FROM training_plan WHERE id = ?", (plan_id,)
        ).fetchone()[0]
        result["days"] = []
        for day in self.connection.execute(
            "SELECT * FROM training_plan_day WHERE revision_id = ? ORDER BY day_order",
            (revision_id,),
        ):
            day_result = dict(day)
            day_result["actions"] = []
            for action in self.connection.execute(
                "SELECT a.*, e.canonical_name AS exercise_name FROM training_plan_action a "
                "JOIN exercise e ON e.id = a.exercise_id WHERE a.day_id = ? "
                "ORDER BY a.action_order",
                (day["id"],),
            ):
                action_result = dict(action)
                action_result["sets"] = [
                    dict(planned_set)
                    for planned_set in self.connection.execute(
                        "SELECT * FROM training_plan_set WHERE action_id = ? ORDER BY set_order",
                        (action["id"],),
                    )
                ]
                day_result["actions"].append(action_result)
            result["days"].append(day_result)
        return result

    def create_plan(self, revision: PlanRevision) -> tuple[int, int]:
        connection = self.connection
        with transaction(connection):
            now = datetime.now(UTC).isoformat()
            cursor = connection.execute(
                "INSERT INTO training_plan(name, created_at) VALUES (?, ?)",
                (revision.name, now),
            )
            plan_id = cursor.lastrowid
            revision_id = self._insert_revision(plan_id, revision, PlanStatus.DRAFT)
            return plan_id, revision_id

    def create_draft_revision(self, plan_id: int, revision: PlanRevision) -> int:
        self._require_plan(plan_id)
        with transaction(self.connection):
            return self._insert_revision(plan_id, revision, PlanStatus.DRAFT)

    def create_imported_revision(
        self,
        target_plan_name: str | None,
        revision: PlanRevision,
        source_path: str,
        rationale: str,
        source_session_id: int | None = None,
        source_export_id: int | None = None,
    ) -> tuple[int, int]:
        """Create an imported draft and provenance record in one transaction."""
        with transaction(self.connection):
            plan = (
                self.connection.execute(
                    "SELECT id FROM training_plan WHERE name = ?", (target_plan_name,)
                ).fetchone()
                if target_plan_name
                else None
            )
            if target_plan_name and plan is None:
                raise ValueError("Target plan was not found.")
            if plan is None:
                cursor = self.connection.execute(
                    "INSERT INTO training_plan(name, created_at) VALUES (?, ?)",
                    (revision.name, datetime.now(UTC).isoformat()),
                )
                plan_id = cursor.lastrowid
                previous_revision_id = None
            else:
                plan_id = plan[0]
                previous_revision_id = self.connection.execute(
                    "SELECT active_revision_id FROM training_plan WHERE id = ?", (plan_id,)
                ).fetchone()[0]
            revision_id = self._insert_revision(plan_id, revision, PlanStatus.DRAFT)
            self.connection.execute(
                "INSERT INTO plan_import(source_path, rationale, status, created_at, plan_id, "
                "revision_id, previous_revision_id, source_session_id, source_export_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source_path,
                    rationale,
                    "draft_created",
                    datetime.now(UTC).isoformat(),
                    plan_id,
                    revision_id,
                    previous_revision_id,
                    source_session_id,
                    source_export_id,
                ),
            )
            return plan_id, revision_id

    def clone_revision(self, plan_id: int, revision_id: int) -> int:
        source = self.get_revision(plan_id, revision_id)
        if source is None:
            raise ValueError("Plan revision was not found.")
        revision = revision_from_snapshot(source)
        return self.create_draft_revision(plan_id, revision)

    def replace_draft_revision(
        self, plan_id: int, revision_id: int, revision: PlanRevision
    ) -> None:
        """Replace draft content transactionally; published revisions are immutable."""
        with transaction(self.connection, immediate=True):
            current = self.get_revision(plan_id, revision_id)
            if current is None:
                raise ValueError("Plan revision was not found.")
            if current["status"] != PlanStatus.DRAFT:
                raise ValueError("Only draft revisions can be edited.")
            action_ids = [
                row[0]
                for row in self.connection.execute(
                    "SELECT a.id FROM training_plan_action a "
                    "JOIN training_plan_day d ON d.id = a.day_id WHERE d.revision_id = ?",
                    (revision_id,),
                )
            ]
            for action_id in action_ids:
                self.connection.execute(
                    "DELETE FROM training_plan_set WHERE action_id = ?", (action_id,)
                )
            self.connection.execute(
                "DELETE FROM training_plan_action WHERE day_id IN "
                "(SELECT id FROM training_plan_day WHERE revision_id = ?)",
                (revision_id,),
            )
            self.connection.execute(
                "DELETE FROM training_plan_day WHERE revision_id = ?", (revision_id,)
            )
            cursor = self.connection.execute(
                "UPDATE training_plan_revision SET purpose = ? "
                "WHERE id = ? AND plan_id = ? AND status = ?",
                (revision.purpose, revision_id, plan_id, PlanStatus.DRAFT),
            )
            if cursor.rowcount != 1:
                raise ValueError("Only draft revisions can be edited.")
            self._insert_children(revision_id, revision)

    def activate_revision(self, plan_id: int, revision_id: int) -> None:
        with transaction(self.connection, immediate=True):
            source = self.get_revision(plan_id, revision_id)
            if source is None:
                raise ValueError("Plan revision was not found.")
            if source["status"] != PlanStatus.DRAFT:
                raise ValueError("Only draft revisions can be activated.")
            revision = revision_from_snapshot(source)
            if self.exercise_repository is None:
                raise ValueError("An exercise repository is required for activation.")
            require_valid_revision(revision, self.exercise_repository.get)
            self.connection.execute(
                "UPDATE training_plan_revision SET status = ? WHERE plan_id = ? AND status = ?",
                (PlanStatus.SUPERSEDED, plan_id, PlanStatus.ACTIVE),
            )
            cursor = self.connection.execute(
                "UPDATE training_plan_revision SET status = ? WHERE id = ? AND plan_id = ?",
                (PlanStatus.ACTIVE, revision_id, plan_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Only draft revisions can be activated.")
            self.connection.execute(
                "UPDATE training_plan SET active_revision_id = ? WHERE id = ?",
                (revision_id, plan_id),
            )
            self.connection.execute(
                "UPDATE plan_import SET status = ?, confirmed_at = ? "
                "WHERE revision_id = ? AND plan_id = ?",
                ("activated", datetime.now(UTC).isoformat(), revision_id, plan_id),
            )

    def _revision_rows(self, plan_id: int):
        return self.connection.execute(
            "SELECT * FROM training_plan_revision WHERE plan_id = ? ORDER BY revision_number",
            (plan_id,),
        )

    def _require_plan(self, plan_id: int) -> None:
        if (
            self.connection.execute(
                "SELECT 1 FROM training_plan WHERE id = ?", (plan_id,)
            ).fetchone()
            is None
        ):
            raise ValueError("Plan was not found.")

    def _insert_revision(self, plan_id: int, revision: PlanRevision, status: PlanStatus) -> int:
        number = self.connection.execute(
            "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM training_plan_revision "
            "WHERE plan_id = ?",
            (plan_id,),
        ).fetchone()[0]
        cursor = self.connection.execute(
            "INSERT INTO training_plan_revision(plan_id, revision_number, status, purpose, "
            "created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (plan_id, number, status, revision.purpose, datetime.now(UTC).isoformat()),
        )
        revision_id = cursor.lastrowid
        self._insert_children(revision_id, revision)
        return revision_id

    def _insert_children(self, revision_id: int, revision: PlanRevision) -> None:
        for day in revision.days:
            day_cursor = self.connection.execute(
                "INSERT INTO training_plan_day(revision_id, day_order, name) VALUES (?, ?, ?)",
                (revision_id, day.order, day.name),
            )
            for action in day.actions:
                action_cursor = self.connection.execute(
                    "INSERT INTO training_plan_action(day_id, exercise_id, action_order, phase, "
                    "rest_seconds, note) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        day_cursor.lastrowid,
                        action.exercise_id,
                        action.order,
                        action.phase,
                        action.rest_seconds,
                        action.note,
                    ),
                )
                for planned_set in action.sets:
                    self.connection.execute(
                        "INSERT INTO training_plan_set(action_id, set_order, value, unit, "
                        "per_side, note) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            action_cursor.lastrowid,
                            planned_set.order,
                            planned_set.value,
                            planned_set.unit,
                            int(planned_set.per_side),
                            planned_set.note,
                        ),
                    )
