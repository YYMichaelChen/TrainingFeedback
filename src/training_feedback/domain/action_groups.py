"""Pure 0.7.0 group prescription contract; no execution state or persistence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator

from .catalog import StartingPosition, require_stable_key
from .models import require_non_negative_finite
from .plans import PlannedSet, ensure_orders, is_positive_int


class SideSequence(StrEnum):
    MEMBER_EACH_SIDE = "member_each_side"
    SAME_SIDE_THEN_SWITCH = "same_side_then_switch"
    ALL_ROUNDS_THEN_SWITCH = "all_rounds_then_switch"


@dataclass(frozen=True)
class GroupMember:
    item_id: str
    order: int
    sets: tuple[PlannedSet, ...]
    starting_position: StartingPosition
    rest_after_member_seconds: float

    def __post_init__(self) -> None:
        require_stable_key(self.item_id)
        ensure_orders((self.order,), "Member")
        object.__setattr__(self, "starting_position", StartingPosition(self.starting_position))
        if not self.sets:
            raise ValueError("Group members require dose sets.")
        ensure_orders((item.order for item in self.sets), "Set")
        if len({item.unit for item in self.sets}) != 1:
            raise ValueError("One member must use one dose unit.")
        if any(not isinstance(item.per_side, bool) for item in self.sets):
            raise ValueError("Per-side flags must be Boolean.")
        if len({item.per_side for item in self.sets}) != 1:
            raise ValueError("One member must use one per-side convention.")
        _require_seconds(self.rest_after_member_seconds)

    @property
    def per_side(self) -> bool:
        return self.sets[0].per_side


@dataclass(frozen=True)
class GroupOccurrence:
    round_number: int
    member_id: str
    side: str | None
    rest_after_seconds: float


@dataclass(frozen=True)
class ActionGroup:
    item_id: str
    members: tuple[GroupMember, ...]
    round_count: int
    side_sequence: SideSequence
    first_side: str | None
    rest_between_sides_seconds: float
    rest_between_rounds_seconds: float
    rest_after_group_seconds: float
    transition: str

    def __post_init__(self) -> None:
        require_stable_key(self.item_id)
        object.__setattr__(self, "side_sequence", SideSequence(self.side_sequence))
        if len(self.members) < 2:
            raise ValueError("A group requires at least two members.")
        ensure_orders((member.order for member in self.members), "Member")
        ids = [self.item_id, *(member.item_id for member in self.members)]
        if len(set(ids)) != len(ids):
            raise ValueError("Group and member item identities must be unique.")
        if not is_positive_int(self.round_count):
            raise ValueError("Round count must be a positive integer.")
        unilateral = any(member.per_side for member in self.members)
        if unilateral and self.first_side not in ("left", "right"):
            raise ValueError("Unilateral work requires an explicit first side.")
        if not unilateral and self.first_side is not None:
            raise ValueError("Bilateral work has no first side.")
        if self.side_sequence != SideSequence.MEMBER_EACH_SIDE and not all(
            member.per_side for member in self.members
        ):
            raise ValueError("This side sequence requires all members to be per-side.")
        for seconds in (
            self.rest_between_sides_seconds,
            self.rest_between_rounds_seconds,
            self.rest_after_group_seconds,
        ):
            _require_seconds(seconds)
        if not unilateral and self.rest_between_sides_seconds != 0:
            raise ValueError("Bilateral work cannot prescribe side-switch rest.")
        if self.round_count == 1 and self.rest_between_rounds_seconds != 0:
            raise ValueError("One round cannot prescribe between-round rest.")
        last = max(self.members, key=lambda member: member.order)
        if last.rest_after_member_seconds != 0:
            raise ValueError("The final member uses side, round or exit rest instead.")
        if not isinstance(self.transition, str):
            raise ValueError("Transition instructions must be text.")

    def require_transition_for_activation(self) -> None:
        positions = {member.starting_position for member in self.members}
        needs_transition = len(positions) > 1 or bool(
            positions & {StartingPosition.MIXED, StartingPosition.UNKNOWN}
        )
        if needs_transition and not self.transition.strip():
            raise ValueError("Mixed or unknown positions require a transition instruction.")

    def occurrences(self) -> Iterator[GroupOccurrence]:
        """Expand planned member work lazily; it does not assert actual performance."""
        positions = iter(self._positions())
        current = next(positions)
        for following in positions:
            round_number, member, side = current
            next_round, next_member, next_side = following
            if self.side_sequence == SideSequence.ALL_ROUNDS_THEN_SWITCH and side != next_side:
                rest = self.rest_between_sides_seconds
            elif round_number != next_round:
                rest = self.rest_between_rounds_seconds
            elif (
                self.side_sequence == SideSequence.SAME_SIDE_THEN_SWITCH and side != next_side
            ) or (member.item_id == next_member.item_id and side != next_side):
                rest = self.rest_between_sides_seconds
            else:
                rest = member.rest_after_member_seconds
            yield GroupOccurrence(round_number, member.item_id, side, rest)
            current = following
        round_number, member, side = current
        yield GroupOccurrence(round_number, member.item_id, side, self.rest_after_group_seconds)

    def _positions(self) -> Iterator[tuple[int, GroupMember, str | None]]:
        members = sorted(self.members, key=lambda member: member.order)
        rounds = range(1, self.round_count + 1)
        sides = (self.first_side, "right" if self.first_side == "left" else "left")
        if self.side_sequence == SideSequence.MEMBER_EACH_SIDE:
            for round_number in rounds:
                for member in members:
                    for side in sides if member.per_side else (None,):
                        yield round_number, member, side
        elif self.side_sequence == SideSequence.SAME_SIDE_THEN_SWITCH:
            for round_number in rounds:
                for side in sides:
                    for member in members:
                        yield round_number, member, side
        else:
            for side in sides:
                for round_number in rounds:
                    for member in members:
                        yield round_number, member, side


def _require_seconds(value: float) -> None:
    if value is None:
        raise ValueError("Rest seconds must be explicitly supplied.")
    require_non_negative_finite(value, "Rest seconds must be finite and non-negative.")
