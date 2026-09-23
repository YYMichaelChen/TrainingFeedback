"""Image validation results and eligibility decisions; no Qt, SQL or filesystem access."""

from dataclasses import dataclass

from .exercises import validate_guidance


@dataclass(frozen=True)
class ImageCheck:
    index: int
    required: bool
    valid: bool
    reason: str | None
    sha256: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class LibraryEligibility:
    text_complete: bool
    images_ready: bool
    removed: bool
    reviewed: bool
    reasons: tuple[str, ...]
    image_checks: tuple[ImageCheck, ...]

    @property
    def eligible(self) -> bool:
        return self.text_complete and self.images_ready and not self.removed


def image_hashes(checks: tuple[ImageCheck, ...]) -> list[dict]:
    return [{"index": check.index, "sha256": check.sha256} for check in checks if check.valid]


def assess_eligibility(content: dict, digest: str, checks: tuple[ImageCheck, ...],
                       review: dict | None, *, removed: bool = False) -> LibraryEligibility:
    guidance = content["guidance"]
    # Text completeness does not pretend that an image placeholder is a valid illustration.
    text = {**guidance, "images": [{"status": "missing"}]}
    try:
        complete = validate_guidance(text).complete
    except (TypeError, AttributeError):
        complete = False
    images_ready = any(check.valid for check in checks) and all(
        check.valid for check in checks if check.required
    )
    reasons = []
    if not complete:
        reasons.append("incomplete_text")
    if not images_ready:
        reasons.append("invalid_images")
    if removed:
        reasons.append("removed")
    reviewed = bool(
        complete and images_ready and review and review["event_type"] == "approved"
        and review["content_sha256"] == digest
        and review["image_hashes"] == image_hashes(checks)
        and all(check.valid or check.reason == "missing" for check in checks)
    )
    return LibraryEligibility(complete, images_ready, removed, reviewed, tuple(reasons), checks)
