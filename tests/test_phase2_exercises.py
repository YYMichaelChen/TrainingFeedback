import pytest

from training_feedback.app import ApplicationContext
from training_feedback.application.exercise_service import ExerciseService
from training_feedback.data.data_root import create_new
from training_feedback.data.exercise_repositories import ExerciseRepository
from training_feedback.data.locator import Locator
from training_feedback.data.seed.catalog import CATALOG, seed_catalog, starter_guidance
from training_feedback.domain.exercises import (
    GuidanceStatus,
    can_activate_guidance,
    validate_guidance,
)


def test_seed_catalog_is_complete_and_idempotent(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    assert len(repository.list()) == len(CATALOG) == 14
    assert repository.resolve("常规臀桥")["canonical_name"] == "臀桥"
    squat = repository.get(repository.resolve("椅子深蹲")["id"])
    assert {area["name"] for area in squat["body_areas"] if area["is_primary"]} == {
        "大腿前侧",
        "臀部",
    }
    seed_catalog(context.database.connection)
    assert len(repository.list()) == 14
    context.close()


def test_guidance_validation_allows_draft_but_requires_complete_approval():
    guidance = starter_guidance("测试动作")
    guidance["stop_criteria"] = []
    assert not validate_guidance(guidance).complete
    assert not can_activate_guidance(guidance)
    guidance["stop_criteria"] = ["出现疼痛时停止。"]
    guidance["review"] = {
        "status": GuidanceStatus.APPROVED.value,
        "reviewer_type": "external_ai_expert",
        "review_source": "review-1",
        "reviewed_at": "2026-09-05T00:00:00+00:00",
        "user_approved_at": "2026-09-05T00:00:00+00:00",
    }
    assert can_activate_guidance(guidance)


def test_guidance_review_requires_external_source_and_user_approval(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("臀桥")["id"]
    revision_id = repository.get(exercise_id)["guidance"][0]["id"]
    service.submit_for_review(revision_id)
    with pytest.raises(ValueError):
        service.approve_guidance(revision_id, {"reviewer_type": "external_ai_expert"})
    service.approve_guidance(
        revision_id,
        {
            "reviewer_type": "external_ai_expert",
            "review_source": "review-1",
            "review_note": "Reviewed.",
            "reviewed_at": "2026-09-05T00:00:00+00:00",
            "user_approved_at": "2026-09-05T00:00:00+00:00",
        },
    )
    service.activate_guidance(revision_id)
    assert repository.get(exercise_id)["guidance"][0]["guidance"]["review"]["status"] == "active"
    context.close()


def test_atomic_guidance_review_does_not_leave_intermediate_status(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("臀桥")["id"]
    revision_id = repository.get(exercise_id)["guidance"][0]["id"]
    with pytest.raises(ValueError, match="Reviewer type and source"):
        service.review_and_activate_guidance(
            revision_id,
            {"reviewed_at": "2026-09-07T00:00:00+00:00"},
        )
    guidance = repository.get(exercise_id)["guidance"][0]["guidance"]
    assert guidance.get("review", {}).get("status", "draft") == "draft"
    service.review_and_activate_guidance(
        revision_id,
        {
            "reviewer_type": "external_ai_expert",
            "review_source": "atomic-review",
            "reviewed_at": "2026-09-07T00:00:00+00:00",
            "user_approved_at": "2026-09-07T00:00:00+00:00",
        },
    )
    current = repository.get(exercise_id)
    assert current["active_guidance_revision_id"] == revision_id
    assert current["guidance"][0]["guidance"]["review"]["status"] == "active"
    context.close()


def test_active_guidance_pointer_survives_revision_edit_and_reopen(tmp_path):
    root = create_new(tmp_path / "data")
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.open(root, locator)
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("臀桥")["id"]
    first = repository.get(exercise_id)["guidance"][0]
    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": "review-1",
        "reviewed_at": "2026-09-05T00:00:00+00:00",
        "user_approved_at": "2026-09-05T00:00:00+00:00",
    }
    service.submit_for_review(first["id"])
    service.approve_guidance(first["id"], review)
    service.activate_guidance(first["id"])
    second_guidance = starter_guidance("臀桥")
    second_guidance["purpose"] = "新的目的"
    second = service.add_guidance_draft(exercise_id, second_guidance)
    assert repository.get(exercise_id)["active_guidance_revision_id"] == first["id"]
    assert repository.get(exercise_id)["guidance"][0]["guidance"]["purpose"] != "新的目的"
    service.submit_for_review(second)
    service.approve_guidance(second, review)
    service.activate_guidance(second)
    current = repository.get(exercise_id)
    assert current["active_guidance_revision_id"] == second
    assert current["guidance"][0]["guidance"]["review"]["status"] == "approved"
    context.close()
    reopened = ApplicationContext.open(root, locator)
    persisted = ExerciseRepository(reopened.database.connection).get(exercise_id)
    assert persisted["active_guidance_revision_id"] == second
    assert len(persisted["guidance"]) == 2
    reopened.close()


def test_failed_guidance_activation_rolls_back_pointer_and_status(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("臀桥")["id"]
    revision_id = repository.get(exercise_id)["guidance"][0]["id"]
    with pytest.raises(ValueError):
        service.activate_guidance(revision_id)
    state = repository.get(exercise_id)
    assert state["active_guidance_revision_id"] is None
    assert state["guidance"][0]["guidance"]["review"]["status"] == "draft"
    context.close()


def test_alias_conflicts_are_rejected(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    with pytest.raises(ValueError):
        repository.add_alias(repository.resolve("臀桥")["id"], "臀桥")
    context.close()


def test_catalog_changes_persist_after_reopen(tmp_path):
    root = create_new(tmp_path / "data")
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.open(root, locator)
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("臀桥")["id"]
    service.set_active(exercise_id, False)
    context.close()

    reopened = ApplicationContext.open(root, locator)
    assert ExerciseRepository(reopened.database.connection).get(exercise_id)["active"] == 0
    reopened.close()
