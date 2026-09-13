"""外部交接：证据导出（JSON/Markdown）与外部计划导入的落盘与登记。

HandoffService 组合三个仓储完成多步编排，render_markdown 是导出文件的展示渲染，
二者都属于 data 层的对外组合门面，与领域规则（domain/handoff.py 的 schema 与解析）分离。
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from ..domain.handoff import (
    EXPORT_SCHEMA_VERSION,
    HandoffError,
    parse_plan_import,
    plan_import_schema,
)
from .database import transaction
from .exercise_repositories import ExerciseRepository
from .feedback_repositories import FeedbackRepository
from .plan_repositories import PlanRepository


def _json_value(value: Any) -> Any:
    """递归把枚举等特殊值转成 JSON 可序列化的标量。"""
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


class HandoffRepository:
    """导出/导入登记的 SQLite 仓储。"""

    def __init__(self, connection):
        self.connection = connection

    def schema_version(self) -> int:
        return self.connection.execute(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migration"
        ).fetchone()[0]

    def list_imports(self) -> list[dict[str, Any]]:
        return [
            dict(row) for row in self.connection.execute("SELECT * FROM plan_import ORDER BY id")
        ]

    def register_export_pair(
        self,
        session_id: int | None,
        paths: tuple[Path, Path],
        write_files: Callable[[int, int], None],
    ) -> tuple[int, int]:
        """Register both formats and write them as one logical user action."""
        with transaction(self.connection):
            now = datetime.now(UTC).isoformat()
            identifiers = []
            for path, file_format in zip(paths, ("json", "markdown"), strict=True):
                cursor = self.connection.execute(
                    "INSERT INTO ai_export(session_id, format, file_path, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (session_id, file_format, str(path), now),
                )
                identifiers.append(cursor.lastrowid)
            write_files(identifiers[0], identifiers[1])
            return identifiers[0], identifiers[1]


class HandoffService:
    """交接门面：组合三个仓储完成证据导出与外部计划导入。"""

    def __init__(self, connection, data_root: Path):
        self.data_root = Path(data_root)
        self.exercises = ExerciseRepository(connection)
        self.plans = PlanRepository(connection, self.exercises)
        self.feedback = FeedbackRepository(connection)
        self.repository = HandoffRepository(connection)

    def build_evidence(self, session_id: int | None = None) -> dict[str, Any]:
        sessions = self.feedback.history()
        if session_id is not None:
            selected_index = next(
                (index for index, session in enumerate(sessions) if session["id"] == session_id),
                None,
            )
            if selected_index is None:
                raise HandoffError("Training session was not found.")
            sessions = sessions[selected_index:]
        return {
            "schema": "training_feedback.evidence",
            "schema_version": EXPORT_SCHEMA_VERSION,
            "exported_at": datetime.now(UTC).isoformat(),
            "provenance": {
                "application": "TrainingFeedback",
                "database_schema_version": self.repository.schema_version(),
                "scope": "session_with_earlier_history" if session_id is not None else "all",
                "session_id": session_id,
                "export_id": None,
                "markdown_export_id": None,
            },
            "plan_import_schema": plan_import_schema(),
            "catalog": [
                _json_value(self.exercises.get(item["id"]))
                for item in self.exercises.list(include_inactive=True)
            ],
            "plans": [
                _json_value(self.plans.get_plan(item["id"])) for item in self.plans.list_plans()
            ],
            "sessions": [_json_value(session) for session in sessions],
            "plan_imports": [_json_value(item) for item in self.repository.list_imports()],
        }

    def export(self, session_id: int | None = None) -> tuple[Path, Path]:
        evidence = self.build_evidence(session_id)
        exports = self.data_root / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        stem = f"evidence-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        json_path = exports / f"{stem}.json"
        markdown_path = exports / f"{stem}.md"
        relative_paths = (
            json_path.relative_to(self.data_root),
            markdown_path.relative_to(self.data_root),
        )

        def write_files(json_id: int, markdown_id: int) -> None:
            evidence["provenance"]["export_id"] = json_id
            evidence["provenance"]["markdown_export_id"] = markdown_id
            json_path.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            markdown_path.write_text(render_markdown(evidence), encoding="utf-8")

        try:
            self.repository.register_export_pair(session_id, relative_paths, write_files)
        except Exception as exc:
            json_path.unlink(missing_ok=True)
            markdown_path.unlink(missing_ok=True)
            raise HandoffError(f"Training evidence could not be exported: {exc}") from exc
        return json_path, markdown_path

    def import_plan_file(self, source: Path) -> tuple[int, int]:
        source = Path(source)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise HandoffError("The external plan file is not valid UTF-8 JSON.") from exc
        imported = parse_plan_import(payload, self.exercises.resolve)
        managed_source = self._copy_import(source)
        try:
            return self.plans.create_imported_revision(
                imported.target_plan_name,
                imported.revision,
                str(managed_source.relative_to(self.data_root)),
                imported.rationale,
                imported.source_session_id,
                imported.source_export_id,
            )
        except Exception as exc:
            managed_source.unlink(missing_ok=True)
            raise HandoffError(f"External plan could not be saved: {exc}") from exc

    def _copy_import(self, source: Path) -> Path:
        imports = self.data_root / "imports"
        imports.mkdir(parents=True, exist_ok=True)
        destination = imports / f"plan-{uuid.uuid4().hex}.json"
        try:
            destination.write_bytes(source.read_bytes())
        except OSError as exc:
            raise HandoffError("The external plan file could not be copied.") from exc
        return destination


def render_markdown(evidence: dict[str, Any]) -> str:
    """Render the evidence snapshot without changing or interpreting its facts."""
    lines = [
        "# TrainingFeedback 训练证据",
        "",
        f"- 导出 ID：{evidence['provenance']['export_id']}",
        f"- 导出时间：{evidence['exported_at']}",
        f"- 范围：{evidence['provenance']['scope']}",
        f"- 会话数量：{len(evidence['sessions'])}",
        "",
        "## 动作指导",
    ]
    _append_catalog(lines, evidence["catalog"])

    lines.extend(["", "## 计划版本"])
    _append_plans(lines, evidence["plans"])

    lines.extend(["", "## 训练会话"])
    _append_sessions(lines, evidence["sessions"])

    lines.extend(["", "## 外部调整来源"])
    _append_imports(lines, evidence["plan_imports"])
    lines.extend(
        [
            "",
            "## 数据完整性",
            "",
            "完整 JSON 文件包含动作指导、计划版本、实际剂量、事件、原始备注和次日反馈。",
        ]
    )
    return "\n".join(lines) + "\n"


def _append_catalog(lines: list[str], catalog: list[dict[str, Any]]) -> None:
    for exercise in catalog:
        lines.extend(["", f"### {exercise['canonical_name']}"])
        lines.append(f"- 别名：{'、'.join(exercise['aliases']) or '无'}")
        areas = [
            f"{area['name']}（{'主要' if area['is_primary'] else '次要'}）"
            for area in exercise["body_areas"]
        ]
        lines.append(f"- 身体部位：{'、'.join(areas) or '无'}")
        lines.append(f"- 分类：{exercise['category']}；器械摘要：{exercise['equipment_summary']}")
        for guidance in exercise["guidance"]:
            content = guidance["guidance"]
            lines.append(f"- 指导版本 {guidance['revision_number']}（稳定指导，不是用户报告）")
            lines.append(
                "  - 指导主要部位："
                f"{'、'.join(content.get('primary_body_areas', [])) or '未记录'}"
            )
            lines.append(
                "  - 指导次要部位："
                f"{'、'.join(content.get('secondary_body_areas', [])) or '未记录'}"
            )
            for key, title in (
                ("purpose", "目的"),
                ("starting_position", "起始姿势"),
                ("breathing", "呼吸"),
                ("tempo_or_pacing", "节奏"),
                ("applicability", "适用性"),
                ("cautions", "注意事项"),
            ):
                lines.append(f"  - {title}：{content.get(key, '')}")
            for step in content.get("steps", []):
                lines.append(f"  - 步骤 {step.get('order')}：{step.get('text', '')}")
            for key, title in (
                ("intended_sensations", "预期感受"),
                ("common_compensations", "常见代偿"),
                ("stop_criteria", "停止标准"),
                ("regressions", "退阶"),
                ("progressions", "进阶"),
                ("equipment", "器械"),
            ):
                lines.append(f"  - {title}：{'；'.join(content.get(key, []))}")
            images = [
                f"{_unknown(image.get('path'))}（{image.get('caption', '')}；"
                f"{image.get('status', '')}）"
                for image in content.get("images", [])
            ]
            lines.append(f"  - 图片：{'；'.join(images) or '无'}")
            review = content.get("review", {})
            lines.append(
                f"  - 审核：状态 {review.get('status', 'unknown')}；"
                f"来源 {_unknown(review.get('review_source'))}；"
                f"用户批准时间 {_unknown(review.get('user_approved_at'))}"
            )


def _append_plans(lines: list[str], plans: list[dict[str, Any]]) -> None:
    for plan in plans:
        lines.extend(["", f"### {plan['name']}"])
        for revision in plan["revisions"]:
            lines.append(
                f"- 版本 {revision['revision_number']}：{revision['status']}；"
                f"目的：{revision['purpose']}"
            )
            for day in revision["days"]:
                lines.append(f"  - 第 {day['day_order']} 天：{day['name']}")
                for action in day["actions"]:
                    lines.append(
                        f"    - {action['action_order']}. {action['exercise_name']}；"
                        f"阶段：{action['phase']}；休息：{action['rest_seconds'] or 0} 秒；"
                        f"备注：{action['note']}"
                    )
                    for planned_set in action["sets"]:
                        lines.append(
                            f"      - 第 {planned_set['set_order']} 组："
                            f"{_unknown(planned_set['value'])} {planned_set['unit']}；"
                            f"每侧：{bool(planned_set['per_side'])}；备注：{planned_set['note']}"
                        )


def _append_sessions(lines: list[str], sessions: list[dict[str, Any]]) -> None:
    for session in sessions:
        lines.extend(["", f"### 会话 {session['id']}（{session['training_date']}）"])
        lines.append(f"- 状态：{session['status']}；计划版本 ID：{session['plan_revision_id']}")
        lines.append(
            f"- 中止原因：{_unknown(session.get('abort_reason'))}；"
            f"中止说明：{_unknown(session.get('abort_note'))}"
        )
        for action in session["actions"]:
            lines.append(
                f"- {action['exercise_name_snapshot']}：{_unknown(action.get('result'))}；"
                f"指导版本 ID：{_unknown(action.get('guidance_revision_id'))}；"
                f"备注：{_unknown(action.get('note'))}"
            )
            lines.append(
                f"  - 处方快照：阶段 {_unknown(action.get('phase_snapshot'))}；"
                f"休息 {_unknown(action.get('rest_seconds_snapshot'))} 秒；"
                f"动作备注：{_unknown(action.get('plan_note_snapshot'))}"
            )
            for session_set in action["sets"]:
                lines.append(
                    f"  - 第 {session_set['set_order']} 组：计划 "
                    f"{_unknown(session_set['planned_value'])} {session_set['planned_unit']}，"
                    f"每侧 {bool(session_set['planned_per_side'])}；实际 "
                    f"{_unknown(session_set['actual_value'])} "
                    f"{_unknown(session_set['actual_unit'])}，"
                    f"每侧 {_unknown(session_set['actual_per_side'])}"
                    f"；计划组备注：{_unknown(session_set.get('plan_note_snapshot'))}"
                )
            if action.get("actual_sets"):
                lines.append("  - 实际完成组：")
                for actual_set in action["actual_sets"]:
                    lines.append(
                        f"    - 第 {actual_set['actual_order']} 组："
                        f"{actual_set['value']} {actual_set['unit']}；"
                        f"每侧：{bool(actual_set['per_side'])}"
                    )
        for audit in session.get("result_retractions", []):
            previous = audit["previous_action"]
            lines.append(
                f"- 结果撤回：{previous['exercise_name_snapshot']}；"
                f"原结果：{previous['result']}；时间：{audit['retracted_at']}；"
                f"原备注：{_unknown(previous.get('note'))}"
            )
            for actual in previous.get("actual_sets", []):
                lines.append(
                    f"  - 撤回前实际第 {actual['actual_order']} 组：{actual['value']} "
                    f"{actual['unit']}；每侧：{bool(actual['per_side'])}"
                )
        for event in session["events"]:
            lines.append(
                f"- 事件：{event['event_type']}，时间：{event['occurred_at']}，"
                f"原因：{_unknown(event.get('reason'))}，说明：{_unknown(event.get('note'))}"
            )
        feedback = session.get("feedback")
        if feedback:
            lines.append(f"- 次日反馈备注：{_unknown(feedback.get('overall_note'))}")
            for area in feedback["areas"]:
                lines.append(f"  - {area['body_area_name_snapshot']}：{_unknown(area['value'])}")
            for audit in feedback["audit"]:
                lines.append(
                    f"  - 备注修正：{audit['target']}；原值：{audit['old_value']}；"
                    f"新值：{audit['new_value']}；时间：{audit['corrected_at']}"
                )
        else:
            lines.append("- 次日反馈：未知（null）")


def _append_imports(lines: list[str], imports: list[dict[str, Any]]) -> None:
    if not imports:
        lines.append("- 无")
    for item in imports:
        lines.append(
            f"- 导入 {item['id']}：状态 {item['status']}；计划/版本 "
            f"{_unknown(item.get('plan_id'))}/{_unknown(item.get('revision_id'))}；"
            f"前一版本 {_unknown(item.get('previous_revision_id'))}；"
            f"理由：{item['rationale']}；确认时间：{_unknown(item.get('confirmed_at'))}"
        )


def _unknown(value: Any) -> str:
    return "未知（null）" if value is None else str(value)
