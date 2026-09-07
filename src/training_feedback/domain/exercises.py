"""动作指导内容的纯校验规则与审核状态判定（不访问数据库）。"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class GuidanceStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    APPROVED = "approved"
    ACTIVE = "active"


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


def validate_guidance(value: dict[str, Any]) -> GuidanceValidation:
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


def guidance_to_json(value: dict[str, Any], *, require_complete: bool = False) -> str:
    validation = validate_guidance(value)
    if require_complete and not validation.complete:
        raise ValueError("; ".join(validation.errors))
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def review_status(value: dict[str, Any]) -> GuidanceStatus:
    try:
        return GuidanceStatus(value.get("review", {}).get("status", GuidanceStatus.DRAFT))
    except (AttributeError, ValueError, TypeError) as exc:
        raise ValueError("Invalid guidance review status.") from exc


def can_activate_guidance(value: dict[str, Any]) -> bool:
    validation = validate_guidance(value)
    review = value.get("review", {})
    return (
        validation.complete
        and review_status(value)
        in (
            GuidanceStatus.APPROVED,
            GuidanceStatus.ACTIVE,
        )
        and has_review_metadata(review)
    )


def has_review_metadata(review: Any) -> bool:
    return isinstance(review, dict) and all(
        review.get(field)
        for field in ("reviewer_type", "review_source", "reviewed_at", "user_approved_at")
    )


def require_review_metadata(review: dict[str, Any]) -> None:
    if not review.get("reviewer_type") or not review.get("review_source"):
        raise ValueError("Reviewer type and source are required.")
    if not review.get("user_approved_at"):
        raise ValueError("Explicit user approval is required.")
    if not review.get("reviewed_at"):
        raise ValueError("Review time is required.")
