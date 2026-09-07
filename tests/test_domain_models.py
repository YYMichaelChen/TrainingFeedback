import pytest

from training_feedback.domain.enums import DoseUnit, ExerciseResult, SessionStatus
from training_feedback.domain.models import SessionActionResult, derive_final_status
from training_feedback.domain.plans import (
    PlanAction,
    PlanDay,
    PlannedSet,
    PlanPhase,
    PlanRevision,
    validate_revision,
)


def test_actual_dose_is_required_for_exceeded_and_partial():
    with pytest.raises(ValueError):
        SessionActionResult(ExerciseResult.EXCEEDED)
    with pytest.raises(ValueError):
        SessionActionResult(ExerciseResult.PARTIAL, (None, None))


def test_not_completed_does_not_accept_actual_dose():
    with pytest.raises(ValueError):
        SessionActionResult(ExerciseResult.NOT_COMPLETED, (0,))


def test_completed_does_not_require_or_infer_actual_dose():
    result = SessionActionResult(ExerciseResult.COMPLETED, note="original note")
    assert result.actual_values == ()
    assert result.note == "original note"


def test_final_status_is_completed_only_when_all_actions_finished():
    assert (
        derive_final_status((ExerciseResult.COMPLETED, ExerciseResult.EXCEEDED))
        == SessionStatus.COMPLETED
    )
    assert (
        derive_final_status((ExerciseResult.COMPLETED, ExerciseResult.PARTIAL))
        == SessionStatus.PARTIAL
    )


def test_plan_supports_equal_unequal_and_per_side_sets():
    equal = tuple(PlannedSet(index, DoseUnit.REPS, 15) for index in (1, 2))
    unequal = tuple(
        PlannedSet(index, DoseUnit.REPS, value, per_side=True)
        for index, value in enumerate((12, 10, 10, 8), 1)
    )
    assert equal[0].value == equal[1].value == 15
    assert [planned_set.value for planned_set in unequal] == [12, 10, 10, 8]
    assert all(planned_set.per_side for planned_set in unequal)


def test_plan_dose_rules_reject_invalid_values_and_mixed_units():
    with pytest.raises(ValueError):
        PlannedSet(1, DoseUnit.REPS)
    with pytest.raises(ValueError):
        PlannedSet(1, DoseUnit.FREE)
    with pytest.raises(ValueError):
        PlanAction(
            1,
            1,
            PlanPhase.MAIN,
            (PlannedSet(1, DoseUnit.REPS, 5), PlannedSet(2, DoseUnit.SECONDS, 5)),
        )


@pytest.mark.parametrize("order", [True, 0, "1"])
def test_plan_orders_require_positive_integers(order):
    with pytest.raises(ValueError):
        PlannedSet(order, DoseUnit.REPS, 5)


def test_plan_activation_requires_active_approved_guidance():
    revision = PlanRevision(
        "基础计划",
        "验证结构化剂量",
        (
            PlanDay(
                1,
                "训练日",
                (PlanAction(1, 7, PlanPhase.MAIN, (PlannedSet(1, DoseUnit.SECONDS, 30),)),),
            ),
        ),
    )
    exercise = {
        "id": 7,
        "active": 1,
        "active_guidance_revision_id": 3,
        "guidance": [{"id": 3, "guidance": {"review": {"status": "draft"}}}],
    }
    errors = validate_revision(revision, lambda exercise_id: exercise if exercise_id == 7 else None)
    assert errors == ("Exercise 7 has no approved active guidance.",)
