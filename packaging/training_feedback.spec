# PyInstaller directory build for the native Windows application.
#
# Produces dist/TrainingFeedback/TrainingFeedback.exe with every runtime
# dependency collected next to it. Build via packaging/build.ps1, which
# verifies the toolchain before invoking this spec.
from pathlib import Path
import sys

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

a = Analysis(
    [str(project_root / "src" / "training_feedback" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
if not any(destination.lower() == "sqlite3.dll" for destination, *_ in a.binaries):
    a.binaries.append(("sqlite3.dll", str(find_sqlite_dll()), "BINARY"))
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
