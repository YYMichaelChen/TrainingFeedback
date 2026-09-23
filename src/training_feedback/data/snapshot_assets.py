"""Hash-addressed retained bytes, published before SQLite references become visible."""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from .catalog_resources import CatalogError, checked_bytes, managed_path, require_sha256


class SnapshotAssets:
    def __init__(self, data_root: Path):
        self.root = managed_path(Path(data_root), "snapshot-assets")

    def read(self, digest: str) -> bytes:
        require_sha256(digest)
        return checked_bytes(self.root, digest, digest)

    def publish(self, data: bytes, digest: str) -> None:
        require_sha256(digest)
        if hashlib.sha256(data).hexdigest() != digest:
            raise CatalogError("Snapshot resource hash does not match.")
        self.root.mkdir(parents=True, exist_ok=True)
        final = managed_path(self.root, digest)
        if final.exists():
            self.read(digest)
            return
        staged = managed_path(self.root, f"stage-{uuid.uuid4().hex}")
        try:
            with staged.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(staged, final)
        finally:
            staged.unlink(missing_ok=True)

    def recover_unreferenced(self, retained: set[str]) -> None:
        """Call under the user's SQLite write lock; committed assets are never deleted."""
        if not self.root.exists():
            return
        for path in self.root.iterdir():
            if path.is_symlink() or not path.is_file():
                continue
            is_stage = path.name.startswith("stage-") and len(path.name) == 38
            is_digest = len(path.name) == 64 and all(c in "0123456789abcdef" for c in path.name)
            if is_stage or (is_digest and path.name not in retained):
                path.unlink()
