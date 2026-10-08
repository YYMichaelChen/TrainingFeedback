"""Required application icon on the isolated startup construction path."""

from PySide6.QtCore import QSettings

from training_feedback.app import LibraryContext
from training_feedback.data.ui_preferences import UiPreferences
from training_feedback.ui.main_window import MainWindow
from training_feedback.ui.theme import apply_theme
from training_feedback.ui.window_icon import apply_application_icon


def test_required_application_icon_is_loaded_and_assigned_to_main_window(qt_app, tmp_path):
    # Exercise the real startup theme/units with machine preferences redirected.
    settings = QSettings(str(tmp_path / "interface.ini"), QSettings.Format.IniFormat)
    apply_theme(qt_app, preferences=UiPreferences(settings))
    icon = apply_application_icon(qt_app)
    context = LibraryContext.create(tmp_path / "data")
    window = MainWindow(context)
    try:
        assert not icon.isNull()
        assert not qt_app.windowIcon().isNull()
        assert window.windowIcon().cacheKey() == qt_app.windowIcon().cacheKey()
    finally:
        window.close()
        context.close()
