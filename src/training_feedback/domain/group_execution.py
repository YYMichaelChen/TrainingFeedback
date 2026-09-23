"""Frozen occurrence expansion and result rules; navigation never implies performance."""

from copy import deepcopy

from .enums import DoseUnit, ExerciseResult
from .group_plans import group_from_item
from .models import derive_final_status, require_non_negative_finite
from .next_day import feedback_areas


def expand_day(day):
    occurrences = []
    for item in sorted(day["items"], key=lambda row: row["order"]):
        if item["kind"] == "group":
            group = group_from_item(item)
            members = {member["item_id"]: member for member in item["members"]}
            expanded = list(group.occurrences())
            for index, occurrence in enumerate(expanded):
                following = expanded[index + 1] if index + 1 < len(expanded) else None
                boundary = "member"
                if following is None:
                    boundary = "group_exit"
                elif (item["side_sequence"] == "all_rounds_then_switch"
                      and occurrence.side != following.side):
                    boundary = "side"
                elif occurrence.round_number != following.round_number:
                    boundary = "round"
                elif occurrence.side != following.side and (
                    item["side_sequence"] == "same_side_then_switch"
                    or occurrence.member_id == following.member_id
                ):
                    boundary = "side"
                occurrences.append(_snapshot(
                    day, item, members[occurrence.member_id], occurrence.side,
                    occurrence.round_number, occurrence.rest_after_seconds, boundary,
                ))
        else:
            if item.get("dose_scope") == "per_side_aggregate":
                occurrences.append(_snapshot(day, item, item, None, None,
                                              item["rest_after_action_seconds"], "action_exit"))
                continue
            sides = (item["first_side"],
                     "right" if item["first_side"] == "left" else "left")
            for index, side in enumerate(sides if item["sets"][0]["per_side"] else (None,)):
                switch = item["sets"][0]["per_side"] and index == 0
                occurrences.append(_snapshot(
                    day, item, item, side, None,
                    item["rest_between_sides_seconds"] if switch
                    else item["rest_after_action_seconds"],
                    "side" if switch else "action_exit",
                ))
    return [{**row, "position": index} for index, row in enumerate(occurrences)]


def _snapshot(day, item, action, side, round_number, rest, boundary):
    value = deepcopy({
        "day_order": day["order"], "day_name": day["name"],
        "item_id": action["item_id"], "item_order": item["order"],
        "member_order": action["order"] if item["kind"] == "group" else None,
        "group_id": item["item_id"] if item["kind"] == "group" else None,
        "group": {key: value for key, value in item.items() if key != "members"}
        if item["kind"] == "group" else None,
        "round_number": round_number, "side": side, "phase": item["phase"],
        "action": action, "rest_after_seconds": rest, "rest_boundary": boundary,
    })
    if action.get("dose_scope"):
        value["dose_scope"] = action["dose_scope"]
    return value


def round_members(session):
    current = session["occurrences"][session["position"]]
    if current["group_id"] is None:
        raise ValueError("The current occurrence is not in an action group.")
    return [
        row for row in session["occurrences"]
        if row["group_id"] == current["group_id"]
        and row["round_number"] == current["round_number"]
        and (current["group"]["side_sequence"] != "all_rounds_then_switch"
             or row["side"] == current["side"])
        and row["result"] is None
    ]


def actual_doses(occurrence, result, actual, note):
    result = ExerciseResult(result)
    if not isinstance(note, str):
        raise ValueError("Result notes must be text.")
    if result in (ExerciseResult.COMPLETED, ExerciseResult.NOT_COMPLETED):
        if actual:
            raise ValueError("This result cannot contain entered actual dose.")
        if result == ExerciseResult.NOT_COMPLETED:
            return []
        return [
            {"order": index, "value": dose["value"], "unit": dose["unit"],
              "side": occurrence["side"], "note": dose["note"] or "",
              "provenance": "prescription_confirmed",
              **({"per_side": dose["per_side"]}
                 if occurrence.get("dose_scope") == "per_side_aggregate" else {})}
            for index, dose in enumerate(
                sorted(occurrence["action"]["sets"], key=lambda row: row["order"]), 1
            )
        ]
    if not actual:
        raise ValueError("Actual dose is required for exceeded or partial results.")
    values = []
    for index, dose in enumerate(actual, 1):
        aggregate = occurrence.get("dose_scope") == "per_side_aggregate"
        if set(dose) != {"value", "unit", "side", "note"} | ({"per_side"} if aggregate else set()):
            raise ValueError("Actual dose requires value, unit, explicit side and note.")
        if aggregate and type(dose["per_side"]) is not bool:
            raise ValueError("Aggregate actual dose requires an explicit per-side choice.")
        unit = DoseUnit(dose["unit"])
        require_non_negative_finite(dose["value"], "Actual dose must be finite and non-negative.")
        if not isinstance(dose["note"], str):
            raise ValueError("Actual dose notes must be text.")
        if dose["value"] is None and not (unit == DoseUnit.FREE and dose["note"].strip()):
            raise ValueError("Actual dose cannot be unknown; free work needs an explanation.")
        if dose["side"] != occurrence["side"]:
            raise ValueError("Actual side must match this occurrence; record the other side there.")
        values.append({**dose, "order": index, "unit": unit.value, "provenance": "user_entered"})
    return values


def final_status(session):
    results = [row["result"] for row in session["occurrences"]]
    if any(result is None for result in results):
        raise ValueError("Every occurrence needs a saved result before finishing.")
    return derive_final_status(tuple(ExerciseResult(result) for result in results))


def session_feedback_areas(session):
    return feedback_areas({"actions": [
        {"result": row["result"], "phase_snapshot": row["phase"],
         "body_area_snapshots": row["body_areas"]}
        for row in session["occurrences"]
    ]})
