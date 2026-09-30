"""Uninstall transport: fixed current-user locator, explicit offer and confirmation."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from ..data.installation import checked_components
from ..data.locator import default_locator_path
from ..data.root_cleanup import CleanupPolicy, commit, offer


def system_policy() -> CleanupPolicy:
    protected = tuple(Path(value) for name in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)")
                      if (value := os.environ.get(name)))
    if not protected:
        raise ValueError("Cannot determine protected system directories; retain data.")
    program = (Path(sys.executable).parent if getattr(sys, "frozen", False)
               else Path(__file__).resolve().parents[3])
    return CleanupPolicy(default_locator_path(), program, Path.home(), protected)


def main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("probe", "commit"))
    parser.add_argument("--offer", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args(arguments)
    checked_components(args.result)
    checked_components(args.offer)
    try:
        policy = system_policy()
        if args.operation == "probe":
            value = offer(policy)
            with args.offer.open("x", encoding="utf-8") as stream:
                json.dump(value, stream, ensure_ascii=True)
            files = [row for row in value["objects"].values() if not row["directory"]]
            lines = ["READY", value["root"], f"Files: {len(files)}; bytes: "
                     f"{sum(row['bytes'] for row in files)}", "Retry interrupted cleanup."
                     if value["retry"] else "Database and all files inside this exact root."]
            code = 0
        else:
            value = json.loads(args.offer.read_text(encoding="utf-8"))
            result = commit(policy, value, user_confirmed=args.confirmed)
            lines = [result["status"], result.get("root", ""), result.get("reason", ""),
                     result.get("recovery", "")]
            code = 0 if result["status"] in {"complete", "cancelled"} else 1
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error, MemoryError) as exc:
        lines, code = ["REFUSED", str(exc)], 1
    with args.result.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines) + "\n")
    return code
