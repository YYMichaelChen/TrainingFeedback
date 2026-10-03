"""Illustration preview with access to the original pixels."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QScrollArea, QSizePolicy, QVBoxLayout


class IllustrationLabel(QLabel):
    def __init__(self, source: QPixmap, *, width: int = 760, parent=None):
        super().__init__(parent)
        self.source = source
        self.max_width = width
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(1, 1)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("单击查看原图")
        self._scale_to_viewport()

    def _scale_to_viewport(self):
        area = self.contentsRect()
        if area.width() <= 1 or area.height() <= 1:
            return
        screen = self.screen() or QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen is not None else 1.0
        logical_bounds = area.size().scaled(
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
        dialog.resize(min(1100, self.source.width() + 48),
                      min(850, self.source.height() + 48))
        layout = QVBoxLayout(dialog)
        image = QLabel()
        image.setPixmap(self.source)
        scroll = QScrollArea()
        scroll.setWidget(image)
        layout.addWidget(scroll)
        dialog.exec()
