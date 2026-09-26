"""界面文案：稳定内部枚举/状态码到中文标签的映射，以及通用对话框工具。"""

import re

from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QMessageBox

from ..domain.enums import AbortReason, DoseUnit, ExerciseResult, FeedbackValue, SessionStatus
from ..domain.plans import PlanPhase

RESULT_LABELS = {
    ExerciseResult.EXCEEDED: "超额完成",
    ExerciseResult.COMPLETED: "按计划完成",
    ExerciseResult.PARTIAL: "部分完成",
    ExerciseResult.NOT_COMPLETED: "未完成",
}

SESSION_STATUS_LABELS = {
    SessionStatus.OPEN: "进行中",
    SessionStatus.PAUSED: "已暂停",
    SessionStatus.COMPLETED: "已完成",
    SessionStatus.PARTIAL: "部分完成",
    SessionStatus.ABORTED: "已中止",
}

ABORT_REASON_LABELS = {
    AbortReason.DISCOMFORT: "身体不适",
    AbortReason.PAIN_OR_INJURY: "疼痛或受伤",
    AbortReason.URGENT_INTERRUPTION: "紧急中断",
    AbortReason.INSUFFICIENT_TIME: "时间不足",
    AbortReason.OTHER: "其他",
}

DOSE_UNIT_LABELS = {
    DoseUnit.REPS: "次",
    DoseUnit.SECONDS: "秒",
    DoseUnit.MINUTES: "分钟",
    DoseUnit.BREATHS: "呼吸次数",
    DoseUnit.FREE: "自定义",
}

PLAN_PHASE_LABELS = {
    PlanPhase.PREPARATION: "准备",
    PlanPhase.MAIN: "主要训练",
    PlanPhase.COOLDOWN: "放松",
}

# 动作库的两条独立状态轴：指导是否已审核，动作是否启用。互不决定。
REVIEW_STATE_LABELS = {True: "已审核", False: "未审核"}
EXERCISE_ENABLED_LABELS = {True: "启用", False: "未启用"}
EXERCISE_SOURCE_LABELS = {"bundled": "程序内置", "custom": "自定义"}

