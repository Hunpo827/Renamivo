"""新功能回归：拖动排序 / 结果提示 / 语言切换 / 关于 / 更新入口。"""
import os, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from renamer import i18n, meta
from renamer.app import Controller
from renamer.core.rules import Rule
from renamer.ui.theme import QSS
from renamer.ui.dialogs import AboutDialog, github_repo
from renamer.ui.main_window import MainWindow

captured = []
def fake_exec(self):
    captured.append(self.text())
    self._clicked = self.button(QMessageBox.Ok) or self.button(QMessageBox.Yes)
    return 0
QMessageBox.exec = fake_exec
QMessageBox.clickedButton = lambda self: getattr(self, "_clicked", None)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: captured.append(a[2] if len(a) > 2 else ""))
QMessageBox.warning = staticmethod(lambda *a, **k: captured.append(a[2] if len(a) > 2 else ""))
QMessageBox.critical = staticmethod(lambda *a, **k: captured.append(a[2] if len(a) > 2 else ""))
QMessageBox.about = staticmethod(lambda *a, **k: None)

results = []
def check(label, cond, extra=""):
    results.append((label, bool(cond)))
    print(("PASS " if cond else "FAIL ") + label + ("  " + str(extra) if extra else ""))

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)
QSettings('Renamivo', 'Renamivo').clear()

i18n.set_language("zh")
ctl = Controller(app)
ctl.launch()
win = ctl.win
app.processEvents()

src = os.path.join(ROOT, "demo3")
shutil.rmtree(src, ignore_errors=True)
os.makedirs(src)
for n in ("a1.txt", "a2.txt", "a3.txt"):
    open(os.path.join(src, n), "w").write("x")

win.open_dir(src)
app.processEvents()

# ---------- 1. 拖动排序
win.rule_panel.set_rules([Rule("add"), Rule("delete"), Rule("replace")])
app.processEvents()
order0 = [c.rule.type for c in win.rule_panel.cards]
check("初始顺序", order0 == ["add", "delete", "replace"], order0)
win.rule_panel.reorder(win.rule_panel.cards[2], 0)      # replace 拖到最前
order1 = [c.rule.type for c in win.rule_panel.cards]
check("拖到最前", order1 == ["replace", "add", "delete"], order1)
from renamer.ui.rule_widgets import RuleCard
visual = [win.rule_panel.vbox.itemAt(i).widget()
          for i in range(win.rule_panel.vbox.count())]
visual = [w.rule.type for w in visual if isinstance(w, RuleCard)]
check("布局视觉顺序同步", visual == order1, visual)
win.rule_panel.reorder(win.rule_panel.cards[0], 2)      # 再拖到末尾
order2 = [c.rule.type for c in win.rule_panel.cards]
check("拖到末尾", order2 == ["add", "delete", "replace"], order2)
check("原地放下不报错", win.rule_panel.reorder(win.rule_panel.cards[1], 1) is None)
win.rule_panel.reorder(win.rule_panel.cards[0], 99)
check("越界索引被夹到末尾",
      [c.rule.type for c in win.rule_panel.cards][-1] == "add",
      [c.rule.type for c in win.rule_panel.cards])

# ---------- 2. 失败路径 + 结果提示
win.rule_panel.set_rules([Rule("add", params={"position": "prefix", "content": "x_"})])
win._recalc(); app.processEvents()
check("预览已生成", win.model.counts()[2] == 3, win.model.counts())

handles = [open(os.path.join(src, n), "r") for n in ("a1.txt", "a2.txt", "a3.txt")]
captured.clear()
win.do_rename(); app.processEvents()
text = " ".join(captured)
check("失败会提示数量", ("成功" in text and "失败" in text), text[:120])
check("失败后已回滚", sorted(os.listdir(src)) == ["a1.txt", "a2.txt", "a3.txt"],
      sorted(os.listdir(src)))
for h in handles:
    h.close()

# ---------- 3. 成功路径 + 结果提示
captured.clear()
win._recalc(); win.do_rename(); app.processEvents()
text = " ".join(captured)
check("成功会提示数量", ("全部成功" in text) and ("3" in text), text[:120])
check("文件确实改了名", sorted(os.listdir(src)) == ["x_a1.txt", "x_a2.txt", "x_a3.txt"],
      sorted(os.listdir(src)))

