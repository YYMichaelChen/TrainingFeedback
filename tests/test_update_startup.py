"""The injected update coordinator must not prevent an isolated main-window startup."""

from training_feedback.app import LibraryContext
from training_feedback.ui.main_window import MainWindow
from training_feedback.ui.release_updates import ReleaseUpdateCoordinator


class NoNetworkUpdateCoordinator(ReleaseUpdateCoordinator):
    def __init__(self):
        super().__init__("0.8.1")
        self.starts = 0

    def start_once(self):
        self.starts += 1
        return False

    def check(self):
        raise AssertionError("The startup scenario must not make a real or manual request.")


def test_update_coordinator_does_not_block_main_window_startup(qt_app, tmp_path):
    context = LibraryContext.create(tmp_path / "data")
    coordinator = NoNetworkUpdateCoordinator()
    window = MainWindow(context, update_coordinator=coordinator)
    try:
        window.show()
        qt_app.processEvents()
        assert window.isVisible()
        assert coordinator.starts == 1
        assert not window.update_notice.isVisible()
    finally:
        window.close()
        context.close()
