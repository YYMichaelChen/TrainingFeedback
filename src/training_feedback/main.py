"""应用入口：负责 Qt 启动与数据目录选择，具体组装逻辑在 bootstrap/app 模块。"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from training_feedback.app import DataRootSwitcher, LibraryContext
from training_feedback.bootstrap import choose_data_root, open_from_locator
from training_feedback.data.data_root import DataRootError
from training_feedback.data.locator import Locator, default_locator_path
from training_feedback.ui.data_root_dialog import DataRootDialog, suggested_data_root
from training_feedback.ui.labels import user_message
from training_feedback.ui.main_window import MainWindow
from training_feedback.ui.theme import apply_theme


def main() -> int:
    """Start the native desktop application."""
    application = QApplication(sys.argv)
    apply_theme(application)
    locator = Locator(default_locator_path())

    def report_error(error: DataRootError) -> None:
        QMessageBox.warning(None, "无法打开数据目录", user_message(str(error)))

    context = open_from_locator(locator, report_error)
    if context is None:

        def choose() -> tuple[Path, bool] | None:
            # 首启（或 locator 失效）时给出文档目录下的默认位置建议；切换数据目录不预填。
            dialog = DataRootDialog(suggested_path=suggested_data_root())
            if dialog.exec() != DataRootDialog.DialogCode.Accepted:
                return None
            return dialog.selected_path(), dialog.creates_new_root()

        context = choose_data_root(locator, choose, report_error)
    if context is None:
        return 0
    switcher = DataRootSwitcher(context, locator)

    def build_window(ctx: LibraryContext) -> MainWindow:
        return MainWindow(ctx, request_switch)

    def request_switch(path, create) -> bool:
        return switcher.switch(path, create, build_window)

    switcher.attach(build_window(context))
    switcher.window.show()
    result = application.exec()
    switcher.context.close()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
