"""Session-local structural history for the native plan editor."""

from copy import deepcopy


class PlanEditHistory:
    """Store structural targets without owning persistence or user facts."""

    def __init__(self):
        self._undo = []
        self._redo = []

    @property
    def can_undo(self):
        return bool(self._undo)

    @property
    def can_redo(self):
        return bool(self._redo)

    def record(self, before, after):
        if before == after:
            return False
        self._undo.append(deepcopy(before))
        self._redo.clear()
        return True

    def undo(self, current):
        if not self._undo:
            return None
        target = self._undo.pop()
        self._redo.append(deepcopy(current))
        return target

    def redo(self, current):
        if not self._redo:
            return None
        target = self._redo.pop()
        self._undo.append(deepcopy(current))
        return target


def merge_plan_structure(target, current):
    """Apply target hierarchy/order while retaining current raw input by stable ID.

    Nodes restored by undo use their saved target value. Surviving nodes retain
    later incomplete text, notes and field caches from the current edit session.
    """

    current_nodes = {}
    for day in current.get("days", []):
        for item in day.get("items", []):
            current_nodes[item.get("item_id")] = item
            for member in item.get("members", []):
                current_nodes[member.get("item_id")] = member

    def merge_node(template):
        identifier = template.get("item_id")
        live = current_nodes.get(identifier)
        result = deepcopy(template)
        if isinstance(live, dict):
            for key in template:
                if key not in {"item_id", "kind", "order", "members"} and key in live:
                    result[key] = deepcopy(live[key])
            if "_input" in live:
                result["_input"] = deepcopy(live["_input"])
        if "order" in template:
            result["order"] = template["order"]
        if template.get("kind") == "group":
            result["kind"] = "group"
            result["members"] = [merge_node(member) for member in template.get("members", [])]
        else:
            result.pop("members", None)
        return result

    result = deepcopy(current)
    result["days"] = []
    for day in target.get("days", []):
        merged_day = {key: deepcopy(value) for key, value in day.items() if key != "items"}
        merged_day["items"] = [merge_node(item) for item in day.get("items", [])]
        result["days"].append(merged_day)
    return result
