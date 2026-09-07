"""版本化训练计划的值对象、激活前校验与版本差异计算。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable, Iterable

from .enums import DoseUnit
from .exercises import GuidanceStatus, can_activate_guidance, review_status
from .models import require_non_negative_finite


class PlanPhase(StrEnum):
    PREPARATION = "preparation"
    MAIN = "main"
    COOLDOWN = "cooldown"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class PlannedSet:
    order: int
    unit: DoseUnit
    value: float | None = None
    per_side: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        try:
            unit = DoseUnit(self.unit)
        except ValueError as exc:
            raise ValueError("Unsupported dose unit.") from exc
        object.__setattr__(self, "unit", unit)
        ensure_orders((self.order,), "Set")
        require_non_negative_finite(
            self.value, "Numeric dose values must be finite and non-negative."
        )
        if unit is DoseUnit.FREE:
            if self.value is None and not self.note.strip():
                raise ValueError("Free doses without a value require a note.")
        elif self.value is None:
            raise ValueError("Numeric dose units require a value.")


@dataclass(frozen=True)
class PlanAction:
    order: int
    exercise_id: int
    phase: PlanPhase
    sets: tuple[PlannedSet, ...]
    rest_seconds: int | float = 0
    note: str = ""

    def __post_init__(self) -> None:
        try:
            phase = PlanPhase(self.phase)
        except ValueError as exc:
            raise ValueError("Unsupported plan action phase.") from exc
        object.__setattr__(self, "phase", phase)
        ensure_orders((self.order,), "Action")
        if not isinstance(self.exercise_id, int) or isinstance(self.exercise_id, bool):
            raise ValueError("Exercise id must be an integer.")
        if not self.sets:
            raise ValueError("Each action requires at least one set.")
        ensure_orders((planned_set.order for planned_set in self.sets), "Set")
        units = {planned_set.unit for planned_set in self.sets}
        if len(units) != 1:
            raise ValueError("All sets in one action must use the same unit.")
        require_non_negative_finite(
            self.rest_seconds, "Rest seconds must be finite and non-negative."
        )


@dataclass(frozen=True)
class PlanDay:
    order: int
    name: str
    actions: tuple[PlanAction, ...]

    def __post_init__(self) -> None:
        ensure_orders((self.order,), "Day")
        if not self.name.strip():
            raise ValueError("Day name cannot be empty.")
        if not self.actions:
            raise ValueError("Each plan day requires at least one action.")
        ensure_orders((action.order for action in self.actions), "Action")


@dataclass(frozen=True)
class PlanRevision:
    name: str
    purpose: str
    days: tuple[PlanDay, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Plan name cannot be empty.")
        if not self.days:
            raise ValueError("A plan requires at least one day.")
        ensure_orders((day.order for day in self.days), "Day")


def validate_revision(
    revision: PlanRevision,
    exercise_lookup: Callable[[int], dict[str, Any] | None],
) -> tuple[str, ...]:
    """Return activation errors without changing the revision or database."""
    errors: list[str] = []
    for day in revision.days:
        for action in day.actions:
            exercise = exercise_lookup(action.exercise_id)
            if exercise is None:
                errors.append(f"Exercise {action.exercise_id} was not found.")
                continue
            if not exercise.get("active"):
                errors.append(f"Exercise {action.exercise_id} is inactive.")
            active_id = exercise.get("active_guidance_revision_id")
            guidance = next(
                (
                    item["guidance"]
                    for item in exercise.get("guidance", [])
                    if item.get("id") == active_id
                ),
                None,
            )
            if (
                guidance is None
                or review_status(guidance) is not GuidanceStatus.ACTIVE
                or not can_activate_guidance(guidance)
            ):
                errors.append(f"Exercise {action.exercise_id} has no approved active guidance.")
    return tuple(errors)


def require_valid_revision(
    revision: PlanRevision,
    exercise_lookup: Callable[[int], dict[str, Any] | None],
) -> None:
    errors = validate_revision(revision, exercise_lookup)
    if errors:
        raise ValueError("Plan revision cannot be activated: " + " ".join(errors))


def ensure_orders(values: Iterable[int], label: str) -> None:
    orders = tuple(values)
    if any(not is_positive_int(order) for order in orders):
        raise ValueError(f"{label} orders must be positive integers.")
    if len(set(orders)) != len(orders):
        raise ValueError(f"{label} orders must be positive and unique.")


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def revision_from_snapshot(source: dict[str, Any]) -> PlanRevision:
    """把仓储读取的版本快照字典还原为领域对象（只读转换，不访问数据库）。"""
    return PlanRevision(
        name=source.get("name", ""),
        purpose=source["purpose"],
        days=tuple(
            PlanDay(
                day["day_order"],
                day["name"],
                tuple(
                    PlanAction(
                        action["action_order"],
                        action["exercise_id"],
                        PlanPhase(action["phase"]),
                        tuple(
                            PlannedSet(
                                planned_set["set_order"],
                                planned_set["unit"],
                                planned_set["value"],
                                bool(planned_set["per_side"]),
                                planned_set.get("note", ""),
                            )
                            for planned_set in action["sets"]
                        ),
                        action["rest_seconds"] or 0,
                        action["note"],
                    )
                    for action in day["actions"]
                ),
            )
            for day in source["days"]
        ),
    )


def diff_revisions(before: PlanRevision, after: PlanRevision) -> tuple[dict[str, Any], ...]:
    """Return display-neutral changes between two revisions without mutation."""
    changes: list[dict[str, Any]] = []

    def add(category: str, path: str, old: Any, new: Any) -> None:
        if old != new:
            changes.append({"category": category, "path": path, "before": old, "after": new})

    add("plan_purpose", "purpose", before.purpose, after.purpose)
    before_days = {day.order: day for day in before.days}
    after_days = {day.order: day for day in after.days}
    for order in sorted(before_days.keys() | after_days.keys()):
        old_day, new_day = before_days.get(order), after_days.get(order)
        if old_day is None or new_day is None:
            add("day_added" if new_day else "day_removed", f"day[{order}]", old_day, new_day)
            continue
        old_actions = {action.order: action for action in old_day.actions}
        new_actions = {action.order: action for action in new_day.actions}
        old_positions = {action.exercise_id: action.order for action in old_day.actions}
        new_positions = {action.exercise_id: action.order for action in new_day.actions}
        for exercise_id in sorted(old_positions.keys() & new_positions.keys()):
            old_count = sum(action.exercise_id == exercise_id for action in old_day.actions)
            new_count = sum(action.exercise_id == exercise_id for action in new_day.actions)
            if old_count == new_count == 1:
                add(
                    "action_reordered",
                    f"day[{order}].exercise[{exercise_id}].order",
                    old_positions[exercise_id],
                    new_positions[exercise_id],
                )
        for action_order in sorted(old_actions.keys() | new_actions.keys()):
            old_action = old_actions.get(action_order)
            new_action = new_actions.get(action_order)
            path = f"day[{order}].action[{action_order}]"
            if old_action is None or new_action is None:
                add(
                    "action_added" if new_action else "action_removed",
                    path,
                    old_action,
                    new_action,
                )
                continue
            add(
                "exercise_changed",
                path + ".exercise_id",
                old_action.exercise_id,
                new_action.exercise_id,
            )
            add("phase_changed", path + ".phase", old_action.phase, new_action.phase)
            add(
                "rest_changed",
                path + ".rest_seconds",
                old_action.rest_seconds,
                new_action.rest_seconds,
            )
            add("action_note_changed", path + ".note", old_action.note, new_action.note)
            old_sets = {planned_set.order: planned_set for planned_set in old_action.sets}
            new_sets = {planned_set.order: planned_set for planned_set in new_action.sets}
            for set_order in sorted(old_sets.keys() | new_sets.keys()):
                old_set = old_sets.get(set_order)
                new_set = new_sets.get(set_order)
                set_path = f"{path}.set[{set_order}]"
                if old_set is None or new_set is None:
                    add("set_added" if new_set else "set_removed", set_path, old_set, new_set)
                    continue
                add("set_value_changed", set_path + ".value", old_set.value, new_set.value)
                add("unit_changed", set_path + ".unit", old_set.unit, new_set.unit)
                add("per_side_changed", set_path + ".per_side", old_set.per_side, new_set.per_side)
                add("set_note_changed", set_path + ".note", old_set.note, new_set.note)
    return tuple(changes)
