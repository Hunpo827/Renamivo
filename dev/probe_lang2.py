import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication
from renamer import i18n, meta
from renamer.app import Controller
from renamer.ui.theme import QSS

app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
QSettings('Renamivo','Renamivo').clear()
i18n.set_language("zh")
app.setApplicationName(meta.app_display_name())
app.setApplicationDisplayName(meta.app_display_name())
ctl = Controller(app); ctl.launch()

def step1():
    ctl.win.set_language("en")

def step2():
    vis = [(w.windowTitle(), w.isVisible()) for w in app.topLevelWidgets() if w.windowTitle()]
    print("可见窗口:", vis)
    print("display:", app.applicationDisplayName(), "| 新窗口标题:", ctl.win.windowTitle())
    app.quit()

QTimer.singleShot(400, step1)
QTimer.singleShot(1400, step2)
app.exec()
