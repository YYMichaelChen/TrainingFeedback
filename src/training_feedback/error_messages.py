"""Chinese presentation of errors; no Qt, data access or validation rules."""

import errno
import json
import logging
import re
import sqlite3

# Known failures of client operations; unexpected programmer exceptions are not
# swallowed here. The UI presents these after the service has unwound its work.
OPERATION_ERRORS = (ValueError, OSError, sqlite3.Error)
_last_diagnostic = "尚无未识别错误诊断。"


def latest_diagnostic():
    return _last_diagnostic


def issue_text(issue):
    labels = {"plan": "计划", "days": "动作列表", "items": "动作", "members": "成员",
              "sets": "剂量组", "value": "数值", "unit": "单位", "name": "名称",
              "purpose": "训练目的", "first_side": "先做哪一侧", "round_count": "轮数",
              "requested_base_number": "复制计划编号",
              "exercise": "动作身份", "content": "内容身份", "source": "来源引用"}
    parts = [str(part + 1) if isinstance(part, int)
             else labels.get(part, FIELD_LABELS.get(part, part)) for part in issue.path]
    reasons = {"number": "请填写有限的非负数；轮数须为正整数，空白仍表示未知",
               "format": "请使用 UTF-8 的计划 JSON v5；本产品 v4 可转换，"
                         "训练证据及其它版本不能导入",
               "required": "尚未填写此必需字段", "orders": "顺序须为不重复的正整数",
               "identity": "条目标识重复，请为不同条目使用不同标识",
               "schema.type": "字段类型不符或尚未填写",
               "schema.pattern": "尚未填写或文本格式不符",
               "schema.minItems": "条目数量不足，请补齐动作、成员或剂量组",
               "schema.enum": "尚未选择有效选项，请按格式说明填写",
               "schema.minimum": "数值小于允许下限",
               "schema.additionalProperties": "存在当前格式不接受的字段，请对照格式说明删除",
               "schema.const": "字段取值与当前格式不符",
               "schema.oneOf": "动作结构不完整，请对照格式说明补齐",
               "schema.not": "该字段不适用于当前操作，请对照格式说明修正"}
    reason = user_message(issue.detail) if issue.code == "rule" else reasons.get(
        issue.code, "字段结构或取值不符合格式要求，请对照当前格式说明修正")
    if issue.code.startswith("content."):
        code = issue.code.removeprefix("content.")
        reason = "动作「" + issue.detail + "」：" + LIBRARY_REASON_LABELS.get(
            code, "内容不可用（" + code + "）") + "；请到动作库处理后重新预览。"
    path = "/".join(map(str, issue.path))
    return ((" → ".join(parts) or "计划文件") + "：" + reason
            + (f"\n字段路径：{path}" if path else ""))

LIBRARY_REASON_LABELS = {
    "disabled": "未启用；仅阻止新开始，历史与暂停训练仍保留",
    "incomplete_text": "指导文字不完整", "invalid_images": "缺少有效必需示意图",
    "removed":
        "已移出可用目录", "missing": "图片未提供", "unavailable": "路径、文件或哈希不可用",
    "hash_mismatch": "图片哈希不一致", "undecodable": "图片无法解码",
    "placeholder": "占位图片不能作为动作示意图",
}

