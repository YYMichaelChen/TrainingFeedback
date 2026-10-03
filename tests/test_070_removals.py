"""070-F lifecycle contracts against isolated synthetic catalogs and user roots."""

import sqlite3
from copy import deepcopy

import pytest
from test_070_group_execution import controller
from test_070_group_plans import DIGEST, PNG, activate, clone_plan, context, enable, payload

from training_feedback.app import LibraryContext
from training_feedback.application.library_workflow import LibraryTarget
from training_feedback.data.backup import create_backup
from training_feedback.data.catalog_builder import build_catalog
from training_feedback.data.database import Database, transaction
from training_feedback.domain.catalog import ExerciseReference, content_sha256

__all__ = ["context", "payload", "controller"]


def targets(context, payload):
    return context.plans._targets(payload)


def request(context, selected, operation="remove"):
    preview = context.removals.preview(selected, operation)
    return context.removals.request(
        selected, operation=operation, reason="  【合成】原因\t\r\n保留  ",
        expected_preview=preview["token"], user_confirmed=True,
    )


def decide(context, identifier, kind, **kwargs):
    service = context.removals
    current = service.get(identifier)
    values = {
        "expected_event_id": current["events"][-1]["id"],
        "source": "  用户本人\t  ", "occurred_at": "2026-09-20", "note": "  原文\t\r\n  ",
        "user_confirmed": True,
    }
    if kind not in {"cancelled", "rejected"}:
        values["expected_preview"] = service.preview_request(identifier)["token"]
    return service.transition(identifier, kind, **(values | kwargs))


def remove(context, selected, operation="remove"):
    identifier = request(context, selected, operation)
    decide(context, identifier, "under_review")
    decide(context, identifier, "approved", apply=True)
    return identifier


def replacement(context, path, *, withdrawn=(), missing=(), changed=()):
    entries = []
    for row in context.catalog.list():
        key = row["content"]["exercise"]["key"]
        if key in missing:
            continue
        content = deepcopy(row["content"])
        if key in changed:
            content["guidance"]["purpose"] += "【更新】"
        entries.append({**row["reference"], "version": row["reference"]["version"] +
                        (1 if key in changed else 0), "content": content,
                        "sha256": content_sha256(content), "withdrawn": key in withdrawn})
    return build_catalog(path, entries=entries, assets={"images/synthetic.png": PNG},
                         version="synthetic-replacement")


def test_batch_remove_preserves_all_evidence_and_records_verbatim(context, payload, controller):
    selected = targets(context, payload)
    context.library.record_review([selected[0]], reviewer_type="human_expert", source="合成专家",
                                  occurred_at="2026-09-19", note="审核原文", user_confirmed=True)
    draft = clone_plan(context, controller.session["revision_id"], name="【合成】移除影响副本")
    directory = context.session_handoff.export(controller.session["id"])
    exports = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    frozen = deepcopy(controller.session)
    plan = context.plans.get(controller.session["revision_id"])
    catalog_bytes = (context.catalog.directory / "catalog.sqlite3").read_bytes()
    preview = context.removals.preview(selected)
    impact = preview["impacts"][0]
    assert {row["status"] for row in impact["plans"]} == {"draft", "active"}
    assert any(row["id"] == draft for row in impact["plans"])
    assert impact["sessions"][0]["status"] == "open"
    assert impact["reviews"] and impact["exports"]
    assert preview["impacts"][1]["groups"]
    identifier = remove(context, selected)
    saved = context.removals.get(identifier)
    assert [e["kind"] for e in saved["events"]] == [
        "requested", "under_review", "approved", "applied",
    ]
    assert saved["reason"] == "  【合成】原因\t\r\n保留  "
    assert saved["events"][-1]["source"] == "  用户本人\t  "
    assert saved["events"][-1]["occurred_at"] == "2026-09-20"
    assert saved["events"][-1]["note"] == "  原文\t\r\n  "
    assert context.sessions.get(frozen["id"]) == frozen
    assert context.plans.get(plan["id"]) == plan
    assert context.snapshot_assets.read(DIGEST) == PNG
    assert context.library.review_events(selected[0])[0]["note"] == "审核原文"
    assert (context.catalog.directory / "catalog.sqlite3").read_bytes() == catalog_bytes
    assert {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()} == exports
    for target in selected:
        assert context.library.eligibility(target).removed
        assert not context.user_library.state(target.exercise)["enabled"]
        assert target.exercise.key not in {r["exercise"]["key"]
                                           for r in context.plans.exercise_choices()}
    assert context.plans.get(draft)["status"] == "draft"


