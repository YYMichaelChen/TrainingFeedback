"""0.7.0 catalog classification, keyed by existing identities; not startup seeding."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.catalog import StartingPosition


@dataclass(frozen=True)
class ExerciseFamily:
    key: str
    name: str
    base_key: str | None
    member_keys: tuple[str, ...]
    starting_position: StartingPosition


FAMILIES = (
    ExerciseFamily(
        "family.glute-bridge", "臀桥动作族", "launch.glute-bridge",
        (
            "launch.glute-bridge", "launch.static-glute-bridge", "launch.butterfly-glute-bridge",
            "main.glute-bridge-leg-open-close", "main.glute-bridge-single-leg-kick",
            "main.single-leg-glute-bridge",
        ),
        StartingPosition.SUPINE,
    ),
    ExerciseFamily(
        "family.seated-supported-core", "坐姿支撑伸腿动作族", "main.crunch-leg-extension",
        (
            "main.crunch-leg-extension", "main.crunch-leg-extension-bicycle",
            "main.crunch-leg-extension-lateral", "main.crunch-leg-extension-combination",
        ),
        StartingPosition.SEATED,
    ),
    ExerciseFamily(
        "family.quadruped-hip", "四点支撑髋部动作族", None,
        (
            "main.quadruped-straight-leg-kickback", "main.donkey-kick", "main.donkey-kick-pulse",
            "main.diagonal-donkey-kick", "main.fire-hydrant",
        ),
        StartingPosition.QUADRUPED,
    ),
    ExerciseFamily(
        "family.prone-hip-extension", "俯卧髋伸动作族", "main.prone-straight-leg-raise",
        (
            "main.prone-straight-leg-raise", "main.prone-bent-knee-leg-raise",
            "main.prone-double-bent-knee-leg-raise",
        ),
        StartingPosition.PRONE,
    ),
)

STANDALONE_POSITIONS = {
    "launch.clamshell": StartingPosition.SIDE_LYING,
    "launch.chair-squat": StartingPosition.STANDING,
    "main.wall-supported-calf-raise": StartingPosition.STANDING,
    "launch.standing-forward-fold": StartingPosition.STANDING,
    "support.wall-calf-stretch": StartingPosition.STANDING,
    "launch.dead-bug": StartingPosition.SUPINE,
    "main.supine-straight-leg-open-close": StartingPosition.SUPINE,
    "launch.supine-360-diaphragmatic-breathing": StartingPosition.SUPINE,
    "launch.supine-figure-four-stretch": StartingPosition.SUPINE,
    "support.supine-single-knee-to-chest": StartingPosition.SUPINE,
    "main.bird-dog": StartingPosition.QUADRUPED,
    "launch.small-cat-cow": StartingPosition.QUADRUPED,
    "launch.kneeling-hip-thrust": StartingPosition.KNEELING,
    "main.kneeling-straight-arm-lean": StartingPosition.KNEELING,
    "launch.half-kneeling-hip-flexor-stretch": StartingPosition.KNEELING,
    "support.seated-upper-back-stretch": StartingPosition.KNEELING,
    "launch.seated-90-90-hip-switch": StartingPosition.SEATED,
    "launch.butterfly-stretch": StartingPosition.SEATED,
}


def catalog_classification() -> dict[str, dict]:
    result = {
        key: {
            "family_key": None, "variant_role": "standalone", "variant_order": 1,
            "parent_exercise_key": None, "starting_position_class": position.value,
        }
        for key, position in STANDALONE_POSITIONS.items()
    }
    for family in FAMILIES:
        for order, key in enumerate(family.member_keys, 1):
            if key in result:
                raise ValueError(f"Duplicate catalog classification: {key}")
            result[key] = {
                "family_key": family.key,
                "variant_role": "base" if key == family.base_key else "variant",
                "variant_order": order,
                # Related movements need not assert direct descent from the base.
                "parent_exercise_key": None,
                "starting_position_class": family.starting_position.value,
            }
    return result
