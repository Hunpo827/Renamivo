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
OUT = os.path.join(ROOT, "dev")

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)
QSettings('Renamivo', 'Renamivo').clear()

RULES = [
    Rule("delete", params={"mode": "brackets", "bracket": "()"}),
    Rule("convert", params={"scope": "stem", "trim": True, "collapse": True}),
    Rule("add", params={"position": "stem_suffix", "content": "_{n}", "seq_digits": 2}),
]

for lang in ("zh", "en"):
    i18n.set_language(lang)
    win = MainWindow()
    win.resize(1400, 880)
    win.show()
    [app.processEvents() for _ in range(4)]
    win.open_dir(DEMO)
    win.rule_panel.set_rules(RULES)
    win._recalc()
    [app.processEvents() for _ in range(4)]
    w2 = win.grab()
    w2.save(os.path.join(OUT, f"shot_{lang}.png"))
    print(lang, "main", w2.width(), w2.height(), len(win.model.rows))
    win.resize(1100, 640)
    [app.processEvents() for _ in range(4)]
    win.grab().save(os.path.join(OUT, f"shot_{lang}_narrow.png"))
    win.resize(1400, 880)
    [app.processEvents() for _ in range(4)]
    if lang == "en":
        dlg = AboutDialog(win)
        dlg.show()
        [app.processEvents() for _ in range(4)]
        dlg.grab().save(os.path.join(OUT, "shot_about_en.png"))
        i18n.set_language("zh")
        dlg2 = AboutDialog(win)
        dlg2.show(); [app.processEvents() for _ in range(4)]
        dlg2.grab().save(os.path.join(OUT, "shot_about_zh.png"))
        dlg.close(); dlg2.close()
    win.close()
    win.deleteLater()
    [app.processEvents() for _ in range(4)]
print("done")
