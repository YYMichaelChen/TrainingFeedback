"""Plan-dialog pane arrangement; no prescriptions or persistence rules live here."""

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QDrag, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QStyleOptionViewItem,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from .compact_widgets import FramedItemDelegate
from .sizing import bind_units, scale_manager, u


class _ActionNameDelegate(FramedItemDelegate):
    def sizeHint(self, option, index):
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        depth = int(self.view.rootIsDecorated())
        parent = index.parent()
        while parent.isValid():
            depth += 1
            parent = parent.parent()
        width = self.view.columnWidth(index.column()) - depth * self.view.indentation()
        height = self.text_height(option, width - 2 * (u(.2) + u(.75)))
        return QSize(max(1, width), max(u(3), height + 2 * (u(.2) + u(.5))))


class PlanActionTree(QTreeWidget):
    """Request a sibling reorder; the document owns the actual order change."""

    reorder_requested = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDropIndicatorShown(False)
        self.setItemDelegate(_ActionNameDelegate(self))
        self.setUniformRowHeights(False)
        self.setMouseTracking(True)
        self.header().sectionResized.connect(self.doItemsLayout)
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self.doItemsLayout)
        self._drag_source = None
        self._drop_line = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.doItemsLayout()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self.doItemsLayout()

    def startDrag(self, supported_actions):
        source = self.currentItem()
        if source is None:
            return
        self._drag_source = source
        drag = QDrag(self)
        drag.setMimeData(self.mimeData([source]))
        drag.setPixmap(self.viewport().grab(self.visualItemRect(source)))
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos())
                        - self.visualItemRect(source).topLeft())
        try:
            # The document handles moves. QAbstractItemView.startDrag would
            # remove the original row again after an accepted MoveAction.
            drag.exec(Qt.DropAction.MoveAction)
        finally:
            self._drag_source = None
            self._drop_line = None
            self.stopAutoScroll()
            self.setState(QAbstractItemView.State.NoState)
            self.viewport().update()

    def _drop_location(self, point):
        source = self._drag_source
        if source is None:
            return None
        parent = source.parent()
        siblings = parent or self.invisibleRootItem()
        target = self.itemAt(point)
        if target is None:
            target = siblings.child(siblings.childCount() - 1)
            if target is None or point.y() < self.visualItemRect(target).bottom():
                return None
        # Hovering a group's children still places a top-level action after that group.
        while target is not None and target.parent() is not parent:
            target = target.parent()
        if target is None:
            return None
        rect = self.visualItemRect(target)
        below = point.y() > rect.center().y()
        slot = siblings.indexOfChild(target) + int(below)
        index = siblings.indexOfChild(source)
        destination = slot - int(index < slot)
        if below:
            last = target
            while last.isExpanded() and last.childCount():
                last = last.child(last.childCount() - 1)
            rect.setBottom(self.visualItemRect(last).bottom())
        y = rect.bottom() if below else rect.top()
        before = source.data(0, Qt.ItemDataRole.UserRole)
        d, i, m = before
        after = (d, destination, None) if m is None else (d, i, destination)
        return before, after, (rect.left(), y, self.viewport().width() - 1)

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        location = self._drop_location(event.position().toPoint())
        self._drop_line = location[2] if event.source() is self and location else None
        if self._drop_line is None:
            event.ignore()
        else:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        self.viewport().update()

    def dragLeaveEvent(self, event):
        self._drop_line = None
        super().dragLeaveEvent(event)
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drop_line is not None:
            left, y, right = self._drop_line
            painter = QPainter(self.viewport())
            painter.setPen(QPen(QColor("#0f8175"), max(2, u(.15))))
            painter.drawLine(left, y, right, y)
            painter.end()

    def dropEvent(self, event):
        location = self._drop_location(event.position().toPoint())
        self._drop_line = None
        self.viewport().update()
        if event.source() is not self or location is None:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        if location[0] != location[1]:
            self.reorder_requested.emit(location[0], location[1])