def test_explicit_confirmation_stale_event_and_illegal_transitions(context, payload):
    selected = targets(context, payload)[:1]
    preview = context.removals.preview(selected)
    with pytest.raises(ValueError, match="confirmation"):
        context.removals.request(selected, reason="原因", expected_preview=preview["token"],
                                 user_confirmed=False)
    identifier = request(context, selected)
    with pytest.raises(ValueError, match="unfinished"):
        request(context, selected)
    with pytest.raises(ValueError, match="transition"):
        decide(context, identifier, "approved")
    with pytest.raises(ValueError, match="confirmation"):
        decide(context, identifier, "under_review", user_confirmed=False)
    with pytest.raises(ValueError):
        decide(context, identifier, "under_review", source=" ")
    with pytest.raises(ValueError):
        decide(context, identifier, "under_review", occurred_at="")
    before = context.removals.get(identifier)["events"][-1]["id"]
    decide(context, identifier, "under_review")
    with pytest.raises(ValueError, match="request changed"):
        decide(context, identifier, "approved", expected_event_id=before)


@pytest.mark.parametrize("stage", ["request", "application"])
def test_changed_reference_impact_requires_fresh_review(context, payload, stage):
    selected = targets(context, payload)[:1]
    preview = context.removals.preview(selected)
    if stage != "request":
        identifier = request(context, selected)
        decide(context, identifier, "under_review")
        if stage == "application":
            decide(context, identifier, "approved")
    context.plans.create(payload)
    with pytest.raises(ValueError, match="impact changed"):
        if stage == "request":
            context.removals.request(selected, reason="原文", expected_preview=preview["token"],
                                     user_confirmed=True)
        else:
            decide(context, identifier, "approved" if stage == "approval" else "applied")
    assert not context.library.eligibility(selected[0]).removed
    if stage != "request":
        decide(context, identifier, "under_review")
        decide(context, identifier, "approved", apply=True)
        assert context.library.eligibility(selected[0]).removed


@pytest.mark.parametrize("change", ["content", "selection", "catalog"])
def test_content_changes_require_new_request_even_after_refresh(context, payload, tmp_path, change):
    selected = targets(context, payload)[:1]
    identifier = request(context, selected)
    decide(context, identifier, "under_review")
    if change == "catalog":
        directory = replacement(context, tmp_path / "updated", changed=[selected[0].exercise.key])
        with LibraryContext.reopen(context.data_root.path, catalog_path=directory) as newer:
            with pytest.raises(ValueError, match="content changed"):
                newer.removals.preview_request(identifier)
            decide(newer, identifier, "cancelled")
        return
    if change == "content":
        content = deepcopy(context.library.target_entry(selected[0])["content"])
        content["guidance"]["purpose"] += "  新文字  "
        context.library.save_override(selected[0].exercise, content, selected[0].content)
    else:
        context.library.select_content(selected[0], user_confirmed=True)
    with pytest.raises(ValueError, match="content changed"):
        context.removals.preview_request(identifier)
    decide(context, identifier, "cancelled")


