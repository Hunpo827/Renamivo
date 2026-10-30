"""目录扫描。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..i18n import tr
from . import naming as N

FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

TMP_PREFIX = ".~brn_"


@dataclass
class FileItem:
    path: str            # 绝对路径
    name: str            # 文件名（含扩展名）
    stem: str
    ext: str
    size: int
    mtime: float
    is_dir: bool
    reldir: str = ""     # 相对根目录的子目录（递归时），根目录为空串

    @property
    def dir_path(self) -> str:
        return os.path.dirname(self.path)


def _is_hidden(entry) -> bool:
    try:
        st = entry.stat(follow_symlinks=False)
    except OSError:
        return False
    attr = getattr(st, "st_file_attributes", 0)
    return bool(attr & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM))


def make_item(path: str, entry, reldir: str = "") -> FileItem | None:
    try:
        st = entry.stat(follow_symlinks=False)
    except OSError:
        return None
    name = entry.name
    stem, ext = N.split_name(name)
    return FileItem(
        path=path,
        name=name,
        stem=stem,
        ext=ext,
        size=st.st_size,
        mtime=st.st_mtime,
        is_dir=entry.is_dir(follow_symlinks=False),
        reldir=reldir,
    )


def scan(root: str, *, recursive: bool = False, include_dirs: bool = False,
         include_hidden: bool = False, limit: int = 30000
         ) -> tuple[list[FileItem], list[str]]:
    """扫描目录，返回 (项目列表, 警告列表)。

    root 不存在/不可读时返回空列表和一条警告，不抛异常。
    """
    items: list[FileItem] = []
    warnings: list[str] = []

    if not root or not os.path.isdir(root):
        return items, [tr("目录不存在或不可访问")]

    def walk(dir_path: str, reldir: str) -> None:
        try:
            with os.scandir(dir_path) as it:
                entries = list(it)
        except OSError as exc:
            warnings.append(tr("无法读取 {path}：{err}", path=dir_path, err=str(exc.strerror or exc)))
            return

        for entry in entries:
            if len(items) >= limit:
                warnings.append(tr("文件数超过 {n}，只显示前 {n} 个", n=limit))
                return
            if entry.name.startswith(TMP_PREFIX):
                continue
            if not include_hidden and _is_hidden(entry):
                continue
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if is_dir:
                if include_dirs:
                    it = make_item(entry.path, entry, reldir)
                    if it:
                        items.append(it)
                if recursive:
                    sub = f"{reldir}/{entry.name}" if reldir else entry.name
                    walk(entry.path, sub)
            else:
                if not entry.is_file(follow_symlinks=False):
                    continue
                it = make_item(entry.path, entry, reldir)
                if it:
                    items.append(it)

    walk(root, "")

    # 资源管理器习惯：文件夹在前，其余按自然顺序
    items.sort(key=lambda x: (not x.is_dir, N.natural_key(x.reldir), N.natural_key(x.name)))
    return items, warnings
