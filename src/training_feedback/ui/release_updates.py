"""Qt transport and presentation for the process-scoped release check."""

from __future__ import annotations

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from ..application.release_updates import (
    LATEST_RELEASE_URL,
    ReleasePayloadError,
    UpdateCheckResult,
    checking_result,
    evaluate_latest_release,
    failed_result,
    idle_result,
)


class ReleaseUpdateCoordinator(QObject):
    """Own exactly one automatic check per application process."""

    result_changed = Signal(object)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.result = idle_result(current_version)
        self._manager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._automatic_started = False

    def start_once(self) -> bool:
        if self._automatic_started:
            return False
        self._automatic_started = True
        return self.check()

    def check(self) -> bool:
        if self._reply is not None:
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
        self._reply = self._manager.get(request)
        self._reply.finished.connect(self._finish)
        return True

    def _finish(self) -> None:
        reply, self._reply = self._reply, None
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

    def _set_result(self, result: UpdateCheckResult) -> None:
        self.result = result
        self.result_changed.emit(result)


class ReleaseDetailsDialog(QDialog):
    """Plain-text release details with browser-only external actions."""

    def __init__(self, result: UpdateCheckResult, parent=None):
        super().__init__(parent)
        release = result.release
        if release is None:
            raise ValueError("Release details require an available release.")
        self.release = release
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
        instruction = QLabel(
            "应用只会打开系统浏览器。下载完成后请自行运行 Setup 覆盖更新；"
            "应用不会自动下载、安装或退出。"
        )
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        buttons = QDialogButtonBox()
        release_button = buttons.addButton(
            "查看 GitHub Release", QDialogButtonBox.ButtonRole.ActionRole
        )
        download_button = buttons.addButton(
            "下载 Setup", QDialogButtonBox.ButtonRole.ActionRole
        )
        close_button = buttons.addButton("稍后", QDialogButtonBox.ButtonRole.RejectRole)
        release_button.clicked.connect(lambda: self._open(self.release.page_url))
        if release.setup is None:
            download_button.setEnabled(False)
        else:
            download_button.clicked.connect(lambda: self._open(self.release.setup.url))
        close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _open(self, url: str) -> None:
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self, "无法打开浏览器", "请稍后重试或手动访问 GitHub Release。")


def show_release_details(result: UpdateCheckResult, parent=None) -> None:
    ReleaseDetailsDialog(result, parent).exec()
