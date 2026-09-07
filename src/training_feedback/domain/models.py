"""训练执行侧的不可变领域记录与终态推导规则。"""

from dataclasses import dataclass
from math import isfinite

from .enums import DoseUnit, ExerciseResult, SessionStatus


def require_non_negative_finite(value: float | None, message: str) -> None:
    """校验剂量类数值：必须是有限非负的 int/float（bool 不算数）。"""
    if value is None:
        return
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not isfinite(value)
        or value < 0
    ):
        raise ValueError(message)


@dataclass(frozen=True)
class ActualSet:
    """One performed set, which may differ from the planned prescription."""

    value: float
    unit: DoseUnit
    per_side: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "unit", DoseUnit(self.unit))
        require_non_negative_finite(
            self.value, "Actual dose values must be finite and non-negative."
        )


@dataclass(frozen=True)
class SessionActionResult:
    result: ExerciseResult
    actual_values: tuple[float | None, ...] = ()
    note: str = ""
    actual_sets: tuple[ActualSet, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "result", ExerciseResult(self.result))
        if self.actual_values and self.actual_sets:
            raise ValueError("Actual dose must use values or actual sets, not both.")
        for value in self.actual_values:
            require_non_negative_finite(
                value, "Actual dose values must be finite and non-negative."
            )
        if self.result in (ExerciseResult.EXCEEDED, ExerciseResult.PARTIAL) and (
            (not self.actual_values and not self.actual_sets)
            or any(value is None for value in self.actual_values)
        ):
            raise ValueError("Actual dose is required for exceeded or partial results.")
        if self.result is ExerciseResult.NOT_COMPLETED and (self.actual_values or self.actual_sets):
            raise ValueError("Not-completed results cannot contain actual dose.")


def derive_final_status(results: tuple[ExerciseResult, ...]) -> SessionStatus:
    if not results:
        raise ValueError("A session must contain at least one action result.")
    if all(result in (ExerciseResult.COMPLETED, ExerciseResult.EXCEEDED) for result in results):
        return SessionStatus.COMPLETED
    return SessionStatus.PARTIAL
