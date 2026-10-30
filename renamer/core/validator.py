"""改名结果校验：非法字符、保留名、重复目标、目标已存在。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..i18n import tr

INVALID_CHARS = '<>:"/\\|?*'
RESERVED = {"CON", "PRN", "AUX", "NUL"} \
    | {f"COM{i}" for i in range(1, 10)} \
    | {f"LPT{i}" for i in range(1, 10)}

STATUS_OK = "ok"
STATUS_UNCHANGED = "unchanged"
STATUS_CONFLICT = "conflict"
STATUS_INVALID = "invalid"

STATUS_LABELS = {
    STATUS_OK: "将变更",
    STATUS_UNCHANGED: "无变化",
    STATUS_CONFLICT: "冲突",
    STATUS_INVALID: "非法",
}


@dataclass
class Problem:
    status: str
    message: str = ""


def validate_name(name: str) -> Problem | None:
    """返回问题描述；None 表示可用。"""
    if not name or not name.strip():
        return Problem(STATUS_INVALID, tr("文件名为空"))
    bad = [c for c in INVALID_CHARS if c in name]
    if bad:
        return Problem(STATUS_INVALID, tr("含非法字符 {chars}", chars=" ".join(bad)))
    if any(ord(c) < 32 for c in name):
        return Problem(STATUS_INVALID, tr("含控制字符"))
    if name != name.rstrip(" ."):
        return Problem(STATUS_INVALID, tr("结尾不能是空格或点"))
    if name.startswith(" "):
        return Problem(STATUS_INVALID, tr("不能以空格开头"))
    if len(name) > 255:
        return Problem(STATUS_INVALID, tr("文件名过长（超过 255 字符）"))
    stem = name.split(".", 1)[0].rstrip(" .").upper()
    if stem in RESERVED:
        return Problem(STATUS_INVALID, tr("{stem} 是系统保留名", stem=stem))
    return None


def evaluate(items, new_names, disk_names=None) -> list[Problem]:
    """items: FileItem 列表；new_names: 与之等长的新文件名列表。

    disk_names: {目录: {已存在的文件名(小写)}}。不同目录里的同名文件互不影响。
    批内自身改名腾出的位置不算冲突。
    """
    n = len(items)
    problems: list[Problem] = [Problem(STATUS_OK) for _ in range(n)]

    if disk_names is None:
        disk_names = {}
    if isinstance(disk_names, set):
        disk_names = {"": disk_names}

    def _dir(it) -> str:
        return (getattr(it, "dir_path", "") or "").casefold()

    # 1. 单个名称合法性
    for i, new in enumerate(new_names):
        p = validate_name(new)
        if p:
            problems[i] = p

    # 2. 同一目录内重名（Windows 不区分大小写）
    seen: dict[tuple[str, str], int] = {}
    dup: set[int] = set()
    for i, new in enumerate(new_names):
        if problems[i].status == STATUS_INVALID:
            continue
        key = (_dir(items[i]), new.casefold())
        if key in seen:
            dup.add(i)
            dup.add(seen[key])
        else:
            seen[key] = i
    for i in dup:
        problems[i] = Problem(STATUS_CONFLICT, tr("与本批次其他文件重名"))

    # 3. 目标名已存在于磁盘，且不是本批次里会腾出来的文件
    src_by_dir: dict[str, set[str]] = {}
    for it in items:
        src_by_dir.setdefault(_dir(it), set()).add(it.name.casefold())

    for i, it in enumerate(items):
        if problems[i].status != STATUS_OK:
            continue
        d = _dir(it)
        key = new_names[i].casefold()
        if key == it.name.casefold():
            problems[i] = Problem(STATUS_UNCHANGED)
            continue
        existing = disk_names.get(d)
        if existing is None:
            continue
        sources = src_by_dir.get(d, set())
        if key not in existing:
            continue
        if key not in sources:
            problems[i] = Problem(STATUS_CONFLICT, tr("目标文件名已存在"))
        else:
            # 目标是本批次里另一个文件；如果它自己不会被改名，就是真冲突
            owners = [j for j, s in enumerate(items)
                      if _dir(s) == d and s.name.casefold() == key]
            if owners and all(problems[j].status == STATUS_UNCHANGED for j in owners):
                problems[i] = Problem(STATUS_CONFLICT, tr("目标文件名已被占用"))

    return problems