# ---------- 4. 语言切换（重建窗口）
i18n.set_language("zh")
check("中文窗口标题", win.windowTitle() == "易名匣", win.windowTitle())
win.rule_panel.set_rules([Rule("convert")])
win.set_language("en")
app.processEvents()
win2 = ctl.win
check("切换后是新窗口", win2 is not win)
check("英文窗口标题", win2.windowTitle() == "Renamivo", win2.windowTitle())
check("规则被带过去", [c.rule.type for c in win2.rule_panel.cards] == ["convert"])
check("语言设置已保存",
      QSettings('Renamivo', 'Renamivo').value("language") == "en")
from PySide6.QtCore import Qt as _Qt
check("表头已英文", win2.model.headerData(1, _Qt.Horizontal) == "Name",
      win2.model.headerData(1, _Qt.Horizontal))

# ---------- 5. 语言回退规则
check("系统语言解析-中文", i18n.resolve_language("zh") == "zh")
check("系统语言解析-英文", i18n.resolve_language("en") == "en")
check("auto 有回退", i18n.resolve_language("auto") in ("zh", "en"))
i18n.set_language("hu")
check("未知语言回退英文", i18n.current_language() == "en")

# ---------- 6. 关于 / 更新入口
i18n.set_language("zh")
dlg = AboutDialog(win2)
check("关于窗口可构建", dlg is not None and dlg.windowTitle() == "关于", dlg.windowTitle())
check("未配置仓库时按钮禁用", not dlg.btn_update.isEnabled() and not dlg.btn_gh.isEnabled())
os.environ["APPDATA"], old = os.environ["APPDATA"], os.environ["APPDATA"]
from renamer.core.config import load_config, save_config, CONFIG_PATH
save_config({"github_repo": "someone/batch-renamer"})
check("config 可覆盖仓库", github_repo() == "someone/batch-renamer", github_repo())
dlg2 = AboutDialog(win2)
check("配好仓库后按钮可用", dlg2.btn_update.isEnabled() and dlg2.btn_gh.isEnabled())
save_config({})
dlg.close(); dlg2.close()

# ---------- 7. 目录树内边距
wrap = win2.dir_panel.view.parentWidget()
m = wrap.layout().contentsMargins()
check("目录树有内边距", m.left() >= 4 and m.top() >= 4, (m.left(), m.top()))


# ---------- 8. 规则组保存 / 载入 / 删除
from PySide6.QtWidgets import QInputDialog
from renamer.core.config import PRESET_DIR, LAST_RULES_PATH, load_json
from pathlib import Path
QInputDialog.getText = staticmethod(lambda *a, **k: ("测试规则组", True))
win2.set_language("zh"); app.processEvents()
win3 = ctl.win
win3.rule_panel.set_rules([Rule("add", params={"content": "x"}), Rule("convert")])
win3.rule_panel._save_group()
gp = PRESET_DIR() / "测试规则组.json"
check("规则组已写入磁盘", gp.exists(), str(gp))
names = [f.stem for f in win3.rule_panel._preset_files()]
check("规则组列表里有它", "测试规则组" in names, names)
win3.rule_panel.clear_rules()
check("清空后没有规则", len(win3.rule_panel.cards) == 0)
win3.rule_panel._load_preset(gp)
check("载入规则组恢复两条规则",
      [c.rule.type for c in win3.rule_panel.cards] == ["add", "convert"],
      [c.rule.type for c in win3.rule_panel.cards])
win3.rule_panel._delete_group(gp)
check("规则组已删除", not gp.exists())

# ---------- 9. 关窗口自动记住规则，下次开恢复
win3.rule_panel.set_rules([Rule("replace")])
win3.close()
saved = load_json(LAST_RULES_PATH(), [])
check("关闭时保存了规则", isinstance(saved, list) and len(saved) == 1, saved)
win4 = MainWindow()
app.processEvents()
check("新窗口自动恢复上次规则",
      [c.rule.type for c in win4.rule_panel.cards] == ["replace"],
      [c.rule.type for c in win4.rule_panel.cards])
win4.close()

# ---------- 10. Qt 自带文案已中文化
from PySide6.QtCore import QCoreApplication
zh_ok = QCoreApplication.translate("QPlatformTheme", "OK")
check("对话框按钮已中文化", zh_ok == "确定", zh_ok)
i18n.set_language("en")
from renamer.app import install_qt_translations
install_qt_translations(app, "en")
en_ok = QCoreApplication.translate("QPlatformTheme", "OK")
check("英文模式下按钮是 OK", en_ok == "OK", en_ok)

bad = [r for r in results if not r[1]]
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
app.quit()
