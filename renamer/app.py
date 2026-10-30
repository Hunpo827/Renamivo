"""程序入口。"""

from __future__ import annotations

import os
import sys
import traceback

from PySide6.QtCore import QLibraryInfo, QSettings, Qt, QTranslator
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from . import i18n, meta

try:                      # 打包脚本会生成，源码/克隆运行时可缺失
    from . import _buildid
    BUILD_ID = _buildid.BUILD_ID
except Exception:
    BUILD_ID = "dev"
from .core.executor import pending_journal, recover
from .i18n import LANG_AUTO, tr
from .resources import resource
from .ui.main_window import MainWindow
from .ui.theme import QSS

APP_ORG = "Renamivo"
APP_KEY = "Renamivo"

_qt_translator = None


def install_qt_translations(app: QApplication, lang: str) -> None:
    """加载 Qt 自带的中文翻译。

    不加载的话，QMessageBox 的 OK / Yes / No、QInputDialog 的按钮
    全是英文——界面自己翻译了，系统对话框却没有。
    """
    global _qt_translator
    if _qt_translator is not None:
        app.removeTranslator(_qt_translator)
        _qt_translator = None
    if lang != "zh":
        return
    try:
        tdir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        candidate = QTranslator(app)
        if candidate.load("qtbase_zh_CN", tdir) or candidate.load("qt_zh_CN", tdir):
            app.installTranslator(candidate)
            _qt_translator = candidate
    except Exception:
        pass


def _excepthook(exc_type, exc, tb) -> None:
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    try:
        err_path = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                                APP_KEY, "error.log")
        os.makedirs(os.path.dirname(err_path), exist_ok=True)
        with open(err_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass
    box = QMessageBox()
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(tr("出现异常"))
    box.setText(tr("程序遇到了一个意外错误，操作未完成。"))
    box.setDetailedText(text)
    box.exec()


class Controller:
    """窗口需要重建（切语言）时用它接管，保证任何时候都至少有一个窗口。"""

    def __init__(self, app: QApplication):
        self.app = app
        self.win: MainWindow | None = None

    def launch(self, start_dir: str = "") -> None:
        win = MainWindow(start_dir=start_dir)
        win.restart_requested.connect(self.restart)
        self.win = win
        win.show()

    def restart(self) -> None:
        old = self.win
        if old is None:
            return
        install_qt_translations(self.app, i18n.current_language())
        start_dir = old.current_dir
        rules = old.rule_panel.rules()
        new = MainWindow(start_dir=start_dir)
        new.restart_requested.connect(self.restart)
        if rules:
            new.rule_panel.set_rules(rules)
        self.win = new
        new.show()
        old.close()
        old.deleteLater()


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)

    # 语言先定，应用名要用对应语言
    settings = QSettings(APP_ORG, APP_KEY)
    lang_setting = settings.value("language", LANG_AUTO) or LANG_AUTO
    i18n.set_language(i18n.resolve_language(lang_setting))
    if os.environ.get("SELFTEST_LANG"):
        i18n.set_language(os.environ["SELFTEST_LANG"])
    install_qt_translations(app, i18n.current_language())

    display = meta.APP_NAME if i18n.current_language() == "zh" else meta.APP_NAME_EN
    app.setApplicationName(display)
    app.setOrganizationName(APP_ORG)
    app.setApplicationDisplayName(display)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)

    app.setFont(QFont("Microsoft YaHei UI", 9))
    icon_file = resource(os.path.join("assets", "icon.ico"))
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))

    sys.excepthook = _excepthook
    app.setProperty("buildId", BUILD_ID)

    # 上次改名没做完？先把现场恢复/告知用户
    j = pending_journal()
    if j and "--selftest" not in sys.argv:
        n = len(j.get("pairs", []))
        ret = QMessageBox.question(
            None, tr("上次的改名没有完成"),
            tr("检测到 {time} 开始的一次改名（{n} 个文件）没有正常结束。\n\n"
               "是否把它恢复到改名前的状态？", time=j.get("started", ""), n=n),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ret == QMessageBox.Yes:
            ok, msg = recover(j)
            QMessageBox.information(None, tr("恢复结果"), msg)

    controller = Controller(app)
    controller.launch()

    # 打包后自检：--selftest，截图后自动退出
    if "--selftest" in sys.argv:
        from PySide6.QtCore import QTimer
        out = os.environ.get("SELFTEST_OUT", "selftest.png")
        win = controller.win
        win.resize(1400, 880)

        def _grab():
            ok = win.grab().save(out)
            print("selftest", ok, out, len(win.model.rows), "rows")
            app.quit()

        QTimer.singleShot(2500, _grab)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
