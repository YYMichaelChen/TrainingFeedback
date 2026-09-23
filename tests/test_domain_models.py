import pytest

from training_feedback.domain.enums import DoseUnit
from training_feedback.domain.plans import (
    PlanAction,
    PlannedSet,
    PlanPhase,
)


def test_plan_dose_rules_reject_invalid_values_and_mixed_units():
    with pytest.raises(ValueError):
        PlannedSet(True, DoseUnit.REPS, 5)
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
