"""Machine-local presentation preferences, independent of every training root."""

from PySide6.QtCore import QSettings


class UiPreferences:
    def __init__(self, settings=None):
        self.settings = settings if settings is not None else QSettings(
            QSettings.Format.IniFormat, QSettings.Scope.UserScope,
            "TrainingFeedback", "Interface",
        )

    def load(self):
        try:
            percent = int(self.settings.value("scale/percent", 100))
        except (ValueError, TypeError):
            percent = 100
        percent = max(80, min(200, round(percent / 10) * 10))
        return self.settings.value("scale/mode", "system") == "custom", percent

    def save(self, custom, percent):
        self.settings.setValue("scale/mode", "custom" if custom else "system")
        self.settings.setValue("scale/percent", percent)
        self.settings.sync()
