import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from renamer.ui.theme import QSS
from renamer.ui.main_window import MainWindow
from renamer.core.rules import Rule

DEMO = os.path.join(ROOT, "demo")
OUT = os.path.join(ROOT, "dev", "shot.png")

app = QApplication(sys.argv)
from PySide6.QtCore import QSettings
QSettings('Renamivo', 'Renamivo').clear()
app.setStyle("Fusion")
app.setStyleSheet(QSS)
win = MainWindow()
win.resize(1400, 880)
win.show()

rules = [
    Rule("delete", params={"mode": "brackets", "bracket": "()"}),
    Rule("convert", params={"scope": "stem", "trim": True, "collapse": True}),
    Rule("add", params={"position": "stem_suffix", "content": "_{n}", "seq_digits": 2}),
]

def step1():
    win.open_dir(DEMO)
    win.rule_panel.set_rules(rules)

def step2():
    ok = win.grab().save(OUT)
    print("saved", ok, OUT, os.path.getsize(OUT) if os.path.exists(OUT) else 0)
    # 打印一些内部状态便于排查
    print("rows", len(win.model.rows), "proxy", win.proxy.rowCount(),
          "dir", win.current_dir)
    if win.model.rows:
        for r in win.model.rows[:5]:
            print("  ", r.item.name, "->", r.new_name, r.effective_status, r.msg)
    app.quit()

QTimer.singleShot(600, step1)
QTimer.singleShot(2000, step2)
app.exec()
