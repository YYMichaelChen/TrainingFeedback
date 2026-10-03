"""Qt transport and presentation for the process-scoped release check."""

from __future__ import annotations

import os
import shutil
import threading
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QObject,
    QProcess,
    QProcessEnvironment,
    QUrl,
    Signal,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
)

from ..application.release_updates import (
    LATEST_RELEASE_URL,
    ReleasePayloadError,
    SetupDownloadError,
    SetupDownloadVerifier,
    UpdateCheckResult,
    UpdateStatus,
    checking_result,
    cleanup_stale_update_directories,
    create_update_directory,
    evaluate_latest_release,
    failed_result,
    idle_result,
)

# 常规退出未生效时的硬退出兜底：启动器检测到本进程结束后才会打开安装程序。
_FORCE_QUIT_FALLBACK_MS = 10_000


def _force_quit() -> None:
    """最后兜底：常规退出未在限定时间内结束进程时硬退出。

    只在已校验下载完成、无用户数据写入进行时武装；SQLite WAL 可安全恢复。
    """
    os._exit(0)


def _request_application_exit() -> None:
    """Close visible windows before asking the application event loop to stop."""
    application = QCoreApplication.instance()
    if application is None:
        return
    try:
        close_all_windows = getattr(application, "closeAllWindows", None)
        if close_all_windows is not None:
            close_all_windows()
    finally:
        application.quit()


