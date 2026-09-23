"""Session-scope portable evidence shares the plan exporter and export identity namespace."""

import json


def known(value):
    return "未知（未记录）" if value is None else str(value)


class GroupSessionHandoff:
    def __init__(self, service, plans):
        self.service, self.plans = service, plans

    def export(self, identifier):
        session = self.service.get(identifier)
        return self.plans.export(session["revision_id"], session_service=self.service,
                                 session_id=identifier)


def render_session_summary(session):
    lines = [
        "## 训练执行事实",
        f"训练日期：{session['training_date']}；状态：{session['status']}；"
        f"保存位置：{session['position'] + 1}",
        f"开始：{session['started_at']}；结束：{session['ended_at'] or '尚未结束'}",
    ]
    for row in session["occurrences"]:
        group = row["group"]
        state = row["start_review"]["eligibility"]["reviewed"]
        reviewed = "未知（未记录）" if state is None else "已审核" if state else "未审核"
        side = ("每侧汇总（侧序未记录）" if row.get("dose_scope") == "per_side_aggregate"
                else row["side"] or "双侧/不分侧")
        lines.extend([
            "",
            f"### {row['position'] + 1}. {row['action']['exercise_name']}",
            (f"动作组：{group['name']}；第 {row['round_number']}/{group['round_count']} 轮"
             if group else "独立动作"),
            f"侧别：{side}；结果：{row['result'] or '未知（未记录）'}",
            f"本次动作后休息：{known(row['rest_after_seconds'])} 秒；边界：{row['rest_boundary']}",
            f"开始时审核：{reviewed}；"
            f"观察时间：{known(row['start_review']['observed_at'])}",
            f"结果批次：{row['batch_id'] if row['batch_id'] is not None else '无'}",
            f"用户原始备注：{row['note'] if row['note'] is not None else '未知（未记录）'}",
        ])
        if not row["actual_sets"]:
            lines.append("实际剂量：未记录（不是零）。")
        for dose in row["actual_sets"]:
            value = (dose["value"] if dose["value"] is not None else
                     "无数值（自由剂量）" if dose["unit"] == "free" else "未知（未记录）")
            side = ("每侧" if dose.get("per_side") else "未知" if dose.get("per_side") is None
                    and "per_side" in dose else dose["side"] or "不分侧")
            lines.append(f"- 实际第 {dose['order']} 组：{value} {dose['unit']}；"
                         f"侧别 {side}；来源 {dose['provenance']}；"
                         + dose["note"])
    lines.extend(["", "### 暂停、中止、撤回及备注修正"])
    for event in session["events"]:
        lines.append(f"- {event['occurred_at']} · {event['kind']}："
                     + json.dumps(event["facts"], ensure_ascii=False))
    lines.extend(["", "### 次日反馈"])
    feedback = session["feedback"]
    if feedback is None:
        lines.append("尚未提交；无默认身体感受。")
    else:
        for area in feedback["areas"]:
            lines.append(f"- {area['name']}：{area['value'] or '未知（未回答）'}")
        lines.append("总体原始备注：" + (feedback["overall_note"] or "未知（未记录）"))
    return "\n".join(lines)
