"""Portable v2 plan/evidence files with retained illustration bytes and managed provenance."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from pathlib import Path

from .. import __version__
from ..application.library_workflow import LibraryTarget
from ..domain.catalog import ExerciseReference
from ..domain.group_plans import EVIDENCE_SCHEMA_VERSION, plan_actions
from .catalog_resources import managed_path
from .conversion_repository import ConversionRepository
from .group_session_handoff import known
from .library_images import image_file_extension


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


class GroupPlanHandoff:
    def __init__(self, service, data_root):
        self.service = service
        self.root = Path(data_root)

    def import_file(self, source: Path):
        raw = Path(source).read_bytes()
        text = raw.decode("utf-8")
        payload = _strict_json(text)
        # Validate before managing files; validate again inside the single write action.
        self.service.validate(payload)
        path = managed_path(self.root, f"imports/plan-v2-{uuid.uuid4().hex}.json")
        try:
            with self.service.library._action():
                payload = self.service.validate(payload)
                self.service.repository.check_source(payload.get("source", {}))
                target_name = payload["plan"].get("target_plan_name")
                plan_id = self.service.repository.find_plan(target_name) if target_name else None
                if target_name and plan_id is None:
                    raise ValueError("Target plan was not found.")
                self.service._lineage(plan_id, payload)
                now = self.service.library.clock.now().isoformat()
                identifier = self.service.repository.create(payload, now, plan_id)
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
        except Exception:
            path.unlink(missing_ok=True)
            raise

    def export(self, revision_id, *, session_service=None, session_id=None):
        stem = ("session" if session_service else "plan") + "-evidence-v2-" + uuid.uuid4().hex
        destination = managed_path(self.root, f"exports/{stem}")
        staged = managed_path(self.root, f"exports/.{stem}.staging")
        staged.mkdir(parents=True)
        try:
            with self.service.library._action():
                session = session_service.get(session_id) if session_service else None
                revision = (session["snapshot"]["revision"] if session
                            else self.service.get(revision_id))
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
                    "plan_import_schema": self.service.schema,
                    "conversion_registrations": ConversionRepository(
                        self.service.repository.connection
                    ).registrations(revision_id, session_id),
                }
                if session:
                    session_service.repository.register_export(session_id, export_id)
                    evidence["session"] = session
                    evidence["previous_revisions"] = [
                        row for row in self.service.revisions(revision["plan_id"])
                        if row["revision_number"] < revision["revision_number"]
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
        "# TrainingFeedback " + ("训练" if "session" in evidence else "计划") + "证据 v2",
        "",
        revision["name"],
        "",
        f"版本：{revision['revision_number']} · {revision['status']}",
        "",
        "范围：冻结计划与已保存训练事实；未记录结果保留未知。" if "session" in evidence
        else "范围：计划版本；不是实际训练完成记录。",
        "",
    ]
    for day in revision["payload"]["plan"]["days"]:
        lines.extend([f"## {day['order']}. {day['name']}", ""])
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
