"""Build-time creation of the application-owned catalog. Never used during startup."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from contextlib import closing
from copy import deepcopy
from pathlib import Path

from ..domain.catalog import content_sha256, require_content_envelope, require_stable_key
from .catalog_resources import CatalogError, managed_path
from .seed.catalog import bundled_catalog
from .seed.families import FAMILIES, catalog_classification
from .seed.images import bundled_image_assets

CATALOG_FORMAT_VERSION = 1
CATALOG_VERSION = "070-illustrated-2"


def source_content() -> list[dict]:
    classification = catalog_classification()
    assets = bundled_image_assets()
    entries = []
    for seed in bundled_catalog():
        guidance = deepcopy(seed["guidance"])
        guidance.pop("review")
        for image in guidance["images"]:
            image.update(required=True, sha256=hashlib.sha256(assets[image["path"]]).hexdigest())
        envelope = {
            "exercise": {"source": "bundled", "key": seed["exercise_key"]},
            "canonical_name": seed["canonical_name"], "aliases": seed["aliases"],
            "category": seed["category"], "equipment_summary": seed["equipment_summary"],
            "body_areas": seed["body_areas"],
            "classification": classification[seed["exercise_key"]], "guidance": guidance,
        }
        entries.append({
            "id": seed["content_id"], "version": seed["content_version"],
            "sha256": content_sha256(envelope), "content": envelope,
        })
    return entries


def build_catalog(
    destination: Path, *, entries: list[dict] | None = None,
    assets: dict[str, bytes] | None = None, version: str = CATALOG_VERSION,
) -> Path:
    """Produce a deterministic payload in an empty directory, cleaning failed builds."""
    destination = Path(destination)
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise CatalogError("Catalog build destination must be empty.")
    require_stable_key(version)
    using_bundled_source = entries is None
    entries = source_content() if using_bundled_source else deepcopy(entries)
    if assets is None:
        assets = bundled_image_assets() if using_bundled_source else {}
    destination.mkdir(parents=True, exist_ok=True)
    try:
        (destination / "images").mkdir()
        for relative, data in assets.items():
            if not relative.startswith("images/"):
                raise CatalogError("Catalog assets must live under images/.")
            path = managed_path(destination, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        with closing(sqlite3.connect(destination / "catalog.sqlite3")) as connection:
            connection.executescript("""
                PRAGMA foreign_keys=ON;
                CREATE TABLE catalog_metadata(
                    format_version INTEGER NOT NULL, version TEXT NOT NULL);
                CREATE TABLE catalog_family(
                    key TEXT PRIMARY KEY, name TEXT NOT NULL, metadata_json TEXT NOT NULL);
                CREATE TABLE catalog_exercise(
                    key TEXT PRIMARY KEY, content_id TEXT NOT NULL,
                    content_version INTEGER NOT NULL,
                    content_sha256 TEXT NOT NULL, content_json TEXT NOT NULL,
                    withdrawn INTEGER NOT NULL DEFAULT 0 CHECK(withdrawn IN (0,1)));
            """)
            connection.execute("INSERT INTO catalog_metadata VALUES (?, ?)",
                               (CATALOG_FORMAT_VERSION, version))
            for family in FAMILIES:
                metadata = {"base_key": family.base_key, "member_keys": family.member_keys,
                            "starting_position_class": family.starting_position.value}
                connection.execute(
                    "INSERT INTO catalog_family VALUES (?, ?, ?)",
                    (family.key, family.name, json.dumps(metadata, ensure_ascii=False)),
                )
            for entry in entries:
                content = entry["content"]
                require_content_envelope(content)
                reference = content["exercise"]
                require_stable_key(reference["key"])
                require_stable_key(entry["id"])
                if reference["source"] != "bundled" or "review" in content["guidance"]:
                    raise CatalogError("Catalog cannot contain user review or custom state.")
                if content_sha256(content) != entry["sha256"]:
                    raise CatalogError("Catalog content hash does not match.")
                if type(entry["version"]) is not int or entry["version"] < 1:
                    raise CatalogError("Content version must be a positive integer.")
                connection.execute(
                    "INSERT INTO catalog_exercise VALUES (?, ?, ?, ?, ?, ?)",
                    (reference["key"], entry["id"], entry["version"], entry["sha256"],
                     json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                     int(entry.get("withdrawn", False))),
                )
            connection.commit()
            connection.execute("VACUUM")
        manifest = {
            "application": "TrainingFeedback", "format_version": CATALOG_FORMAT_VERSION,
            "catalog_version": version,
            "contents": [{"key": entry["content"]["exercise"]["key"],
                          "id": entry["id"], "version": entry["version"],
                          "sha256": entry["sha256"]} for entry in entries],
            "files": [
                {"path": path.relative_to(destination).as_posix(), "bytes": path.stat().st_size,
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in sorted(destination.rglob("*")) if path.is_file()
            ],
        }
        (destination / "catalog-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        from .catalog_repository import CatalogRepository
        from .library_images import inspect_images

        with CatalogRepository(destination) as catalog:
            for entry in catalog.list():
                checks = inspect_images(entry["content"]["guidance"]["images"], catalog.image_bytes)
                if any(not check.valid and check.reason != "missing" for check in checks):
                    raise CatalogError("Catalog contains an invalid illustration.")
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination
