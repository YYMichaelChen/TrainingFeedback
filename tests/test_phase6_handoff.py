import json
from datetime import datetime, timezone

import pytest

from tests.test_phase4_sessions import FixedClock, _active_plan
from training_feedback.app import ApplicationContext
from training_feedback.data.data_root import create_new
from training_feedback.data.feedback_repositories import FeedbackRepository
from training_feedback.data.handoff import HandoffError, HandoffService
from training_feedback.data.locator import Locator
from training_feedback.data.session_repositories import SessionRepository
from training_feedback.domain.enums import ExerciseResult, FeedbackValue
from training_feedback.domain.session_controller import SessionController
from training_feedback.ui.history_page import HistoryPage
from training_feedback.ui.plan_page import PlanPage
from training_feedback.ui.settings_page import SettingsPage


def _context(tmp_path):
    return ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )


def _import_payload(exercise_name="臀桥", target_plan_name=None):
    plan = {
        "name": "外部调整计划",
        "purpose": "根据训练证据调整剂量",
        "days": [
            {
                "order": 1,
                "name": "调整训练日",
                "actions": [
                    {
                        "order": 1,
                        "exercise_name": exercise_name,
                        "phase": "main",
                        "rest_seconds": 60,
                        "note": "外部专家原始备注",
                        "sets": [
                            {
                                "order": 1,
                                "value": 20,
                                "unit": "reps",
                                "per_side": False,
                                "note": "逐字保留",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    if target_plan_name is not None:
        plan["target_plan_name"] = target_plan_name
    return {
        "schema": "training_feedback.plan",
        "schema_version": 1,
        "rationale": "外部 AI 专家建议增加剂量。",
        "plan": plan,
    }


def test_export_writes_versioned_json_markdown_and_registers_both_files(tmp_path):
    context = _context(tmp_path)
    service = HandoffService(context.database.connection, context.data_root.path)
    json_path, markdown_path = service.export()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "training_feedback.evidence"
    assert payload["schema_version"] == 1
    assert payload["sessions"] == []
    assert payload["catalog"]
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "训练证据" in markdown
    assert "稳定指导，不是用户报告" in markdown
    assert "## 计划版本" in markdown
    records = context.database.connection.execute(
        "SELECT format, file_path FROM ai_export ORDER BY id"
    ).fetchall()
    assert [row[0] for row in records] == ["json", "markdown"]
    assert all(not row[1].startswith("..") for row in records)
    context.close()


def test_export_failure_rolls_back_registry_and_removes_partial_files(tmp_path, monkeypatch):
    context = _context(tmp_path)
    service = HandoffService(context.database.connection, context.data_root.path)

    def fail_markdown(_evidence):
        raise OSError("injected Markdown failure")

    monkeypatch.setattr("training_feedback.data.handoff.render_markdown", fail_markdown)

    with pytest.raises(HandoffError, match="injected Markdown failure"):
        service.export()

    assert context.database.connection.execute("SELECT COUNT(*) FROM ai_export").fetchone()[0] == 0
    assert not list((context.data_root.path / "exports").glob("*"))
    context.close()


def test_selected_session_export_includes_only_it_and_earlier_history(tmp_path):
    context = _context(tmp_path)
    service = HandoffService(context.database.connection, context.data_root.path)
    service.feedback.history = lambda: [{"id": 3}, {"id": 2}, {"id": 1}]

    evidence = service.build_evidence(2)

    assert [session["id"] for session in evidence["sessions"]] == [2, 1]
    assert evidence["provenance"]["scope"] == "session_with_earlier_history"
    context.close()


def test_session_export_preserves_notes_unknowns_events_and_feedback(tmp_path):
    context = _context(tmp_path)
    plans, exercises, plan_id = _active_plan(context)
    clock = FixedClock(datetime(2026, 9, 6, 10, 15, tzinfo=timezone.utc))
    controller = SessionController(
        SessionRepository(context.database.connection), plans, exercises, clock
    )
    session = controller.start(plan_id)
    note = "  动作原始备注\n第二行  "
    controller.record_result(session["actions"][0]["id"], ExerciseResult.COMPLETED, note=note)
    session = controller.finish()
    feedback_note = "  次日原始备注  "
    FeedbackRepository(context.database.connection).submit(
        session["id"],
        {"臀部": FeedbackValue.SOME_SORENESS},
        feedback_note,
        datetime(2026, 9, 7).date(),
        datetime(2026, 9, 7, 9, tzinfo=timezone.utc),
    )

    json_path, markdown_path = HandoffService(
        context.database.connection, context.data_root.path
    ).export(session["id"])

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    exported = payload["sessions"][0]
    assert payload["provenance"]["session_id"] == session["id"]
    assert payload["provenance"]["export_id"] is not None
    assert exported["actions"][0]["note"] == note
    assert exported["actions"][0]["sets"][0]["actual_value"] is None
    assert exported["events"][0]["event_type"] == "completed"
    assert exported["feedback"]["overall_note"] == feedback_note
    assert exported["feedback"]["areas"][0]["value"] == "some_soreness"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert note in markdown
    assert "未知（null）" in markdown
    assert feedback_note in markdown
    context.close()


def test_import_creates_draft_and_provenance_without_activation(tmp_path):
    context = _context(tmp_path)
    source = tmp_path / "external-plan.json"
    source.write_text(json.dumps(_import_payload(), ensure_ascii=False), encoding="utf-8")
    service = HandoffService(context.database.connection, context.data_root.path)

    plan_id, revision_id = service.import_plan_file(source)

    revision = service.plans.get_revision(plan_id, revision_id)
    assert revision["status"] == "draft"
    assert revision["days"][0]["actions"][0]["exercise_name"] == "臀桥"
    assert revision["days"][0]["actions"][0]["sets"][0]["note"] == "逐字保留"
    imported = context.database.connection.execute("SELECT * FROM plan_import").fetchone()
    assert imported["status"] == "draft_created"
    assert imported["plan_id"] == plan_id
    assert imported["revision_id"] == revision_id
    assert imported["rationale"] == "外部 AI 专家建议增加剂量。"
    assert imported["confirmed_at"] is None
    assert list((context.data_root.path / "imports").glob("*.json"))
    context.close()


def test_import_can_target_existing_plan_without_changing_active_revision(tmp_path):
    context = _context(tmp_path)
    existing = context.database.connection.execute(
        "SELECT id FROM training_plan WHERE name = ?", ("臀腿与核心基础",)
    ).fetchone()[0]
    before = context.database.connection.execute(
        "SELECT COUNT(*) FROM training_plan_revision WHERE plan_id = ?", (existing,)
    ).fetchone()[0]
    source = tmp_path / "external-plan.json"
    source.write_text(
        json.dumps(_import_payload(target_plan_name="臀腿与核心基础"), ensure_ascii=False),
        encoding="utf-8",
    )

    plan_id, _revision_id = HandoffService(
        context.database.connection, context.data_root.path
    ).import_plan_file(source)

    assert plan_id == existing
    assert (
        context.database.connection.execute(
            "SELECT COUNT(*) FROM training_plan_revision WHERE plan_id = ?", (existing,)
        ).fetchone()[0]
        == before + 1
    )
    assert (
        context.database.connection.execute(
            "SELECT active_revision_id FROM training_plan WHERE id = ?", (existing,)
        ).fetchone()[0]
        is None
    )
    context.close()


def test_imported_draft_activation_records_confirmation_and_preserves_previous(tmp_path):
    context = _context(tmp_path)
    plans, _exercises, expected_plan_id = _active_plan(context)
    before = plans.get_plan(expected_plan_id)
    previous_revision_id = before["active_revision_id"]
    previous_revision = plans.get_revision(expected_plan_id, previous_revision_id)
    service = HandoffService(context.database.connection, context.data_root.path)
    source = tmp_path / "external-plan.json"
    source.write_text(
        json.dumps(_import_payload(target_plan_name="执行测试计划"), ensure_ascii=False),
        encoding="utf-8",
    )
    plan_id, revision_id = service.import_plan_file(source)

    assert plan_id == expected_plan_id
    assert service.plans.get_plan(plan_id)["active_revision_id"] == previous_revision_id
    service.plans.activate_revision(plan_id, revision_id)

    plan = service.plans.get_plan(plan_id)
    imported = context.database.connection.execute("SELECT * FROM plan_import").fetchone()
    assert plan["active_revision_id"] == revision_id
    assert imported["previous_revision_id"] == previous_revision_id
    assert imported["status"] == "activated"
    assert imported["confirmed_at"] is not None
    preserved = service.plans.get_revision(plan_id, previous_revision_id)
    assert preserved["status"] == "superseded"
    assert preserved["purpose"] == previous_revision["purpose"]
    assert preserved["days"] == previous_revision["days"]
    json_path, markdown_path = service.export()
    evidence = json.loads(json_path.read_text(encoding="utf-8"))
    assert evidence["plan_imports"][0]["previous_revision_id"] == previous_revision_id
    assert "外部 AI 专家建议增加剂量。" in markdown_path.read_text(encoding="utf-8")
    context.close()


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda payload: payload.update(schema_version=99), "schema version"),
        (lambda payload: payload["plan"].pop("purpose"), "name and purpose"),
        (
            lambda payload: payload["plan"]["days"][0]["actions"][0].update(exercise_name="不存在"),
            "Unknown exercise",
        ),
        (
            lambda payload: payload["plan"]["days"][0]["actions"][0].update(phase="invalid"),
            "validation failed",
        ),
    ],
)
def test_invalid_import_writes_nothing(tmp_path, mutate, message):
    context = _context(tmp_path)
    payload = _import_payload()
    mutate(payload)
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    service = HandoffService(context.database.connection, context.data_root.path)
    before = context.database.connection.execute("SELECT COUNT(*) FROM plan_import").fetchone()[0]

    with pytest.raises(HandoffError, match=message):
        service.import_plan_file(source)

    assert (
        context.database.connection.execute("SELECT COUNT(*) FROM plan_import").fetchone()[0]
        == before
    )
    assert not list((context.data_root.path / "imports").glob("*.json"))
    context.close()


def test_import_rolls_back_revision_and_removes_managed_copy_on_write_failure(tmp_path):
    context = _context(tmp_path)
    source = tmp_path / "external-plan.json"
    source.write_text(json.dumps(_import_payload(), ensure_ascii=False), encoding="utf-8")
    context.database.connection.execute(
        "CREATE TRIGGER fail_plan_import BEFORE INSERT ON plan_import "
        "BEGIN SELECT RAISE(ABORT, 'injected import failure'); END"
    )
    service = HandoffService(context.database.connection, context.data_root.path)
    plan_count = context.database.connection.execute(
        "SELECT COUNT(*) FROM training_plan"
    ).fetchone()[0]

    with pytest.raises(HandoffError, match="injected import failure"):
        service.import_plan_file(source)

    assert (
        context.database.connection.execute("SELECT COUNT(*) FROM training_plan").fetchone()[0]
        == plan_count
    )
    assert (
        context.database.connection.execute("SELECT COUNT(*) FROM plan_import").fetchone()[0] == 0
    )
    assert not list((context.data_root.path / "imports").glob("*.json"))
    context.close()


def test_handoff_actions_are_available_from_natural_ui_pages(qt_app, tmp_path):
    context = _context(tmp_path)
    settings = SettingsPage(context)
    history = HistoryPage(context)
    plans = PlanPage(context)

    assert settings.export_button.text() == "导出全部训练证据"
    assert history.export_button.text() == "导出所选训练证据"
    assert plans.import_button.text() == "导入外部计划 JSON"

    settings.close()
    history.close()
    plans.close()
    context.close()
