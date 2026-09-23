"""Lifecycle transitions and identity matching without persistence or UI dependencies."""

TRANSITIONS = {
    "requested": {"under_review", "cancelled", "rejected"},
    "under_review": {"under_review", "approved", "cancelled", "rejected"},
    "approved": {"under_review", "applied", "cancelled"},
    "applied": set(),
    "rejected": set(),
    "cancelled": set(),
}


def require_transition(current, requested):
    if requested not in TRANSITIONS.get(current, set()):
        raise ValueError("This lifecycle transition is not allowed.")


def contains_exercise(value, exercise):
    """Match explicit namespaced identities in frozen JSON, never names or substrings."""
    if isinstance(value, dict):
        return value.get("exercise") == exercise or any(
            contains_exercise(child, exercise) for child in value.values()
        )
    if isinstance(value, list):
        return any(contains_exercise(child, exercise) for child in value)
    return False
