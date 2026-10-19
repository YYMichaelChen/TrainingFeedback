"""Bounded immutable byte snapshots for user-selected input files."""

from __future__ import annotations

from pathlib import Path


class FileTooLargeError(ValueError):
    pass


def read_limited_bytes(source: Path, maximum_bytes: int) -> bytes:
    """Read at most the accepted payload plus one overflow-detection byte."""
    with Path(source).open("rb") as stream:
        payload = stream.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes:
        raise FileTooLargeError
    return payload
