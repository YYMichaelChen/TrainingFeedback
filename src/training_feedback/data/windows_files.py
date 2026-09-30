"""Handle-bound Windows file operations; no recursive path-based deletion."""

from __future__ import annotations

import ctypes
import hashlib
import os
from ctypes import wintypes as w
from pathlib import Path


class FileSafetyError(OSError):
    pass


class FileInfo(ctypes.Structure):
    _fields_ = [("attributes", w.DWORD), ("created", w.FILETIME), ("accessed", w.FILETIME),
                ("written", w.FILETIME), ("volume", w.DWORD), ("size_high", w.DWORD),
                ("size_low", w.DWORD), ("links", w.DWORD), ("id_high", w.DWORD),
                ("id_low", w.DWORD)]


def api():
    if os.name != "nt":
        raise FileSafetyError("Data deletion requires the Windows safety backend.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p,
                                   w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    kernel.GetFileInformationByHandle.argtypes = [w.HANDLE, ctypes.POINTER(FileInfo)]
    kernel.GetFileInformationByHandle.restype = w.BOOL
    kernel.SetFileInformationByHandle.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    kernel.SetFileInformationByHandle.restype = w.BOOL
    kernel.SetFilePointerEx.argtypes = [w.HANDLE, ctypes.c_longlong, ctypes.c_void_p, w.DWORD]
    kernel.SetFilePointerEx.restype = w.BOOL
    kernel.ReadFile.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD,
                               ctypes.POINTER(w.DWORD), ctypes.c_void_p]
    kernel.ReadFile.restype = w.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    kernel.GetCurrentProcess.restype = w.HANDLE
    return kernel


def sid_text(sid, kernel, security) -> str:
    text = w.LPWSTR()
    security.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(w.LPWSTR)]
    security.ConvertSidToStringSidW.restype = w.BOOL
    if not security.ConvertSidToStringSidW(sid, ctypes.byref(text)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return text.value
    finally:
        kernel.LocalFree(ctypes.cast(text, ctypes.c_void_p))


def current_sid() -> str:
    kernel = api()
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    security.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
    security.OpenProcessToken.restype = w.BOOL
    security.GetTokenInformation.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                           w.DWORD, ctypes.POINTER(w.DWORD)]
    security.GetTokenInformation.restype = w.BOOL
    token = w.HANDLE()
    if not security.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        size = w.DWORD()
        security.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        buffer = ctypes.create_string_buffer(size.value)
        if not security.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        return sid_text(sid, kernel, security)
    finally:
        kernel.CloseHandle(token)


class BoundFile:
    """Reject aliases and pin an existing object against replacement until close."""

    def __init__(self, path: Path, *, delete=False, directory=False, owner: str | None = None):
        self.path = Path(path)
        self.kernel = api()
        self.handle = None
        access = 0x20080 | (0x10000 if delete else 0)  # READ_CONTROL, ATTRIBUTES, DELETE
        if not directory:
            access |= 0x80000000  # GENERIC_READ
        # Deny directory write handles as well as rename/delete: a pinned empty
        # directory must not be converted into a reparse point during inventory.
        # Creating children does not require a shared write handle on the parent.
        share = 1 if directory else 0
        handle = self.kernel.CreateFileW(str(path), access, share, None, 3,
                                         0x02000000 | 0x00200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise FileSafetyError("A selected file is in use or access is denied.")
        self.handle = handle
        try:
            info = self.info()
            if info.attributes & 0x400:
                raise FileSafetyError("Reparse points cannot be used for cleanup.")
            if bool(info.attributes & 0x10) != directory:
                raise FileSafetyError("A selected object changed its type.")
            if not directory and info.links != 1:
                raise FileSafetyError("Files with multiple hard links cannot be deleted.")
            if delete and info.attributes & 1:
                raise FileSafetyError("Read-only files cannot be safely removed.")
            if owner is not None and self.owner() != owner:
                raise FileSafetyError("Selected data does not belong to the current user.")
        except Exception:
            self.close()
            raise

    def info(self):
        info = FileInfo()
        if not self.kernel.GetFileInformationByHandle(self.handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        return info

    def owner(self) -> str:
        security = ctypes.WinDLL("advapi32", use_last_error=True)
        security.GetSecurityInfo.argtypes = [w.HANDLE, ctypes.c_int, w.DWORD,
                                            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
                                            ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.POINTER(ctypes.c_void_p)]
        security.GetSecurityInfo.restype = w.DWORD
        owner, descriptor = ctypes.c_void_p(), ctypes.c_void_p()
        code = security.GetSecurityInfo(self.handle, 1, 1, ctypes.byref(owner), None,
                                        None, None, ctypes.byref(descriptor))
        if code:
            raise ctypes.WinError(code)
        try:
            return sid_text(owner, self.kernel, security)
        finally:
            self.kernel.LocalFree(descriptor)

    def identity(self) -> dict:
        info = self.info()
        return {"volume": info.volume, "file_id": (info.id_high << 32) | info.id_low,
                "directory": bool(info.attributes & 0x10)}

    def digest(self) -> str:
        digest = hashlib.sha256()
        for chunk in self.chunks():
            digest.update(chunk)
        return digest.hexdigest()

    def read_bytes(self) -> bytes:
        return b"".join(self.chunks())

    def chunks(self):
        if not self.kernel.SetFilePointerEx(self.handle, 0, None, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        buffer = ctypes.create_string_buffer(1024 * 1024)
        count = w.DWORD()
        while True:
            if not self.kernel.ReadFile(
                self.handle, buffer, len(buffer), ctypes.byref(count), None,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            if not count.value:
                break
            yield buffer.raw[:count.value]

    def delete(self):
        # FILE_DISPOSITION_INFO.DeleteFile is a BOOLEAN. Deletion occurs on handle close.
        disposition = ctypes.c_ubyte(1)
        if not self.kernel.SetFileInformationByHandle(
            self.handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition),
        ):
            raise FileSafetyError("A confirmed object could not be deleted.")
        self.close()

    def close(self):
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class BoundTree:
    """Pin every ancestor and every confirmed descendant before deleting anything."""

    def __init__(self, root: Path, *, owner: str | None = None):
        self.root = Path(root)
        self.parents = []
        self.objects = {}
        try:
            for path in reversed(self.root.parents):
                self.parents.append(BoundFile(path, directory=True))
            self.objects[""] = BoundFile(self.root, directory=True, delete=True, owner=owner)
            self._collect(self.root, owner)
        except Exception:
            self.close()
            raise

    def _collect(self, directory, owner):
        # A held nonempty directory cannot be renamed/deleted. No reparse point is traversed.
        for path in sorted(directory.iterdir()):
            attributes = path.lstat().st_file_attributes
            if attributes & 0x400:
                raise FileSafetyError("Cleanup inventory contains a reparse point.")
            is_directory = bool(attributes & 0x10)
            relative = path.relative_to(self.root).as_posix()
            self.objects[relative] = BoundFile(path, directory=is_directory,
                                               delete=True, owner=owner)
            if is_directory:
                self._collect(path, owner)

    def inventory(self) -> dict:
        result = {}
        for name, bound in self.objects.items():
            identity = bound.identity()
            if not identity["directory"]:
                identity["sha256"] = bound.digest()
                info = bound.info()
                identity["bytes"] = (info.size_high << 32) | info.size_low
            result[name] = identity
        return result

    def close(self):
        for bound in reversed(list(self.objects.values())):
            bound.close()
        for bound in reversed(self.parents):
            bound.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
