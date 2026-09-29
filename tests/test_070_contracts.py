"""070-A contract examples, fixed identity mapping and old-fact preservation."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from training_feedback.data.catalog_builder import source_content
from training_feedback.data.catalog_repository import CatalogRepository
from training_feedback.data.catalog_resources import catalog_directory
from training_feedback.data.seed.catalog import bundled_catalog
from training_feedback.data.seed.families import FAMILIES, catalog_classification
from training_feedback.domain.action_groups import ActionGroup, GroupMember, SideSequence
from training_feedback.domain.catalog import ExerciseReference, content_sha256
from training_feedback.domain.plans import PlannedSet

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CONTRACTS = ROOT / "docs" / "reference" / "contracts"
RUNTIME_CONTRACTS = ROOT / "src" / "training_feedback" / "contracts"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def example():
    return load_json(REFERENCE_CONTRACTS / "plan-v3.example.json")


def group_contract(payload=None):
    group = payload or example()["plan"]["days"][0]["items"][1]
    members = tuple(
        GroupMember(
            member["item_id"], member["order"],
            tuple(PlannedSet(
                dose["order"], dose["unit"], dose["value"], dose["per_side"], dose["note"]
            ) for dose in member["sets"]),
            member["classification"]["starting_position_class"],
            member["rest_after_member_seconds"],
        ) for member in group["members"]
    )
    return ActionGroup(
        group["item_id"], members, group["round_count"], group["side_sequence"],
        group["first_side"], group["rest_between_sides_seconds"],
        group["rest_between_rounds_seconds"], group["rest_after_group_seconds"],
        group["transition"],
    )


@pytest.fixture
def validator():
    schema = load_json(RUNTIME_CONTRACTS / "plan-v3.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize("mutation", [
    lambda p: p["plan"].update(approved=True),
    lambda p: p["plan"]["days"][0]["items"][0]["exercise"].update(source="legacy"),
    lambda p: p["plan"]["days"][0]["items"][1]["members"][0].update(kind="group"),
])
def test_v2_schema_rejects_fabricated_state_namespace_and_nested_groups(validator, mutation):
    payload = example()
    mutation(payload)
    assert list(validator.iter_errors(payload))


def test_mixed_units_and_sides_remain_separate_occurrences():
    group = group_contract()
    bilateral = replace(group.members[1], sets=(PlannedSet(1, "seconds", 20),))
    group = replace(group, members=(group.members[0], bilateral),
                    side_sequence=SideSequence.MEMBER_EACH_SIDE)
    assert [(o.member_id, o.side) for o in group.occurrences()][:3] == [
        ("example.kick", "left"), ("example.kick", "right"), ("example.hydrant", None),
    ]
    with pytest.raises(ValueError, match="all members"):
        replace(group, side_sequence=SideSequence.SAME_SIDE_THEN_SWITCH)


@pytest.mark.parametrize("changes", [
    {"round_count": 0}, {"first_side": None}, {"rest_after_group_seconds": -1},
])
def test_group_rejects_invalid_rounds_missing_side_and_negative_rest(changes):
    with pytest.raises(ValueError):
        replace(group_contract(), **changes)


def test_group_identity_position_and_member_rules():
    group = group_contract()
    with pytest.raises(ValueError, match="identities"):
        replace(group, item_id=group.members[0].item_id)
    with pytest.raises(ValueError, match="unique"):
        replace(group, members=(group.members[0], replace(group.members[1], order=1)))
    with pytest.raises(ValueError, match="per-side convention"):
        replace(group.members[0], sets=(PlannedSet(1, "reps", 1, True),
                                       PlannedSet(2, "reps", 1, False)))
    with pytest.raises(ValueError, match="one dose unit"):
        replace(group.members[0], sets=(PlannedSet(1, "reps", 1, True),
                                       PlannedSet(2, "seconds", 1, True)))
    with pytest.raises(ValueError, match="final member"):
        replace(group, members=(group.members[0],
                                replace(group.members[1], rest_after_member_seconds=5)))
    mixed = replace(group, members=(replace(group.members[0], starting_position="prone"),
                                    group.members[1]), transition="")
    with pytest.raises(ValueError, match="transition"):
        mixed.require_transition_for_activation()
    replace(mixed, transition="【合成】俯卧转四点支撑").require_transition_for_activation()
    group.require_transition_for_activation()


def test_round_expansion_is_lazy_and_respects_right_first_and_member_order():
    group = replace(group_contract(), round_count=10**12, first_side="right")
    group = replace(group, members=tuple(reversed(group.members)))
    occurrences = group.occurrences()
    first = next(occurrences)
    assert (first.round_number, first.member_id, first.side) == (1, "example.kick", "right")
    assert next(occurrences).member_id == "example.hydrant"


def test_terminal_and_bilateral_rest_fields_cannot_hide_extra_rest():
    group = group_contract()
    with pytest.raises(ValueError, match="One round"):
        replace(group, round_count=1)
    bilateral = tuple(replace(member, sets=(PlannedSet(1, "reps", 1),))
                      for member in group.members)
    with pytest.raises(ValueError, match="no first side"):
        replace(group, members=bilateral, side_sequence="member_each_side")
    with pytest.raises(ValueError, match="side-switch rest"):
        replace(group, members=bilateral, side_sequence="member_each_side", first_side=None)
    valid = replace(group, members=bilateral, side_sequence="member_each_side", first_side=None,
                    rest_between_sides_seconds=0)
    assert all(occurrence.side is None for occurrence in valid.occurrences())


def test_identity_and_hash_preserve_namespaces_text_and_array_order():
    assert ExerciseReference("bundled", "same-key") != ExerciseReference("custom", "same-key")
    for key in ("", "../escape", "with space", "a\n"):
        with pytest.raises(ValueError):
            ExerciseReference("bundled", key)
    assert content_sha256({"a": 1, "b": "  文本\t\r\n"}) == content_sha256(
        {"b": "  文本\t\r\n", "a": 1}
    )
    assert content_sha256({"text": " x "}) != content_sha256({"text": "x"})
    assert content_sha256({"items": [1, 2]}) != content_sha256({"items": [2, 1]})
    with pytest.raises(ValueError):
        content_sha256({"value": math.nan})


def test_catalog_inventory_covers_all_source_identities_and_freezes_v1():
    baseline_path = REFERENCE_CONTRACTS / "baseline/catalog-070-baseline.json"
    assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == (
        "d3555e076d4a553996d2a0917c53fa224632778a369d9e70c821981efd629521"
    )
    baseline = load_json(baseline_path)
    assert baseline["application_baseline"] == "0.6.1"
    assert baseline["database_schema_baseline"] == 16
    assert "not shipped 0.7.0 artwork or approval" in baseline["notice"]

    v1_path = REFERENCE_CONTRACTS / "baseline/plan-v1-baseline.schema.json"
    assert hashlib.sha256(v1_path.read_bytes()).hexdigest() == (
        "ecedf88628c687ca9aeb789005f717e8e0d81dc4340f82b36e26f9259956e41f"
    )
    v1_schema = load_json(v1_path)
    Draft202012Validator.check_schema(v1_schema)
    assert v1_schema["properties"]["schema_version"] == {"const": 1}

    classification = catalog_classification()
    historical = {entry["exercise"]["key"]: entry for entry in baseline["entries"]}
    current = {
        entry["content"]["exercise"]["key"]: entry
        for entry in source_content()
    }
    assert len(historical) == len(baseline["entries"]) == 36
    assert set(historical) == set(current) == set(classification)
    assert len(classification) == 36
    assert set(classification) == {seed["exercise_key"] for seed in bundled_catalog()}
    assert sum(len(family.member_keys) for family in FAMILIES) == 18
    assert sum(c["variant_role"] == "standalone" for c in classification.values()) == 18
    content_doc = (ROOT / "docs/initial-exercises-and-plan.md").read_text(encoding="utf-8")
    for entry in baseline["entries"]:
        assert entry["canonical_name"] in content_doc
        assert entry["image_readiness"] == "missing"
        assert entry["external_review"] == "unreviewed"
        assert all(image == {
            "path": None,
            "caption": "暂无动作示意图",
            "status": "missing",
            "required": True,
            "sha256": None,
        } for image in entry["images"])

    directory = catalog_directory()
    manifest = load_json(directory / "catalog-manifest.json")
    expected_contents = [
        {
            "key": entry["content"]["exercise"]["key"],
            "id": entry["id"],
            "version": entry["version"],
            "sha256": entry["sha256"],
        }
        for entry in source_content()
    ]
    assert manifest["application"] == "TrainingFeedback"
    assert manifest["format_version"] == 1
    assert manifest["contents"] == expected_contents
    declared_files = {item["path"]: item for item in manifest["files"]}
    actual_files = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file() and path.name != "catalog-manifest.json"
    }
    assert set(declared_files) == actual_files
    for relative, item in declared_files.items():
        payload = (directory / relative).read_bytes()
        assert len(payload) == item["bytes"]
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]

    with CatalogRepository(directory) as catalog:
        shipped = {
            entry["content"]["exercise"]["key"]: entry
            for entry in catalog.list()
        }
    assert set(shipped) == set(current)
    for key, entry in current.items():
        serialized_content = json.loads(json.dumps(entry["content"], ensure_ascii=False))
        assert historical[key]["exercise"] == entry["content"]["exercise"]
        assert historical[key]["content"]["id"] == entry["id"]
        assert entry["content"]["classification"] == classification[key]
        assert shipped[key] == {
            "reference": {
                "id": entry["id"],
                "version": entry["version"],
                "sha256": entry["sha256"],
            },
            "content": serialized_content,
            "withdrawn": False,
        }
        for image in entry["content"]["guidance"]["images"]:
            assert image["status"] == "available"
            assert image["required"] is True
            assert declared_files[image["path"]]["sha256"] == image["sha256"]
    assert classification["main.quadruped-straight-leg-kickback"][
        "starting_position_class"
    ] == "quadruped"
    assert classification["main.prone-straight-leg-raise"]["starting_position_class"] == "prone"
