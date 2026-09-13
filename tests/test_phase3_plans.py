import pytest

from tests.guidance_fixtures import complete_guidance as starter_guidance
from training_feedback.app import ApplicationContext
from training_feedback.application.exercise_service import ExerciseService
from training_feedback.data.data_root import create_new
from training_feedback.data.exercise_repositories import ExerciseRepository
from training_feedback.data.locator import Locator
from training_feedback.data.plan_repositories import PlanRepository
from training_feedback.data.seed.plans import seed_initial_proposal
from training_feedback.domain.enums import DoseUnit
from training_feedback.domain.plans import (
    PlanAction,
    PlanDay,
    PlannedSet,
    PlanPhase,
    PlanRevision,
    diff_revisions,
)
from training_feedback.ui.plan_editor import PlanEditor
from training_feedback.ui.plan_revision_diff import render_diff, render_revision


def _approved_exercise(context):
    exercises = ExerciseRepository(context.database.connection)
    service = ExerciseService(exercises)
    exercise = exercises.resolve("臀桥")
    revision = exercises.get(exercise["id"])["guidance"][0]["id"]
    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": "test-review",
        "reviewed_at": "2026-09-05T00:00:00+00:00",
        "user_approved_at": "2026-09-05T00:00:00+00:00",
    }
    service.submit_for_review(revision)
    service.approve_guidance(revision, review)
    service.activate_guidance(revision)
    return exercises, exercise["id"]


def _revision(exercise_id, value=15):
    return PlanRevision(
        "验证计划",
        "验证计划持久化",
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(
                        1,
                        exercise_id,
                        PlanPhase.MAIN,
                        (
                            PlannedSet(1, DoseUnit.REPS, value, note="保留原始说明"),
                            PlannedSet(2, DoseUnit.REPS, value - 2),
                        ),
                        rest_seconds=45,
                        note="动作备注",
                    ),
                ),
            ),
        ),
    )