def test_batch_application_rolls_back_all_state_events_and_assets(context, payload, monkeypatch):
    selected = targets(context, payload)
    identifier = request(context, selected)
    decide(context, identifier, "under_review")
    before = context.removals.get(identifier)
    original = context.removals.repository.tombstone
    count = 0

    def fail(*args):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("injected second-target failure")
        return original(*args)

    monkeypatch.setattr(context.removals.repository, "tombstone", fail)
    with pytest.raises(OSError):
        decide(context, identifier, "approved", apply=True)
    assert context.removals.get(identifier) == before
    assert context.user_library.asset_hashes() == set()
    assert not list(context.snapshot_assets.root.glob("*"))
    assert all(context.user_library.disposition(t.exercise) is None for t in selected)
    assert context.database.connection.execute(
        "SELECT COUNT(*) FROM library_plan_invalidation"
    ).fetchone()[0] == 0


def test_restore_validates_images_does_not_enable_or_reactivate_plan(context, payload):
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    selected = targets(context, payload)[:1]
    context.library.record_review(selected, reviewer_type="human_expert", source="合成",
                                  occurred_at="2026-09-19", note="旧审核", user_confirmed=True)
    review = context.library.review_events(selected[0])
    remove(context, selected)
    path = context.snapshot_assets.root / DIGEST
    path.write_bytes(b"invalid image")
    with pytest.raises(ValueError, match="Repair"):
        request(context, selected, "restore")
    assert not context.library.eligibility(selected[0]).reviewed
    assert context.library.review_events(selected[0]) == review
    path.write_bytes(PNG)
    identifier = request(context, selected, "restore")
    decide(context, identifier, "under_review")
    decide(context, identifier, "approved")
    path.unlink()
    with pytest.raises(ValueError, match="Repair"):
        decide(context, identifier, "applied")
    path.write_bytes(PNG)
    decide(context, identifier, "applied")
    assert context.library.eligibility(selected[0]).eligible
    assert not context.user_library.state(selected[0].exercise)["enabled"]
    context.library.set_enabled(selected[0], True, user_confirmed=True)
    with pytest.raises(ValueError, match="new plan revision"):
        context.sessions.preview_start(revision, 1)
    renewed = clone_plan(context, revision, name="【合成】恢复后副本")
    activate(context, renewed)
    assert context.sessions.preview_start(renewed, 1)
    assert context.library.review_events(selected[0]) == review


def test_removed_entry_blocked_from_all_new_use_while_frozen_work_finishes(
    context, payload, controller,
):
    selected = targets(context, payload)[:1]
    remove(context, selected)
    for operation in (
        lambda: context.library.select_content(selected[0], user_confirmed=True),
        lambda: context.library.set_enabled(selected[0], True, user_confirmed=True),
        lambda: context.library.require_for_activation(selected),
        lambda: context.library.require_for_new_session(selected),
        lambda: context.plans.create(payload),
    ):
        with pytest.raises(ValueError):
            operation()
    controller.record("completed", note="移除后冻结训练仍可完成")
    controller.pause()
    with LibraryContext.reopen(context.data_root.path,
                               catalog_path=context.catalog.directory) as reopened:
        resumed = reopened.session_controller()
        resumed.resume()
        assert resumed.current["note"] == "移除后冻结训练仍可完成"
        while resumed.unfinished:
            resumed.navigate(resumed.unfinished[0]["position"])
            resumed.record("completed")
        resumed.finish(user_confirmed=True)
        assert resumed.session["status"] == "completed"
        assert reopened.session_handoff.export(resumed.session["id"]).is_dir()
        with pytest.raises(ValueError, match="new plan revision"):
            reopened.sessions.preview_start(resumed.session["revision_id"], 1)


