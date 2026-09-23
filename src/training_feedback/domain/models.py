"""通用数值校验与训练结果终态推导规则（纯规则，不访问数据库）。"""

from math import isfinite

from .enums import ExerciseResult, SessionStatus


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


def derive_final_status(results: tuple[ExerciseResult, ...]) -> SessionStatus:
    if not results:
        raise ValueError("A session must contain at least one action result.")
    if all(result in (ExerciseResult.COMPLETED, ExerciseResult.EXCEEDED) for result in results):
        return SessionStatus.COMPLETED
    return SessionStatus.PARTIAL
