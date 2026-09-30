"""Measure tracked files and synthetic application services; never operate the client.

Run with the repository interpreter. No data-root argument is accepted. All roots,
locators and backups belong to a newly allocated temporary directory under .tmp.
Output contains aggregate timings and source function names, never user content.
"""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import importlib.metadata
import json
import math
import platform
import pstats
import subprocess
import sys
import tempfile
from collections import defaultdict
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

PROJECT = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(PROJECT), *args], encoding="utf-8",
    ).strip()


def checked_path(root: Path, relative: str) -> Path:
    """Refuse escapes/reparse points before reading or creating measurement files."""
    path = root / relative
    if path != root and root not in path.parents:
        raise ValueError("Measurement path is outside its owned directory.")
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError("Measurement paths cannot contain links or junctions.")
    if root.resolve() not in path.resolve().parents:
        raise ValueError("Measurement path does not resolve inside its owned directory.")
    return path


def inventory() -> dict:
    groups = defaultdict(lambda: {"files": 0, "bytes": 0})
    duplicates = defaultdict(list)
    largest = []
    names = git("ls-files", "-z").split("\0")
    deleted = []
    for name in filter(None, names):
        path = checked_path(PROJECT, name)
        if not path.exists():
            deleted.append(name)
            continue
        data = path.read_bytes()
        group = name.split("/", 1)[0] if "/" in name else "top-level"
        groups[group]["files"] += 1
        groups[group]["bytes"] += len(data)
        largest.append({"path": name, "bytes": len(data)})
        duplicates[hashlib.sha256(data).hexdigest()].append((name, len(data)))
    manifest_path = checked_path(PROJECT, "dist/TrainingFeedback.build-manifest.json")
    payload = {"status": "not run", "reason": "No existing payload manifest."}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        artifacts = manifest["artifact_hashes"]
        payload = {
            "status": "historical manifest inventory only; payload not reverified",
            "application_version": manifest["application_version"],
            "source_revision": manifest["source_revision"],
            "source_dirty": manifest["source_dirty"],
            "built_at": manifest["built_at"],
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "files": len(artifacts), "bytes": sum(row["bytes"] for row in artifacts),
            "largest": sorted(artifacts, key=lambda row: row["bytes"], reverse=True)[:10],
        }
    return {
        "basis": "git ls-files working-tree bytes; ignored trees never enumerated",
        "tracked_paths_missing_from_worktree": deleted,
        "groups": dict(sorted(groups.items())),
        "total_files": sum(row["files"] for row in groups.values()),
        "total_bytes": sum(row["bytes"] for row in groups.values()),
        "largest": sorted(largest, key=lambda row: row["bytes"], reverse=True)[:15],
        "exact_duplicates": [
            {"bytes_each": rows[0][1], "paths": sorted(name for name, _ in rows)}
            for rows in duplicates.values() if len(rows) > 1
        ],
        "payload": payload,
        "build_duration": {"status": "not run", "reason": "No build for this development task."},
    }


def summarize(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "samples": len(values),
        "p50_ms": round(ordered[math.ceil(len(values) * .5) - 1], 3),
        "p95_ms": round(ordered[math.ceil(len(values) * .95) - 1], 3),
        "max_ms": round(ordered[-1], 3),
        "raw_ms": [round(value, 3) for value in values],
    }


def measure(operation, samples: int, *, warmups: int = 2) -> dict:
    for _ in range(warmups):
        operation()
    values = []
    for _ in range(samples):
        start = perf_counter()
        operation()
        values.append((perf_counter() - start) * 1000)
    return summarize(values)


def profile(operation) -> list[dict]:
    recorder = cProfile.Profile()
    recorder.runcall(operation)
    rows = []
    for (filename, line, name), (_primitive, calls, own, cumulative, _callers) in (
        pstats.Stats(recorder).stats.items()
    ):
        path = Path(filename)
        if PROJECT / "src" in path.parents:
            rows.append({"function": f"{path.relative_to(PROJECT).as_posix()}:{line}:{name}",
                         "calls": calls, "own_ms": round(own * 1000, 3),
                         "cumulative_ms": round(cumulative * 1000, 3)})
    return sorted(rows, key=lambda row: row["cumulative_ms"], reverse=True)[:12]


def synthetic_content(context, number: int) -> dict:
    content = deepcopy(context.catalog.list()[0]["content"])
    content["canonical_name"] = f"【合成性能样本】动作 {number:04d}"
    content["aliases"] = []
    content["guidance"]["images"] = []
    content["classification"]["parent_exercise_key"] = None
    return content


def seed_plans(context, count: int) -> None:
    from training_feedback.domain.group_plans import plan_actions

    payload = json.loads(checked_path(
        PROJECT, "docs/reference/contracts/plan-v3.example.json",
    ).read_text(encoding="utf-8"))
    for _, _, action in plan_actions(payload["plan"]):
        entry = context.catalog.get(action["exercise"]["key"])
        action["content"] = entry["reference"]
        action["classification"] = entry["content"]["classification"]
    for number in range(count):
        payload["plan"]["name"] = f"【合成性能样本】计划 {number:04d}"
        context.plans.create(payload)


