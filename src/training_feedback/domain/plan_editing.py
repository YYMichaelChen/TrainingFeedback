"""Versioned editable input and structured strict validation, independent of Qt/storage."""

from copy import deepcopy
from dataclasses import dataclass
from math import isfinite

from jsonschema import Draft202012Validator

from .execution_modes import execution_mode
from .group_plans import group_from_item, validate_action
from .plans import PlannedSet

EDIT_FORMAT_VERSION = 2
NUMBERS = {"value", "round_count", "rest_after_set_seconds", "rest_after_member_seconds",
           "rest_after_action_seconds", "rest_between_sides_seconds",
           "rest_between_rounds_seconds", "rest_after_group_seconds"}


@dataclass(frozen=True)
class PlanIssue:
    code: str
    path: tuple = ()
    node_id: str | None = None
    detail: str = ""


class PlanIssues(ValueError):
    def __init__(self, issues):
        self.issues = issues
        super().__init__("Plan input has unresolved issues.")


def compile_input(raw):
    """Convert numeric text only in a copy; raw text is always the saved source."""
    issues = []

    def visit(value, path=(), node=None):
        if isinstance(value, list):
            return [visit(row, (*path, i), node) for i, row in enumerate(value)]
        if not isinstance(value, dict):
            return value
        node = value.get("item_id", node)
        result = {}
        for key, item in value.items():
            if key == "_input":
                continue  # Inapplicable input caches are internal only.
            if key in NUMBERS and isinstance(item, str):
                try:
                    number = float(item.strip()) if item.strip() else None
                    if number is not None and (not isfinite(number) or number < 0):
                        raise ValueError
                    if key == "round_count" and number is not None:
                        if not number.is_integer() or number < 1:
                            raise ValueError
                        number = int(number)
                    result[key] = number
                except ValueError:
                    issues.append(PlanIssue("number", (*path, key), node))
                    result[key] = None
            else:
                result[key] = visit(item, (*path, key), node)
        return result

    return visit(deepcopy(raw)), issues


def payload_issues(payload, schema, *, activation=False):
    """Collect independent structural and domain errors; invalid parents stop descent."""
    if not isinstance(payload, dict) or payload.get("schema") != "training_feedback.plan" \
            or payload.get("schema_version") != schema["properties"]["schema_version"]["const"]:
        return [PlanIssue("format")]
    issues = []
    def finite(value, path=()):
        if isinstance(value, float) and not isfinite(value):
            issues.append(PlanIssue("number", path))
        elif isinstance(value, dict):
            for key, child in value.items():
                finite(child, (*path, key))
        elif isinstance(value, list):
            for i, child in enumerate(value):
                finite(child, (*path, i))
    finite(payload)
    validator = Draft202012Validator(schema)

    def expand(error):
        if error.validator == "oneOf" and isinstance(error.instance, dict):
            kind = error.instance.get("kind")
            selected = [child for child in error.context
                        if child.schema_path[0] == (1 if kind == "group" else 0)]
            if selected:
                return selected
        return [error]

    for error in validator.iter_errors(payload):
        for item in expand(error):
            path = tuple(item.absolute_path)
            if item.validator == "required":
                missing = [key for key in item.validator_value if key not in item.instance]
                issues.extend(PlanIssue("required", (*path, key)) for key in missing)
            else:
                issues.append(PlanIssue("schema." + item.validator, path, detail=item.message))
    invalid_paths = [issue.path for issue in issues]
    seen = set()
    plan = payload.get("plan")
    if not isinstance(plan, dict):
        return issues
    days = plan.get("days", [])
    if not isinstance(days, list):
        return issues

    def check_order(rows, path):
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            return
        orders = [row.get("order") for row in rows]
        if any(type(order) is not int or order < 1 for order in orders):
            issues.append(PlanIssue("orders", path))
        elif len(set(orders)) != len(orders):
            issues.append(PlanIssue("orders", path))

    check_order(days, ("plan", "days"))
    for d, day in enumerate(days):
        if not isinstance(day, dict) or not isinstance(day.get("items"), list):
            continue
        base = ("plan", "days", d, "items")
        check_order(day["items"], base)
        for i, item in enumerate(day["items"]):
            if not isinstance(item, dict):
                continue
            path = (*base, i)
            actions = item.get("members", []) if item.get("kind") == "group" else [item]
            if not isinstance(actions, list):
                continue
            if item.get("kind") == "group":
                check_order(actions, (*path, "members"))
            for row in ([item, *actions] if item.get("kind") == "group" else [item]):
                if not isinstance(row, dict):
                    continue
                node = row.get("item_id")
                if isinstance(node, str):
                    if node in seen:
                        issues.append(PlanIssue("identity", path, node))
                    seen.add(node)
            for m, action in enumerate(actions):
                action_path = (*path, "members", m) if item.get("kind") == "group" else path
                if not isinstance(action, dict) or any(
                    p[:len(action_path)] == action_path for p in invalid_paths
                ):
                    continue
                check_order(action.get("sets"), (*action_path, "sets"))
                dose_issues = []
                for s, dose in enumerate(action["sets"]):
                    if execution_mode(action) == "alternating":
                        if dose["unit"] != "reps":
                            dose_issues.append(PlanIssue("rule", (*action_path, "sets", s, "unit"),
                                action.get("item_id"), "Alternating work requires reps."))
                        value = dose["value"]
                        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                                or not isfinite(value) or value < 0 or int(value) != value):
                            dose_issues.append(PlanIssue("rule", (*action_path, "sets", s, "value"),
                                action.get("item_id"),
                                "Alternating reps must be non-negative integers."))
                    try:
                        PlannedSet(dose["order"], dose["unit"], dose["value"],
                                   dose["per_side"], dose["note"])
                    except ValueError as exc:
                        field = ("note" if str(exc) == "Free doses without a value require a note."
                                 else "value")
                        dose_issues.append(PlanIssue(
                            "rule", (*action_path, "sets", s, field),
                            action.get("item_id"), str(exc)))
                if dose_issues:
                    issues.extend(dose_issues)
                    continue
                try:
                    validate_action(action)
                except (ValueError, TypeError, KeyError) as exc:
                    issues.append(rule_issue(exc, action_path, action.get("item_id"), action))
            if item.get("kind") == "group" and item.get("side_sequence") in (
                    "same_side_then_switch", "all_rounds_then_switch"):
                for m, member in enumerate(actions):
                    if isinstance(member, dict) and member.get("execution_mode") in (
                            "whole", "alternating"):
                        issues.append(PlanIssue("rule", (*path, "members", m, "execution_mode"),
                            member.get("item_id"),
                            "该成员与组侧序冲突：请改为逐个成员完成或移出动作组。"))
            if item.get("kind") == "group" and not any(
                issue.path[:len(path)] == path for issue in issues
            ):
                try:
                    group = group_from_item(item)
                    if activation:
                        group.require_transition_for_activation()
                except (ValueError, TypeError, KeyError) as exc:
                    issues.append(rule_issue(exc, path, item.get("item_id"), item))
    return issues


