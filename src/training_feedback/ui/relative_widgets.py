"""Native equivalents of auto-height fields, proportional grids and local scrolling."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from .sizing import scale_manager, u


class LocalScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        event.accept()


class _VerticalGrip(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setToolTip("拖动下沿调整输入框高度")
        self.origin = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = (event.globalPosition().y(), self.editor.height())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            height = self.origin[1] + event.globalPosition().y() - self.origin[0]
            self.editor.height_units = max(self.editor.minimum_lines_height() / u(), height / u())
            self.editor.update_height()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.origin = None
        event.accept()


class ResizableTextEdit(QPlainTextEdit):
    """Three visible lines initially; a native vertical grip grows within its scroll host."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.height_units = 0
        self.grip = _VerticalGrip(self)
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self.update_height)
        self.update_height()

    def minimum_lines_height(self):
        return self.fontMetrics().lineSpacing() * 3 + u(1)

    def update_height(self):
        self.setFixedHeight(max(self.minimum_lines_height(), u(self.height_units)))
        self.setViewportMargins(0, 0, 0, u(.5))
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.grip.setGeometry(0, self.height() - u(.5), self.width(), u(.5))

    def wheelEvent(self, event):
        super().wheelEvent(event)
        event.accept()


class AdaptiveFields(QWidget):
    def __init__(self, minimum=14, parent=None, *, max_columns=4):
        super().__init__(parent)
        self.minimum = minimum
        self.max_columns = max_columns
        self.fields = []
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.columns = 0
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self.reflow)

    def addRow(self, title, widget):
        cell = QWidget()
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setWordWrap(True)
        layout.addWidget(label)
        widget.setMinimumWidth(0)
        policy = widget.sizePolicy()
        policy.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
        widget.setSizePolicy(policy)
        layout.addWidget(widget)
        self.fields.append(cell)
        self.columns = 0
        self.reflow()

    def reflow(self):
        columns = max(1, min(self.max_columns,
                             (self.width() + u(1)) // max(1, u(self.minimum + 1))))
        self.grid.setHorizontalSpacing(u(1))
        self.grid.setVerticalSpacing(u(.5))
        if columns == self.columns:
            return
        old_columns, self.columns = self.columns, columns
        for index in range(max(old_columns, columns)):
            self.grid.setColumnStretch(index, 1 if index < columns else 0)
        for index, cell in enumerate(self.fields):
            self.grid.addWidget(cell, index // columns, index % columns)
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()


class RelativeTable(QTableWidget):
    def __init__(self, weights, parent=None):
        super().__init__(0, len(weights), parent)
        self.weights = weights
        self.height_budget = lambda: u(36)
        self.setMinimumWidth(u(28))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setStretchLastSection(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.verticalHeader().hide()
        self.setWordWrap(True)
        self.model().rowsInserted.connect(self.update_metrics)
        self.model().rowsRemoved.connect(self.update_metrics)
        self.model().dataChanged.connect(self.update_metrics)
        self.model().modelReset.connect(self.update_metrics)
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self.update_metrics)
        self.update_metrics()

    def update_metrics(self, *_):
        minimum = u(28)
        for column, weight in enumerate(self.weights):
            content = max((self.cellWidget(row, column).minimumSizeHint().width()
                           for row in range(self.rowCount())
                           if self.cellWidget(row, column) is not None), default=0)
            minimum = max(minimum, round((content + u(.25)) * sum(self.weights) / weight))
        self.setMinimumWidth(minimum)
        self.horizontalHeader().setMinimumSectionSize(u(1.5))
        width = max(1, self.viewport().width())
        assigned = 0
        for column, weight in enumerate(self.weights):
            size = (width - assigned if column == len(self.weights) - 1
                    else round(width * weight / sum(self.weights)))
            self.setColumnWidth(column, size)
            assigned += size
        self.verticalHeader().setMinimumSectionSize(u(2.5))
        self.verticalHeader().setDefaultSectionSize(u(2.5))
        self.resizeRowsToContents()
        height = self.horizontalHeader().sizeHint().height() + sum(
            self.rowHeight(row) for row in range(self.rowCount())
        ) + self.frameWidth() * 2
        if self.rowCount() > 8:
            height = min(height, max(u(5), round(self.height_budget() * .5)))
        self.setFixedHeight(max(u(2.5), height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_metrics()

    def sizeHint(self):
        return QSize(u(28), self.height())

    def wheelEvent(self, event):
        super().wheelEvent(event)
        event.accept()
