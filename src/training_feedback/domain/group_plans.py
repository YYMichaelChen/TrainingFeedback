"""V2 plan validation, identity-based diffs and editable document operations."""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
from uuid import uuid4

from jsonschema import Draft202012Validator

from .action_groups import ActionGroup, GroupMember
from .catalog import ExerciseReference, require_classification
from .models import require_non_negative_finite
from .plans import PlannedSet, ensure_orders

PLAN_IMPORT_SCHEMA_VERSION = 2
EVIDENCE_SCHEMA_VERSION = 2


def validate_plan_payload(payload: dict, schema: dict, *, activation: bool = False) -> dict:
    if not isinstance(payload, dict) or payload.get("schema_version") != PLAN_IMPORT_SCHEMA_VERSION:
        raise ValueError("Only plan format version 2 is accepted.")
    errors = list(Draft202012Validator(schema).iter_errors(payload))
    if errors:
        error = errors[0]
        path = "/".join(str(part) for part in error.absolute_path)
        raise ValueError(f"Invalid plan v2 at {path}: {error.message}")
    _require_finite(payload)
    plan = payload["plan"]
    ensure_orders((day["order"] for day in plan["days"]), "Day")
    seen = set()
    for day in plan["days"]:
        ensure_orders((item["order"] for item in day["items"]), "Item")
        for item in day["items"]:
            rows = [item, *item.get("members", [])]
            for row in rows:
                if row["item_id"] in seen:
                    raise ValueError("Plan item identities must be unique throughout the revision.")
                seen.add(row["item_id"])
            if item["kind"] == "group":
                group = group_from_item(item)
                if activation:
                    group.require_transition_for_activation()
                for member in item["members"]:
                    validate_action(member)
            else:
                validate_action(item)
                unilateral = item["sets"][0]["per_side"]
                if unilateral and item["first_side"] not in ("left", "right"):
                    raise ValueError("Unilateral work requires an explicit first side.")
                if not unilateral and (
                    item["first_side"] is not None or item["rest_between_sides_seconds"] != 0
                ):
                    raise ValueError("Bilateral work has no side or side-switch rest.")
    return deepcopy(payload)


def validate_stored_plan(payload, schema, originals, *, activation=False):
    """Validate persisted migration facts without accepting provenance from external input.

    Unknown side/rest fields are allowed only when an unchanged migration binding
    exists in the stored revision. Rule-check projections never become saved facts.
    """
    projected = deepcopy(payload)
    for _day, _item, action in plan_actions(projected["plan"]):
        if "provenance" not in action:
            continue
        prior = originals.get(action["item_id"])
        if prior is None or action.get("provenance") != prior.get("provenance"):
            raise ValueError("Migration provenance must match stored facts.")
        for key in ("exercise", "dose_scope"):
            if action.get(key) != prior.get(key):
                raise ValueError("Migration identity or dose scope cannot be changed implicitly.")
        projection = migration_validation_projection(action)
        action.clear()
        action.update(projection)
    if not projected["rationale"] and any("provenance" in row for row in originals.values()):
        projected["rationale"] = "validation-only"
    validate_plan_payload(projected, schema, activation=activation)
    return deepcopy(payload)


def migration_validation_projection(action):
    projected = deepcopy(action)
    scope = projected.pop("dose_scope")
    projected.pop("provenance")
    if scope not in ("per_side_aggregate", "whole") or projected["first_side"] is not None:
        raise ValueError("Migrated aggregate work has no recorded first side.")
    if any(dose["per_side"] for dose in projected["sets"]) != (scope == "per_side_aggregate"):
        raise ValueError("Changing aggregate dose scope requires an explicitly replaced action.")
    if scope == "per_side_aggregate":
        projected["first_side"] = "left"  # Validation-only; never a saved side order.
    for key in ("rest_between_sides_seconds", "rest_after_action_seconds"):
        if projected[key] is None:
            projected[key] = 0
    for dose in projected["sets"]:
        if dose["rest_after_set_seconds"] is None:
            dose["rest_after_set_seconds"] = 0
    return projected


def _require_finite(value):
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("Plan numbers must be finite.")
    if isinstance(value, dict):
        for item in value.values():
            _require_finite(item)
    elif isinstance(value, list):
        for item in value:
            _require_finite(item)


def validate_action(action):
    require_classification(action["classification"], ExerciseReference(**action["exercise"]))
    sets = tuple(
        PlannedSet(row["order"], row["unit"], row["value"], row["per_side"], row["note"])
        for row in action["sets"]
    )
    GroupMember(
        action["item_id"],
        action["order"],
        sets,
        action["classification"]["starting_position_class"],
        0,
    )
    for dose in action["sets"]:
        require_non_negative_finite(dose["rest_after_set_seconds"], "Invalid set rest.")
    for field in (
        "rest_after_member_seconds",
        "rest_after_action_seconds",
        "rest_between_sides_seconds",
    ):
        if field in action:
            require_non_negative_finite(action[field], "Invalid boundary rest.")
    if action.get("kind") == "action":
        unilateral = sets[0].per_side
        if unilateral and action["first_side"] not in ("left", "right"):
            raise ValueError("Unilateral work requires an explicit first side.")
        if not unilateral and (
            action["first_side"] is not None or action["rest_between_sides_seconds"] != 0
        ):
            raise ValueError("Bilateral work has no side or side-switch rest.")
    if max(action["sets"], key=lambda row: row["order"])["rest_after_set_seconds"] != 0:
        raise ValueError("The final set must use boundary rest, not set rest.")


