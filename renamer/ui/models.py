"""文件列表的表格模型与筛选代理。"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor, QFont

from ..core import naming as N
from ..i18n import tr
from ..core.scanner import FileItem
from ..core.validator import (STATUS_CONFLICT, STATUS_INVALID, STATUS_LABELS,
                              STATUS_OK, STATUS_UNCHANGED, Problem)

COL_CHECK = 0
COL_NAME = 1
COL_DIR = 2
COL_NEW = 3
COL_TYPE = 4
COL_SIZE = 5
COL_MTIME = 6
COL_STATUS = 7

COLUMN_COUNT = 8


def headers() -> list[str]:
    """表头按当前语言生成（语言切换后重建窗口即可生效）。"""
    return ["", tr("名称"), tr("子目录"), tr("新名称"),
            tr("类型"), tr("大小"), tr("修改时间"), tr("状态")]

ROLE_SORT = Qt.UserRole + 1
ROLE_TIP = Qt.UserRole + 2

COLOR_OK = QColor("#1a7f37")
COLOR_DIM = QColor("#8b949e")
COLOR_BAD = QColor("#cf222e")


def human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    for unit in ("KB", "MB", "GB", "TB"):
        n /= 1024.0
        if n < 1024:
            return f"{n:.1f} {unit}"
    return f"{n:.1f} PB"


@dataclass
class Row:
    item: FileItem
    new_name: str = ""
    status: str = STATUS_OK
    msg: str = ""
    checked: bool = True

    @property
    def changed(self) -> bool:
        return self.new_name != self.item.name

    @property
    def effective_status(self) -> str:
        if not self.changed:
            return STATUS_UNCHANGED
        return self.status


class FileTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows: list[Row] = []
        self._bold = QFont()
        self._bold.setBold(True)

    # ---- Qt 接口
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else COLUMN_COUNT

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None
        if role == Qt.DisplayRole:
            return headers()[section]
        if role == Qt.TextAlignmentRole:
            if section in (COL_SIZE,):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)
        return None

    def flags(self, index):
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == COL_CHECK:
            base |= Qt.ItemIsUserCheckable
        return base

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        col = index.column()
        it = row.item

        if role == Qt.CheckStateRole and col == COL_CHECK:
            return Qt.Checked if row.checked else Qt.Unchecked

        if role == Qt.DisplayRole:
            if col == COL_CHECK:
                return ""
            if col == COL_NAME:
                return it.name
            if col == COL_DIR:
                return it.reldir
            if col == COL_NEW:
                return row.new_name
            if col == COL_TYPE:
                if it.is_dir:
                    return tr("文件夹")
                return it.ext.upper() or "—"
            if col == COL_SIZE:
                return "—" if it.is_dir else human_size(it.size)
            if col == COL_MTIME:
                import datetime
                return datetime.datetime.fromtimestamp(it.mtime).strftime("%Y-%m-%d %H:%M")
            if col == COL_STATUS:
                st = row.effective_status
                if not row.checked:
                    return tr("不处理")
                label = tr(STATUS_LABELS.get(st, st))
                if st in (STATUS_CONFLICT, STATUS_INVALID) and row.msg:
                    return f"{label}·{row.msg}"
                return label
            return ""

        if role == Qt.ForegroundRole:
            if col == COL_NEW:
                st = row.effective_status
                if st == STATUS_UNCHANGED:
                    return COLOR_DIM
                if st in (STATUS_CONFLICT, STATUS_INVALID):
                    return COLOR_BAD
                return COLOR_OK
            if col == COL_STATUS:
                if not row.checked:
                    return COLOR_DIM
                st = row.effective_status
                if st in (STATUS_CONFLICT, STATUS_INVALID):
                    return COLOR_BAD
                if st == STATUS_UNCHANGED:
                    return COLOR_DIM
                return COLOR_OK
            if col == COL_NAME and row.checked and row.changed:
                return QColor("#0b57d0")
            return None

        if role == Qt.FontRole and col == COL_NEW and row.checked and row.changed:
            return self._bold

        if role == ROLE_TIP:
            if col == COL_STATUS and row.msg:
                return row.msg
            if col == COL_NAME:
                return it.path
            return None

        if role == ROLE_SORT:
            if col in (COL_NAME, COL_NEW):
                return N.natural_key(row.new_name if col == COL_NEW else it.name)
            if col == COL_SIZE:
                return it.size
            if col == COL_MTIME:
                return it.mtime
            if col == COL_TYPE:
                return (it.ext.casefold(), N.natural_key(it.name))
            if col == COL_DIR:
                return N.natural_key(it.reldir)
            if col == COL_STATUS:
                return row.effective_status
            return None

        return None

    def setData(self, index, value, role=Qt.EditRole) -> bool:
        if role == Qt.CheckStateRole and index.column() == COL_CHECK:
            row = self.rows[index.row()]
            row.checked = Qt.CheckState(value) == Qt.Checked
            self.dataChanged.emit(self.index(index.row(), 0),
                                  self.index(index.row(), COL_STATUS))
            return True
        return False

    # ---- 自有接口
    def set_items(self, items: list[FileItem]) -> None:
        self.beginResetModel()
        self.rows = [Row(item=it, new_name=it.name) for it in items]
        self.endResetModel()

    def apply_preview(self, names: list[str], problems: list[Problem]) -> None:
        if not self.rows:
            return
        for row, name, prob in zip(self.rows, names, problems):
            row.new_name = name
            row.status = prob.status
            row.msg = prob.message
        top = self.index(0, 0)
        bottom = self.index(len(self.rows) - 1, COLUMN_COUNT - 1)
        self.dataChanged.emit(top, bottom)

    def set_all_checked(self, checked: bool) -> None:
        if not self.rows:
            return
        for row in self.rows:
            row.checked = checked
        self.dataChanged.emit(self.index(0, 0),
                              self.index(len(self.rows) - 1, COLUMN_COUNT - 1))

    def invert_checked(self) -> None:
        if not self.rows:
            return
        for row in self.rows:
            row.checked = not row.checked
        self.dataChanged.emit(self.index(0, 0),
                              self.index(len(self.rows) - 1, COLUMN_COUNT - 1))

    def counts(self) -> tuple[int, int, int, int]:
        """(总数, 勾选数, 勾选且将变更, 勾选但有冲突)"""
        total = len(self.rows)
        checked = sum(1 for r in self.rows if r.checked)
        will = sum(1 for r in self.rows if r.checked and r.changed
                   and r.status in (STATUS_OK,))
        bad = sum(1 for r in self.rows if r.checked and r.changed
                  and r.status in (STATUS_CONFLICT, STATUS_INVALID))
        return total, checked, will, bad


class FileFilterProxy(QSortFilterProxyModel):
    """支持：文字搜索（含正则）、类型筛选、只看变更。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search = ""
        self.search_regex = False
        self.ext_filter: str | None = None     # None = 全部
        self.only_changed = False
        self.only_checked = False
        self._rx = None

    def set_search(self, text: str) -> None:
        self.search = (text or "").strip()
        self._rx = None
        if self.search and self.search_regex:
            try:
                self._rx = re.compile(self.search, re.IGNORECASE)
            except re.error:
                self._rx = None
        self.invalidateFilter()

    def set_ext_filter(self, ext: str | None) -> None:
        self.ext_filter = ext
        self.invalidateFilter()

    def set_only_changed(self, v: bool) -> None:
        self.only_changed = v
        self.invalidateFilter()

    def set_only_checked(self, v: bool) -> None:
        self.only_checked = v
        self.invalidateFilter()

    def _match_text(self, row: Row) -> bool:
        if not self.search:
            return True
        if self._rx is not None:
            return bool(self._rx.search(row.item.name) or self._rx.search(row.new_name)
                        or self._rx.search(row.item.reldir))
        s = self.search.casefold()
        return (s in row.item.name.casefold() or s in row.new_name.casefold()
                or s in row.item.reldir.casefold())

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None or source_row >= len(model.rows):
            return False
        row = model.rows[source_row]
        if self.only_changed and not row.changed:
            return False
        if self.only_checked and not row.checked:
            return False
        if self.ext_filter is not None:
            if self.ext_filter == "":
                if row.item.ext:
                    return False
            elif row.item.ext.casefold() != self.ext_filter.casefold():
                return False
        return self._match_text(row)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        model = self.sourceModel()
        a = model.data(left, ROLE_SORT) if left.isValid() else None
        b = model.data(right, ROLE_SORT) if right.isValid() else None
        if a is None or b is None:
            return super().lessThan(left, right)
        try:
            return a < b
        except TypeError:
            return str(a) < str(b)
