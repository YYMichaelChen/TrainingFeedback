"""动作指导内容的纯校验规则与审核事实判定（不访问数据库）。

一个指导版本"已审核"当且仅当它带有完整的审核证据（审核人类型、外部来源、
审核发生时间、用户确认时间）。当前模型的选用/启用由 library_state 表达，
历史旧模型的快照字段只作为转换证据保留。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

REVIEW_EVIDENCE_FIELDS = ("reviewer_type", "review_source", "reviewed_at", "user_approved_at")

REQUIRED_SCALARS = (
    "purpose",
    "starting_position",
    "breathing",
    "tempo_or_pacing",
    "applicability",
    "cautions",
)
REQUIRED_LISTS = (
    "intended_sensations",
    "common_compensations",
    "stop_criteria",
    "regressions",
    "progressions",
    "equipment",
    "images",
)


@dataclass(frozen=True)
class GuidanceValidation:
    complete: bool
    errors: tuple[str, ...]


def normalize_name(value: str) -> str:
    return unicodedata.normalize("NFKC", value.strip()).casefold()


def blank_review() -> dict[str, Any]:
    """未审核版本的审核块：没有任何审核证据，也不携带旧版本的受管原件引用。"""
    return {
        "reviewer_type": None,
        "review_source": None,
        "review_note": "",
        "reviewed_at": None,
        "user_approved_at": None,
    }


def validate_guidance(
    value: dict[str, Any], *, require_body_areas: bool = False
) -> GuidanceValidation:
    errors: list[str] = []
    for field in REQUIRED_SCALARS:
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"{field} is required")
    for field in REQUIRED_LISTS:
        entries = value.get(field)
        if (
            not isinstance(entries, list)
            or (field != "equipment" and not entries)
            or any(
                not isinstance(entry, (str, dict)) or (isinstance(entry, str) and not entry.strip())
                for entry in entries
            )
        ):
            errors.append(f"{field} must contain meaningful entries")
    if require_body_areas:
        for field in ("primary_body_areas", "secondary_body_areas"):
            entries = value.get(field)
            if (
                not isinstance(entries, list)
                or not entries
                or any(not isinstance(entry, str) or not entry.strip() for entry in entries)
            ):
                errors.append(f"{field} must contain meaningful entries")
    steps = value.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("steps must contain at least one item")
    else:
        orders = [step.get("order") for step in steps if isinstance(step, dict)]
        if (
            len(orders) != len(steps)
            or len(set(orders)) != len(orders)
            or any(not isinstance(order, int) or order < 1 for order in orders)
        ):
            errors.append("steps must have unique positive order values")
        if any(not isinstance(step.get("text"), str) or not step["text"].strip() for step in steps):
            errors.append("each step requires text")
    images = value.get("images")
    if (
        isinstance(images, list)
        and images
        and any(
            not isinstance(image, dict) or image.get("status") not in ("available", "missing")
            for image in images
        )
    ):
        errors.append("each image requires available or missing status")
    return GuidanceValidation(not errors, tuple(errors))


def is_reviewed(value: dict[str, Any]) -> bool:
    """已审核 = 这一版带有完整的外部审核证据与用户确认时间。与是否被采用无关。"""
    if not isinstance(value, dict):
        return False
    review = value.get("review")
    return isinstance(review, dict) and all(review.get(field) for field in REVIEW_EVIDENCE_FIELDS)


def require_review_occurrence(value: str) -> None:
    """Validate newly entered occurrence precision without rewriting legacy records."""
    message = "Review occurrence must be a valid date or timezone-aware datetime."
    if not isinstance(value, str):
        raise ValueError(message)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            date.fromisoformat(value)
        elif re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?"
            r"(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)", value
        ):
            parsed = datetime.fromisoformat(value)
            if parsed.utcoffset() is None:
                raise ValueError(message)
        else:
            raise ValueError(message)
    except ValueError as exc:
        raise ValueError(message) from exc
