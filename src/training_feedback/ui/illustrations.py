"""Illustration preview with access to the original pixels."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QScrollArea, QVBoxLayout


class IllustrationLabel(QLabel):
    def __init__(self, source: QPixmap, *, width: int = 760, parent=None):
        super().__init__(parent)
        self.source = source
        self.setPixmap(source.scaledToWidth(
            min(width, source.width()), Qt.TransformationMode.SmoothTransformation,
        ))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("单击查看原图")

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
