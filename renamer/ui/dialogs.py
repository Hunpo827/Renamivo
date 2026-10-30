"""关于窗口与改名结果提示。"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QMessageBox, QPushButton, QVBoxLayout,
                               QWidget)

from .. import meta
from ..core.config import app_data_dir, load_config
from ..i18n import tr
from ..resources import resource


def github_repo() -> str:
    """优先读 config.json，其次 meta.py；都空就返回空串。"""
    try:
        repo = (load_config() or {}).get("github_repo") or ""
    except Exception:
        repo = ""
    return (repo or meta.GITHUB_REPO or "").strip().strip("/")


def open_url(url: str) -> None:
    QDesktopServices.openUrl(QUrl(url))


def show_rename_result(parent, result, skipped: int = 0) -> None:
    """执行完改名后的统一提示：成功 / 失败数量 + 失败明细。"""
    ok = result.done
    fail = len(result.failed)
    box = QMessageBox(parent)
    box.setWindowTitle(tr("改名结果"))
    if fail == 0:
        box.setIcon(QMessageBox.Information)
        text = tr("全部成功：{ok} 个文件已改名。", ok=ok)
    else:
        box.setIcon(QMessageBox.Warning)
        text = tr("成功 {ok} 个，失败 {fail} 个。", ok=ok, fail=fail)
    if skipped:
        text += "\n" + tr("跳过 {n} 个冲突项。", n=skipped)
    box.setText(text)
    if result.rolled_back:
        box.setInformativeText(tr("已回滚到改名前的状态。"))
    if result.failed:
        lines = [tr("失败项：")]
        for path, msg in result.failed[:30]:
            lines.append(f"  {os.path.basename(path)} — {msg}")
        if len(result.failed) > 30:
            lines.append(tr("… 另有 {n} 个", n=len(result.failed) - 30))
        box.setDetailedText("\n".join(lines))
    box.exec()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("关于"))
        self.setModal(True)
        self.setMinimumWidth(560)
        self._repo = github_repo()
        self._build()

    # ---------------------------------------------------------- UI
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 14)
        outer.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(14)
        icon_path = resource(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            lb_icon = QLabel()
            pix = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio,
                                            Qt.SmoothTransformation)
            lb_icon.setPixmap(pix)
            lb_icon.setFixedSize(64, 64)
            head.addWidget(lb_icon, 0, Qt.AlignTop)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        name = QLabel(tr("易名匣"))
        name.setObjectName("appTitle")
        title_box.addWidget(name)
        ver = QLabel(f"v{meta.APP_VERSION}")
        ver.setObjectName("hint")
        title_box.addWidget(ver)
        desc = QLabel(tr("批量改名 Windows 文件名，先预览再执行，支持撤销。"))
        desc.setWordWrap(True)
        title_box.addWidget(desc)
        head.addLayout(title_box, 1)
        outer.addLayout(head)

        outer.addWidget(self._line())

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        row = 0

        grid.addWidget(self._caption(tr("数据目录")), row, 0, Qt.AlignTop)
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        data_path = QLabel(str(app_data_dir()))
        data_path.setObjectName("hint")
        data_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        data_path.setWordWrap(True)
        path_row.addWidget(data_path, 1)
        btn_dir = QPushButton(tr("打开目录"))
        btn_dir.setObjectName("flatBtn")
        btn_dir.clicked.connect(lambda: open_url(QUrl.fromLocalFile(str(app_data_dir())).toString()))
        path_row.addWidget(btn_dir)
        grid.addLayout(path_row, row, 1)
        row += 1

        grid.addWidget(self._caption("GitHub"), row, 0, Qt.AlignTop)
        if self._repo:
            link = QLabel(f"https://github.com/{self._repo}")
            link.setObjectName("linkLabel")
            link.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(link, row, 1)
        else:
            hint = QLabel(tr("GitHub 仓库地址未配置") + "\n" +
                          tr("在 config.json 里填 github_repo，或在 renamer/meta.py 里改 GITHUB_REPO。"))
            hint.setObjectName("hint")
            hint.setWordWrap(True)
            grid.addWidget(hint, row, 1)
        row += 1

        outer.addLayout(grid)
        outer.addWidget(self._line())

        short = QLabel(f"<b>{tr('快捷键')}</b><br>{tr('Ctrl+O 打开文件夹 · F5 刷新 · Ctrl+F 搜索')}")
        short.setWordWrap(True)
        outer.addWidget(short)
        safety = QLabel(f"<b>{tr('安全机制')}</b><br>"
                        + tr("所有改名先预览；冲突会被拦下；执行中途出错自动回滚；随时可撤销。"))
        safety.setWordWrap(True)
        outer.addWidget(safety)

        outer.addWidget(self._line())

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.btn_gh = QPushButton(tr("GitHub 项目主页"))
        self.btn_gh.setObjectName("flatBtn")
        self.btn_gh.setEnabled(bool(self._repo))
        self.btn_gh.clicked.connect(
            lambda: open_url(meta.GITHUB_HOME.format(repo=self._repo)))
        buttons.addWidget(self.btn_gh)

        self.btn_update = QPushButton(tr("检查最新版本"))
        self.btn_update.setObjectName("primaryBtn")
        self.btn_update.setEnabled(bool(self._repo))
        self.btn_update.clicked.connect(self.check_update)
        buttons.addWidget(self.btn_update)

        btn_close = QPushButton(tr("关闭"))
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_close)
        outer.addLayout(buttons)

    def _caption(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setObjectName("fieldLabel")
        return lb

    def _line(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setObjectName("hr")
        return f

    # ---------------------------------------------------------- 更新
    def check_update(self) -> None:
        """按需求：直接跳到 GitHub 最新版下载页，不做版本比对。"""
        if not self._repo:
            QMessageBox.information(
                self, tr("提示"),
                tr("GitHub 仓库地址未配置") + "\n" +
                tr("在 config.json 里填 github_repo，或在 renamer/meta.py 里改 GITHUB_REPO。"))
            return
        open_url(meta.GITHUB_LATEST.format(repo=self._repo))
