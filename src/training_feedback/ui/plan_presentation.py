"""User-facing presentation data for saved plan revisions."""

from __future__ import annotations

from .labels import (
    DOSE_UNIT_LABELS,
    LIBRARY_REASON_LABELS,
    PLAN_PHASE_LABELS,
    PLAN_STATUS_LABELS,
)

SIDE_SEQUENCE_LABELS = {
    "member_each_side": "每个成员完成两侧后继续",
    "same_side_then_switch": "同侧完成各轮后换侧",
    "all_rounds_then_switch": "完成全部轮次后换侧",
}
_ABSENT = "not_applicable"


def _rest(value):
    return "未记录" if value is None else f"{value} 秒"


def _boundary(record, field):
    return _rest(record[field]) if field in record else "不适用"


def _sets(action, *, every_round=False):
    return [
        {
            "order": dose["order"],
            "dose": (
                "自由剂量（自定义）"
                if dose["unit"] == "free" and dose["value"] is None
                else (
                    "未记录"
                    if dose["value"] is None
                    else f"{dose['value']} {DOSE_UNIT_LABELS[dose['unit']]}"
                )
            ),
            "per_side": dose["per_side"],
            "note": dose["note"],
            "rest": _boundary(dose, "rest_after_set_seconds"),
            "every_round": every_round,
        }
        for dose in sorted(action["sets"], key=lambda row: row["order"])
    ]


def _action(action, *, every_round=False):
    return {
        "name": action["exercise_name"],
        "phase": PLAN_PHASE_LABELS[action.get("phase", "main")],
        "note": action["note"],
        "sets": _sets(action, every_round=every_round),
        "rest_after": (
            _boundary(action, "rest_after_member_seconds")
            if "rest_after_member_seconds" in action
            else _boundary(action, "rest_after_action_seconds")
        ),
        "rest_between_sides": _boundary(action, "rest_between_sides_seconds"),
        "first_side": action.get("first_side", _ABSENT),
    }


def _item(item):
    if item["kind"] == "action":
        return {"kind": "action", "order": item["order"], **_action(item)}
    return {
        "kind": "group",
        "order": item["order"],
        "name": item["name"],
        "phase": PLAN_PHASE_LABELS[item["phase"]],
        "round_count": item["round_count"],
        "side_sequence": SIDE_SEQUENCE_LABELS[item["side_sequence"]],
        "first_side": item.get("first_side", _ABSENT),
        "transition": item["transition"],
        "note": item["note"],
        "rest_between_sides": _boundary(item, "rest_between_sides_seconds"),
        "rest_between_rounds": _boundary(item, "rest_between_rounds_seconds"),
        "rest_after": _boundary(item, "rest_after_group_seconds"),
        "members": [
            {"order": member["order"], **_action(member, every_round=True)}
            for member in sorted(item["members"], key=lambda row: row["order"])
        ],
    }


def plan_presentation(revision, content_issues=()):
    """Project revision facts into a safe, display-oriented hierarchy."""
    plan = revision["payload"]["plan"]
    return {
        "name": plan["name"],
        "version": revision["revision_number"],
        "status": PLAN_STATUS_LABELS[revision["status"]],
        "status_key": revision["status"],
        "purpose": plan["purpose"],
        "adjustment": revision["rationale"],
        "issues": [
            {
                "name": issue["name"],
                "reasons": [
                    LIBRARY_REASON_LABELS.get(reason, reason) for reason in issue["reasons"]
                ],
            }
            for issue in content_issues
        ],
        "days": [
            {
                "order": day["order"],
                "name": day["name"],
                "items": [
                    _item(item) for item in sorted(day["items"], key=lambda row: row["order"])
                ],
            }
            for day in sorted(plan["days"], key=lambda row: row["order"])
        ],
    }
