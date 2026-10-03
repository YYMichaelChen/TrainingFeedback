"""Create owned synthetic P4 materials and service diagnostics, without a Qt app.

No existing-root, locator or destination argument is accepted. Every write is
inside a newly allocated directory under .tmp/response-acceptance. Retain that
directory for developer-operated installed-client checks; never clean it here.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
import tempfile
from pathlib import Path
from time import perf_counter

from measure_baseline import (
    PROJECT,
    checked_path,
    git,
    measure,
    profile,
    seed_plans,
    synthetic_content,
)

OPERATIONS = (
    "startup", "switch", "library", "search", "save", "plans", "history", "backup",
)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cold(context):
    context.library._display_checks_cache = {}
    return context.library.browse(latest=True, for_display=True)


def diagnostics(context):
    result = {
        "basis": "36 bundled + 100 imageless drafts + 20 draft plans; original protocol",
        "cold": measure(lambda: cold(context), 20),
        "warm": measure(lambda: context.library.browse(latest=True, for_display=True), 20),
        "cold_profile": profile(lambda: cold(context)),
    }
    context.library._display_checks_cache = {}
    cards = []
    for row in context.library.browse(latest=True, defer_checks=True):
        start = perf_counter()
        context.library.display_eligibility(row["target"])
        cards.append({"name": row["display"]["content"]["canonical_name"],
                      "ms": round((perf_counter() - start) * 1000, 3)})
    result["individual_checks_single_diagnostic"] = cards
    result["client_status"] = "not run; excludes card icons, rendering and event-loop delays"
    return result


def seed_history(context):
    from training_feedback.application.library_workflow import LibraryTarget
    from training_feedback.domain.catalog import ExerciseReference
    from training_feedback.domain.group_plans import plan_actions

    # Selecting contents freezes all 36 real bundled illustrations into this
    # synthetic root, providing a substantial backup without artificial padding.
    targets = [LibraryTarget(ExerciseReference(**entry["content"]["exercise"]),
                             entry["reference"]) for entry in context.catalog.list()]
    context.library.select_contents(targets, user_confirmed=True)
    payload = json.loads(checked_path(
        PROJECT, "docs/reference/contracts/plan-v3.example.json",
    ).read_text(encoding="utf-8"))
    payload["plan"]["name"] = "【合成人工验收】训练流程，不是个人处方"
    payload["rationale"] = "【合成测试】仅测试软件，未经过外部审核，不用于真实训练。"
    for _, _, action in plan_actions(payload["plan"]):
        entry = context.catalog.get(action["exercise"]["key"])
        action["content"] = entry["reference"]
        action["classification"] = entry["content"]["classification"]
    plan_targets = context.plans._targets(payload)
    context.library.set_enabled_batch(plan_targets, True, user_confirmed=True)
    revision = context.plans.create(payload)
    preview = context.plans.preview(revision)
    context.plans.activate(revision, expected_preview=preview["token"], user_confirmed=True)
    # Use service/controller transactions, never raw inserts or fabricated reviews.
    for number in range(100):
        controller = context.session_controller()
        preview = context.sessions.preview_start(revision, 1)
        controller.start(revision, 1, expected_preview=preview["token"], user_confirmed=True)
        while controller.unfinished:
            controller.next_unfinished()
            controller.record("not_completed", note=f"【合成历史】{number:03d}，没有实际训练")
        controller.finish(user_confirmed=True)
    return {"history_count": len(context.sessions.history()),
            "plan_count": len(context.plans.list_plans()),
            "active_plan_name": payload["plan"]["name"],
            "external_reviews": "none created", "actual_training": "none"}


def file_inventory(directory):
    files = []
    for path in sorted(directory.rglob("*")):
        checked_path(directory, path.relative_to(directory).as_posix())
        if path.is_file():
            files.append({"path": path.relative_to(directory).as_posix(),
                          "bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"files": files, "bytes": sum(row["bytes"] for row in files)}


def main():
    from training_feedback.app import LibraryContext
    from training_feedback.data.locator import Locator

    parent = checked_path(PROJECT, ".tmp/response-acceptance")
    parent.mkdir(parents=True, exist_ok=True)
    owned = Path(tempfile.mkdtemp(prefix="p4-", dir=parent))
    checked_path(parent, owned.name)
    result = {
        "owned_directory": str(owned), "source_revision": git("rev-parse", "HEAD"),
        "source_dirty": bool(git("status", "--porcelain")),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(), "platform": platform.platform(),
        "pyside6": importlib.metadata.version("PySide6"),
        "client_checks": "not run", "samples": 20, "warmups": 2,
        "cache_conditions": "OS cache uncontrolled; cold means image-check cache only",
        "candidate_exe_sha256": "1d2f09f781a8a2217921946f48ffc187c9cdb94e716cafa124880dd2cc9a8961",
    }
    small = checked_path(owned, "小样本")
    with LibraryContext.create(small):
        pass
    large = checked_path(owned, "大样本")
    with LibraryContext.create(large) as context:
        for number in range(100):
            context.library.create_custom(synthetic_content(context, number))
        seed_plans(context, 20)
        result["diagnostics_before_history"] = diagnostics(context)
        result["large_material"] = seed_history(context)
    result["small_inventory"] = file_inventory(small)
    result["large_inventory"] = file_inventory(large)
    for name, root in (("小样本配置", small), ("大样本配置", large)):
        Locator(checked_path(owned, f"{name}/TrainingFeedback/locator.json")).save(root)
    for number in range(22):
        checked_path(owned, f"备份输出/backup-{number:02d}").mkdir(parents=True)
    with checked_path(owned, "人工计时.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("operation", "sample", "kind", "video", "start_seconds",
                         "end_seconds", "no_feedback_start", "no_feedback_end", "result", "note"))
        for operation in OPERATIONS:
            for number in range(22):
                writer.writerow((operation, number, "warmup" if number < 2 else "sample",
                                 "", "", "", "", "", "not run", ""))
    write_json(checked_path(owned, "材料清单.json"), result)
    print(json.dumps({"owned_directory": str(owned),
                      "large_bytes": result["large_inventory"]["bytes"],
                      "history_count": result["large_material"]["history_count"],
                      "cold_p95_ms": result["diagnostics_before_history"]["cold"]["p95_ms"],
                      "client_checks": "not run"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
