"""规则卡片与规则面板（支持拖动排序、中英双语）。"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
                               QFrame, QGridLayout, QHBoxLayout, QInputDialog,
                               QLabel, QLineEdit, QMenu, QMessageBox, QPushButton,
                               QScrollArea, QSizePolicy, QSpinBox,
                               QStackedWidget, QToolButton, QVBoxLayout,
                               QWidget)

from ..core import naming as N
from ..core.config import PRESET_DIR
from ..core.rules import (CASE_LABELS, POSITION_LABELS, RULE_LABELS, SCOPE_LABELS,
                          WIDTH_LABELS, Rule)
from ..i18n import tr
from .icons import icon

MIME_RULE = "application/x-batch-renamer-rule"

TYPE_COLORS = {
    "add": "#0b57d0",
    "delete": "#cf222e",
    "replace": "#8250df",
    "convert": "#1a7f37",
}


class RuleCard(QFrame):
    changed = Signal()
    move_up = Signal(object)
    move_down = Signal(object)
    deleted = Signal(object)
    drag_requested = Signal(object)

    HEADER_H = 30

    def __init__(self, rule: Rule, parent=None):
        super().__init__(parent)
        self.rule = rule
        self._press: QPoint | None = None
        self.setObjectName("ruleCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self._build()

    # ---------------------------------------------------------- 骨架
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 6, 8, 8)
        outer.setSpacing(4)

        head = QHBoxLayout()
        head.setSpacing(6)
        head.setContentsMargins(0, 0, 0, 0)

        self.chk = QCheckBox()
        self.chk.setChecked(self.rule.enabled)
        self.chk.setToolTip(tr("启用 / 停用这条规则"))
        self.chk.stateChanged.connect(self._on_enabled)
        head.addWidget(self.chk)

        badge = QLabel(tr(RULE_LABELS.get(self.rule.type, self.rule.type)))
        badge.setStyleSheet(
            f"background:{TYPE_COLORS.get(self.rule.type, '#666')};color:white;"
            "border-radius:3px;padding:0px 7px;font-size:11px;")
        badge.setFixedHeight(17)
        head.addWidget(badge)

        self.desc = QLabel()
        self.desc.setObjectName("ruleDesc")
        head.addWidget(self.desc, 1)

        for ic, tip, sig in (("up", tr("上移"), self.move_up),
                             ("down", tr("下移"), self.move_down),
                             ("cross", tr("删除此规则"), self.deleted)):
            b = QToolButton()
            b.setIcon(icon(ic))
            b.setIconSize(QSize(14, 14))
            b.setToolTip(tip)
            b.setObjectName("cardBtn")
            b.setFixedSize(22, 22)
            b.clicked.connect(lambda _=False, s=sig: s.emit(self))
            head.addWidget(b)

        outer.addLayout(head)

        body = QWidget()
        outer.addWidget(body)
        self.grid = QGridLayout(body)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(5)

        builder = getattr(self, f"_build_{self.rule.type}", None)
        if builder:
            builder()
        self._refresh()

    # ---------------------------------------------------------- 拖动排序
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() <= self.HEADER_H:
            self._press = event.position().toPoint()
        else:
            self._press = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press is None or not (event.buttons() & Qt.LeftButton):
            return
        moved = event.position().toPoint() - self._press
        if moved.manhattanLength() < QApplication.startDragDistance():
            return
        self._press = None
        self.drag_requested.emit(self)

    def mouseReleaseEvent(self, event):
        self._press = None
        super().mouseReleaseEvent(event)

    def _row(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(5)
        return h

    # ---------------------------------------------------------- 小工具
    def _label(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setObjectName("fieldLabel")
        return lb

    def _combo(self, items, key: str, width: int = 0) -> QComboBox:
        cb = QComboBox()
        for label, value in items:
            cb.addItem(tr(label), value)
        idx = cb.findData(self.rule.params.get(key))
        if idx >= 0:
            cb.setCurrentIndex(idx)
        if width:
            cb.setMinimumWidth(width)
        cb.currentIndexChanged.connect(lambda _i, k=key, c=cb: self._set(k, c.currentData()))
        return cb

    def _spin(self, key: str, lo: int, hi: int, width: int = 58) -> QSpinBox:
        sp = QSpinBox()
        sp.setRange(lo, hi)
        sp.setValue(int(self.rule.params.get(key, lo)))
        sp.setFixedWidth(width)
        sp.valueChanged.connect(lambda v, k=key: self._set(k, v))
        return sp

    def _edit(self, key: str, placeholder: str = "", width: int = 0) -> QLineEdit:
        ed = QLineEdit(str(self.rule.params.get(key, "") or ""))
        ed.setPlaceholderText(tr(placeholder) if placeholder else "")
        ed.setClearButtonEnabled(True)
        if width:
            ed.setFixedWidth(width)
        else:
            ed.setMinimumWidth(110)
        ed.textChanged.connect(lambda t, k=key: self._set(k, t))
        return ed

    def _check(self, key: str, text: str) -> QCheckBox:
        cb = QCheckBox(tr(text))
        cb.setChecked(bool(self.rule.params.get(key)))
        cb.stateChanged.connect(lambda st, k=key: self._set(k, st == Qt.Checked))
        return cb

    def _set(self, key: str, value) -> None:
        self.rule.params[key] = value
        self._refresh()
        self.changed.emit()

    def _on_enabled(self, state: int) -> None:
        self.rule.enabled = state == Qt.Checked
        self._refresh()
        self.changed.emit()

    def _refresh(self) -> None:
        desc = self.rule.describe()
        if not self.rule.enabled:
            desc = desc + "  " + tr("（已停用）")
        self.desc.setText(desc)
        self.grid.parentWidget().setEnabled(self.rule.enabled)
        self.desc.setStyleSheet("" if self.rule.enabled else "color:#9aa0a6;")

    def _hint(self, text: str) -> QLabel:
        lb = QLabel(tr(text))
        lb.setObjectName("hint")
        return lb

    # ---------------------------------------------------------- 添加
    def _build_add(self) -> None:
        r0 = self._row()
        r0.addWidget(self._label(tr("位置")))
        r0.addWidget(self._combo(
            [(POSITION_LABELS[k], k) for k in ("prefix", "stem_suffix", "ext_suffix")],
            "position", 200))
        r0.addSpacing(6)
        r0.addWidget(self._label(tr("内容")))
        self.ed_content = self._edit("content", "如 IMG_{n} 或 {date}-产品")
        r0.addWidget(self.ed_content, 1)
        self.grid.addLayout(r0, 0, 0, 1, 2)

        r1 = self._row()
        r1.addWidget(self._label(tr("序号")))
        r1.addWidget(QLabel(tr("起始")))
        r1.addWidget(self._spin("seq_start", 0, 999999))
        r1.addWidget(QLabel(tr("步长")))
        r1.addWidget(self._spin("seq_step", -99, 99, 50))
        r1.addWidget(QLabel(tr("位数")))
        r1.addWidget(self._spin("seq_digits", 0, 10, 50))
        r1.addSpacing(10)
        r1.addWidget(self._label(tr("时间格式")))
        self.ed_date = self._edit("date_format", "YYYYMMDD", 120)
        r1.addWidget(self.ed_date)
        self.lb_date_preview = QLabel()
        self.lb_date_preview.setObjectName("hint")
        r1.addWidget(self.lb_date_preview)
        r1.addStretch(1)
        self.grid.addLayout(r1, 1, 0, 1, 2)

        # 占位符按钮单独一行，窄窗口下也不会把卡片撑宽
        r2 = self._row()
        r2.addWidget(self._hint("可用占位符："))
        for token, tip in (("{n}", "序号"), ("{date}", "时间"), ("{name}", "当前主名"),
                           ("{ext}", "扩展名"), ("{orig}", "原文件名"),
                           ("{parent}", "上级文件夹名")):
            b = QToolButton()
            b.setText(token)
            b.setToolTip(tr(tip))
            b.setObjectName("tokenBtn")
            b.clicked.connect(lambda _=False, t=token: self._insert_token(t))
            r2.addWidget(b)
        r2.addStretch(1)
        self.grid.addLayout(r2, 2, 0, 1, 2)

        self.ed_date.textChanged.connect(self._update_date_preview)
        self._update_date_preview()

    def _insert_token(self, token: str) -> None:
        self.ed_content.insert(token)
        self.ed_content.setFocus()

    def _update_date_preview(self) -> None:
        self.lb_date_preview.setText("= " + N.format_now(self.ed_date.text()))

    # ---------------------------------------------------------- 删除
    def _build_delete(self) -> None:
        r0 = self._row()
        r0.addWidget(self._label(tr("范围")))
        r0.addWidget(self._combo([(SCOPE_LABELS[k], k) for k in ("stem", "ext", "full")],
                                 "scope", 120))
        r0.addWidget(self._label(tr("方式")))
        mode_combo = self._combo(
            [("删除指定文字", "text"), ("正则表达式", "regex"),
             ("按位置删除", "position"), ("删除括号内容", "brackets")],
            "mode", 140)
        r0.addWidget(mode_combo)
        r0.addWidget(self._check("trim_after", "清理残留空格"))
        r0.addStretch(1)
        self.grid.addLayout(r0, 0, 0, 1, 2)

        self.stack = QStackedWidget()
        self.grid.addWidget(self.stack, 1, 0, 1, 2)

        p1 = QWidget()
        l1 = self._row()
        p1.setLayout(l1)
        l1.addWidget(self._edit("text", "要删除的文字，如 副本"))
        l1.addWidget(self._check("ignore_case", "忽略大小写"))
        l1.addWidget(self._check("first_only", "只删第一个"))
        self.stack.addWidget(p1)

        p2 = QWidget()
        l2 = self._row()
        p2.setLayout(l2)
        l2.addWidget(self._edit("pattern", r"正则，如 \(\d+\) 或 ^\d{8}_"))
        l2.addWidget(self._check("ignore_case", "忽略大小写"))
        l2.addWidget(self._check("first_only", "只删第一个"))
        self.stack.addWidget(p2)

        p3 = QWidget()
        l3 = self._row()
        p3.setLayout(l3)
        l3.addWidget(QLabel(tr("从")))
        l3.addWidget(self._combo([("开头", "head"), ("结尾", "tail")], "pos_from", 90))
        l3.addWidget(QLabel(tr("删除")))
        l3.addWidget(self._spin("count", 0, 500, 64))
        l3.addWidget(QLabel(tr("个字符")))
        l3.addStretch(1)
        self.stack.addWidget(p3)

        p4 = QWidget()
        l4 = self._row()
        p4.setLayout(l4)
        l4.addWidget(QLabel(tr("括号类型")))
        l4.addWidget(self._combo([("圆括号 ( )", "()"), ("方括号 [ ]", "[]"),
                                  ("花括号 { }", "{}"), ("尖括号 < >", "<>"),
                                  ("中文括号 （ ）", "（）"), ("中文方头 【 】", "【】")],
                                 "bracket", 150))
        l4.addWidget(self._check("keep_bracket", "保留括号，只删里面的内容"))
        l4.addStretch(1)
        self.stack.addWidget(p4)

        modes = ["text", "regex", "position", "brackets"]
        cur = self.rule.params.get("mode", "text")
        self.stack.setCurrentIndex(modes.index(cur) if cur in modes else 0)
        mode_combo.currentIndexChanged.connect(lambda i: self.stack.setCurrentIndex(i))

    # ---------------------------------------------------------- 替换
    def _build_replace(self) -> None:
        r0 = self._row()
        r0.addWidget(self._label(tr("范围")))
        r0.addWidget(self._combo([(SCOPE_LABELS[k], k) for k in ("stem", "ext", "full")],
                                 "scope", 120))
        r0.addWidget(self._label(tr("查找")))
        r0.addWidget(self._edit("find", "要被替换的内容"), 1)
        r0.addWidget(QLabel("→"))
        r0.addWidget(self._label(tr("替换为")))
        r0.addWidget(self._edit("repl", "留空表示删除"), 1)
        self.grid.addLayout(r0, 0, 0, 1, 2)

        r1 = self._row()
        r1.addWidget(self._check("use_regex", r"使用正则（替换处可用 \1 或 $1 引用分组）"))
        r1.addWidget(self._check("ignore_case", "忽略大小写"))
        r1.addWidget(self._check("first_only", "只替换第一个"))
        r1.addStretch(1)
        self.grid.addLayout(r1, 1, 0, 1, 2)

    # ---------------------------------------------------------- 转换
    def _build_convert(self) -> None:
        r0 = self._row()
        r0.addWidget(self._label(tr("范围")))
        r0.addWidget(self._combo([(SCOPE_LABELS[k], k) for k in ("stem", "ext", "full")],
                                 "scope", 120))
        r0.addSpacing(8)
        r0.addWidget(self._label(tr("大小写")))
        r0.addWidget(self._combo([(CASE_LABELS[k], k) for k in
                                  ("none", "upper", "lower", "title", "capitalize")],
                                 "case", 160))
        r0.addSpacing(8)
        r0.addWidget(self._label(tr("全/半角")))
        r0.addWidget(self._combo([(WIDTH_LABELS[k], k) for k in ("none", "half", "full")],
                                 "width", 130))
        r0.addWidget(self._combo([("全部字符", "all"), ("仅字母数字", "alnum"),
                                  ("仅符号", "punct")], "width_scope", 110))
        r0.addStretch(1)
        self.grid.addLayout(r0, 0, 0, 1, 2)

        r1 = self._row()
        r1.addWidget(self._check("trim", "去首尾空格"))
        r1.addWidget(self._check("collapse", "连续空格合一"))
        r1.addWidget(self._check("nospace", "删所有空格"))
        r1.addWidget(self._check("accents", "去重音(á→a)"))
        r1.addSpacing(10)
        r1.addWidget(self._label(tr("扩展名改为")))
        r1.addWidget(self._edit("set_ext", "留空不改", 90))
        r1.addWidget(self._hint("对所有文件生效"))
        r1.addStretch(1)
        self.grid.addLayout(r1, 1, 0, 1, 2)


class _DropArea(QWidget):
    """卡片容器：接收拖动，画一条插入指示线。"""

    def __init__(self, panel: "RulePanel"):
        super().__init__()
        self.panel = panel
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_RULE) and self.panel.drag_card is not None:
            event.setDropAction(Qt.MoveAction)
            event.accept()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat(MIME_RULE) or self.panel.drag_card is None:
            return
        pos = event.position().toPoint()
        self.panel.show_drop_indicator(pos.y())
        # 拖到上下边缘时自动滚动
        sb = self.panel.scroll.verticalScrollBar()
        if pos.y() < 28:
            sb.setValue(sb.value() - 14)
        elif pos.y() > self.height() - 28:
            sb.setValue(sb.value() + 14)
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event):
        self.panel.hide_drop_indicator()

    def dropEvent(self, event):
        card = self.panel.drag_card
        if card is None or not event.mimeData().hasFormat(MIME_RULE):
            return
        idx = self.panel.drop_index(event.position().y())
        self.panel.hide_drop_indicator()
        self.panel.reorder(card, idx)
        event.setDropAction(Qt.MoveAction)
        event.accept()


class RulePanel(QWidget):
    rules_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: list[RuleCard] = []
        self.drag_card: RuleCard | None = None
        self._last_group = ""
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        bar = QWidget()
        bar.setObjectName("sectionBar")
        bar.setFixedHeight(38)
        h = QHBoxLayout(bar)
        h.setContentsMargins(10, 2, 8, 2)
        h.setSpacing(6)
        title = QLabel(tr("改名规则"))
        title.setObjectName("sectionTitle")
        h.addWidget(title)
        self.lb_hint = QLabel(tr("按从上到下的顺序依次执行 · 拖动卡片可调整顺序"))
        self.lb_hint.setObjectName("hint")
        h.addWidget(self.lb_hint)
        h.addStretch(1)

        self.btn_add = QToolButton()
        self.btn_add.setText(tr("添加规则"))
        self.btn_add.setIcon(icon("plus", light=True))
        self.btn_add.setIconSize(QSize(16, 16))
        self.btn_add.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_add.setPopupMode(QToolButton.InstantPopup)
        self.btn_add.setObjectName("primaryBtn")
        menu = QMenu(self.btn_add)
        for t in ("add", "delete", "replace", "convert"):
            act = menu.addAction(tr(RULE_LABELS[t]))
            act.triggered.connect(lambda _=False, k=t: self.add_rule(k))
        self.btn_add.setMenu(menu)
        h.addWidget(self.btn_add)

        btn_clear = QPushButton(tr("清空"))
        btn_clear.setObjectName("flatBtn")
        btn_clear.clicked.connect(self.clear_rules)
        h.addWidget(btn_clear)

        btn_save = QPushButton(tr("存为规则组"))
        btn_save.setObjectName("flatBtn")
        btn_save.setToolTip(tr("把这组规则存下来，下次一键载入"))
        btn_save.clicked.connect(self._save_group)
        h.addWidget(btn_save)

        self.btn_load = QToolButton()
        self.btn_load.setText(tr("规则组 ▾"))
        self.btn_load.setObjectName("flatBtn")
        self.btn_load.setPopupMode(QToolButton.InstantPopup)
        self.btn_load.setMenu(self._build_preset_menu())
        h.addWidget(self.btn_load)

        outer.addWidget(bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumWidth(0)
        self.scroll.setObjectName("ruleScroll")
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.holder = _DropArea(self)
        self.vbox = QVBoxLayout(self.holder)
        self.vbox.setContentsMargins(10, 8, 10, 8)
        self.vbox.setSpacing(7)
        self.vbox.addStretch(1)
        self.scroll.setWidget(self.holder)
        outer.addWidget(self.scroll, 1)

        self.empty = QLabel(tr("还没有规则。\n点右上角「添加规则」，"
                               "比如「添加 → 文件名开头 → IMG_{n}」。"))
        self.empty.setObjectName("emptyHint")
        self.empty.setAlignment(Qt.AlignCenter)
        self.vbox.insertWidget(0, self.empty)

        # 拖动插入指示线（绝对定位的浮层，不进布局，避免位置抖动）
        self.indicator = QFrame(self.holder)
        self.indicator.setObjectName("dropLine")
        self.indicator.setFixedHeight(3)
        self.indicator.hide()

    # ---------------------------------------------------------- 规则增删
    def add_rule(self, rule_type: str) -> None:
        self._add_card(RuleCard(Rule(type=rule_type)))
        self.rules_changed.emit()
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum())

    def _add_card(self, card: RuleCard) -> None:
        card.changed.connect(self.rules_changed)
        card.deleted.connect(self._remove_card)
        card.move_up.connect(lambda c: self._move(c, -1))
        card.move_down.connect(lambda c: self._move(c, 1))
        card.drag_requested.connect(self.start_drag)
        self.cards.append(card)
        self.vbox.insertWidget(len(self.cards) - 1, card)
        self._sync_empty()

    def _remove_card(self, card: RuleCard) -> None:
        if card in self.cards:
            self.cards.remove(card)
            self.vbox.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
            self._sync_empty()
            self.rules_changed.emit()

    def _move(self, card: RuleCard, delta: int) -> None:
        i = self.cards.index(card)
        j = i + delta
        if not (0 <= j < len(self.cards)):
            return
        self.cards[i], self.cards[j] = self.cards[j], self.cards[i]
        self._relayout()
        self.rules_changed.emit()

    def _relayout(self) -> None:
        for c in self.cards:
            self.vbox.removeWidget(c)
        for i, c in enumerate(self.cards):
            self.vbox.insertWidget(i, c)

    def clear_rules(self) -> None:
        for card in list(self.cards):
            self._remove_card(card)

    def _sync_empty(self) -> None:
        self.empty.setVisible(not self.cards)
        self.lb_hint.setVisible(bool(self.cards))

    def rules(self) -> list[Rule]:
        return [c.rule for c in self.cards]

    def set_rules(self, rules: list[Rule]) -> None:
        for card in list(self.cards):
            self.vbox.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self.cards.clear()
        for r in rules:
            self._add_card(RuleCard(r))
        self._sync_empty()
        self.rules_changed.emit()

    # ---------------------------------------------------------- 拖动
    def start_drag(self, card: RuleCard) -> None:
        self.drag_card = card
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_RULE, b"1")
        drag.setMimeData(mime)
        pix = card.grab()
        if not pix.isNull():
            drag.setPixmap(pix.scaled(int(pix.width() * 0.6), int(pix.height() * 0.6),
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation))
            drag.setHotSpot(QPoint(0, 0))
        card.setProperty("dragging", True)
        card.setStyleSheet("QFrame#ruleCard{border:1px dashed #0b57d0;}")
        drag.exec(Qt.MoveAction)
        card.setStyleSheet("")
        card.setProperty("dragging", False)
        self.hide_drop_indicator()
        self.drag_card = None

    def _others(self) -> list[RuleCard]:
        return [c for c in self.cards if c is not self.drag_card]

    def drop_index(self, y: int) -> int:
        idx = 0
        for c in self._others():
            if y > c.geometry().center().y():
                idx += 1
        return idx

    def show_drop_indicator(self, y: int) -> None:
        others = self._others()
        if not others:
            self.indicator.hide()
            return
        idx = self.drop_index(y)
        if idx == 0:
            line_y = others[0].geometry().top() - 4
        else:
            line_y = others[idx - 1].geometry().bottom() + 4
        self.indicator.setGeometry(12, max(0, line_y), max(0, self.holder.width() - 24), 3)
        self.indicator.show()
        self.indicator.raise_()

    def hide_drop_indicator(self) -> None:
        self.indicator.hide()

    def reorder(self, card: RuleCard, index: int) -> None:
        others = [c for c in self.cards if c is not card]
        index = max(0, min(index, len(others)))
        if card in self.cards and self.cards.index(card) == index:
            return                      # 原地放下，不用动
        others.insert(index, card)
        self.cards = others
        self._relayout()
        self.rules_changed.emit()

    # ---------------------------------------------------------- 规则组
    def _preset_files(self) -> list[Path]:
        d = PRESET_DIR()
        d.mkdir(parents=True, exist_ok=True)
        return sorted(d.glob("*.json"), key=lambda p: p.stem.casefold())

    def _build_preset_menu(self) -> QMenu:
        menu = QMenu(self)
        files = self._preset_files()
        if not files:
            a = menu.addAction(tr("（还没有保存过规则组）"))
            a.setEnabled(False)
        for f in files:
            act = menu.addAction(f.stem)
            act.triggered.connect(lambda _=False, p=f: self._load_preset(p))
        menu.addSeparator()
        if files:
            del_menu = menu.addMenu(tr("删除规则组"))
            for f in files:
                act = del_menu.addAction(f.stem)
                act.triggered.connect(lambda _=False, p=f: self._delete_group(p))
        menu.addAction(tr("从文件导入…")).triggered.connect(self._import_preset)
        return menu

    def _refresh_preset_menu(self) -> None:
        self.btn_load.setMenu(self._build_preset_menu())

    @staticmethod
    def _safe_name(name: str) -> str:
        bad = '<>:"/\\|?*'
        out = "".join("_" if c in bad else c for c in name).strip(" .")
        return out or "group"

    def _save_group(self) -> None:
        if not self.cards:
            QMessageBox.information(self, tr("提示"), tr("当前没有规则可保存。"))
            return
        d = PRESET_DIR()
        d.mkdir(parents=True, exist_ok=True)
        name, ok = QInputDialog.getText(
            self, tr("保存为规则组"),
            tr("给这组规则起个名字，下次从「规则组」里一键载入："),
            QLineEdit.Normal, self._last_group or tr("我的规则组"))
        name = (name or "").strip()
        if not ok or not name:
            return
        path = d / (self._safe_name(name) + ".json")
        if path.exists():
            ret = QMessageBox.question(
                self, tr("已存在"),
                tr("规则组「{name}」已存在，要覆盖吗？", name=name),
                QMessageBox.Cancel | QMessageBox.Ok)
            if ret != QMessageBox.Ok:
                return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in self.rules()], f,
                          ensure_ascii=False, indent=1)
        except OSError as exc:
            QMessageBox.warning(self, tr("保存失败"), str(exc))
            return
        self._last_group = name
        self._refresh_preset_menu()
        QMessageBox.information(self, tr("已保存"),
                                tr("规则组「{name}」已保存。", name=name))

    def _delete_group(self, path: Path) -> None:
        if QMessageBox.question(
                self, tr("删除规则组"),
                tr("确定删除规则组「{name}」？", name=path.stem),
                QMessageBox.Cancel | QMessageBox.Ok) != QMessageBox.Ok:
            return
        try:
            path.unlink()
        except OSError:
            pass
        self._refresh_preset_menu()

    def _load_preset(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            rules = [Rule.from_dict(d) for d in data]
        except Exception as exc:
            QMessageBox.warning(self, tr("载入失败"), f"{path.name}: {exc}")
            return
        self.set_rules(rules)
        self._last_group = path.stem

    def _import_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("导入规则组"), str(PRESET_DIR()),
                                              tr("预设文件 (*.json)"))
        if path:
            self._load_preset(Path(path))


