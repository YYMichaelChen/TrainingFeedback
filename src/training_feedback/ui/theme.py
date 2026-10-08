"""Shared native widget palette, spacing and semantic emphasis."""

from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .sizing import InterfaceScale, UnitStyle, bind_units


def apply_theme(application: QApplication, *, preferences=None) -> None:
    application.setStyle(UnitStyle())
    if not hasattr(application, "interface_scale"):
        application.interface_scale = InterfaceScale(application, preferences)
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
    bind_units(application, "setStyleSheet", STYLESHEET.replace("CHEVRON_PATH", arrow),
               kind="style")


STYLESHEET = """
QWidget { color: #233249; }
QMainWindow, QDialog { background: #f3f6fa; }
QLabel { background: transparent; }
QLabel#pageTitle { font-size: 1.4u; font-weight: 700; margin: 0.125u 0 0.375u 0; }
QLabel#actionTitle { font-size: 1.25u; font-weight: 700; }
QLabel#dialogTitle { font-size: 1.4u; font-weight: 700; }
QToolButton { min-height: 2.5u; min-width: 2.5u; }
QCheckBox::indicator, QRadioButton::indicator { width: 1.25u; height: 1.25u; }
QTreeWidget#planActions::item { min-height: 2.5u; padding: 0.25u 0.5u; }
QTreeWidget#planActions::item:selected { background: #ecf5f4; border-left: 0.2u solid #0f8175; }
QPushButton#actionCapsule { border-radius: 1.25u; min-width: 0; }
QPushButton#actionCapsule:checked { background: #ecf5f4; border-color: #0f8175; }
QPushButton#tableActionButton { min-width: 0; padding: 0.5u; }
QLabel#sectionTitle { font-size: 1.125u; font-weight: 700; }
QLabel#muted { color: #607187; }
QLabel#eyebrow { color: #0c8175; font-weight: 700; }
QLabel#statusBadge { color: #115e59; background: #e0f2ed; padding: 0.625u; border-radius: 0.5u; }
QFrame#card, QWidget#card { background: white; border: 1px solid #dce5ef; border-radius: 0.75u; }
QFrame#hero { background: #e4f2ee; border: 1px solid #cee6de; border-radius: 0.875u; }
QFrame#sidebar { background: #172b40; border: none; }
QLabel#brand { color: white; font-size: 1.25u; font-weight: 700; }
QLabel#brandCaption { color: #9eb6c9; font-size: 0.75u; }
QToolButton#updateNotice { color: #ffd166; background: transparent; border: 0.125u solid #ffd166;
                           border-radius: 0.75u; font-size: 1u; font-weight: 700; padding: 0; }
QToolButton#updateNotice:hover { color: white; border-color: white; background: #245a65; }
QListWidget#navigation { background: transparent; border: none; color: #c4d3df; padding: 0; }
QListWidget#navigation::item { padding: 0.75u 0.625u; margin: 0.1875u 0;
                               border: none; border-radius: 0.5u; }
QListWidget#navigation::item:selected { background: #245a65; color: #ffffff; }
QListWidget#navigation::item:hover:!selected { background: #223e55; }
QPushButton { background: #ffffff; border: 1px solid #cbd7e4; border-radius: 0.375u;
              padding: 0.375u 0.875u; min-height: 1.5u; min-width: 3u; }
QPushButton:hover { background: #eef6f7; border-color: #6fa8a6; }
QPushButton:pressed { background: #d6eae6; }
QPushButton:focus { border: 0.125u solid #0f877a; }
QPushButton#primaryButton { background: #0f8175; border-color: #0f8175;
                            color: white; font-weight: 700; }
QPushButton#primaryButton:hover { background: #0b6d63; }
QPushButton#dangerButton { color: #ab4247; border-color: #e2c5c7; background: #fff7f7; }
QPushButton#secondaryButton { color: #2469a0; background: #eaf3fc; border-color: #c9dff2; }
QPushButton:disabled { color: #8a98a8; background: #edf1f5; border-color: #e0e6ed; }
QPushButton#primaryButton:disabled, QPushButton#secondaryButton:disabled,
QPushButton#dangerButton:disabled { color: #8a98a8; background: #edf1f5; border-color: #e0e6ed; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {
    background: white; border: 1px solid #cbd7e4; border-radius: 0.375u;
    padding: 0.375u; min-height: 1.5u; selection-background-color: #cbeae3;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #0f8175; }
QComboBox { padding-right: 1.5u; }
QComboBox::drop-down { border: none; width: 1.375u; }
QComboBox::down-arrow { image: url(CHEVRON_PATH); width: 0.75u; height: 0.5u; }
QLineEdit:disabled, QComboBox:disabled { background: #edf1f5; color: #8a98a8; }
QListWidget, QTreeWidget, QTableWidget, QTextBrowser, QPlainTextEdit, QTextEdit {
    background: #ffffff; border: 1px solid #dce5ef; border-radius: 0.5u;
    selection-background-color: #d5eee9; selection-color: #115e59;
}
QListWidget::item { padding: 0.6875u 0.75u; border-bottom: 1px solid #eef2f6; }
QListWidget::item:selected { background: #d5eee9; color: #115e59; }
QListWidget::item:hover:!selected { background: #f0f6fb; }
QHeaderView::section { background: #edf3f8; color: #52657a; border: none; padding: 0.5u; }
QTableWidget { gridline-color: #e5edf4; }
QGroupBox { background: white; border: 1px solid #dce5ef; border-radius: 0.625u;
            margin-top: 1u; padding: 1.125u 0.625u 0.625u; }
QGroupBox::title { subcontrol-origin: margin; left: 0.875u; color: #41627a; font-weight: 700; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: #f3f6fa; }
QScrollBar:vertical { background: transparent; width: 0.625u; margin: 0; }
QScrollBar::handle:vertical { background: #bbcbd7; border-radius: 0.3125u; min-height: 1.75u; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background: #dfe8ee; border: none; border-radius: 0.25u; max-height: 0.5u; }
QProgressBar::chunk { background: #159986; border-radius: 0.25u; }
QProgressBar#updateDownloadProgress { min-height: 1.375u; max-height: 1.375u; }
QCheckBox { spacing: 0.4375u; }
QTabWidget::pane { border: 1px solid #dce5ef; background: white; }
QTabBar::tab { padding: 0.5u 0.75u; background: #e9eff5; border: none; color: #607187; }
QTabBar::tab:selected { background: white; color: #0f8175; border-bottom: 0.125u solid #0f8175; }
QToolTip { background: white; color: #233249; border: 1px solid #cbd7e4; padding: 0.375u; }
"""