def services(samples: int, custom_counts: list[int]) -> dict:
    from training_feedback.app import LibraryContext
    from training_feedback.data.backup import create_backup

    parent = checked_path(PROJECT, ".tmp/measurements")
    parent.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="baseline-", dir=parent) as directory:
        owned = Path(directory)
        # TemporaryDirectory may recursively clean only the freshly allocated owned path.
        checked_path(parent, owned.name)
        for custom_count in custom_counts:
            root = checked_path(owned, f"root-{custom_count}")
            context = LibraryContext.create(root)
            try:
                for number in range(custom_count):
                    context.library.create_custom(synthetic_content(context, number))
                plan_count = 20 if custom_count else 0
                seed_plans(context, plan_count)
                timings = {}
                timings["catalog_browse_deferred"] = measure(
                    lambda: context.library.browse(latest=True, defer_checks=True), samples,
                )
                timings["catalog_browse_display_warm"] = measure(
                    lambda: context.library.browse(latest=True, for_display=True), samples,
                )

                def cold_display():
                    context.library._display_checks_cache = {}
                    context.library.browse(latest=True, for_display=True)

                timings["catalog_browse_display_cache_cold"] = measure(cold_display, samples)
                timings["catalog_search_display"] = measure(
                    lambda: context.library.browse("臀", latest=True, for_display=True), samples,
                )
                timings["plan_list"] = measure(context.plans.list_plans, samples)
                timings["history_empty"] = measure(context.sessions.history, samples)
                display_profile = profile(
                    lambda: context.library.browse(latest=True, for_display=True),
                )
                # Save the same override (same dataset size), preserving a synthetic tab/newline.
                entry = context.catalog.list()[0]
                from training_feedback.domain.catalog import ExerciseReference

                reference = ExerciseReference(**entry["content"]["exercise"])
                content = deepcopy(entry["content"])
                content["guidance"]["images"] = []
                content["guidance"]["purpose"] = "  【合成性能样本】原文\t\r\n  "
                # Pin once before timing so each repeated save has the same database size.
                context.library.save_override(reference, content, entry["reference"])
                timings["override_save_transaction"] = measure(
                    lambda: context.library.save_override(reference, content, entry["reference"]),
                    samples,
                )
                backup_number = 0

                def backup():
                    nonlocal backup_number
                    backup_number += 1
                    destination = checked_path(owned, f"backup-{custom_count}-{backup_number}")
                    create_backup(root, destination, context.database.connection)

                timings["backup"] = measure(backup, samples)
                hotspots = {
                    "display_warm": display_profile,
                    "save": profile(lambda: context.library.save_override(
                        reference, content, entry["reference"],
                    )),
                }
            finally:
                context.close()

            def reopen():
                with LibraryContext.reopen(root):
                    pass

            timings["root_reopen_same_process"] = measure(reopen, samples)
            # No Qt app/window exists: this measures interpreter + import + context only.
            worker = (
                "from pathlib import Path; from training_feedback.app import LibraryContext; "
                "import sys; ctx=LibraryContext.reopen(Path(sys.argv[1])); ctx.close()"
            )
            timings["fresh_process_context"] = measure(lambda: subprocess.run(
                [sys.executable, "-c", worker, str(root)], cwd=PROJECT,
                check=True, capture_output=True,
            ), samples)
            results.append({"custom_exercises_initial": custom_count,
                            "local_overrides_after_save": 1, "plans": plan_count, "sessions": 0,
                            "root_bytes": sum(path.stat().st_size for path in root.rglob("*")
                                              if path.is_file()),
                            "timings": timings, "profiles": hotspots,
                            "reopen_profile": profile(reopen)})
        # New-root creation includes teardown, but all targets are distinct, owned children.
        create_number = 0

        def create():
            nonlocal create_number
            create_number += 1
            with LibraryContext.create(checked_path(owned, f"new-{create_number}")):
                pass

        creation = measure(create, samples)
    return {
        "protocol": "2 warmups, nearest-rank percentiles; wall clock; sequential operations",
        "samples_per_operation": samples,
        "catalog": "owned bundled catalog; custom text synthetic; no synthetic approvals",
        "cache_conditions": "OS file cache uncontrolled/warm; cold means image-check cache only",
        "create_context_including_close": creation,
        "datasets": results,
        "client_checks": {
            "startup_to_usable_window": "not run", "root_switch_window": "not run",
            "page_rendering": "not run", "input_to_search_update": "not run",
            "populated_history": "not run", "max_ui_unresponsive_interval": "not run",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--custom-counts", type=int, nargs="+", default=[0, 100])
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    if args.samples < 20 or any(count < 0 for count in args.custom_counts):
        parser.error("Use at least 20 timing samples and nonnegative synthetic counts.")
    result = {
        "measured_at_utc": datetime.now(UTC).isoformat(),
        "source_revision": git("rev-parse", "HEAD"),
        "source_dirty": bool(git("status", "--porcelain")),
        "measurement_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "environment": {
            "platform": platform.platform(), "machine": platform.machine(),
            "processor": platform.processor(), "python": platform.python_version(),
            "dependencies": {name: importlib.metadata.version(name) for name in (
                "PySide6", "jsonschema", "pytest", "ruff", "pyinstaller",
                "pyinstaller-hooks-contrib",
            )},
        },
        "inventory": inventory(),
    }
    if not args.inventory_only:
        result["services"] = services(args.samples, args.custom_counts)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