POSITION_LABELS = {
    "supine": "仰卧", "prone": "俯卧", "side_lying": "侧卧", "quadruped": "四点支撑",
    "seated": "坐姿", "kneeling": "跪姿", "standing": "站姿", "mixed": "混合体位",
    "unknown": "未分类",
}
GROUP_PLAN_TEXT = {
    "title": "训练计划 · 动作组", "new": "新建计划", "edit": "编辑草稿", "clone": "复制为草稿",
    "activate": "预览并启用", "import": "导入 v2 计划…", "export": "导出 v2 证据…",
    "name": "计划名称", "purpose": "训练目的", "rationale": "本次安排或调整理由",
    "day": "训练日", "add_day": "添加训练日", "rename_day": "修改训练日名称",
    "action": "独立动作", "group": "动作组", "add_action": "添加动作", "add_group": "添加动作组",
    "add_member": "添加成员", "edit_item": "编辑所选项", "remove": "移除所选项",
    "up": "上移", "down": "下移", "move_day": "移至另一训练日…", "move_member": "移至另一动作组…",
    "choose": "选择动作", "phase": "训练阶段", "note": "原始备注",
    "sets": "逐组剂量（动作组内为每轮剂量）", "value": "数值", "unit": "单位",
    "per_side": "每侧", "set_rest": "组间休息秒", "add_set": "添加剂量组",
    "remove_set": "删除剂量组",
    "member_rest": "成员后休息秒", "side_rest": "换侧休息秒", "round_rest": "轮间休息秒",
    "exit_rest": "退出后休息秒", "first_side": "先做哪一侧", "rounds": "轮数",
    "sequence": "换侧顺序", "transition": "体位 / 支撑转换说明", "group_name": "动作组名称",
    "none": "不适用", "left": "左侧", "right": "右侧",
    "member_each_side": "每个成员分别完成两侧", "same_side_then_switch": "每轮先同侧序列再换侧",
    "all_rounds_then_switch": "先一侧全部轮次再换侧", "save": "保存草稿", "error": "无法完成操作",
    "preview": "完整计划、差异与执行顺序", "confirm": "确认启用当前计划及列出的未审核指导",
    "unreviewed": "未审核指导", "diff": "变更明细", "new_revision": "新计划或新版本",
    "dissolve": "移除后只剩一个成员。明确拆散这个动作组？请先将轮数设为 1。",
    "remove_confirm": "确定移除所选计划项？保存后生效。", "exported": "证据已导出到：",
    "no_plans": "暂无计划", "json_filter": "JSON 文件 (*.json)",
    "rest_seconds": "休息 {value} 秒",
    "select_destination": "选择目标", "expanded": "执行顺序（每行完成一个成员的全部组）",
    "preview_truncated": "预览仅显示前 300 个执行位置；完整处方及轮数保留。",
    "before": "原值", "after": "新值", "removed": "已移除", "added": "新增",
    "item_id": "条目身份", "kind": "类型", "order": "顺序", "members": "成员",
    "days": "训练日", "items": "计划项", "content": "内容引用", "classification": "动作分类",
    "exercise": "动作身份", "exercise_name": "动作名称", "source": "来源",
    "id": "编号", "family_key": "动作族", "variant_role": "族内角色",
    "variant_order": "族内顺序", "parent_exercise_key": "父动作",
    "starting_position_class": "起始体位", "target_plan_name": "目标计划", "group_id": "动作组身份",
    "rest_after_set_seconds": "组间休息秒", "rest_after_member_seconds": "成员后休息秒",
    "rest_after_action_seconds": "动作后休息秒", "rest_after_group_seconds": "动作组后休息秒",
    "rest_between_sides_seconds": "换侧休息秒", "rest_between_rounds_seconds": "轮间休息秒",
    "round_count": "轮数", "side_sequence": "换侧顺序", "unknown": "未知 / 不适用",
    "yes": "是", "no": "否", "import_basis": "原始导入依据", "original_file": "受管原件",
    "migration_basis": "迁移保留的原登记（只读证据）", "provenance": "事实来源",
    "dose_scope": "剂量范围", "per_side_aggregate": "每侧汇总（侧序未记录）",
    "whole": "整体动作", "migration_time": "迁移时绑定", "source_id": "原记录 ID",
    "side_order_recorded": "曾记录侧序", "set_rest_recorded": "曾记录组间休息",
}
VARIANT_LABELS = {"base": "基础动作", "variant": "变式", "standalone": "独立动作"}
EXECUTION_TEXT = {
    "title": "训练执行", "hub": "训练与历史", "unknown": "未记录", "both": "双侧 / 不分侧",
    "left": "左侧", "right": "右侧", "side": "换侧休息", "round": "轮间休息",
    "member": "成员间休息", "group_exit": "动作组后休息", "action_exit": "动作后休息",
    "note": "可选原始备注", "actual": "实际完成的组（只填写当前侧；未做的组不填写）",
    "value": "实际数值", "unit": "单位", "side_column": "侧别", "set_note": "自由剂量说明 / 组备注",
    "add_set": "增加实际组", "remove_set": "删除所选实际组", "save_result": "保存结果",
    "cancel": "取消录入", "round_complete": "本轮未记录成员按计划完成…",
    "round_preview": "确认本轮完成范围",
    "round_hint": "仅确认以下未记录位置的全部处方；原有结果保留。",
    "retract": "撤回当前结果…", "retract_batch": "撤回此整轮批次…",
    "retract_hint": "以下已保存事实将归档并恢复为未记录：",
    "next": "下一个未记录位置", "pause": "暂停训练", "abort": "中止训练…",
    "finish": "完成训练…", "finish_hint": "所有位置已有结果，确认保存最终训练状态：",
    "discard": "放弃未保存输入？",
    "discard_hint": "离开将放弃当前实际剂量和备注输入；已保存结果保留。",
    "error": "操作未完成", "reload": "重新载入已保存状态", "guidance": "冻结动作指导",
    "invalid_image": "图片文件当前不可用；冻结文字与停止条件仍可阅读。",
    "start": "预览并开始训练…", "resume": "恢复未完成训练", "start_preview": "确认训练日与指导",
    "unreviewed": "本次使用未审核指导：", "none": "无", "previous_day": "前一天训练尚未完成",
    "history": "训练历史", "export": "导出训练证据…", "exported": "训练证据已导出到：",
    "feedback": "次日反馈…", "submit": "保存次日反馈", "overall_note": "总体原始备注",
    "feedback_hint": "未选择的部位保留未知；不会自动填入身体感受。",
    "correct": "修正备注（保留原文记录）…", "choose_note": "选择需要修正的备注",
    "refresh": "刷新", "no_sessions": "暂无训练记录", "no_next": "已到最后一个位置",
    "next_label": "下一位置：", "prescription": "当前侧计划剂量：", "saved": "已保存：",
    "actual_unknown": "实际剂量未记录（不是零）", "performed": "实际剂量：",
    "confirmed": "由按计划完成确认", "entered": "用户填写", "no_feedback": "次日反馈尚未提交",
    "unknown_feedback": "未知（未回答）", "events": "操作记录", "started": "开始训练",
    "paused": "暂停", "resumed": "恢复", "finished": "完成训练", "aborted": "中止训练",
    "result_retracted": "撤回结果", "note_correction": "修正备注",
    "per_side_aggregate": "每侧汇总（侧序未记录）", "stored_actual": "原记录（未补推）",
    "imported_event": "迁移保留的原操作", "imported_retraction": "迁移保留的撤回原件",
    "imported_note_correction": "迁移保留的备注修正原件",
    "progress": "已完成 {done}/{total} 项",
}


def occurrence_title(row):
    group = row["group"]
    prefix = (f"{group['name']} · 第 {row['round_number']}/{group['round_count']} 轮 · "
              if group else "独立动作 · ")
    return (f"{row['position'] + 1}. {prefix}{row['action']['exercise_name']} · "
             + occurrence_side_text(row))


def occurrence_side_text(row):
    if row.get("dose_scope") == "per_side_aggregate":
        return EXECUTION_TEXT["per_side_aggregate"]
    return EXECUTION_TEXT.get(row["side"], EXECUTION_TEXT["both"])


def seconds_text(value):
    return "未知（未记录）" if value is None else f"{value:g}"


def occurrence_prescription(row):
    lines = [EXECUTION_TEXT["prescription"]]
    for dose in sorted(row["action"]["sets"], key=lambda item: item["order"]):
        value = "按说明" if dose["value"] is None else f"{dose['value']:g}"
        scope = ("每侧 " if row.get("dose_scope") == "per_side_aggregate"
                 and dose["per_side"] else "")
        unit = label(DOSE_UNIT_LABELS, dose["unit"])
        lines.append(f"第 {dose['order']} 组：{scope}{value} {unit}；"
                     f"组间休息 {seconds_text(dose['rest_after_set_seconds'])} 秒；{dose['note']}")
    rest = seconds_text(row["rest_after_seconds"])
    lines.append(f"{EXECUTION_TEXT[row['rest_boundary']]}：{rest} 秒")
    lines.append("计划原始备注：" + (row["action"]["note"] or ""))
    if row["group"]:
        lines.extend(["体位 / 支撑转换：" + row["group"]["transition"],
                      "动作组原始备注：" + row["group"]["note"]])
    return "\n".join(lines)


