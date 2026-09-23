"""冻结的 v1 外部计划导入 schema（仅作契约基线证据；v1 导入解析已随旧运行时退役）。"""

from __future__ import annotations

from typing import Any

EXPORT_SCHEMA_VERSION = 1
PLAN_IMPORT_SCHEMA = "training_feedback.plan"


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
