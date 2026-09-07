"""外部交接的纯领域契约：导入 schema、导入解析校验。

证据文件的 Markdown 渲染属于展示职责，位于 data/handoff.py。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .enums import DoseUnit
from .plans import PlanAction, PlanDay, PlannedSet, PlanPhase, PlanRevision, is_positive_int

EXPORT_SCHEMA_VERSION = 1
PLAN_IMPORT_SCHEMA = "training_feedback.plan"


class HandoffError(ValueError):
    """Raised when external handoff data violates the versioned contract."""


@dataclass(frozen=True)
class ImportedPlan:
    revision: PlanRevision
    target_plan_name: str | None
    rationale: str
    source_session_id: int | None
    source_export_id: int | None


def plan_import_schema() -> dict[str, Any]:
    """Describe the exact external response accepted by this application."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TrainingFeedback external plan response",
        "type": "object",
        "required": ["schema", "schema_version", "rationale", "plan"],
        "properties": {
            "schema": {"const": PLAN_IMPORT_SCHEMA},
            "schema_version": {"const": EXPORT_SCHEMA_VERSION},
            "rationale": {"type": "string"},
            "source": {
                "type": "object",
                "properties": {
                    "session_id": {"type": ["integer", "null"], "minimum": 1},
                    "export_id": {"type": ["integer", "null"], "minimum": 1},
                },
            },
            "plan": {
                "type": "object",
                "required": ["name", "purpose", "days"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "target_plan_name": {"type": ["string", "null"]},
                    "purpose": {"type": "string"},
                    "days": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["order", "name", "actions"],
                            "properties": {
                                "order": {"type": "integer", "minimum": 1},
                                "name": {"type": "string", "minLength": 1},
                                "actions": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "required": [
                                            "order",
                                            "exercise_name",
                                            "phase",
                                            "sets",
                                        ],
                                        "properties": {
                                            "order": {"type": "integer", "minimum": 1},
                                            "exercise_name": {"type": "string"},
                                            "phase": {"enum": ["preparation", "main", "cooldown"]},
                                            "rest_seconds": {
                                                "type": "number",
                                                "minimum": 0,
                                            },
                                            "note": {"type": "string"},
                                            "sets": {
                                                "type": "array",
                                                "minItems": 1,
                                                "items": {
                                                    "type": "object",
                                                    "required": ["order", "unit"],
                                                    "properties": {
                                                        "order": {
                                                            "type": "integer",
                                                            "minimum": 1,
                                                        },
                                                        "value": {
                                                            "type": ["number", "null"],
                                                            "minimum": 0,
                                                        },
                                                        "unit": {
                                                            "enum": [
                                                                "reps",
                                                                "seconds",
                                                                "minutes",
                                                                "breaths",
                                                                "free",
                                                            ]
                                                        },
                                                        "per_side": {"type": "boolean"},
                                                        "note": {"type": "string"},
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }


def parse_plan_import(
    payload: Any, exercise_resolver: Callable[[str], dict[str, Any] | None]
) -> ImportedPlan:
    if not isinstance(payload, dict) or payload.get("schema") != PLAN_IMPORT_SCHEMA:
        raise HandoffError("Unsupported external plan schema.")
    if payload.get("schema_version") != EXPORT_SCHEMA_VERSION:
        raise HandoffError("Unsupported external plan schema version.")
    plan = payload.get("plan")
    if not isinstance(plan, dict):
        raise HandoffError("External plan content is missing.")
    name = plan.get("name")
    purpose = plan.get("purpose")
    days = plan.get("days")
    if not isinstance(name, str) or not name.strip() or not isinstance(purpose, str):
        raise HandoffError("External plan name and purpose must be text.")
    if not isinstance(days, list) or not days:
        raise HandoffError("External plan must contain at least one day.")
    try:
        parsed_days = tuple(_parse_day(day, exercise_resolver) for day in days)
        revision = PlanRevision(name, purpose, parsed_days)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, HandoffError):
            raise
        raise HandoffError(f"External plan validation failed: {exc}") from exc
    rationale = payload.get("rationale", "")
    if not isinstance(rationale, str) or not rationale.strip():
        raise HandoffError("External rationale must contain text.")
    target_name = plan.get("target_plan_name")
    if target_name is not None and not isinstance(target_name, str):
        raise HandoffError("Target plan name must be text.")
    source_session_id, source_export_id = _parse_source(payload.get("source", {}))
    return ImportedPlan(
        revision,
        target_name,
        rationale,
        source_session_id,
        source_export_id,
    )


def _parse_source(source: Any) -> tuple[int | None, int | None]:
    if not isinstance(source, dict):
        raise HandoffError("External plan source must be an object.")
    return (
        _optional_id(source.get("session_id"), "session"),
        _optional_id(source.get("export_id"), "export"),
    )


def _parse_day(day: Any, exercise_resolver: Callable[[str], dict[str, Any] | None]) -> PlanDay:
    if not isinstance(day, dict):
        raise HandoffError("Each external plan day must be an object.")
    if not is_positive_int(day.get("order")):
        raise HandoffError("External day order must be a positive integer.")
    if not isinstance(day.get("name"), str):
        raise HandoffError("External day name must be text.")
    if not isinstance(day.get("actions"), list) or not day["actions"]:
        raise HandoffError("Each external plan day requires actions.")
    actions = tuple(_parse_action(action, exercise_resolver) for action in day["actions"])
    return PlanDay(day["order"], day["name"], actions)


def _parse_action(
    action: Any, exercise_resolver: Callable[[str], dict[str, Any] | None]
) -> PlanAction:
    if not isinstance(action, dict):
        raise HandoffError("Each external plan action must be an object.")
    if not is_positive_int(action.get("order")):
        raise HandoffError("External action order must be a positive integer.")
    if not isinstance(action.get("sets"), list) or not action["sets"]:
        raise HandoffError("Each external plan action requires sets.")
    exercise_name = action.get("exercise_name")
    exercise = exercise_resolver(exercise_name) if isinstance(exercise_name, str) else None
    if exercise is None:
        raise HandoffError(f"Unknown exercise in external plan: {exercise_name}.")
    if not isinstance(action.get("note", ""), str):
        raise HandoffError("External action notes must be text.")
    sets = tuple(_parse_set(item) for item in action["sets"])
    return PlanAction(
        action["order"],
        exercise["id"],
        PlanPhase(action["phase"]),
        sets,
        action.get("rest_seconds", 0),
        action.get("note", ""),
    )


def _parse_set(item: Any) -> PlannedSet:
    if not isinstance(item, dict):
        raise HandoffError("Each external plan set must be an object.")
    if not is_positive_int(item.get("order")):
        raise HandoffError("External set order must be a positive integer.")
    note = item.get("note", "")
    if not isinstance(note, str):
        raise HandoffError("External set notes must be text.")
    per_side = item.get("per_side", False)
    if not isinstance(per_side, bool):
        raise HandoffError("External per-side values must be Boolean.")
    return PlannedSet(item["order"], DoseUnit(item["unit"]), item.get("value"), per_side, note)


def _optional_id(value: Any, label: str) -> int | None:
    if value is None:
        return None
    if not is_positive_int(value):
        raise HandoffError(f"External source {label} id must be a positive integer.")
    return value