def occurrence_result_text(row):
    lines = [EXECUTION_TEXT["saved"] + RESULT_LABELS[row["result"]]
             if row["result"] is not None else EXECUTION_TEXT["unknown"]]
    if not row["actual_sets"]:
        lines.append(EXECUTION_TEXT["actual_unknown"])
    for dose in row["actual_sets"]:
        value = "按说明" if dose["value"] is None else f"{dose['value']:g}"
        source = ("stored_actual" if dose["provenance"] == "stored_actual" else
                  "confirmed" if dose["provenance"] == "prescription_confirmed" else "entered")
        side = ("每侧" if dose.get("per_side") else "侧别未知"
                if "per_side" in dose and dose["per_side"] is None
                else EXECUTION_TEXT.get(dose["side"], EXECUTION_TEXT["both"]))
        lines.append(f"{EXECUTION_TEXT['performed']}第 {dose['order']} 组：{value} "
                     f"{label(DOSE_UNIT_LABELS, dose['unit'])} · "
                      f"{side} · "
                     f"{EXECUTION_TEXT[source]}；{dose['note']}")
    if row["note"] is not None:
        lines.append(EXECUTION_TEXT["note"] + "：" + row["note"])
    return "\n".join(lines)


def imported_original_text(kind, original):
    """迁移保留事件的原件说明；原始载荷留在数据库，不向用户展示 JSON。"""
    if kind == "imported_event":
        event_type = original.get("event_type")
        text = "原事件：" + EXECUTION_TEXT.get(event_type, event_type or EXECUTION_TEXT["unknown"])
        extra = "；".join(part for part in (original.get("reason"), original.get("note")) if part)
        return [text + ("；" + extra if extra else "")]
    if kind == "imported_retraction":
        return [f"原撤回：{original.get('retracted_at') or EXECUTION_TEXT['unknown']}；"
                "原动作记录已作为迁移证据保留"]
    if kind == "imported_note_correction":
        old_value = original.get("old_value") or "（空）"
        new_value = original.get("new_value") or "（空）"
        return [f"原备注修正：{old_value} → {new_value}"]
    return ["原记录已作为迁移证据保留"]


def session_history_text(session):
    lines = [f"{session['training_date']} · {SESSION_STATUS_LABELS[session['status']]}",
             session["snapshot"]["revision"]["name"],
             f"开始：{session['started_at']}；结束：{session['ended_at'] or '尚未结束'}"]
    for row in session["occurrences"]:
        lines.extend(["", occurrence_title(row), occurrence_prescription(row),
                      occurrence_result_text(row), "开始时审核：" + REVIEW_STATE_LABELS[
                          row["start_review"]["eligibility"]["reviewed"]]])
    lines.extend(["", EXECUTION_TEXT["events"]])
    for event in session["events"]:
        lines.append(f"{event['occurred_at']} · {EXECUTION_TEXT[event['kind']]}")
        facts = event["facts"]
        if event["kind"].startswith("imported_"):
            lines.extend(imported_original_text(event["kind"], facts["original"]))
        if event["kind"] == "aborted":
            lines.extend([ABORT_REASON_LABELS[facts["reason"]], facts["note"]])
        elif event["kind"] == "result_retracted":
            for row in facts["before"]:
                lines.extend([occurrence_title(row), occurrence_result_text(row)])
        elif event["kind"] == "note_correction":
            lines.extend(["原文：" + facts["old_value"], "修正后：" + facts["new_value"]])
    feedback = session["feedback"]
    if feedback is None:
        lines.extend(["", EXECUTION_TEXT["no_feedback"]])
    else:
        lines.extend(["", "次日反馈：" + feedback["submitted_at"]])
        lines.extend(f"{area['name']}：" + FEEDBACK_VALUE_LABELS.get(
            area["value"], EXECUTION_TEXT["unknown_feedback"]) for area in feedback["areas"])
        lines.append(EXECUTION_TEXT["overall_note"] + "：" + (feedback["overall_note"] or ""))
    return "\n".join(lines)
