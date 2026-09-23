"""070-D real schema/service/UI integration with isolated synthetic catalogs and roots."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from copy import deepcopy
from pathlib import Path

import pytest
from image_fixtures import png_bytes
from PySide6.QtWidgets import QDialog, QMessageBox

from training_feedback.app import LibraryContext
from training_feedback.application.library_workflow import LibraryTarget
from training_feedback.data.catalog_builder import build_catalog, source_content
from training_feedback.data.database import transaction
from training_feedback.data.plan_contract import plan_v2_schema
from training_feedback.domain.catalog import ExerciseReference, content_sha256
from training_feedback.domain.group_plans import (
    PlanDocument,
    diff_plans,
    plan_actions,
    validate_plan_payload,
)
from training_feedback.ui.group_plan_page import (
    ActionPrescriptionDialog,
    GroupPlanActivation,
    GroupPlanEditor,
    GroupPrescriptionDialog,
    render_plan,
)

ROOT = Path(__file__).resolve().parents[1]
PNG = png_bytes()
DIGEST = hashlib.sha256(PNG).hexdigest()


@pytest.fixture
def context(tmp_path):
    entries = source_content()
    for entry in entries:
        entry["content"]["guidance"]["images"] = [
            {
                "path": "images/synthetic.png",
                "sha256": DIGEST,
                "status": "available",
                "required": True,
                "caption": "【合成计划测试】非训练图片",
            }
        ]
        entry["sha256"] = content_sha256(entry["content"])
    catalog = build_catalog(
        tmp_path / "program/catalog", entries=entries, assets={"images/synthetic.png": PNG}
    )
    with LibraryContext.create(tmp_path / "user", catalog_path=catalog) as result:
        yield result


@pytest.fixture
def payload(context):
    value = json.loads((ROOT / "docs/contracts/plan-v2.example.json").read_text(encoding="utf-8"))
    value["plan"].pop("target_plan_name")
    for _day, _item, action in plan_actions(value["plan"]):
        entry = context.catalog.get(action["exercise"]["key"])
        action["content"] = entry["reference"]
        action["classification"] = entry["content"]["classification"]
    return value


def enable(context, payload):
    targets = {
        action["exercise"]["key"]: LibraryTarget(
            ExerciseReference(**action["exercise"]),
            action["content"],
        )
        for _day, _item, action in plan_actions(payload["plan"])
    }
    context.library.select_contents(list(targets.values()), user_confirmed=True)
    context.library.set_enabled_batch(list(targets.values()), True, user_confirmed=True)


def activate(context, identifier):
    preview = context.plans.preview(identifier)
    context.plans.activate(identifier, expected_preview=preview["token"], user_confirmed=True)
    return preview


def test_runtime_schema_matches_reviewed_contract_and_only_accepts_v2():
    assert plan_v2_schema() == json.loads(
        (ROOT / "docs/contracts/plan-v2.schema.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ValueError, match="version 2"):
        validate_plan_payload({"schema_version": 1}, plan_v2_schema())


def test_normalized_save_reopen_and_unequal_group_doses_remain_verbatim(context, payload):
    identifier = context.plans.create(payload)
    saved = context.plans.get(identifier)
    assert saved["payload"] == payload
    assert saved["status"] == "draft" and saved["pins"] == []
    connection = context.database.connection
    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("group_plan_day", "group_plan_item", "group_plan_set")
    }
    assert counts == {"group_plan_day": 1, "group_plan_item": 4, "group_plan_set": 4}
    with LibraryContext.reopen(
        context.data_root.path, catalog_path=context.catalog.directory
    ) as other:
        assert other.plans.get(identifier) == saved
    assert context.library.user.references() == []  # saving a draft does not select/enable/review


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p.update(schema_version=True),
        lambda p: p["plan"]["days"][0]["items"][1].update(item_id="example.bridge"),
        lambda p: p["plan"]["days"][0]["items"][0]["sets"][0].update(value=math.nan),
        lambda p: p["plan"]["days"][0]["items"][0]["content"].update(sha256="0" * 64),
        lambda p: p["plan"]["days"][0]["items"][0]["exercise"].update(key="unknown.exercise"),
    ],
)
def test_invalid_v2_inputs_leave_no_partial_plan(context, payload, mutation):
    mutation(payload)
    with pytest.raises(ValueError):
        context.plans.create(payload)
    assert context.plans.list_plans() == []
    assert context.library.user.references() == []


def test_activation_freezes_prescription_and_assets_and_cloning_preserves_lineage(context, payload):
    enable(context, payload)
    identifier = context.plans.create(payload)
    preview = activate(context, identifier)
    assert set(preview["unreviewed"]) == {"臀桥", "直腿后踢", "消防栓"}
    saved = context.plans.get(identifier)
    assert saved["status"] == "active" and len(saved["pins"]) == 3
    assert all(pin["review"]["reviewed"] is False for pin in saved["pins"])
    with pytest.raises(ValueError, match="Only draft"):
        context.plans.save(identifier, payload, expected_token=saved["edit_token"])
    for query in (
        "UPDATE group_plan_set SET value=999",
        "DELETE FROM group_plan_item",
        "UPDATE group_plan_revision SET status='draft'",
        "DELETE FROM group_plan_pin",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            with transaction(context.database.connection):
                context.database.connection.execute(query)
    clone = context.plans.clone(identifier)
    cloned = context.plans.get(clone)
    assert cloned["payload"] == saved["payload"] and cloned["pins"] == []
    activate(context, clone)
    old = context.plans.get(identifier)
    assert old["status"] == "superseded"
    assert old["pins"] == saved["pins"] and old["payload"] == saved["payload"]
    assert context.snapshot_assets.read(DIGEST) == PNG


def test_stale_edit_and_activation_preview_reject_changes(context, payload):
    enable(context, payload)
    identifier = context.plans.create(payload)
    original = context.plans.get(identifier)
    preview = context.plans.preview(identifier)
    changed = deepcopy(payload)
    changed["plan"]["purpose"] += "【合成】修改"
    context.plans.save(identifier, changed, expected_token=original["edit_token"])
    with pytest.raises(ValueError, match="changed"):
        context.plans.save(identifier, payload, expected_token=original["edit_token"])
    with pytest.raises(ValueError, match="preview changed"):
        context.plans.activate(identifier, expected_preview=preview["token"], user_confirmed=True)
    assert context.plans.get(identifier)["pins"] == []
    preview = context.plans.preview(identifier)
    action = changed["plan"]["days"][0]["items"][0]
    item = LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
    context.library.record_review(
        [item],
        reviewer_type="external_ai_expert",
        source="【合成】来源",
        occurred_at="2026-09-17",
        note="",
        user_confirmed=True,
    )
    with pytest.raises(ValueError, match="preview changed"):
        context.plans.activate(identifier, expected_preview=preview["token"], user_confirmed=True)
    assert context.plans.get(identifier)["status"] == "draft"


def test_activation_failure_on_second_pin_rolls_back_everything(context, payload, monkeypatch):
    enable(context, payload)
    first = context.plans.create(payload)
    activate(context, first)
    draft = context.plans.clone(first)
    preview = context.plans.preview(draft)
    original = context.plans.repository.pin
    count = 0

    def fail(*args):
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError("injected pin failure")
        return original(*args)

    monkeypatch.setattr(context.plans.repository, "pin", fail)
    with pytest.raises(RuntimeError, match="injected"):
        context.plans.activate(draft, expected_preview=preview["token"], user_confirmed=True)
    assert context.plans.get(draft)["pins"] == []
    assert context.plans.get(draft)["status"] == "draft"
    assert context.plans.get(first)["status"] == "active"


def test_late_save_failure_restores_entire_draft(context, payload, monkeypatch):
    identifier = context.plans.create(payload)
    before = context.plans.get(identifier)

    def fail(*args):
        raise RuntimeError("injected child failure")

    monkeypatch.setattr(context.plans.repository, "_children", fail)
    changed = deepcopy(payload)
    changed["plan"]["purpose"] = "different"
    with pytest.raises(RuntimeError):
        context.plans.save(identifier, changed, expected_token=before["edit_token"])
    assert context.plans.get(identifier) == before


def test_mixed_positions_require_transition_only_at_activation(context, payload):
    group = payload["plan"]["days"][0]["items"][1]
    member = group["members"][0]
    prone = next(
        choice
        for choice in context.plans.exercise_choices()
        if choice["exercise"]["key"] == "main.prone-straight-leg-raise"
    )
    member.update(prone)
    group["transition"] = ""
    enable(context, payload)
    identifier = context.plans.create(payload)
    with pytest.raises(ValueError, match="transition"):
        context.plans.preview(identifier)
    group["transition"] = "【合成】俯卧转四点支撑"
    context.plans.save(identifier, payload, expected_token=1)
    activate(context, identifier)


def test_item_key_cannot_be_reused_for_a_different_movement(context, payload):
    identifier = context.plans.create(payload)
    changed = deepcopy(payload)
    changed["plan"]["days"][0]["items"][0].update(
        next(
            choice
            for choice in context.plans.exercise_choices()
            if choice["exercise"]["key"] == "launch.dead-bug"
        )
    )
    with pytest.raises(ValueError, match="reused item identity"):
        context.plans.save(identifier, changed, expected_token=1)
    assert context.plans.get(identifier)["payload"] == payload


def test_v2_file_import_retains_original_and_does_not_activate(context, payload, tmp_path):
    path = tmp_path / "外部计划.json"
    raw = json.dumps(payload, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")
    path.write_bytes(raw)
    identifier = context.plan_handoff.import_file(path)
    imported = context.plans.get(identifier)
    assert imported["status"] == "draft" and imported["pins"] == []
    assert context.library.user.references() == []
    stored = context.data_root.path / imported["import"]["source_path"]
    assert stored.read_bytes() == raw
    changed = deepcopy(payload)
    changed["rationale"] = "【合成】本地调整"
    context.plans.save(identifier, changed, expected_token=1)
    assert context.plans.get(identifier)["import"] == imported["import"]
    assert stored.read_bytes() == raw


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":1}',
        b'{"schema_version":2,"schema_version":2}',
        b'{"schema_version":2,"bad":NaN}',
    ],
)
def test_bad_import_files_leave_no_managed_files(context, tmp_path, raw):
    source = tmp_path / "bad.json"
    source.write_bytes(raw)
    with pytest.raises(ValueError):
        context.plan_handoff.import_file(source)
    assert context.plans.list_plans() == []
    assert list((context.data_root.path / "imports").iterdir()) == []


def test_import_registration_failure_cleans_file_and_rows(context, payload, tmp_path, monkeypatch):
    source = tmp_path / "plan.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    def fail(*args):
        raise RuntimeError("injected import failure")

    monkeypatch.setattr(context.plans.repository, "register_import", fail)
    with pytest.raises(RuntimeError):
        context.plan_handoff.import_file(source)
    assert context.plans.list_plans() == []
    assert list((context.data_root.path / "imports").iterdir()) == []


def test_export_is_portable_and_json_markdown_agree_after_catalog_replacement(
    context, payload, tmp_path
):
    enable(context, payload)
    identifier = context.plans.create(payload)
    activate(context, identifier)
    baseline = context.plans.get(identifier)
    # Pinned content survives complete replacement by an empty catalog.
    new_catalog = build_catalog(tmp_path / "replacement", entries=[], version="removed-all-test")
    with LibraryContext.reopen(context.data_root.path, catalog_path=new_catalog) as reopened:
        destination = reopened.plan_handoff.export(identifier)
        evidence = json.loads((destination / "evidence.json").read_text(encoding="utf-8"))
        assert evidence["schema_version"] == 2
        assert evidence["revision"] == baseline
        assert len(evidence["assets"]) == 1 and len(evidence["contents"]) == 3
        asset = evidence["assets"][0]
        assert (destination / asset["path"]).read_bytes() == PNG
        markdown = (destination / "evidence.md").read_text(encoding="utf-8")
        embedded = markdown.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
        assert json.loads(embedded) == evidence
        assert json.loads((destination / "plan.json").read_text(encoding="utf-8")) == payload
    # Unknown source identities fail; an existing managed export ID can be returned as a source.
    returned = deepcopy(payload)
    returned["plan"]["target_plan_name"] = payload["plan"]["name"]
    returned["source"] = {"session_id": None, "export_id": evidence["provenance"]["export_id"]}
    path = tmp_path / "response.json"
    path.write_text(json.dumps(returned), encoding="utf-8")
    imported = context.plan_handoff.import_file(path)
    assert context.plans.get(imported)["status"] == "draft"
    assert context.plans.get(identifier) == baseline
    returned["source"]["export_id"] = 999999
    path.write_text(json.dumps(returned), encoding="utf-8")
    with pytest.raises(ValueError, match="data root"):
        context.plan_handoff.import_file(path)


def test_export_failure_cleans_files_and_registration(context, payload, monkeypatch):
    identifier = context.plans.create(payload)
    import training_feedback.data.group_plan_handoff as handoff_module

    monkeypatch.setattr(
        handoff_module.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("fail"))
    )
    with pytest.raises(OSError):
        context.plan_handoff.export(identifier)
    assert list((context.data_root.path / "exports").iterdir()) == []
    assert (
        context.database.connection.execute("SELECT COUNT(*) FROM group_plan_export").fetchone()[0]
        == 0
    )


def test_document_move_remove_and_dissolve_require_explicit_choices(payload):
    original = deepcopy(payload["plan"])
    document = PlanDocument(original)
    document.add_day("【合成】第二天")
    document.move_item_to_day(0, 0, 1)
    assert original == payload["plan"]
    with pytest.raises(ValueError, match="dissolution"):
        document.remove_member(0, 0, 0)
    assert len(document.plan["days"][0]["items"][0]["members"]) == 2
    document.plan["days"][0]["items"][0]["round_count"] = 1
    document.plan["days"][0]["items"][0]["rest_between_rounds_seconds"] = 0
    document.remove_member(0, 0, 0, dissolve=True)
    remaining = document.plan["days"][0]["items"][0]
    assert remaining["kind"] == "action" and remaining["item_id"] == "example.hydrant"
    assert remaining["sets"][0]["value"] == 1


def test_action_editor_invalid_input_stays_visible_and_cancel_does_not_write(
    qt_app, context, payload, monkeypatch
):
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    action = payload["plan"]["days"][0]["items"][0]
    dialog = ActionPrescriptionDialog(context.plans.exercise_choices(), action)
    dialog.sets.item(0, 0).setText("not a number")
    dialog.save()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.sets.item(0, 0).text() == "not a number" and warnings
    dialog.reject()
    assert context.plans.list_plans() == []
    dialog = ActionPrescriptionDialog(context.plans.exercise_choices(), action)
    dialog.save()
    assert dialog.value == action


def test_ui_group_plan_creation_edit_cancel_and_confirmation(qt_app, context, payload, monkeypatch):
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    editor = GroupPlanEditor(context.plans)
    editor.document = PlanDocument(payload["plan"])
    editor.name.setText(payload["plan"]["name"])
    editor.purpose.setPlainText("【合成】界面目的")
    editor.rationale.setPlainText(payload["rationale"])
    editor.save()
    assert editor.result() == QDialog.DialogCode.Accepted
    identifier = editor.saved_id
    saved = context.plans.get(identifier)
    cancelled = GroupPlanEditor(context.plans, saved)
    cancelled.name.setText("unsaved")
    cancelled.reject()
    assert context.plans.get(identifier) == saved
    enable(context, saved["payload"])
    preview = GroupPlanActivation(context.plans, identifier)
    preview.show()
    qt_app.processEvents()
    assert preview.buttons.isVisible() and preview.rect().contains(preview.buttons.geometry())
    preview.activate()
    assert warnings and context.plans.get(identifier)["status"] == "draft"
    preview.confirm.setChecked(True)
    preview.activate()
    assert context.plans.get(identifier)["status"] == "active"
    page = context.create_plan_page()
    assert page.revisions.count() == 1
    assert "轮数" in page.detail.toPlainText()
    assert "组间休息秒" in render_plan(saved["payload"]["plan"])


def test_group_editor_keeps_invalid_side_and_rest_inputs(qt_app, context, payload, monkeypatch):
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    group = payload["plan"]["days"][0]["items"][1]
    dialog = GroupPrescriptionDialog(context.plans.exercise_choices(), group)
    dialog.fields["rest_between_rounds_seconds"].setText("-5")
    dialog.save()
    assert dialog.value is None and warnings
    assert dialog.fields["rest_between_rounds_seconds"].text() == "-5"
    dialog.fields["rest_between_rounds_seconds"].setText("7")
    dialog.save()
    assert dialog.value == group


def test_zero_free_dose_and_original_note_rendering_are_not_defaults(context, payload):
    from training_feedback.ui.group_plan_page import render_fields

    first = payload["plan"]["days"][0]["items"][0]
    first["sets"][0].update(unit="free", value=None, note="  【合成】说明\r\n保留  ")
    first["sets"][1].update(unit="free", value=0, note="left")
    identifier = context.plans.create(payload)
    loaded = context.plans.get(identifier)["payload"]
    assert loaded == payload
    assert render_fields({"note": "left", "first_side": "left"}) == (
        "原始备注：left\n先做哪一侧：左侧"
    )
    first["sets"][0]["note"] = "\t "
    with pytest.raises(ValueError):
        context.plans.save(identifier, payload, expected_token=1)
    assert context.plans.get(identifier)["payload"] == loaded


def test_activation_rechecks_images_and_enabled_state_after_preview(context, payload):
    enable(context, payload)
    identifier = context.plans.create(payload)
    preview = context.plans.preview(identifier)
    path = context.snapshot_assets.root / DIGEST
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="eligible"):
        context.plans.activate(identifier, expected_preview=preview["token"], user_confirmed=True)
    assert context.plans.get(identifier)["pins"] == []
    path.write_bytes(PNG)
    action = payload["plan"]["days"][0]["items"][0]
    context.library.set_enabled(
        LibraryTarget(ExerciseReference(**action["exercise"]), action["content"]),
        False, user_confirmed=True,
    )
    with pytest.raises(ValueError, match="not enabled"):
        context.plans.activate(identifier, expected_preview=preview["token"], user_confirmed=True)
    assert context.plans.get(identifier)["status"] == "draft"


def test_another_activation_invalidates_preview_and_keeps_prior_pins(context, payload):
    enable(context, payload)
    first = context.plans.create(payload)
    second = context.plans.clone(first)
    preview = context.plans.preview(second)
    activate(context, first)
    with pytest.raises(ValueError, match="preview changed"):
        context.plans.activate(second, expected_preview=preview["token"], user_confirmed=True)
    assert context.plans.get(first)["status"] == "active"
    assert context.plans.get(second)["pins"] == []


def test_missing_historical_asset_exports_unknown_without_rewriting_activation(context, payload):
    enable(context, payload)
    identifier = context.plans.create(payload)
    activate(context, identifier)
    before = context.plans.get(identifier)
    (context.snapshot_assets.root / DIGEST).unlink()
    destination = context.plan_handoff.export(identifier)
    evidence = json.loads((destination / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["assets"] == []
    assert all(not row["images"][0]["available"] for row in evidence["contents"])
    assert context.plans.get(identifier) == before
    assert all(pin["review"]["eligible"] for pin in before["pins"])


def test_member_move_reorder_and_diff_preserve_repeated_movement_identity(payload):
    document = PlanDocument(payload["plan"])
    first = document.plan["days"][0]["items"][1]
    third = deepcopy(first["members"][0])
    third.update(item_id="additional.kick", order=3, rest_after_member_seconds=0)
    first["members"].append(third)
    second = deepcopy(first)
    second.update(item_id="group.two", order=3)
    for row in second["members"]:
        row["item_id"] += ".two"
    document.plan["days"][0]["items"].append(second)
    prior = deepcopy(document.plan)
    document.move_member(first, 2, second)
    assert len(first["members"]) == 2 and len(second["members"]) == 4
    changes = diff_plans(prior, document.plan)
    moved = next(row for row in changes if row["item_id"] == "additional.kick")
    assert moved["before"][1]["group_id"] != moved["after"][1]["group_id"]
    assert moved["before"][1]["exercise"] == moved["after"][1]["exercise"]
    with pytest.raises(ValueError, match="two members"):
        document.move_member(first, 0, second)
