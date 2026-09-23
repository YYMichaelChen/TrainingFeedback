"""Technical image inspection. Domain code consumes only the returned value objects."""

from __future__ import annotations

import hashlib

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImageReader

from ..domain.library_eligibility import ImageCheck


def decode_image_size(data: bytes) -> tuple[int, int]:
    buffer = QBuffer()
    buffer.setData(QByteArray(data))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer)
    reader.setDecideFormatFromContent(True)
    image = reader.read()
    if image.isNull() or image.width() <= 0 or image.height() <= 0:
        raise ValueError("Image bytes cannot be decoded.")
    return image.width(), image.height()


def image_file_extension(data: bytes) -> str:
    """Use the decoded format for portable export filenames, not an untrusted source suffix."""
    decode_image_size(data)
    buffer = QBuffer()
    buffer.setData(QByteArray(data))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer)
    reader.setDecideFormatFromContent(True)
    extension = bytes(reader.format()).decode("ascii").lower()
    if not extension or not extension.isalnum():
        raise ValueError("Image format cannot be exported.")
    return extension


def inspect_images(images: list[dict], read_image) -> tuple[ImageCheck, ...]:
    checks = []
    for index, image in enumerate(images):
        required = image["required"]
        if image.get("placeholder") is True:
            checks.append(ImageCheck(index, required, False, "placeholder"))
            continue
        if image["status"] == "missing":
            checks.append(ImageCheck(index, required, False, "missing"))
            continue
        try:
            data = read_image(image)
        except (OSError, ValueError, KeyError):
            checks.append(ImageCheck(index, required, False, "unavailable"))
            continue
        digest = hashlib.sha256(data).hexdigest()
        if digest != image["sha256"]:
            checks.append(ImageCheck(index, required, False, "hash_mismatch"))
            continue
        try:
            width, height = decode_image_size(data)
        except ValueError:
            checks.append(ImageCheck(index, required, False, "undecodable"))
            continue
        checks.append(ImageCheck(index, required, True, None, digest, width, height))
    return tuple(checks)
