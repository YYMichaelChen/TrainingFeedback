"""Installer safety is exercised only on isolated fake payloads and synthetic paths."""

import hashlib
import json
import os
import subprocess
import sys

import pytest

from training_feedback.application import installer_cli
from training_feedback.data.installation import (
    APP_ID,
    INSTALL_RECEIPT,
    PROGRAM_MANIFEST,
    InstallPathError,
    InstallPolicy,
    installed_files,
    local_path,
    register_install,
    validate_install_target,
)


@pytest.fixture
def policy(tmp_path):
    return InstallPolicy(tmp_path / "home", (tmp_path / "Windows", tmp_path / "Program Files"),
                         tmp_path / "profile/TrainingFeedback", (tmp_path / "data",))


def payload(path, *, extra=None):
    path.mkdir(parents=True)
    files = {"TrainingFeedback.exe": b"synthetic executable, never launched",
             "_internal/current.dll": b"synthetic dll", **(extra or {})}
    for name, data in files.items():
        destination = path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    manifest = {"format": "training_feedback.program", "version": 1, "app_id": APP_ID,
                "application_version": "synthetic-current",
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    (path / PROGRAM_MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    return path


def installed(path, **kwargs):
    payload(path, **kwargs)
    for suffix in ("exe", "dat"):
        (path / f"unins000.{suffix}").write_bytes(b"synthetic Inno file, never launched")
    register_install(path, path / "unins000.exe")
    return path


@pytest.mark.parametrize("name", [
    "relative/path", r"C:relative", r"\\server\share\program", r"\\?\C:\program",
    "C:\\", r"C:\program\..\other", r"C:\program\CON.txt", "C:\\program\\bad. ",
])
def test_install_refuses_ambiguous_or_dangerous_syntax(name, policy):
    with pytest.raises(InstallPathError):
        validate_install_target(name, policy)


def test_custom_chinese_space_path_and_tail_separator_are_safe(tmp_path, policy):
    target = tmp_path / "我的程序 安装" / "TrainingFeedback"
    assert validate_install_target(str(target) + "\\", policy) == target
    assert not target.exists()
    assert local_path(str(target).replace("\\", "/")) == target


@pytest.mark.parametrize("boundary", ["Windows", "Program Files", "data", "home"])
def test_protected_and_known_root_paths_are_refused_without_writes(tmp_path, policy, boundary):
    target = tmp_path / boundary
    target.mkdir()
    original = target / "keep.txt"
    original.write_bytes(b"untouched synthetic sentinel")
    with pytest.raises(InstallPathError):
        validate_install_target(str(target), policy)
    assert original.read_bytes() == b"untouched synthetic sentinel"


def test_marker_ancestor_is_refused_without_opening_database(tmp_path, policy):
    root = tmp_path / "unregistered-synthetic-root"
    root.mkdir()
    marker = root / "training_feedback.marker.json"
    marker.write_bytes(b"do not parse or discover my database")
    with pytest.raises(InstallPathError, match="inside a data root"):
        validate_install_target(str(root / "program"), policy)
    assert marker.read_bytes() == b"do not parse or discover my database"


def test_unrelated_directory_is_refused_and_preserved(tmp_path, policy):
    target = tmp_path / "occupied"
    target.mkdir()
    (target / "notes.txt").write_bytes(b"untouched")
    with pytest.raises((InstallPathError, OSError)):
        validate_install_target(str(target), policy)
    assert (target / "notes.txt").read_bytes() == b"untouched"


def test_registered_payload_validates_but_modified_binary_is_refused(tmp_path, policy):
    target = installed(tmp_path / "program")
    assert validate_install_target(str(target), policy) == target
    (target / "_internal/current.dll").write_bytes(b"modified")
    with pytest.raises(InstallPathError, match="changed"):
        validate_install_target(str(target), policy)
    assert (target / "_internal/current.dll").read_bytes() == b"modified"


def test_unknown_empty_directory_is_not_installer_owned(tmp_path):
    target = installed(tmp_path / "program")
    (target / "my-empty-directory").mkdir()
    with pytest.raises(InstallPathError, match="unrelated files"):
        installed_files(target)
    assert (target / "my-empty-directory").is_dir()


def test_prepare_removes_only_hash_verified_obsolete_payload(tmp_path, policy):
    target = installed(tmp_path / "program", extra={"_internal/obsolete.dll": b"old"})
    incoming = payload(tmp_path / "incoming")
    old_receipt = (target / INSTALL_RECEIPT).read_bytes()
    installer_cli.remove_obsolete(target, incoming, policy)
    assert not (target / "_internal/obsolete.dll").exists()
    assert (target / INSTALL_RECEIPT).read_bytes() == old_receipt
    assert (target / "TrainingFeedback.exe").read_bytes().startswith(b"synthetic")


def test_prepare_refuses_unknown_file_before_any_deletion(tmp_path, policy):
    target = installed(tmp_path / "program", extra={"_internal/obsolete.dll": b"old"})
    incoming = payload(tmp_path / "incoming")
    (target / "_internal/user-note.txt").write_bytes(b"user text")
    with pytest.raises(InstallPathError, match="unrelated"):
        installer_cli.remove_obsolete(target, incoming, policy)
    assert (target / "_internal/obsolete.dll").read_bytes() == b"old"
    assert (target / "_internal/user-note.txt").read_bytes() == b"user text"


def test_registration_failure_never_claims_install_complete(tmp_path):
    target = payload(tmp_path / "program")
    (target / "unins000.exe").write_bytes(b"synthetic")
    (target / "unins000.dat").write_bytes(b"synthetic")
    (target / "unknown.txt").write_bytes(b"preserve")
    with pytest.raises(InstallPathError, match="incomplete"):
        register_install(target, target / "unins000.exe")
    assert not (target / INSTALL_RECEIPT).exists()
    assert (target / "unknown.txt").read_bytes() == b"preserve"


def test_hardlinked_program_file_is_refused(tmp_path):
    target = installed(tmp_path / "program")
    os.link(target / "_internal/current.dll", tmp_path / "external.dll")
    with pytest.raises(InstallPathError, match="hard links"):
        installed_files(target)
    assert (tmp_path / "external.dll").read_bytes() == b"synthetic dll"


def test_actual_junction_is_refused_and_external_sentinel_preserved(tmp_path, policy):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"preserve")
    link = tmp_path / "redirect"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                   check=True, capture_output=True)
    with pytest.raises(InstallPathError, match="reparse"):
        validate_install_target(str(link / "program"), policy)
    assert (outside / "sentinel").read_bytes() == b"preserve"


def test_cli_failure_reports_error_and_preserves_target(tmp_path, policy, monkeypatch):
    monkeypatch.setattr(installer_cli, "system_policy", lambda: policy)
    target = tmp_path / "data"
    result = tmp_path / "result.txt"
    assert installer_cli.main([
        "validate", "--directory", str(target), "--result", str(result),
    ]) == 1
    assert "overlaps" in result.read_text(encoding="utf-8")
    assert not target.exists()


def test_main_helper_dispatch_does_not_import_qt_or_open_locator(tmp_path):
    result = tmp_path / "result.txt"
    script = (
        "import sys; from training_feedback import main; "
        "sys.argv=['synthetic','--installer-helper','validate','--directory','relative',"
        f"'--result',{str(result)!r}]; "
        "code=main.main(); assert code==1; "
        "assert not any(name.startswith('PySide6') for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", script], check=True, capture_output=True)
    assert "relative paths" in result.read_text(encoding="utf-8")
