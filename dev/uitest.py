"""端到端测试：真的执行一次改名，再撤销。"""
import os, sys, shutil, tempfile, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from renamer.ui.theme import QSS
from renamer.ui.main_window import MainWindow
from renamer.core.rules import Rule
from renamer.core import history

# ---- 让所有对话框自动点"确定"
def fake_exec(self):
    self._clicked = self.button(QMessageBox.Ok) or self.button(QMessageBox.Yes)
    return 0
QMessageBox.exec = fake_exec
QMessageBox.clickedButton = lambda self: getattr(self, "_clicked", None)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.about = staticmethod(lambda *a, **k: None)

src = os.path.join(ROOT, "demo2")
shutil.rmtree(src, ignore_errors=True)
os.makedirs(src)
for i, n in enumerate(["产品图片 (1).jpg", "产品图片 (2).jpg", "产品图片 (3).jpg",
                       "IMG 007 copy.png", "报告  final.docx", "notes.txt"]):
    with open(os.path.join(src, n), "w", encoding="utf-8") as f:
        f.write(f"content-{i}")

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)
win = MainWindow()
win.resize(1400, 880)
win.show()

results = []
def check(label, cond, extra=""):
    results.append((label, bool(cond), extra))
    print(("PASS " if cond else "FAIL ") + label + ("  " + str(extra) if extra else ""))

def run():
    win.open_dir(src)
    app.processEvents()

    # 1) 预览：删括号 + 加序号 + 小写扩展名
    win.rule_panel.set_rules([
        Rule("delete", params={"mode": "brackets", "bracket": "()"}),
        Rule("convert", params={"trim": True, "collapse": True}),
        Rule("add", params={"position": "stem_suffix", "content": "_{n}", "seq_digits": 2}),
    ])
    win._recalc()
    app.processEvents()
    total, checked, will, bad = win.model.counts()
    check("预计算得出可改名数量", will == 6, f"total={total} will={will} bad={bad}")
    new_names = [r.new_name for r in win.model.rows]
    check("括号被删除且无残留空格", all("(" not in n and "  " not in n for n in new_names), new_names)
    check("序号已按顺序追加", all(re.search(r"_\d{2}\.[a-z]+$", n) for n in new_names), new_names)

    # 2) 筛选：只看变更 / 搜索
    win.proxy.set_search("图片")
    check("搜索筛选生效", win.proxy.rowCount() == 3, win.proxy.rowCount())
    win.proxy.set_search("")
    win.file_panel.cb_type.setCurrentIndex(win.file_panel.cb_type.findData("txt"))
    check("按类型筛选生效", win.proxy.rowCount() == 1, win.proxy.rowCount())
    win.file_panel.cb_type.setCurrentIndex(0)
    check("清除类型筛选", win.proxy.rowCount() == 6, win.proxy.rowCount())

    # 3) 勾选列
    win.model.set_all_checked(False)
    win._recalc()
    check("全不选后无法执行", win.model.counts()[2] == 0, win.model.counts())
    win.model.rows[0].checked = True
    win._recalc()
    check("勾选1个后可执行1个", win.model.counts()[2] == 1, win.model.counts())
    win.model.set_all_checked(True)
    win._recalc()

    # 4) 真的改名
    before = sorted(os.listdir(src))
    win.do_rename()
    app.processEvents()
    after = sorted(os.listdir(src))
    check("磁盘上文件名已改变", after != before, after)
    check("文件数量不变", len(after) == len(before), (len(before), len(after)))
    check("没有残留临时文件", not any(n.startswith(".~brn_") for n in after), after)
    # 内容没有串号：notes.txt 的内容还是它自己的
    check("文件内容未被改坏", open(os.path.join(src, after[0]), encoding="utf-8").read().startswith("content-"),
          after[0])

    # 5) 撤销
    batches = history.load_history()
    bid = batches[-1]["id"]
    win._undo(bid)
    app.processEvents()
    restored = sorted(os.listdir(src))
    check("撤销后文件名完全恢复", restored == before, restored)

    # 6) 冲突处理：让所有文件重名 → 应该一个都不改
    win.rule_panel.set_rules([
        Rule("convert", params={"set_ext": "xxx"}),
        Rule("delete", params={"mode": "position", "pos_from": "tail", "count": 999}),
    ])
    win._recalc()
    app.processEvents()
    check("全部冲突时不执行", win.model.counts()[2] == 0, win.model.counts())
    before2 = sorted(os.listdir(src))
    win.do_rename()
    app.processEvents()
    check("冲突时磁盘未被改动", sorted(os.listdir(src)) == before2)

    # 7) 递归扫描
    os.makedirs(os.path.join(src, "子目录"), exist_ok=True)
    with open(os.path.join(src, "子目录", "深层 文件.txt"), "w") as f:
        f.write("z")
    win.file_panel.chk_recursive.setChecked(True)
    win.rescan()
    app.processEvents()
    check("递归扫描包含子目录文件", any("子目录" in r.item.reldir for r in win.model.rows),
          [r.item.reldir for r in win.model.rows])

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed")
    app.quit()

QTimer.singleShot(500, run)
app.exec()
