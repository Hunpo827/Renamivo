"""带日志的两阶段改名执行器。

为什么分两步：
  Windows 文件系统不区分大小写，`a.txt -> A.txt` 这类"只改大小写"的重命名
  直接用 os.rename 会失败；此外 a->b、b->a 这种环形交换也必须先落到临时名。
所以所有改名统一走：源 → 临时名 → 目标名。

为什么写日志：
  第二阶段中途断电/崩溃时，磁盘上会留下一堆 .~brn_xxx 临时文件。
  journal.json 记录了每个文件的 src/dst/tmp 和当前状态，程序下次启动时
  可以据此把现场恢复成改名前的样子。
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from ..i18n import tr
from .config import JOURNAL_PATH

_MAX_PATH = 240


def long_path(p: str) -> str:
    r"""超长路径加 \\?\ 前缀，绕过 260 字符限制。"""
    if os.name != "nt":
        return p
    ap = os.path.abspath(p)
    if ap.startswith("\\\\?\\"):
        return ap
    if len(ap) < _MAX_PATH:
        return ap
    if ap.startswith("\\\\"):
        return "\\\\?\\UNC\\" + ap[2:]
    return "\\\\?\\" + ap


@dataclass
class RenamePair:
    src: str
    dst: str
    tmp: str = ""
    state: str = "pending"      # pending / staged / done


@dataclass
class ExecResult:
    ok: bool = True
    done: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)
    rolled_back: bool = False
    message: str = ""

    @property
    def pairs_done(self) -> int:
        return self.done


# ---------------------------------------------------------------- 日志

def _new_journal(pairs: list[RenamePair]) -> dict:
    jid = uuid.uuid4().hex[:8]
    for i, p in enumerate(pairs):
        d = os.path.dirname(p.src)
        p.tmp = os.path.join(d, f".~brn_{jid}_{i}")
    return {
        "id": jid,
        "started": datetime.now().isoformat(timespec="seconds"),
        "phase": "prepared",
        "pairs": [{"src": p.src, "dst": p.dst, "tmp": p.tmp, "state": "pending"}
                  for p in pairs],
    }


def _save_journal(journal: dict) -> None:
    path = JOURNAL_PATH()
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(journal, f, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        pass


def _clear_journal() -> None:
    try:
        JOURNAL_PATH().unlink(missing_ok=True)
    except OSError:
        pass


def pending_journal() -> dict | None:
    """启动时调用：如果有未完成的改名日志，返回它。"""
    try:
        with open(JOURNAL_PATH(), "r", encoding="utf-8") as f:
            j = json.load(f)
        if j.get("phase") in ("prepared", "staged"):
            return j
    except Exception:
        pass
    return None


def recover(journal: dict) -> tuple[bool, str]:
    """把未完成的改名回滚到原状。"""
    items = journal.get("pairs", [])
    errors = 0
    for it in reversed(items):
        src, tmp_, state = it["src"], it.get("tmp", ""), it.get("state", "pending")
        try:
            if state == "done" and os.path.exists(long_path(it["dst"])):
                os.rename(long_path(it["dst"]), long_path(src))
            elif state == "staged" and tmp_ and os.path.exists(long_path(tmp_)):
                os.rename(long_path(tmp_), long_path(src))
        except OSError:
            errors += 1
    if errors:
        return False, tr("恢复完成，但有 {n} 个文件需要手工处理", n=errors)
    _clear_journal()
    return True, tr("已恢复到改名前的状态")


# ---------------------------------------------------------------- 执行

def execute(pairs: list[RenamePair], progress=None) -> ExecResult:
    """执行改名。任何一步失败都会把已完成的改名回滚。"""
    pairs = [p for p in pairs if os.path.abspath(p.src) != os.path.abspath(p.dst)]
    result = ExecResult()
    if not pairs:
        result.message = tr("没有需要改名的文件")
        return result

    # 动手前的最后一次检查：目标是不是已经被占用了
    src_keys = {os.path.abspath(p.src).casefold() for p in pairs}
    for p in pairs:
        if os.path.exists(long_path(p.dst)):
            if os.path.abspath(p.dst).casefold() not in src_keys:
                result.ok = False
                result.message = tr("目标已存在: {name}", name=os.path.basename(p.dst))
                return result

    journal = _new_journal(pairs)
    _save_journal(journal)

    def rollback(reason: str) -> ExecResult:
        _save_journal(journal)
        ok, _msg = recover(journal)
        r = ExecResult(ok=False, done=result.done, failed=result.failed,
                       rolled_back=True, message=reason)
        return r

    total = len(pairs)
    # ---- 第一阶段：源 → 临时名
    for i, p in enumerate(pairs):
        try:
            if not os.path.exists(long_path(p.src)):
                result.failed.append((p.src, tr("源文件不存在")))
                return rollback(tr("文件在执行前已被移走，已回滚"))
            os.rename(long_path(p.src), long_path(p.tmp))
            journal["pairs"][i]["state"] = "staged"
            _save_journal(journal)
        except OSError as exc:
            result.failed.append((p.src, str(exc)))
            return rollback(tr("改名失败：{name} — {err}", name=os.path.basename(p.src), err=str(exc.strerror or exc)))
        if progress and i % 20 == 0:
            progress(i, total)
    journal["phase"] = "staged"
    _save_journal(journal)

    # ---- 第二阶段：临时名 → 目标名
    for i, p in enumerate(pairs):
        try:
            os.rename(long_path(p.tmp), long_path(p.dst))
            journal["pairs"][i]["state"] = "done"
            result.done += 1
            if i % 20 == 0:
                _save_journal(journal)
                if progress:
                    progress(i, total)
        except OSError as exc:
            result.failed.append((p.dst, str(exc)))
            return rollback(tr("写入目标名失败：{name} — {err}", name=os.path.basename(p.dst), err=str(exc.strerror or exc)))

    journal["phase"] = "committed"
    _save_journal(journal)
    _clear_journal()
    if progress:
        progress(total, total)
    result.ok = True
    result.message = tr("已改名 {n} 个文件", n=result.done)
    return result


def undo(records: list[dict]) -> ExecResult:
    """撤销：records 为 [{'old': 绝对路径, 'new': 绝对路径}, ...]"""
    pairs = [RenamePair(src=r["new"], dst=r["old"]) for r in reversed(records)]
    for p in pairs:
        if not os.path.exists(long_path(p.src)):
            return ExecResult(ok=False, message=tr("找不到 {name}，无法撤销", name=os.path.basename(p.src)))
        if os.path.exists(long_path(p.dst)):
            return ExecResult(ok=False, message=tr("原名称已被占用：{name}", name=os.path.basename(p.dst)))
    return execute(pairs)