def test_plan_repository_persists_and_clones_revision(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    exercises, exercise_id = _approved_exercise(context)
    repository = PlanRepository(context.database.connection, exercises)
    plan_id, revision_id = repository.create_plan(_revision(exercise_id))
    draft_id = repository.clone_revision(plan_id, revision_id)
    source = repository.get_revision(plan_id, revision_id)
    clone = repository.get_revision(plan_id, draft_id)
    assert source["status"] == "draft"
    assert clone["status"] == "draft"
    assert clone["name"] == "验证计划"
    assert clone["days"][0]["actions"][0]["sets"][0]["note"] == "保留原始说明"
    context.close()


def test_activation_supersedes_old_revision_and_reopen_preserves_history(tmp_path):
    root = create_new(tmp_path / "data")
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.open(root, locator)
    exercises, exercise_id = _approved_exercise(context)
    repository = PlanRepository(context.database.connection, exercises)
    plan_id, first_id = repository.create_plan(_revision(exercise_id))
    repository.activate_revision(plan_id, first_id)
    second_id = repository.clone_revision(plan_id, first_id)
    repository.activate_revision(plan_id, second_id)
    plan = repository.get_plan(plan_id)
    assert plan["active_revision_id"] == second_id
    assert [revision["status"] for revision in plan["revisions"]] == ["superseded", "active"]
    context.close()
    reopened = ApplicationContext.open(root, locator)
    persisted = PlanRepository(
        reopened.database.connection, ExerciseRepository(reopened.database.connection)
    ).get_plan(plan_id)
    assert len(persisted["revisions"]) == 2
    reopened.close()


def test_unapproved_guidance_blocks_activation_without_partial_state(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    exercises = ExerciseRepository(context.database.connection)
    exercise_id = exercises.resolve("臀桥")["id"]
    repository = PlanRepository(context.database.connection, exercises)
    plan_id, revision_id = repository.create_plan(_revision(exercise_id))
    with pytest.raises(ValueError):
        repository.activate_revision(plan_id, revision_id)
    state = repository.get_plan(plan_id)
    assert state["active_revision_id"] is None
    assert state["revisions"][0]["status"] == "draft"
    context.close()


def test_initial_proposal_is_draft_and_idempotent(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    first = seed_initial_proposal(context.database.connection)
    second = seed_initial_proposal(context.database.connection)
    repository = PlanRepository(context.database.connection)
    plan = repository.get_plan(first)
    assert first == second
    assert plan["active_revision_id"] is None
    assert len(plan["revisions"]) == 1
    assert plan["revisions"][0]["status"] == "draft"
    assert len(plan["revisions"][0]["days"][0]["actions"]) == 11
    context.close()


def test_application_startup_seeds_the_initial_draft_proposal(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    plans = PlanRepository(context.database.connection).list_plans()
    assert [plan["name"] for plan in plans] == ["臀腿与核心基础"]
    assert plans[0]["active_revision_id"] is None
    context.close()


def test_seeded_proposal_activates_after_explicit_guidance_approval(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    exercises = ExerciseRepository(context.database.connection)
    service = ExerciseService(exercises)
    plan_repository = PlanRepository(context.database.connection, exercises)
    plan = plan_repository.get_plan(plan_repository.list_plans()[0]["id"])
    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": "phase-3-proposal-review",
        "reviewed_at": "2026-09-05T00:00:00+00:00",
        "user_approved_at": "2026-09-05T00:00:00+00:00",
    }
    reviewed = set()
    for action in plan["revisions"][0]["days"][0]["actions"]:
        if action["exercise_id"] in reviewed:
            continue
        revision_id = exercises.get(action["exercise_id"])["guidance"][0]["id"]
        service.submit_for_review(revision_id)
        service.approve_guidance(revision_id, review)
        service.activate_guidance(revision_id)
        reviewed.add(action["exercise_id"])
    plan_repository.activate_revision(plan["id"], plan["revisions"][0]["id"])
    assert plan_repository.get_plan(plan["id"])["active_revision_id"] == plan["revisions"][0]["id"]
    context.close()


def test_revision_diff_reports_structured_dose_change():
    before = _revision(7, 15)
    after = _revision(7, 20)
    changes = diff_revisions(before, after)
    assert any(change["category"] == "set_value_changed" for change in changes)
    assert any(change["before"] == 15 and change["after"] == 20 for change in changes)


def test_revision_diff_reports_exercise_replacement_at_the_same_action_order():
    before = _revision(1)
    after = _revision(2)
    assert any(
        change["category"] == "exercise_changed" and change["before"] == 1 and change["after"] == 2
        for change in diff_revisions(before, after)
    )


def test_revision_diff_reports_reordered_unique_actions():
    before = PlanRevision(
        "排序计划",
        "排序",
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(1, 1, PlanPhase.MAIN, (PlannedSet(1, DoseUnit.REPS, 10),)),
                    PlanAction(2, 2, PlanPhase.MAIN, (PlannedSet(1, DoseUnit.REPS, 10),)),
                ),
            ),
        ),
    )
    after = PlanRevision(
        "排序计划",
        "排序",
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(1, 2, PlanPhase.MAIN, (PlannedSet(1, DoseUnit.REPS, 10),)),
                    PlanAction(2, 1, PlanPhase.MAIN, (PlannedSet(1, DoseUnit.REPS, 10),)),
                ),
            ),
        ),
    )
    assert (
        sum(change["category"] == "action_reordered" for change in diff_revisions(before, after))
        == 2
    )


