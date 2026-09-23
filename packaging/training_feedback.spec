# PyInstaller directory build for the native Windows application.
#
# Produces dist/TrainingFeedback/TrainingFeedback.exe with every runtime
# dependency collected next to it. Build via packaging/build.ps1, which
# verifies the toolchain before invoking this spec.
import os
import re
import sys
from pathlib import Path

project_root = Path(SPECPATH).parent
icon_path = project_root / "icon" / "TrainingFeedback.ico"
if not icon_path.is_file():
    raise FileNotFoundError(f"packaged icon missing: {icon_path}")


def find_sqlite_dll() -> Path:
    """Locate sqlite3.dll for build interpreters that ship it separately.

    Only the layouts of supported Windows build environments are tried; any
    other environment fails loudly instead of silently shipping a broken
    build.
    """
    candidates = [
        Path(sys.base_prefix) / "Library" / "bin" / "sqlite3.dll",  # conda layout
        Path(sys.base_prefix) / "DLLs" / "sqlite3.dll",  # python.org layout
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "sqlite3.dll was not collected by PyInstaller and none of the "
        f"supported build layouts provide it (base prefix: {sys.base_prefix})"
    )


def conda_runtime_dll(name: str) -> Path | None:
    """Return a Conda runtime DLL that PyInstaller may fail to resolve.

    Python.org environments either bundle the equivalent dependency beside the
    extension module or let PyInstaller resolve it normally. Conda exposes the
    unversioned import name from Library/bin, so collect that exact filename when
    this supported layout is selected.
    """
    candidate = Path(sys.base_prefix) / "Library" / "bin" / name
    return candidate if candidate.is_file() else None


def normalize_binary_sources(entries):
    """Keep collected DLLs inside declared build roots.

    The desktop host can register unrelated DLL directories in the Python process.
    PyInstaller's dependency scanner can then collect those files even after PATH
    has been isolated. Prefer the selected interpreter's same-named DLL; omit the
    Windows ICU/API-set contracts that the supported OS resolves; fail on every
    other external source.
    """
    allowed_roots = [project_root.resolve(), Path(os.environ["SystemRoot"]).resolve()]
    interpreter_dirs = [
        Path(sys.prefix) / "Library" / "bin",
        Path(sys.prefix) / "DLLs",
        Path(sys.base_prefix) / "Library" / "bin",
        Path(sys.base_prefix) / "DLLs",
    ]
    normalized = []
    for destination, source, typecode in entries:
        source_path = Path(source).resolve()
        if any(source_path == root or root in source_path.parents for root in allowed_roots):
            normalized.append((destination, source, typecode))
            continue

        filename = Path(destination).name
        replacement = next(
            (directory / filename for directory in interpreter_dirs
             if (directory / filename).is_file()),
            None,
        )
        if replacement is not None:
            print(f"Replacing external binary source: {destination} -> {replacement}")
            normalized.append((destination, str(replacement), typecode))
            continue

        lowered = filename.lower()
        if (lowered == "icuuc.dll" or re.fullmatch(r"icudt\d+\.dll", lowered)
                or lowered.startswith("api-ms-win-")):
            print(f"Using Windows system contract instead of external binary: {destination}")
            continue
        raise RuntimeError(
            f"PyInstaller selected a binary outside the project, interpreter, and Windows: "
            f"{destination} <- {source_path}"
        )
    return normalized

a = Analysis(
    [str(project_root / "src" / "training_feedback" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "src/training_feedback/ui/chevron.svg"), "training_feedback/ui"),
        (str(project_root / "src/training_feedback/catalog"), "training_feedback/catalog"),
        (str(project_root / "src/training_feedback/contracts"), "training_feedback/contracts"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
a.binaries = normalize_binary_sources(a.binaries)
if not any(destination.lower() == "sqlite3.dll" for destination, *_ in a.binaries):
    a.binaries.append(("sqlite3.dll", str(find_sqlite_dll()), "BINARY"))
ffi_dll = conda_runtime_dll("ffi.dll")
if ffi_dll and not any(destination.lower() == "ffi.dll" for destination, *_ in a.binaries):
    a.binaries.append(("ffi.dll", str(ffi_dll), "BINARY"))
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TrainingFeedback",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TrainingFeedback",
)