def rule_issue(exc, path, node, row):
    message = str(exc)
    suffix = {
        "Choose an execution mode.": ("execution_mode",),
        "Alternating work requires a starting rule for every set.": ("alternating_start",),
        "Alternating work requires reps.": ("sets", 0, "unit"),
        "Alternating reps must be non-negative integers.": ("sets", 0, "value"),
        "Only alternating work has an alternating starting rule.": ("alternating_start",),
        "Dose convention conflicts with execution mode.": ("sets", 0, "per_side"),
        "A plan with this name already exists.": ("plan", "name"),
        "A plan base number must be between 001 and 999.": ("requested_base_number",),
        "That plan base number is already in use.": ("requested_base_number",),
        "Unilateral work requires an explicit first side.": ("first_side",),
        "Bilateral work has no side or side-switch rest.": ("rest_between_sides_seconds",),
        "Bilateral work has no first side.": ("first_side",),
        "Bilateral work cannot prescribe side-switch rest.": ("rest_between_sides_seconds",),
        "One round cannot prescribe between-round rest.": ("rest_between_rounds_seconds",),
        "One member must use one dose unit.": ("sets", 0, "unit"),
        "One member must use one per-side convention.": ("sets", 0, "per_side"),
        "Mixed or unknown positions require a transition instruction.": ("transition",),
        "This side sequence requires all members to be per-side.": ("side_sequence",),
        "The final set must use boundary rest, not set rest.": (
            "sets", max(0, len(row.get("sets", [])) - 1), "rest_after_set_seconds"),
        "The final member uses side, round or exit rest instead.": (
            "members", max(0, len(row.get("members", [])) - 1), "rest_after_member_seconds"),
    }.get(message, ())
    inconsistent_field = {
        "One member must use one dose unit.": "unit",
        "One member must use one per-side convention.": "per_side",
    }.get(message)
    if inconsistent_field and row.get("sets"):
        first = row["sets"][0][inconsistent_field]
        index = next((i for i, dose in enumerate(row["sets"])
                      if dose[inconsistent_field] != first), 0)
        suffix = ("sets", index, inconsistent_field)
    return PlanIssue("rule", (*path, *suffix), node, message)
