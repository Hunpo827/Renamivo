import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from renamer import i18n
from renamer.resources import desktop_dir
from renamer.ui.theme import QSS
from renamer.ui.main_window import MainWindow
app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
QSettings('Renamivo','Renamivo').clear()
i18n.set_language("zh")
win = MainWindow(); win.resize(1400,880); win.show()
import time
end = time.time() + 1.2
while time.time() < end:
    app.processEvents()
    time.sleep(0.02)
print("desktop →", desktop_dir())
print("current_dir →", win.current_dir)
print("列表项数:", len(win.model.rows))
idx = win.dir_panel.view.currentIndex()
print("目录树选中:", win.dir_panel.fs.filePath(idx) if idx.isValid() else "(none)")
print("齿轮图标:", win.btn_help.iconSize().width(), "px; 按钮:", win.btn_help.width(), "x", win.btn_help.height())
win.grab().save(os.path.join(ROOT, "dev", "desktop_start.png"))
