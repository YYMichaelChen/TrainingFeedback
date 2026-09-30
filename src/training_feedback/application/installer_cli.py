"""Internal installer commands, dispatched before importing the Qt client."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ..data.installation import (
    INSTALL_RECEIPT,
    InstallPathError,
    InstallPolicy,
    checked_components,
    installed_files,
    local_path,
    overlaps,
    read_manifest,
    register_install,
    validate_install_target,
)
from ..data.locator import default_locator_path
from ..data.windows_files import BoundTree


def system_policy() -> InstallPolicy:
    locator = default_locator_path()
    checked_components(locator)
    roots = ()
    if locator.exists():
        try:
            value = json.loads(locator.read_text(encoding="utf-8"))
            roots = (local_path(value["data_root"]),)
        except (ValueError, KeyError, TypeError):
            # An occupied target still requires exact program ownership; ancestors are checked.
            roots = ()
    protected = tuple(Path(value) for key in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)")
                      if (value := os.environ.get(key)))
    if not protected:
        raise InstallPathError("System-directory boundaries could not be determined.")
    return InstallPolicy(Path.home(), protected, locator.parent, roots)


def remove_obsolete(directory: Path, payload: Path, policy: InstallPolicy) -> None:
    """Only exact, hash-verified former payload names; never recursively sweep a directory."""
    directory = validate_install_target(str(directory), policy)
    if not directory.exists() or not any(directory.iterdir()):
        return
    owned = installed_files(directory)
    incoming = read_manifest(payload)
    # Keep receipt until new registration; keep the exact Inno uninstaller and its data.
    stale = [name for name in owned if name not in incoming and name != INSTALL_RECEIPT
             and not name.startswith("unins")]
    with BoundTree(directory) as tree:
        inventory = tree.inventory()
        for name, digest in owned.items():
            if inventory.get(name, {}).get("sha256") != digest:
                raise InstallPathError("Program files changed after preflight; stopped.")
        for name in stale:
            tree.objects[name].delete()
        # Delete only now-empty owned parents of stale files, using their pinned handles.
        parents = {str(Path(name).parent).replace("\\", "/") for name in stale}
        for name in sorted(parents, key=lambda value: value.count("/"), reverse=True):
            if name not in {".", ""} and not any((directory / name).iterdir()):
                tree.objects[name].delete()


def main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("validate", "prepare", "register"))
    parser.add_argument("--directory", required=True)
    parser.add_argument("--payload")
    parser.add_argument("--uninstaller")
    parser.add_argument("--previous-directory")
    parser.add_argument("--result", required=True)
    args = parser.parse_args(arguments)
    result_path = Path(args.result)
    # The caller uses its own fresh temporary result file; never follow a redirected result.
    checked_components(result_path)
    try:
        directory = local_path(args.directory)
        if args.operation == "register":
            if not args.uninstaller:
                raise InstallPathError("Missing installed uninstaller identity.")
            register_install(directory, local_path(args.uninstaller))
        else:
            policy = system_policy()
            validate_install_target(args.directory, policy)
            if args.previous_directory:
                previous = local_path(args.previous_directory)
                if previous != directory and overlaps(previous, directory):
                    raise InstallPathError("Old and new program directories cannot overlap.")
            if args.uninstaller:
                owned = installed_files(directory)
                uninstaller = local_path(args.uninstaller)
                if (uninstaller.parent != directory or uninstaller.name not in owned
                        or not uninstaller.name.endswith(".exe")
                        or not uninstaller.name.startswith("unins")):
                    raise InstallPathError("The previous uninstaller identity is invalid.")
            if args.operation == "prepare":
                if not args.payload:
                    raise InstallPathError("Missing incoming payload identity.")
                remove_obsolete(directory, Path(args.payload), policy)
        message, code = "OK", 0
    except (InstallPathError, OSError, ValueError, TypeError) as exc:
        message, code = str(exc), 1
    # Plain UTF-8 text is deliberately readable by Inno without a JSON interpreter.
    with result_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(message + "\n")
    return code