class ReleaseUpdateCoordinator(QObject):
    """Own the process-scoped release check and verified Setup download."""

    result_changed = Signal(object)
    download_started = Signal(object)
    download_progress = Signal(int, int)
    download_failed = Signal(str)
    installer_handoff_started = Signal(str)

    def __init__(self, current_version: str, parent=None, *, update_temp_root=None):
        super().__init__(parent)
        self.current_version = current_version
        self._update_temp_root = (
            None if update_temp_root is None else Path(update_temp_root)
        )
        cleanup_stale_update_directories(self._update_temp_root)
        self.result = idle_result(current_version)
        self._manager = QNetworkAccessManager(self)
        self._check_reply: QNetworkReply | None = None
        self._download_reply: QNetworkReply | None = None
        self._download_stream = None
        self._download_verifier: SetupDownloadVerifier | None = None
        self._download_directory: Path | None = None
        self._download_part: Path | None = None
        self._download_target: Path | None = None
        self._download_error = ""
        self._detached_launcher: QProcess | None = None
        self._force_quit_timer: threading.Timer | None = None
        self._automatic_started = False

    @property
    def download_active(self) -> bool:
        return self._download_reply is not None

    @property
    def download_received(self) -> int:
        if self._download_verifier is None:
            return 0
        return self._download_verifier.received

    @property
    def download_total(self) -> int:
        if self._download_verifier is None:
            return 0
        return self._download_verifier.asset.size

    @property
    def download_error(self) -> str:
        return self._download_error

    def start_once(self) -> bool:
        if self._automatic_started:
            return False
        self._automatic_started = True
        return self.check()

    def check(self) -> bool:
        if self._check_reply is not None or self._download_reply is not None:
            return False
        self._set_result(checking_result(self.current_version))
        request = QNetworkRequest(QUrl(LATEST_RELEASE_URL))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(
            b"User-Agent", f"TrainingFeedback/{self.current_version}".encode("ascii")
        )
        request.setRawHeader(b"X-GitHub-Api-Version", b"2026-03-10")
        request.setTransferTimeout(10_000)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self._check_reply = self._manager.get(request)
        self._check_reply.finished.connect(self._finish_check)
        return True

    def _finish_check(self) -> None:
        reply, self._check_reply = self._check_reply, None
        if reply is None:
            return
        result = failed_result(self.current_version)
        try:
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if reply.error() != QNetworkReply.NetworkError.NoError or status != 200:
                result = failed_result(self.current_version)
            else:
                try:
                    result = evaluate_latest_release(bytes(reply.readAll()), self.current_version)
                except ReleasePayloadError:
                    result = failed_result(self.current_version)
        finally:
            reply.deleteLater()
        self._set_result(result)

    def download_and_install(self) -> bool:
        release = self.result.release
        if (
            self.result.status != UpdateStatus.AVAILABLE
            or release is None
            or release.setup is None
            or self._download_reply is not None
        ):
            return False
        self._download_error = ""
        directory: Path | None = None
        try:
            directory = create_update_directory(self._update_temp_root)
            part = directory / f"{release.setup.name}.part"
            stream = part.open("xb")
        except OSError as exc:
            if directory is not None:
                shutil.rmtree(directory, ignore_errors=True)
            self._download_error = f"无法创建更新临时文件：{exc}"
            self.download_failed.emit(self._download_error)
            return False

        self._download_directory = directory
        self._download_part = part
        self._download_target = directory / release.setup.name
        self._download_stream = stream
        self._download_verifier = SetupDownloadVerifier(release.setup)

        request = QNetworkRequest(QUrl(release.setup.url))
        request.setRawHeader(b"Accept", b"application/octet-stream")
        request.setRawHeader(
            b"User-Agent", f"TrainingFeedback/{self.current_version}".encode("ascii")
        )
        request.setTransferTimeout(30_000)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self._download_reply = self._manager.get(request)
        self._download_reply.readyRead.connect(self._read_download)
        self._download_reply.finished.connect(self._finish_download)
        self.download_started.emit(release.setup)
        self.download_progress.emit(0, release.setup.size)
        return True

    def _read_download(self) -> None:
        reply = self._download_reply
        if reply is None or self._download_stream is None or self._download_verifier is None:
            return
        chunk = bytes(reply.readAll())
        if not chunk or self._download_error:
            return
        try:
            self._download_verifier.add(chunk)
            written = self._download_stream.write(chunk)
            if written != len(chunk):
                raise OSError("更新临时文件未完整写入。")
        except (OSError, SetupDownloadError) as exc:
            self._download_error = str(exc)
            reply.abort()
            return
        self.download_progress.emit(
            self._download_verifier.received, self._download_verifier.asset.size
        )

    def _finish_download(self) -> None:
        reply = self._download_reply
        if reply is None:
            return
        self._read_download()
        self._download_reply = None
        if self._download_stream is not None:
            try:
                self._download_stream.close()
            except OSError as exc:
                if not self._download_error:
                    self._download_error = str(exc)
            self._download_stream = None
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if not self._download_error and (
            reply.error() != QNetworkReply.NetworkError.NoError or status != 200
        ):
            self._download_error = "安装包下载失败，请重试或使用浏览器下载。"
        if not self._download_error and self._download_verifier is not None:
            try:
                self._download_verifier.finish()
                os.replace(self._download_part, self._download_target)
            except (OSError, SetupDownloadError) as exc:
                self._download_error = str(exc)
        reply.deleteLater()

        if self._download_error:
            message = self._download_error
            self._discard_download()
            self._download_error = message
            self.download_failed.emit(message)
            return

        target = self._download_target
        if target is None:
            self._download_error = "安装包临时路径丢失。"
            self._discard_download()
            self.download_failed.emit(self._download_error)
            return
        powershell = (
            Path(os.environ.get("SystemRoot", r"C:\Windows"))
            / "System32"
            / "WindowsPowerShell"
            / "v1.0"
            / "powershell.exe"
        )
        if not powershell.is_file():
            self._download_error = "无法找到系统更新启动程序，请重试或使用浏览器下载。"
            self._discard_download()
            self.download_failed.emit(self._download_error)
            return

        process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("TRAINING_FEEDBACK_UPDATE_PARENT_PID", str(os.getpid()))
        environment.insert("TRAINING_FEEDBACK_UPDATE_INSTALLER", str(target))
        environment.insert("TRAINING_FEEDBACK_UPDATE_DIRECTORY", str(target.parent))
        process.setProcessEnvironment(environment)
        process.setProgram(str(powershell))
        process.setArguments([
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
            "-Command",
            (
                "$parentId = [int]$env:TRAINING_FEEDBACK_UPDATE_PARENT_PID; "
                "Wait-Process -Id $parentId -ErrorAction SilentlyContinue; "
                "try { "
                "Start-Process -FilePath $env:TRAINING_FEEDBACK_UPDATE_INSTALLER "
                "-WorkingDirectory $env:TRAINING_FEEDBACK_UPDATE_DIRECTORY -Wait "
                "} finally { "
                "Remove-Item -LiteralPath $env:TRAINING_FEEDBACK_UPDATE_DIRECTORY "
                "-Recurse -Force -ErrorAction SilentlyContinue "
                "}"
            ),
        ])
        process.setWorkingDirectory(str(target.parent))
        started, _process_id = process.startDetached()
        if not started:
            self._download_error = "无法安排安装程序启动，请重试或使用浏览器下载。"
            self._discard_download()
            self.download_failed.emit(self._download_error)
            return
        self._detached_launcher = process
        # 硬退出不能依赖 Qt 事件循环：正是事件循环未继续推进时，
        # 先前的 QTimer 兜底也会一起失效。
        timer = threading.Timer(_FORCE_QUIT_FALLBACK_MS / 1000, _force_quit)
        timer.daemon = True
        self._force_quit_timer = timer
        timer.start()
        try:
            self.installer_handoff_started.emit(str(target))
        except Exception:
            # 启动器已在等待本进程；可视通知失败不影响退出。
            pass
        finally:
            # 先关闭可见窗口，再退出主事件循环；两步都不依赖
            # 对话框通知槽成功。若 Qt 关闭链路卡住，后台计时器最后兜底。
            _request_application_exit()

    def _discard_download(self) -> None:
        directory = self._download_directory
        self._download_verifier = None
        self._download_directory = None
        self._download_part = None
        self._download_target = None
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)

    def _set_result(self, result: UpdateCheckResult) -> None:
        self.result = result
        self.result_changed.emit(result)