@pytest.mark.parametrize("mode", ["withdrawn", "missing"])
def test_publisher_observation_root_reopen_retains_frozen_history(
    context, payload, controller, tmp_path, mode,
):
    selected = targets(context, payload)[:1]
    controller.pause()
    frozen = deepcopy(controller.session)
    key = selected[0].exercise.key
    directory = replacement(context, tmp_path / "publisher", **{mode: [key]})
    with LibraryContext.reopen(context.data_root.path, catalog_path=directory) as newer:
        events = newer.removals.publisher_events(selected[0].exercise)
        assert events[-1]["disposition"] == mode
        assert "occurred_at" not in events[-1]
        assert newer.library.eligibility(selected[0]).removed
        assert not newer.user_library.state(selected[0].exercise)["enabled"]
        assert newer.sessions.get(frozen["id"]) == frozen
        new_controller = newer.session_controller()
        new_controller.resume()
        new_controller.record("completed")
        new_controller.pause()
        assert newer.session_handoff.export(frozen["id"]).is_dir()
        assert newer.user_library.disposition(selected[0].exercise) is None
    with LibraryContext.reopen(context.data_root.path, catalog_path=directory) as again:
        assert again.removals.publisher_events(selected[0].exercise) == events


def test_publisher_cannot_be_overridden_and_local_removal_survives_catalog_return(
    context, payload, tmp_path,
):
    selected = targets(context, payload)[:1]
    remove(context, selected)
    directory = replacement(context, tmp_path / "withdrawn", withdrawn=[selected[0].exercise.key])
    with LibraryContext.reopen(context.data_root.path, catalog_path=directory) as newer:
        with pytest.raises(ValueError, match="Publisher withdrawal"):
            request(newer, selected, "restore")
    with LibraryContext.reopen(context.data_root.path,
                               catalog_path=context.catalog.directory) as returned:
        assert returned.library.eligibility(selected[0]).removed
        remove(returned, selected, "restore")
        assert returned.library.eligibility(selected[0]).eligible
        assert not returned.user_library.state(selected[0].exercise)["enabled"]


def test_custom_archive_preserves_variants_and_references(context, payload):
    original = targets(context, payload)[0]
    identifier = context.library.copy_to_custom(original.exercise, original.content, "合成自定义")
    entry = context.user_library.content(identifier)
    selected = LibraryTarget(ExerciseReference(**entry["content"]["exercise"]), entry["reference"])
    # Custom resources must be copied through the existing managed override path.
    child_id = context.library.copy_to_custom(selected.exercise, selected.content, "合成依赖变体")
    child_entry = context.user_library.content(child_id)
    child = deepcopy(child_entry["content"])
    child["classification"]["parent_exercise_key"] = entry["content"]["exercise"]
    child["classification"]["variant_role"] = "variant"
    context.library.save_override(ExerciseReference(**child["exercise"]), child,
                                  child_entry["reference"])
    preview = context.removals.preview([selected])
    assert preview["impacts"][0]["variants"][0]["name"] == "合成依赖变体"
    remove(context, [selected])
    child_row = context.library.get(ExerciseReference(**child["exercise"]))
    assert child_row and child_row["local_contents"][-1]["content"] == child
    assert not context.library.removal_state(ExerciseReference(**child["exercise"]))["removed"]
    remove(context, [selected], "restore")
    assert context.user_library.content(identifier) == entry


def test_export_impact_tracks_saved_draft_and_missing_files(context, payload):
    revision = context.plans.create(payload)
    directory = context.plan_handoff.export(revision)
    selected = targets(context, payload)[:1]
    altered = deepcopy(payload)
    altered["plan"]["days"][0]["items"].pop(0)
    altered["plan"]["days"][0]["items"][0]["order"] = 1
    context.plans.save(revision, altered, expected_token=1)
    impact = context.removals.preview(selected)["impacts"][0]
    assert not impact["plans"] and impact["exports"][0]["availability"] == "available"
    (directory / "evidence.json").unlink()
    changed = context.removals.preview(selected)["impacts"][0]
    assert changed["exports"][0]["availability"] == "unknown"


