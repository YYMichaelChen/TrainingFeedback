"""把外部审核答复原件保存为数据根内的受管文件。

审核记录里的自由文本备注无法保证出处可追溯，因此原始答复照 `handoff` 的受管导入原件
同样的方式复制进数据根：先复制文件，调用方的数据库写入失败时再删除副本。文件放在数据根内，
备份与整根复制才会带着它走。
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from .data_root import DataRootError

REVIEWS_DIRECTORY = "reviews"
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024


class ReviewAttachmentError(DataRootError):
    pass


@dataclass(frozen=True)
class ReviewAttachment:
    relative_path: str
    sha256: str
    original_name: str
    bytes: int

    def remove_from(self, data_root: Path) -> None:
        """数据库写入失败时清理已复制的原件，避免留下无人引用的文件。"""
        (Path(data_root) / self.relative_path).unlink(missing_ok=True)


def _managed_name(source: Path) -> str:
    """保留可读的原始文件名片段，并用随机前缀避免覆盖已有原件。"""
    stem = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", source.stem).strip("-")
    suffix = re.sub(r"[^0-9A-Za-z.]+", "", source.suffix)[:16]
    readable = (stem[:60] or "review") + suffix
    return f"review-{uuid.uuid4().hex}-{readable}"


def store_review_answer(data_root: Path, source: Path) -> ReviewAttachment:
    source = Path(source)
    if not source.is_file():
        raise ReviewAttachmentError("The selected review answer file was not found.")
    try:
        payload = source.read_bytes()
    except OSError as exc:
        raise ReviewAttachmentError("The review answer file could not be read.") from exc
    if len(payload) > MAX_ATTACHMENT_BYTES:
        raise ReviewAttachmentError("The review answer file is too large to store.")
    reviews = Path(data_root) / REVIEWS_DIRECTORY
    try:
        reviews.mkdir(parents=True, exist_ok=True)
        destination = reviews / _managed_name(source)
        destination.write_bytes(payload)
    except OSError as exc:
        raise ReviewAttachmentError("The review answer file could not be stored.") from exc
    return ReviewAttachment(
        relative_path=f"{REVIEWS_DIRECTORY}/{destination.name}",
        sha256=hashlib.sha256(payload).hexdigest(),
        original_name=source.name,
        bytes=len(payload),
    )
