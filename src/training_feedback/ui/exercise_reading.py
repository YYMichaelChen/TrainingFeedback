"""Read-only action reading surfaces; callers own content and image provenance."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

from PySide6.QtCore import QEvent, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QPainter, QPixmap, QTextLayout, QTextOption
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .labels import localize_dialog_buttons, user_message


def show_readonly_text(parent, title: str, text: str) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.resize(720, 560)
    layout = QVBoxLayout(dialog)
    view = QPlainTextEdit()
    view.setReadOnly(True)
    view.setPlainText(text)
    layout.addWidget(view, 1)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    localize_dialog_buttons(buttons)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()


def _text(value) -> str:
    return "未填写" if value is None or value == "" else str(value)


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
    return label


GROUPS = (
    ("怎么做", True, (
        ("starting_position", "起始姿势"), ("steps", "动作步骤"),
        ("breathing", "呼吸"), ("tempo_or_pacing", "节奏或保持"),
    )),
    ("安全提醒", True, (
        ("stop_criteria", "停止条件"), ("cautions", "注意事项"),
        ("common_compensations", "常见代偿"),
    )),
    ("认识动作", False, (
        ("purpose", "训练目的"), ("primary_body_areas", "主要身体部位"),
        ("secondary_body_areas", "次要身体部位"),
        ("intended_sensations", "应有感受"), ("applicability", "适用情况"),
        ("equipment", "所需器械"),
    )),
    ("进阶与退阶", False, (("regressions", "退阶方式"), ("progressions", "进阶方式"))),
)


class GroupedGuidance(QScrollArea):
    """One scroll container with selectable verbatim fields and hanging numbers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumSize(0, 0)
        self._guidance = None
        self.set_guidance(None)

    def set_guidance(self, guidance, *, reset=True):
        if not reset and guidance == self._guidance:
            return
        self._guidance = deepcopy(guidance)
        old = self.takeWidget()
        if old is not None:
            old.deleteLater()
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(14)
        for title, expanded, fields in GROUPS:
            group = QFrame()
            group.setObjectName("safetyGroup" if title == "安全提醒" else "readingGroup")
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(12, 10, 12, 12)
            toggle = QToolButton()
            toggle.setText(title)
            toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            toggle.setCheckable(True)
            toggle.setChecked(expanded)
            toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
            toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            body = QWidget()
            body_layout = QVBoxLayout(body)
            body_layout.setContentsMargins(0, 4, 0, 0)
            body_layout.setSpacing(10)
            for key, name in fields:
                heading = _label(name)
                heading.setObjectName("readingFieldTitle")
                body_layout.addWidget(heading)
                value = (guidance or {}).get(key)
                if isinstance(value, list) and value:
                    rows = QGridLayout()
                    rows.setContentsMargins(0, 0, 0, 0)
                    rows.setColumnStretch(1, 1)
                    for index, item in enumerate(value):
                        if key == "steps" and isinstance(item, dict):
                            number, text = item.get("order", index + 1), item.get("text")
                        else:
                            number = index + 1
                            text = ("\n".join(_text(part) for part in item.values())
                                    if isinstance(item, dict) else item)
                        number_label = QLabel(f"{number}.")
                        number_label.setTextFormat(Qt.TextFormat.PlainText)
                        rows.addWidget(number_label, index, 0, Qt.AlignmentFlag.AlignTop)
                        rows.addWidget(_label(_text(text)), index, 1)
                    body_layout.addLayout(rows)
                else:
                    body_layout.addWidget(_label("未填写" if value == [] else _text(value)))
            body.setVisible(expanded)
            toggle.toggled.connect(body.setVisible)
            toggle.toggled.connect(
                lambda checked, button=toggle: button.setArrowType(
                    Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow))
            group_layout.addWidget(toggle)
            group_layout.addWidget(body)
            layout.addWidget(group)
        layout.addStretch(1)
        self.setWidget(panel)
        self.verticalScrollBar().setValue(0)


