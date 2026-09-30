"""070-C image eligibility, exact review evidence and new-model Qt workflows."""

from __future__ import annotations

import hashlib
import sqlite3
from copy import deepcopy

import pytest
from image_fixtures import png_bytes
from PySide6.QtWidgets import QDialog

from training_feedback.app import LibraryContext
from training_feedback.application.library_workflow import LibraryTarget
from training_feedback.data.catalog_builder import build_catalog, source_content
from training_feedback.data.catalog_resources import CatalogError
from training_feedback.data.database import transaction
from training_feedback.domain.catalog import ExerciseReference, content_sha256
from training_feedback.ui.catalog_library_page import CatalogEditor
from training_feedback.ui.illustrations import IllustrationLabel

PNG = png_bytes()
DIGEST = hashlib.sha256(PNG).hexdigest()
BRIDGE = ExerciseReference("bundled", "launch.glute-bridge")
CLAM = ExerciseReference("bundled", "launch.clamshell")


@pytest.fixture
def context(tmp_path):
    entries = source_content()
    for entry in entries:
        entry["content"]["guidance"]["images"] = [{
            "path": "images/synthetic.png", "sha256": DIGEST, "status": "available",
            "required": True, "caption": "【合成测试图】不是专家审核素材",
        }]
        entry["sha256"] = content_sha256(entry["content"])
    catalog = build_catalog(tmp_path / "program/catalog", entries=entries,
                            assets={"images/synthetic.png": PNG})
    with LibraryContext.create(tmp_path / "user", catalog_path=catalog) as result:
        yield result


def target(context, reference=BRIDGE):
    return LibraryTarget(reference, context.catalog.get(reference.key)["reference"])


def local_target(context, identifier):
    entry = context.user_library.content(identifier)
    return LibraryTarget(ExerciseReference(**entry["content"]["exercise"]), entry["reference"])


def record(service, targets, **kwargs):
    service.record_review(
        targets, reviewer_type="external_ai_expert", source="【合成】外部审核来源",
        occurred_at="2026-09-17", note="  【合成】原文\t\r\n保留  ",
        user_confirmed=True, **kwargs,
    )


@pytest.mark.parametrize("failure", ["deleted", "changed", "undecodable"])
def test_invalid_selected_image_blocks_every_entry_without_erasing_review(context, failure):
    service, item = context.library, target(context)
    service.select_content(item, user_confirmed=True)
    service.set_enabled(item, True, user_confirmed=True)
    record(service, [item])
    original_events = service.review_events(item)
    path = context.snapshot_assets.root / DIGEST
    displayed = next(row for row in service.browse(for_display=True)
                     if row["target"].exercise == BRIDGE)
    assert displayed["eligibility"].eligible
    if failure == "deleted":
        path.unlink()
    else:
        path.write_bytes(png_bytes(90) if failure == "changed" else b"undecodable")
    displayed = next(row for row in service.browse(for_display=True)
                     if row["target"].exercise == BRIDGE)
    assert not displayed["eligibility"].eligible
    assert not service.eligibility(item).eligible
    assert not service.eligibility(item).reviewed
    for operation in (
        lambda: service.select_content(item, user_confirmed=True),
        lambda: service.set_enabled(item, True, user_confirmed=True),
        lambda: service.require_for_activation([item]),
        lambda: service.require_for_new_session([item]),
        lambda: record(service, [item]),
    ):
        with pytest.raises(CatalogError, match="not eligible"):
            operation()
    assert service.review_events(item) == original_events
    assert service.get(BRIDGE)["enabled"]
    path.write_bytes(PNG)
    assert service.eligibility(item).reviewed
    assert service.review_events(item) == original_events


