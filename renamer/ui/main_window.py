"""主窗口。"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

from PySide6.QtCore import (QDir, QModelIndex, QPoint, QSettings, QSize, Qt,
                            QTimer, Signal)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
                               QFileSystemModel, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMenu, QMessageBox,
                               QPushButton, QSplitter, QTableView, QToolButton,
                               QTreeView, QVBoxLayout, QWidget)

from .. import meta
from ..core import history
from ..core.config import (LAST_RULES_PATH, load_config, load_json,
                           save_json)
from ..core.executor import RenamePair, execute, undo
from ..core.rules import ApplyCtx, Rule, apply_rules
from ..core.scanner import scan
from ..core.validator import (STATUS_CONFLICT, STATUS_INVALID, STATUS_OK,
                              evaluate)
from ..i18n import LANG_AUTO, LANGUAGES, current_language, resolve_language, set_language, tr
from ..resources import desktop_dir, resource
from .icons import icon
from .dialogs import AboutDialog, show_rename_result
from .models import (COL_CHECK, COL_DIR, COL_MTIME, COL_NAME, COL_NEW, COL_SIZE,
                     COL_STATUS, COL_TYPE, FileFilterProxy, FileTableModel)
from .rule_widgets import RulePanel


def open_in_explorer(path: str, select: bool = True) -> None:
    path = os.path.normpath(path)
    try:
        if select:
            subprocess.Popen(f'explorer /select,"{path}"')
        else:
            os.startfile(path)  # noqa: S606
    except Exception:
        pass


# ==================================================================== 目录树
class DirPanel(QWidget):
    dir_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = ""
        self.fs = QFileSystemModel(self)
        self.fs.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Drives)
        self.fs.setRootPath("")
        self.fs.setReadOnly(True)

        self.view = QTreeView()
        self.view.setModel(self.fs)
        self.view.setHeaderHidden(True)
        self.view.setIndentation(16)
        self.view.setAnimated(False)
        self.view.setExpandsOnDoubleClick(True)
        self.view.setUniformRowHeights(True)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for c in (1, 2, 3):
            self.view.setColumnHidden(c, True)

        from PySide6.QtWidgets import QHeaderView
        self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)

        root = self.fs.index("")
        if root.isValid():
            self.view.setRootIndex(root)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QWidget()
        bar.setObjectName("sectionBar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(10, 6, 10, 6)
        lb = QLabel(tr("目录"))
        lb.setObjectName("sectionTitle")
        h.addWidget(lb)
        h.addStretch(1)
        lay.addWidget(bar)

        # 套一层白底容器做内边距：QTreeView 自己的 viewportMargins 会被内部布局重置
        wrap = QWidget()
        wrap.setObjectName("treeWrap")
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(6, 6, 6, 6)
        wl.setSpacing(0)
        wl.addWidget(self.view)
        lay.addWidget(wrap, 1)

        self.view.selectionModel().currentChanged.connect(self._on_current)

    def _on_current(self, cur: QModelIndex, _prev) -> None:
        if not cur.isValid():
            return
        path = self.fs.filePath(cur)
        if os.path.isdir(path) and path != self._current:
            self._current = path
            self.dir_changed.emit(path)

    def select_path(self, path: str) -> None:
        path = os.path.abspath(path)
        idx = self.fs.index(path)
        if not idx.isValid():
            drive = os.path.splitdrive(path)[0] + os.sep
            idx = self.fs.index(drive)
        chain = []
        p = idx
        while p.isValid():
            chain.append(p)
            p = p.parent()
        for p in reversed(chain):
            self.view.expand(p)
        self.view.setCurrentIndex(idx)
        self.view.scrollTo(idx, QAbstractItemView.PositionAtCenter)
        # 子项是异步加载的，展开后立刻 scrollTo 往往还看不到，稍后再补一次
        for delay in (60, 250, 600):
            QTimer.singleShot(delay, self._ensure_visible)

    def _ensure_visible(self) -> None:
        idx = self.view.currentIndex()
        if idx.isValid():
            self.view.scrollTo(idx, QAbstractItemView.PositionAtCenter)


# ==================================================================== 文件列表
class FilePanel(QWidget):
    filters_changed = Signal()
    rescan_needed = Signal()
    execute_clicked = Signal()
    language_changed = Signal(str)

    def __init__(self, model: FileTableModel, proxy: FileFilterProxy, parent=None):
        super().__init__(parent)
        self.model = model
        self.proxy = proxy
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        bar = QWidget()
        bar.setObjectName("sectionBar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(6)

        self.ed_search = QLineEdit()
        self.ed_search.setPlaceholderText(tr("搜索文件名或新文件名…"))
        self.ed_search.setClearButtonEnabled(True)
        self.ed_search.setMinimumWidth(140)
        self.ed_search.setMaximumWidth(360)
        self.ed_search.textChanged.connect(self._on_search)
        h.addWidget(self.ed_search, 1)

        self.btn_regex = QToolButton()
        self.btn_regex.setText(".*")
        self.btn_regex.setCheckable(True)
        self.btn_regex.setToolTip(tr("把搜索内容当作正则表达式"))
        self.btn_regex.toggled.connect(lambda _v: self._on_search(self.ed_search.text()))
        h.addWidget(self.btn_regex)

        self.cb_type = QComboBox()
        self.cb_type.setMinimumWidth(100)
        self.cb_type.addItem(tr("全部类型"), None)
        self.cb_type.currentIndexChanged.connect(self._on_type)
        h.addWidget(self.cb_type)

        self.chk_changed = QCheckBox(tr("只看变更"))
        self.chk_changed.stateChanged.connect(
            lambda s: (self.proxy.set_only_changed(s == Qt.Checked),
                       self.filters_changed.emit()))
        h.addWidget(self.chk_changed)

        self.chk_checked = QCheckBox(tr("只看勾选"))
        self.chk_checked.stateChanged.connect(
            lambda s: (self.proxy.set_only_checked(s == Qt.Checked),
                       self.filters_changed.emit()))
        h.addWidget(self.chk_checked)

        self.chk_recursive = QCheckBox(tr("含子文件夹"))
        self.chk_recursive.setToolTip(tr("递归扫描当前目录下的所有子文件夹"))
        self.chk_recursive.stateChanged.connect(lambda _s: self.rescan_needed.emit())
        h.addWidget(self.chk_recursive)

        self.chk_dirs = QCheckBox(tr("含文件夹"))
        self.chk_dirs.setToolTip(tr("把子文件夹也列出来，可以一起改名"))
        self.chk_dirs.stateChanged.connect(lambda _s: self.rescan_needed.emit())
        h.addWidget(self.chk_dirs)

        self.chk_hidden = QCheckBox(tr("隐藏项"))
        self.chk_hidden.stateChanged.connect(lambda _s: self.rescan_needed.emit())
        h.addWidget(self.chk_hidden)

        outer.addWidget(bar)

        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(-1, Qt.AscendingOrder)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setAlternatingRowColors(True)
        self.view.setWordWrap(False)
        self.view.setTextElideMode(Qt.ElideMiddle)
        self.view.verticalHeader().setVisible(False)
        self.view.verticalHeader().setDefaultSectionSize(24)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setShowGrid(False)
        self.view.doubleClicked.connect(self._on_double_click)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._on_context_menu)

        hh = self.view.horizontalHeader()
        from PySide6.QtWidgets import QHeaderView
        hh.setHighlightSections(False)
        hh.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hh.setSectionResizeMode(COL_CHECK, QHeaderView.Fixed)
        hh.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        hh.setSectionResizeMode(COL_DIR, QHeaderView.Fixed)
        hh.setSectionResizeMode(COL_NEW, QHeaderView.Stretch)
        hh.setSectionResizeMode(COL_TYPE, QHeaderView.Fixed)
        hh.setSectionResizeMode(COL_SIZE, QHeaderView.Fixed)
        hh.setSectionResizeMode(COL_MTIME, QHeaderView.Fixed)
        hh.setSectionResizeMode(COL_STATUS, QHeaderView.Fixed)
        self.view.setColumnWidth(COL_CHECK, 30)
        self.view.setColumnWidth(COL_DIR, 130)
        self.view.setColumnWidth(COL_TYPE, 80)
        self.view.setColumnWidth(COL_SIZE, 84)
        self.view.setColumnWidth(COL_MTIME, 130)
        self.view.setColumnWidth(COL_STATUS, 118)
        self.view.setColumnHidden(COL_DIR, True)

        outer.addWidget(self.view, 1)

        act = QWidget()
        act.setObjectName("sectionBar")
        a = QHBoxLayout(act)
        a.setContentsMargins(10, 6, 10, 6)
        a.setSpacing(8)
        self.lb_count = QLabel(tr("未打开文件夹"))
        self.lb_count.setObjectName("pathLabel")
        a.addWidget(self.lb_count)
        a.addStretch(1)

        for text, slot in ((tr("全选"), lambda: self.model.set_all_checked(True)),
                           (tr("全不选"), lambda: self.model.set_all_checked(False)),
                           (tr("反选"), self.model.invert_checked)):
            b = QPushButton(text)
            b.setObjectName("flatBtn")
            b.clicked.connect(slot)
            b.clicked.connect(self.filters_changed.emit)
            a.addWidget(b)

        self.btn_exec = QPushButton(tr("执行改名"))
        self.btn_exec.setObjectName("primaryBtn")
        self.btn_exec.setIcon(icon("play", light=True))
        self.btn_exec.setIconSize(QSize(16, 16))
        self.btn_exec.setMinimumWidth(140)
        self.btn_exec.setEnabled(False)
        self.btn_exec.clicked.connect(self.execute_clicked)
        a.addWidget(self.btn_exec)

        outer.addWidget(act)

    # ---- 筛选槽
    def _on_search(self, text: str) -> None:
        self.proxy.search_regex = self.btn_regex.isChecked()
        self.proxy.set_search(text)
        self.filters_changed.emit()

    def _on_type(self, _i: int) -> None:
        self.proxy.set_ext_filter(self.cb_type.currentData())
        self.filters_changed.emit()

    def refresh_types(self, items) -> None:
        cur = self.cb_type.currentData()
        counts: dict[str, int] = {}
        for it in items:
            if not it.is_dir:
                counts[it.ext.casefold()] = counts.get(it.ext.casefold(), 0) + 1
        self.cb_type.blockSignals(True)
        self.cb_type.clear()
        self.cb_type.addItem(tr("全部类型"), None)
        for ext, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            label = f"{ext.upper() if ext else tr('无扩展名')} ({n})"
            self.cb_type.addItem(label, ext)
        if cur is not None:
            idx = self.cb_type.findData(cur)
            if idx >= 0:
                self.cb_type.setCurrentIndex(idx)
        self.cb_type.blockSignals(False)

    # ---- 交互
    def _on_double_click(self, proxy_index: QModelIndex) -> None:
        src = self.proxy.mapToSource(proxy_index)
        row = self.model.rows[src.row()]
        if row.item.is_dir:
            return
        open_in_explorer(row.item.path)

    def _on_context_menu(self, pos) -> None:
        idx = self.view.indexAt(pos)
        if not idx.isValid():
            return
        src = self.proxy.mapToSource(idx)
        row = self.model.rows[src.row()]
        menu = QMenu(self)
        menu.addAction(tr("在资源管理器中显示")).triggered.connect(
            lambda: open_in_explorer(row.item.path))
        menu.addAction(tr("复制文件名")).triggered.connect(
            lambda: self._copy(row.item.name))
        menu.addAction(tr("复制新文件名")).triggered.connect(
            lambda: self._copy(row.new_name))
        menu.addAction(tr("复制完整路径")).triggered.connect(
            lambda: self._copy(row.item.path))
        menu.addSeparator()
        menu.addAction(tr("打开所在文件夹")).triggered.connect(
            lambda: open_in_explorer(row.item.dir_path, select=False))
        menu.exec(self.view.viewport().mapToGlobal(pos))

    def _copy(self, text: str) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)


# ==================================================================== 主窗口
class MainWindow(QMainWindow):
    restart_requested = Signal()

    def __init__(self, parent=None, start_dir: str = ""):
        super().__init__(parent)
        self.setWindowTitle(tr("易名匣"))
        self.setMinimumSize(1100, 640)
        self.setAcceptDrops(True)
        ico = resource(os.path.join("assets", "icon.ico"))
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        self.settings = QSettings("Renamivo", "Renamivo")
        self.cfg = load_config()
        self.current_dir = ""
        self._items = []
        self._disk_cache: dict[str, set[str]] = {}
        self._busy = False

        self.model = FileTableModel(self)
        self.proxy = FileFilterProxy(self)
        self.proxy.setSourceModel(self.model)

        self._build_ui()
        self._connect()

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._recalc)

        self._restore_geometry()
        self._restore_last_rules()

        start = start_dir if start_dir and os.path.isdir(start_dir) else desktop_dir()
        QTimer.singleShot(0, lambda: self._goto_initial(start))

    # ---------------------------------------------------------- 布局
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top = QWidget()
        top.setObjectName("sectionBar")
        t = QHBoxLayout(top)
        t.setContentsMargins(10, 6, 10, 6)
        t.setSpacing(8)

        self.btn_open = QPushButton(tr("打开文件夹"))
        self.btn_open.setObjectName("primaryBtn")
        self.btn_open.setIcon(icon("folder", light=True))
        self.btn_open.setIconSize(QSize(16, 16))
        t.addWidget(self.btn_open)

        self.btn_up = QPushButton(tr("上一级"))
        self.btn_up.setObjectName("flatBtn")
        self.btn_up.setIcon(icon("up"))
        self.btn_up.setIconSize(QSize(16, 16))
        t.addWidget(self.btn_up)

        self.btn_refresh = QPushButton(tr("刷新"))
        self.btn_refresh.setObjectName("flatBtn")
        self.btn_refresh.setIcon(icon("refresh"))
        self.btn_refresh.setIconSize(QSize(16, 16))
        t.addWidget(self.btn_refresh)

        self.lb_path = QLabel("")
        self.lb_path.setObjectName("pathLabel")
        self.lb_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        t.addWidget(self.lb_path, 1)

        self.btn_undo = QToolButton()
        self.btn_undo.setText(tr("撤销"))
        self.btn_undo.setPopupMode(QToolButton.InstantPopup)
        self.btn_undo.setToolTip(tr("撤销改名"))
        t.addWidget(self.btn_undo)

        self.btn_help = QToolButton()
        self.btn_help.setText(tr("设置"))
        self.btn_help.setToolTip(tr("设置"))
        self.btn_help.clicked.connect(self._show_help_menu)
        t.addWidget(self.btn_help)

        root.addWidget(top)

        self.hsplit = QSplitter(Qt.Horizontal)
        self.dir_panel = DirPanel()
        self.hsplit.addWidget(self.dir_panel)

        self.vsplit = QSplitter(Qt.Vertical)
        self.rule_panel = RulePanel()
        self.file_panel = FilePanel(self.model, self.proxy)
        self.vsplit.addWidget(self.rule_panel)
        self.vsplit.addWidget(self.file_panel)
        self.vsplit.setStretchFactor(0, 0)
        self.vsplit.setStretchFactor(1, 1)
        self.vsplit.setSizes([420, 380])
        self.hsplit.addWidget(self.vsplit)
        self.hsplit.setStretchFactor(0, 0)
        self.hsplit.setStretchFactor(1, 1)
        self.hsplit.setSizes([270, 1000])
        self.hsplit.setChildrenCollapsible(False)

        root.addWidget(self.hsplit, 1)

        self.status = self.statusBar()
        self.status.showMessage(tr("就绪"))

    def _build_help_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.addAction(tr("关于本软件")).triggered.connect(self.show_about)
        act_update = menu.addAction(tr("检查更新"))
        act_update.triggered.connect(self.check_update)
        menu.addAction(tr("GitHub 项目主页")).triggered.connect(self.open_github)
        menu.addSeparator()
        lang_menu = menu.addMenu(tr("界面语言"))
        group = lang_menu
        cur = self.settings.value("language", LANG_AUTO) or LANG_AUTO
        for key, label in ((LANG_AUTO, tr("自动（跟随系统）")),
                           ("zh", LANGUAGES["zh"]), ("en", LANGUAGES["en"])):
            act = group.addAction(label)
            act.setCheckable(True)
            act.setChecked(cur == key)
            act.triggered.connect(lambda _=False, k=key: self.set_language(k))
        return menu

    def _show_help_menu(self) -> None:
        menu = self._build_help_menu()
        pos = self.btn_help.mapToGlobal(QPoint(0, self.btn_help.height() + 2))
        menu.exec(pos)

    def _connect(self) -> None:
        self.btn_open.clicked.connect(self.choose_dir)
        self.btn_up.clicked.connect(self.go_up)
        self.btn_refresh.clicked.connect(self.rescan)


        self.undo_menu = QMenu(self)
        self.undo_menu.aboutToShow.connect(self._populate_undo_menu)
        self.btn_undo.setMenu(self.undo_menu)

        self.dir_panel.dir_changed.connect(self.open_dir)
        self.rule_panel.rules_changed.connect(self._schedule_recalc)
        self.file_panel.filters_changed.connect(self._schedule_recalc)
        self.file_panel.rescan_needed.connect(self.rescan)
        self.file_panel.execute_clicked.connect(self.do_rename)

        self.model.dataChanged.connect(self._on_model_changed)
        self.file_panel.view.horizontalHeader().sortIndicatorChanged.connect(
            lambda *_: self._schedule_recalc())

        for seq, slot in ((QKeySequence.Open, self.choose_dir),
                          (QKeySequence.Refresh, self.rescan)):
            act = QAction(self, shortcut=seq, triggered=slot)
            act.setShortcutContext(Qt.WindowShortcut)
            self.addAction(act)
        act_search = QAction(self, shortcut=QKeySequence.Find,
                             triggered=lambda: (self.file_panel.ed_search.setFocus(),
                                                self.file_panel.ed_search.selectAll()))
        act_search.setShortcutContext(Qt.WindowShortcut)
        self.addAction(act_search)

    # ---------------------------------------------------------- 语言 / 帮助
    def set_language(self, lang: str) -> None:
        self.settings.setValue("language", lang)
        set_language(resolve_language(lang))
        # 应用名是进程级的，启动时设一次就固定了；切语言必须同步改，
        # 否则任务栏、窗口列表里还挂着中文名。
        name = meta.app_display_name()
        QApplication.setApplicationName(name)
        QApplication.setApplicationDisplayName(name)
        self.restart_requested.emit()

    def show_about(self) -> None:
        AboutDialog(self).exec()

    def open_github(self) -> None:
        from .dialogs import github_repo, open_url
        repo = github_repo()
        if not repo:
            QMessageBox.information(
                self, tr("提示"),
                tr("GitHub 仓库地址未配置") + "\n" +
                tr("在 config.json 里填 github_repo，或在 renamer/meta.py 里改 GITHUB_REPO。"))
            return
        open_url(meta.GITHUB_HOME.format(repo=repo))

    def check_update(self) -> None:
        from .dialogs import github_repo, open_url
        repo = github_repo()
        if not repo:
            QMessageBox.information(
                self, tr("提示"),
                tr("GitHub 仓库地址未配置") + "\n" +
                tr("在 config.json 里填 github_repo，或在 renamer/meta.py 里改 GITHUB_REPO。"))
            return
        open_url(meta.GITHUB_LATEST.format(repo=repo))
        self.status.showMessage(tr("已在浏览器中打开最新版下载页"))

    # ---------------------------------------------------------- 目录
    def choose_dir(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(self, tr("打开文件夹"), self.current_dir or "")
        if d:
            self.dir_panel.select_path(d)
            self.open_dir(d)

    def go_up(self) -> None:
        if not self.current_dir:
            return
        parent = os.path.dirname(self.current_dir.rstrip("\\/"))
        if parent and os.path.isdir(parent):
            self.dir_panel.select_path(parent)
            self.open_dir(parent)

    def _goto_initial(self, path: str) -> None:
        """启动时落到桌面：文件列表和左侧目录树都定位过去。"""
        self.dir_panel.select_path(path)
        self.open_dir(path)

    def open_dir(self, path: str) -> None:
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return
        if path != self.current_dir:
            self.current_dir = path
            self.lb_path.setText(path)
            self.lb_path.setToolTip(path)
        self.rescan()

    def rescan(self) -> None:
        if not self.current_dir:
            return
        fp = self.file_panel
        items, warns = scan(
            self.current_dir,
            recursive=fp.chk_recursive.isChecked(),
            include_dirs=fp.chk_dirs.isChecked(),
            include_hidden=fp.chk_hidden.isChecked(),
        )
        self._items = items
        self._disk_cache = self._read_disk_names(items)
        self.model.set_items(items)
        self.file_panel.view.setColumnHidden(COL_DIR, not fp.chk_recursive.isChecked())
        fp.refresh_types(items)
        self.settings.setValue("opt_recursive", fp.chk_recursive.isChecked())
        self.settings.setValue("opt_dirs", fp.chk_dirs.isChecked())
        self.settings.setValue("opt_hidden", fp.chk_hidden.isChecked())
        self._recalc()
        msg = tr("{path} — 共 {n} 项", path=self.current_dir, n=len(items))
        if warns:
            msg += "  |  " + warns[0]
        self.status.showMessage(msg)

    def _read_disk_names(self, items) -> dict[str, set[str]]:
        dirs = {it.dir_path for it in items}
        out: dict[str, set[str]] = {}
        for d in dirs:
            try:
                with os.scandir(d) as it:
                    out[d.casefold()] = {e.name.casefold() for e in it}
            except OSError:
                out[d.casefold()] = set()
        return out

    # ---------------------------------------------------------- 预览计算
    def _schedule_recalc(self) -> None:
        if self._busy:
            return
        self._timer.start()

    def _on_model_changed(self, *_args) -> None:
        self._schedule_recalc()

    def _display_rows(self):
        out = []
        for pr in range(self.proxy.rowCount()):
            src = self.proxy.mapToSource(self.proxy.index(pr, 0))
            if src.isValid() and src.row() < len(self.model.rows):
                out.append(self.model.rows[src.row()])
        return out

    def _recalc(self) -> None:
        if self._busy:
            return
        self._busy = True
        try:
            rows = self.model.rows
            if not rows:
                self._update_counts()
                return
            rules = self.rule_panel.rules()
            now = datetime.now()

            counter = 0
            seq: dict[int, int] = {}
            for row in self._display_rows():
                seq[id(row)] = counter
                if row.checked:
                    counter += 1

            names = []
            for row in rows:
                ctx = ApplyCtx(now=now,
                               parent=os.path.basename(row.item.dir_path) or row.item.dir_path)
                names.append(apply_rules(rules, row.item.name, seq.get(id(row), 0), ctx))

            problems = evaluate([r.item for r in rows], names, self._disk_cache)
            self.model.apply_preview(names, problems)
        finally:
            self._busy = False
        self._update_counts()

    def _update_counts(self) -> None:
        total, checked, will, bad = self.model.counts()
        fp = self.file_panel
        if not self.current_dir:
            fp.lb_count.setText(tr("未打开文件夹"))
            fp.btn_exec.setEnabled(False)
            return
        parts = [tr("共 {n} 项", n=total), tr("勾选 {n}", n=checked)]
        if will:
            parts.append(f"<span style='color:#1a7f37'>{tr('将改名 {n}', n=will)}</span>")
        if bad:
            parts.append(f"<span style='color:#cf222e'>{tr('冲突 {n}', n=bad)}</span>")
        n_un = sum(1 for r in self.model.rows if r.checked and not r.changed)
        if n_un:
            parts.append(tr("无变化 {n}", n=n_un))
        fp.lb_count.setText(" · ".join(parts))
        fp.btn_exec.setEnabled(will > 0)
        fp.btn_exec.setText(tr("执行改名 ({n})", n=will) if will else tr("执行改名"))

    # ---------------------------------------------------------- 执行
    def do_rename(self) -> None:
        rows = [r for r in self.model.rows
                if r.checked and r.changed and r.status == STATUS_OK]
        bad = [r for r in self.model.rows
               if r.checked and r.changed and r.status in (STATUS_CONFLICT, STATUS_INVALID)]
        if not rows:
            QMessageBox.information(self, tr("没有可执行的项目"),
                                    tr("请先添加规则，并勾选需要改名的文件。"))
            return

        if bad:
            detail = "\n".join(f"{r.item.name} → {r.new_name}（{r.msg}）" for r in bad[:10])
            if len(bad) > 10:
                detail += "\n" + tr("… 另有 {n} 个", n=len(bad) - 10)
            box = QMessageBox(self)
            box.setWindowTitle(tr("有项目会失败"))
            box.setIcon(QMessageBox.Warning)
            box.setText(tr("{n} 个项目存在冲突或非法字符，将被跳过。", n=len(bad)))
            box.setDetailedText(detail)
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            box.button(QMessageBox.Ok).setText(
                tr("跳过它们，改另外 {n} 个", n=len(rows)))
            box.button(QMessageBox.Cancel).setText(tr("返回检查"))
            box.exec()
            if box.clickedButton() is box.button(QMessageBox.Cancel):
                return

        head = "\n".join(f"{r.item.name}  →  {r.new_name}" for r in rows[:8])
        if len(rows) > 8:
            head += "\n" + tr("… 另有 {n} 个", n=len(rows) - 8)
        box = QMessageBox(self)
        box.setWindowTitle(tr("确认改名"))
        box.setIcon(QMessageBox.Question)
        box.setText(tr("确定要把 {n} 个文件改名吗？", n=len(rows)))
        box.setInformativeText(tr("改名后可以用顶部的「撤销改名」还原。"))
        box.setDetailedText(head)
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        box.button(QMessageBox.Ok).setText(tr("开始改名"))
        box.button(QMessageBox.Cancel).setText(tr("取消"))
        box.exec()
        if box.clickedButton() is not box.button(QMessageBox.Ok):
            return

        pairs = [RenamePair(r.item.path, os.path.join(r.item.dir_path, r.new_name))
                 for r in rows]
        result = execute(pairs)

        if result.ok:
            history.add_batch([{"old": p.src, "new": p.dst} for p in pairs])
            show_rename_result(self, result, skipped=len(bad))
            self.rescan()
        else:
            show_rename_result(self, result, skipped=len(bad))
            self.rescan()

    def _populate_undo_menu(self) -> None:
        self.undo_menu.clear()
        batches = history.load_history()
        if not batches:
            a = self.undo_menu.addAction(tr("（没有可撤销的操作）"))
            a.setEnabled(False)
            return
        for b in reversed(batches[-12:]):
            act = self.undo_menu.addAction(f"{b['time']}  ·  "
                                           + tr("共 {n} 项", n=b["count"]))
            act.triggered.connect(lambda _=False, bid=b["id"]: self._undo(bid))
        self.undo_menu.addSeparator()
        a = self.undo_menu.addAction(tr("改名历史"))
        a.triggered.connect(self._show_history)

    def _undo(self, bid: str) -> None:
        b = history.get_batch(bid)
        if not b:
            return
        if QMessageBox.question(
                self, tr("撤销改名"),
                tr("要把 {time} 改名的 {n} 个文件改回原名吗？",
                   time=b["time"], n=b["count"]),
                QMessageBox.Cancel | QMessageBox.Ok) != QMessageBox.Ok:
            return
        result = undo(b["records"])
        if result.ok:
            history.drop_batch(bid)
            self.rescan()
            self.status.showMessage(tr("已撤销 {n} 个文件的改名", n=result.done))
        else:
            QMessageBox.warning(self, tr("撤销失败"), result.message)

    def _show_history(self) -> None:
        batches = history.load_history()
        if not batches:
            QMessageBox.information(self, tr("改名历史"), tr("还没有改名记录。"))
            return
        lines = []
        for b in reversed(batches):
            lines.append(f"{b['time']}  ·  " + tr("共 {n} 项", n=b["count"]))
            for r in b["records"][:3]:
                lines.append(f"    {os.path.basename(r['new'])}  ←  "
                             f"{os.path.basename(r['old'])}")
            if len(b["records"]) > 3:
                lines.append("    " + tr("… 另有 {n} 个", n=len(b["records"]) - 3))
        QMessageBox.information(self, tr("改名历史（最近 30 批）"), "\n".join(lines[:120]))

    # ---------------------------------------------------------- 窗口状态
    def _restore_geometry(self) -> None:
        geo = self.settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        else:
            self.resize(1280, 820)
        state = self.settings.value("splitter_h")
        if state:
            self.hsplit.restoreState(state)
        state = self.settings.value("splitter_v")
        if state:
            self.vsplit.restoreState(state)
        fp = self.file_panel
        fp.chk_recursive.setChecked(bool(self.settings.value("opt_recursive", False, type=bool)))
        fp.chk_dirs.setChecked(bool(self.settings.value("opt_dirs", False, type=bool)))
        fp.chk_hidden.setChecked(bool(self.settings.value("opt_hidden", False, type=bool)))

    def _restore_last_rules(self) -> None:
        """上次关窗口时的规则组自动恢复，省得每次重配。"""
        data = load_json(LAST_RULES_PATH(), [])
        if not isinstance(data, list) or not data:
            return
        try:
            rules = [Rule.from_dict(d) for d in data]
        except Exception:
            return
        if rules:
            self.rule_panel.set_rules(rules)

    def closeEvent(self, event) -> None:
        save_json(LAST_RULES_PATH(),
                  [r.to_dict() for r in self.rule_panel.rules()])
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_h", self.hsplit.saveState())
        self.settings.setValue("splitter_v", self.vsplit.saveState())
        super().closeEvent(event)

    # ---------------------------------------------------------- 拖放
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if p and os.path.isdir(p):
                self.dir_panel.select_path(p)
                self.open_dir(p)
                break
            if p and os.path.isfile(p):
                d = os.path.dirname(p)
                self.dir_panel.select_path(d)
                self.open_dir(d)
                break