def test_catalog_to_plan_revision_chain_preserves_history(tmp_path):
    """Prove the Phase 3 acceptance workflow across catalog and plan layers."""
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    exercises = ExerciseRepository(context.database.connection)
    service = ExerciseService(exercises)
    incomplete = starter_guidance("验收动作")
    incomplete["stop_criteria"] = []
    exercise_id = service.create_exercise(
        "验收动作", "main", "none", [("臀部", True)], ["验收动作别名"], incomplete
    )
    assert exercises.resolve("验收动作别名")["id"] == exercise_id
    incomplete_revision = exercises.get(exercise_id)["guidance"][0]["id"]
    with pytest.raises(ValueError):
        service.activate_guidance(incomplete_revision)

    approved_guidance = starter_guidance("验收动作")
    guidance_revision = service.add_guidance_draft(exercise_id, approved_guidance)
    service.submit_for_review(guidance_revision)
    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": "phase-3-acceptance",
        "reviewed_at": "2026-09-05T00:00:00+00:00",
        "user_approved_at": "2026-09-05T00:00:00+00:00",
    }
    service.approve_guidance(guidance_revision, review)

    repository = PlanRepository(context.database.connection, exercises)
    original = _revision(exercise_id, 15)
    plan_id, first_draft = repository.create_plan(original)
    with pytest.raises(ValueError):
        repository.activate_revision(plan_id, first_draft)
    assert repository.get_plan(plan_id)["active_revision_id"] is None

    service.activate_guidance(guidance_revision)
    repository.activate_revision(plan_id, first_draft)
    changed_draft = repository.clone_revision(plan_id, first_draft)
    changed = _revision(exercise_id, 20)
    repository.replace_draft_revision(plan_id, changed_draft, changed)
    assert any(
        item["category"] == "set_value_changed" for item in diff_revisions(original, changed)
    )
    repository.activate_revision(plan_id, changed_draft)

    plan = repository.get_plan(plan_id)
    assert [item["status"] for item in plan["revisions"]] == ["superseded", "active"]
    assert plan["active_revision_id"] == changed_draft
    assert plan["revisions"][0]["days"][0]["actions"][0]["sets"][0]["value"] == 15
    assert plan["revisions"][1]["days"][0]["actions"][0]["sets"][0]["value"] == 20
    context.close()


def test_activation_preview_renders_structured_sets_and_first_activation_message(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = PlanRepository(context.database.connection)
    per_side_revision = PlanRevision(
        "预览计划",
        "确认每组剂量",
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(
                        1, 1, PlanPhase.MAIN, (PlannedSet(1, DoseUnit.SECONDS, 30, per_side=True),)
                    ),
                ),
            ),
        ),
    )
    plan_id, revision_id = repository.create_plan(per_side_revision)
    draft = repository.get_revision(plan_id, revision_id)
    assert "30.0 秒 / 每侧" in render_revision(draft)
    assert "当前没有启用的计划版本" in render_diff(None, draft)
    context.close()