ERROR_TRANSLATIONS = {
    "Only plan format version 5 is accepted.": "请使用当前计划格式 v5；v4 文件请通过导入入口转换。",
    "Choose an execution mode.": "请选择整体完成、分侧完成或左右交替。",
    "Alternating work requires a starting rule for every set.":
        "请选择每组先左、先右或任选；未选择不能代替任选。",
    "Alternating work requires reps.": "左右交替目前仅支持“次”，请修改此组单位；原输入仍保留。",
    "Alternating reps must be non-negative integers.":
        "左右交替次数须为有限的非负整数；空白不是零。",
    "Only alternating work has an alternating starting rule.": "仅左右交替可指定每组起始规则。",
    "Dose convention conflicts with execution mode.":
        "计量口径与执行方式冲突：整体使用整体剂量，分侧使用每侧剂量。",
    "An unfinished historical upgrade is unsupported. Create a new empty "
    "data root; the original root and files are preserved.":
        "此数据目录有未完成的历史升级，当前版本不再续做。请新建空数据目录；原目录和文件已保留。",
    "An unfinished historical reset is unsupported. Create a new empty "
    "data root; the original root and files are preserved.":
        "此数据目录有未完成的历史重置，当前版本不再续做。请新建空数据目录；原目录和文件已保留。",
    "This root has interrupted uninstall cleanup. Reinstall the current program "
    "and retry cleanup; the remaining files are preserved.":
        "此目录有未完成的卸载数据清理。请重新安装当前程序后重试清理；剩余文件已保留。",
    "Only plan format version 4 is accepted.":
        "此计划文件不是当前支持的格式。请使用当前版本导出的计划文件（格式版本 4）。",
    "The displayed plan revision changed.": "当前草稿已被修改，请重新打开后核对。",
    "A plan base number must be between 001 and 999.":
        "计划编号必须是 001 至 999 的整数。",
    "That plan base number is already in use.": "这个计划编号已经使用，请输入其他编号。",
    "A plan with this name already exists.": "这个计划名称已经使用，请输入其他名称。",
    "An unchanged copy cannot be saved as a new upgrade.": (
        "计划内容没有变化，不能另存为新升级版本。"
    ),
    "The active plan changed; reopen the upgrade draft.": (
        "当前启用计划已改变，请重新打开升级草稿。"
    ),
    "Only the latest active revision can be upgraded.":
        "只能升级当前最新的启用计划。",
    "An upgrade draft already exists; reopen it to continue.": (
        "已有该计划的升级草稿，请打开草稿继续编辑。"
    ),
    "The activation preview changed. Review it again.":
        "预览后计划或审核状态已变化，请重新查看并确认。",
    "Plan item identities must be unique throughout the revision.":
        "计划内的条目身份不能重复。",
    "The final set must use boundary rest, not set rest.":
        "最后一组的组间休息应为零；请填写相应换侧、成员或退出休息。",
    "Unilateral work requires an explicit first side.":
        "每侧训练需明确先做左侧还是右侧。",
    "Bilateral work has no side or side-switch rest.":
        "非每侧训练不能设置起始侧或换侧休息。",
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
    "Removing this member requires explicit group dissolution.":
        "移除此成员需要明确拆散动作组。",
    "Keep two members or explicitly dissolve the source group first.":
        "来源动作组需保留至少两个成员，或先明确拆散。",
    "Keep two members or remove/dissolve the group in the plan tree.":
        "请保留至少两个成员，或在计划树中移除、拆散动作组。",
    "Explicit confirmation is required.": "请明确确认本次操作。",
    "Select at least one content revision.": "请选择至少一个动作。",
    "The displayed content changed.": "所显示的内容已变化，请刷新后重新核对。",
    "The displayed review changed.": "审核记录已变化，请刷新后重新核对。",
    "The selected content changed; refresh the target.":
        "使用内容已变化，请核对后重试。",
    "Select one content revision per exercise.": "同一动作只能选定一个使用内容。",
    "Duplicate review targets are not allowed.": "请勿重复选择同一审核内容。",
    "Exercise is not enabled.": "该动作尚未启用。",
    "Unknown exercise identity.": "找不到指定的动作身份。",
    "Image is unavailable or invalid.": "图片不可用或校验失败。",
    "Image bytes cannot be decoded.": "所选文件无法解码为有效图片。",
    "A real external reviewer type is required.": "请选择实际外部审核者类型。",
    "Review source and note must be text.": "请填写真实审核来源，备注需为文本。",
    "Repair unavailable illustrations before review.":
        "记录审核前请修复不可用的示意图。",
    "Withdraw the prior review before recording another.":
        "请先撤销已有审核，再记录新的审核。",
    "There is no current review to withdraw.": "没有可撤销的当前审核。",
    "Names and aliases must be distinct.": "名称与别名不能重复。",
    "A name or alias belongs to another exercise.": "名称或别名已属于另一个动作。",
    "Unknown exercise family.": "找不到指定动作族。",
    "Exercise parent must be in the same family.": "父动作必须存在且属于同一动作族。",
    "Exercise family parent links cannot form a cycle.":
        "父动作关系不能形成循环。",
    "An exercise cannot be its own parent.": "动作不能以自己为父动作。",
    "Standalone exercises have no family or parent.":
        "独立动作不能指定动作族或父动作。",
    "A base exercise cannot have a parent.": "基础动作不能指定父动作。",
    "An open or paused session already exists.": "已经存在进行中或已暂停的训练。",
    "An active plan revision is required to start training.":
        "开始训练前必须先启用计划版本。",
    "A plan day must be selected before starting training.":
        "开始训练前必须选择计划。",
    "The selected plan day was not found.": "没有找到所选计划的动作列表。",
    "The session changed before it could be resumed.":
        "训练状态已发生变化，请重新打开训练。",
    "The session changed before it could be updated.":
        "训练状态已发生变化，请刷新后重试。",
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
    "Only an open or paused session can record results.":
        "只有进行中或已暂停的训练才能记录结果。",
    "A recorded action result cannot be changed.":
        "已记录的动作结果不能在普通训练流程中修改。",
    "Only an open or paused session can finish.": "只有进行中或已暂停的训练才能完成。",
    "Only an open or paused session can retract results.":
        "训练已结束，不能撤回动作结果。",
    "Select a recorded action to retract.": "请选择一个已记录结果的动作。",
    "Every exercise must have a result before finishing.":
        "完成训练前必须为每个动作记录结果。",
    "An abort reason is required.": "中止训练必须选择原因。",
    "Actual dose is required for exceeded or partial results.": (
        "超额或部分完成时必须填写实际剂量。"
    ),
    "This session is not eligible for next-day feedback.":
        "这次训练目前不符合填写次日反馈的条件。",
    "Next-day feedback has already been submitted.": "这次训练的次日反馈已经提交。",
    "Feedback must be submitted before its note is corrected.":
        "提交反馈后才能修正备注。",
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
    "The canonical name and aliases must be distinct.":
        "标准名称与别名不能相同。",
    "The canonical name or alias is already in use.":
        "该标准名称或别名已被其他动作使用。",
    "Exercise was not found.": "没有找到指定的训练动作。",
    "Select at least one guidance revision to review.":
        "请至少选择一个要复核的动作。",
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
    "External plan must contain at least one day.": "外部计划必须包含动作列表。",
    "External rationale must contain text.": "外部调整理由不能为空。",
    "The selected path is not an empty directory.":
        "所选路径不是空目录，无法在此创建数据目录。",
    "The selected directory is not empty.": "所选目录不是空目录，无法在此创建数据目录。",
    "This is already a data root. Open it explicitly.": (
        "该目录已是有效数据目录，请选择「打开已有数据目录」并直接选中它。"
    ),
    "Choose one valid Windows directory name.":
        "请输入单个有效的 Windows 目录名称。",
    "Choose an existing parent directory.": "请选择已存在的父目录。",
    "The directory is not a TrainingFeedback data root.":
        "所选目录不是训练反馈数据目录。",
    "The data-root metadata is incomplete or invalid.":
        "所选目录的数据信息不完整或已损坏。",
    "The data-root metadata cannot be read.":
        "所选目录的标记或配置文件无法读取，可能已损坏。",
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
    "The data-root configuration belongs to another application.":
        "所选目录的配置属于其他应用。",
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
    "A backup destination cannot be inside the source data root.":
        "备份目录不能位于数据目录内部。",
    "The backup destination must be empty.": "备份目录必须是空目录。",
    "Cannot create the backup destination.": "无法创建备份目录，请检查磁盘权限。",
    "The data-root backup could not be completed.":
        "备份未能完成，已清理不完整副本。",
}