LIBRARY_REASON_LABELS = {
    "disabled": "未启用；仅阻止新开始，历史与暂停训练仍保留",
    "incomplete_text": "指导文字不完整", "invalid_images": "缺少有效必需示意图",
    "removed": "已移出可用目录", "missing": "图片未提供", "unavailable": "路径、文件或哈希不可用",
    "hash_mismatch": "图片哈希不一致", "undecodable": "图片无法解码",
    "placeholder": "占位图片不能作为动作示意图",
}
LIBRARY_TEXT = {
    "removal": "移除与恢复审核",
    "parent_missing": "（保留的父动作身份，当前目录缺项）",
    "removed": "已移除／发行方撤回",
    "close": "关闭",
    "title": "动作库", "search": "按名称或别名搜索", "all_positions": "全部起始体位",
    "gallery_count": "共 {count} 个动作 · 点击卡片查看指导",
    "back_to_gallery": "← 返回动作库", "batch_mode": "批量选择",
    "standalone": "独立动作", "name": "动作 / 动作族", "source": "来源", "position": "起始体位",
    "readiness": "图片资格", "review": "审核", "enabled": "启用状态", "bundled": "程序内置",
    "custom": "自定义", "ready": "可用", "draft": "草稿", "none": "无",
    "details": "完整指导",
    "select": "使用当前内容", "enable": "启用动作",
    "disable": "停用动作", "edit": "编辑动作内容…", "copy": "复制为自定义…",
    "image": "替换为本地示意图…", "record_review": "记录外部审核…",
    "batch_review": "审核选中的动作…", "withdraw": "撤销当前审核",
    "refresh": "刷新", "confirm_title": "确认操作",
    "confirm_select": "将当前显示的内容投入使用？新训练计划将使用此内容。",
    "confirm_enable": "确认更改动作启用状态？未审核的图文不会因此变成已审核。",
    "confirm_withdraw": "确认撤销当前内容的审核？原始审核事件和文件会保留。",
    "error": "操作未完成", "copy_name": "自定义动作名称", "pick_image": "选择实际示意图",
    "image_filter": "图片 (*.png *.jpg *.jpeg *.webp *.bmp *.gif)",
    "review_title": "记录外部审核", "reviewer": "审核者类型", "review_source": "外部来源",
    "occurred": "实际审核发生时间", "occurrence_hint": "日期或带时区时间；默认未知",
    "note": "原始备注", "answer": "选择审核答复原件…", "no_answer": "未附原件",
    "answer_file": "答复原件",
    "review_confirm": "我确认此次外部审核涵盖列表中每个动作的文字及实际图片",
    "record": "记录审核", "edit_title": "编辑动作内容", "family": "动作族",
    "role": "族内角色", "order": "显示顺序", "parent": "父动作", "aliases": "别名（逐行）",
    "category": "类别", "equipment": "器械概述", "save": "保存",
    "membership": "确认所显示的动作族、角色和父动作关系",
    "invalid_image": "图片不可用；文字与停止条件仍可阅读。",
    "identity": "内容身份", "catalog": "程序目录版本",
    "state_none": "尚未投入使用", "state_latest": "使用中",
    "state_stale": "使用中 · 有更新内容未启用",
    "review_events": "审核事件", "approved": "记录审核", "withdrawn": "撤销审核",
}

IMAGE_STATUS_LABELS = {
    "available": "有可用图片",
    "missing": "缺失图片",
}

REVIEWER_TYPE_LABELS = {
    None: "未记录",
    "external_ai_expert": "外部 AI 专家",
    "human_expert": "人工专家",
}

PLAN_STATUS_LABELS = {
    "draft": "草稿",
    "active": "使用中",
    "superseded": "已被替代",
}

CATEGORY_LABELS = {
    "main": "主要训练",
    "supporting": "辅助训练",
    "general": "常规",
}

FEEDBACK_VALUE_LABELS = {
    FeedbackValue.SIGNIFICANT_SORENESS: "明显酸痛，已影响活动",
    FeedbackValue.SOME_SORENESS: "有些酸痛",
    FeedbackValue.NO_OBVIOUS_SENSATION: "没有明显感觉",
    FeedbackValue.DISCOMFORT_OR_INJURY: "不适或受伤",
}


def label(mapping: dict, value) -> str:
    return mapping.get(value, mapping.get(str(value), str(value)))


def planned_set_text(item: dict, *, snapshot: bool = False) -> str:
    """显示计划或会话逐组处方；原文只读，空数值不补成零。"""
    prefix = "planned_" if snapshot else ""
    value = item[f"{prefix}value"]
    unit = item[f"{prefix}unit"]
    note = item.get("plan_note_snapshot" if snapshot else "note") or ""
    dose = str(value) if value is not None else "未记录数值"
    if value is None and unit == DoseUnit.FREE and note:
        dose = note
    text = f"第 {item['set_order']} 组：{dose} {label(DOSE_UNIT_LABELS, unit)}"
    if item[f"{prefix}per_side"]:
        text += " / 每侧"
    if note and not (value is None and unit == DoseUnit.FREE):
        text += f"；组备注：{note}"
    return text


def session_prescription_text(action: dict) -> str:
    """显示会话中的冻结处方，不访问当前计划或目录。"""
    lines = [planned_set_text(item, snapshot=True) for item in action["sets"]]
    if action.get("phase_snapshot") is not None:
        lines.append(f"阶段：{label(PLAN_PHASE_LABELS, action['phase_snapshot'])}")
    rest = action.get("rest_seconds_snapshot")
    lines.append(f"休息：{str(rest) + ' 秒' if rest is not None else '未记录'}")
    if action.get("plan_note_snapshot"):
        lines.append(f"处方动作备注：{action['plan_note_snapshot']}")
    return "\n".join(lines)


def make_unit_combo(selected: DoseUnit | str | None = None) -> QComboBox:
    """构造剂量单位下拉框；selected 为要预选的单位（枚举或其取值）。"""
    combo = QComboBox()
    for unit in DoseUnit:
        combo.addItem(label(DOSE_UNIT_LABELS, unit), unit.value)
    if selected is not None:
        combo.setCurrentIndex(combo.findData(DoseUnit(selected).value))
    return combo


def localize_dialog_buttons(buttons: QDialogButtonBox) -> None:
    texts = {
        QDialogButtonBox.StandardButton.Ok: "确定",
        QDialogButtonBox.StandardButton.Cancel: "取消",
        QDialogButtonBox.StandardButton.Save: "保存",
        QDialogButtonBox.StandardButton.Close: "关闭",
        QDialogButtonBox.StandardButton.Open: "浏览",
        QDialogButtonBox.StandardButton.Yes: "是",
        QDialogButtonBox.StandardButton.No: "否",
    }
    for button_type, text in texts.items():
        button = buttons.button(button_type)
        if button is not None:
            button.setText(text)


