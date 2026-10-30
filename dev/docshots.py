"""生成 README 用的界面截图（中英文各一套）。"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from renamer import i18n
from renamer.ui.theme import QSS
from renamer.ui.main_window import MainWindow
from renamer.ui.dialogs import AboutDialog
from renamer.core.rules import Rule

DEMO = os.path.join(ROOT, "demo")
OUT = os.path.join(ROOT, "docs", "images")
os.makedirs(OUT, exist_ok=True)

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)

# demo 里放一组能看出效果的规则
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
    [app.processEvents() for _ in range(3)]
    win.open_dir(DEMO)
    win.rule_panel.set_rules(RULES)
    win._recalc()
    [app.processEvents() for _ in range(4)]
    win.grab().save(os.path.join(OUT, f"main-{lang}.png"))
    print(lang, "main", win.model.counts())

    dlg = AboutDialog(win)
    dlg.show()
    [app.processEvents() for _ in range(3)]
    dlg.grab().save(os.path.join(OUT, f"about-{lang}.png"))
    dlg.close()
    win.close()
    win.deleteLater()
    app.processEvents()

print(sorted(os.listdir(OUT)))
