"""Install owned Qt Chinese translations independently of the system UI language."""

from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QTranslator


def install_chinese(application):
    translator = QTranslator(application)
    resource = Path(__file__).with_name("qtbase_zh_CN.qm")
    if not resource.is_file():
        resource = (Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
                    / resource.name)
    if not translator.load(str(resource)):
        raise ValueError("程序中文翻译资源缺失，请重新安装当前版本。")
    application.installTranslator(translator)
    application.chinese_translator = translator
