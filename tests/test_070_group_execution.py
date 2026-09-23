"""070-E uses synthetic catalogs and temporary roots only, never personal training data."""

import json
import sqlite3
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from test_070_group_plans import DIGEST, PNG, ROOT, activate, context, enable, payload

from training_feedback.app import LibraryContext
from training_feedback.data.backup import create_backup
from training_feedback.data.catalog_builder import build_catalog
from training_feedback.data.database import transaction
from training_feedback.domain.group_execution import expand_day

# Imported fixtures are deliberately shared with D's isolated synthetic catalog.
__all__ = ["context", "payload"]


class Clock:
    value = datetime(2026, 9, 19, 23, 45, tzinfo=timezone(timedelta(hours=8)))

    def now(self):
        return self.value

    def today(self):
        return self.value.date()


@pytest.fixture
def controller(context, payload):
    context.sessions.clock = Clock()
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    controller = context.session_controller()
    preview = context.sessions.preview_start(revision, 1)
    controller.start(revision, 1, expected_preview=preview["token"], user_confirmed=True)
    return controller


def dose(row, value, unit="reps", note=""):
    return {"value": value, "unit": unit, "side": row["side"], "note": note}


@pytest.mark.parametrize("sequence", [
    "member_each_side", "same_side_then_switch", "all_rounds_then_switch",
])
def test_expansion_matches_frozen_contract(payload, sequence):
    day = payload["plan"]["days"][0]
    day["items"][1]["side_sequence"] = sequence
    rows = expand_day(day)
    expected = json.loads((ROOT / "tests/fixtures/070/group-execution-expectations.json")
                          .read_text(encoding="utf-8"))[sequence]
    assert [[row["round_number"], row["item_id"], row["side"], row["rest_after_seconds"]]
            for row in rows[1:]] == expected
    assert [row["position"] for row in rows] == list(range(9))
    assert rows[0]["rest_boundary"] == "action_exit"
    assert rows[-1]["rest_boundary"] == "group_exit"


def test_standalone_unilateral_is_explicit_and_mixed_units_do_not_sum(context, payload):
    action = payload["plan"]["days"][0]["items"][0]
    action.update(first_side="right", rest_between_sides_seconds=4)
    for planned in action["sets"]:
        planned["per_side"] = True
    group = payload["plan"]["days"][0]["items"][1]
    group["members"][1]["sets"][0].update(unit="seconds", value=13)
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    preview = context.sessions.preview_start(revision, 1)
    session = context.sessions.start(revision, 1, expected_preview=preview["token"],
                                     user_confirmed=True)
    rows = session["occurrences"]
    assert [row["side"] for row in rows[:2]] == ["right", "left"]
    assert [row["rest_after_seconds"] for row in rows[:2]] == [4, 15]
    assert rows[2]["action"]["sets"][0]["unit"] == "reps"
    assert rows[3]["action"]["sets"][0]["unit"] == "seconds"


def test_start_freezes_everything_and_requires_fresh_disclosure(context, payload):
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    preview = context.sessions.preview_start(revision, 1)
    assert preview["unreviewed"] == ["臀桥", "直腿后踢", "消防栓"]
    target = context.plans._targets(payload)[0]
    context.library.record_review([target], reviewer_type="external_ai_expert", source="合成",
                                  occurred_at="2026-09-19", note="", user_confirmed=True)
    with pytest.raises(ValueError, match="preview changed"):
        context.sessions.start(revision, 1, expected_preview=preview["token"], user_confirmed=True)
    assert context.sessions.active() is None
    preview = context.sessions.preview_start(revision, 1)
    with pytest.raises(ValueError, match="confirmation"):
        context.sessions.start(revision, 1, expected_preview=preview["token"], user_confirmed=False)
    session = context.sessions.start(revision, 1, expected_preview=preview["token"],
                                     user_confirmed=True)
    row = session["occurrences"][0]
    assert row["activation_review"]["reviewed"] is False
    assert row["start_review"]["eligibility"]["reviewed"] is True
    assert row["result"] is None and row["note"] is None and row["actual_sets"] == []
    with pytest.raises(ValueError, match="unfinished"):
        context.sessions.preview_start(revision, 1)


@pytest.mark.parametrize("result", ["completed", "partial", "exceeded", "not_completed"])
def test_individual_outcomes_preserve_zero_unknown_and_verbatim(controller, result):
    controller.navigate(1)
    original = deepcopy(controller.current)
    note = "  用户原文\t\r\n````不作推测  "
    actual = [dose(original, 0)] if result in ("partial", "exceeded") else []
    controller.record(result, actual=actual, note=note)
    row = controller.current
    assert row["note"] == note and row["result"] == result
    assert row["position"] == 1
    assert row["action"] == original["action"] and row["content"] == original["content"]
    if result == "not_completed":
        assert row["actual_sets"] == []
    else:
        assert row["actual_sets"][0]["value"] == (1 if result == "completed" else 0)
        assert row["actual_sets"][0]["side"] == "left"
    assert controller.session["occurrences"][3]["actual_sets"] == []
    with pytest.raises(ValueError, match="already"):
        controller.record("completed")


