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
display = meta.APP_NAME if i18n.current_language()=="zh" else meta.APP_NAME_EN
app.setApplicationName(display); app.setApplicationDisplayName(display)
print("start zh: display=", app.applicationDisplayName(), "| appName=", app.applicationName())
ctl = Controller(app); ctl.launch(); app.processEvents()
print("  win title:", ctl.win.windowTitle())
ctl.win.set_language("en")
app.processEvents(); app.processEvents()
print("after en: display=", app.applicationDisplayName(), "| appName=", app.applicationName())
print("  win title:", ctl.win.windowTitle())
print("  所有顶层窗口标题:", [w.windowTitle() for w in app.topLevelWidgets() if w.windowTitle()])
