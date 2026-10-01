"""Program-directory ownership and read-only install preflight (no user DB access)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from ..domain.windows_paths import validate_child_name

APP_ID = "A5D9D2A7-9C93-4F13-9F1A-7C1C2E1D8D60"
PROGRAM_MANIFEST = ".training-feedback-program.json"
INSTALL_RECEIPT = ".training-feedback-install.json"


class InstallPathError(ValueError):
    pass


def missing_ownership_message(directory: Path, filename: str) -> str:
    return (
        f"程序目录缺少归属记录（{filename}），无法安全覆盖：{directory}\n"
        "如果这里是以前安装的 TrainingFeedback，请取消本次安装，"
        "使用旧程序的卸载器仅卸载程序并保留数据，然后重新运行安装器。\n"
        "如果这里存放的是其它文件，请保留这些文件，并选择新的空目录。"
        "本次检查不会删除程序目录或训练数据。"
    )


def local_path(value: str) -> Path:
    """Accept an absolute drive path without following aliases or trimming names."""
    if not isinstance(value, str) or not value or "\x00" in value:
        raise InstallPathError("Choose an absolute local program directory.")
    windows = PureWindowsPath(value)
    if not windows.is_absolute() or not re.fullmatch(r"[A-Za-z]:", windows.drive):
        raise InstallPathError("Network, device and relative paths are not supported.")
    raw_parts = re.split(r"[\\/]", value[3:].rstrip("\\/"))
    try:
        for part in raw_parts:
            validate_child_name(part)
    except ValueError as exc:
        raise InstallPathError("The program path contains an invalid directory name.") from exc
    return Path(str(windows))


def overlaps(first: Path, second: Path) -> bool:
    a, b = PureWindowsPath(str(first)), PureWindowsPath(str(second))
    return a == b or a in b.parents or b in a.parents


def checked_components(path: Path) -> None:
    for part in reversed((path, *path.parents)):
        try:
            metadata = part.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(metadata.st_mode)
                or getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise InstallPathError("Program paths cannot contain links or reparse points.")
        if part != path and not stat.S_ISDIR(metadata.st_mode):
            raise InstallPathError("A program-directory parent is not a directory.")


def relative_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise InstallPathError("The program ownership manifest is invalid.")
    try:
        for part in name.split("/"):
            validate_child_name(part)
    except ValueError as exc:
        raise InstallPathError("The program ownership manifest is invalid.") from exc
    target = root.joinpath(*name.split("/"))
    checked_components(target)
    return target


def file_digest(path: Path) -> str:
    checked_components(path)
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise InstallPathError("Program files must be ordinary files without hard links.")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(directory: Path) -> dict[str, str]:
    path = relative_file(directory, PROGRAM_MANIFEST)
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or value.get("format") != "training_feedback.program"
            or type(value.get("version")) is not int or value["version"] != 1
            or value.get("app_id") != APP_ID or not isinstance(value.get("files"), dict)):
        raise InstallPathError("This directory has no valid TrainingFeedback program manifest.")
    files = value["files"]
    if "TrainingFeedback.exe" not in files or PROGRAM_MANIFEST in files:
        raise InstallPathError("The program ownership manifest is incomplete.")
    for name, digest in files.items():
        relative_file(directory, name)
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise InstallPathError("The program ownership manifest is invalid.")
    return {**files, PROGRAM_MANIFEST: file_digest(path)}


def enumerate_files(directory: Path) -> set[str]:
    checked_components(directory)
    result = set()
    for current, directories, filenames in os.walk(directory, followlinks=False):
        parent = Path(current)
        for name in (*directories, *filenames):
            checked_components(parent / name)
        for name in filenames:
            result.add((parent / name).relative_to(directory).as_posix())
        for name in directories:
            if not any((parent / name).iterdir()):
                # Unknown empty directories are user-owned too.
                result.add((parent / name).relative_to(directory).as_posix() + "/")
    return result


def installed_files(directory: Path) -> dict[str, str]:
    try:
        files = read_manifest(directory)
    except FileNotFoundError as exc:
        raise InstallPathError(missing_ownership_message(directory, PROGRAM_MANIFEST)) from exc
    receipt_path = relative_file(directory, INSTALL_RECEIPT)
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InstallPathError(missing_ownership_message(directory, INSTALL_RECEIPT)) from exc
    if (not isinstance(receipt, dict) or receipt.get("app_id") != APP_ID
            or receipt.get("format") != "training_feedback.install"
            or type(receipt.get("version")) is not int or receipt["version"] != 1
            or receipt.get("manifest_sha256") != files[PROGRAM_MANIFEST]
            or PureWindowsPath(receipt.get("directory", "")) != PureWindowsPath(str(directory))
            or not isinstance(receipt.get("uninstaller"), dict)):
        raise InstallPathError("The installed program receipt is invalid.")
    uninstall_files = receipt["uninstaller"]
    if (len(uninstall_files) != 2 or not any(
        re.fullmatch(r"unins\d{3}\.exe", name) for name in uninstall_files
    )):
        raise InstallPathError("The installed uninstaller receipt is invalid.")
    for name, digest in uninstall_files.items():
        if (not re.fullmatch(r"unins\d{3}\.(exe|dat)", name)
                or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)):
            raise InstallPathError("The installed uninstaller receipt is invalid.")
    exe = next(name for name in uninstall_files if name.endswith(".exe"))
    if exe.removesuffix(".exe") + ".dat" not in uninstall_files:
        raise InstallPathError("The installed uninstaller receipt is invalid.")
    files.update(uninstall_files)
    files[INSTALL_RECEIPT] = file_digest(receipt_path)
    actual = enumerate_files(directory)
    if actual != set(files):
        raise InstallPathError(
            "This program directory contains unrelated files. Preserve them and choose an empty "
            "directory, or explicitly uninstall the program first."
        )
    for name, digest in files.items():
        if file_digest(relative_file(directory, name)) != digest:
            raise InstallPathError("Installed program files changed; uninstall the program first.")
    return files


@dataclass(frozen=True)
class InstallPolicy:
    home: Path
    protected: tuple[Path, ...]
    locator_directory: Path
    known_roots: tuple[Path, ...] = ()


def validate_install_target(value: str, policy: InstallPolicy) -> Path:
    target = local_path(value)
    if target == target.parent:
        raise InstallPathError("A drive root cannot be a program directory.")
    home, candidate = PureWindowsPath(str(policy.home)), PureWindowsPath(str(target))
    if candidate == home or candidate in home.parents:
        raise InstallPathError("The user home directory cannot be replaced by program files.")
    for boundary in (*policy.protected, policy.locator_directory, *policy.known_roots):
        if overlaps(target, boundary):
            raise InstallPathError("The program directory overlaps a protected or data directory.")
    checked_components(target)
    # Probe only exact ancestors, never discover databases or scan sibling roots.
    for parent in (target, *target.parents):
        if (parent / "training_feedback.marker.json").exists():
            raise InstallPathError("The program directory is inside a data root.")
    if target.exists():
        if not target.is_dir():
            raise InstallPathError("Choose a program directory, not a file.")
        if any(target.iterdir()):
            installed_files(target)
    ancestor = target
    while not ancestor.exists():
        ancestor = ancestor.parent
    if not os.access(ancestor, os.W_OK):
        raise InstallPathError("The program directory is not writable.")
    return target


def register_install(directory: Path, uninstaller: Path) -> None:
    """Record only payload + the exact Inno-generated uninstaller after installation."""
    files = read_manifest(directory)
    if (uninstaller.parent != directory
            or not re.fullmatch(r"unins\d{3}\.exe", uninstaller.name)):
        raise InstallPathError("The installed uninstaller is outside the program directory.")
    uninstall_files = {
        path.name: file_digest(path) for path in (uninstaller, uninstaller.with_suffix(".dat"))
    }
    expected = set(files) | set(uninstall_files)
    if enumerate_files(directory) - {INSTALL_RECEIPT} != expected:
        raise InstallPathError("Unexpected files remain; installation is incomplete.")
    for name, digest in files.items():
        if file_digest(relative_file(directory, name)) != digest:
            raise InstallPathError("Payload validation failed; installation is incomplete.")
    receipt = {"format": "training_feedback.install", "version": 1, "app_id": APP_ID,
               "directory": str(directory), "manifest_sha256": files[PROGRAM_MANIFEST],
               "uninstaller": uninstall_files}
    destination = relative_file(directory, INSTALL_RECEIPT)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    checked_components(temporary)
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, ensure_ascii=True, indent=2)
        stream.write("\n")
    temporary.replace(destination)
