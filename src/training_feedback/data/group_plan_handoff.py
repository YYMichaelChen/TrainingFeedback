"""Portable v5 files and strict v4 conversion with retained bytes and provenance."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from .. import __version__
from ..application.library_workflow import LibraryTarget
from ..domain.catalog import ExerciseReference
from ..domain.execution_modes import alternating_explanation, execution_mode, upgrade_payload
from ..domain.group_plans import (
    EVIDENCE_SCHEMA_VERSION,
    continuous_plan_day,
    diff_plans,
    plan_actions,
    revision_code_for_change,
    validate_plan_payload,
)
from ..domain.plan_editing import PlanIssue, PlanIssues, payload_issues
from .bounded_files import FileTooLargeError, read_limited_bytes
from .catalog_resources import managed_path
from .conversion_repository import ConversionRepository
from .group_session_handoff import known
from .library_images import image_file_extension
from .plan_contract import plan_v4_schema
from .root_lock import RootMutationLease

MAX_PLAN_IMPORT_BYTES = 4 * 1024 * 1024
MAX_PLAN_JSON_DEPTH = 64
MAX_PLAN_JSON_VALUES = 50_000


def _strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Duplicate JSON keys are not allowed.")
            value[key] = item
        return value

    def nonfinite(value):
        raise ValueError("Plan numbers must be finite: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def _require_bounded_json(payload) -> None:
    stack = [(payload, 1)]
    values = 0
    while stack:
        value, depth = stack.pop()
        values += 1
        if values > MAX_PLAN_JSON_VALUES:
            raise ValueError("The plan file contains too many JSON values.")
        if depth > MAX_PLAN_JSON_DEPTH:
            raise ValueError("The plan file JSON is nested too deeply.")
        if isinstance(value, dict):
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)


@dataclass(frozen=True)
class PlanImportPreview:
    raw: bytes
    sha256: str
    payload: dict
    warnings: tuple
    target_token: str
    changes: tuple
    conversion_note: str = ""


class GroupPlanHandoff:
    def __init__(self, service, data_root):
        self.service = service
        self.root = Path(data_root)

    def import_file(self, source: Path):
        return self.import_preview(self.preview_file(source))

    def _parse(self, raw):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("导入失败，尚未保存计划。文件须使用 UTF-8 编码，"
                             "请另存后重新选择。") from None
        try:
            payload = _strict_json(text)
        except RecursionError:
            raise ValueError("The plan file JSON is nested too deeply.") from None
        except json.JSONDecodeError as exc:
            raise ValueError(f"导入失败，尚未保存计划。JSON 语法有误：第 {exc.lineno} 行、"
                             f"第 {exc.colno} 列，请检查引号、逗号和括号。") from None
        except ValueError as exc:
            from ..error_messages import user_message
            raise ValueError("导入失败，尚未保存计划。" + user_message(exc)) from None
        _require_bounded_json(payload)
        return text, payload

    def _check_import(self, payload):
        from ..domain.catalog import content_sha256
        if isinstance(payload, dict) and payload.get("schema_version") == 4:
            schema = plan_v4_schema()
            issues = payload_issues(payload, schema)
            if issues:
                raise PlanIssues(issues)
            validate_plan_payload(payload, schema)
            payload = upgrade_payload(payload)
        candidate, issues = self.service.input_issues(payload)
        state = None
        if isinstance(candidate, dict):
            source = candidate.get("source", {})
            if isinstance(source, dict):
                for field in ("session_id", "export_id"):
                    if field in source and (source[field] is None or type(source[field]) is int):
                        try:
                            self.service.repository.check_source({field: source[field]})
                        except ValueError as exc:
                            issues.append(PlanIssue("rule", ("source", field), detail=str(exc)))
        if not issues:
            try:
                if candidate["intent"] == "upgrade":
                    plan_id = self.service.repository.find_base_number(
                        candidate["target_base_number"])
                    if plan_id is None:
                        raise ValueError("Target plan base code was not found.")
                    active = self.service.repository.active(plan_id)
                    if active is None:
                        raise ValueError("The target plan has no active revision to upgrade.")
                    if self.service.upgrade_draft(active["id"]):
                        raise ValueError("An upgrade draft already exists; reopen it to continue.")
                    self.service._lineage(plan_id, candidate)
                    revision_code_for_change(active["base_number"], active["plan_code"],
                                              active["payload"]["plan"], candidate["plan"])
                    state = active
                elif self.service.repository.find_plan(candidate["plan"]["name"]) is not None:
                    raise ValueError("A plan with this name already exists.")
            except ValueError as exc:
                path = (("plan", "name") if str(exc) == "A plan with this name already exists."
                        else ("target_base_number",) if str(exc) in {
                            "Target plan base code was not found.",
                            "The target plan has no active revision to upgrade.",
                            "An upgrade draft already exists; reopen it to continue.",
                        } else ("plan",))
                issues.append(PlanIssue("rule", path, detail=str(exc)))
        if issues:
            raise PlanIssues(issues)
        warnings = []
        for _, _, action in plan_actions(candidate["plan"]):
            target = LibraryTarget(ExerciseReference(**action["exercise"]), action["content"])
            status = self.service.library.eligibility(target)
            reasons = list(status.reasons)
            if not self.service.library.user.state(target.exercise)["enabled"]:
                reasons.append("disabled")
            if reasons:
                warnings.append((action["exercise_name"], tuple(reasons)))
        return (candidate, tuple(warnings),
                content_sha256({"active": state, "warnings": warnings}),
                tuple(diff_plans(state["payload"]["plan"] if state else None, candidate["plan"])))

    def preview_file(self, source):
        try:
            raw = read_limited_bytes(Path(source), MAX_PLAN_IMPORT_BYTES)
        except FileTooLargeError:
            raise ValueError("The plan file is too large to import.") from None
        except OSError as exc:
            raise ValueError("The selected plan file could not be read.") from exc
        _text, payload = self._parse(raw)
        legacy = isinstance(payload, dict) and payload.get("schema_version") == 4
        payload, warnings, token, changes = self._check_import(payload)
        return PlanImportPreview(raw, hashlib.sha256(raw).hexdigest(), payload, warnings,
                                 token, changes, "v4 文件将按原有整体／分侧语义转换为 v5 草稿；"
                                 "原始文件保留，不自动改为左右交替。" if legacy else "")

    def format_help(self):
        return ("新文件使用 UTF-8 编码的 training_feedback.plan JSON v5。\n"
                "本产品 v4 文件先严格校验，再按原有整体／分侧语义转换为新草稿，保留原件。\n"
                "execution_mode 为 whole／separate_sides／alternating，分别表示整体／分侧／交替。\n"
                "alternating_start 交替时为 left／right／either，其它模式为 null。\n"
                "交替仅支持非负整数次；per_side=true 为每侧次数，false 为总次数。\n"
                "新建：intent 为 new；升级：intent 为 upgrade，填写 target_base_number。\n"
                "名称、动作精确身份、内容哈希、分类、剂量及适用休息必须完整。\n"
                "数字须为有限非负数，顺序为不重复正整数；单侧动作须选择先做侧。\n"
                "自由剂量可用 value=null、unit=free，但必须写明备注。\n"
                "来源引用须属于当前数据目录；动作和内容身份必须与目录精确匹配。\n"
                "导入文件最多 4 MiB；JSON 最深 64 层、最多 50000 个值，超限不会截断。\n"
                "文件整体合格后仅导入为草稿，不会自动启用动作、审核内容或启用计划。\n"
                "v2/v3、未来版、训练证据、Excel、Word 和自然语言文件不能导入。\n"
                "以下 schema 是完整字段说明；示例剂量只供格式参考，不是个人训练建议。\n\n"
                + json.dumps(self.service.schema, ensure_ascii=False, indent=2))

    def example_payload(self):
        from ..domain.group_plans import action_from_choice
        choices = self.service.exercise_choices()
        if not choices:
            raise ValueError("当前没有可引用的动作，请先添加动作后再保存示例。")
        action = action_from_choice(choices[0])
        action["sets"] = [{"order": 1, "unit": "reps", "value": 1, "per_side": False,
                           "rest_after_set_seconds": 0, "note": "仅为格式示例"}]
        return {"schema": "training_feedback.plan", "schema_version": 5, "intent": "new",
                "rationale": "仅为文件格式示例，不是个人事实或训练建议。",
                "plan": {"name": "格式参考计划（请自行修改）", "purpose": "",
                         "days": [{"order": 1, "items": [action]}]}}

    def import_preview(self, preview):
        with RootMutationLease(self.root):
            return self._import_preview(preview)

    def _import_preview(self, preview):
        raw = preview.raw
        text, payload = self._parse(raw)
        version = payload.get("schema_version") if isinstance(payload, dict) else "unknown"
        path = managed_path(self.root, f"imports/plan-v{version}-{uuid.uuid4().hex}.json")
        try:
            with self.service.library._action():
                payload, _warnings, token, _changes = self._check_import(payload)
                if (token != preview.target_token
                        or hashlib.sha256(raw).hexdigest() != preview.sha256):
                    raise ValueError("导入预览已过期，请重新选择文件并核对。尚未保存计划。")
                self.service.repository.check_source(payload.get("source", {}))
                now = self.service.library.clock.now().isoformat()
                if payload["intent"] == "upgrade":
                    plan_id = self.service.repository.find_base_number(
                        payload["target_base_number"]
                    )
                    if plan_id is None:
                        raise ValueError("Target plan base code was not found.")
                    active = self.service.repository.active(plan_id)
                    if active is None:
                        raise ValueError("The target plan has no active revision to upgrade.")
                    existing = self.service.upgrade_draft(active["id"])
                    if existing:
                        raise ValueError(
                            "An upgrade draft for this plan already exists; open it to continue."
                        )
                    self.service._lineage(plan_id, payload)
                    code, _changes = revision_code_for_change(
                        active["base_number"], active["plan_code"],
                        active["payload"]["plan"], payload["plan"],
                    )
                    identifier = self.service.repository.create(
                        payload, now, plan_id, plan_code=code,
                        change_description=payload.get("change_description", ""),
                        upgrade_source_revision_id=active["id"],
                    )
                else:
                    self.service._lineage(None, payload)
                    if self.service.repository.find_plan(payload["plan"]["name"]) is not None:
                        raise ValueError("A plan with this name already exists.")
                    identifier = self.service.repository.create(
                        payload, now,
                        change_description=payload.get("change_description", ""),
                    )
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(raw)
                self.service.repository.register_import(
                    identifier,
                    path.relative_to(self.root).as_posix(),
                    hashlib.sha256(raw).hexdigest(),
                    text,
                    now,
                )
                return identifier
        except Exception as exc:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                raise ValueError("导入失败，尚未保存计划；托管原件清理失败，请反馈此路径："
                                 + str(path)) from exc
            raise

    def export(self, revision_id, *, session_service=None, session_id=None):
        with RootMutationLease(self.root):
            return self._export(
                revision_id,
                session_service=session_service,
                session_id=session_id,
            )

    def _export(self, revision_id, *, session_service=None, session_id=None):
        stem = ("session" if session_service else "plan") + "-evidence-v5-" + uuid.uuid4().hex
        destination = managed_path(self.root, f"exports/{stem}")
        staged = managed_path(self.root, f"exports/.{stem}.staging")
        staged.mkdir(parents=True)
        try:
            with self.service.library._action():
                session = session_service.get(session_id) if session_service else None
                revision = (session["snapshot"]["revision"] if session
                            else self.service.ready_revision(revision_id))
                revision = {key: value for key, value in revision.items()
                            if key not in {"editing_identifier", "document_token"}}
                revision_id = revision["id"]
                now = self.service.library.clock.now().isoformat()
                export_id = self.service.repository.register_export(
                    revision_id,
                    destination.relative_to(self.root).as_posix(),
                    now,
                )
                schema_version = self.service.repository.schema_version()
                evidence = {
                    "schema": "training_feedback.evidence",
                    "schema_version": EVIDENCE_SCHEMA_VERSION,
                    "provenance": {
                        "application_version": __version__,
                        "catalog_version": self.service.library.catalog.version,
                        "database_schema_version": schema_version,
                        "export_id": export_id,
                        "exported_at": now,
                        "scope": "training_session" if session else "plan_revision",
                    },
                    "revision": revision,
                    "contents": [],
                    "assets": [],
                    "plan_import_schema": (plan_v4_schema()
                        if revision["payload"]["schema_version"] == 4 else self.service.schema),
                    "execution_semantics_version": revision["payload"]["schema_version"],
                    "conversion_registrations": ConversionRepository(
                        self.service.repository.connection
                    ).registrations(revision_id, session_id),
                }
                if session:
                    session_service.repository.register_export(session_id, export_id)
                    evidence["session"] = session
                    evidence["previous_revisions"] = [
                        row for row in self.service.repository.revisions(revision["plan_id"])
                        if row["revision_number"] < revision["revision_number"]
                        and row["status"] in {"active", "superseded"}
                    ]
                    evidence["earlier_sessions"] = [
                        {"id": row["id"], "training_date": row["training_date"],
                         "status": row["status"], "revision_id": row["revision_id"],
                         "results": [{"item_id": o["item_id"], "side": o["side"],
                                      "round_number": o["round_number"], "result": o["result"],
                                      "actual_sets": o["actual_sets"], "note": o["note"]}
                                     for o in row["occurrences"]], "feedback": row["feedback"]}
                        for row in session_service.history() if row["id"] < session_id
                    ]
                pins = {pin["item_key"]: pin for pin in revision["pins"]}
                retained = set()
                for _day, _item, action in plan_actions(revision["payload"]["plan"]):
                    pin = pins.get(action["item_id"])
                    if pin:
                        entry = self.service.library.user.content(pin["content_id"])
                    else:
                        target = LibraryTarget(
                            ExerciseReference(**action["exercise"]), action["content"]
                        )
                        entry = self.service.library.target_entry(target)
                    image_files = []
                    for image in entry["content"]["guidance"]["images"]:
                        exported = {"declaration": image, "path": None, "available": False}
                        if image["status"] == "available":
                            try:
                                data = self.service.library._read_image(entry, image)
                                extension = image_file_extension(data)
                            except (OSError, ValueError, KeyError):
                                data = None
                            if data is not None:
                                relative = f"assets/{image['sha256']}.{extension}"
                                if relative not in retained:
                                    file = managed_path(staged, relative)
                                    file.parent.mkdir(exist_ok=True)
                                    file.write_bytes(data)
                                    retained.add(relative)
                                    evidence["assets"].append(
                                        {
                                            "path": relative,
                                            "sha256": image["sha256"],
                                            "bytes": len(data),
                                        }
                                    )
                                exported.update(path=relative, available=True)
                        image_files.append(exported)
                    evidence["contents"].append(
                        {
                            "item_id": action["item_id"],
                            "reference": entry["reference"],
                            "content": entry["content"],
                            "images": image_files,
                            "activation_review": pin["review"] if pin else None,
                            "binding_provenance": pin["review"].get("provenance", "plan_activation")
                            if pin else "draft_reference",
                            "content_provenance": entry.get("provenance"),
                        }
                    )
                for name, payload in (
                    ("evidence.json", evidence),
                    ("plan.json", revision["payload"]),
                    ("plan-response.schema.json", self.service.schema),
                ):
                    (staged / name).write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                        encoding="utf-8",
                    )
                (staged / "evidence.md").write_text(
                    render_plan_evidence(evidence), encoding="utf-8"
                )
                os.replace(staged, destination)
            return destination
        except Exception:
            shutil.rmtree(staged, ignore_errors=True)
            shutil.rmtree(destination, ignore_errors=True)
            raise


def render_plan_evidence(evidence):
    """Readable hierarchy followed by verbatim JSON facts (no inference or missing-field loss)."""
    revision = evidence["revision"]
    lines = [
            "# TrainingFeedback " + ("训练" if "session" in evidence else "计划") + "证据 v5",
        "",
        revision["name"],
        "",
        f"计划代码：{revision['plan_code']} · {revision['status']}",
        "",
        "范围：冻结计划与已保存训练事实；未记录结果保留未知。" if "session" in evidence
        else "范围：计划版本；不是实际训练完成记录。",
        "",
    ]
    for day in [continuous_plan_day(revision["payload"]["plan"])]:
        lines.extend(["## 计划动作", ""])
        for item in day["items"]:
            lines.append(f"### {item['order']}. {item.get('name', item.get('exercise_name', ''))}")
            if item["kind"] == "group":
                lines.append(f"轮数：{item['round_count']}；换侧：{item['side_sequence']}")
                lines.append(f"先做侧：{item['first_side']}；转换说明：{item['transition']}")
                lines.append(f"换侧休息：{item['rest_between_sides_seconds']} 秒；"
                             f"轮间休息：{item['rest_between_rounds_seconds']} 秒；"
                             f"退出休息：{item['rest_after_group_seconds']} 秒")
                lines.append(f"动作组原始备注：{item['note']}")
            for action in item.get("members", [item]):
                lines.append(f"- {action['exercise_name']} · {action['item_id']}")
                lines.append(f"  - 阶段：{item['phase']}；原始备注：{action['note']}")
                if item["kind"] == "action":
                    lines.append(f"  - 先做侧：{known(action['first_side'])}；换侧休息："
                                  f"{known(action['rest_between_sides_seconds'])} 秒；动作后休息："
                                  f"{known(action['rest_after_action_seconds'])} 秒")
                else:
                    lines.append(f"  - 成员后休息：{action['rest_after_member_seconds']} 秒")
                for dose in action["sets"]:
                    if execution_mode(action) == "alternating":
                        lines.append("  - " + alternating_explanation(action, dose))
                    lines.append(
                        f"  - {dose['order']}: {dose['value']} {dose['unit']}"
                        f"; per_side={dose['per_side']}; {dose['note']}"
                        f"；组间休息：{known(dose['rest_after_set_seconds'])} 秒"
                    )
    lines.extend(["", "## 动作指导与激活时事实", ""])
    for entry in evidence["contents"]:
        content = entry["content"]
        lines.extend([f"### {content['canonical_name']} · {entry['item_id']}",
                      f"内容身份：{entry['reference']['id']} v{entry['reference']['version']}；"
                      f"SHA-256：{entry['reference']['sha256']}",
                      f"绑定来源：{entry['binding_provenance']}"])
        review = entry["activation_review"]
        reviewed = (
            "未知（未记录）" if review is None or review["reviewed"] is None
            else ("已审核" if review["reviewed"] else "未审核")
        )
        lines.append(f"激活时审核：{reviewed}（不是执行或身体反馈）")
        guidance = content["guidance"]
        for field, title in (
            ("purpose", "目的"), ("starting_position", "起始姿势"), ("steps", "步骤"),
            ("breathing", "呼吸"), ("tempo_or_pacing", "节奏"),
            ("intended_sensations", "预期感受"), ("common_compensations", "常见代偿"),
            ("stop_criteria", "停止条件"), ("regressions", "退阶"), ("progressions", "进阶"),
            ("applicability", "适用情况"), ("cautions", "注意事项"), ("equipment", "器材"),
        ):
            value = guidance.get(field)
            lines.append(f"- {title}：")
            if isinstance(value, list):
                for item in value:
                    lines.append("  - " + (item["text"] if isinstance(item, dict) else item))
            else:
                lines.append("  " + str(value if value is not None else "未知"))
        for image in entry["images"]:
            if image["available"]:
                lines.append(f"![动作指导图片]({image['path']})")
                lines.append(image["declaration"].get("caption", ""))
            else:
                lines.append("- 图片未提供或当前文件不可用；未推测历史可用状态。")
    if "session" in evidence:
        from .group_session_handoff import render_session_summary

        lines.extend(["", render_session_summary(evidence["session"]), ""])
    lines.extend(["", "## 图片与完整冻结事实", ""])
    for asset in evidence["assets"]:
        lines.append(f"- [{asset['sha256']}]({asset['path']})")
    # A long fence keeps arbitrary backticks inside original text from closing the block.
    serialized = json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False)
    longest = max((len(run) for run in re.findall(r"`+", serialized)), default=0)
    fence = "`" * max(3, longest + 1)
    lines.extend(["", fence + "json", serialized, fence, ""])
    return "\n".join(lines)
