r"""Materialize the frozen synthetic schema-16 root for packaged acceptance.

Copies the checked-in baseline bytes from ``docs/contracts/baseline/``
(``schema16-root/`` plus its metadata) into a caller-chosen empty directory and
points a fresh isolated locator at the copy. The old fixture generator retired
with the pre-conversion desktop runtime in 070-G3; the frozen baseline is now
the single source of truth for the synthetic acceptance root. The packaged
candidate converts this root to the current schema on first open, which is
exactly the seamless-upgrade scenario the acceptance runbook exercises.

Every user-visible string in the fixture is marked as synthetic so fixture
content can never be mistaken for real training evidence, and fixture approval
metadata never enters production seed data.

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
import hashlib
import json
import shutil
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

# Allow running straight from the repository without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_feedback.data.locator import Locator  # noqa: E402

MARK = "【合成验收数据】"
BASELINE = Path(__file__).resolve().parents[1] / "docs" / "contracts" / "baseline"


def _verify_copy(root: Path) -> None:
    """Fail loudly if the checked-in fixture bytes did not survive the copy."""
    preservation = json.loads(
        (BASELINE / "schema16-preservation.json").read_text(encoding="utf-8")
    )
    for relative, expected in preservation["resources"].items():
        target = root / relative
        if not target.is_file():
            raise ValueError(f"Baseline resource missing after copy: {relative}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Baseline resource hash mismatch after copy: {relative}")
    database = root / "training_feedback.sqlite3"
    uri = database.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError(f"Baseline database failed integrity check: {database}")
        violations = db.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(
                f"Baseline database failed foreign-key check: {database} ({violations})"
            )


def prepare_acceptance_root(base: Path) -> dict:
    """Copy the frozen synthetic fixture under an empty base directory."""
    base = Path(base).expanduser().resolve()
    if base.exists() and any(base.iterdir()):
        raise ValueError(f"Base directory must be empty or absent: {base}")

    root = base / "data-root"
    shutil.copytree(BASELINE / "schema16-root", root)
    _verify_copy(root)

    (base / "localappdata" / "TrainingFeedback").mkdir(parents=True, exist_ok=True)
    locator = Locator(base / "localappdata" / "TrainingFeedback" / "locator.json")
    locator.save(root)

    metadata = json.loads((BASELINE / "schema16-fixture.json").read_text(encoding="utf-8"))
    exports = tuple(root / "exports" / name for name in metadata["exports"])
    for path in exports:
        if not path.is_file():
            raise ValueError(f"Baseline export missing after copy: {path}")

    notice = (
        f"{MARK}\n"
        "此目录由 packaging/prepare_acceptance_data.py 从仓库冻结基线复制生成，"
        "内容全部为合成数据，不包含任何真实训练记录。\n\n"
        "首次用打包程序打开时会自动完成一次性数据升级（schema 16 → 当前版本）。\n\n"
        "用打包程序打开（PowerShell 7）：\n"
        f'  $env:LOCALAPPDATA = "{base / "localappdata"}"\n'
        "  & <构建目录>\\TrainingFeedback.exe\n\n"
        "验收后请整体删除本目录。\n"
    )
    (base / "README.txt").write_text(notice, encoding="utf-8")
    return {
        "base": base,
        "data_root": root,
        "locator": locator.path,
        "sessions": metadata["sessions"],
        "exports": exports,
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