def test_plan_editor_preserves_unequal_sets_notes_and_other_actions(qt_app, tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = PlanRepository(context.database.connection)
    plan = repository.get_plan(repository.list_plans()[0]["id"])
    draft = plan["revisions"][0]
    original = draft["days"][0]["actions"][3]["sets"]
    original[1]["note"] = "逐字保留"
    context.database.connection.execute(
        "UPDATE training_plan_set SET note = ? WHERE id = ?",
        (original[1]["note"], original[1]["id"]),
    )
    draft = repository.get_revision(plan["id"], draft["id"])
    editor = PlanEditor(repository, plan, draft)
    editor.action_selector.setCurrentRow(3)
    rebuilt = editor._build_revision()
    selected = rebuilt.days[0].actions[3].sets
    assert [item.value for item in selected] == [12, 12, 10]
    assert selected[1].note == "逐字保留"
    editor.table.item(2, 1).setText("9")
    rebuilt = editor._build_revision()
    assert rebuilt.days[0].actions[3].sets[2].value == 9
    assert rebuilt.days[0].actions[4].sets[0].value == 12
    editor.close()
    context.close()


def test_plan_editor_edits_action_metadata_without_changing_other_actions(qt_app, tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = PlanRepository(context.database.connection)
    plan = repository.get_plan(repository.list_plans()[0]["id"])
    editor = PlanEditor(repository, plan, plan["revisions"][0])
    editor.action_selector.setCurrentRow(3)
    editor.phase.setCurrentIndex(editor.phase.findData("cooldown"))
    editor.rest.setValue(75)
    editor.action_note.setText("保留动作说明")
    rebuilt = editor._build_revision()
    selected = rebuilt.days[0].actions[3]
    untouched = rebuilt.days[0].actions[4]
    assert selected.phase == PlanPhase.COOLDOWN
    assert selected.rest_seconds == 75
    assert selected.note == "保留动作说明"
    assert untouched.phase == PlanPhase.MAIN
    assert untouched.rest_seconds == 45
    assert untouched.note == ""
    editor._save()
    persisted = repository.get_revision(plan["id"], plan["revisions"][0]["id"])
    persisted_action = persisted["days"][0]["actions"][3]
    assert persisted_action["phase"] == "cooldown"
    assert persisted_action["rest_seconds"] == 75
    assert persisted_action["note"] == "保留动作说明"
    editor.close()
    context.close()


def test_plan_editor_uses_controlled_units_and_preserves_individual_sets_on_mode_switch(
    monkeypatch, qt_app, tmp_path
):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = PlanRepository(context.database.connection)
    plan = repository.get_plan(repository.list_plans()[0]["id"])
    editor = PlanEditor(repository, plan, plan["revisions"][0])
    editor.action_selector.setCurrentRow(3)
    assert editor.table.cellWidget(0, 2).currentData() == "reps"
    assert editor.table.cellWidget(0, 2).currentText() == "次"
    assert editor.table.cellWidget(0, 3).isChecked() is False
    for row in range(editor.table.rowCount()):
        editor.table.cellWidget(row, 2).setCurrentIndex(
            editor.table.cellWidget(row, 2).findData("minutes")
        )
        editor.table.item(row, 1).setText("2")
    rebuilt = editor._build_revision()
    assert rebuilt.days[0].actions[3].sets[0].unit == DoseUnit.MINUTES
    assert rebuilt.days[0].actions[3].sets[0].value == 2
    monkeypatch.setattr("training_feedback.ui.plan_editor.confirm", lambda *args: True)
    editor.equal_toggle.setChecked(True)
    editor.equal_toggle.setChecked(False)
    assert [item.value for item in editor._build_revision().days[0].actions[3].sets] == [2, 2, 2]
    editor.close()
    context.close()


def test_activation_rolls_back_if_pointer_update_fails(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    exercises, exercise_id = _approved_exercise(context)
    repository = PlanRepository(context.database.connection, exercises)
    plan_id, first_id = repository.create_plan(_revision(exercise_id))
    repository.activate_revision(plan_id, first_id)
    second_id = repository.clone_revision(plan_id, first_id)
    context.database.connection.execute(
        "CREATE TRIGGER fail_plan_pointer_update BEFORE UPDATE OF active_revision_id "
        "ON training_plan BEGIN SELECT RAISE(ABORT, 'injected pointer failure'); END"
    )
    with pytest.raises(Exception, match="injected pointer failure"):
        repository.activate_revision(plan_id, second_id)
    state = repository.get_plan(plan_id)
    assert state["active_revision_id"] == first_id
    assert [item["status"] for item in state["revisions"]] == ["active", "draft"]
    context.close()


def test_free_and_minutes_doses_persist_with_required_free_note(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = PlanRepository(context.database.connection)
    revision = PlanRevision(
        "单位计划",
        "覆盖分钟和自由单位",
        (
            PlanDay(
                1,
                "训练日",
                (
                    PlanAction(
                        1,
                        1,
                        PlanPhase.MAIN,
                        (PlannedSet(1, DoseUnit.MINUTES, 2),),
                    ),
                    PlanAction(
                        2,
                        2,
                        PlanPhase.MAIN,
                        (PlannedSet(1, DoseUnit.FREE, note="按舒适节奏完成"),),
                    ),
                ),
            ),
        ),
    )
    plan_id, revision_id = repository.create_plan(revision)
    persisted = repository.get_revision(plan_id, revision_id)
    assert persisted["days"][0]["actions"][0]["sets"][0]["unit"] == "minutes"
    free = persisted["days"][0]["actions"][1]["sets"][0]
    assert free["unit"] == "free"
    assert free["value"] is None
    assert free["note"] == "按舒适节奏完成"
    context.close()


def test_draft_replacement_rolls_back_after_child_insert_failure(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = PlanRepository(context.database.connection)
    plan_id, revision_id = repository.create_plan(_revision(1))
    before = repository.get_revision(plan_id, revision_id)
    context.database.connection.execute(
        "CREATE TRIGGER fail_plan_day_insert BEFORE INSERT ON training_plan_day "
        "BEGIN SELECT RAISE(ABORT, 'injected day failure'); END"
    )
    replacement = _revision(1, 25)
    with pytest.raises(Exception, match="injected day failure"):
        repository.replace_draft_revision(plan_id, revision_id, replacement)
    after = repository.get_revision(plan_id, revision_id)
    assert after["purpose"] == before["purpose"]
    assert after["days"][0]["actions"][0]["sets"][0]["value"] == 15
    context.close()
