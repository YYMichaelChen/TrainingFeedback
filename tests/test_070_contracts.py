"""070-A contract examples, fixed identity mapping and old-fact preservation."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from migration_070_fixtures import create_schema16_baseline, logical_baseline

from training_feedback.app import LibraryContext
from training_feedback.data.catalog_builder import source_content
from training_feedback.data.catalog_conversion import convert_catalog_root
from training_feedback.data.catalog_repository import CatalogRepository
from training_feedback.data.catalog_resources import catalog_directory
from training_feedback.data.conversion_repository import OLD_TABLES
from training_feedback.data.seed.catalog import bundled_catalog
from training_feedback.data.seed.families import FAMILIES, catalog_classification
from training_feedback.domain.action_groups import ActionGroup, GroupMember, SideSequence
from training_feedback.domain.catalog import ExerciseReference, content_sha256
from training_feedback.domain.plans import PlannedSet

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs" / "contracts"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def example():
    return load_json(CONTRACTS / "plan-v2.example.json")


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
    schema = load_json(CONTRACTS / "plan-v2.schema.json")
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
    baseline_path = CONTRACTS / "baseline/catalog-070-baseline.json"
    assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == (
        "d3555e076d4a553996d2a0917c53fa224632778a369d9e70c821981efd629521"
    )
    baseline = load_json(baseline_path)
    assert baseline["application_baseline"] == "0.6.1"
    assert baseline["database_schema_baseline"] == 16
    assert "not shipped 0.7.0 artwork or approval" in baseline["notice"]

    v1_path = CONTRACTS / "baseline/plan-v1-baseline.schema.json"
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


def test_schema16_fixture_preserves_full_facts_on_copy_and_reopen(tmp_path):
    result = create_schema16_baseline(tmp_path / "original")
    original = result["baseline"]
    tables = original["tables"]
    mapping = result["mapping_expectations"]
    assert {r["status"] for r in tables["training_session"]} == {"completed", "partial", "paused"}
    assert {r["guidance_reviewed_snapshot"] for r in tables["training_session_action"]} == {
        None, 0, 1,
    }
    assert any(row["value"] == 0 for row in tables["training_session_actual_set"])
    assert any(row["result"] is None for row in tables["training_session_action"])
    assert any(row["value"] is None for row in tables["next_day_feedback_area"])
    assert len(tables["session_result_retraction"]) == 1
    assert len(tables["note_correction_audit"]) == 1
    assert tables["plan_import"] and tables["ai_export"]
    revisions = {row["id"]: row for row in tables["exercise_guidance_revision"]}
    current = json.loads(revisions[mapping["selected_override_id"]]["guidance_json"])
    prior = json.loads(revisions[mapping["historical_guidance_id"]]["guidance_json"])
    assert current["purpose"] == "【合成迁移数据】  自定义原文\t\r\n末尾空格  "
    assert current["purpose"] != prior["purpose"]
    assert prior["images"][0]["status"] == "missing"
    assert current["review"]["reviewed_at"] == "2026-09-09"
    assert current["review"]["review_answer_file"] in original["resources"]
    assert current["images"][0]["path"] in original["resources"]
    assert "exercise-images/synthetic-corrupt.png" in original["resources"]
    assert "exercise-images/synthetic-absent.png" not in original["resources"]
    custom_rows = [row for row in tables["exercise"] if row["id"] in mapping["custom_old_ids"]]
    assert len(custom_rows) == 3
    assert {row["bundled_exercise_key"] for row in custom_rows} == {None, "retired.synthetic-key"}
    assert any(row["active"] == 0 for row in custom_rows)
    copy = tmp_path / "副本 copy"
    shutil.copytree(result["data_root"], copy)
    assert logical_baseline(copy) == original
    assert logical_baseline(result["data_root"]) == original
    assert convert_catalog_root(copy)
    assert not convert_catalog_root(copy)
    with LibraryContext.reopen(copy) as context:
        db = context.database.connection
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert not names.intersection(OLD_TABLES)
        preserved = {}
        for row in db.execute("SELECT * FROM conversion_original"):
            preserved.setdefault(row["source_table"], []).append(json.loads(row["row_json"]))
        for table, records in tables.items():
            if table in OLD_TABLES:
                ordered = sorted(preserved.get(table, []),
                                 key=lambda row: json.dumps(row, sort_keys=True))
                assert ordered == sorted(records, key=lambda row: json.dumps(row, sort_keys=True))
        assert preserved["app_config"][0]["synthetic_unknown_setting"] == {
            "original": "  保留\t未知设置  "}
        assert "synthetic_unknown_setting" not in json.loads(
            (copy / "app_config.json").read_text(encoding="utf-8"))
        bridge = ExerciseReference("bundled", "launch.glute-bridge")
        contents = context.user_library.contents(bridge)
        selected = context.library.get(bridge)["selected"]
        assert selected["provenance"]["original_revision"]["id"] == mapping["selected_override_id"]
        assert selected["content"]["guidance"]["purpose"] == current["purpose"]
        assert context.user_library.review_events(selected["id"])[0]["image_hashes"] == []
        impacts = context.removals.repository.impacts({"source": "bundled", "key": bridge.key})
        assert any(row.get("provenance") == "converted_registration" for row in impacts["exports"])
        assert len(contents) >= 2
        for identifier in mapping["custom_old_ids"]:
            identity = json.loads(db.execute(
                "SELECT target_json FROM conversion_mapping WHERE source_table='exercise' "
                "AND source_key=?", (str(identifier),)).fetchone()[0])
            assert identity["source"] == "custom"
        for before in tables["training_session"]:
            session = context.sessions.get(before["id"])
            assert session["status"] == before["status"]
            actions = [a for a in tables["training_session_action"]
                       if a["session_id"] == before["id"]]
            assert len(session["occurrences"]) == len(actions)
            for action in actions:
                occurrence = next(row for row in session["occurrences"]
                                  if row["id"] == action["id"])
                assert occurrence["result"] == action["result"]
                assert occurrence["note"] == action["note"]
                assert occurrence["recorded_at"] is None
                assert occurrence["start_review"]["eligibility"]["reviewed"] == (
                    None if action["guidance_reviewed_snapshot"] is None
                    else bool(action["guidance_reviewed_snapshot"]))
                assert occurrence["start_review"]["eligibility"]["images_ready"] is None
                actual = [a for a in tables["training_session_actual_set"]
                          if a["session_action_id"] == action["id"]]
                values = [(a["value"], a["unit"], a["per_side"])
                          for a in occurrence["actual_sets"]]
                assert values == [(a["value"], a["unit"], bool(a["per_side"])) for a in actual]
        exported = context.session_handoff.export(result["sessions"]["completed"])
        evidence = load_json(exported / "evidence.json")
        assert evidence["provenance"]["export_id"] > max(row["id"] for row in tables["ai_export"])
        observed = evidence["session"]["occurrences"][0]["start_review"]["eligibility"]
        assert observed["reviewed"] is None
        assert "未知（未记录）" in (exported / "evidence.md").read_text(encoding="utf-8")
        assert evidence["conversion_registrations"]
        for path, digest in original["resources"].items():
            if path not in {"app_config.json", ".training-feedback.lock"}:
                import hashlib

                assert hashlib.sha256((copy / path).read_bytes()).hexdigest() == digest
