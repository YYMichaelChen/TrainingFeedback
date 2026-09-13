"""0.5.0：批量审核、受管审核原件、内置动作选择性导入。"""

import json

import pytest

from training_feedback.app import ApplicationContext
from training_feedback.data.data_root import create_new
from training_feedback.data.locator import Locator
from training_feedback.data.review_attachments import (
    REVIEWS_DIRECTORY,
    ReviewAttachmentError,
)
from training_feedback.data.seed.catalog import bundled_catalog
from training_feedback.domain.exercises import GuidanceStatus, review_status


def _context(tmp_path):
    return ApplicationContext.open(
        create_new(tmp_path / "data"), Locator(tmp_path / "locator.json")
    )


def _reviewable(service, name):
    return next(
        item for item in service.list_reviewable_guidance() if item["exercise_name"] == name
    )


def test_batch_approval_applies_one_review_to_every_selected_revision(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    targets = [_reviewable(service, name) for name in ("臀桥", "蚌式开合", "死虫式")]

    approved = service.confirm_guidance_reviews(
        [item["revision_id"] for item in targets],
        review_source="外部 AI 会话 A",
        reviewed_at="2026-09-13",
        review_note="原始答复：reviews/answer.md",
        user_confirmed=True,
    )

    assert approved == 3
    for item in targets:
        exercise = service.get(item["exercise_id"])
        assert exercise["active_guidance_revision_id"] == item["revision_id"]
        active = next(
            revision
            for revision in exercise["guidance"]
            if revision["id"] == item["revision_id"]
        )
        review = active["guidance"]["review"]
        assert review_status(active["guidance"]) is GuidanceStatus.ACTIVE
        assert review["review_source"] == "外部 AI 会话 A"
        assert review["reviewed_at"] == "2026-09-13"
        assert review["review_note"] == "原始答复：reviews/answer.md"
        assert review["user_approved_at"]
    context.close()


def test_batch_approval_requires_explicit_confirmation_and_a_selection(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    target = _reviewable(service, "臀桥")

    with pytest.raises(ValueError):
        service.confirm_guidance_reviews(
            [target["revision_id"]],
            review_source="外部 AI",
            reviewed_at="2026-09-13",
            user_confirmed=False,
        )
    with pytest.raises(ValueError):
        service.confirm_guidance_reviews(
            [], review_source="外部 AI", reviewed_at="2026-09-13", user_confirmed=True
        )
    with pytest.raises(ValueError):
        service.confirm_guidance_reviews(
            [target["revision_id"]],
            review_source="外部 AI",
            reviewed_at="不是日期",
            user_confirmed=True,
        )

    assert service.get(target["exercise_id"])["active_guidance_revision_id"] is None
    context.close()


def test_batch_approval_rolls_back_every_revision_when_one_fails(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    first = _reviewable(service, "臀桥")
    second = _reviewable(service, "蚌式开合")

    with pytest.raises(ValueError):
        service.confirm_guidance_reviews(
            [first["revision_id"], 9999],
            review_source="外部 AI",
            reviewed_at="2026-09-13",
            user_confirmed=True,
        )

    assert service.get(first["exercise_id"])["active_guidance_revision_id"] is None
    assert service.get(second["exercise_id"])["active_guidance_revision_id"] is None
    context.close()


def test_approval_stores_the_review_answer_as_a_managed_file(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    target = _reviewable(service, "臀桥")
    answer = tmp_path / "外部答复 2026-09-13.md"
    answer.write_text("逐项结论：可进入用户复核。", encoding="utf-8")

    service.confirm_guidance_reviews(
        [target["revision_id"]],
        review_source="外部 AI 会话 A",
        reviewed_at="2026-09-13",
        user_confirmed=True,
        answer_file=answer,
    )

    exercise = service.get(target["exercise_id"])
    review = next(
        revision["guidance"]["review"]
        for revision in exercise["guidance"]
        if revision["id"] == target["revision_id"]
    )
    stored = context.data_root.path / review["review_answer_file"]
    assert review["review_answer_file"].startswith(f"{REVIEWS_DIRECTORY}/")
    assert review["review_answer_original_name"] == answer.name
    assert stored.is_file()
    assert stored.read_text(encoding="utf-8") == "逐项结论：可进入用户复核。"
    assert len(review["review_answer_sha256"]) == 64
    # 原件留在数据根内，备份与整根复制才会带着它走。
    assert stored.parent == context.data_root.path / REVIEWS_DIRECTORY
    context.close()


def test_failed_approval_removes_the_copied_review_answer(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    answer = tmp_path / "answer.md"
    answer.write_text("结论", encoding="utf-8")

    with pytest.raises(ValueError):
        service.confirm_guidance_reviews(
            [9999],
            review_source="外部 AI",
            reviewed_at="2026-09-13",
            user_confirmed=True,
            answer_file=answer,
        )

    reviews = context.data_root.path / REVIEWS_DIRECTORY
    assert not reviews.exists() or not any(reviews.iterdir())
    context.close()


def test_missing_review_answer_file_is_reported_before_any_approval(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    target = _reviewable(service, "臀桥")

    with pytest.raises(ReviewAttachmentError):
        service.confirm_guidance_reviews(
            [target["revision_id"]],
            review_source="外部 AI",
            reviewed_at="2026-09-13",
            user_confirmed=True,
            answer_file=tmp_path / "does-not-exist.md",
        )

    assert service.get(target["exercise_id"])["active_guidance_revision_id"] is None
    context.close()


def test_bundled_exercise_can_be_imported_as_a_new_exercise(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    item = next(item for item in bundled_catalog() if item["canonical_name"] == "臀桥")
    exercise_id = service.repository.get_by_bundled_key(item["exercise_key"])["id"]
    with service.repository.transaction():
        service.repository.connection.execute(
            "DELETE FROM exercise_guidance_revision WHERE exercise_id = ?", (exercise_id,)
        )
        service.repository.connection.execute(
            "DELETE FROM exercise_body_area WHERE exercise_id = ?", (exercise_id,)
        )
        service.repository.connection.execute(
            "DELETE FROM exercise_alias WHERE exercise_id = ?", (exercise_id,)
        )
        service.repository.connection.execute(
            "DELETE FROM training_plan_set WHERE action_id IN "
            "(SELECT id FROM training_plan_action WHERE exercise_id = ?)",
            (exercise_id,),
        )
        service.repository.connection.execute(
            "DELETE FROM training_plan_action WHERE exercise_id = ?", (exercise_id,)
        )
        service.repository.connection.execute(
            "DELETE FROM exercise WHERE id = ?", (exercise_id,)
        )
    preview = {
        entry["exercise_key"]: entry for entry in service.preview_bundled_guidance()
    }
    assert preview[item["exercise_key"]]["match_status"] == "missing"

    created = service.accept_bundled_guidance({}, import_keys=[item["exercise_key"]])

    assert len(created) == 1
    imported = service.repository.get_by_bundled_key(item["exercise_key"])
    assert imported is not None
    detail = service.get(imported["id"])
    assert detail["canonical_name"] == "臀桥"
    assert detail["category"] == item["category"]
    assert sorted(detail["aliases"]) == sorted(item["aliases"])
    assert {(area["name"], bool(area["is_primary"])) for area in detail["body_areas"]} == {
        (name, primary) for name, primary in item["body_areas"]
    }
    assert detail["active_guidance_revision_id"] is None
    only = detail["guidance"][0]
    assert review_status(only["guidance"]) is GuidanceStatus.DRAFT
    assert only["guidance"]["review"]["review_source"] is None
    assert only["bundled_content_id"] == item["content_id"]
    context.close()


def test_importing_a_present_bundled_exercise_is_refused(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    item = next(item for item in bundled_catalog() if item["canonical_name"] == "臀桥")
    before = len(service.list(include_inactive=True))

    with pytest.raises(ValueError):
        service.accept_bundled_guidance({}, import_keys=[item["exercise_key"]])

    assert len(service.list(include_inactive=True)) == before
    context.close()


def test_import_and_mapping_cannot_target_the_same_bundled_exercise(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    item = next(item for item in bundled_catalog() if item["canonical_name"] == "臀桥")
    local = service.repository.get_by_bundled_key(item["exercise_key"])

    with pytest.raises(ValueError):
        service.accept_bundled_guidance(
            {item["exercise_key"]: local["id"]}, import_keys=[item["exercise_key"]]
        )
    context.close()


def test_bundled_import_rolls_back_when_a_later_key_fails(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    keys = [item["exercise_key"] for item in bundled_catalog()[:2]]
    before = {row["canonical_name"] for row in service.list(include_inactive=True)}

    with pytest.raises(ValueError):
        service.accept_bundled_guidance({}, import_keys=keys)

    assert {row["canonical_name"] for row in service.list(include_inactive=True)} == before
    rows = service.repository.connection.execute(
        "SELECT COUNT(*) FROM exercise"
    ).fetchone()
    assert rows[0] == len(before)
    context.close()


def test_legacy_reviews_without_answer_file_stay_valid(tmp_path):
    context = _context(tmp_path)
    service = context.exercise_service()
    target = _reviewable(service, "臀桥")

    service.confirm_guidance_reviews(
        [target["revision_id"]],
        review_source="外部 AI",
        reviewed_at="2026-09-13",
        user_confirmed=True,
    )

    row = service.repository.connection.execute(
        "SELECT guidance_json FROM exercise_guidance_revision WHERE id = ?",
        (target["revision_id"],),
    ).fetchone()
    review = json.loads(row[0])["review"]
    assert "review_answer_file" not in review
    assert review_status(json.loads(row[0])) is GuidanceStatus.ACTIVE
    context.close()
