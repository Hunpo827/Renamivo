"""生成 README 用的界面截图（中英文各一套）。"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from renamer import i18n
from renamer.core.rules import Rule
from renamer.ui.main_window import MainWindow
from renamer.ui.theme import QSS

DEMO = os.path.join(ROOT, "demo")
OUT = os.path.join(ROOT, "docs", "images")
os.makedirs(OUT, exist_ok=True)

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)


def pump(seconds: float) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


RULES = [
    Rule("delete", params={"mode": "brackets", "bracket": "()"}),
    Rule("convert", params={"scope": "stem", "trim": True, "collapse": True}),
    Rule("add", params={"position": "stem_suffix", "content": "_{n}", "seq_digits": 2}),
]

for lang in ("zh", "en"):
    i18n.set_language(lang)
    QSettings("Renamivo", "Renamivo").clear()
    win = MainWindow()
    win.resize(1400, 880)
    win.show()
    pump(0.3)

    # 目录树也定位到 demo，别把桌面上的私人文件夹截进去
    win.dir_panel.select_path(DEMO)
    win.open_dir(DEMO)
    win.rule_panel.set_rules(RULES)
    win._recalc()
    pump(1.2)

    path = os.path.join(OUT, f"main-{lang}.png")
    win.grab().save(path)
    idx = win.dir_panel.view.currentIndex()
    print(lang, "->", path, "| tree:", win.dir_panel.fs.filePath(idx),
          "| rows:", len(win.model.rows))
    win.close()
    win.deleteLater()
    pump(0.2)

print(sorted(os.listdir(OUT)))
