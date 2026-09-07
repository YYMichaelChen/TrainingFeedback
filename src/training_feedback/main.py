"""应用入口：负责 Qt 启动与数据目录选择，具体组装逻辑在 bootstrap/app 模块。"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from training_feedback.bootstrap import choose_data_root, open_from_locator
from training_feedback.data.locator import Locator, default_locator_path
from training_feedback.ui.data_root_dialog import DataRootDialog
from training_feedback.ui.main_window import MainWindow


def main() -> int:
    """Start the native desktop application."""
    application = QApplication(sys.argv)
    locator = Locator(default_locator_path())
    context = open_from_locator(locator)
    if context is None:

        def choose() -> tuple[Path, bool] | None:
            dialog = DataRootDialog()
            if dialog.exec() != DataRootDialog.DialogCode.Accepted:
                return None
            return dialog.selected_path(), dialog.creates_new_root()

        context = choose_data_root(locator, choose)
    if context is None:
        return 0
    window = MainWindow(context)
    window.show()
    result = application.exec()
    context.close()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
