"""纯字符串处理工具：不依赖 Qt，可独立单元测试。

设计原则：所有改名操作都以 **文件名（含扩展名）** 为输入输出，
内部按 scope 拆成 (stem, ext) 分别处理，避免出现
"把扩展名里的 abc 也替换掉" 这类事故。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime

# ---------------------------------------------------------------- 名称拆分


def split_name(name: str) -> tuple[str, str]:
    """把文件名拆成 (主名, 扩展名)。扩展名不含点，没有扩展名则返回空串。

    'a.b.txt' -> ('a.b', 'txt')
    '.gitignore' -> ('.gitignore', '')
    'README' -> ('README', '')
    'a.' -> ('a.', '')
    """
    i = name.rfind(".")
    if i <= 0:
        return name, ""
    ext = name[i + 1:]
    if not ext:
        return name, ""
    return name[:i], ext


def join_name(stem: str, ext: str) -> str:
    return f"{stem}.{ext}" if ext else stem


# ---------------------------------------------------------------- 大小写

def to_upper(s: str) -> str:
    return s.upper()


def to_lower(s: str) -> str:
    return s.lower()


_WORD_START = re.compile(r"(^|[^0-9A-Za-z])([a-z])")


def to_title(s: str) -> str:
    """每个单词首字母大写：'my cool file' -> 'My Cool File'。"""
    return _WORD_START.sub(lambda m: m.group(1) + m.group(2).upper(), s)


def to_capitalize(s: str) -> str:
    """只有首字母大写，其余不变。"""
    for idx, ch in enumerate(s):
        if ch.isalpha():
            return s[:idx] + ch.upper() + s[idx + 1:]
    return s


# ---------------------------------------------------------------- 全角/半角

def _is_punct(ch: str) -> bool:
    if ch.isascii():
        return not (ch.isalnum() or ch.isspace())
    return unicodedata.category(ch).startswith("P")


def _accept(ch: str, scope: str) -> bool:
    """scope: all / alnum / punct —— 决定哪些字符参与全半角转换。"""
    if scope == "alnum":
        return ch.isalnum()
    if scope == "punct":
        return _is_punct(ch)
    return True


def to_halfwidth(s: str, scope: str = "all") -> str:
    """全角转半角。全角空格一并转普通空格（scope=all 时）。"""
    out = []
    for ch in s:
        o = ord(ch)
        if o == 0x3000:
            out.append(" " if scope == "all" else ch)
            continue
        if 0xFF01 <= o <= 0xFF5E and _accept(ch, scope):
            out.append(chr(o - 0xFEE0))
            continue
        out.append(ch)
    return "".join(out)


def to_fullwidth(s: str, scope: str = "all") -> str:
    """半角转全角（只转可打印 ASCII 与普通空格）。"""
    out = []
    for ch in s:
        o = ord(ch)
        if ch == " " and scope == "all":
            out.append("\u3000")
            continue
        if 0x21 <= o <= 0x7E and _accept(ch, scope):
            out.append(chr(o + 0xFEE0))
            continue
        out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------- 空格/重音

_SPACES = re.compile(r"[ \t\u00a0\u3000]{2,}")


def collapse_spaces(s: str) -> str:
    """连续两个及以上空格 → 一个。全角空格与不换行空格也算空格。"""
    s = s.replace("\u00a0", " ").replace("\u3000", " ")
    return _SPACES.sub(" ", s)


def strip_spaces(s: str) -> str:
    return s.strip(" \t\u00a0\u3000")


def remove_all_spaces(s: str) -> str:
    return re.sub(r"[ \t\u00a0\u3000]", "", s)


def strip_accents(s: str) -> str:
    """去掉拉丁字母的重音符号：á→a, o-double-acute→o。中文不受影响。"""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


# ---------------------------------------------------------------- 自然排序

_NUM_SPLIT = re.compile(r"(\d+)")


def natural_key(s: str):
    """自然排序键：'img2' < 'img10'。"""
    parts = []
    for tok in _NUM_SPLIT.split(s):
        if tok.isdigit():
            parts.append((0, int(tok), ""))
        else:
            parts.append((1, 0, tok.lower()))
    return parts


# ---------------------------------------------------------------- 日期格式

_FRIENDLY = [
    ("YYYY", "%Y"), ("YY", "%y"),
    ("MM", "%m"), ("DD", "%d"),
    ("hh", "%H"), ("HH", "%H"),
    ("mm", "%M"), ("ss", "%S"),
]


def normalize_date_format(fmt: str) -> str:
    """把 YYYY-MM-DD 这类"人话"格式转成 strftime；含 % 的原样返回。"""
    if not fmt:
        return "%Y%m%d"
    if "%" in fmt:
        return fmt
    out = fmt
    for token, code in _FRIENDLY:
        out = out.replace(token, code)
    return out


def format_now(fmt: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    try:
        return now.strftime(normalize_date_format(fmt))
    except Exception:
        return now.strftime("%Y%m%d")


# ---------------------------------------------------------------- 序号

def format_seq(index: int, start: int = 1, step: int = 1, digits: int = 0) -> str:
    """index 为 0 基序号；digits<=0 表示不补零。"""
    n = start + index * step
    if digits and digits > 0:
        return str(n).zfill(digits)
    return str(n)


# ---------------------------------------------------------------- 占位符

@dataclass
class TokenEnv:
    """占位符展开的上下文。"""
    index: int = 0
    seq_start: int = 1
    seq_step: int = 1
    seq_digits: int = 3
    date_format: str = "%Y%m%d"
    now: datetime | None = None


_TOKEN_RE = re.compile(r"\{(n|date|time|now|name|ext|orig|parent)\}")


def expand_tokens(text: str, env: TokenEnv, current_name: str = "",
                  orig_name: str = "", parent: str = "") -> str:
    """展开 {n} {date} {name} {ext} {orig} {parent}。未知占位符原样保留。"""
    now = env.now or datetime.now()

    def rep(m):
        tok = m.group(1)
        if tok == "n":
            return format_seq(env.index, env.seq_start, env.seq_step, env.seq_digits)
        if tok in ("date", "time", "now"):
            return format_now(env.date_format, now)
        stem, ext = split_name(current_name)
        if tok == "name":
            return stem
        if tok == "ext":
            return ext
        if tok == "orig":
            return orig_name
        if tok == "parent":
            return parent
        return m.group(0)

    return _TOKEN_RE.sub(rep, text)


TOKEN_HELP = ("{n} 序号 · {date} 时间 · {name} 当前主名 · {ext} 扩展名 · "
              "{orig} 原文件名 · {parent} 上级文件夹名")


def has_token(text: str, *tokens: str) -> bool:
    return any("{%s}" % t in text for t in tokens)
