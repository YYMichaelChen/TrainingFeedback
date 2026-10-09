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
    def __init__(self, weights, parent=None, *, compact_columns=()):
        super().__init__(0, len(weights), parent)
        self.weights = weights
        self.compact_columns = frozenset(compact_columns)
        self._updating_metrics = False
        self.height_budget = lambda: u(36)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setStretchLastSection(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalScrollBar().setToolTip("左右拖动可查看其余列。")
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
        if self._updating_metrics:
            return
        self._updating_metrics = True
        try:
            self._update_metrics()
        finally:
            self._updating_metrics = False

    def _update_metrics(self):
        header = self.horizontalHeader()
        minimums = []
        for column, weight in enumerate(self.weights):
            title = self.horizontalHeaderItem(column)
            title_width = (header.fontMetrics().horizontalAdvance(title.text()) + u(1)
                           if title is not None else 0)
            content = max((self.cellWidget(row, column).minimumSizeHint().width()
                           for row in range(self.rowCount())
                           if self.cellWidget(row, column) is not None), default=0)
            # A control can widen its own column, never multiply the whole table.
            minimums.append(max(u(weight), title_width, content + u(.25)))
        header.setMinimumSectionSize(u(1.5))
        width = max(1, self.viewport().width())
        extra = max(0, width - sum(minimums))
        flexible = [column for column in range(len(self.weights))
                    if column not in self.compact_columns]
        remaining_weight = sum(self.weights[column] for column in flexible)
        sizes = list(minimums)
        for column in flexible:
            addition = round(extra * self.weights[column] / remaining_weight)
            sizes[column] += addition
            extra -= addition
            remaining_weight -= self.weights[column]
        for column, size in enumerate(sizes):
            self.setColumnWidth(column, size)
        self.verticalHeader().setMinimumSectionSize(u(2.5))
        self.verticalHeader().setDefaultSectionSize(u(2.5))
        self.resizeRowsToContents()
        height = self.horizontalHeader().sizeHint().height() + sum(
            self.rowHeight(row) for row in range(self.rowCount())
        ) + self.frameWidth() * 2
        if self.rowCount() > 8:
            height = min(height, max(u(5), round(self.height_budget() * .5)))
        if sum(sizes) > width:
            height += self.horizontalScrollBar().sizeHint().height()
        self.setFixedHeight(max(u(2.5), height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_metrics()

    def sizeHint(self):
        return QSize(u(28), self.height())

    def minimumSizeHint(self):
        # Keep column overflow inside the table instead of widening its form.
        return QSize(0, self.height())

    def wheelEvent(self, event):
        super().wheelEvent(event)
        event.accept()