ERROR_TRANSLATIONS = {
    "Only plan format version 2 is accepted.": "此入口只接受 v2 计划，请使用当前导出附带的格式。",
    "The displayed plan revision changed.": "当前草稿已被修改，请重新打开后核对。",
    "The activation preview changed. Review it again.":
        "预览后计划或审核状态已变化，请重新查看并确认。",
    "Plan item identities must be unique throughout the revision.": "计划内的条目身份不能重复。",
    "The final set must use boundary rest, not set rest.":
        "最后一组的组间休息应为零；请填写相应换侧、成员或退出休息。",
    "Unilateral work requires an explicit first side.": "每侧训练需明确先做左侧还是右侧。",
    "Bilateral work has no side or side-switch rest.": "非每侧训练不能设置起始侧或换侧休息。",
    "Mixed or unknown positions require a transition instruction.":
        "体位不同或未知时，请补充转换说明后启用。",
    "External source does not belong to this data root.":
        "外部答复引用的会话或导出不属于当前数据根。",
    "A reused item identity cannot refer to another exercise.":
        "已有条目身份不能改指另一个动作；请新建条目。",
    "Select an exercise content revision.": "请选择动作。",
    "Duplicate JSON keys are not allowed.": "计划 JSON 含重复字段，无法确定其含义。",
    "Group name cannot be empty.": "动作组名称不能为空。",
    "Set the group to one round explicitly before dissolving it.":
        "请先明确把动作组改为一轮，再拆散为独立动作。",
    "Removing this member requires explicit group dissolution.": "移除此成员需要明确拆散动作组。",
    "Keep two members or explicitly dissolve the source group first.":
        "来源动作组需保留至少两个成员，或先明确拆散。",
    "Keep two members or remove/dissolve the group in the plan tree.":
        "请保留至少两个成员，或在计划树中移除、拆散动作组。",
    "Explicit confirmation is required.": "请明确确认本次操作。",
    "Select at least one content revision.": "请选择至少一个动作。",
    "The displayed content changed.": "所显示的内容已变化，请刷新后重新核对。",
    "The displayed review changed.": "审核记录已变化，请刷新后重新核对。",
    "The selected content changed; refresh the target.": "使用内容已变化，请核对后重试。",
    "Select one content revision per exercise.": "同一动作只能选定一个使用内容。",
    "Duplicate review targets are not allowed.": "请勿重复选择同一审核内容。",
    "Exercise is not enabled.": "该动作尚未启用。",
    "Unknown exercise identity.": "找不到指定的动作身份。",
    "Image is unavailable or invalid.": "图片不可用或校验失败。",
    "Image bytes cannot be decoded.": "所选文件无法解码为有效图片。",
    "A real external reviewer type is required.": "请选择实际外部审核者类型。",
    "Review source and note must be text.": "请填写真实审核来源，备注需为文本。",
    "Repair unavailable illustrations before review.": "记录审核前请修复不可用的示意图。",
    "Withdraw the prior review before recording another.": "请先撤销已有审核，再记录新的审核。",
    "There is no current review to withdraw.": "没有可撤销的当前审核。",
    "Names and aliases must be distinct.": "名称与别名不能重复。",
    "A name or alias belongs to another exercise.": "名称或别名已属于另一个动作。",
    "Unknown exercise family.": "找不到指定动作族。",
    "Exercise parent must be in the same family.": "父动作必须存在且属于同一动作族。",
    "Exercise family parent links cannot form a cycle.": "父动作关系不能形成循环。",
    "An exercise cannot be its own parent.": "动作不能以自己为父动作。",
    "Standalone exercises have no family or parent.": "独立动作不能指定动作族或父动作。",
    "A base exercise cannot have a parent.": "基础动作不能指定父动作。",
    "An open or paused session already exists.": "已经存在进行中或已暂停的训练。",
    "An active plan revision is required to start training.": "开始训练前必须先启用计划版本。",
    "A plan day must be selected before starting training.": "开始训练前必须选择训练日。",
    "The selected plan day was not found.": "没有找到所选训练日。",
    "The session changed before it could be resumed.": "训练状态已发生变化，请重新打开训练。",
    "The session changed before it could be updated.": "训练状态已发生变化，请刷新后重试。",
    "Guidance revision has already been reviewed.": (
        "该指导已经审核过了；要重新审核请先撤销此次审核。"
    ),
    "Guidance recorded in training history cannot return to review.": (
        "该指导已经被训练记录引用，不能撤销审核；需要修改内容请编辑后另存。"
    ),
    "Complete review evidence is required.": "审核证据不完整，无法记录这次审核。",
    "Complete guidance is required before recording a review.": (
        "请先补全动作指导内容，再记录这次审核。"
    ),
    "Guidance content must be complete before it can be used.": (
        "指导内容不完整，不能投入使用。"
    ),
    "No open or paused session was found.": "没有找到进行中或已暂停的训练。",
    "Only an open or paused session can record results.": "只有进行中或已暂停的训练才能记录结果。",
    "A recorded action result cannot be changed.": "已记录的动作结果不能在普通训练流程中修改。",
    "Only an open or paused session can finish.": "只有进行中或已暂停的训练才能完成。",
    "Only an open or paused session can retract results.": "训练已结束，不能撤回动作结果。",
    "Select a recorded action to retract.": "请选择一个已记录结果的动作。",
    "Every exercise must have a result before finishing.": "完成训练前必须为每个动作记录结果。",
    "An abort reason is required.": "中止训练必须选择原因。",
    "Actual dose is required for exceeded or partial results.": (
        "超额或部分完成时必须填写实际剂量。"
    ),
    "This session is not eligible for next-day feedback.": "这次训练目前不符合填写次日反馈的条件。",
    "Next-day feedback has already been submitted.": "这次训练的次日反馈已经提交。",
    "Feedback must be submitted before its note is corrected.": "提交反馈后才能修正备注。",
    "Only supported note fields can be corrected.": "只能修正允许的备注字段。",
    "Session was not found.": "没有找到这次训练。",
    "Session action was not found.": "没有找到这项训练动作。",
    "Guidance JSON must be an object.": "动作指导 JSON 必须是对象。",
    "Guidance must be an object.": "动作指导内容格式无效。",
    "Canonical name cannot be empty.": "标准名称不能为空。",
    "Alias cannot be empty.": "别名不能为空。",
    "Body area cannot be empty.": "身体部位不能为空。",
    "Duplicate alias values are not allowed.": "别名不能重复。",
    "Duplicate body area values are not allowed.": "身体部位不能重复。",
    "The canonical name and aliases must be distinct.": "标准名称与别名不能相同。",
    "The canonical name or alias is already in use.": "该标准名称或别名已被其他动作使用。",
    "Exercise was not found.": "没有找到指定的训练动作。",
    "Select at least one guidance revision to review.": "请至少选择一个要复核的动作。",
    "Select at least one guidance revision to return to review.": (
        "请至少选择一个要撤销审核的动作。"
    ),
    "Explicit user confirmation is required.": "必须明确确认。",
    "Unknown bundled exercise selection.": "所选内置动作不存在，请重新打开预览。",
    "Each bundled exercise requires a different local exercise.": (
        "每项内置指导必须对应不同的本地动作，请检查目标选择。"
    ),
    "Selected exercise was not found.": "没有找到所选本地动作，请重新打开预览。",
    "Selected exercise is linked to different bundled content.": (
        "所选动作已关联其他内置指导，请选择对应的本地动作。"
    ),
    "Exercise is already linked to different bundled content.": (
        "该动作已关联其他内置指导，无法重复关联。"
    ),
    "Bundled exercise is already linked to another exercise.": (
        "这项内置指导已关联其他本地动作，请使用已关联的目标。"
    ),
    "Bundled guidance is incomplete.": "内置指导内容不完整，无法接收此草稿。",
    "Step order must be a positive integer.": "动作步骤顺序必须是正整数。",
    "Guidance revision was not found.": "没有找到指定的动作指导。",
    "No reviewable guidance revision is selected.": "请选择一个可复核的动作。",
    "Reviewer type and source are required.": "审核人类型和来源不能为空。",
    "Explicit user approval is required.": "必须明确批准。",
    "Review time is required.": "审核时间不能为空。",
    "Review occurrence must be a valid date or timezone-aware datetime.": (
        "请填写有效的审核发生日期，或包含时区的日期时间；只知道日期时无需补填时刻。"
    ),
    "The displayed plan revision has changed. Reopen its preview.": (
        "所显示的计划版本已发生变化，请重新打开预览、核对内容后再启用。"
    ),
    "Database is not open.": "数据库尚未打开。",
    "Training session was not found.": "没有找到指定的训练会话。",
    "Unsupported external plan schema.": "不支持此外部计划格式。",
    "Unsupported external plan schema version.": "不支持此外部计划格式版本。",
    "External plan content is missing.": "外部计划缺少计划内容。",
    "External plan must contain at least one day.": "外部计划至少需要一个训练日。",
    "External rationale must contain text.": "外部调整理由不能为空。",
    "The selected path is not an empty directory.": "所选路径不是空目录，无法在此创建数据目录。",
    "The selected directory is not empty.": "所选目录不是空目录，无法在此创建数据目录。",
    "The directory is not a TrainingFeedback data root.": "所选目录不是训练反馈数据目录。",
    "The data-root metadata is incomplete or invalid.": "所选目录的数据信息不完整或已损坏。",
    "The data-root metadata cannot be read.": "所选目录的标记或配置文件无法读取，可能已损坏。",
    "The selected directory is empty. Create a new data root instead.": (
        "所选目录是空目录。请改选「创建新的数据目录」，在此新建数据目录。"
    ),
    "Cannot create the data root.": "无法在所选位置创建数据目录，请检查磁盘权限。",
    "The data root requires a newer version of TrainingFeedback.": (
        "该数据目录由更新版本的应用创建，请升级应用后再打开。"
    ),
    "The database requires a newer version of TrainingFeedback.": (
        "该数据库由更新版本的应用创建，请升级应用后再打开。"
    ),
    "This development data version is outside the support window. Reinstall the "
    "current application version and create a new data directory; the original data "
    "directory is preserved and will not be deleted or reset.": (
        "此开发数据版本已超出支持范围，请重新安装当前版本并新建数据目录。"
        "原数据目录已保留，不会自动删除或重置。"
    ),
    "The data-root configuration belongs to another application.": "所选目录的配置属于其他应用。",
    "The selected path is not a directory.": "所选路径不是目录。",
    "The data root does not contain its database.": "所选数据目录缺少数据库文件。",
    "The TrainingFeedback database is invalid.": "数据目录中的数据库无效或已损坏。",
    "The data root is in use; close it before upgrading.":
        "数据目录正在使用中，请先关闭使用它的窗口，再重试升级。",
    "An interrupted data upgrade must be recovered before opening this root.":
        "此数据目录的升级曾中断，需要完成内部恢复后才能打开。",
    "Cannot record the data-root location.": "无法记录数据目录位置，请检查磁盘权限。",
    "Pause the active training session before switching data roots.": (
        "请先暂停当前训练，再切换数据目录。"
    ),
    "The source data root does not exist.": "源数据目录不存在。",
    "A backup destination cannot be inside the source data root.": "备份目录不能位于数据目录内部。",
    "The backup destination must be empty.": "备份目录必须是空目录。",
    "Cannot create the backup destination.": "无法创建备份目录，请检查磁盘权限。",
    "The data-root backup could not be completed.": "备份未能完成，已清理不完整副本。",
}


