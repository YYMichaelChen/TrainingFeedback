"""计划版本的只读文本渲染与版本差异展示。"""

from __future__ import annotations

from typing import Any

from ..domain.plans import diff_revisions, revision_from_snapshot
from .labels import (
    DOSE_UNIT_LABELS,
    PLAN_PHASE_LABELS,
    PLAN_STATUS_LABELS,
    label,
    planned_set_text,
)


def render_revision(revision: dict[str, Any]) -> str:
    """Render one persisted revision without changing any plan data."""
    lines = [
        f"版本 {revision['revision_number']}【{label(PLAN_STATUS_LABELS, revision['status'])}】",
        f"训练目的：{revision['purpose']}",
    ]
    for day in revision["days"]:
        lines.append(f"第 {day['day_order']} 天：{day['name']}")
        for action in day["actions"]:
            lines.append(
                f"  {action['action_order']}．{action.get('exercise_name', '动作')} "
                f"【{label(PLAN_PHASE_LABELS, action['phase'])}】— "
                f"休息 {action['rest_seconds'] or 0} 秒"
            )
            if action["note"]:
                lines.append(f"     备注：{action['note']}")
            for planned_set in action["sets"]:
                lines.append(f"     {planned_set_text(planned_set)}")
    return "\n".join(lines)


def render_diff(before: dict[str, Any] | None, after: dict[str, Any]) -> str:
    """Render the structured domain diff using persisted revision snapshots."""
    if before is None:
        return "当前没有启用的计划版本。启用此草稿后，它将成为第一个当前版本。"
    changes = diff_revisions(revision_from_snapshot(before), revision_from_snapshot(after))
    if not changes:
        return "与当前版本相比没有训练安排变化。"
    labels = {
        "exercise_changed": "训练动作",
        "action_reordered": "动作顺序",
        "phase_changed": "动作阶段",
        "rest_changed": "休息时间",
        "action_note_changed": "动作备注",
        "set_value_changed": "组数值",
        "unit_changed": "剂量单位",
        "per_side_changed": "每侧执行",
        "set_note_changed": "组备注",
        "set_added": "新增组",
        "set_removed": "删除组",
        "action_added": "新增动作",
        "action_removed": "删除动作",
        "day_added": "新增训练日",
        "day_removed": "删除训练日",
        "plan_purpose": "计划目的",
    }
    def display(change: dict[str, Any], key: str):
        """把 diff 中的枚举取值翻译为中文标签，其余原样展示。"""
        value = change[key]
        if change["category"] == "phase_changed":
            return label(PLAN_PHASE_LABELS, value)
        if change["category"] == "unit_changed":
            return label(DOSE_UNIT_LABELS, value)
        return value

    return "\n".join(
        f"{labels.get(change['category'], change['category'])} ({change['path']})\n"
        f"  修改前：{display(change, 'before')}\n"
        f"  修改后：{display(change, 'after')}"
        for change in changes
    )
