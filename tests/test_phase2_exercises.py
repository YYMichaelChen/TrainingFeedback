from copy import deepcopy

import pytest
from PySide6.QtWidgets import QDialog

from tests.guidance_fixtures import complete_guidance as starter_guidance
from training_feedback.app import ApplicationContext
from training_feedback.application.exercise_service import ExerciseService
from training_feedback.data.data_root import create_new
from training_feedback.data.exercise_repositories import ExerciseRepository
from training_feedback.data.locator import Locator
from training_feedback.data.seed.catalog import CATALOG, seed_catalog
from training_feedback.domain.exercises import (
    GuidanceStatus,
    can_activate_guidance,
    fresh_guidance_draft,
    validate_guidance,
)
from training_feedback.ui.exercise_editor import ExerciseEditor


def _reviewed_guidance(name: str, status: GuidanceStatus) -> dict:
    guidance = starter_guidance(name)
    guidance["review"] = {
        "status": status.value,
        "reviewer_type": "external_ai_expert",
        "review_source": "review-1",
        "review_note": "旧版本审核意见",
        "reviewed_at": "2026-09-05T00:00:00+00:00",
        "user_approved_at": "2026-09-05T00:00:00+00:00",
    }
    return guidance


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


def test_metadata_update_rejects_a_canonical_name_that_matches_its_alias(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("臀桥")["id"]

    with pytest.raises(ValueError, match="aliases"):
        service.update_metadata(exercise_id, "常规臀桥", "main", "")

    assert repository.get(exercise_id)["canonical_name"] == "臀桥"
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


def test_fresh_guidance_draft_clears_review_facts_without_mutating_source():
    source = _reviewed_guidance("测试动作", GuidanceStatus.ACTIVE)
    original = deepcopy(source)

    draft = fresh_guidance_draft(source)

    assert source == original
    assert draft["purpose"] == source["purpose"]
    assert draft["review"] == {
        "status": "draft",
        "reviewer_type": None,
        "review_source": None,
        "review_note": "",
        "reviewed_at": None,
        "user_approved_at": None,
    }


def test_create_and_add_guidance_always_store_fresh_drafts(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)

    approved = _reviewed_guidance("用户动作", GuidanceStatus.APPROVED)
    created_id = service.create_exercise(
        "用户动作", "main", "", [("核心", True)], [], approved
    )
    created = repository.get(created_id)
    assert created["guidance"][0]["guidance"]["review"]["status"] == "draft"
    assert created["guidance"][0]["guidance"]["review"]["reviewed_at"] is None

    exercise_id = repository.resolve("臀桥")["id"]
    first = repository.get(exercise_id)["guidance"][0]
    service.review_and_activate_guidance(
        first["id"],
        {
            "reviewer_type": "external_ai_expert",
            "review_source": "review-1",
            "reviewed_at": "2026-09-05T00:00:00+00:00",
            "user_approved_at": "2026-09-05T00:00:00+00:00",
        },
    )
    active_copy = repository.get(exercise_id)["guidance"][0]["guidance"]
    second_id = service.add_guidance_draft(exercise_id, active_copy)

    current = repository.get(exercise_id)
    second = next(row for row in current["guidance"] if row["id"] == second_id)
    assert current["active_guidance_revision_id"] == first["id"]
    assert second["guidance"]["review"]["status"] == "draft"
    assert second["guidance"]["review"]["reviewer_type"] is None
    context.close()


def test_edit_exercise_persists_all_fields_and_preserves_secondary_areas(tmp_path):
    context = ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = service.create_exercise(
        "旧名称",
        "main",
        "旧器材",
        [("旧主要", True), ("保留次要", False)],
        ["旧别名"],
        starter_guidance("旧名称"),
    )
    edited_guidance = _reviewed_guidance("新名称", GuidanceStatus.ACTIVE)
    edited_guidance["purpose"] = "逐字保留的新目的。"

    service.edit_exercise(
        exercise_id,
        "新名称",
        "supporting",
        "弹力带",
        ["新主要"],
        ["新别名"],
        edited_guidance,
    )

    saved = repository.get(exercise_id)
    assert saved["canonical_name"] == "新名称"
    assert saved["category"] == "supporting"
    assert saved["equipment_summary"] == "弹力带"
    assert saved["aliases"] == ["新别名"]
    assert {(area["name"], area["is_primary"]) for area in saved["body_areas"]} == {
        ("新主要", 1),
        ("保留次要", 0),
    }
    assert len(saved["guidance"]) == 2
    assert saved["guidance"][-1]["guidance"]["purpose"] == "逐字保留的新目的。"
    assert saved["guidance"][-1]["guidance"]["review"]["status"] == "draft"
    context.close()


def test_edit_exercise_later_failure_rolls_back_every_field_after_reopen(
    tmp_path, monkeypatch
):
    root = create_new(tmp_path / "data")
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.open(root, locator)
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("椅子深蹲")["id"]
    before = repository.get(exercise_id)

    def fail_guidance_write(*_args, **_kwargs):
        raise ValueError("injected guidance failure")

    monkeypatch.setattr(repository, "add_guidance_revision", fail_guidance_write)
    with pytest.raises(ValueError, match="injected guidance failure"):
        service.edit_exercise(
            exercise_id,
            "事务内新名称",
            "supporting",
            "新器材",
            ["新主要"],
            ["新别名"],
            starter_guidance("事务内新名称"),
        )
    context.close()

    reopened = ApplicationContext.open(root, locator)
    persisted = ExerciseRepository(reopened.database.connection).get(exercise_id)
    for field in (
        "canonical_name",
        "category",
        "equipment_summary",
        "aliases",
        "body_areas",
        "active_guidance_revision_id",
        "guidance",
    ):
        assert persisted[field] == before[field]
    reopened.close()


@pytest.mark.parametrize(
    "aliases",
    (["重复别名", " 重复别名 "], ["常规臀桥"]),
    ids=("duplicates-in-request", "belongs-to-another-exercise"),
)
def test_edit_exercise_duplicate_or_conflicting_aliases_roll_back_metadata(
    tmp_path, aliases
):
    root = create_new(tmp_path / "data")
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.open(root, locator)
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("蚌式开合")["id"]
    before = repository.get(exercise_id)

    with pytest.raises(ValueError, match="alias"):
        service.edit_exercise(
            exercise_id,
            "不应保存的新名称",
            "supporting",
            "不应保存的新器材",
            ["不应保存的新区域"],
            aliases,
            starter_guidance("不应保存的新名称"),
        )
    context.close()

    reopened = ApplicationContext.open(root, locator)
    persisted = ExerciseRepository(reopened.database.connection).get(exercise_id)
    assert persisted["canonical_name"] == before["canonical_name"]
    assert persisted["equipment_summary"] == before["equipment_summary"]
    assert persisted["aliases"] == before["aliases"]
    assert persisted["body_areas"] == before["body_areas"]
    assert persisted["guidance"] == before["guidance"]
    reopened.close()


def test_renamed_seed_exercise_is_not_recreated_on_reopen(tmp_path):
    root = create_new(tmp_path / "data")
    locator = Locator(tmp_path / "locator.json")
    context = ApplicationContext.open(root, locator)
    repository = ExerciseRepository(context.database.connection)
    service = ExerciseService(repository)
    exercise_id = repository.resolve("蚌式开合")["id"]
    original = repository.get(exercise_id)

    service.edit_exercise(
        exercise_id,
        "用户重命名的蚌式",
        original["category"],
        original["equipment_summary"],
        [area["name"] for area in original["body_areas"] if area["is_primary"]],
        original["aliases"],
        original["guidance"][-1]["guidance"],
    )
    context.close()

    reopened = ApplicationContext.open(root, locator)
    reopened_repository = ExerciseRepository(reopened.database.connection)
    assert len(reopened_repository.list(include_inactive=True)) == len(CATALOG)
    assert reopened_repository.get(exercise_id)["canonical_name"] == "用户重命名的蚌式"
    assert reopened_repository.get_by_canonical_name("蚌式开合") is None
    reopened.close()


def test_exercise_editor_saves_primary_areas_through_complete_edit_use_case(qt_app):
    calls = []

    class RecordingService:
        def edit_exercise(self, *args):
            calls.append(args)

    exercise = {
        "id": 7,
        "canonical_name": "测试动作",
        "category": "main",
        "equipment_summary": "旧器材",
        "aliases": ["旧别名"],
        "body_areas": [
            {"name": "主要区域", "is_primary": 1},
            {"name": "次要区域", "is_primary": 0},
        ],
        "active_guidance_revision_id": None,
        "guidance": [
            {
                "id": 17,
                "revision_number": 1,
                "created_at": "2026-09-10T00:00:00+00:00",
                "guidance": starter_guidance("测试动作"),
            }
        ],
    }
    editor = ExerciseEditor(RecordingService(), exercise)
    assert editor.areas_edit.text() == "主要区域"
    editor.name_edit.setText("编辑后动作")
    editor.equipment_edit.setText("新器材")
    editor.aliases_edit.setText("别名一, 别名二")
    editor.areas_edit.setText("区域一, 区域二")

    editor._save()

    assert editor.result() == QDialog.DialogCode.Accepted
    assert calls[0][0:4] == (7, "编辑后动作", "main", "新器材")
    assert calls[0][4] == ["区域一", "区域二"]
    assert calls[0][5] == ["别名一", "别名二"]
    assert calls[0][6]["purpose"] == starter_guidance("测试动作")["purpose"]
    editor.close()
