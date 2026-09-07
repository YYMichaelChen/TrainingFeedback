"""首发动作目录与保守版入门指导文案（内容以 docs/initial-exercises-and-plan.md 为权威来源）。"""

from __future__ import annotations

from typing import Any

CATALOG = [
    ("臀桥", "main", "", ["臀部"], ["常规臀桥"]),
    ("蚌式开合", "main", "", ["臀部"], []),
    ("椅子深蹲", "main", "chair", ["大腿前侧", "臀部"], []),
    ("死虫式", "main", "mat", ["核心"], []),
    ("蝴蝶臀桥", "main", "", ["臀部"], []),
    ("跪姿臀冲", "main", "mat", ["臀部", "核心"], []),
    ("静态臀桥", "main", "", ["臀部", "核心"], []),
    ("仰卧360°膈肌呼吸", "supporting", "mat", [], []),
    ("小幅猫牛式", "supporting", "mat", [], []),
    ("坐姿90/90髋转换", "supporting", "", [], []),
    ("蝴蝶式", "supporting", "", [], []),
    ("仰卧4字臀部拉伸", "supporting", "mat", [], []),
    ("半跪髋屈肌拉伸", "supporting", "mat", [], []),
    ("站立体前屈", "supporting", "", [], []),
]


def starter_guidance(name: str) -> dict[str, Any]:
    return {
        "purpose": f"用于安全、可控地练习{name}。",
        "starting_position": "保持稳定、舒适且可以自然呼吸的起始姿势。",
        "steps": [{"order": 1, "text": "缓慢完成动作并保持可控。"}],
        "breathing": "全程保持自然呼吸，不屏息。",
        "tempo_or_pacing": "慢速、平稳，避免借力。",
        "intended_sensations": ["目标区域轻度用力"],
        "common_compensations": ["避免用其他部位代偿"],
        "stop_criteria": ["出现疼痛、尖锐不适或无法保持控制时立即停止。"],
        "regressions": ["减少幅度或次数，并保持动作可控。"],
        "progressions": ["在无不适且动作稳定时逐步增加挑战。"],
        "equipment": [],
        "applicability": "按个人情况选择，必要时寻求专业建议。",
        "cautions": "这不是医疗建议；疼痛或伤病时停止并寻求专业帮助。",
        "images": [{"path": None, "caption": "暂无图片", "status": "missing"}],
        "review": {
            "status": "draft",
            "reviewer_type": None,
            "review_source": None,
            "review_note": "",
            "reviewed_at": None,
            "user_approved_at": None,
        },
    }


def seed_catalog(connection) -> None:
    from ..exercise_repositories import ExerciseRepository

    repository = ExerciseRepository(connection)
    with connection:
        for name, category, equipment, areas, aliases in CATALOG:
            if repository.get_by_canonical_name(name) is None:
                exercise_id = repository.create(
                    name,
                    category,
                    equipment,
                    [(area, True) for area in areas],
                )
                for alias in aliases:
                    repository.add_alias(exercise_id, alias)
                repository.add_guidance_revision(exercise_id, starter_guidance(name))
        connection.commit()
