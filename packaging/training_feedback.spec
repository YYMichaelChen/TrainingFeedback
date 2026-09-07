# PyInstaller development smoke build for the native Windows application.
from pathlib import Path

project_root = Path(SPECPATH).parent
sqlite_dll = Path(__import__("sys").prefix) / "Library" / "bin" / "sqlite3.dll"

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
a.binaries.append(("sqlite3.dll", str(sqlite_dll), "BINARY"))
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TrainingFeedback",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