@pytest.mark.parametrize("actual", [
    [],
    [{"value": True, "unit": "reps", "side": "left", "note": ""}],
    [{"value": float("nan"), "unit": "reps", "side": "left", "note": ""}],
    [{"value": 2, "unit": "reps", "side": "right", "note": ""}],
    [{"value": None, "unit": "free", "side": "left", "note": " "}],
])
def test_bad_actual_doses_never_write(controller, actual):
    controller.navigate(1)
    before = deepcopy(controller.session)
    with pytest.raises(ValueError):
        controller.record("partial", actual=actual)
    assert controller.service.get(before["id"]) == before


def test_free_actual_with_original_explanation_is_not_fabricated_numeric(controller):
    controller.navigate(1)
    controller.record("partial", actual=[dose(controller.current, None, "free", "  自由说明  ")])
    saved = controller.current["actual_sets"][0]
    assert saved["value"] is None and saved["note"] == "  自由说明  "


def test_batch_targets_both_sides_unrecorded_members_and_retracts_only_its_facts(controller):
    controller.navigate(1)
    controller.record("partial", actual=[dose(controller.current, 0)], note="  例外  ")
    exception = deepcopy(controller.current)
    preview = controller.preview_round()
    assert [row["position"] for row in preview["members"]] == [2, 3, 4]
    controller.complete_round(preview, user_confirmed=True)
    assert controller.session["occurrences"][1] == exception
    assert all(row["result"] is None for row in controller.session["occurrences"][5:])
    with pytest.raises(ValueError):
        controller.complete_round(preview, user_confirmed=True)
    controller.navigate(2)
    batch = controller.current["batch_id"]
    before = deepcopy(controller.session)
    controller.retract(user_confirmed=True)
    assert controller.session["occurrences"][1] == exception
    assert all(row["result"] is None for row in controller.session["occurrences"][2:])
    audit = controller.session["events"][-1]
    assert audit["kind"] == "result_retracted" and audit["facts"]["batch_id"] == batch
    assert audit["facts"]["before"] == before["occurrences"][2:5]
    with pytest.raises(ValueError, match="already retracted"):
        controller.service.retract(controller.session["id"], batch_id=batch,
                                    expected_version=controller.session["version"],
                                    user_confirmed=True)


def test_all_rounds_batch_cannot_complete_other_side(context, payload):
    payload["plan"]["days"][0]["items"][1]["side_sequence"] = "all_rounds_then_switch"
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    controller = context.session_controller()
    start = context.sessions.preview_start(revision, 1)
    controller.start(revision, 1, expected_preview=start["token"], user_confirmed=True)
    controller.navigate(1)
    preview = controller.preview_round()
    assert [row["position"] for row in preview["members"]] == [1, 2]
    controller.complete_round(preview, user_confirmed=True)
    assert all(row["result"] is None for row in controller.session["occurrences"][3:])


def test_stale_navigation_and_second_writer_reject_round_and_results(context, controller):
    controller.navigate(1)
    preview = controller.preview_round()
    with LibraryContext.reopen(
        context.data_root.path, catalog_path=context.catalog.directory
    ) as other:
        writer = other.session_controller()
        writer.resume()
        writer.navigate(2)
        writer.record("not_completed")
    with pytest.raises(ValueError, match="preview changed"):
        controller.complete_round(preview, user_confirmed=True)
    with pytest.raises(ValueError, match="session changed"):
        controller.record("completed")
    controller.reload()
    assert controller.current["position"] == 2 and controller.current["result"] == "not_completed"


def test_batch_failure_rolls_back_results_membership_and_version(controller, monkeypatch):
    controller.navigate(1)
    before = deepcopy(controller.session)
    original = controller.service.repository.record
    calls = 0

    def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected second result failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(controller.service.repository, "record", fail)
    with pytest.raises(RuntimeError):
        controller.complete_round(controller.preview_round(), user_confirmed=True)
    assert controller.service.get(before["id"]) == before


