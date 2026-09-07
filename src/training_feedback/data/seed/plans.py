"""初始计划提案的种子数据（保持草稿态，由用户审核后启用）。

动作清单以 docs/initial-exercises-and-plan.md 为权威来源；_ACTION_SPECS 是
唯一事实来源，initial_proposal 与 seed_initial_proposal 都从它派生，
避免两处维护同一份动作名列表。
"""

from __future__ import annotations

from ...domain.enums import DoseUnit
from ...domain.plans import PlanAction, PlanDay, PlannedSet, PlanPhase, PlanRevision
from ..plan_repositories import PlanRepository

PLAN_NAME = "臀腿与核心基础"


def _sets(values: tuple[float, ...], unit: DoseUnit, per_side: bool = False):
    return tuple(
        PlannedSet(index, unit, value, per_side) for index, value in enumerate(values, 1)
    )


# (动作标准名, 阶段, 计划组, 休息秒数)
_ACTION_SPECS = (
    ("仰卧360°膈肌呼吸", PlanPhase.PREPARATION, _sets((5, 5), DoseUnit.BREATHS), 30),
    ("小幅猫牛式", PlanPhase.PREPARATION, _sets((6,), DoseUnit.REPS), 30),
    ("坐姿90/90髋转换", PlanPhase.PREPARATION, _sets((6, 6), DoseUnit.REPS, True), 30),
    ("臀桥", PlanPhase.MAIN, _sets((12, 12, 10), DoseUnit.REPS), 60),
    ("蚌式开合", PlanPhase.MAIN, _sets((12, 12), DoseUnit.REPS, True), 45),
    ("椅子深蹲", PlanPhase.MAIN, _sets((10, 10), DoseUnit.REPS), 60),
    ("死虫式", PlanPhase.MAIN, _sets((8, 8), DoseUnit.REPS, True), 45),
    ("静态臀桥", PlanPhase.MAIN, _sets((20, 20), DoseUnit.SECONDS), 45),
    ("蝴蝶式", PlanPhase.COOLDOWN, _sets((30, 30), DoseUnit.SECONDS), 20),
    ("半跪髋屈肌拉伸", PlanPhase.COOLDOWN, _sets((30, 30), DoseUnit.SECONDS, True), 20),
    ("站立体前屈", PlanPhase.COOLDOWN, _sets((20, 20), DoseUnit.SECONDS), 20),
)


def initial_proposal(exercise_ids: dict[str, int]) -> PlanRevision:
    return PlanRevision(
        PLAN_NAME,
        "验证准备、等量与不等量组、重复次数、单侧训练、计时保持、次日反馈和外部 AI 导出。",
        (
            PlanDay(
                1,
                "基础训练日",
                tuple(
                    PlanAction(index, exercise_ids[name], phase, planned_sets, rest)
                    for index, (name, phase, planned_sets, rest) in enumerate(_ACTION_SPECS, 1)
                ),
            ),
        ),
    )


def seed_initial_proposal(connection) -> int:
    """播种初始计划提案；幂等，已存在时直接返回其 id。"""
    existing = connection.execute(
        "SELECT id FROM training_plan WHERE name = ?", (PLAN_NAME,)
    ).fetchone()
    if existing is not None:
        return existing[0]
    from ..exercise_repositories import ExerciseRepository

    exercises = ExerciseRepository(connection)
    exercise_ids = {}
    for name, *_ in _ACTION_SPECS:
        resolved = exercises.resolve(name)
        if resolved is None:
            raise ValueError(f"Seed exercise is missing: {name}")
        exercise_ids[name] = resolved["id"]
    plan_id, _ = PlanRepository(connection).create_plan(initial_proposal(exercise_ids))
    return plan_id
