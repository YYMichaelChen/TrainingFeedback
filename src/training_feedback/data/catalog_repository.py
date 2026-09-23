"""Verified, read-only program catalog, independent of user database connections."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..domain.catalog import content_sha256, require_content_envelope
from .catalog_resources import CatalogError, catalog_directory, checked_bytes, managed_path


class CatalogRepository:
    def __init__(self, directory: Path | None = None):
        self.directory = Path(directory) if directory is not None else catalog_directory()
        self.connection = None
        try:
            self.manifest = json.loads(
                (self.directory / "catalog-manifest.json").read_text(encoding="utf-8")
            )
            if (self.manifest.get("application"), self.manifest.get("format_version")) != (
                "TrainingFeedback", 1,
            ):
                raise CatalogError("Unsupported catalog format.")
            self.version = self.manifest["catalog_version"]
            files = self.manifest["files"]
            declared = {item["path"] for item in files}
            if len(declared) != len(files) or "catalog.sqlite3" not in declared:
                raise CatalogError("Invalid catalog file inventory.")
            actual = {path.relative_to(self.directory).as_posix()
                      for path in self.directory.rglob("*") if path.is_file()}
            if actual != declared | {"catalog-manifest.json"}:
                raise CatalogError("Catalog file inventory does not match.")
            for item in files:
                if item["path"] != "catalog.sqlite3" and not item["path"].startswith("images/"):
                    raise CatalogError("Unexpected catalog file.")
                data = checked_bytes(self.directory, item["path"], item["sha256"])
                if len(data) != item["bytes"]:
                    raise CatalogError("Catalog resource size does not match.")
            path = managed_path(self.directory, "catalog.sqlite3")
            self.connection = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA query_only=ON")
            metadata = self.connection.execute("SELECT * FROM catalog_metadata").fetchall()
            if len(metadata) != 1 or tuple(metadata[0]) != (1, self.version):
                raise CatalogError("Catalog database metadata does not match.")
            if self.connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CatalogError("Catalog database is corrupt.")
            contents = self.manifest["contents"]
            expected = {item["key"]: item for item in contents}
            if len(expected) != len(contents):
                raise CatalogError("Duplicate catalog identity.")
            rows = self.list()
            if {row["content"]["exercise"]["key"] for row in rows} != set(expected):
                raise CatalogError("Catalog content inventory does not match.")
            for row in rows:
                key = row["content"]["exercise"]["key"]
                if expected[key] != {"key": key, **row["reference"]}:
                    raise CatalogError("Catalog content identity does not match.")
                for image in row["content"]["guidance"]["images"]:
                    if image["status"] == "available":
                        if image["path"] not in declared or not image["path"].startswith("images/"):
                            raise CatalogError("Image is absent from the catalog manifest.")
                        checked_bytes(self.directory, image["path"], image["sha256"])
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
            self.close()
            if isinstance(exc, CatalogError):
                raise
            raise CatalogError("The program catalog could not be opened.") from exc

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def _decode(self, row) -> dict | None:
        if row is None:
            return None
        content = json.loads(row["content_json"])
        require_content_envelope(content)
        if (content_sha256(content) != row["content_sha256"]
                or content["exercise"] != {"source": "bundled", "key": row["key"]}
                or "review" in content["guidance"]):
            raise CatalogError("Invalid immutable catalog content.")
        return {"reference": {"id": row["content_id"], "version": row["content_version"],
                              "sha256": row["content_sha256"]},
                "content": content, "withdrawn": bool(row["withdrawn"])}

    def get(self, key: str) -> dict | None:
        return self._decode(self.connection.execute(
            "SELECT * FROM catalog_exercise WHERE key=?", (key,),
        ).fetchone())

    def list(self) -> list[dict]:
        return [self._decode(row) for row in self.connection.execute(
            "SELECT * FROM catalog_exercise ORDER BY key"
        )]

    def families(self) -> list[dict]:
        return [{"key": row["key"], "name": row["name"], **json.loads(row["metadata_json"])}
                for row in self.connection.execute("SELECT * FROM catalog_family ORDER BY key")]

    def image_bytes(self, image: dict) -> bytes:
        if not image["path"].startswith("images/"):
            raise CatalogError("Catalog images must be inside images/.")
        return checked_bytes(self.directory, image["path"], image["sha256"])