def test_pause_restart_keeps_position_and_frozen_work_after_catalog_replacement(
    controller, context, tmp_path
):
    controller.navigate(1)
    controller.record("completed")
    controller.navigate(3)
    controller.pause()
    frozen = deepcopy(controller.session)
    replacement = build_catalog(tmp_path / "empty-catalog", entries=[], version="gone")
    with LibraryContext.reopen(context.data_root.path, catalog_path=replacement) as other:
        other.sessions.clock = Clock()
        other.sessions.clock.value += timedelta(days=1, hours=-22)
        resumed = other.session_controller()
        resumed.resume()
        assert resumed.session["training_date"] == frozen["training_date"]
        assert resumed.current["position"] == 3 and resumed.current["result"] is None
        assert resumed.session["occurrences"] == frozen["occurrences"]
        assert not other.sessions.previous_day(resumed.session)  # 01:45
        other.sessions.clock.value += timedelta(minutes=15)
        assert other.sessions.previous_day(resumed.session)
        resumed.record("partial", actual=[dose(resumed.current, 1)])
        resumed.abort("urgent_interruption", "  原因原文  ", user_confirmed=True)
        assert resumed.session["abort_note"] == "  原因原文  "
        assert resumed.session["occurrences"][2]["result"] is None


def test_finish_requires_all_results_and_terminal_results_are_immutable(context, controller):
    with pytest.raises(ValueError, match="Every occurrence"):
        controller.finish(user_confirmed=True)
    while controller.unfinished:
        controller.navigate(controller.unfinished[0]["position"])
        controller.record("completed")
    controller.finish(user_confirmed=True)
    assert controller.session["status"] == "completed"
    for command in (lambda: controller.record("completed"), controller.pause,
                    lambda: controller.retract(user_confirmed=True), controller.resume):
        with pytest.raises(ValueError):
            command()
    for query in (
        "UPDATE group_session SET position=0", "DELETE FROM group_occurrence_result",
        "UPDATE group_actual_set SET value=999", "DELETE FROM group_session_occurrence",
    ):
        with pytest.raises(sqlite3.IntegrityError):
            with transaction(context.database.connection):
                context.database.connection.execute(query)


def test_feedback_uses_performed_snapshots_and_preserves_unanswered(controller):
    controller.navigate(1)
    controller.record("partial", actual=[dose(controller.current, 0)], note="  原始备注  ")
    controller.navigate(2)
    controller.record("not_completed")
    controller.abort("insufficient_time", "", user_confirmed=True)
    areas = controller.service.feedback_areas(controller.session)
    assert areas == ("臀部",)
    with pytest.raises(ValueError, match="eligible"):
        controller.service.submit_feedback(controller.session["id"], {"臀部": None}, "")
    controller.service.clock.value += timedelta(days=1)
    feedback = controller.service.submit_feedback(controller.session["id"], {"臀部": None},
                                                   "  总体\t\r\n原文  ")
    assert feedback["areas"] == [{"name": "臀部", "value": None}]
    identifier = controller.session["id"]
    corrected = controller.service.correct_note(identifier, "overall_note", "  修正  ",
                                                expected_value=feedback["overall_note"])
    assert corrected["feedback"]["overall_note"] == "  修正  "
    assert corrected["events"][-1]["facts"]["old_value"] == "  总体\t\r\n原文  "
    with pytest.raises(ValueError, match="changed"):
        controller.service.correct_note(identifier, "overall_note", "overwrite",
                                         expected_value=feedback["overall_note"])


def test_export_after_catalog_replacement_is_portable_and_lossless(
    controller, context, tmp_path, payload
):
    controller.navigate(1)
    controller.complete_round(controller.preview_round(), user_confirmed=True)
    controller.retract(user_confirmed=True)
    controller.record("partial", actual=[dose(controller.current, 0)], note="  ````原文  ")
    controller.pause()
    replacement = build_catalog(tmp_path / "gone", entries=[], version="replaced")
    with LibraryContext.reopen(context.data_root.path, catalog_path=replacement) as other:
        directory = other.session_handoff.export(controller.session["id"])
        evidence = json.loads((directory / "evidence.json").read_text(encoding="utf-8"))
        assert evidence["provenance"]["scope"] == "training_session"
        assert evidence["session"] == controller.session
        assert evidence["provenance"]["database_schema_version"] == 22
        assert evidence["session"]["snapshot"]["catalog_version"] != "replaced"
        assert len(evidence["assets"]) == 1
        assert (directory / evidence["assets"][0]["path"]).read_bytes() == PNG
        markdown = (directory / "evidence.md").read_text(encoding="utf-8")
        embedded = markdown.split("`````json\n", 1)[1].rsplit("\n`````", 1)[0]
        assert json.loads(embedded) == evidence
        assert "未知（未记录）" in markdown and "实际第 1 组：0.0" in markdown
    returned = deepcopy(payload)
    returned["source"] = {"session_id": controller.session["id"],
                          "export_id": evidence["provenance"]["export_id"]}
    plan_id = controller.session["snapshot"]["revision"]["plan_id"]
    assert context.plans.create(returned, plan_id=plan_id)


