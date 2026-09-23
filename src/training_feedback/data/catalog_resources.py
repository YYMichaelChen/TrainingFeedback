"""Portable resource paths shared by catalog building, reading and snapshots."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath


class CatalogError(ValueError):
    pass


def catalog_directory() -> Path:
    # __file__ has the same package-relative meaning in source, wheels and PyInstaller.
    return Path(__file__).resolve().parents[1] / "catalog"


def managed_path(root: Path, relative: str) -> Path:
    if (
        not isinstance(relative, str) or not relative or "\\" in relative
        or ":" in relative or "\x00" in relative
    ):
        raise CatalogError("Resource path must be portable and relative.")
    parts = relative.split("/")
    if any(part in ("", ".", "..") for part in parts) or PurePosixPath(relative).is_absolute():
        raise CatalogError("Resource path escapes its managed directory.")
    root = root.resolve()
    path = root.joinpath(*parts).resolve()
    if not path.is_relative_to(root):
        raise CatalogError("Resource path escapes its managed directory.")
    return path


def require_sha256(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise CatalogError("Expected a SHA-256 content digest.")


def checked_bytes(root: Path, relative: str, digest: str) -> bytes:
    require_sha256(digest)
    try:
        value = managed_path(root, relative).read_bytes()
    except OSError as exc:
        raise CatalogError("Managed resource is unavailable.") from exc
    if hashlib.sha256(value).hexdigest() != digest:
        raise CatalogError("Managed resource hash does not match.")
    return value
