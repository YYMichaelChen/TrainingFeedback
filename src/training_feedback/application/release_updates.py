"""Pure GitHub Release parsing and application-version comparison."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlsplit

REPOSITORY = "YYMichaelChen/TrainingFeedback"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
MAX_RELEASE_RESPONSE_BYTES = 1_048_576
UPDATE_DIRECTORY_PREFIX = "TrainingFeedback-update-"
UPDATE_MARKER_FILENAME = ".training-feedback-update"
UPDATE_MARKER_CONTENT = "TrainingFeedback update download\n"

_VERSION = re.compile(r"^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_DIGEST = re.compile(r"^sha256:([0-9a-fA-F]{64})$")
_UPDATE_DIRECTORY = re.compile(r"^TrainingFeedback-update-[a-z0-9_]{8}$")
_UPDATE_FILE = re.compile(
    r"^TrainingFeedback-(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)-Setup\.exe(?:\.part)?$"
)


class ReleasePayloadError(ValueError):
    """The remote response is not a release this application can trust."""


class SetupDownloadError(ValueError):
    """The downloaded Setup does not match the selected release asset."""


class UpdateStatus(str, Enum):
    IDLE = "idle"
    CHECKING = "checking"
    CURRENT = "current"
    AHEAD = "ahead"
    AVAILABLE = "available"
    FAILED = "failed"


@dataclass(frozen=True)
class SetupAsset:
    name: str
    url: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    name: str
    notes: str
    page_url: str
    published_at: str
    setup: SetupAsset | None


@dataclass(frozen=True)
class UpdateCheckResult:
    status: UpdateStatus
    current_version: str
    release: ReleaseInfo | None = None


def create_update_directory(temp_root: Path | None = None) -> Path:
    """Create and mark one application-owned temporary update directory."""
    directory = Path(tempfile.mkdtemp(
        prefix=UPDATE_DIRECTORY_PREFIX,
        dir=None if temp_root is None else temp_root,
    ))
    try:
        (directory / UPDATE_MARKER_FILENAME).write_text(
            UPDATE_MARKER_CONTENT, encoding="ascii", newline="\n"
        )
    except OSError:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return directory


def cleanup_stale_update_directories(temp_root: Path | None = None) -> int:
    """Best-effort removal of strictly recognized updater temporary directories."""
    root = Path(tempfile.gettempdir()) if temp_root is None else Path(temp_root)
    try:
        resolved_root = root.resolve(strict=True)
        candidates = list(root.iterdir())
    except OSError:
        return 0

    removed = 0
    for directory in candidates:
        if _UPDATE_DIRECTORY.fullmatch(directory.name) is None:
            continue
        try:
            if (
                not directory.is_dir()
                or directory.is_symlink()
                or directory.is_junction()
                or directory.resolve(strict=True).parent != resolved_root
            ):
                continue
            entries = list(directory.iterdir())
            if not entries:
                continue
            marker = directory / UPDATE_MARKER_FILENAME
            if not all(
                entry.is_file()
                and not entry.is_symlink()
                and (entry.name == UPDATE_MARKER_FILENAME or _UPDATE_FILE.fullmatch(entry.name))
                for entry in entries
            ):
                continue
            if marker in entries:
                if marker.read_text(encoding="ascii") != UPDATE_MARKER_CONTENT:
                    continue
            elif not any(_UPDATE_FILE.fullmatch(entry.name) for entry in entries):
                continue
        except (OSError, UnicodeError):
            continue
        shutil.rmtree(directory, ignore_errors=True)
        if not directory.exists():
            removed += 1
    return removed


class SetupDownloadVerifier:
    """Incrementally verify the exact size and digest of one Setup asset."""

    def __init__(self, asset: SetupAsset):
        self.asset = asset
        self.received = 0
        self._digest = hashlib.sha256()

    def add(self, chunk: bytes) -> None:
        self.received += len(chunk)
        if self.received > self.asset.size:
            raise SetupDownloadError("安装包大小超过发布记录。")
        self._digest.update(chunk)

    def finish(self) -> None:
        if self.received != self.asset.size:
            raise SetupDownloadError("安装包大小与发布记录不一致。")
        if not hmac.compare_digest(self._digest.hexdigest(), self.asset.sha256):
            raise SetupDownloadError("安装包 SHA-256 与发布记录不一致。")


def checking_result(current_version: str) -> UpdateCheckResult:
    return UpdateCheckResult(UpdateStatus.CHECKING, current_version)


def failed_result(current_version: str) -> UpdateCheckResult:
    return UpdateCheckResult(UpdateStatus.FAILED, current_version)


def idle_result(current_version: str) -> UpdateCheckResult:
    return UpdateCheckResult(UpdateStatus.IDLE, current_version)


def _version(value: object, *, tag: bool = False) -> tuple[str, tuple[int, int, int]]:
    if not isinstance(value, str):
        raise ReleasePayloadError("Release version is missing.")
    if tag and not value.startswith("v"):
        raise ReleasePayloadError("Release tag must start with v.")
    match = _VERSION.fullmatch(value)
    if match is None:
        raise ReleasePayloadError("Release version is not X.Y.Z.")
    parts = tuple(int(part) for part in match.groups())
    return ".".join(str(part) for part in parts), parts


def _trusted_url(value: object, expected_path: str) -> str:
    if not isinstance(value, str):
        raise ReleasePayloadError("Release URL is missing.")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() != "github.com"
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ReleasePayloadError("Release URL is not trusted.")
    return value


def _setup_asset(assets: object, version: str, tag: str) -> SetupAsset | None:
    if not isinstance(assets, list):
        return None
    expected_name = f"TrainingFeedback-{version}-Setup.exe"
    matches = [asset for asset in assets if isinstance(asset, dict)
               and asset.get("name") == expected_name]
    if len(matches) != 1:
        return None
    asset = matches[0]
    digest = asset.get("digest")
    size = asset.get("size")
    match = _DIGEST.fullmatch(digest) if isinstance(digest, str) else None
    if (
        asset.get("state") != "uploaded"
        or match is None
        or type(size) is not int
        or size <= 0
    ):
        return None
    expected_path = f"/{REPOSITORY}/releases/download/{tag}/{expected_name}"
    try:
        url = _trusted_url(asset.get("browser_download_url"), expected_path)
    except ReleasePayloadError:
        return None
    return SetupAsset(expected_name, url, size, match.group(1).lower())


def evaluate_latest_release(raw: bytes, current_version: str) -> UpdateCheckResult:
    """Validate one latest-release response and compare it to the running version."""
    if len(raw) > MAX_RELEASE_RESPONSE_BYTES:
        raise ReleasePayloadError("Release response is too large.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleasePayloadError("Release response is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ReleasePayloadError("Release response is not an object.")
    if payload.get("draft") is not False or payload.get("prerelease") is not False:
        raise ReleasePayloadError("Latest release is not a stable published release.")

    normalized_current, current_parts = _version(current_version)
    tag = payload.get("tag_name")
    normalized_latest, latest_parts = _version(tag, tag=True)
    page_url = _trusted_url(
        payload.get("html_url"), f"/{REPOSITORY}/releases/tag/{tag}"
    )
    name = payload.get("name")
    notes = payload.get("body")
    published_at = payload.get("published_at")
    if name is None:
        name = tag
    if notes is None:
        notes = ""
    if not all(isinstance(value, str) for value in (name, notes, published_at)):
        raise ReleasePayloadError("Release text fields are invalid.")

    release = ReleaseInfo(
        version=normalized_latest,
        tag=tag,
        name=name,
        notes=notes,
        page_url=page_url,
        published_at=published_at,
        setup=_setup_asset(payload.get("assets"), normalized_latest, tag),
    )
    if current_parts < latest_parts:
        status = UpdateStatus.AVAILABLE
    elif current_parts > latest_parts:
        status = UpdateStatus.AHEAD
    else:
        status = UpdateStatus.CURRENT
    return UpdateCheckResult(status, normalized_current, release)
