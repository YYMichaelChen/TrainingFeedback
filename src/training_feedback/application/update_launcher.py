"""Windows update handoff with a watchdog outside the application process."""

from __future__ import annotations

import base64
import ctypes
import os
import subprocess
from ctypes import wintypes
from pathlib import Path

LAUNCHER_READY_FILENAME = ".update-launcher-ready"
LAUNCHER_LOG_FILENAME = "update-launcher.log"

# The inherited handle pins this exact process, including after its PID is reused.
# No executable-name lookup, process-tree termination or data-root access is used.
LAUNCHER_SCRIPT = r"""$ErrorActionPreference = 'Stop'
$directory = $env:TRAINING_FEEDBACK_UPDATE_DIRECTORY
$installer = $env:TRAINING_FEEDBACK_UPDATE_INSTALLER
$completed = $false
$parentHandle = [IntPtr]([long]$env:TRAINING_FEEDBACK_UPDATE_PARENT_HANDLE)
try {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class TrainingFeedbackUpdateParent {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool TerminateProcess(IntPtr handle, uint exitCode);
    [DllImport("kernel32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CloseHandle(IntPtr handle);
}
'@
    $state = [TrainingFeedbackUpdateParent]::WaitForSingleObject($parentHandle, 0)
    if ($state -ne 0 -and $state -ne 258) { throw 'Invalid application handle.' }
    [IO.File]::WriteAllText((Join-Path $directory '.update-launcher-ready'), 'ready')
    $state = [TrainingFeedbackUpdateParent]::WaitForSingleObject($parentHandle, 10000)
    if ($state -eq 258) {
        Write-Output 'Normal application exit timed out; terminating the bound process.'
        $terminated = [TrainingFeedbackUpdateParent]::TerminateProcess($parentHandle, 0)
        # TerminateProcess is asynchronous. Even a successful call is not proof of exit.
        $state = [TrainingFeedbackUpdateParent]::WaitForSingleObject($parentHandle, 30000)
        if ($state -ne 0) {
            throw "Application did not exit (termination requested: $terminated)."
        }
    }
    if ($state -ne 0) { throw 'Cannot confirm application exit; Setup was not started.' }
    Write-Output 'Application exited; starting verified Setup.'
    Start-Process -FilePath $installer -WorkingDirectory $directory -Wait
    $completed = $true
} catch {
    Write-Output $_.Exception.Message
    exit 1
} finally {
    if ('TrainingFeedbackUpdateParent' -as [type]) {
        [void][TrainingFeedbackUpdateParent]::CloseHandle($parentHandle)
    }
    # Retain diagnostics on failure. Later startup recognizes only owned artifacts.
    if ($completed) {
        Set-Location -LiteralPath $env:SystemRoot
        Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue
    }
}
"""


def start_update_launcher(target: Path) -> subprocess.Popen:
    """Start hidden PowerShell with only wait/terminate rights to this process.

    Called only after Setup verification and outside a user-data transaction.
    The caller waits for the ready artifact before requesting normal Qt exit.
    """
    if os.name != "nt":
        raise OSError("应用内安装仅支持 Windows。")
    target = target.resolve(strict=True)
    powershell = (
        Path(os.environ.get("SystemRoot", r"C:\Windows"))
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    if not powershell.is_file():
        raise OSError("无法找到系统更新启动程序。")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.DuplicateHandle.argtypes = [
        wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE,
        ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, wintypes.BOOL, wintypes.DWORD,
    ]
    kernel.DuplicateHandle.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    current = kernel.GetCurrentProcess()
    inherited = wintypes.HANDLE()
    # SYNCHRONIZE | PROCESS_TERMINATE, inheritable, without DUPLICATE_SAME_ACCESS.
    if not kernel.DuplicateHandle(
        current, current, current, ctypes.byref(inherited), 0x00100001, True, 0,
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        environment = dict(os.environ)
        environment.update(
            TRAINING_FEEDBACK_UPDATE_PARENT_HANDLE=str(inherited.value),
            TRAINING_FEEDBACK_UPDATE_INSTALLER=str(target),
            TRAINING_FEEDBACK_UPDATE_DIRECTORY=str(target.parent),
        )
        startup = subprocess.STARTUPINFO()
        startup.lpAttributeList = {"handle_list": [inherited.value]}
        encoded = base64.b64encode(LAUNCHER_SCRIPT.encode("utf-16-le")).decode("ascii")
        with (target.parent / LAUNCHER_LOG_FILENAME).open("xb") as log:
            return subprocess.Popen(
                [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive",
                 "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
                cwd=target.parent, env=environment, startupinfo=startup,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            )
    finally:
        kernel.CloseHandle(inherited)