def group_from_item(item) -> ActionGroup:
    return ActionGroup(
        item["item_id"],
        tuple(
            GroupMember(
                member["item_id"],
                member["order"],
                tuple(
                    PlannedSet(
                        row["order"], row["unit"], row["value"], row["per_side"], row["note"]
                    )
                    for row in member["sets"]
                ),
                member["classification"]["starting_position_class"],
                member["rest_after_member_seconds"],
            )
            for member in item["members"]
        ),
        item["round_count"],
        item["side_sequence"],
        item["first_side"],
        item["rest_between_sides_seconds"],
        item["rest_between_rounds_seconds"],
        item["rest_after_group_seconds"],
        item["transition"],
    )


def plan_actions(plan):
    for day in sorted(plan["days"], key=lambda day: day["order"]):
        for item in sorted(day["items"], key=lambda item: item["order"]):
            for action in sorted(item.get("members", [item]), key=lambda action: action["order"]):
                yield day, item, action


def identity_rows(plan):
    result = {}
    for day in plan["days"]:
        for item in day["items"]:
            path = f"{day['order']}:{day['name']}/{item['order']}"
            result[item["item_id"]] = (path, {k: v for k, v in item.items() if k != "members"})
            for member in item.get("members", []):
                result[member["item_id"]] = (
                    f"{path}:{item['name']}/{member['order']}",
                    {**member, "group_id": item["item_id"], "phase": item["phase"]},
                )
    return result


def diff_plans(before, after):
    if before is None:
        return [{"item_id": None, "path": "plan", "before": None, "after": deepcopy(after)}]
    changes = []
    for key in ("name", "purpose", "target_plan_name"):
        if before.get(key) != after.get(key):
            changes.append(
                {"item_id": None, "path": key, "before": before.get(key), "after": after.get(key)}
            )
    old_days = [(day["order"], day["name"]) for day in before["days"]]
    new_days = [(day["order"], day["name"]) for day in after["days"]]
    if old_days != new_days:
        changes.append({"item_id": None, "path": "days", "before": old_days, "after": new_days})
    old, new = identity_rows(before), identity_rows(after)
    for key in sorted(old.keys() | new.keys()):
        if old.get(key) != new.get(key):
            changes.append(
                {
                    "item_id": key,
                    "path": (new.get(key) or old[key])[0],
                    "before": deepcopy(old.get(key)),
                    "after": deepcopy(new.get(key)),
                }
            )
    return changes


def new_item_id():
    return "item." + uuid4().hex


class PlanDocument:
    """An unsaved editable copy. Commands never access repositories or infer performed work."""

    def __init__(self, plan):
        self.plan = deepcopy(plan)

    @staticmethod
    def reorder(rows):
        for order, row in enumerate(rows, 1):
            row["order"] = order

    def add_day(self, name):
        if not name.strip():
            raise ValueError("Day name cannot be empty.")
        self.plan["days"].append({"order": len(self.plan["days"]) + 1, "name": name, "items": []})

    def move(self, rows, index, offset):
        target = index + offset
        if not 0 <= target < len(rows):
            return
        rows[index], rows[target] = rows[target], rows[index]
        self.reorder(rows)

    def remove_member(self, day_index, group_index, member_index, *, dissolve=False):
        day = self.plan["days"][day_index]
        group = day["items"][group_index]
        if len(group["members"]) == 2:
            if not dissolve:
                raise ValueError("Removing this member requires explicit group dissolution.")
            if group["round_count"] != 1:
                raise ValueError("Set the group to one round explicitly before dissolving it.")
            survivor = deepcopy(group["members"][1 - member_index])
            survivor.pop("rest_after_member_seconds")
            survivor.update(
                kind="action",
                order=group["order"],
                phase=group["phase"],
                first_side=group["first_side"] if survivor["sets"][0]["per_side"] else None,
                rest_between_sides_seconds=group["rest_between_sides_seconds"]
                if survivor["sets"][0]["per_side"]
                else 0,
                rest_after_action_seconds=group["rest_after_group_seconds"],
            )
            day["items"][group_index] = survivor
        else:
            del group["members"][member_index]
            self.reorder(group["members"])

    def move_member(self, source_group, index, destination_group):
        if len(source_group["members"]) <= 2:
            raise ValueError("Keep two members or explicitly dissolve the source group first.")
        if source_group is destination_group:
            raise ValueError("Choose another destination group.")
        member = source_group["members"].pop(index)
        destination_group["members"].append(member)
        self.reorder(source_group["members"])
        self.reorder(destination_group["members"])

    def move_item_to_day(self, day_index, item_index, destination_index):
        if day_index == destination_index:
            raise ValueError("Choose another destination day.")
        source = self.plan["days"][day_index]["items"]
        destination = self.plan["days"][destination_index]["items"]
        destination.append(source.pop(item_index))
        self.reorder(source)
        self.reorder(destination)


def action_from_choice(choice, *, member=False):
    action = {**deepcopy(choice), "item_id": new_item_id(), "order": 1, "sets": [], "note": ""}
    if member:
        action["rest_after_member_seconds"] = 0
    else:
        action.update(
            kind="action",
            phase="main",
            first_side=None,
            rest_between_sides_seconds=0,
            rest_after_action_seconds=0,
        )
    return action


def blank_group():
    return {
        "kind": "group",
        "item_id": new_item_id(),
        "order": 1,
        "name": "",
        "phase": "main",
        "round_count": 1,
        "side_sequence": "member_each_side",
        "first_side": None,
        "transition": "",
        "rest_between_sides_seconds": 0,
        "rest_between_rounds_seconds": 0,
        "rest_after_group_seconds": 0,
        "members": [],
        "note": "",
    }
