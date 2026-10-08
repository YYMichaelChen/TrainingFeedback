"""Illustration preview with access to the original pixels."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QScrollArea, QSizePolicy, QVBoxLayout

from .sizing import bind_units, fit_dialog, u


class IllustrationLabel(QLabel):
    def __init__(self, source: QPixmap, *, width: int | None = None, parent=None):
        super().__init__(parent)
        self.source = source
        self.max_width = width if width is not None else u(47.5)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bind_units(self, "setMinimumSize", 0.0625, 0.0625)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("单击查看原图")
        self._scale_to_viewport()

    def _source_size(self) -> QSize:
        dpr = self.source.devicePixelRatio() or 1.0
        return QSize(
            max(1, round(self.source.width() / dpr)),
            max(1, round(self.source.height() / dpr)),
        )

    def heightForWidth(self, width: int) -> int:
        source = self._source_size()
        display_width = min(self.max_width, max(1, width))
        return max(1, round(display_width * source.height() / source.width()))

    def sizeHint(self) -> QSize:
        return QSize(self.max_width, self.heightForWidth(self.max_width))

    def minimumSizeHint(self) -> QSize:
        width = min(u(22.5), self.max_width)
        return QSize(width, self.heightForWidth(width))

    def _scale_to_viewport(self):
        area = self.contentsRect()
        if area.width() <= 1 or area.height() <= 1:
            return
        screen = self.screen() or QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen is not None else 1.0
        logical_bounds = self._source_size().scaled(
            min(self.max_width, area.width()), area.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        physical = self.source.scaled(
            round(logical_bounds.width() * dpr), round(logical_bounds.height() * dpr),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        physical.setDevicePixelRatio(dpr)
        self.setPixmap(physical)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_to_viewport()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        dialog = QDialog(self)
        dialog.setWindowTitle("动作示意图 · 原图")
        fit_dialog(dialog, width=.9, height=.9, square=True)
        layout = QVBoxLayout(dialog)
        image = QLabel()
        image.setPixmap(self.source)
        scroll = QScrollArea()
        scroll.setWidget(image)
        layout.addWidget(scroll)
        dialog.exec()