ERROR_TRANSLATIONS.update({
    "An abort reason is required.": "请明确选择一个中止原因。",
    "An unfinished session already exists. Resume it first.":
        "已有未结束训练，请先恢复并处理。",
    "Select a day from the displayed plan revision.": "请选择当前计划版本。",
    "The start preview changed. Review it again.":
        "开始训练的依据已变化，请重新预览。",
    "The session changed. Reload the displayed session.":
        "训练记录已变化，请重新载入已保存状态。",
    "Only an open session accepts this action.": "只有进行中的训练可以执行此操作。",
    "Record only the displayed occurrence.": "请在当前显示的训练位置记录结果。",
    "This occurrence already has a saved result.":
        "当前训练位置已保存结果，请先明确撤回。",
    "The current occurrence is not in an action group.":
        "当前是独立动作，不能按整轮记录。",
    "This round has no unrecorded occurrences.": "当前轮次没有尚未记录的成员。",
    "The round preview changed. Review it again.": "本轮完成范围已变化，请重新预览。",
    "Every occurrence needs a saved result before finishing.":
        "请为每个训练位置保存结果后再完成训练。",
    "Actual dose must be finite and non-negative.": "实际剂量必须是有限的非负数字。",
    "Actual dose cannot be unknown; free work needs an explanation.":
        "请填写实际剂量；自由剂量不填数字时，必须填写具体说明。",
    "Actual side must match this occurrence; record the other side there.":
        "实际剂量只能属于当前侧；另一侧请在对应训练位置记录。",
    "This batch was already retracted or changed.":
        "此批次已撤回或变化，请重新载入。",
    "Retract this result using its complete batch.":
        "此结果属于整轮批次，请撤回该完整批次。",
    "This occurrence has no saved result.": "当前训练位置尚未保存结果。",
    "The note changed. Reload the displayed session.":
        "备注已变化，请重新载入后再修正。",
    "Only terminal session notes can be corrected.":
        "只有已结束训练的备注可以审计式修正。",
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
    "preview":
        "预览全部影响", "submit": "提交申请", "close": "关闭", "error": "操作未完成",
    "confirm_request": "我已查看全部动作与引用影响，确认提交此申请",
    "confirm_decision": "我已查看当前范围和影响，确认执行所选决定",
    "consequence": "移除后禁止新用，保留计划、图片与历史；未结束训练可继续。恢复须重新启用，"
                   "受影响计划须另行编辑并确认新版本。变体不会连带移除。",
    "plans": "引用计划", "groups": "引用组合与成员", "sessions": "引用训练",
    "reviews": "指导审核记录", "variants": "依赖变体", "exports": "已有导出",
    "draft":
        "草稿", "active": "活动", "superseded": "已被替代", "open": "进行中",
    "paused":
        "暂停", "completed": "完成", "partial": "部分完成", "aborted": "已中止",
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
    "button_applied":
        "应用已批准决定", "button_rejected": "驳回", "button_cancelled": "取消申请",
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
    "Repair current content and images before restoration.":
        "请先补全当前内容并修复图片后再恢复。",
    "A decision source and a text note are required.":
        "请填写真实决定来源，备注可留空。",
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
    "The data-root lock path is invalid.":
        "数据目录的锁文件路径无效，请不要手动改动数据目录。",
    "There is not enough free space for a recoverable upgrade.":
        "磁盘剩余空间不足，无法安全升级数据目录；请释放空间后重试。",
    "Upgrade resources cannot contain linked paths.":
        "数据目录中包含链接路径，无法安全升级；请移除链接后重试。",
    "An upgrade resource is not a regular file.":
        "数据目录中存在非常规文件，无法安全升级。",
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
    "A guidance revision was not converted.":
        "有动作指导未被升级收录，请从备份恢复后再打开。",
    "An unfinished session has no recorded prescription.":
        "升级后的未完结训练缺少处方记录，请从备份恢复后再打开。",
})


