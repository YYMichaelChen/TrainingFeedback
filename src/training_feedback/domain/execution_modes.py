"""Execution semantics shared by plan validation, expansion and presentation."""

from copy import deepcopy
from math import isfinite

EXECUTION_MODE_LABELS = {"whole": "整体完成", "separate_sides": "分侧完成",
                         "alternating": "左右交替"}
ALTERNATING_START_LABELS = {None: "未选择", "left": "先左", "right": "先右", "either": "任选"}


def execution_mode(action):
    """Missing mode is meaningful only for retained pre-v5 facts."""
    return action.get("execution_mode", "separate_sides" if any(
        dose.get("per_side") for dose in action.get("sets", [])) else "whole")


def upgrade_payload(payload):
    """Project a validated v4 revision or internal raw draft; never rewrite its source."""
    result = deepcopy(payload)
    if result.get("schema_version") != 4:
        return result
    result["schema_version"] = 5
    for day in result.get("plan", {}).get("days", []):
        for item in day.get("items", []):
            for action in item.get("members", [item]):
                action.setdefault("execution_mode", execution_mode(action))
                action.setdefault("alternating_start", None)
    return result


def validate_execution(action):
    mode = execution_mode(action)
    if mode not in EXECUTION_MODE_LABELS:
        raise ValueError("Choose an execution mode.")
    if mode == "alternating":
        if action.get("alternating_start") not in ("left", "right", "either"):
            raise ValueError("Alternating work requires a starting rule for every set.")
        for dose in action["sets"]:
            if dose["unit"] != "reps":
                raise ValueError("Alternating work requires reps.")
            value = dose["value"]
            if (isinstance(value, bool) or not isinstance(value, (float, int))
                    or not isfinite(value) or value < 0 or int(value) != value):
                raise ValueError("Alternating reps must be non-negative integers.")
    else:
        if action.get("alternating_start") is not None:
            raise ValueError("Only alternating work has an alternating starting rule.")
        if any(dose["per_side"] != (mode == "separate_sides") for dose in action["sets"]):
            raise ValueError("Dose convention conflicts with execution mode.")


def alternating_explanation(action, dose):
    """Planned allocation only. Never used to infer actual side measurements."""
    if dose.get("unit", "reps") != "reps":
        return "左右交替仅支持“次”；当前单位输入已保留，请修改后再启用。"
    value = dose.get("value")
    try:
        count = float(value)
        if not isfinite(count) or count < 0 or not count.is_integer():
            raise ValueError
        count = int(count)
    except (ValueError, TypeError):
        return "交替次数须填写非负整数；到达一侧计一次，起始摆位和回中不计次。"
    if dose["per_side"]:
        amount = f"计划左右各 {count} 次，共 {count * 2} 次到达"
    elif count % 2 == 0:
        amount = f"计划共 {count} 次到达，左右各 {count // 2} 次"
    elif action.get("alternating_start") in ("left", "right"):
        left = count // 2 + (action["alternating_start"] == "left")
        amount = f"计划共 {count} 次到达，左 {left}、右 {count - left} 次"
    else:
        amount = f"计划共 {count} 次到达，先到的一侧 {count // 2 + 1}、另一侧 {count // 2} 次"
    starting = ALTERNATING_START_LABELS.get(action.get("alternating_start"), "未选择")
    return (amount + "；每组" + starting
            + "；到达一侧计一次，起始摆位和回中不计次；此为计划推算，非实际记录。")