@pytest.mark.parametrize("path", ["https://example.test/image.png", "other/image.png"])
def test_escaping_or_remote_image_declaration_never_qualifies(context, path):
    entry = deepcopy(context.catalog.get(BRIDGE.key))
    entry["content"]["guidance"]["images"][0]["path"] = path
    entry["reference"]["sha256"] = content_sha256(entry["content"])
    entry["reference"]["id"] += ".invalid"
    with transaction(context.database.connection):
        identifier = context.user_library.retain(
            entry, "override", {}, {path: (DIGEST, len(PNG))}, "synthetic",
        )
    context.snapshot_assets.publish(PNG, DIGEST)
    item = local_target(context, identifier)
    assert not context.library.eligibility(item).eligible
    with pytest.raises(CatalogError):
        context.library.select_content(item, user_confirmed=True)


def test_missing_and_optional_images_are_distinct(context):
    service, item = context.library, target(context)
    content = deepcopy(service.target_entry(item)["content"])
    content["guidance"]["images"].append({"path": None, "sha256": None, "status": "missing",
                                          "caption": "【合成】可选", "required": False})
    identifier = service.save_override(BRIDGE, content, item.content)
    optional = local_target(context, identifier)
    assert service.eligibility(optional).eligible
    record(service, [optional])
    assert service.eligibility(optional).reviewed
    assert service.eligibility(optional).image_checks[1].reason == "missing"
    content["guidance"]["images"][1]["required"] = True
    identifier = service.save_override(BRIDGE, content, optional.content)
    missing = local_target(context, identifier)
    assert not service.eligibility(missing).eligible
    assert not service.eligibility(missing).reviewed
    with pytest.raises(CatalogError):
        service.select_contents([item, missing], user_confirmed=True)


def test_review_binding_edit_withdraw_and_original_answer_survive(context, tmp_path):
    service, item = context.library, target(context)
    answer = tmp_path / "answer.txt"
    answer.write_bytes(b"synthetic answer\r\n verbatim ")
    record(service, [item], answer_file=answer)
    assert service.eligibility(item).reviewed
    assert not service.get(BRIDGE)["enabled"] and service.get(BRIDGE)["selected"] is None
    first = service.review_events(item)[0]
    assert first["reviewed_at"] == "2026-09-17"
    assert first["note"] == "  【合成】原文\t\r\n保留  "
    assert first["image_hashes"] == [{"index": 0, "sha256": DIGEST}]
    stored_answer = context.data_root.path / first["attachment"]["path"]
    assert stored_answer.read_bytes() == answer.read_bytes()
    service.select_content(item, user_confirmed=True)
    service.set_enabled(item, True, user_confirmed=True)
    content = deepcopy(service.target_entry(item)["content"])
    content["guidance"]["purpose"] = "【合成】改版"
    identifier = service.save_override(BRIDGE, content, item.content)
    edited = local_target(context, identifier)
    assert not service.eligibility(edited).reviewed
    assert service.get(BRIDGE)["selected"]["reference"] == item.content
    with pytest.raises(CatalogError, match="changed"):
        service.withdraw_review(item, first["id"] + 1, note="", user_confirmed=True)
    service.withdraw_review(item, first["id"], note="【合成】撤销", user_confirmed=True)
    assert service.review_events(item)[0] == first
    assert not service.eligibility(item).reviewed
    assert service.get(BRIDGE)["enabled"]
    assert stored_answer.exists()
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with transaction(context.database.connection):
            context.database.connection.execute("DELETE FROM library_review_event")


def test_batch_failure_rolls_back_reviews_selection_and_attachment(context, tmp_path, monkeypatch):
    service = context.library
    first, second = target(context), target(context, CLAM)
    answer = tmp_path / "answer.txt"
    answer.write_text("【合成】回答", encoding="utf-8")
    append = context.user_library.append_review
    calls = 0

    def fail_second(identifier, event):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected second review failure")
        return append(identifier, event)

    monkeypatch.setattr(context.user_library, "append_review", fail_second)
    with pytest.raises(RuntimeError, match="injected"):
        record(service, [first, second], answer_file=answer)
    assert context.user_library.references() == []
    assert not list((context.data_root.path / "reviews").glob("*"))
    assert not list(context.snapshot_assets.root.glob("*"))
    monkeypatch.setattr(context.user_library, "append_review", append)
    service.select_contents([first, second], user_confirmed=True)
    stale = LibraryTarget(CLAM, {**second.content, "version": 999})
    with pytest.raises(CatalogError, match="changed"):
        service.set_enabled_batch([first, stale], True, user_confirmed=True)
    assert not service.get(BRIDGE)["enabled"]
    record(service, [first, second], answer_file=answer)
    assert service.eligibility(first).reviewed and service.eligibility(second).reviewed