# Additional literals found by the 2026-10-17 source inventory. Keep the exact
# internal strings as keys; translate only at presentation boundaries.
ERROR_TRANSLATIONS.update({
    "A confirmed object could not be deleted.": "无法删除已确认的文件或目录。",
    "A distinct plan name and unused base number are required.":
        "请填写不同的计划名称，并选择尚未使用的计划编号。",
    "A drive root cannot be a program directory.":
        "不能将磁盘根目录用作程序安装目录。",
    "A group requires at least two members.": "动作组至少需要两个成员，请添加动作。",
    "A plan requires at least one day.": "计划至少需要一个动作列表。",
    "A program-directory parent is not a directory.":
        "程序目录的上级路径不是文件夹。",
    "A revision code must be assigned for an existing plan.":
        "已有计划的新版本缺少版本编号。",
    "A selected file is in use or access is denied.":
        "所选文件正在使用中，或没有访问权限。",
    "A selected object changed its type.": "所选文件或目录的类型已变化，请重新选择。",
    "A session must contain at least one action result.":
        "训练记录至少需要一个动作结果。",
    "A stable key must be a non-empty portable identifier.":
        "条目编号不能为空，且只能使用允许的字符。",
    "Abort notes must be text.": "中止训练的备注必须是文本。",
    "Actual dose notes must be text.": "实际剂量备注必须是文本。",
    "Actual dose requires value, unit, explicit side and note.":
        "实际剂量信息不完整，请填写数值、单位、明确的侧别和备注字段。",
    "Aggregate actual dose requires an explicit per-side choice.":
        "填写汇总实际剂量时，必须明确选择是否按每侧记录。",
    "All plan base numbers 001–999 are in use.":
        "计划编号 001 至 999 已全部使用，无法新建计划。",
    "All sets in one action must use the same unit.":
        "同一动作的所有剂量组必须使用相同单位。",
    "An existing cleanup must be resolved first.": "请先处理尚未完成的数据清理。",
    "An existing database has no schema version.": "数据库缺少格式版本信息。",
    "An override cannot change exercise identity.":
        "覆盖动作内容时不能更改动作身份，请另建动作。",
    "An upgrade draft for this plan already exists; open it to continue.":
        "该计划已有升级草稿，请打开已有草稿继续编辑。",
    "At least one training target is required.": "至少需要选择一个训练动作。",
    "Available images require a byte hash.": "可用图片缺少文件校验值。",
    "Available images require unique paths.": "可用图片的文件路径不能重复。",
    "Batch does not belong to this session.": "这批结果不属于当前训练。",
    "Bilateral work cannot prescribe side-switch rest.":
        "非每侧训练没有换侧休息，请将换侧休息明确填为 0。",
    "Bilateral work has no first side.": "非每侧训练不需要起始侧，请选择“不适用”。",
    "Cannot determine protected system directories; retain data.":
        "无法确认系统目录边界，已停止清理并保留数据。",
    "Catalog assets must live under images/.":
        "内置动作图片必须放在 images 子目录内。",
    "Catalog build destination must be empty.": "生成内置动作库的目标目录必须为空。",
    "Catalog cannot contain user review or custom state.":
        "内置动作库不能包含个人审核或自定义状态。",
    "Catalog contains an invalid illustration.": "内置动作库包含无效示意图。",
    "Catalog content hash does not match.": "内置动作内容的校验值不匹配。",
    "Catalog content identity does not match.": "内置动作内容身份不匹配。",
    "Catalog content inventory does not match.": "内置动作内容与清单不一致。",
    "Catalog database is corrupt.": "内置动作库文件已损坏，请重新安装程序。",
    "Catalog database metadata does not match.": "内置动作库的版本信息不匹配。",
    "Catalog file inventory does not match.": "内置动作库的文件与清单不一致。",
    "Catalog images must be inside images/.":
        "内置动作图片必须位于 images 子目录内。",
    "Catalog resource size does not match.": "内置动作资源的文件大小不匹配。",
    "Changing aggregate dose scope requires an explicitly replaced action.":
        "如需改变汇总剂量的记录范围，请明确替换为新的动作条目。",
    "Choose a program directory, not a file.": "请选择程序安装文件夹，不能选择文件。",
    "Choose a valid data-root location.": "请选择有效的数据目录位置。",
    "Choose an absolute local program directory.":
        "请选择本机程序安装目录的完整路径。",
    "Choose another destination day.": "请选择不同的目标动作列表。",
    "Choose another destination group.": "请选择另一个目标动作组。",
    "Cleanup completion has no marker evidence.":
        "清理完成状态缺少对应记录，无法确认已完成。",
    "Cleanup intent is invalid.": "清理操作记录无效，已停止清理。",
    "Cleanup inventory contains a reparse point.":
        "清理清单包含链接路径，无法安全清理。",
    "Cleanup marker identity is invalid.": "清理标记身份无效，已停止清理。",
    "Cleanup object identity is invalid.": "待清理文件的身份信息无效。",
    "Cleanup progress is invalid.": "清理进度记录无效。",
    "Cleanup recovery state changed after confirmation.":
        "确认后清理恢复状态已变化，请重新核对。",
    "Cleanup root disappeared before its deletion was recorded.":
        "尚未记录删除完成时，数据目录已消失，无法确认清理结果。",
    "Cleanup root identity is missing.": "清理记录缺少数据目录身份。",
    "Confirmed remaining objects disappeared unexpectedly.":
        "已确认的剩余文件意外消失，清理已停止。",
    "Content aliases must be text.": "动作别名必须是文本。",
    "Content became ineligible during plan activation.":
        "启用计划时动作内容已变为不可用，请重新核对。",
    "Content cannot contain review evidence.": "动作内容中不能直接包含审核记录。",
    "Content display fields must be text.": "动作的名称、说明等展示字段必须是文本。",
    "Content envelope fields do not match the catalog contract.":
        "动作内容字段不符合当前格式要求。",
    "Content identity does not match its bytes.": "动作内容与其身份校验信息不一致。",
    "Content requires a name.": "动作内容必须填写名称。",
    "Content requires an explicit image inventory.": "动作内容缺少明确的图片清单。",
    "Content version must be a positive integer.": "内容版本号必须是正整数。",
    "Custom content requires a name.": "自定义动作必须填写名称。",
    "Data deletion requires the Windows safety backend.":
        "当前环境不支持安全清理数据，请保留数据目录。",
    "Database recovery or active sidecars prevent data deletion.":
        "数据库正在使用或有待恢复文件，暂时不能清理数据。",
    "Database schema is newer than this application.":
        "数据库格式比当前程序新，请更新程序后再打开。",
    "Database schema is older than the supported window.":
        "数据库格式已超出当前支持范围，请新建空数据目录，保留原目录。",
    "Day name cannot be empty.": "动作列表名称不能为空。",
    "Duplicate catalog identity.": "内置动作库包含重复的内容身份。",
    "Each action requires at least one set.": "每个动作至少需要一组剂量，请添加剂量组。",
    "Each plan day requires at least one action.": "每个动作列表至少需要一个动作。",
    "Enablement must be Boolean.": "启用状态必须明确为启用或停用。",
    "Exact exercise content was not found.": "没有找到指定版本的动作内容。",
    "Exercise id must be an integer.": "动作编号必须是整数。",
    "Exercise image must be a filename inside exercise-images.":
        "动作图片必须是 exercise-images 目录内的文件。",
    "Exercise key and name conflict.": "动作编号与名称不一致，请重新选择动作。",
    "Exercise was withdrawn from the catalog.":
        "该动作已从内置目录撤回，不能用于新的安排。",
    "Existing content identity has different bytes.":
        "相同内容身份对应了不同文件，无法覆盖。",
    "Expected a SHA-256 content digest.": "缺少有效的 SHA-256 文件校验值。",
    "Expected bundled content.": "此操作需要选择内置动作内容。",
    "Feedback must contain exactly the derived training areas.":
        "反馈部位必须与本次训练对应的部位一致，请重新打开反馈页面。",
    "Files with multiple hard links cannot be deleted.":
        "文件有多个硬链接，无法安全删除。",
    "Free doses without a value require a note.":
        "自由剂量未填写数值时，必须填写剂量说明。",
    "Group and member item identities must be unique.":
        "动作组及其成员的条目身份不能重复。",
    "Group members require dose sets.": "动作至少需要一组剂量，请点击“添加剂量组”后填写。",
    "Image availability must be explicit.": "必须明确记录图片是否可用。",
    "Image binding does not match the content revision.":
        "图片与当前内容版本不匹配。",
    "Image format cannot be exported.": "此图片格式无法导出。",
    "Image is absent from the catalog manifest.": "内置动作清单中缺少这张图片。",
    "Image is outside the managed image directories.":
        "图片不在应用管理的图片目录内。",
    "Image requirement must be explicit.": "必须明确记录图片是否为必需内容。",
    "Installed program files changed; uninstall the program first.":
        "已安装的程序文件发生变化，请先卸载程序再安装。",
    "Invalid boundary rest.": "动作、成员或换侧休息必须填写有限且不小于 0 的秒数。",
    "Invalid catalog file inventory.": "内置动作库的文件清单无效。",
    "Invalid database integrity.": "数据库完整性检查未通过。",
    "Invalid database references.": "数据库存在无效的记录关联。",
    "Invalid exercise classification fields.": "动作分类字段无效。",
    "Invalid immutable catalog content.": "内置动作内容无效或已被修改。",
    "Invalid occurrence position.": "训练执行位置无效，请重新打开当前训练。",
    "Invalid schema version.": "数据库格式版本无效。",
    "Invalid set rest.": "组间休息必须填写有限且不小于 0 的秒数。",
    "Invalid variant role.": "动作的族内角色无效，请重新选择。",
    "Latest release is not a stable published release.":
        "最新发布记录不是已公开的稳定版本。",
    "Managed resource hash does not match.": "资源文件的校验值不匹配，文件可能已变化。",
    "Managed resource is unavailable.": "资源文件不可用，可能缺失或无法读取。",
    "Migrated aggregate work has no recorded first side.":
        "迁入的汇总记录没有起始侧信息，不能补作已知事实。",
    "Migration identity or dose scope cannot be changed implicitly.":
        "不能隐式更改迁入记录的身份或剂量范围。",
    "Migration provenance must match stored facts.":
        "迁入来源信息必须与已保存的记录一致。",
    "Missing images cannot claim a path or a byte hash.":
        "标记为缺失的图片不能同时填写路径或文件校验值。",
    "Missing incoming payload identity.": "缺少待安装程序的载荷身份信息。",
    "Missing installed uninstaller identity.": "缺少已安装卸载程序的身份信息。",
    "Network, device and relative paths are not supported.":
        "不支持网络路径、设备路径或相对路径。",
    "New custom images require a managed custom-image path.":
        "新增自定义图片必须保存在应用管理的自定义图片目录中。",
    "Numeric dose units require a value.": "选择次数、秒等数值单位后，必须填写剂量数值。",
    "Numeric dose values must be finite and non-negative.":
        "剂量必须是有限且不小于 0 的数字。",
    "Occurrence does not belong to this session.": "该执行位置不属于当前训练。",
    "Old and new program directories cannot overlap.":
        "新旧程序安装目录不能互相包含。",
    "One member must use one dose unit.": "同一动作的各组剂量必须使用相同单位。",
    "One member must use one per-side convention.":
        "同一动作的所有剂量组必须统一是否按每侧记录。",
    "One round cannot prescribe between-round rest.":
        "动作组只有一轮，没有轮间休息，请明确填为 0。",
    "Only draft revisions can be activated.": "只有草稿版本可以启用。",
    "Only draft revisions can be edited.": "只有草稿可以编辑，请先复制或创建升级草稿。",
    "Only result and feedback notes can be corrected.":
        "只能修正训练结果备注和次日反馈备注。",
    "Override images must be originals or managed local images.":
        "覆盖内容只能使用原有图片或应用管理的本地图片。",
    "Payload validation failed; installation is incomplete.":
        "安装文件校验失败，安装未完成。",
    "Pending reset recovery prevents data deletion.":
        "存在尚未处理的重置恢复记录，不能删除数据。",
    "Per-side flags must be Boolean.": "“每侧”必须明确选择是或否。",
    "Plan classification does not match the exact content revision.":
        "计划中的动作分类与所选内容版本不一致，请重新选择动作。",
    "Plan name cannot be empty.": "计划名称不能为空。",
    "Plan numbers must be finite.": "计划数值必须是有限数字，不能使用无穷大或 NaN。",
    "Plan revision was not found.": "没有找到指定的计划版本。",
    "Program files changed after preflight; stopped.":
        "预检查后程序文件发生变化，安装已停止。",
    "Program files must be ordinary files without hard links.":
        "程序文件必须是没有硬链接的普通文件。",
    "Program paths cannot contain links or reparse points.":
        "程序安装路径不能包含链接或重解析点。",
    "Read-only files cannot be safely removed.": "无法安全删除只读文件。",
    "Release URL is missing.": "发布记录缺少下载页面地址。",
    "Release URL is not trusted.": "发布记录中的地址不可信，已停止打开。",
    "Release details require an available release.":
        "没有可显示的发布详情，请重新检查更新。",
    "Release response is not an object.": "更新服务返回的数据结构无效。",
    "Release response is not valid JSON.": "更新服务返回的数据不是有效 JSON。",
    "Release response is too large.": "更新服务返回的数据过大。",
    "Release tag must start with v.": "发布标签格式无效，应以 v 开头。",
    "Release text fields are invalid.": "发布说明中的文本字段无效。",
    "Release version is missing.": "发布记录缺少版本号。",
    "Release version is not X.Y.Z.": "发布版本号格式无效，应为主版本.次版本.补丁版本。",
    "Remaining identities changed; cleanup stopped.":
        "剩余文件的身份已变化，清理已停止。",
    "Reparse points cannot be used for cleanup.": "不能通过链接路径清理数据。",
    "Resource path escapes its managed directory.": "资源路径超出了应用管理目录。",
    "Resource path must be portable and relative.": "资源路径必须是有效的相对路径。",
    "Rest seconds must be explicitly supplied.":
        "请填写休息秒数；不休息请明确填 0，空白不能当作 0。",
    "Rest seconds must be finite and non-negative.":
        "休息秒数必须是有限且不小于 0 的数字。",
    "Result notes must be text.": "训练结果备注必须是文本。",
    "Retained content hash does not match.": "保留内容的校验值不匹配。",
    "Review note must be text.": "审核备注必须是文本。",
    "Round count must be a positive integer.": "动作组轮数必须是大于 0 的整数。",
    "SQLite foreign keys could not be enabled.":
        "数据库关联约束无法启用，不能继续打开数据库。",
    "Select a content revision before enabling.":
        "启用动作前，请先选择使用的内容版本。",
    "Select one occurrence or one complete batch to retract.":
        "请选择一个执行结果或一整批结果进行撤回。",
    "Selected data does not belong to the current user.":
        "所选数据不属于当前系统用户，无法清理。",
    "Snapshot resource hash does not match.": "训练快照资源的校验值不匹配。",
    "System-directory boundaries could not be determined.":
        "无法确认系统目录边界，操作已停止。",
    "Target plan base code was not found.": "没有找到目标计划编号。",
    "Target plan was not found.": "没有找到目标计划。",
    "The catalog content changed; refresh the displayed target.":
        "动作库内容已变化，请刷新后重新选择。",
    "The cleanup record cannot certify completion.": "清理记录无法确认操作已完成。",
    "The cleanup recovery record is invalid; retain the remaining files.":
        "清理恢复记录无效，请保留剩余文件。",
    "The confirmed directory or files changed; no deletion.":
        "已确认的目录或文件发生变化，本次未执行删除。",
    "The confirmed root disappeared; no locator deletion.":
        "已确认的数据目录已消失，未删除目录位置记录。",
    "The current database is missing.": "当前数据目录缺少数据库文件。",
    "The database is invalid; retain this root.": "数据库无效，请保留此数据目录。",
    "The directory is not a TrainingFeedback root.":
        "此目录不是训练反馈的数据目录。",
    "The existing root lock is missing; data deletion is disabled.":
        "数据目录锁文件缺失，已禁用数据删除。",
    "The final member uses side, round or exit rest instead.":
        "最后一个成员之后使用换侧、轮间或动作组后休息；请将该成员后的休息填为 0。",
    "The installed program receipt is invalid.": "程序安装登记无效。",
    "The installed uninstaller is outside the program directory.":
        "卸载程序不在当前程序安装目录内。",
    "The installed uninstaller receipt is invalid.": "卸载程序登记无效。",
    "The locator changed after confirmation; no data was deleted.":
        "确认后数据目录位置记录发生变化，未删除任何数据。",
    "The locator changed; retain the remaining cleanup files.":
        "数据目录位置记录发生变化，请保留剩余清理文件。",
    "The locator is missing and cleanup completion is uncertain.":
        "数据目录位置记录缺失，无法确认清理是否完成。",
    "The plan content pin does not match its prescription.":
        "计划固定的动作内容与处方不匹配。",
    "The previous uninstaller identity is invalid.": "旧版卸载程序的身份无效。",
    "The program catalog could not be opened.":
        "无法打开程序内置动作库，请重新安装当前程序。",
    "The program directory is inside a data root.": "程序不能安装在训练数据目录内。",
    "The program directory is not writable.": "没有程序安装目录的写入权限。",
    "The program directory overlaps a protected or data directory.":
        "程序安装目录与受保护目录或训练数据目录重叠，请选择其他位置。",
    "The program ownership manifest is incomplete.": "程序文件归属清单不完整。",
    "The program ownership manifest is invalid.": "程序文件归属清单无效。",
    "The program path contains an invalid directory name.":
        "程序安装路径包含无效的目录名称。",
    "The review answer file could not be read.":
        "无法读取审核答复原件，请检查文件是否可访问。",
    "The review answer file could not be stored.":
        "无法保存审核答复原件，请检查磁盘空间和权限。",
    "The review answer file is too large to store.": "审核答复原件过大，无法保存。",
    "The root configuration belongs to another application.":
        "此数据目录的配置属于其他应用。",
    "The root metadata is incomplete.": "数据目录的基本信息不完整。",
    "The root model is unsupported or cleanup is incomplete.":
        "数据格式不受支持，或之前的清理尚未完成。",
    "The selected review answer file was not found.": "没有找到所选审核答复原件。",
    "The selected root is a dangerous directory.": "所选目录是不能清理的受保护位置。",
    "The selected root overlaps program, system or locator files.":
        "所选数据目录与程序、系统或目录位置记录重叠，无法清理。",
    "The source plan code is invalid.": "来源计划编号无效。",
    "The target plan has no active revision to upgrade.":
        "目标计划没有已启用版本，无法创建升级。",
    "The upgrade target base code does not match the selected plan.":
        "升级目标编号与所选计划不一致，请重新选择。",
    "The user home directory cannot be replaced by program files.":
        "不能用程序文件替换用户主目录。",
    "This directory has no valid TrainingFeedback program manifest.":
        "此目录没有有效的训练反馈程序文件清单。",
    "This program directory contains unrelated files. Preserve them and choose an empty "
    "directory, or explicitly uninstall the program first.":
        "此程序目录包含其他文件。请保留这些文件并选择空目录，或先明确卸载程序。",
    "This result cannot contain entered actual dose.":
        "此结果类型不能填写实际剂量。",
    "This root has not completed catalog-model conversion.":
        "此数据目录未完成动作库格式转换，当前程序无法打开。",
    "This side sequence requires all members to be per-side.":
        "当前换侧顺序要求所有成员按每侧记录，请统一勾选“每侧”或更换换侧顺序。",
    "Transition instructions must be text.": "体位／支撑转换说明必须是文本。",
    "Unanswered work has no result note to correct.":
        "尚未记录结果的训练动作没有可修正的结果备注。",
    "Unexpected catalog file.": "内置动作库包含清单之外的文件。",
    "Unexpected files remain; installation is incomplete.":
        "安装目录仍有未预期的文件，安装未完成。",
    "Unknown or unsupported data format; retain this root.":
        "数据格式未知或不受支持，请保留此数据目录。",
    "Unsupported catalog format.": "不支持此内置动作库格式。",
    "Unsupported database schema; retain this root.":
        "不支持此数据库格式，请保留数据目录。",
    "Unsupported dose unit.": "不支持此剂量单位，请重新选择。",
    "Unsupported plan action phase.": "不支持此训练阶段，请重新选择。",
    "Upgrade recovery state must be resolved before deleting this root.":
        "请先处理升级恢复状态，再清理此数据目录。",
    "Use an explicit Upgrade to add a revision to an existing plan.":
        "如需为已有计划增加版本，请使用“升级”操作。",
    "Variant order must be a positive integer.": "族内显示顺序必须是大于 0 的整数。",
    "Conversion evidence is immutable.": "迁入证据已固定，不能修改或删除。",
    "Conversion provenance is immutable.": "迁入来源记录已固定，不能修改。",
    "Lifecycle evidence is immutable.": "移除、恢复等操作的历史证据不能修改或删除。",
    "Only open sessions accept result changes.": "只有进行中的训练可以修改结果。",
    "Plan evidence is immutable.": "计划历史证据不能修改或删除。",
    "Published plan is immutable.": "已启用的计划不能直接修改，请创建升级草稿。",
    "Published plan revisions are immutable.": "已启用的计划版本不能修改或删除。",
    "Retained catalog evidence is immutable.": "已保留的动作内容证据不能修改或删除。",
    "Review events are immutable.": "审核事件不能直接修改或删除，请使用撤销审核操作。",
    "Session evidence is immutable.": "训练历史证据不能修改或删除。",
    "Session snapshot or terminal state is immutable.": "训练快照和已结束的训练状态不能修改。",
})


