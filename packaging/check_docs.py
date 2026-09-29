"""Validate tracked documentation links, repository paths, and identity claims."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REPOSITORY_PATH = re.compile(r"`((?:src|tests|packaging|docs|content)/[^`\r\n]+)`")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
EXPLICIT_ID = re.compile(r"<a\s+id=[\"']([^\"']+)[\"']\s*>", re.IGNORECASE)
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "data:", "codex:", "plugin:")


def _git_markdown_files() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.md",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return sorted(ROOT / line for line in result.stdout.splitlines() if line)


def _slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r" +", "-", value)


def _anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        anchors.update(match.group(1) for match in EXPLICIT_ID.finditer(line))
        heading = HEADING.match(line)
        if not heading:
            continue
        base = _slug(heading.group(1))
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def _link_target(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1]
    if " " in raw and not raw.startswith(EXTERNAL_PREFIXES):
        raw = raw.split(" ", 1)[0]
    return unquote(raw)


def check_markdown_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            raw = _link_target(match.group(1))
            if not raw or raw.startswith(EXTERNAL_PREFIXES):
                continue
            target_text, _, fragment = raw.partition("#")
            target = path if not target_text else (path.parent / target_text).resolve()
            if not target.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing link target {raw}")
                continue
            if fragment and target.is_file() and target.suffix.lower() == ".md":
                anchors = anchor_cache.setdefault(target, _anchors(target))
                if fragment not in anchors:
                    errors.append(f"{path.relative_to(ROOT)}: missing anchor {raw}")
    return errors


def check_repository_paths(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in REPOSITORY_PATH.finditer(text):
            raw = match.group(1).rstrip("/\\")
            if any(marker in raw for marker in ("<", ">", "*", "...")):
                continue
            target = ROOT.joinpath(*raw.split("/"))
            if not target.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing repository path {raw}")
    return errors


def _constant(text: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)}\s*=\s*(\d+)\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"missing integer constant {name}")
    return int(match.group(1))


def check_identities() -> list[str]:
    errors: list[str] = []
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]

    package_text = (ROOT / "src/training_feedback/__init__.py").read_text(encoding="utf-8")
    package_match = re.search(r'^__version__\s*=\s*"([^"]+)"', package_text, re.MULTILINE)
    package_version = package_match.group(1) if package_match else None
    if package_version != version:
        errors.append(
            f"application version mismatch: pyproject={version}, package={package_version}"
        )

    migrations = (ROOT / "src/training_feedback/data/migrations.py").read_text(encoding="utf-8")
    schema = _constant(migrations, "LATEST_SCHEMA_VERSION")
    if not re.search(
        rf"SUPPORTED_SCHEMA_APPLICATIONS\s*=\s*\{{[^}}]*\b{schema}\s*:\s*\"[^\"]*\b{re.escape(version)}\b",
        migrations,
        re.DOTALL,
    ):
        errors.append(f"schema/application map does not include {schema} -> {version}")

    contract_text = (ROOT / "src/training_feedback/domain/group_plans.py").read_text(
        encoding="utf-8"
    )
    plan_contract = _constant(contract_text, "PLAN_IMPORT_SCHEMA_VERSION")
    evidence_contract = _constant(contract_text, "EVIDENCE_SCHEMA_VERSION")
    if plan_contract != evidence_contract:
        errors.append(
            f"plan/evidence contract mismatch: {plan_contract} != {evidence_contract}"
        )

    schema_path = ROOT / f"src/training_feedback/contracts/plan-v{plan_contract}.schema.json"
    if not schema_path.is_file():
        errors.append(f"missing canonical current contract {schema_path.relative_to(ROOT)}")
    else:
        contract_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        declared = contract_schema.get("properties", {}).get("schema_version", {}).get("const")
        if declared != plan_contract:
            errors.append(f"contract schema declares {declared}, expected {plan_contract}")

    catalog = json.loads(
        (ROOT / "src/training_feedback/catalog/catalog-manifest.json").read_text(encoding="utf-8")
    )["catalog_version"]
    expected_lines = {
        ROOT / "README.md": (
            f"- Application: `{version}`",
            f"- Database schema: `{schema}`",
        ),
        ROOT / "docs/README.md": (
            f"- Current application: `{version}`",
            f"- Current database schema: `{schema}`",
            f"- Current plan/evidence contract: `{plan_contract}`",
            f"- Current catalog: `{catalog}`",
        ),
        ROOT / "docs/history/README.md": (
            f"- Application: **{version}**",
            f"- Database schema: **{schema}**",
            f"- Catalog: **{catalog}**",
            f"- Current plan/evidence contract: **{plan_contract}**",
        ),
    }
    for path, claims in expected_lines.items():
        text = path.read_text(encoding="utf-8")
        for claim in claims:
            if claim not in text:
                errors.append(f"{path.relative_to(ROOT)}: missing identity claim {claim}")

    mirrors = [
        path.relative_to(ROOT).as_posix()
        for version_number in (2, 3)
        for path in (ROOT / "docs").rglob(f"plan-v{version_number}.schema.json")
        if "archive" not in path.relative_to(ROOT / "docs").parts
    ]
    if mirrors:
        errors.append("current contract schema mirrors remain under docs/: " + ", ".join(mirrors))
    return errors


def main() -> int:
    files = _git_markdown_files()
    errors = check_markdown_links(files)
    errors.extend(check_repository_paths(files))
    errors.extend(check_identities())
    if errors:
        print("Documentation checks failed:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print(f"Documentation checks passed for {len(files)} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
