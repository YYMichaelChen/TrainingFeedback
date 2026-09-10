"""Complete synthetic guidance used by tests that exercise review workflows."""


def complete_guidance(name: str) -> dict:
    return {
        "purpose": f"用于安全、可控地练习{name}。",
        "primary_body_areas": ["测试区域"],
        "secondary_body_areas": [],
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