class PlanPanes(QWidget):
    guidance_visibility_changed = Signal(bool)

    def __init__(self, left, center, guidance, tree, parent=None):
        super().__init__(parent)
        self.left, self.center, self.tree = left, center, tree
        self.mode = None
        self.drawer_open = False
        self.guidance_visible = None
        self._capsules_dirty = True
        self._capsule_buttons = []
        self.setMinimumSize(0, 0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.capsules = QScrollArea()
        self.capsules.setWidgetResizable(True)
        self.capsules.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.capsule_body = QWidget()
        self.capsule_row = QHBoxLayout(self.capsule_body)
        self.capsule_row.setContentsMargins(0, 0, 0, 0)
        self.capsules.setWidget(self.capsule_body)
        layout.addWidget(self.capsules)
        self.row = QHBoxLayout()
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.addWidget(left)
        self.row.addWidget(center, 1)
        self.right = QFrame()
        self.right.setObjectName("card")
        self.right.setMinimumWidth(0)
        right_layout = QVBoxLayout(self.right)
        self.close_drawer = QPushButton("关闭指导")
        self.close_drawer.clicked.connect(self.hide_drawer)
        right_layout.addWidget(self.close_drawer)
        right_layout.addWidget(guidance, 1)
        self.row.addWidget(self.right)
        layout.addLayout(self.row, 1)
        self.guidance_button = QPushButton("☰ 动作指导")
        self.guidance_button.setAccessibleName("打开动作指导抽屉")
        self.guidance_button.clicked.connect(self.toggle_drawer)
        center.layout().insertWidget(0, self.guidance_button, 0, Qt.AlignmentFlag.AlignRight)
        bind_units(layout, "setSpacing", .5)
        bind_units(self.row, "setSpacing", .5)
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self.reflow)
            manager.changed.connect(self.rebuild_capsules)
        self.reflow()

    def rebuild_capsules(self):
        self._capsules_dirty = True
        if self.mode == "narrow":
            self._build_capsules()

    def update_capsule_selection(self):
        for item, button in self._capsule_buttons:
            button.setChecked(item is self.tree.currentItem())
            button.setEnabled(self.tree.isEnabled())

    def _build_capsules(self):
        if self.tree is None:
            return
        self._capsules_dirty = False
        self._capsule_buttons = []
        while self.capsule_row.count():
            item = self.capsule_row.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for index in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(index)
            for item in [root, *[root.child(i) for i in range(root.childCount())]]:
                button = QPushButton(item.text(0))
                button.setObjectName("actionCapsule")
                button.setCheckable(True)
                button.setChecked(item is self.tree.currentItem())
                button.setEnabled(self.tree.isEnabled())
                button.clicked.connect(lambda checked=False, selected=item:
                                       self.tree.setCurrentItem(selected))
                self.capsule_row.addWidget(button)
                self._capsule_buttons.append((item, button))
        self.capsule_row.addStretch()
        height = max((self.capsule_row.itemAt(index).widget().sizeHint().height()
                      for index in range(self.capsule_row.count())
                      if self.capsule_row.itemAt(index).widget() is not None), default=u(2.5))
        scrollbar = self.capsules.horizontalScrollBar().sizeHint().height()
        self.capsules.setFixedHeight(height + scrollbar + self.capsules.frameWidth() * 2)

    def reflow(self):
        width = self.width()
        mode = "wide" if width >= u(96) else "medium" if width >= u(64) else "narrow"
        if mode != self.mode:
            self.drawer_open = False
            self.mode = mode
            if mode == "wide":
                self.row.addWidget(self.right)
            else:
                self.row.removeWidget(self.right)
                self.right.setParent(self)
        self.left.setVisible(mode != "narrow" and self.tree is not None)
        self.capsules.setVisible(mode == "narrow" and self.tree is not None)
        if mode == "narrow" and self._capsules_dirty:
            self._build_capsules()
        self.guidance_button.setVisible(mode != "wide")
        self.close_drawer.setVisible(mode != "wide")
        if mode != "narrow" and self.tree is not None:
            self.left.setFixedWidth(max(u(13), min(u(18), round(self.width() * .17))))
        if mode == "wide":
            self.right.setFixedWidth(max(u(22), min(u(30), round(self.width() * .28))))
            self.right.show()
        else:
            self.right.setVisible(self.drawer_open)
            if self.drawer_open:
                width = min(self.width(), max(u(22), min(u(30), round(self.width() * .8))))
                self.right.setFixedWidth(width)
                self.right.setGeometry(self.width() - width, 0, width, self.height())
                self.right.raise_()
        visible = mode == "wide" or self.drawer_open
        if visible != self.guidance_visible:
            self.guidance_visible = visible
            self.guidance_visibility_changed.emit(visible)

    def toggle_drawer(self):
        self.drawer_open = not self.drawer_open
        self.reflow()

    def hide_drawer(self):
        self.drawer_open = False
        self.reflow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
