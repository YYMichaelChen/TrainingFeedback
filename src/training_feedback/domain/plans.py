"""计划处方的值对象与通用顺序校验（纯规则，不访问数据库）。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable

from .enums import DoseUnit
from .models import require_non_negative_finite


class PlanPhase(StrEnum):
    PREPARATION = "preparation"
    MAIN = "main"
    COOLDOWN = "cooldown"


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


def ensure_orders(values: Iterable[int], label: str) -> None:
    orders = tuple(values)
    if any(not is_positive_int(order) for order in orders):
        raise ValueError(f"{label} orders must be positive integers.")
    if len(set(orders)) != len(orders):
        raise ValueError(f"{label} orders must be positive and unique.")


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
