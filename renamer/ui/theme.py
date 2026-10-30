"""界面样式。浅色 + 细边框，信息密度接近资源管理器。"""

from __future__ import annotations

import os

from ..resources import resource


def _url(name: str) -> str:
    p = resource(os.path.join("assets", "ui", name))
    return p.replace("\\", "/")


QSS = """
QWidget {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 12px;
    color: #1f2328;
}
QMainWindow, QWidget#central { background: #f6f7f9; }

QWidget#sectionBar {
    background: #ffffff;
    border-bottom: 1px solid #e3e6ea;
}
QLabel#sectionTitle { font-weight: 600; font-size: 13px; }
QLabel#fieldLabel { color: #57606a; }
QLabel#hint { color: #8b949e; font-size: 11px; }
QLabel#emptyHint { color: #9aa0a6; padding: 28px; }
QLabel#ruleDesc { color: #1f2328; }
QLabel#pathLabel { color: #57606a; padding: 0 4px; }

QFrame#ruleCard {
    background: #ffffff;
    border: 1px solid #dde1e6;
    border-radius: 6px;
}
QFrame#hr { border: none; border-top: 1px solid #eceff2; max-height: 1px; }
QFrame#dropLine { background: #0b57d0; border: none; border-radius: 1px; }
QLabel#appTitle { font-size: 17px; font-weight: 700; }
QLabel#linkLabel { color: #0b57d0; }

QPushButton, QToolButton {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 5px;
    padding: 5px 12px;
    color: #1f2328;
}
QPushButton:hover, QToolButton:hover { background: #f3f4f6; border-color: #b6bdc6; }
QPushButton:pressed, QToolButton:pressed { background: #e9ecef; }
QPushButton:disabled, QToolButton:disabled { color: #a8b0b8; background: #f6f7f9; }

QPushButton#primaryBtn, QToolButton#primaryBtn {
    background: #0b57d0; color: #ffffff; border: 1px solid #0b57d0; font-weight: 600;
}
QPushButton#primaryBtn:hover, QToolButton#primaryBtn:hover { background: #0a4bb5; }
QPushButton#primaryBtn:disabled, QToolButton#primaryBtn:disabled {
    background: #b6c7e6; border-color: #b6c7e6; color: #ffffff;
}

QPushButton#flatBtn, QToolButton#flatBtn {
    border: 1px solid transparent; background: transparent; color: #57606a;
}
QPushButton#flatBtn:hover, QToolButton#flatBtn:hover {
    background: #eef1f4; border-color: transparent; color: #1f2328;
}

QToolButton#cardBtn {
    border: none; background: transparent; color: #8b949e; padding: 0;
    font-size: 13px;
}
QToolButton#cardBtn:hover { background: #eceff2; border-radius: 3px; color: #1f2328; }

QToolButton#tokenBtn {
    border: 1px solid #dde1e6; border-radius: 3px; padding: 0 5px;
    color: #0b57d0; background: #f6f8fb; font-family: Consolas, monospace;
    font-size: 11px; min-height: 18px;
}
QToolButton#tokenBtn:hover { background: #e8eefb; border-color: #b9cdf2; }

QLineEdit, QSpinBox, QComboBox {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    padding: 3px 6px;
    min-height: 20px;
    selection-background-color: #0b57d0;
    selection-color: #ffffff;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #0b57d0; }
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
    background: #f2f4f6; color: #9aa0a6;
}

/* ---- 数字框的上下箭头（默认是空白的，必须自己画） */
QSpinBox { padding-right: 16px; }
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 15px;
    background: transparent;
    border-left: 1px solid #e8ebef;
    border-bottom: 1px solid #e8ebef;
    border-top-right-radius: 3px;
}
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 15px;
    background: transparent;
    border-left: 1px solid #e8ebef;
    border-bottom-right-radius: 3px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #eef1f4; }
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed { background: #e2e6ea; }
QSpinBox::up-arrow { image: url("@UP@"); width: 7px; height: 4px; }
QSpinBox::down-arrow { image: url("@DOWN@"); width: 7px; height: 4px; }
QSpinBox::up-arrow:disabled, QSpinBox::up-arrow:off { image: url("@UP_DIS@"); }
QSpinBox::down-arrow:disabled, QSpinBox::down-arrow:off { image: url("@DOWN_DIS@"); }

/* ---- 下拉框 */
QComboBox { padding-right: 22px; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 20px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow { image: url("@DOWN@"); width: 9px; height: 6px; }
QComboBox QAbstractItemView {
    border: 1px solid #d0d7de; background: #ffffff;
    selection-background-color: #e8eefb; selection-color: #1f2328;
    outline: none;
}

QTableView {
    background: #ffffff;
    alternate-background-color: #fbfcfd;
    border: none;
    gridline-color: #eef0f3;
    selection-background-color: #e8eefb;
    selection-color: #1f2328;
}
QTableView::item { padding: 2px 4px; }
QHeaderView::section {
    background: #f1f3f5;
    color: #57606a;
    border: none;
    border-right: 1px solid #e3e6ea;
    border-bottom: 1px solid #d8dde3;
    padding: 5px 6px;
    font-weight: 600;
}
QHeaderView::section:hover { background: #e9ecef; }

QWidget#treeWrap { background: #ffffff; }

QTreeView {
    background: #ffffff;
    border: none;
    outline: none;
    show-decoration-selected: 1;
}
QTreeView::item { padding: 5px 6px 5px 2px; border: none; }
QTreeView::item:selected { background: #e8eefb; color: #1f2328; }
QTreeView::item:hover { background: #f3f6fb; }

QScrollArea#ruleScroll { background: #f6f7f9; border: none; }
QScrollBar:vertical {
    background: transparent; width: 10px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #c9cfd6; border-radius: 5px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #aeb6bf; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: #c9cfd6; border-radius: 5px; min-width: 24px; }

QSplitter::handle { background: #e3e6ea; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

QStatusBar { background: #ffffff; border-top: 1px solid #e3e6ea; color: #57606a; }
QToolTip {
    background: #1f2328; color: #ffffff; border: none; padding: 4px 6px;
}

/* 复选框交给 Fusion 画：自带对勾，比自绘的纯色方块好认得多 */
QCheckBox { spacing: 6px; }

QMenu { background: #ffffff; border: 1px solid #d0d7de; padding: 4px; }
QMenu::item { padding: 5px 22px 5px 12px; border-radius: 4px; }
QMenu::item:selected { background: #e8eefb; }
QMenu::separator { height: 1px; background: #eceff2; margin: 4px 6px; }
"""


def _build() -> str:
    up = _url("up.png")
    down = _url("down.png")
    css = QSS
    css = css.replace("@UP_DIS@", up)      # 禁用态先用同色，避免空白
    css = css.replace("@DOWN_DIS@", down)
    css = css.replace("@UP@", up)
    css = css.replace("@DOWN@", down)
    return css


QSS = _build()