ERROR_TRANSLATIONS.update({
    "An abort reason is required.": "请明确选择一个中止原因。",
    "An unfinished session already exists. Resume it first.": "已有未结束训练，请先恢复并处理。",
    "Select a day from the displayed plan revision.": "请选择当前计划版本中的训练日。",
    "The start preview changed. Review it again.": "开始训练的依据已变化，请重新预览。",
    "The session changed. Reload the displayed session.": "训练记录已变化，请重新载入已保存状态。",
    "Only an open session accepts this action.": "只有进行中的训练可以执行此操作。",
    "Record only the displayed occurrence.": "请在当前显示的训练位置记录结果。",
    "This occurrence already has a saved result.": "当前训练位置已保存结果，请先明确撤回。",
    "The current occurrence is not in an action group.": "当前是独立动作，不能按整轮记录。",
    "This round has no unrecorded occurrences.": "当前轮次没有尚未记录的成员。",
    "The round preview changed. Review it again.": "本轮完成范围已变化，请重新预览。",
    "Every occurrence needs a saved result before finishing.":
        "请为每个训练位置保存结果后再完成训练。",
    "Actual dose must be finite and non-negative.": "实际剂量必须是有限的非负数字。",
    "Actual dose cannot be unknown; free work needs an explanation.":
        "请填写实际剂量；自由剂量不填数字时，必须填写具体说明。",
    "Actual side must match this occurrence; record the other side there.":
        "实际剂量只能属于当前侧；另一侧请在对应训练位置记录。",
    "This batch was already retracted or changed.": "此批次已撤回或变化，请重新载入。",
    "Retract this result using its complete batch.": "此结果属于整轮批次，请撤回该完整批次。",
    "This occurrence has no saved result.": "当前训练位置尚未保存结果。",
    "The note changed. Reload the displayed session.": "备注已变化，请重新载入后再修正。",
    "Only terminal session notes can be corrected.": "只有已结束训练的备注可以审计式修正。",
    "Feedback has not been submitted.": "次日反馈尚未提交。",
})