class ReleaseDetailsDialog(QDialog):
    """Plain-text release details with verified in-app installation by default."""

    def __init__(self, coordinator: ReleaseUpdateCoordinator, parent=None):
        super().__init__(parent)
        result = coordinator.result
        release = result.release
        if release is None:
            raise ValueError("Release details require an available release.")
        self.release = release
        self.coordinator = coordinator
        self.setWindowTitle("应用更新")
        self.resize(620, 500)
        layout = QVBoxLayout(self)
        title = QLabel(f"发现新版本 v{release.version}")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            f"当前版本：{result.current_version}\n"
            f"发布时间：{release.published_at or '未提供'}"
        ))

        notes = QPlainTextEdit()
        notes.setReadOnly(True)
        notes.setPlainText(release.notes or "未提供发布说明。")
        layout.addWidget(notes, 1)

        if release.setup is None:
            asset_text = "未找到可验证的 Setup；请打开 GitHub Release 查看。"
        else:
            size_mib = release.setup.size / (1024 * 1024)
            asset_text = (
                f"安装包：{release.setup.name}\n"
                f"大小：{size_mib:.2f} MiB\n"
                f"SHA-256：{release.setup.sha256}"
            )
        asset_label = QLabel(asset_text)
        asset_label.setWordWrap(True)
        layout.addWidget(asset_label)
        self.instruction = QLabel()
        self.instruction.setWordWrap(True)
        layout.addWidget(self.instruction)
        self.progress = QProgressBar()
        self.progress.setObjectName("updateDownloadProgress")
        self.progress.setRange(0, 1000)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        buttons = QDialogButtonBox()
        self.install_button = buttons.addButton(
            "下载并安装", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.install_button.setDefault(True)
        release_button = buttons.addButton(
            "查看 GitHub Release", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.browser_button = buttons.addButton(
            "浏览器下载", QDialogButtonBox.ButtonRole.ActionRole
        )
        close_button = buttons.addButton("稍后", QDialogButtonBox.ButtonRole.RejectRole)
        self.install_button.clicked.connect(self._install)
        release_button.clicked.connect(lambda: self._open(self.release.page_url))
        if release.setup is None:
            self.install_button.setEnabled(False)
            self.browser_button.setEnabled(False)
            self.instruction.setText(
                "当前 Release 没有可验证的唯一安装包，只能打开 Release 页面查看。"
            )
        else:
            self.browser_button.clicked.connect(lambda: self._open(self.release.setup.url))
            self.instruction.setText(
                "默认由应用在后台下载并校验安装包；校验成功后会自动退出当前应用，"
                "退出完成后再打开安装程序。也可以选择浏览器下载。"
            )
        close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

        coordinator.download_started.connect(self._download_started)
        coordinator.download_progress.connect(self._download_progress)
        coordinator.download_failed.connect(self._download_failed)
        coordinator.installer_handoff_started.connect(self._installer_handoff_started)
        if coordinator.download_active:
            self._download_started(release.setup)
            self._download_progress(
                coordinator.download_received, coordinator.download_total
            )
        elif coordinator.download_error:
            self.instruction.setText(
                f"上次应用内更新失败：{coordinator.download_error}\n"
                "可以重试，或改用浏览器下载。"
            )

    def _install(self) -> None:
        self.coordinator.download_and_install()

    def _download_started(self, _asset) -> None:
        self.install_button.setEnabled(False)
        self.install_button.setText("后台下载中…")
        self.progress.setVisible(True)
        self.instruction.setText(
            "正在后台下载安装包；下载完成并校验通过后会先退出当前应用，再打开安装程序。"
        )

    def _download_progress(self, received: int, total: int) -> None:
        if total > 0:
            self.progress.setValue(min(1000, received * 1000 // total))

    def _download_failed(self, message: str) -> None:
        self.install_button.setEnabled(self.release.setup is not None)
        self.install_button.setText("重新下载并安装")
        self.progress.setVisible(False)
        self.instruction.setText("应用内更新未完成，可以重试，或改用浏览器下载。")
        QMessageBox.warning(self, "更新失败", message)

    def _installer_handoff_started(self, _path: str) -> None:
        self.instruction.setText(
            "安装包已校验，正在退出当前应用；退出后会自动打开安装程序。"
            "若长时间没有退出，请直接手动关闭本应用，安装程序同样会自动打开。"
        )
        self.accept()

    def _open(self, url: str) -> None:
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self, "无法打开浏览器", "请稍后重试或手动访问 GitHub Release。")


def show_release_details(coordinator: ReleaseUpdateCoordinator, parent=None) -> None:
    ReleaseDetailsDialog(coordinator, parent).exec()
