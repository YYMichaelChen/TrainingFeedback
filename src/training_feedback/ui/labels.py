"""界面文案：稳定内部枚举/状态码到中文标签的映射，以及通用对话框工具。"""

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

GUIDANCE_STATUS_LABELS = {
    "draft": "草稿",
    "pending_review": "待审核",
    "approved": "已批准",
    "active": "已启用",
    "rejected": "已拒绝",
    "missing": "缺失",
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
    "active": "当前版本",
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
    "An open or paused session already exists.": "已经存在进行中或已暂停的训练。",
    "An active plan revision is required to start training.": "开始训练前必须先启用计划版本。",
    "A plan day must be selected before starting training.": "开始训练前必须选择训练日。",
    "The selected plan day was not found.": "没有找到所选训练日。",
    "The session changed before it could be resumed.": "训练状态已发生变化，请重新打开训练。",
    "The session changed before it could be updated.": "训练状态已发生变化，请刷新后重试。",
    "Guidance revision cannot be changed after activation.": "动作指导启用后不能原地修改。",
    "Guidance revision must be pending review before approval.": "动作指导必须先提交审核才能批准。",
    "Guidance revision is already approved.": "该动作指导已经批准过了。",
    "No open or paused session was found.": "没有找到进行中或已暂停的训练。",
    "Only an open or paused session can record results.": "只有进行中或已暂停的训练才能记录结果。",
    "A recorded action result cannot be changed.": "已记录的动作结果不能在普通训练流程中修改。",
    "Only an open or paused session can finish.": "只有进行中或已暂停的训练才能完成。",
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
    "Complete guidance and explicit user approval are required.": (
        "请先补全动作指导内容，并明确批准该版本后再启用。"
    ),
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
    "Guidance revision was not found.": "没有找到指定的动作指导版本。",
    "No reviewable guidance revision is selected.": "请选择一个可复核的动作指导版本。",
    "Reviewer type and source are required.": "审核人类型和来源不能为空。",
    "Explicit user approval is required.": "必须明确批准。",
    "Review time is required.": "审核时间不能为空。",
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
    "The data root requires a newer version of TrainingFeedback.": (
        "该数据目录由更新版本的应用创建，请升级应用后再打开。"
    ),
    "The database requires a newer version of TrainingFeedback.": (
        "该数据库由更新版本的应用创建，请升级应用后再打开。"
    ),
    "The data-root configuration belongs to another application.": "所选目录的配置属于其他应用。",
    "The selected path is not a directory.": "所选路径不是目录。",
    "The data root does not contain its database.": "所选数据目录缺少数据库文件。",
    "The TrainingFeedback database is invalid.": "数据目录中的数据库无效或已损坏。",
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


def user_message(message: str) -> str:
    translated = ERROR_TRANSLATIONS.get(message)
    if translated is not None:
        return translated
    if message.startswith("Exercise ") and message.endswith(" was not found."):
        return "没有找到指定的训练动作。"
    if message.startswith("Plan revision cannot be activated:"):
        return "计划版本无法启用：" + message.partition(":")[2]
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
