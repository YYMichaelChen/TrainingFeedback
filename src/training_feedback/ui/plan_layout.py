"""Plan-dialog pane arrangement; no prescriptions or persistence rules live here."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from .sizing import bind_units, scale_manager, u


class PlanActionTree(QTreeWidget):
    """Request a sibling reorder; the document owns the actual order change."""

    reorder_requested = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDropIndicatorShown(True)

    def dropEvent(self, event):
        source = self.currentItem()
        target = self.itemAt(event.position().toPoint())
        if (event.source() is not self or source is None or target is None
                or source is target or source.parent() is not target.parent()):
            event.ignore()
            return
        before = source.data(0, Qt.ItemDataRole.UserRole)
        after = target.data(0, Qt.ItemDataRole.UserRole)
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        self.reorder_requested.emit(before, after)


class PlanPanes(QWidget):
    def __init__(self, left, center, guidance, tree, parent=None):
        super().__init__(parent)
        self.left, self.center, self.tree = left, center, tree
        self.mode = None
        self.drawer_open = False
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
        if self.tree is None:
            return
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
        self.capsule_row.addStretch()
        height = max((self.capsule_row.itemAt(index).widget().sizeHint().height()
                      for index in range(self.capsule_row.count())
                      if self.capsule_row.itemAt(index).widget() is not None), default=u(2.5))
        scrollbar = self.capsules.horizontalScrollBar().sizeHint().height()
        self.capsules.setFixedHeight(height + scrollbar + self.capsules.frameWidth() * 2)

    def reflow(self):
        width = self.window().width()
        mode = "wide" if width >= u(80) else "medium" if width >= u(56) else "narrow"
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
        self.guidance_button.setVisible(mode != "wide")
        self.close_drawer.setVisible(mode != "wide")
        if mode != "narrow" and self.tree is not None:
            self.left.setFixedWidth(max(u(12), min(u(18), round(self.width() * .18))))
        if mode == "wide":
            self.right.setFixedWidth(max(u(16), min(u(26), round(self.width() * .24))))
            self.right.show()
        else:
            self.right.setVisible(self.drawer_open)
            if self.drawer_open:
                width = min(self.width(), max(u(16), min(u(26), round(self.width() * .8))))
                self.right.setFixedWidth(width)
                self.right.setGeometry(self.width() - width, 0, width, self.height())
                self.right.raise_()

    def toggle_drawer(self):
        self.drawer_open = not self.drawer_open
        self.reflow()

    def hide_drawer(self):
        self.drawer_open = False
        self.reflow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