LIFECYCLE_TEXT = {
    "no_decision": "尚无已应用决定", "enabled": "当前已启用", "disabled": "当前未启用",
    "batch_targets": "本批全部动作",
    "prior_impact": "此前保存的影响依据",
    "remove": "移除", "restore": "恢复", "new_request": "新建移除／恢复申请",
    "target": "动作", "disposition": "可用状态",
    "plan_revision": "计划版本",
    "catalog_version": "目录版本",
    "reason": "申请原因（原文）", "note": "本次决定备注（原文）",
    "preview": "预览全部影响", "submit": "提交申请", "close": "关闭", "error": "操作未完成",
    "confirm_request": "我已查看全部动作与引用影响，确认提交此申请",
    "confirm_decision": "我已查看当前范围和影响，确认执行所选决定",
    "consequence": "移除后禁止新用，保留计划、图片与历史；未结束训练可继续。恢复须重新启用，"
                   "受影响计划须另行编辑并确认新版本。变体不会连带移除。",
    "plans": "引用计划", "groups": "引用组合与成员", "sessions": "引用训练",
    "reviews": "指导审核记录", "variants": "依赖变体", "exports": "已有导出",
    "draft": "草稿", "active": "活动", "superseded": "已被替代", "open": "进行中",
    "paused": "暂停", "completed": "完成", "partial": "部分完成", "aborted": "已中止",
    "requested": "已申请", "under_review": "审核中", "approved": "已批准",
    "applied": "已应用", "rejected": "已驳回", "cancelled": "已取消",
    "withdrawn": "已撤回", "removed": "已移除／撤回", "restored": "已恢复",
    "available": "可访问", "unknown": "文件不可读，影响未知", "missing": "当前目录已缺项",
    "reload": "重新载入申请", "request": "申请", "status": "审核状态",
    "local": "本数据目录的决定", "publisher": "发行方目录记录",
    "publisher_note": "这里只记录当前程序目录的可用性和本机观察时间，不推测发行方决定发生时间。"
                      "发行方撤回不能用本地恢复覆盖。",
    "self": "填入我本人", "self_source": "用户本人明确决定", "source": "决定来源",
    "occurred": "决定实际发生时间",
    "button_preview": "预览当前影响", "button_under_review": "进入／刷新审核",
    "button_approved": "批准", "button_approve_apply": "批准并应用",
    "button_applied": "应用已批准决定", "button_rejected": "驳回", "button_cancelled": "取消申请",
}