ACTIVATION_REASONS = {
    "was not found": "动作不存在",
    "is not enabled": "动作未启用",
    "has no guidance in use": "动作尚未投入使用",
    "has incomplete guidance in use": "动作的使用内容不完整",
}


def _activation_reasons(detail: str) -> str:
    """Translate each activation reason while retaining the action identifier."""
    reasons = []
    for exercise_id, reason in re.findall(r"Exercise (\d+) ([^.]+)\.", detail):
        translated = ACTIVATION_REASONS.get(reason) or user_message(reason)
        reasons.append(f"动作 {exercise_id} {translated}")
    return "；".join(reasons) if reasons else user_message(detail.strip())


FIELD_LABELS = {
    "execution_mode": "执行方式", "alternating_start": "每组先到哪一侧",
    "plan": "计划", "days": "动作列表", "items": "计划条目", "members": "动作组成员",
    "sets": "剂量组", "name": "名称", "purpose": "训练目的", "note": "备注",
    "value": "数值", "unit": "单位", "order": "顺序", "per_side": "每侧",
    "first_side": "起始侧", "round_count": "轮数", "side_sequence": "换侧顺序",
    "phase":
        "训练阶段", "transition": "体位／支撑转换说明", "exercise_name": "动作名称",
    "rest_after_set_seconds":
        "组间休息秒数", "rest_after_member_seconds": "成员后休息秒数",
    "rest_after_action_seconds":
        "动作后休息秒数", "rest_after_group_seconds": "动作组后休息秒数",
    "rest_between_sides_seconds":
        "换侧休息秒数", "rest_between_rounds_seconds": "轮间休息秒数",
    "schema": "格式标识", "schema_version": "格式版本", "intent": "计划用途",
    "rationale":
        "调整说明", "change_description": "变更说明", "target_base_number": "目标计划编号",
    "plan_code": "计划编号", "exercise": "动作引用", "classification": "动作分类",
    "content": "内容版本", "item_id": "条目编号", "kind": "条目类型",
    "source":
        "来源", "key": "标识", "id": "编号", "version": "版本", "sha256": "校验值",
}