class _ZoomView(QGraphicsView):
    def __init__(self, source: QPixmap, parent=None):
        super().__init__(parent)
        self._fit = True
        scene = QGraphicsScene(self)
        self.item = QGraphicsPixmapItem(source)
        self.item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        scene.addItem(self.item)
        scene.setSceneRect(self.item.boundingRect())
        self.setScene(scene)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.GlobalColor.white)
        self.scale_label = None

    def _show_scale(self):
        if self.scale_label is not None:
            self.scale_label.setText(f"{self.transform().m11() * 100:.1f}%")

    def fit(self):
        self._fit = True
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.resetTransform()
        self.fitInView(self.item.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 4.0:
            factor = 4.0 / self.transform().m11()
            self.scale(factor, factor)
        self._show_scale()

    def zoom(self, scale: float):
        self._fit = False
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scale = min(4.0, max(0.1, scale))
        current = self.transform().m11()
        self.scale(scale / current, scale / current)
        self._show_scale()

    def wheelEvent(self, event):
        if event.angleDelta().y():
            self.zoom(self.transform().m11() * (1.2 ** (event.angleDelta().y() / 120)))
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit:
            self.fit()

    def event(self, event):
        result = super().event(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.viewport().update()
        return result


class ImageViewer(QDialog):
    def __init__(self, source: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("动作示意图 · 放大查看")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.resize(1000, 760)
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.view = _ZoomView(source)
        for title, callback in (
            ("适应窗口", self.view.fit), ("实际大小", lambda: self.view.zoom(1.0)),
            ("−", lambda: self.view.zoom(self.view.transform().m11() / 1.2)),
            ("+", lambda: self.view.zoom(self.view.transform().m11() * 1.2)),
        ):
            button = QPushButton(title)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        self.view.scale_label = QLabel()
        toolbar.addWidget(self.view.scale_label)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("滚轮缩放 · 拖动查看 · Esc 关闭"))
        layout.addLayout(toolbar)
        layout.addWidget(self.view, 1)
        QTimer.singleShot(0, self.view.fit)


class _FittedImage(QWidget):
    """The source never contributes its dimensions to the enclosing layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source = QPixmap()
        self.message = "暂无图片"
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def set_source(self, source: QPixmap, message=""):
        self.source, self.message = source, message
        self.setCursor(Qt.CursorShape.PointingHandCursor if not source.isNull()
                       else Qt.CursorShape.ArrowCursor)
        self.setToolTip("单击放大查看" if not source.isNull() else message)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        area = QRectF(self.contentsRect()).adjusted(8, 8, -8, -8)
        if area.width() <= 0 or area.height() <= 0:
            return
        if self.source.isNull():
            painter.setPen(Qt.GlobalColor.darkGray)
            painter.drawText(area, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                             self.message)
            return
        source_size = self.source.deviceIndependentSize()
        ratio = min(area.width() / source_size.width(), area.height() / source_size.height())
        target = QRectF(0, 0, source_size.width() * ratio, source_size.height() * ratio)
        target.moveCenter(area.center())
        painter.drawPixmap(target, self.source, QRectF(self.source.rect()))

    def event(self, event):
        result = super().event(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.update()
        return result

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.source.isNull():
            ImageViewer(self.source, self).exec()
        else:
            super().mousePressEvent(event)


class _Caption(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.preview = _label("")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.preview)
        self.full = QToolButton()
        self.full.setText("查看完整说明…")
        policy = self.full.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.full.setSizePolicy(policy)
        self.full.clicked.connect(lambda: show_readonly_text(self, "图片说明", self.text))
        layout.addWidget(self.full, 0, Qt.AlignmentFlag.AlignLeft)

    def set_text(self, text: str):
        self.text = text
        self.preview.setText(text or "未填写图片说明")
        self._measure()

    def _measure(self):
        self.preview.setFixedHeight(self.preview.fontMetrics().lineSpacing() * 2 + 4)
        line_count = 0
        for paragraph in self.text.split("\n"):
            text_layout = QTextLayout(paragraph, self.preview.font())
            option = QTextOption()
            option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
            text_layout.setTextOption(option)
            text_layout.beginLayout()
            while True:
                line = text_layout.createLine()
                if not line.isValid():
                    break
                line.setLineWidth(max(1, self.preview.width()))
                line_count += 1
            text_layout.endLayout()
            if not paragraph:
                line_count += 1
        self.full.setVisible(line_count > 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._measure()


class IllustrationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.declarations = []
        self.loader = None
        self.index = 0
        self.setMinimumSize(0, 0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.image = _FittedImage()
        layout.addWidget(self.image, 1)
        self.caption = _Caption()
        layout.addWidget(self.caption)
        self.navigation = QWidget()
        controls = QHBoxLayout(self.navigation)
        controls.setContentsMargins(0, 0, 0, 0)
        self.previous = QPushButton("‹ 上一张")
        self.next = QPushButton("下一张 ›")
        self.page = QLabel()
        self.previous.clicked.connect(lambda: self._show(self.index - 1))
        self.next.clicked.connect(lambda: self._show(self.index + 1))
        controls.addWidget(self.previous)
        controls.addStretch()
        controls.addWidget(self.page)
        controls.addStretch()
        controls.addWidget(self.next)
        layout.addWidget(self.navigation)

    def set_images(self, declarations: list, loader: Callable[[int], bytes], *, reset=True):
        self.declarations = deepcopy(declarations)
        self.loader = loader
        self.navigation.setVisible(len(declarations) > 1)
        self._show(0 if reset else min(self.index, max(0, len(declarations) - 1)))

    def _show(self, index):
        if not self.declarations:
            self.image.set_source(QPixmap(), "未说明图片状态；动作指导仍可阅读。")
            self.caption.set_text("")
            return
        self.index = max(0, min(index, len(self.declarations) - 1))
        declaration = self.declarations[self.index]
        self.caption.set_text(str(declaration.get("caption") or ""))
        source = QPixmap()
        message = ""
        try:
            if not source.loadFromData(self.loader(self.index)):
                raise ValueError("图片文件损坏或格式无法读取。")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            source = QPixmap()
            message = f"图片不可用：{user_message(str(exc))}\n动作指导仍可阅读。"
        self.image.set_source(source, message)
        self.page.setText(f"{self.index + 1} / {len(self.declarations)}")
        self.previous.setEnabled(self.index > 0)
        self.next.setEnabled(self.index + 1 < len(self.declarations))


class ExerciseReading(QWidget):
    """Move the same widgets between layouts, preserving reading position/state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("exerciseReading")
        self.setStyleSheet(
            "QWidget#exerciseReading { background: white; border: 1px solid #dce5ef; }"
            "QScrollArea > QWidget > QWidget { background: white; }"
            "QFrame#readingGroup { background: #ffffff; border: 1px solid #dce5ef;"
            " border-radius: 8px; }"
            "QFrame#safetyGroup { background: #eef7f5; border: 1px solid #c5dfd9;"
            " border-radius: 8px; }"
            "QLabel#readingFieldTitle { color: #233249; font-weight: 600; }"
            "QToolButton { color: #115e59; padding: 5px; text-align: left; }"
        )
        self.setMinimumSize(0, 0)
        self._identity = None
        self._wide = None
        self._sizes = None
        self.stack = QStackedWidget()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.tabs = QTabWidget()
        self.stack.addWidget(self.splitter)
        self.stack.addWidget(self.tabs)
        self.guidance = GroupedGuidance()
        self.images = IllustrationPanel()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self._set_mode(False)

    def sizeHint(self):
        return QSize(800, 440)

    def set_content(self, identity, guidance: dict | None, loader: Callable[[int], bytes]):
        reset = identity != self._identity
        self._identity = deepcopy(identity)
        self.guidance.set_guidance(guidance, reset=reset)
        self.images.set_images((guidance or {}).get("images", []), loader, reset=reset)

    def _set_mode(self, wide):
        if wide == self._wide:
            return
        position = self.guidance.verticalScrollBar().value()
        if self._wide:
            self._sizes = self.splitter.sizes()
        self._wide = wide
        if wide:
            self.tabs.removeTab(self.tabs.indexOf(self.guidance))
            self.tabs.removeTab(self.tabs.indexOf(self.images))
            self.images.setMinimumWidth(300)
            self.guidance.setMinimumWidth(400)
            self.splitter.addWidget(self.images)
            self.splitter.addWidget(self.guidance)
            # A removed tab can retain its hidden flag when reparented.
            self.images.show()
            self.guidance.show()
            self.stack.setCurrentWidget(self.splitter)
            self.splitter.setSizes(self._sizes or [450, 550])
        else:
            self.images.setMinimumWidth(0)
            self.guidance.setMinimumWidth(0)
            self.tabs.addTab(self.guidance, "动作指导")
            self.tabs.addTab(self.images, "示意图")
            self.tabs.setCurrentIndex(0)
            self.stack.setCurrentWidget(self.tabs)
        self.guidance.verticalScrollBar().setValue(position)
        # Layout application can adjust the scroll range after reparenting.
        identity = deepcopy(self._identity)
        QTimer.singleShot(0, lambda: self.guidance.verticalScrollBar().setValue(position)
                          if self._identity == identity else None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._set_mode(self.contentsRect().width() >= 760)
