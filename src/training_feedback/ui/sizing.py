"""One font-relative logical unit; Qt handles physical device pixel scaling."""

from __future__ import annotations

import re
from weakref import ref

from PySide6.QtCore import QEvent, QObject, QSize, Qt, Signal
from PySide6.QtGui import QFont, QFontInfo
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle

from ..data.ui_preferences import UiPreferences


class InterfaceScale(QObject):
    changed = Signal()

    def __init__(self, application, preferences=None):
        super().__init__(application)
        self.application = application
        self.preferences = preferences if preferences is not None else UiPreferences()
        self.base_font = QFont(application.font())
        # A readable 1rem default (12 points at Qt's normal logical DPI).
        self.base_font.setPointSizeF(max(12.0, self.base_font.pointSizeF()))
        self.custom, self.percent = self.preferences.load()
        self._apply()
        application.installEventFilter(self)

    @property
    def unit(self):
        return QFontInfo(self.application.font()).pixelSize()

    def set_scale(self, custom, percent):
        self.custom = bool(custom)
        self.percent = max(80, min(200, round(percent / 10) * 10))
        self.preferences.save(self.custom, self.percent)
        self._apply()
        self.changed.emit()

    def _apply(self):
        font = QFont(self.base_font)
        font.setPointSizeF(font.pointSizeF() * (self.percent / 100 if self.custom else 1))
        self.application.setFont(font)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress and event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier
        ):
            key = event.key()
            if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_Minus, Qt.Key.Key_0):
                current = self.percent if self.custom else 100
                if key == Qt.Key.Key_0:
                    self.set_scale(False, 100)
                else:
                    self.set_scale(True, current + (-10 if key == Qt.Key.Key_Minus else 10))
                event.accept()
                return True
        return super().eventFilter(watched, event)


def scale_manager():
    application = QApplication.instance()
    return getattr(application, "interface_scale", None)


class UnitStyle(QProxyStyle):
    """Native default layout metrics also derive from the same unit."""

    def __init__(self):
        super().__init__("Fusion")

    def pixelMetric(self, metric, option=None, widget=None):
        dimensions = {
            QStyle.PixelMetric.PM_LayoutLeftMargin: .75,
            QStyle.PixelMetric.PM_LayoutTopMargin: .75,
            QStyle.PixelMetric.PM_LayoutRightMargin: .75,
            QStyle.PixelMetric.PM_LayoutBottomMargin: .75,
            QStyle.PixelMetric.PM_LayoutHorizontalSpacing: .5,
            QStyle.PixelMetric.PM_LayoutVerticalSpacing: .5,
            QStyle.PixelMetric.PM_SmallIconSize: 1.25,
            QStyle.PixelMetric.PM_ButtonIconSize: 1.25,
            QStyle.PixelMetric.PM_ToolBarIconSize: 1.25,
            QStyle.PixelMetric.PM_ScrollBarExtent: .75,
            QStyle.PixelMetric.PM_IndicatorWidth: 1.25,
            QStyle.PixelMetric.PM_IndicatorHeight: 1.25,
            QStyle.PixelMetric.PM_ExclusiveIndicatorWidth: 1.25,
            QStyle.PixelMetric.PM_ExclusiveIndicatorHeight: 1.25,
        }
        if metric in dimensions:
            return u(dimensions[metric])
        return super().pixelMetric(metric, option, widget)


def u(multiplier=1):
    """Round only at the Qt API boundary, in logical pixels (never multiply DPR)."""
    application = QApplication.instance()
    unit = QFontInfo(application.font()).pixelSize() if application is not None else 16
    return round(unit * multiplier)


def unit_stylesheet(template):
    """QSS lacks rem: compile owned `u` tokens into Qt logical dimensions."""
    return re.sub(r"(\d+(?:\.\d+)?)u\b", lambda match: f"{u(float(match[1]))}px", template)


class _UnitBinding(QObject):
    def __init__(self, target, method, values, kind):
        super().__init__(target)
        self.target = ref(target)
        self.method, self.values, self.kind = method, values, kind
        manager = scale_manager()
        if manager is not None:
            manager.changed.connect(self.apply)
        self.apply()

    def apply(self):
        target = self.target()
        if target is None:
            return
        if self.kind == "style":
            getattr(target, self.method)(unit_stylesheet(self.values[0]))
        else:
            values = [u(value) for value in self.values]
            if self.kind == "size":
                getattr(target, self.method)(QSize(*values))
            else:
                getattr(target, self.method)(*values)


def bind_units(target, method, *values, kind=None):
    """Keep a declarative dimension live when the user changes interface scale."""
    bindings = getattr(target, "_unit_bindings", None)
    if bindings is None:
        target._unit_bindings = bindings = {}
    previous = bindings.pop(method, None)
    if previous is not None:
        manager = scale_manager()
        if manager is not None:
            manager.changed.disconnect(previous.apply)
        previous.deleteLater()
    bindings[method] = _UnitBinding(target, method, values, kind)


def fit_dialog(dialog, *, width=.85, height=.88, square=False):
    screen = dialog.screen() or QApplication.primaryScreen()
    if screen is None:
        return
    area = screen.availableGeometry()
    if square:
        side = round(min(area.width() * width, area.height() * height))
        dialog.resize(side, side)
        return
    # The available screen wins over the requested lower clamp on small displays.
    dialog.resize(min(max(round(area.width() * width), u(60)), u(110),
                      round(area.width() * .96)),
                  min(max(round(area.height() * height), u(36)), u(70),
                      round(area.height() * .96)))


def initial_size(widget, width, height):
    screen = widget.screen() or QApplication.primaryScreen()
    area = screen.availableGeometry() if screen is not None else None
    widget.resize(min(u(width), round(area.width() * .9)) if area is not None else u(width),
                  min(u(height), round(area.height() * .9)) if area is not None else u(height))