def _field_path(path):
    parts = path.split("/") if isinstance(path, str) else path
    return " / ".join(
        f"第 {int(part) + 1} 项" if str(part).isdigit()
        else FIELD_LABELS.get(str(part), str(part)) for part in parts
    ) or "计划文件"


def _schema_reason(error):
    rule, expected = error.validator, error.validator_value
    if rule == "required" and isinstance(error.instance, dict):
        missing = [FIELD_LABELS.get(key, key) for key in expected if key not in error.instance]
        return "缺少必填字段：" + "、".join(missing)
    if rule == "type":
        types = {"object": "对象", "array": "列表", "string": "文本", "number": "数字",
                 "integer": "整数", "boolean": "是／否", "null": "空值"}
        values = expected if isinstance(expected, list) else [expected]
        return "字段类型应为：" + "或".join(types.get(value, value) for value in values)
    if rule in {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"}:
        operator = {"minimum": "不小于", "maximum": "不大于",
                    "exclusiveMinimum": "大于", "exclusiveMaximum": "小于"}[rule]
        return f"数值必须{operator} {expected}"
    if rule in {"minItems", "maxItems", "minLength", "maxLength"}:
        boundary = "至少" if rule.startswith("min") else "最多"
        unit = "项" if rule.endswith("Items") else "个字符"
        return f"此字段{boundary}需要 {expected} {unit}"
    return {
        "enum": "字段取值不在允许范围内，请重新选择或核对文件",
        "const": "字段值与当前格式要求不一致",
        "pattern": "文本格式不符合要求，请检查是否为空或包含不允许的字符",
        "additionalProperties": "包含当前格式不支持的字段",
        "uniqueItems": "列表中不能包含重复项",
        "anyOf": "动作或动作组结构不完整，请核对成员、剂量和必填字段",
        "oneOf": "动作或动作组结构不符合要求，请核对成员、剂量和必填字段",
        "not": "此处包含当前计划用途不允许的字段或值",
    }.get(rule, "字段不符合当前计划格式要求，请核对文件")


def _system_error(error):
    if isinstance(error, json.JSONDecodeError):
        return f"JSON 文件格式有误，请检查第 {error.lineno} 行、第 {error.colno} 列。"
    if isinstance(error, UnicodeError):
        return "文件文字编码无效，无法读取；请使用 UTF-8 编码的文件。"
    if isinstance(error, OSError):
        code = getattr(error, "winerror", None)
        windows = {2: "找不到指定文件", 3: "找不到指定路径", 5: "没有访问权限",
                   32: "文件正在被其他程序使用", 33: "文件已被锁定", 80: "文件已存在",
                   112: "磁盘空间不足", 183: "文件或目录已存在", 206: "路径或文件名过长",
                   995: "操作已取消", 10060: "网络连接超时", 10061: "网络连接被拒绝"}
        posix = {errno.ENOENT: "找不到指定文件或目录", errno.EACCES: "没有访问权限",
                 errno.EPERM: "没有执行此操作的权限", errno.EEXIST: "文件或目录已存在",
                 errno.ENOSPC: "磁盘空间不足", errno.EBUSY: "文件或设备正在使用中",
                 errno.EINVAL: "路径或操作参数无效", errno.EIO: "文件读写失败",
                 errno.ENOTDIR: "路径不是目录", errno.EISDIR: "所选路径是目录，不能作为文件使用",
                 errno.ENAMETOOLONG: "路径或文件名过长", errno.EROFS: "目标位置为只读",
                 errno.ETIMEDOUT: "连接超时", errno.ECONNREFUSED: "连接被拒绝"}
        reason = windows.get(code) if code is not None else posix.get(error.errno)
        if code is None and error.errno is None:
            return None  # Application-supplied OSError messages use the normal mapping.
        detail = reason or "系统无法完成文件或网络操作"
        detail += f"（系统错误码 {code if code is not None else error.errno}）。"
        for title, path in (("路径", error.filename), ("目标路径", error.filename2)):
            if path is not None:
                detail += f"\n{title}：{path}"
        return detail
    if isinstance(error, sqlite3.Error):
        code = getattr(error, "sqlite_errorcode", None)
        base = code & 255 if code is not None else None
        reason = {5: "数据库正在使用中，请关闭占用它的程序后重试。",
                  6: "数据库已锁定，请稍后重试。", 8: "数据库只读，无法保存。",
                  10: "数据库读写失败，请检查磁盘与权限。", 11: "数据库已损坏，无法继续操作。",
                  13: "磁盘空间不足，无法保存数据库。", 14: "无法打开数据库文件。",
                  19: "数据不符合保存约束，可能有重复记录或缺少关联内容。",
                  26: "文件不是有效的数据库。"}.get(base, "数据库操作未完成，请反馈错误信息。")
        return reason + (f"（数据库错误码 {code}）" if code is not None else "")
    if isinstance(error, KeyError):
        key = str(error.args[0]) if error.args else "未知字段"
        return "数据缺少必需字段：" + FIELD_LABELS.get(key, key)
    if isinstance(error, MemoryError):
        return "可用内存不足，无法完成此操作。请关闭不需要的程序后重试。"
    return None


def user_message(error: str | BaseException) -> str:
    """Translate errors only, never arbitrary user-authored names or notes."""
    global _last_diagnostic
    if hasattr(error, "issues"):
        return "存在待完善内容：\n" + "\n".join(issue_text(issue) for issue in error.issues)
    message = str(error)
    translated = ERROR_TRANSLATIONS.get(message)
    if translated is not None:
        return translated
    if isinstance(error, BaseException):
        translated = _system_error(error)
        if translated is not None:
            return translated
    if message.startswith(("Invalid plan v4 at ", "Invalid plan v5 at ")):
        path, _, detail = message[len("Invalid plan v4 at "):].partition(": ")
        cause = error.__cause__ if isinstance(error, BaseException) else None
        if cause is not None and hasattr(cause, "validator"):
            reason = _schema_reason(cause)
        else:
            missing = re.fullmatch(r"'([^']+)' is a required property", detail)
            reason = ("缺少必填字段：" + FIELD_LABELS.get(missing[1], missing[1]) if missing
                      else "字段类型、取值或结构不符合当前格式要求")
        return f"计划文件格式有误（格式版本 4）。\n位置：{_field_path(path)}\n原因：{reason}。"
    if message.startswith("Content is not eligible: "):
        return "当前内容不可用：" + "；".join(
            LIBRARY_REASON_LABELS.get(reason, f"内容状态异常（状态码：{reason}）")
            for reason in message.partition(": ")[2].split(", ")
        )
    if message.startswith("Exercise ") and message.endswith(" was not found."):
        return "没有找到指定的训练动作。"
    if message.startswith("Plan revision cannot be activated:"):
        return "计划版本无法启用：" + _activation_reasons(message.partition(":")[2])
    if message.startswith("The data-root upgrade could not be completed: "):
        detail = message.partition(": ")[2]
        return (
            "数据目录升级未能完成，原始数据保持不变；请关闭其他使用此目录的程序后重试。"
            "原因：" + user_message(detail)
        )
    if message.startswith("The interrupted upgrade could not be recovered: "):
        detail = message.partition(": ")[2]
        return (
            "上次中断的升级无法自动恢复，请从备份恢复数据目录后再打开。"
            "原因：" + user_message(detail)
        )
    ordered = re.fullmatch(r"(Set|Action|Day|Item|Member) orders must be (.+)\.", message)
    if ordered:
        label = {"Set": "剂量组", "Action": "动作", "Day": "动作列表",
                 "Item": "计划条目", "Member": "动作组成员"}[ordered[1]]
        rule = "不重复的正整数" if ordered[2] == "positive and unique" else "正整数"
        return f"{label}顺序必须是{rule}。"
    transition = re.fullmatch(r"Invalid session transition: (.+) -> (.+)\.", message)
    if transition:
        states = {"open": "进行中", "paused": "已暂停", "finished": "已完成",
                  "completed": "已完成", "aborted": "已中止"}
        return (f"不能将训练从“{states.get(transition[1], transition[1])}”"
                f"改为“{states.get(transition[2], transition[2])}”。")
    enum = re.fullmatch(r"(.+) is not a valid (\w+)", message, re.DOTALL)
    if enum:
        name = {"SideSequence": "换侧顺序", "StartingPosition": "起始体位", "DoseUnit": "剂量单位",
                "PlanPhase": "训练阶段", "ExerciseResult": "动作结果", "FeedbackValue": "反馈",
                "SessionStatus": "训练状态", "AbortReason": "中止原因"}.get(enum[2], "字段")
        return f"{name}的取值无效：{enum[1]}。请重新选择。"
    for prefix, chinese in (
        ("Plan numbers must be finite: ", "计划数值必须是有限数字，不能使用："),
        ("Application icon resource is unavailable: ",
         "程序图标文件不可用，请重新安装程序。路径："),
        ("Duplicate catalog classification: ", "内置动作分类重复，条目标识："),
        ("could not convert string to float: ", "此处必须填写数字，当前输入："),
    ):
        if message.startswith(prefix):
            return chinese + message[len(prefix):]
    inventory = re.fullmatch(
        r"Bundled image source inventory differs: missing=(.*), unexpected=(.*)", message, re.DOTALL
    )
    if inventory:
        return f"内置图片来源与清单不一致。\n缺失：{inventory[1]}\n清单外文件：{inventory[2]}"
    integer = re.fullmatch(r"invalid literal for int\(\) with base \d+: (.*)", message, re.DOTALL)
    if integer:
        return "此处必须填写整数，当前输入：" + integer[1]
    # Persisted cleanup reasons and third-party APIs may provide only text.
    system = re.fullmatch(r"\[(WinError|Errno) (\d+)\] (.*)", message, re.DOTALL)
    if system:
        code = int(system[2])
        exception = OSError(code if system[1] == "Errno" else None, "")
        if system[1] == "WinError":
            exception.winerror = code
        paths = system[3].partition(": ")[2]
        return _system_error(exception) + ("\n相关路径：" + paths if paths else "")
    if re.match(r"^[\s\d]*[\u4e00-\u9fff「“（]", message):
        return message  # Already-localized messages may quote user text verbatim.
    if not message.strip():
        return "操作未完成，程序未提供具体原因。请反馈当时进行的操作。"
    logging.getLogger(__name__).error("未识别的客户端错误：%s", message)
    _last_diagnostic = repr(error)
    return "操作未完成，遇到了未识别的错误。请在设置中复制最近错误诊断，并反馈当时进行的操作。"