def test_backup_and_other_roots_keep_decisions_isolated(context, payload, tmp_path):
    selected = targets(context, payload)[:1]
    identifier = remove(context, selected)
    copied = create_backup(context.data_root.path, tmp_path / "备份 空格",
                           context.database.connection)
    with LibraryContext.reopen(copied, catalog_path=context.catalog.directory) as restored:
        assert restored.removals.get(identifier) == context.removals.get(identifier)
        assert restored.library.eligibility(selected[0]).removed
    with LibraryContext.create(tmp_path / "other", catalog_path=context.catalog.directory) as other:
        assert other.removals.requests() == []
        assert not other.library.eligibility(selected[0]).removed


def test_schema24_reopen_preserves_rows_and_lifecycle_journal_immutable(tmp_path, context, payload):
    path = tmp_path / "schema24.sqlite3"
    with Database(path) as connection:
        connection.execute("INSERT INTO library_reference VALUES (1,'custom','example','unknown')")
        connection.commit()
    with Database(path) as connection:
        assert tuple(connection.execute("SELECT * FROM library_reference").fetchone()) == (
            1, "custom", "example", "unknown",
        )
        assert connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == 24
    remove(context, targets(context, payload)[:1])
    connection = context.database.connection
    for table in ("library_lifecycle_request", "library_lifecycle_event"):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            with transaction(connection):
                connection.execute(f"DELETE FROM {table}")


def test_missing_image_draft_can_be_removed_without_fabricating_assets(tmp_path):
    with LibraryContext.create(tmp_path / "draft root") as context:
        entry = context.catalog.list()[0]
        selected = LibraryTarget(ExerciseReference(**entry["content"]["exercise"]),
                                 entry["reference"])
        remove(context, [selected])
        assert context.library.eligibility(selected).removed
        assert context.user_library.asset_hashes() == set()
        with pytest.raises(ValueError, match="Repair"):
            request(context, [selected], "restore")


def test_new_session_impact_invalidates_prior_approval(context, payload):
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    selected = targets(context, payload)[:1]
    identifier = request(context, selected)
    decide(context, identifier, "under_review")
    decide(context, identifier, "approved")
    preview = context.sessions.preview_start(revision, 1)
    context.sessions.start(revision, 1, expected_preview=preview["token"], user_confirmed=True)
    with pytest.raises(ValueError, match="impact changed"):
        decide(context, identifier, "applied")
    assert context.removals.get(identifier)["status"] == "approved"
    decide(context, identifier, "under_review")
    decide(context, identifier, "approved", apply=True)


def test_publisher_missing_parent_keeps_retained_relationship_editable(
    context, payload, tmp_path, qt_app,
):
    from training_feedback.ui.catalog_library_page import CatalogEditor

    parent = targets(context, payload)[0]
    copied = context.library.copy_to_custom(parent.exercise, parent.content, "保留关系的变体")
    entry = context.user_library.content(copied)
    content = deepcopy(entry["content"])
    content["classification"].update(
        variant_role="variant",
        parent_exercise_key={"source": "bundled", "key": parent.exercise.key},
    )
    child_id = context.library.save_override(ExerciseReference(**content["exercise"]), content,
                                             entry["reference"])
    child = context.user_library.content(child_id)
    child_target = LibraryTarget(ExerciseReference(**content["exercise"]), child["reference"])
    assert context.user_library.contents(parent.exercise) == []
    directory = replacement(context, tmp_path / "parent-missing", missing=[parent.exercise.key])
    with LibraryContext.reopen(context.data_root.path, catalog_path=directory) as newer:
        assert newer.removals.publisher_events(parent.exercise)[-1]["disposition"] == "missing"
        assert newer.library.get(parent.exercise) is None
        dialog = CatalogEditor(newer.library, child_target)
        assert dialog.parent_combo.currentData() == content["classification"]["parent_exercise_key"]
        changed = deepcopy(content)
        changed["guidance"]["purpose"] += "原文修订"
        saved = newer.library.save_override(child_target.exercise, changed, child_target.content)
        stored = newer.user_library.content(saved)["content"]
        assert stored["classification"] == content["classification"]
