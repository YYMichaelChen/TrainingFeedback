"""Stable catalog identities and immutable content fingerprints for the new model."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ExerciseSource(StrEnum):
    BUNDLED = "bundled"
    CUSTOM = "custom"


class StartingPosition(StrEnum):
    SUPINE = "supine"
    PRONE = "prone"
    SIDE_LYING = "side_lying"
    QUADRUPED = "quadruped"
    SEATED = "seated"
    KNEELING = "kneeling"
    STANDING = "standing"
    MIXED = "mixed"
    UNKNOWN = "unknown"


def require_stable_key(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", value):
        raise ValueError("A stable key must be a non-empty portable identifier.")


@dataclass(frozen=True)
class ExerciseReference:
    source: ExerciseSource
    key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", ExerciseSource(self.source))
        require_stable_key(self.key)


def content_sha256(content: dict[str, Any]) -> str:
    """Hash an explicit content envelope; caller keeps user review/state outside it.

    Keys are sorted, arrays retain their order, text is not normalized. NaN and
    infinity are not valid content. Image paths/hashes belong in the envelope.
    """
    encoded = json.dumps(
        content, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require_content_envelope(content: dict[str, Any]) -> None:
    """Content carries technique/identity only; review and enablement live separately."""
    required = {
        "exercise", "canonical_name", "aliases", "category", "equipment_summary",
        "body_areas", "classification", "guidance",
    }
    if not isinstance(content, dict) or set(content) != required:
        raise ValueError("Content envelope fields do not match the catalog contract.")
    ExerciseReference(**content["exercise"])
    for field in ("canonical_name", "category", "equipment_summary"):
        if not isinstance(content[field], str):
            raise ValueError("Content display fields must be text.")
    if not content["canonical_name"].strip():
        raise ValueError("Content requires a name.")
    if not isinstance(content["aliases"], list) or any(
        not isinstance(alias, str) or not alias.strip() for alias in content["aliases"]
    ):
        raise ValueError("Content aliases must be text.")
    require_classification(content["classification"], ExerciseReference(**content["exercise"]))
    guidance = content["guidance"]
    if not isinstance(guidance, dict) or "review" in guidance:
        raise ValueError("Content cannot contain review evidence.")
    images = guidance.get("images")
    if not isinstance(images, list):
        raise ValueError("Content requires an explicit image inventory.")
    seen = set()
    for image in images:
        if not isinstance(image, dict) or image.get("status") not in ("available", "missing"):
            raise ValueError("Image availability must be explicit.")
        if type(image.get("required")) is not bool:
            raise ValueError("Image requirement must be explicit.")
        if image["status"] == "available":
            if not isinstance(image.get("path"), str) or image["path"] in seen:
                raise ValueError("Available images require unique paths.")
            if not isinstance(image.get("sha256"), str) or not re.fullmatch(
                r"[a-f0-9]{64}", image["sha256"],
            ):
                raise ValueError("Available images require a byte hash.")
            seen.add(image["path"])
        elif image.get("path") is not None or image.get("sha256") is not None:
            raise ValueError("Missing images cannot claim a path or a byte hash.")
    content_sha256(content)


def require_classification(classification: dict, reference: ExerciseReference) -> None:
    if not isinstance(classification, dict) or set(classification) != {
        "family_key", "variant_role", "variant_order", "parent_exercise_key",
        "starting_position_class",
    }:
        raise ValueError("Invalid exercise classification fields.")
    StartingPosition(classification["starting_position_class"])
    role = classification["variant_role"]
    if role not in {"base", "variant", "standalone"}:
        raise ValueError("Invalid variant role.")
    if type(classification["variant_order"]) is not int or classification["variant_order"] < 1:
        raise ValueError("Variant order must be a positive integer.")
    family = classification["family_key"]
    parent = classification["parent_exercise_key"]
    if role == "standalone":
        if family is not None or parent is not None:
            raise ValueError("Standalone exercises have no family or parent.")
    else:
        require_stable_key(family)
    if parent is not None:
        if not isinstance(parent, dict) or ExerciseReference(**parent) == reference:
            raise ValueError("An exercise cannot be its own parent.")
        if role == "base":
            raise ValueError("A base exercise cannot have a parent.")
