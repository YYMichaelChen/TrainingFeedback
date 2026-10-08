"""Responsive native toolbars and measured cards; no content or persistence rules."""

from PySide6.QtCore import QEvent, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import (
    QLayout,
    QListView,
    QListWidget,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from .sizing import bind_units, scale_manager, u


class _FlowLayout(QLayout):
    def __init__(self, parent):
        super().__init__(parent)
        self.items = []
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self.items.append(item)
        self.invalidate()

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, True)

    def _arrange(self, rect, apply):
        x, y, row_height = rect.x(), rect.y(), 0
        gap = u(.5)
        for item in self.items:
            if item.isEmpty():
                continue
            size = item.sizeHint()
            width = size.width()
            if x > rect.x() and x + width > rect.x() + rect.width():
                x, y, row_height = rect.x(), y + row_height + gap, 0
            if apply:
                item.setGeometry(QRect(x, y, width, size.height()))
            x += width + gap
            row_height = max(row_height, size.height())
        return y + row_height - rect.y()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            if item.isEmpty():
                continue
            size = size.expandedTo(item.minimumSize()).expandedTo(item.sizeHint())
        return size

    def sizeHint(self):
        return self.minimumSize()


class ActionBar(QWidget):
    """Keep full button labels; wrap to a second row when space is insufficient."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.flow = _FlowLayout(self)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self._refresh)

    def addWidget(self, widget):
        self.flow.addWidget(widget)

    def _refresh(self):
        self.flow.invalidate()
        self.updateGeometry()


class FramedItemDelegate(QStyledItemDelegate):
    """Measure and draw inside the same inset rectangle, including wrapped names."""

    def __init__(self, view, *, gallery=False):
        super().__init__(view)
        self.view, self.gallery = view, gallery

    def text_height(self, option, width):
        return option.fontMetrics.boundingRect(
            QRect(0, 0, max(1, width), 100000),
            Qt.TextFlag.TextWordWrap, option.text,
        ).height()

    def sizeHint(self, option, index):
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        width = (self.view.gridSize().width() if self.gallery
                 else self.view.viewport().width())
        height = (self.text_height(option, width - 2 * (u(.2) + u(.75)))
                  + 2 * (u(.2) + u(.5)))
        if self.gallery:
            return self.view.gridSize()
        return QSize(max(1, width), max(u(3), height))

    def paint(self, painter, option, index):
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        rect = option.rect.adjusted(u(.2), u(.2), -u(.2), -u(.2))
        painter.save()
        painter.setClipRect(option.rect)
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#0f8175" if selected or hovered else "#dce5ef"), 1))
        painter.setBrush(QColor("#e8f5f1" if selected else "#f0f7f8" if hovered else "#ffffff"))
        painter.drawRoundedRect(rect, u(.5), u(.5))
        text_rect = rect.adjusted(u(.75), u(.5), -u(.75), -u(.5))
        if self.gallery:
            image_rect = QRect(text_rect.x(), text_rect.y(), text_rect.width(), u(9))
            option.icon.paint(painter, image_rect, Qt.AlignmentFlag.AlignCenter)
            text_rect.setTop(image_rect.bottom() + u(.5))
        painter.setFont(option.font)
        painter.setPen(QColor("#115e59" if selected else "#233249"))
        alignment = (Qt.AlignmentFlag.AlignCenter if self.gallery
                     else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        painter.drawText(text_rect, Qt.TextFlag.TextWordWrap | alignment, option.text)
        if option.state & QStyle.StateFlag.State_HasFocus:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(QColor("#0f8175"), 1, Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), u(.4), u(.4))
        painter.restore()


class CardList(QListWidget):
    def __init__(self, parent=None, *, gallery=False):
        super().__init__(parent)
        self.gallery = gallery
        self.setMinimumSize(0, 0)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setMouseTracking(True)
        self.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setItemDelegate(FramedItemDelegate(self, gallery=gallery))
        style = "QListWidget { background: transparent; border: none; }"
        if gallery:
            # The delegate supplies all card insets; native item padding must not
            # enlarge a cell beyond its grid slot and wrap the last column away.
            style += "QListWidget::item { padding: 0; margin: 0; border: none; }"
            self.setSpacing(0)
            self.setViewMode(QListView.ViewMode.IconMode)
            self.setResizeMode(QListView.ResizeMode.Adjust)
            self.setMovement(QListView.Movement.Static)
            self.setFlow(QListView.Flow.LeftToRight)
            self.setWrapping(True)
            bind_units(self, "setIconSize", 13, 9, kind="size")
        bind_units(self, "setStyleSheet", style, kind="style")
        self.model().dataChanged.connect(self.update_metrics)
        self.model().rowsInserted.connect(self.update_metrics)
        self.model().rowsRemoved.connect(self.update_metrics)
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self.update_metrics)
        self.update_metrics()

    def update_metrics(self, *_):
        if self.gallery:
            # Leave one logical pixel for view-layout rounding; distribute the
            # remaining width across every column rather than capping card width.
            available = max(1, self.viewport().width() - 1)
            columns = max(1, available // max(1, u(17)))
            width = available // columns
            height = u(15)
            text_width = width - 2 * (u(.2) + u(.75))
            insets = 2 * (u(.2) + u(.5)) + u(9) + u(.5)
            for row in range(self.count()):
                option = QStyleOptionViewItem()
                option.font, option.fontMetrics = self.font(), self.fontMetrics()
                option.text = self.item(row).text()
                height = max(height, self.itemDelegate().text_height(option, text_width) + insets)
            self.setGridSize(QSize(width, height))
        self.doItemsLayout()
        self.viewport().update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_metrics()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange and hasattr(self, "gallery"):
            self.update_metrics()


def frame_combo_popup(combo):
    """Use measured independent rows instead of style-dependent popup row heights."""
    view = QListView(combo)
    view.setObjectName("exercisePicker")
    view.setWordWrap(True)
    view.setTextElideMode(Qt.TextElideMode.ElideNone)
    view.setMouseTracking(True)
    view.setUniformItemSizes(False)
    view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
    view.setItemDelegate(FramedItemDelegate(view))
    combo.setView(view)
    combo.setMaxVisibleItems(10)
    manager = scale_manager()
    if manager is not None:
        manager.changed.connect(view.doItemsLayout)
