"""外部审核发生时间的一键填入。

这个字段记录的是外部审核实际发生的时间，不是操作应用的时间，因此输入框默认保持为空：
应用不替用户断言审核何时发生。按钮只是省去手输，每一次点击都是用户的明确选择。
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

_last_occurrence: str | None = None


def last_occurrence() -> str | None:
    """本次程序运行内上一次实际填写的发生时间。"""
    return _last_occurrence


def remember_occurrence(value: str) -> None:
    """批准成功后记住用户填写的值，便于同一次审核在多个动作上保持一致。"""
    global _last_occurrence
    text = value.strip()
    if text:
        _last_occurrence = text


def clear_remembered_occurrence() -> None:
    """清空记住的值；用于需要干净起点的场合。"""
    global _last_occurrence
    _last_occurrence = None


def today_text(now: datetime) -> str:
    """只有日期精度：只知道审核发生在哪一天时使用。"""
    return now.astimezone().date().isoformat()


def now_text(now: datetime) -> str:
    """带时区、到分钟的本机时间：审核刚刚发生时使用。"""
    return now.astimezone().replace(second=0, microsecond=0).isoformat(timespec="minutes")


class OccurrenceQuickFill(QWidget):
    """把「今天」「此刻」「沿用上次」填入目标输入框，填入后仍可自由修改。"""

    def __init__(self, target: QLineEdit, clock, parent=None):
        super().__init__(parent)
        self.target = target
        self.clock = clock
        self.today_button = QPushButton("今天")
        self.now_button = QPushButton("此刻")
        self.reuse_button = QPushButton("沿用上次")
        self.today_button.clicked.connect(self.fill_today)
        self.now_button.clicked.connect(self.fill_now)
        self.reuse_button.clicked.connect(self.fill_previous)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for button in (self.today_button, self.now_button, self.reuse_button):
            layout.addWidget(button)
        layout.addStretch(1)
        self.refresh()

    def refresh(self) -> None:
        previous = last_occurrence()
        self.reuse_button.setEnabled(previous is not None)
        self.reuse_button.setToolTip(
            f"沿用上次填写的 {previous}" if previous else "本次运行还没有填写过发生时间"
        )

    def fill_today(self) -> None:
        self.target.setText(today_text(self.clock.now()))

    def fill_now(self) -> None:
        self.target.setText(now_text(self.clock.now()))

    def fill_previous(self) -> None:
        previous = last_occurrence()
        if previous:
            self.target.setText(previous)
