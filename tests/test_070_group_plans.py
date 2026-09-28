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
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QPushButton

from training_feedback.app import LibraryContext
from training_feedback.application.library_workflow import LibraryTarget
from training_feedback.data.catalog_builder import build_catalog, source_content
from training_feedback.data.database import transaction
from training_feedback.data.plan_contract import plan_v3_schema
from training_feedback.domain.catalog import ExerciseReference, content_sha256
from training_feedback.domain.group_plans import (
    PlanDocument,
    diff_plans,
    new_item_id,
    plan_actions,
    revision_code_for_change,
    validate_plan_payload,
)
from training_feedback.ui.group_plan_page import (
    ActionPrescriptionDialog,
    GroupPlanActivation,
    GroupPlanEditor,
    GroupPrescriptionDialog,
    MultiExerciseSelectionDialog,
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
    value = json.loads((ROOT / "docs/contracts/plan-v3.example.json").read_text(encoding="utf-8"))
    value["plan"].pop("target_plan_name", None)
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


def clone_plan(context, revision_id, *, name="【合成】独立副本"):
    used = {plan["base_number"] for plan in context.plans.list_plans()}
    base_number = next(number for number in range(1, 1000) if number not in used)
    return context.plans.clone(
        revision_id, base_number=base_number, name=name, change_description="",
    )


def activate(context, identifier):
    preview = context.plans.preview(identifier)
    context.plans.activate(identifier, expected_preview=preview["token"], user_confirmed=True)
    return preview


def test_runtime_schema_matches_reviewed_contract_and_only_accepts_v3():
    schema = plan_v3_schema()
    assert schema == json.loads(
        (ROOT / "docs/contracts/plan-v3.schema.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ValueError, match="version 3"):
        validate_plan_payload({"schema_version": 2}, schema)
    example = json.loads((ROOT / "docs/contracts/plan-v3.example.json").read_text(encoding="utf-8"))
    example["rationale"] = ""
    assert validate_plan_payload(example, schema)["rationale"] == ""


def test_revision_codes_classify_structure_and_text_and_grow_past_99(payload):
    original = deepcopy(payload["plan"])
    text_only = deepcopy(original)
    text_only["purpose"] += "【说明】"
    code, changes = revision_code_for_change(7, "plan-007.01.99", original, text_only)
    assert code == "plan-007.01.100" and changes
    structural = deepcopy(original)
    structural["days"][0]["items"][0]["phase"] = "cooldown"
    code, _ = revision_code_for_change(7, "plan-007.01.99", original, structural)
    assert code == "plan-007.02.00"
    with pytest.raises(ValueError, match="unchanged"):
        revision_code_for_change(7, "plan-007.01.99", original, deepcopy(original))


def test_upgrade_reopens_one_draft_and_recomputes_code_from_source(context, payload):
    enable(context, payload)
    identifier = context.plans.create(payload)
    activate(context, identifier)
    source = context.plans.get(identifier)
    assert source["plan_code"] == "plan-001.01.00"
    assert context.plans.upgrade_draft(identifier) is None

    unchanged = deepcopy(source["payload"])
    with pytest.raises(ValueError, match="unchanged"):
        context.plans.create_upgrade(identifier, unchanged)

    changed = deepcopy(source["payload"])
    changed["plan"]["purpose"] += "【改版】"
    draft_id = context.plans.create_upgrade(identifier, changed)
    draft = context.plans.get(draft_id)
    assert draft["plan_code"] == "plan-001.01.01"
    assert draft["upgrade_source_revision_id"] == identifier
    assert context.plans.upgrade_draft(identifier)["id"] == draft_id

    changed_again = deepcopy(draft["payload"])
    changed_again["plan"]["purpose"] += "【再编辑】"
    context.plans.save(draft_id, changed_again, expected_token=draft["edit_token"])
    updated = context.plans.get(draft_id)
    assert updated["plan_code"] == "plan-001.01.01"
    assert updated["revision_number"] == draft["revision_number"]


def test_normalized_save_reopen_and_unequal_group_doses_remain_verbatim(context, payload):
    identifier = context.plans.create(payload)
    saved = context.plans.get(identifier)
    assert saved["plan_code"] == "plan-001.01.00"
    assert saved["payload"] == {**payload, "plan_code": saved["plan_code"]}
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
def test_invalid_v3_inputs_leave_no_partial_plan(context, payload, mutation):
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
    clone = clone_plan(context, identifier)
    cloned = context.plans.get(clone)
    assert cloned["payload"]["plan"] | {"name": saved["name"]} == saved["payload"]["plan"]
    assert cloned["base_number"] != saved["base_number"] and cloned["pins"] == []
    activate(context, clone)
    old = context.plans.get(identifier)
    assert old["status"] == "active"
    assert old["pins"] == saved["pins"] and old["payload"] == saved["payload"]
    assert context.plans.get(clone)["status"] == "active"
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
    draft = clone_plan(context, first, name="【合成】失败回滚副本")
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


def test_v3_file_import_retains_original_and_does_not_activate(context, payload, tmp_path):
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


def test_v3_upgrade_import_targets_base_and_uses_difference_code(context, payload, tmp_path):
    enable(context, payload)
    active_id = context.plans.create(payload)
    activate(context, active_id)
    active = context.plans.get(active_id)
    imported = deepcopy(active["payload"])
    imported.update(intent="upgrade", target_base_number=active["base_number"])
    imported["plan"]["purpose"] += "【导入改版】"
    source = tmp_path / "upgrade.json"
    source.write_text(json.dumps(imported, ensure_ascii=False), encoding="utf-8")

    revision_id = context.plan_handoff.import_file(source)
    revision = context.plans.get(revision_id)
    assert revision["plan_id"] == active["plan_id"]
    assert revision["upgrade_source_revision_id"] == active_id
    assert revision["plan_code"] == "plan-001.01.01"
    assert revision["status"] == "draft"


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
        assert evidence["schema_version"] == 3
        assert evidence["revision"] == baseline
        assert len(evidence["assets"]) == 1 and len(evidence["contents"]) == 3
        asset = evidence["assets"][0]
        assert (destination / asset["path"]).read_bytes() == PNG
        markdown = (destination / "evidence.md").read_text(encoding="utf-8")
        embedded = markdown.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
        assert json.loads(embedded) == evidence
        exported_plan = json.loads((destination / "plan.json").read_text(encoding="utf-8"))
        assert exported_plan == payload | {"plan_code": "plan-001.01.00"}
    # Unknown source identities fail; an existing managed export ID can be returned as a source.
    returned = deepcopy(payload)
    returned["plan"]["name"] = "【合成】已导回计划"
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
    blank = ActionPrescriptionDialog(context.plans.exercise_choices())
    assert blank.rest.text() == "" and blank.side_rest.text() == ""
    blank.add_set()
    blank.add_set()
    assert blank.sets.item(0, 0).text() == ""
    assert blank.sets.item(0, 3).text() == ""
    blank.sets.item(0, 0).setText("2")
    blank.sets.item(0, 3).setText("5")
    blank.sets.item(0, 4).setText("  【合成】剂量原文  ")
    blank.sets.item(1, 0).setText("9")
    blank.sets.item(1, 3).setText("0")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
    blank.sets.setCurrentCell(0, 0)
    blank.fill_equal_sets()
    assert blank.sets.item(1, 0).text() == "2"
    assert blank.sets.item(1, 3).text() == "5"
    assert blank.sets.item(1, 4).text() == "  【合成】剂量原文  "


def test_new_plan_add_day_selects_it_and_add_action_opens(qt_app, context, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    editor = GroupPlanEditor(context.plans)
    assert any("不对应日历日期" in label.text() for label in editor.findChildren(QLabel))
    buttons = {button.text(): button for button in editor.findChildren(QPushButton)}
    selected = editor.tree.currentItem()
    assert selected.data(0, Qt.ItemDataRole.UserRole) == (0, None, None)
    selected.setText(0, "1. 【合成】上肢日")
    assert editor.document.plan["days"][0]["name"] == "【合成】上肢日"
    buttons["添加训练日"].click()
    selected = editor.tree.currentItem()
    assert selected.text(0) == "2. "
    assert selected.data(0, Qt.ItemDataRole.UserRole) == (1, None, None)

    buttons["添加动作"].click()
    first_editor = editor.inline_editor
    assert isinstance(first_editor, MultiExerciseSelectionDialog)
    assert not editor.tree.isEnabled()
    first_editor.search.setText(first_editor.exercise_list.item(0).text().split(" · ", 1)[0])
    assert first_editor.exercise_list.item(0).isHidden() is False
    first_editor.exercise_list.item(0).setSelected(True)
    first_editor.search.clear()
    first_editor.exercise_list.item(1).setSelected(True)
    first_editor.save()
    actions = editor.document.plan["days"][1]["items"]
    assert len(actions) == 2 and all(action["sets"] == [] for action in actions)
    assert editor.tree.currentItem().data(0, Qt.ItemDataRole.UserRole) == (1, 0, None)
    editor.name.setText("【合成】未完成计划")
    editor.save()
    assert editor.result() != QDialog.DialogCode.Accepted
    assert actions[0]["sets"] == []
    buttons["编辑所选项"].click()
    assert isinstance(editor.inline_editor, ActionPrescriptionDialog)
    editor.inline_editor.reject()
    editor.tree.setCurrentItem(editor.tree.topLevelItem(1))
    buttons["添加动作组"].click()
    assert isinstance(editor.inline_editor, GroupPrescriptionDialog)
    assert not editor.tree.isEnabled()
    editor.inline_editor.reject()
    assert editor.tree.currentItem().data(0, Qt.ItemDataRole.UserRole) == (1, None, None)


def test_editor_hierarchy_shows_selected_action_group_and_member_doses(qt_app, context, payload):
    editor = GroupPlanEditor(context.plans)
    editor.document = PlanDocument(payload["plan"])
    editor.refresh()
    day = editor.tree.topLevelItem(0)
    action = day.child(0)
    editor.tree.setCurrentItem(action)
    assert editor.detail_title.text() == payload["plan"]["days"][0]["items"][0]["exercise_name"]
    assert editor.detail_sets.rowCount() == 2
    group = day.child(1)
    editor.tree.setCurrentItem(group)
    assert editor.detail_sets.rowCount() == sum(
        len(member["sets"]) for member in payload["plan"]["days"][0]["items"][1]["members"]
    )
    member = group.child(0)
    editor.tree.setCurrentItem(member)
    assert editor.detail_title.text() == member.text(0).split(". ", 1)[1]
    assert editor.detail_sets.rowCount() == len(
        payload["plan"]["days"][0]["items"][1]["members"][0]["sets"]
    )


def test_ui_group_plan_creation_edit_cancel_and_confirmation(qt_app, context, payload, monkeypatch):
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
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
    assert page.presentation["days"][0]["items"][1]["round_count"] == (
        saved["payload"]["plan"]["days"][0]["items"][1]["round_count"]
    )
    assert page.presentation["days"][0]["items"][1]["rest_between_rounds"] == "7 秒"


def test_plan_page_shows_adjustment_without_technical_evidence(qt_app, context, payload,
                                                               monkeypatch):
    payload["rationale"] = "【合成】根据昨日记录减少臀部训练量"
    identifier = context.plans.create(payload)
    revision = deepcopy(context.plans.get(identifier))
    revision["import"] = {
        "original_payload": json.dumps({"rationale": "【合成】导入原文"}),
        "source_path": "imports/private-source.json",
    }
    revision["conversion_registrations"] = [{"source_id": 987}]
    revision["payload"]["plan"]["days"][0]["items"][0]["provenance"] = {
        "source_id": 987,
    }
    revision["payload"]["plan"]["days"][0]["items"][0]["source_id"] = 987
    revision["payload"]["plan"]["days"][0]["items"][0]["dose_scope"] = "per_side_aggregate"
    monkeypatch.setattr(context.plans, "get", lambda _identifier: revision)
    monkeypatch.setattr(context.plans, "content_issues", lambda _identifier: [])

    page = context.create_plan_page()
    visible_text = "\n".join(label.text() for label in page.findChildren(QLabel))
    assert page.presentation["adjustment"] == payload["rationale"]
    assert visible_text.count("调整说明：") == 1
    assert payload["rationale"] in visible_text
    assert "原始导入依据" not in visible_text
    assert "受管原件" not in visible_text
    assert "迁移保留" not in visible_text
    assert "private-source.json" not in visible_text
    assert "987" not in visible_text
    activation_text = render_plan(revision["payload"]["plan"], revision["rationale"])
    assert activation_text.count("调整说明：") == 1
    assert "987" not in activation_text
    assert "per_side_aggregate" not in activation_text
    assert page.presentation["days"][0]["items"][1]["kind"] == "group"
    group = page.presentation["days"][0]["items"][1]
    assert group["round_count"] == payload["plan"]["days"][0]["items"][1]["round_count"]
    assert all(member["sets"][0]["every_round"] for member in group["members"])


def test_plan_page_empty_state_and_revision_navigation(qt_app, context, payload):
    page = context.create_plan_page()
    assert page.revisions.count() == 0
    assert not page.empty_label.isHidden()
    assert page.detail_scroll.isHidden()

    first = context.plans.create(payload)
    second_payload = deepcopy(payload)
    second_payload["plan"]["name"] = "【合成】另一版计划"
    second_day = deepcopy(second_payload["plan"]["days"][0])
    second_day["order"] = 2
    second_day["name"] = "【合成】第二训练日"
    for plan_item in second_day["items"]:
        plan_item["item_id"] = new_item_id()
        if plan_item["kind"] == "group":
            for member in plan_item["members"]:
                member["item_id"] = new_item_id()
    second_payload["plan"]["days"].append(second_day)
    second = context.plans.create(second_payload)
    page.refresh(second)
    assert page.revisions.count() == 2
    assert page.revisions.currentItem().data(Qt.ItemDataRole.UserRole) == second
    assert page.revision_title.text() == second_payload["plan"]["name"]
    assert page.day_navigation.count() == len(second_payload["plan"]["days"])
    page.resize(1366, 768)
    page.show()
    qt_app.processEvents()
    page.day_navigation.setFocus()
    QTest.keyClick(page.day_navigation, Qt.Key.Key_Down)
    qt_app.processEvents()
    assert page.day_navigation.currentIndex() == 1
    assert page.detail_scroll.verticalScrollBar().value() > 0
    page.refresh(first)
    assert page.revisions.currentItem().data(Qt.ItemDataRole.UserRole) == first
    assert page.presentation["name"] == payload["plan"]["name"]


def test_plan_presentation_keeps_zero_unknown_and_per_side_distinct(context, payload):
    from training_feedback.ui.plan_presentation import plan_presentation

    identifier = context.plans.create(payload)
    revision = deepcopy(context.plans.get(identifier))
    action = revision["payload"]["plan"]["days"][0]["items"][0]
    action["rest_after_action_seconds"] = None
    action["rest_between_sides_seconds"] = 0.123456789
    action["sets"][0]["value"] = 1.123456789
    action["sets"][0]["rest_after_set_seconds"] = 0
    action["sets"][0]["per_side"] = False
    action["sets"][1]["per_side"] = True
    model = plan_presentation(revision)
    shown_action = model["days"][0]["items"][0]
    assert shown_action["rest_after"] == "未记录"
    assert shown_action["sets"][0]["rest"] == "0 秒"
    assert shown_action["sets"][0]["dose"] == "1.123456789 次"
    assert shown_action["rest_between_sides"] == "0.123456789 秒"
    assert shown_action["sets"][0]["per_side"] is False
    assert shown_action["sets"][1]["per_side"] is True

    missing = deepcopy(revision)
    missing_action = missing["payload"]["plan"]["days"][0]["items"][0]
    del missing_action["rest_after_action_seconds"]
    del missing_action["sets"][0]["rest_after_set_seconds"]
    missing_model = plan_presentation(missing)
    shown_missing = missing_model["days"][0]["items"][0]
    assert shown_missing["rest_after"] == "不适用"
    assert shown_missing["sets"][0]["rest"] == "不适用"


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
    blank = GroupPrescriptionDialog(context.plans.exercise_choices())
    assert all(field.text() == "" for field in blank.fields.values())


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
    second = clone_plan(context, first, name="【合成】并发激活副本")
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
