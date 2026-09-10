"""次日反馈规则：从已完成动作推导需评价的身体部位并校验提交值。"""

from __future__ import annotations

from datetime import date

from .enums import ExerciseResult, FeedbackValue
from .training import is_terminal_session

PERFORMED_RESULTS = frozenset(
    (ExerciseResult.COMPLETED, ExerciseResult.EXCEEDED, ExerciseResult.PARTIAL)
)


def performed_actions(session: dict) -> list[dict]:
    return [
        action
        for action in session["actions"]
        if action.get("result") in PERFORMED_RESULTS
    ]


def feedback_areas(session: dict) -> tuple[str, ...]:
    areas: list[str] = []
    for action in performed_actions(session):
        # Supporting movements can have anatomically useful primary-area metadata
        # without creating next-day soreness prompts in their supporting phase.
        if action.get("phase_snapshot", "main") != "main":
            continue
        snapshots = action.get("body_area_snapshots", [])
        for area in snapshots:
            if isinstance(area, dict) and area.get("is_primary") is True:
                name = area.get("name")
                if isinstance(name, str) and name and name not in areas:
                    areas.append(name)
    return tuple(areas)


def can_submit_feedback(session: dict, current_date: date) -> bool:
    if not is_terminal_session(session["status"]):
        return False
    if date.fromisoformat(session["training_date"]) >= current_date:
        return False
    return bool(feedback_areas(session))


def validate_feedback_values(
    session: dict, values: dict[str, FeedbackValue | str | None]
) -> dict[str, FeedbackValue | None]:
    expected = set(feedback_areas(session))
    if set(values) != expected:
        raise ValueError("Feedback must contain exactly the derived training areas.")
    normalized: dict[str, FeedbackValue | None] = {}
    for area, value in values.items():
        normalized[area] = None if value is None else FeedbackValue(value)
    return normalized
