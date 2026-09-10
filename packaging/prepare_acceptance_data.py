r"""Prepare an isolated synthetic data root for packaged acceptance (Phase 8-B1).

Creates a fresh TrainingFeedback data root plus a locator under a caller-chosen
empty directory, using only application services and repositories (no direct
SQL). Every user-visible string is marked as synthetic so fixture content can
never be mistaken for real training evidence, and fixture approval metadata
never enters production seed data.

Layout produced under the base directory:

    <base>/data-root/                            # TrainingFeedback data root
    <base>/localappdata/TrainingFeedback/        # isolated locator home
    <base>/README.txt                            # synthetic notice + launch hint

Run the packaged build against the fixture with:

    $env:LOCALAPPDATA = "<base>\localappdata"
    & dist\TrainingFeedback\TrainingFeedback.exe
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from datetime import date, datetime, timezone
from pathlib import Path

# Allow running straight from the repository without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_feedback.app import ApplicationContext  # noqa: E402
from training_feedback.application.exercise_service import ExerciseService  # noqa: E402
from training_feedback.data.exercise_repositories import ExerciseRepository  # noqa: E402
from training_feedback.data.feedback_repositories import FeedbackRepository  # noqa: E402
from training_feedback.data.handoff import HandoffService  # noqa: E402
from training_feedback.data.locator import Locator  # noqa: E402
from training_feedback.data.plan_repositories import PlanRepository  # noqa: E402
from training_feedback.data.session_repositories import SessionRepository  # noqa: E402
from training_feedback.domain.enums import DoseUnit, ExerciseResult, FeedbackValue  # noqa: E402
from training_feedback.domain.models import ActualSet  # noqa: E402
from training_feedback.domain.plans import (  # noqa: E402
    PlanAction,
    PlanDay,
    PlannedSet,
    PlanPhase,
    PlanRevision,
)
from training_feedback.domain.session_controller import SessionController  # noqa: E402

MARK = "【合成验收数据】"
PLAN_NAME = f"{MARK}验收演示计划"
REVIEW_SOURCE = "synthetic-acceptance-fixture"

# Deterministic fixture timeline (UTC).
DAY1 = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)
DAY2 = datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc)
DAY3 = datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc)


class FixedClock:
    def __init__(self, current: datetime):
        self.current = current

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


def _activate_seed_guidance(
    service: ExerciseService, exercises, names: list[str]
) -> dict[str, int]:
    """Approve and activate seed guidance for the fixture exercises."""
    review = {
        "reviewer_type": "external_ai_expert",
        "review_source": REVIEW_SOURCE,
        "review_note": f"{MARK}合成审阅记录，仅用于打包验收。",
        "reviewed_at": "2026-09-04T00:00:00+00:00",
        "user_approved_at": "2026-09-04T00:00:00+00:00",
    }
    ids: dict[str, int] = {}
    for name in names:
        exercise = exercises.resolve(name)
        guidance_id = exercises.get(exercise["id"])["guidance"][0]["id"]
        service.submit_for_review(guidance_id)
        service.approve_guidance(guidance_id, review)
        service.activate_guidance(guidance_id)
        ids[name] = exercise["id"]
    return ids


def _build_plan(plans: PlanRepository, ids: dict[str, int]) -> int:
    """Create two revisions: the first ends superseded, the second active."""
    revision1 = PlanRevision(
        PLAN_NAME,
        f"{MARK}初始版本：仅臀桥。",
        (
            PlanDay(
                1,
                f"{MARK}训练日",
                (
                    PlanAction(
                        1,
                        ids["臀桥"],
                        PlanPhase.MAIN,
                        (
                            PlannedSet(1, DoseUnit.REPS, 12, per_side=True),
                            PlannedSet(2, DoseUnit.REPS, 12, per_side=True),
                        ),
                        rest_seconds=45,
                    ),
                ),
            ),
        ),
    )
    plan_id, revision1_id = plans.create_plan(revision1)
    plans.activate_revision(plan_id, revision1_id)

    revision2 = PlanRevision(
        PLAN_NAME,
        f"{MARK}第二版：加入椅子深蹲与死虫式，并保留逐字备注。",
        (
            PlanDay(
                1,
                f"{MARK}训练日",
                (
                    PlanAction(
                        1,
                        ids["臀桥"],
                        PlanPhase.MAIN,
                        (
                            PlannedSet(1, DoseUnit.REPS, 12, per_side=True),
                            PlannedSet(2, DoseUnit.REPS, 12, per_side=True),
                        ),
                        rest_seconds=45,
                        note=f"{MARK}计划备注  保留\t原文",
                    ),
                    PlanAction(
                        2,
                        ids["椅子深蹲"],
                        PlanPhase.MAIN,
                        (
                            PlannedSet(1, DoseUnit.REPS, 10),
                            PlannedSet(2, DoseUnit.REPS, 10),
                            PlannedSet(3, DoseUnit.REPS, 10),
                        ),
                        rest_seconds=60,
                    ),
                    PlanAction(
                        3,
                        ids["死虫式"],
                        PlanPhase.MAIN,
                        (
                            PlannedSet(1, DoseUnit.REPS, 8, per_side=True),
                            PlannedSet(2, DoseUnit.REPS, 8, per_side=True),
                        ),
                        rest_seconds=30,
                    ),
                ),
            ),
        ),
    )
    revision2_id = plans.create_draft_revision(plan_id, revision2)
    plans.activate_revision(plan_id, revision2_id)
    return plan_id


def _record_sessions(
    context: ApplicationContext, plans: PlanRepository, exercises, plan_id: int
) -> tuple[dict, dict, dict]:
    """Record a completed session, a partial session, and a paused session."""
    sessions = SessionRepository(context.database.connection)

    # Day 1: all actions completed or exceeded -> final status completed.
    controller = SessionController(sessions, plans, exercises, FixedClock(DAY1))
    completed = controller.start(plan_id)
    by_name = {a["exercise_name_snapshot"]: a for a in completed["actions"]}
    controller.record_result(
        by_name["臀桥"]["id"],
        ExerciseResult.EXCEEDED,
        note=f"{MARK}  超额完成\t保留原文  ",
        actual_sets=(
            ActualSet(14, DoseUnit.REPS, per_side=True),
            ActualSet(14, DoseUnit.REPS, per_side=True),
        ),
    )
    controller.record_result(by_name["椅子深蹲"]["id"], ExerciseResult.COMPLETED)
    controller.record_result(
        by_name["死虫式"]["id"], ExerciseResult.COMPLETED, note=f"{MARK}无额外感受。"
    )
    completed = controller.finish()

    # Day 2: one partial and one not completed -> final status partial.
    controller = SessionController(sessions, plans, exercises, FixedClock(DAY2))
    partial = controller.start(plan_id)
    by_name = {a["exercise_name_snapshot"]: a for a in partial["actions"]}
    controller.record_result(
        by_name["臀桥"]["id"], ExerciseResult.COMPLETED, note=f"{MARK}按计划完成。"
    )
    controller.record_result(
        by_name["椅子深蹲"]["id"],
        ExerciseResult.PARTIAL,
        note=f"{MARK}第三组腿部疲劳，提前结束。",
        actual_sets=(ActualSet(10, DoseUnit.REPS), ActualSet(10, DoseUnit.REPS)),
    )
    controller.record_result(
        by_name["死虫式"]["id"],
        ExerciseResult.NOT_COMPLETED,
        note=f"{MARK}时间不足，未执行。",
    )
    partial = controller.finish()

    # Day 3: one recorded action, then paused (resumable across restart).
    controller = SessionController(sessions, plans, exercises, FixedClock(DAY3))
    paused = controller.start(plan_id)
    by_name = {a["exercise_name_snapshot"]: a for a in paused["actions"]}
    controller.record_result(
        by_name["臀桥"]["id"], ExerciseResult.COMPLETED, note=f"{MARK}暂停前已完成。"
    )
    paused = controller.pause()
    return completed, partial, paused


def _record_feedback(context: ApplicationContext, completed: dict, partial: dict) -> None:
    feedback = FeedbackRepository(context.database.connection)
    feedback.submit(
        completed["id"],
        {
            "臀部": FeedbackValue.SOME_SORENESS,
            "大腿前侧": FeedbackValue.NO_OBVIOUS_SENSATION,
            "核心": FeedbackValue.NO_OBVIOUS_SENSATION,
        },
        f"{MARK}次日反馈原文：右侧臀部更明显。",
        date(2026, 9, 6),
        datetime(2026, 9, 6, 8, 0, tzinfo=timezone.utc),
    )
    # Second session leaves one area explicitly unanswered (unknown stays unknown).
    feedback.submit(
        partial["id"],
        {"臀部": FeedbackValue.SIGNIFICANT_SORENESS, "大腿前侧": None},
        "",
        date(2026, 9, 8),
        datetime(2026, 9, 8, 8, 0, tzinfo=timezone.utc),
    )


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack("!I", len(payload)) + kind + payload + struct.pack("!I", checksum)


def _solid_png(red: int, green: int, blue: int, width: int = 64, height: int = 48) -> bytes:
    """Return a deterministic, dependency-free RGB PNG for synthetic fixture checks."""
    header = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    scanline = b"\x00" + bytes((red, green, blue)) * width
    pixels = zlib.compress(scanline * height, level=9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", pixels)
        + _png_chunk(b"IEND", b"")
    )


def _write_images(context: ApplicationContext) -> None:
    images = context.data_root.path / "exercise-images"
    images.mkdir(parents=True, exist_ok=True)
    (images / f"{MARK}臀桥图片夹具.png").write_bytes(_solid_png(46, 125, 50))
    (images / f"{MARK}死虫式图片夹具.png").write_bytes(_solid_png(30, 90, 180))


def _import_draft(context: ApplicationContext, base: Path) -> None:
    payload = {
        "schema": "training_feedback.plan",
        "schema_version": 1,
        "rationale": f"{MARK}外部专家建议：臀桥剂量提升到每侧 14 次。",
        "plan": {
            "name": PLAN_NAME,
            "target_plan_name": PLAN_NAME,
            "purpose": f"{MARK}导入草稿，等待人工核对，不应已激活。",
            "days": [
                {
                    "order": 1,
                    "name": f"{MARK}训练日",
                    "actions": [
                        {
                            "order": 1,
                            "exercise_name": "臀桥",
                            "phase": "main",
                            "rest_seconds": 45,
                            "note": f"{MARK}导入备注原文",
                            "sets": [
                                {"order": 1, "value": 14, "unit": "reps", "per_side": True,
                                 "note": f"{MARK}逐字保留"},
                                {"order": 2, "value": 14, "unit": "reps", "per_side": True,
                                 "note": ""},
                            ],
                        }
                    ],
                }
            ],
        },
    }
    source = base / "import-source.json"
    source.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        HandoffService(context.database.connection, context.data_root.path).import_plan_file(source)
    finally:
        source.unlink(missing_ok=True)


def prepare_acceptance_root(base: Path) -> dict:
    """Create the synthetic fixture under an empty base directory."""
    base = Path(base).expanduser().resolve()
    if base.exists() and any(base.iterdir()):
        raise ValueError(f"Base directory must be empty or absent: {base}")
    (base / "localappdata" / "TrainingFeedback").mkdir(parents=True, exist_ok=True)
    locator = Locator(base / "localappdata" / "TrainingFeedback" / "locator.json")

    context = ApplicationContext.create(base / "data-root", locator)
    try:
        connection = context.database.connection
        service = context.exercise_service()
        exercise_repository = ExerciseRepository(connection)
        ids = _activate_seed_guidance(service, exercise_repository, ["臀桥", "椅子深蹲", "死虫式"])
        plans = PlanRepository(connection, exercise_repository)
        plan_id = _build_plan(plans, ids)
        completed, partial, paused = _record_sessions(
            context, plans, exercise_repository, plan_id
        )
        _record_feedback(context, completed, partial)
        _write_images(context)
        json_path, markdown_path = HandoffService(connection, context.data_root.path).export()
        _import_draft(context, base)
    finally:
        context.close()

    notice = (
        f"{MARK}\n"
        "此目录由 packaging/prepare_acceptance_data.py 生成，内容全部为合成数据，"
        "不包含任何真实训练记录。\n\n"
        "用打包程序打开（PowerShell 7）：\n"
        f'  $env:LOCALAPPDATA = "{base / "localappdata"}"\n'
        "  & <构建目录>\\TrainingFeedback.exe\n\n"
        "验收后请整体删除本目录。\n"
    )
    (base / "README.txt").write_text(notice, encoding="utf-8")
    return {
        "base": base,
        "data_root": base / "data-root",
        "locator": locator.path,
        "sessions": {
            "completed": completed["id"],
            "partial": partial["id"],
            "paused": paused["id"],
        },
        "exports": (json_path, markdown_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("base", type=Path, help="Empty (or absent) fixture output directory.")
    args = parser.parse_args(argv)
    try:
        result = prepare_acceptance_root(args.base)
    except Exception as exc:
        print(f"prepare-acceptance-data failed: {exc}", file=sys.stderr)
        return 1
    print(f"Synthetic acceptance data ready: {result['data_root']}")
    print(f"Locator: {result['locator']}")
    print(f"Sessions: {result['sessions']}")
    print(f"Exports: {result['exports'][0].name}, {result['exports'][1].name}")
    print(f"Launch with: $env:LOCALAPPDATA = \"{result['base'] / 'localappdata'}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