def test_start_rechecks_missing_retained_images(context, payload):
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    preview = context.sessions.preview_start(revision, 1)
    path = context.snapshot_assets.root / DIGEST
    path.unlink()
    with pytest.raises(ValueError):
        context.sessions.start(revision, 1, expected_preview=preview["token"], user_confirmed=True)
    assert context.sessions.active() is None


def test_backup_preserves_execution_batches_retractions_and_resume(context, controller, tmp_path):
    controller.navigate(1)
    controller.complete_round(controller.preview_round(), user_confirmed=True)
    controller.retract(user_confirmed=True)
    controller.record("partial", actual=[dose(controller.current, 0)], note="  备份原文  ")
    controller.navigate(4)
    controller.pause()
    destination = create_backup(context.data_root.path, tmp_path / "备份 空格",
                                 context.database.connection)
    replacement = build_catalog(tmp_path / "backup-catalog", entries=[], version="gone")
    with LibraryContext.reopen(destination, catalog_path=replacement) as restored:
        assert restored.sessions.get(controller.session["id"]) == controller.session
        assert restored.snapshot_assets.read(DIGEST) == PNG
        resumed = restored.session_controller()
        resumed.resume()
        assert resumed.current["position"] == 4 and resumed.current["result"] is None
        assert restored.session_handoff.export(resumed.session["id"]).is_dir()


def test_open_session_blocks_root_switch_and_paused_root_stays_isolated(
    context, controller, tmp_path
):
    with LibraryContext.create(tmp_path / "other", catalog_path=context.catalog.directory) as other:
        target = other.data_root.path
    with pytest.raises(ValueError, match="Pause"):
        context.switch(target)
    controller.pause()
    frozen = deepcopy(controller.session)
    catalog_path, source_path = context.catalog.directory, context.data_root.path
    switched = context.switch(target)
    try:
        assert switched.sessions.history() == []
        with LibraryContext.reopen(source_path, catalog_path=catalog_path) as original:
            assert original.sessions.get(frozen["id"]) == frozen
    finally:
        switched.close()


def test_partial_finish_and_individual_retraction_keep_original_before_image(controller):
    controller.record("partial", actual=[dose(controller.current, 1)], note="  改前  ")
    before = deepcopy(controller.current)
    controller.retract(user_confirmed=True)
    assert controller.session["events"][-1]["facts"]["before"] == [before]
    assert controller.current["result"] is None and controller.current["note"] is None
    controller.record("not_completed", note="  改后  ")
    while controller.unfinished:
        controller.navigate(controller.unfinished[0]["position"])
        controller.record("completed")
    controller.finish(user_confirmed=True)
    assert controller.session["status"] == "partial"


def test_retraction_failure_restores_batch_and_audit(controller, monkeypatch):
    controller.navigate(1)
    controller.complete_round(controller.preview_round(), user_confirmed=True)
    before = deepcopy(controller.session)
    original = controller.service.repository.clear_result
    calls = 0

    def fail(identifier):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected retraction failure")
        original(identifier)

    monkeypatch.setattr(controller.service.repository, "clear_result", fail)
    with pytest.raises(RuntimeError):
        controller.retract(user_confirmed=True)
    assert controller.service.get(before["id"]) == before


def test_session_export_failure_cleans_files_and_both_registrations(
    context, controller, monkeypatch
):
    def fail(*args):
        raise OSError("injected export failure")

    monkeypatch.setattr("training_feedback.data.group_plan_handoff.os.replace", fail)
    with pytest.raises(OSError):
        context.session_handoff.export(controller.session["id"])
    assert list((context.data_root.path / "exports").iterdir()) == []
    for table in ("group_plan_export", "group_session_export"):
        count = context.database.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count == 0


def test_disabled_content_blocks_new_start_but_not_resume(context, controller):
    target = context.plans._targets(controller.session["snapshot"]["revision"]["payload"])[0]
    context.library.set_enabled(target, False, user_confirmed=True)
    controller.pause()
    controller.resume()
    controller.record("completed")
    controller.abort("other", "", user_confirmed=True)
    with pytest.raises(ValueError, match="not enabled"):
        context.sessions.preview_start(controller.session["revision_id"], 1)


def test_start_creation_failure_rolls_back_all_occurrences(context, payload, monkeypatch):
    enable(context, payload)
    revision = context.plans.create(payload)
    activate(context, revision)
    preview = context.sessions.preview_start(revision, 1)

    def fail(*args):
        raise RuntimeError("injected creation event failure")

    monkeypatch.setattr(context.sessions.repository, "event", fail)
    with pytest.raises(RuntimeError):
        context.sessions.start(revision, 1, expected_preview=preview["token"], user_confirmed=True)
    assert context.sessions.history() == []
    assert context.database.connection.execute(
        "SELECT COUNT(*) FROM group_session_occurrence"
    ).fetchone()[0] == 0