def test_image_replacement_copy_and_membership_do_not_inherit_review(context, tmp_path):
    service, item = context.library, target(context)
    record(service, [item])
    image = tmp_path / "new.png"
    image.write_bytes(png_bytes(200))
    identifier = service.attach_illustration(item, image, "【合成】新图片")
    changed = local_target(context, identifier)
    assert service.eligibility(changed).eligible and not service.eligibility(changed).reviewed
    copied_id = service.copy_to_custom(BRIDGE, item.content, "【合成】自定义副本")
    copied = local_target(context, copied_id)
    assert not service.eligibility(copied).reviewed
    assert not service.get(copied.exercise)["enabled"]
    content = deepcopy(service.target_entry(copied)["content"])
    content["classification"]["variant_role"] = "variant"
    content["classification"]["parent_exercise_key"] = {
        "source": copied.exercise.source.value, "key": copied.exercise.key,
    }
    with pytest.raises(ValueError, match="own parent"):
        service.save_override(copied.exercise, content, copied.content)
    content["classification"]["parent_exercise_key"] = {"source": "bundled", "key": CLAM.key}
    with pytest.raises(CatalogError, match="same family"):
        service.save_override(copied.exercise, content, copied.content)
    content["classification"]["parent_exercise_key"] = None
    content["classification"]["family_key"] = "family.unknown"
    with pytest.raises(CatalogError, match="Unknown exercise family"):
        service.save_override(copied.exercise, content, copied.content)
    with pytest.raises(CatalogError, match="name or alias"):
        service.copy_to_custom(BRIDGE, item.content, "蚌式开合")


def test_ui_browses_families_filters_variants_and_keeps_stop_text(qt_app, context):
    page = context.create_library_page()
    page.resize(1100, 740)
    page.show()
    qt_app.processEvents()
    assert page.cards.count() == 36
    assert not page.cards.item(0).icon().isNull()
    assert page.stack.currentIndex() == 0
    page.batch_toggle.setChecked(True)
    page.cards.item(0).setSelected(True)
    page.cards.item(1).setSelected(True)
    assert page.batch_review_button.isEnabled()
    assert page.batch_removal_button.isEnabled()
    page.cards.itemClicked.emit(page.cards.item(0))
    assert page.stack.currentIndex() == 0
    page.batch_toggle.setChecked(False)
    assert not page.batch_review_button.isEnabled()
    page.position.setCurrentIndex(page.position.findData("prone"))
    assert page.cards.count() == 3
    page.search.setText("俯卧屈腿")
    assert page.cards.count() == 1
    page.cards.itemClicked.emit(page.cards.item(0))
    assert page.stack.currentIndex() == 1
    assert "停止条件" in page.guidance.toPlainText()
    assert page.images_layout.count() >= 1
    preview = page.images_layout.itemAt(0).widget()
    assert isinstance(preview, IllustrationLabel)
    assert preview.source.width() == 2
    assert preview.pixmap().width() == 2
    page.position.setCurrentIndex(0)
    assert page.stack.currentIndex() == 0
    page.search.setText("基础臀桥")
    page.cards.itemClicked.emit(page.cards.item(0))
    assert page.target.exercise.key == "launch.glute-bridge"
    page.search.setText("蛙式臀桥")
    page.cards.itemClicked.emit(page.cards.item(0))
    assert page.target.exercise.key == "launch.butterfly-glute-bridge"
    page.search.setText("not found")
    assert page.cards.count() == 0
    assert page.target is None
    assert not page.actions["select"].isEnabled()
    page.close()


