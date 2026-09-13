"""Shared native widget palette, spacing and semantic emphasis."""

from pathlib import Path

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication


def apply_theme(application: QApplication) -> None:
    application.setStyle("Fusion")
    application.setFont(QFont("Microsoft YaHei UI", 10))
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, "#f3f6fa"),
        (QPalette.ColorRole.WindowText, "#233249"),
        (QPalette.ColorRole.Base, "#ffffff"),
        (QPalette.ColorRole.AlternateBase, "#f4f8fb"),
        (QPalette.ColorRole.Text, "#233249"),
        (QPalette.ColorRole.Button, "#ffffff"),
        (QPalette.ColorRole.ButtonText, "#233249"),
        (QPalette.ColorRole.Highlight, "#d5eee9"),
        (QPalette.ColorRole.HighlightedText, "#115e59"),
        (QPalette.ColorRole.ToolTipBase, "#ffffff"),
        (QPalette.ColorRole.ToolTipText, "#233249"),
    ):
        palette.setColor(role, QColor(color))
    application.setPalette(palette)
    arrow = Path(__file__).with_name("chevron.svg").as_posix()
    application.setStyleSheet(STYLESHEET.replace("CHEVRON_PATH", arrow))


STYLESHEET = """
QWidget { color: #233249; }
QMainWindow, QDialog { background: #f3f6fa; }
QLabel { background: transparent; }
QLabel#pageTitle { font-size: 25px; font-weight: 700; margin: 4px 0 8px 0; }
QLabel#sectionTitle { font-size: 18px; font-weight: 700; }
QLabel#muted { color: #607187; }
QLabel#eyebrow { color: #0c8175; font-weight: 700; }
QLabel#statusBadge { color: #115e59; background: #e0f2ed; padding: 10px; border-radius: 8px; }
QFrame#card, QWidget#card { background: white; border: 1px solid #dce5ef; border-radius: 12px; }
QFrame#hero { background: #e4f2ee; border: 1px solid #cee6de; border-radius: 14px; }
QFrame#sidebar { background: #172b40; border: none; }
QLabel#brand { color: white; font-size: 22px; font-weight: 700; }
QLabel#brandCaption { color: #9eb6c9; font-size: 12px; }
QListWidget#navigation { background: transparent; border: none; color: #c4d3df; padding: 0; }
QListWidget#navigation::item { padding: 14px 12px; margin: 3px 0;
                               border: none; border-radius: 8px; }
QListWidget#navigation::item:selected { background: #245a65; color: #ffffff; }
QListWidget#navigation::item:hover:!selected { background: #223e55; }
QPushButton { background: #ffffff; border: 1px solid #cbd7e4; border-radius: 7px;
              padding: 8px 14px; min-height: 20px; }
QPushButton:hover { background: #eef6f7; border-color: #6fa8a6; }
QPushButton:pressed { background: #d6eae6; }
QPushButton:focus { border: 2px solid #0f877a; }
QPushButton#primaryButton { background: #0f8175; border-color: #0f8175;
                            color: white; font-weight: 700; }
QPushButton#primaryButton:hover { background: #0b6d63; }
QPushButton#dangerButton { color: #ab4247; border-color: #e2c5c7; background: #fff7f7; }
QPushButton#secondaryButton { color: #2469a0; background: #eaf3fc; border-color: #c9dff2; }
QPushButton:disabled { color: #8a98a8; background: #edf1f5; border-color: #e0e6ed; }
QPushButton#primaryButton:disabled, QPushButton#secondaryButton:disabled,
QPushButton#dangerButton:disabled { color: #8a98a8; background: #edf1f5; border-color: #e0e6ed; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {
    background: white; border: 1px solid #cbd7e4; border-radius: 6px;
    padding: 6px; min-height: 20px; selection-background-color: #cbeae3;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #0f8175; }
QComboBox { padding-right: 24px; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: url(CHEVRON_PATH); width: 12px; height: 8px; }
QLineEdit:disabled, QComboBox:disabled { background: #edf1f5; color: #8a98a8; }
QListWidget, QTreeWidget, QTableWidget, QTextBrowser, QPlainTextEdit, QTextEdit {
    background: #ffffff; border: 1px solid #dce5ef; border-radius: 8px;
    selection-background-color: #d5eee9; selection-color: #115e59;
}
QListWidget::item { padding: 11px 12px; border-bottom: 1px solid #eef2f6; }
QListWidget::item:selected { background: #d5eee9; color: #115e59; }
QListWidget::item:hover:!selected { background: #f0f6fb; }
QHeaderView::section { background: #edf3f8; color: #52657a; border: none; padding: 8px; }
QTableWidget { gridline-color: #e5edf4; }
QGroupBox { background: white; border: 1px solid #dce5ef; border-radius: 10px;
            margin-top: 16px; padding: 18px 10px 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; color: #41627a; font-weight: 700; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: #f3f6fa; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #bbcbd7; border-radius: 5px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background: #dfe8ee; border: none; border-radius: 4px; max-height: 8px; }
QProgressBar::chunk { background: #159986; border-radius: 4px; }
QCheckBox { spacing: 7px; }
QTabWidget::pane { border: 1px solid #dce5ef; background: white; }
QTabBar::tab { padding: 10px 16px; background: #e9eff5; border: none; color: #607187; }
QTabBar::tab:selected { background: white; color: #0f8175; border-bottom: 2px solid #0f8175; }
QToolTip { background: white; color: #233249; border: 1px solid #cbd7e4; padding: 6px; }
"""
