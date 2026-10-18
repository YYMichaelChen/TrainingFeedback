"""界面文案：稳定内部枚举/状态码到中文标签的映射，以及通用对话框工具。"""

from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QMessageBox

from ..domain.enums import AbortReason, DoseUnit, ExerciseResult, FeedbackValue, SessionStatus
from ..domain.execution_modes import alternating_explanation, execution_mode
from ..domain.plans import PlanPhase
from ..error_messages import ERROR_TRANSLATIONS as ERROR_TRANSLATIONS
from ..error_messages import LIBRARY_REASON_LABELS as LIBRARY_REASON_LABELS
from ..error_messages import OPERATION_ERRORS as OPERATION_ERRORS
from ..error_messages import user_message as user_message

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

MAIN_WINDOW_TEXT = {
    "page_open_failed": "「{name}」页面无法打开：{message}",
    "page_open_retry": "请保留当前数据并反馈以上信息；切换到其他页面后再回来会重试打开。",
}
GROUP_PLAN_TEXT = {
    "title": "训练计划 · 动作组", "new": "新建计划", "edit": "编辑草稿", "clone": "复制为独立计划",
    "upgrade": "升级所选计划",
    "activate": "预览并启用", "import": "导入计划文件…", "export": "导出计划资料…",
    "name": "计划名称", "purpose": "训练目的", "rationale": "调整说明",
    "change_description": "变更说明", "base_number": "三位计划编号",
    "clone_name_prompt": "输入独立计划名称", "clone_base_prompt": "输入未使用的三位编号（001–999）",
    "upgrade_preview": "将以 {code} 保存升级草稿。是否保存？",
    "draft_preview": "将以 {code} 保存草稿。是否保存？",
    "select_detail": "在左侧选择动作查看指导，或选择动作组查看训练安排。",
    "search_exercises": "搜索动作名称或体位",
    "choose_multiple_exercises": "至少选择一个动作；所选动作会以未完成处方加入计划。",
    "action": "独立动作", "group": "动作组", "add_action": "添加动作", "add_group": "添加动作组",
    "add_member": "添加成员", "edit_item": "编辑所选项", "remove": "移除所选项",
    "member": "成员", "set_order": "第几组",
    "up": "上移", "down": "下移", "move_member": "移至另一动作组…",
    "choose": "选择动作", "phase": "训练阶段", "note": "原始备注",
    "sets": "逐组剂量（动作组内为每轮剂量）", "value": "数值", "unit": "单位",
    "per_side": "每侧", "set_rest": "组间休息秒", "add_set": "添加剂量组",
    "remove_set": "删除剂量组", "fill_equal_sets": "按所选组填充相同剂量",
    "fill_equal_sets_confirm": (
        "这会覆盖其他组的剂量、单位、每侧和备注。若所选组有适用的组间休息，"
        "也会覆盖其他适用组的休息；所选组休息不适用时，保留其他组休息。继续吗？"
    ),
    "member_rest": "成员后休息秒", "side_rest": "换侧休息秒", "round_rest": "轮间休息秒",
    "exit_rest": "动作结束后休息（秒）", "first_side": "先做哪一侧", "rounds": "轮数",
    "execution_mode": "执行方式", "alternating_start": "每组先到哪一侧",
    "sequence": "换侧顺序", "transition": "体位 / 支撑转换说明", "group_name": "动作组名称",
    "none": "不适用", "left": "左侧", "right": "右侧",
    "member_each_side": "逐个成员完成", "same_side_then_switch": "每轮先同侧序列再换侧",
    "all_rounds_then_switch": "先一侧全部轮次再换侧", "save": "保存草稿", "error": "无法完成操作",
    "preview": "完整计划、差异与执行顺序", "confirm": "确认启用当前计划及列出的未审核指导",
    "unreviewed": "未审核指导", "diff": "变更明细", "new_revision": "新计划或新版本",
    "dissolve": "移除后只剩一个成员。明确拆散这个动作组？请先将轮数设为 1。",
    "remove_confirm": "确定移除所选计划项？保存后生效。", "exported": "计划资料已导出到：",
    "no_plans": "暂无计划", "json_filter": "JSON 文件 (*.json)",
    "empty_revision_hint": "暂无计划修订。可新建计划，或导入计划文件。",
    "images_tab": "动作示意图",
    "rest_seconds": "休息 {value} 秒",
    "select_destination": "选择目标", "expanded": "执行顺序（每行完成一个成员的全部组）",
    "preview_truncated": "预览仅显示前 300 个执行位置；完整处方及轮数保留。",
    "before": "原值", "after": "新值", "removed": "已移除", "added": "新增",
    "item_id": "条目身份", "kind": "类型", "order": "顺序", "members": "成员",
    "days": "动作列表", "items": "计划动作", "content": "内容引用", "classification": "动作分类",
    "exercise": "动作身份", "exercise_name": "动作名称", "source": "来源",
    "id": "编号", "family_key": "动作族", "variant_role": "族内角色",
    "variant_order": "族内顺序", "parent_exercise_key": "父动作",
    "starting_position_class": "起始体位", "target_plan_name": "目标计划", "group_id": "动作组身份",
    "rest_after_set_seconds": "组间休息秒", "rest_after_member_seconds": "成员后休息秒",
    "rest_after_action_seconds": "动作后休息秒", "rest_after_group_seconds": "动作组后休息秒",
    "rest_between_sides_seconds": "换侧休息秒", "rest_between_rounds_seconds": "轮间休息秒",
    "round_count": "轮数", "side_sequence": "换侧顺序", "unknown": "未知 / 不适用",
    "yes": "是", "no": "否",
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
    "start": "预览并开始训练…", "resume": "恢复未完成训练", "start_preview": "确认计划与指导",
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
    if execution_mode(row["action"]) == "alternating":
        return "左右交替（每组连续完成）"
    if row.get("dose_scope") == "per_side_aggregate":
        return EXECUTION_TEXT["per_side_aggregate"]
    return EXECUTION_TEXT.get(row["side"], EXECUTION_TEXT["both"])


def seconds_text(value):
    return "未知（未记录）" if value is None else f"{value:g}"


def occurrence_prescription(row):
    lines = [EXECUTION_TEXT["prescription"]]
    for dose in sorted(row["action"]["sets"], key=lambda item: item["order"]):
        if execution_mode(row["action"]) == "alternating":
            lines.append(f"第 {dose['order']} 组：" + alternating_explanation(row["action"], dose))
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
        if dose.get("recording_scope") == "total":
            side = "交替总次数（实际左右次数及起始侧未记录）"
        order = dose.get("planned_set_order", dose["order"])
        lines.append(f"{EXECUTION_TEXT['performed']}第 {order} 组：{value} "
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
LIBRARY_TEXT = {
    "removal": "移除与恢复审核",
    "parent_missing": "（保留的父动作身份，当前目录缺项）",
    "removed": "已移除／发行方撤回",
    "close": "关闭",
    "title": "动作库", "search": "按名称或别名搜索", "all_positions": "全部起始体位",
    "gallery_count": "共 {count} 个动作 · 点击卡片查看指导",
    "loading": "正在打开动作库…",
    "load_failed": "动作库无法载入：{message}\n请保留当前数据并反馈以上信息。",
    "back_to_gallery": "← 返回动作库", "batch_mode": "批量选择",
    "standalone": "独立动作", "name": "动作 / 动作族", "source": "来源", "position": "起始体位",
    "readiness": "图片资格", "review": "审核", "enabled": "启用状态", "bundled": "程序内置",
    "custom": "自定义", "ready": "可用", "draft": "草稿", "checking": "校验中…", "none": "无",
    "details": "完整指导", "images_tab": "动作示意图",
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
    return mapping.get(value, mapping.get(str(value), f"未知选项（标识：{value}）"))


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




def confirm(parent, title: str, message: str) -> bool:
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Question)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    yes = dialog.addButton("是", QMessageBox.ButtonRole.YesRole)
    dialog.addButton("否", QMessageBox.ButtonRole.NoRole)
    dialog.exec()
    return dialog.clickedButton() is yes