ERROR_TRANSLATIONS.update({
    "Exercise is removed or withdrawn; edit the plan explicitly.":
        "动作已移除或撤回，请在新计划版本中明确编辑替换。",
    "This plan was affected by removal; confirm a new plan revision.":
        "此计划曾受动作移除影响，请编辑并确认新的计划版本后再开始训练。",
    "This lifecycle transition is not allowed.": "当前申请状态不允许此操作。",
    "Lifecycle request was not found.": "未找到此移除／恢复申请。",
    "Unknown lifecycle operation.": "未知的移除／恢复操作。",
    "The local removal state does not match this operation.":
        "动作当前移除状态已变化，请核对移除或恢复的范围。",
    "Publisher withdrawal cannot be restored by a local decision.":
        "当前发行方目录已撤回或缺少此动作，不能用本地决定恢复。",
    "Repair current content and images before restoration.": "请先补全当前内容并修复图片后再恢复。",
    "A decision source and a text note are required.": "请填写真实决定来源，备注可留空。",
    "A lifecycle reason is required.": "请填写移除或恢复的申请原因。",
    "An unfinished lifecycle request already exists for this exercise.":
        "此动作已有待处理申请，请先处理或取消该申请。",
    "The removal impact changed. Refresh and review it again.":
        "影响依据已变化或尚未预览，请预览当前影响、进入／刷新审核后重新批准。",
    "The lifecycle content changed. Cancel and submit a new request.":
        "动作内容或选用状态已变化，请取消原申请并重新提交，保留原审核过程。",
    "The lifecycle request changed. Reload its history.":
        "申请已有新决定，请重新载入历史后再操作。",
    "Unknown library model; this data root needs a newer application.":
        "此数据目录由更新版本的应用创建，请升级应用后再打开。",
    "An unmarked root already contains current-model work.":
        "此数据目录已包含当前模型的数据但未完成升级登记，请从备份恢复后再打开。",
    "Conversion marker and configuration disagree.":
        "此数据目录的升级登记与配置不一致，请从备份恢复后再打开。",
    "The upgrade data root does not exist.": "要升级的数据目录不存在。",
    "The data-root lock path is invalid.": "数据目录的锁文件路径无效，请不要手动改动数据目录。",
    "There is not enough free space for a recoverable upgrade.":
        "磁盘剩余空间不足，无法安全升级数据目录；请释放空间后重试。",
    "Upgrade resources cannot contain linked paths.":
        "数据目录中包含链接路径，无法安全升级；请移除链接后重试。",
    "An upgrade resource is not a regular file.": "数据目录中存在非常规文件，无法安全升级。",
    "Data-root resources changed during upgrade backup.":
        "升级备份期间数据目录内容发生变化，请关闭其他程序后重试。",
    "The upgrade recovery journal or manifest is unreadable.":
        "升级恢复信息无法读取，请不要手动改动数据目录；仍失败请从备份恢复。",
    "The upgrade recovery journal is invalid.":
        "升级恢复信息无效，请不要手动改动数据目录；仍失败请从备份恢复。",
    "The upgrade recovery manifest hash does not match.":
        "升级恢复快照的校验信息不匹配，请从备份恢复后再打开。",
    "The upgrade recovery manifest format is invalid.":
        "升级恢复快照的格式无效，请从备份恢复后再打开。",
    "Upgrade resource hashes or inventory do not match.":
        "升级前后的文件校验不一致，请从备份恢复后再打开。",
    "Converted references failed validation.":
        "升级后的数据引用未通过校验，请从备份恢复后再打开。",
    "Converted model configuration is missing.":
        "升级后的数据目录缺少模型配置，请从备份恢复后再打开。",
    "Conversion facts are missing.": "升级登记缺失，请从备份恢复后再打开。",
    "Original managed resource bytes changed during conversion.":
        "升级过程中原始文件内容发生变化，请关闭其他程序后重试。",
    "Original conversion facts failed preservation validation.":
        "升级未能完整保留原始数据，请从备份恢复后再打开。",
    "Obsolete live tables remain after conversion.":
        "升级后仍残留旧数据表，请从备份恢复后再打开。",
    "Converted external identities do not match original facts.":
        "升级后的数据身份与原始记录不一致，请从备份恢复后再打开。",
    "Converted facts do not match their original records.":
        "升级后的数据与原始记录不一致，请从备份恢复后再打开。",
    "A guidance revision was not converted.": "有动作指导未被升级收录，请从备份恢复后再打开。",
    "An unfinished session has no recorded prescription.":
        "升级后的未完结训练缺少处方记录，请从备份恢复后再打开。",
})


ACTIVATION_REASONS = {
    "was not found": "动作不存在",
    "is not enabled": "动作未启用",
    "has no guidance in use": "动作尚未投入使用",
    "has incomplete guidance in use": "动作的使用内容不完整",
}


def _activation_reasons(detail: str) -> str:
    """把逐动作的激活阻塞原因翻成中文；无法识别时保留原文，不吞掉信息。"""
    reasons = []
    for exercise_id, reason in re.findall(r"Exercise (\d+) ([^.]+)\.", detail):
        reasons.append(f"动作 {exercise_id} {ACTIVATION_REASONS.get(reason, reason)}")
    return "；".join(reasons) if reasons else detail.strip()


def user_message(message: str) -> str:
    if message.startswith("Invalid plan v2 at "):
        return "v2 计划格式不完整或字段无效，请核对：" + message[len("Invalid plan v2 at "):]
    if message.startswith("Content is not eligible: "):
        return "当前内容不可用：" + "；".join(
            LIBRARY_REASON_LABELS.get(reason, reason)
            for reason in message.partition(": ")[2].split(", ")
        )
    translated = ERROR_TRANSLATIONS.get(message)
    if translated is not None:
        return translated
    if message.startswith("Exercise ") and message.endswith(" was not found."):
        return "没有找到指定的训练动作。"
    if message.startswith("Plan revision cannot be activated:"):
        return "计划版本无法启用：" + _activation_reasons(message.partition(":")[2])
    if message.startswith("The data-root upgrade could not be completed: "):
        detail = message.partition(": ")[2]
        return (
            "数据目录升级未能完成，原始数据保持不变；请关闭其他使用此目录的程序后重试。"
            "原因：" + (ERROR_TRANSLATIONS.get(detail) or detail)
        )
    if message.startswith("The interrupted upgrade could not be recovered: "):
        detail = message.partition(": ")[2]
        return (
            "上次中断的升级无法自动恢复，请从备份恢复数据目录后再打开。"
            "原因：" + (ERROR_TRANSLATIONS.get(detail) or detail)
        )
    return message


def confirm(parent, title: str, message: str) -> bool:
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Question)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    yes = dialog.addButton("是", QMessageBox.ButtonRole.YesRole)
    dialog.addButton("否", QMessageBox.ButtonRole.NoRole)
    dialog.exec()
    return dialog.clickedButton() is yes