def test_ui_displays_latest_content_without_version_picker(qt_app, context):
    service, item = context.library, target(context)
    content = deepcopy(service.target_entry(item)["content"])
    content["guidance"]["purpose"] = "【合成】最新版本目的"
    service.save_override(BRIDGE, content, item.content)
    page = context.create_library_page()
    assert not hasattr(page, "versions")
    page.search.setText("基础臀桥")
    page.cards.itemClicked.emit(page.cards.item(0))
    assert page.target.content != item.content
    assert "【合成】最新版本目的" in page.guidance.toPlainText()
    assert "尚未投入使用" in page.status.text()
    page.close()


def test_ui_editor_cancel_and_verbatim_save_do_not_change_selection(qt_app, context):
    service, item = context.library, target(context)
    content = deepcopy(service.target_entry(item)["content"])
    content["guidance"]["purpose"] = "【合成】  多行\r\n\t原文  "
    original_id = service.save_override(BRIDGE, content, item.content)
    original = local_target(context, original_id)
    service.select_content(original, user_confirmed=True)
    before = service.get(BRIDGE)
    editor = CatalogEditor(service, original)
    editor.reject()
    assert service.get(BRIDGE) == before
    editor = CatalogEditor(service, original)
    editor._save()
    assert editor.result() == QDialog.DialogCode.Accepted
    saved = context.user_library.content(editor.saved_id)
    assert saved["content"]["guidance"]["purpose"] == content["guidance"]["purpose"]
    assert service.get(BRIDGE)["selected"]["reference"] == original.content


def test_stale_selected_version_does_not_enable_another_version(context):
    service, item = context.library, target(context)
    service.select_content(item, user_confirmed=True)
    content = deepcopy(service.target_entry(item)["content"])
    content["guidance"]["purpose"] = "【合成】新的当前版本"
    new = local_target(context, service.save_override(BRIDGE, content, item.content))
    service.select_content(new, user_confirmed=True)
    with pytest.raises(CatalogError, match="selected content changed"):
        service.set_enabled(item, True, user_confirmed=True)
    assert not service.get(BRIDGE)["enabled"]


def test_optional_corruption_is_visible_and_invalidates_review_only(context):
    service, item = context.library, target(context)
    optional_bytes = png_bytes(150)
    optional_hash = hashlib.sha256(optional_bytes).hexdigest()
    optional_path = context.data_root.path / "custom-exercise-images/optional.png"
    optional_path.write_bytes(optional_bytes)
    content = deepcopy(service.target_entry(item)["content"])
    content["guidance"]["images"].append({"path": "custom-exercise-images/optional.png",
        "sha256": optional_hash, "status": "available", "required": False,
        "caption": "【合成】可选图"})
    local = local_target(context, service.save_override(BRIDGE, content, item.content))
    record(service, [local])
    (context.snapshot_assets.root / optional_hash).unlink()
    status = service.eligibility(local)
    assert status.eligible and not status.reviewed
    assert status.image_checks[1].reason == "unavailable"
    service.select_content(local, user_confirmed=True)


def test_text_incomplete_and_placeholder_images_remain_drafts(context):
    item, service = target(context), context.library
    content = deepcopy(service.target_entry(item)["content"])
    content["guidance"]["purpose"] = ""
    identifier = service.save_override(BRIDGE, content, item.content)
    incomplete = local_target(context, identifier)
    assert "incomplete_text" in service.eligibility(incomplete).reasons
    content["guidance"]["purpose"] = "【合成】完整目的"
    content["guidance"]["images"][0]["placeholder"] = True
    identifier = service.save_override(BRIDGE, content, item.content)
    placeholder = local_target(context, identifier)
    assert service.eligibility(placeholder).image_checks[0].reason == "placeholder"
    for draft in (incomplete, placeholder):
        with pytest.raises(CatalogError, match="not eligible"):
            service.select_content(draft, user_confirmed=True)


def test_family_cycles_rejected_without_overwriting_existing_versions(context):
    service, item = context.library, target(context)
    a = local_target(context, service.copy_to_custom(BRIDGE, item.content, "【合成】变式甲"))
    b = local_target(context, service.copy_to_custom(BRIDGE, item.content, "【合成】变式乙"))
    first = deepcopy(service.target_entry(a)["content"])
    first["classification"].update(variant_role="variant", parent_exercise_key={
        "source": b.exercise.source.value, "key": b.exercise.key,
    })
    a2 = local_target(context, service.save_override(a.exercise, first, a.content))
    second = deepcopy(service.target_entry(b)["content"])
    second["classification"].update(variant_role="variant", parent_exercise_key={
        "source": a.exercise.source.value, "key": a.exercise.key,
    })
    with pytest.raises(CatalogError, match="cycle"):
        service.save_override(b.exercise, second, b.content)
    assert service.target_entry(a2)["content"] == first
    assert len(service.get(b.exercise)["local_contents"]) == 1


def test_large_draft_library_keeps_valid_display_checks_without_stale_bytes(context, monkeypatch):
    from training_feedback.data import library_images

    service = context.library
    content = deepcopy(service.target_entry(target(context))["content"])
    content["guidance"]["images"] = []
    content["aliases"] = []
    content["classification"]["parent_exercise_key"] = None
    for number in range(100):
        content["canonical_name"] = f"【合成】无图草稿 {number}"
        service.create_custom(content)
    service.browse(latest=True, for_display=True)
    decode = library_images.decode_image_size
    calls = []

    def counted(data):
        calls.append(1)
        return decode(data)

    monkeypatch.setattr(library_images, "decode_image_size", counted)
    rows = service.browse(latest=True, for_display=True)
    assert len(rows) == 136
    assert not calls
    (context.catalog.directory / "images/synthetic.png").write_bytes(b"changed")
    assert not service.display_eligibility(target(context)).eligible


def test_save_rechecks_names_after_another_writer_changes_the_library(context, monkeypatch):
    service, item = context.library, target(context)
    content = deepcopy(service.target_entry(item)["content"])
    content["canonical_name"] = "【合成】并发占用名称"
    content["aliases"] = []
    retain = service._retain

    def race(*args):
        with LibraryContext.reopen(
            context.data_root.path, catalog_path=context.catalog.directory,
        ) as other:
            competing = deepcopy(content)
            competing["guidance"]["images"] = []
            other.library.create_custom(competing)
        return retain(*args)

    monkeypatch.setattr(service, "_retain", race)
    with pytest.raises(CatalogError, match="name or alias"):
        service.save_override(BRIDGE, content, item.content)
    assert not service.get(BRIDGE)["local_contents"]


def test_batch_selection_revalidates_and_rolls_back_earlier_target(context):
    service = context.library
    good, other = target(context), target(context, CLAM)
    content = deepcopy(service.target_entry(other)["content"])
    content["guidance"]["images"] = [{"path": None, "sha256": None, "required": True,
                                      "status": "missing", "caption": "【合成】缺图"}]
    bad = local_target(context, service.save_override(CLAM, content, other.content))
    with pytest.raises(CatalogError, match="not eligible"):
        service.select_contents([good, bad], user_confirmed=True)
    assert service.get(BRIDGE)["selected"] is None
    assert service.get(CLAM)["selected"] is None
    assert service.get(BRIDGE)["local_contents"] == []


def test_review_evidence_survives_backup_and_reopen(context, tmp_path):
    from training_feedback.data.backup import create_backup

    item = target(context)
    record(context.library, [item])
    events = context.library.review_events(item)
    context.library.select_content(item, user_confirmed=True)
    context.library.set_enabled(item, True, user_confirmed=True)
    backup = create_backup(context.data_root.path, tmp_path / "copy", context.database.connection)
    with LibraryContext.reopen(backup, catalog_path=context.catalog.directory) as reopened:
        assert reopened.library.review_events(item) == events
        assert reopened.library.eligibility(item).reviewed
        assert reopened.library.require_for_new_session([item]) == ()
