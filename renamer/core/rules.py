"""规则引擎：把一组规则按顺序作用在文件名上。纯逻辑，不依赖 Qt。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..i18n import join_list, tr
from . import naming as N

RULE_TYPES = ("add", "delete", "replace", "convert")

RULE_LABELS = {
    "add": "添加",
    "delete": "删除",
    "replace": "替换",
    "convert": "转换",
}

RULE_DEFAULTS: dict[str, dict[str, Any]] = {
    "add": {
        "position": "prefix",       # prefix / stem_suffix / ext_suffix
        "content": "",
        "seq_start": 1,
        "seq_step": 1,
        "seq_digits": 3,
        "date_format": "YYYYMMDD",
    },
    "delete": {
        "scope": "stem",            # stem / ext / full
        "mode": "text",             # text / regex / position / brackets
        "text": "",
        "ignore_case": False,
        "first_only": False,
        "pattern": "",
        "pos_from": "head",         # head / tail
        "count": 1,
        "bracket": "()",
        "keep_bracket": False,
        "trim_after": True,
    },
    "replace": {
        "scope": "stem",
        "find": "",
        "repl": "",
        "use_regex": False,
        "ignore_case": False,
        "first_only": False,
    },
    "convert": {
        "scope": "stem",
        "case": "none",             # none / upper / lower / title / capitalize
        "width": "none",            # none / half / full
        "width_scope": "all",       # all / alnum / punct
        "accents": False,
        "trim": False,
        "collapse": False,
        "nospace": False,
        "set_ext": "",
    },
}

POSITION_LABELS = {
    "prefix": "文件名开头",
    "stem_suffix": "文件名结尾（扩展名前）",
    "ext_suffix": "扩展名之后",
}
SCOPE_LABELS = {"stem": "文件名", "ext": "扩展名", "full": "整个文件名"}
CASE_LABELS = {
    "none": "不变", "upper": "全部大写", "lower": "全部小写",
    "title": "每个单词首字母大写", "capitalize": "仅首字母大写",
}
WIDTH_LABELS = {"none": "不变", "half": "全角 → 半角", "full": "半角 → 全角"}


@dataclass
class Rule:
    type: str
    enabled: bool = True
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        base = dict(RULE_DEFAULTS.get(self.type, {}))
        base.update(self.params or {})
        self.params = base

    # ---- 序列化（预设保存用）
    def to_dict(self) -> dict:
        return {"type": self.type, "enabled": self.enabled, "params": dict(self.params)}

    @classmethod
    def from_dict(cls, d: dict) -> "Rule":
        return cls(type=d["type"], enabled=d.get("enabled", True),
                   params=d.get("params", {}))

    def describe(self) -> str:
        p = self.params
        if self.type == "add":
            pos = tr(POSITION_LABELS.get(p["position"], p["position"]))
            txt = p["content"] or tr("(空)")
            return tr("{pos}添加：{txt}", pos=pos, txt=txt)

        if self.type == "delete":
            sc = tr(SCOPE_LABELS.get(p["scope"], p["scope"]))
            if p["mode"] == "text":
                return tr("从{sc}删除文字：{txt}", sc=sc, txt=p["text"] or tr("(空)"))
            if p["mode"] == "regex":
                return tr("从{sc}删除正则：{pat}", sc=sc, pat=p["pattern"] or tr("(空)"))
            if p["mode"] == "position":
                where = tr("开头") if p["pos_from"] == "head" else tr("结尾")
                return tr("从{sc}{where}删除 {n} 个字符", sc=sc, where=where,
                          n=p["count"])
            kind = tr("括号内内容") if p.get("keep_bracket") else tr("括号及其内容")
            return tr("删除{sc}中的 {br} {kind}", sc=sc, br=p["bracket"], kind=kind)

        if self.type == "replace":
            sc = tr(SCOPE_LABELS.get(p["scope"], p["scope"]))
            f = p["find"] or tr("(空)")
            r = p["repl"] or tr("(空)")
            regex = tr("（正则）") if p["use_regex"] else ""
            return tr("{sc}中 {f} → {r}{regex}", sc=sc, f=f, r=r, regex=regex)

        if self.type == "convert":
            bits = []
            if p["case"] != "none":
                bits.append(tr(CASE_LABELS[p["case"]]))
            if p["width"] != "none":
                bits.append(tr(WIDTH_LABELS[p["width"]]))
            if p["accents"]:
                bits.append(tr("去重音"))
            if p["trim"]:
                bits.append(tr("去首尾空格"))
            if p["collapse"]:
                bits.append(tr("合并连续空格"))
            if p["nospace"]:
                bits.append(tr("删除所有空格"))
            if p["set_ext"]:
                bits.append(tr("扩展名改为 .{ext}", ext=p["set_ext"]))
            sc = tr(SCOPE_LABELS.get(p["scope"], p["scope"]))
            ops = join_list(bits) if bits else tr("(未选择操作)")
            return tr("{sc}：{ops}", sc=sc, ops=ops)

        return self.type


@dataclass
class ApplyCtx:
    """一次改名计算里对所有文件都一样的上下文。"""
    now: datetime
    parent: str = ""


_BRACKETS = {
    "()": ("(", ")"),
    "[]": ("[", "]"),
    "{}": ("{", "}"),
    "<>": ("<", ">"),
    "（）": ("（", "）"),
    "【】": ("【", "】"),
}


def _brace_to_backref(s: str) -> str:
    """允许用 $1 / ${1} 写反向引用（用户习惯），转成 Python 的 \\1。"""
    return re.sub(r"\$\{?(\d+)\}?", r"\\\1", s)


def _sub_in(scope: str, name: str, fn) -> str:
    """把 fn 应用到 scope 指定的那一段上。"""
    stem, ext = N.split_name(name)
    if scope == "ext":
        return N.join_name(stem, fn(ext))
    if scope == "full":
        return fn(name)
    return N.join_name(fn(stem), ext)


def _apply_add(p: dict, name: str, index: int, ctx: ApplyCtx) -> str:
    env = N.TokenEnv(index=index, seq_start=int(p["seq_start"]),
                     seq_step=int(p["seq_step"]), seq_digits=int(p["seq_digits"]),
                     date_format=p["date_format"], now=ctx.now)
    stem, ext = N.split_name(name)
    txt = N.expand_tokens(p["content"], env, current_name=name,
                          orig_name=name, parent=ctx.parent)
    if not txt:
        return name
    pos = p["position"]
    if pos == "prefix":
        return txt + name
    if pos == "stem_suffix":
        return N.join_name(stem + txt, ext)
    return name + txt


def _apply_delete(p: dict, name: str, index: int, ctx: ApplyCtx) -> str:
    out = _apply_delete_raw(p, name)
    if p.get("trim_after", True):
        out = _sub_in(p["scope"], out, N.strip_spaces)
    return out


def _apply_delete_raw(p: dict, name: str) -> str:
    mode = p["mode"]
    flags = re.IGNORECASE if p["ignore_case"] else 0
    limit = 1 if p["first_only"] else 0

    if mode == "text":
        needle = p["text"]
        if not needle:
            return name

        def fn(s: str) -> str:
            if p["ignore_case"]:
                return re.sub(re.escape(needle), "", s, count=limit, flags=flags)
            return s.replace(needle, "", limit) if limit else s.replace(needle, "")

        return _sub_in(p["scope"], name, fn)

    if mode == "regex":
        pat = p["pattern"]
        if not pat:
            return name
        try:
            rx = re.compile(pat, flags)
        except re.error:
            return name
        return _sub_in(p["scope"], name, lambda s: rx.sub("", s, count=limit))

    if mode == "position":
        n = max(0, int(p["count"]))
        if n == 0:
            return name
        if p["pos_from"] == "head":
            return _sub_in(p["scope"], name, lambda s: s[n:])
        return _sub_in(p["scope"], name, lambda s: s[:-n] if len(s) > n else "")

    if mode == "brackets":
        o, c = _BRACKETS.get(p["bracket"], ("(", ")"))
        esc_o, esc_c = re.escape(o), re.escape(c)
        inner = f"[^{esc_o}{esc_c}]*"
        if p["keep_bracket"]:
            rx = re.compile(esc_o + "(" + inner + ")" + esc_c)
            return _sub_in(p["scope"], name, lambda s: rx.sub(o + c, s))
        rx = re.compile(esc_o + inner + esc_c)
        return _sub_in(p["scope"], name, lambda s: rx.sub("", s))

    return name


def _apply_replace(p: dict, name: str, index: int, ctx: ApplyCtx) -> str:
    find = p["find"]
    if not find:
        return name
    repl = p["repl"]
    flags = re.IGNORECASE if p["ignore_case"] else 0
    limit = 1 if p["first_only"] else 0

    if p["use_regex"]:
        try:
            rx = re.compile(find, flags)
        except re.error:
            return name
        return _sub_in(p["scope"], name, lambda s: rx.sub(_brace_to_backref(repl), s, count=limit))

    def fn(s: str) -> str:
        if p["ignore_case"]:
            return re.sub(re.escape(find), lambda _m: repl, s, count=limit, flags=flags)
        return s.replace(find, repl, limit) if limit else s.replace(find, repl)

    return _sub_in(p["scope"], name, fn)


def _apply_convert(p: dict, name: str, index: int, ctx: ApplyCtx) -> str:
    def convert_text(s: str) -> str:
        if not s:
            return s
        if p["width"] == "half":
            s = N.to_halfwidth(s, p["width_scope"])
        elif p["width"] == "full":
            s = N.to_fullwidth(s, p["width_scope"])
        case = p["case"]
        if case == "upper":
            s = N.to_upper(s)
        elif case == "lower":
            s = N.to_lower(s)
        elif case == "title":
            s = N.to_title(s)
        elif case == "capitalize":
            s = N.to_capitalize(s)
        if p["accents"]:
            s = N.strip_accents(s)
        if p["trim"]:
            s = N.strip_spaces(s)
        if p["collapse"]:
            s = N.collapse_spaces(s)
        if p["nospace"]:
            s = N.remove_all_spaces(s)
        return s

    out = _sub_in(p["scope"], name, convert_text)

    set_ext = (p["set_ext"] or "").strip().lstrip(".")
    if set_ext:
        stem, _old = N.split_name(out)
        out = N.join_name(stem, set_ext)
    return out


_APPLIERS = {
    "add": _apply_add,
    "delete": _apply_delete,
    "replace": _apply_replace,
    "convert": _apply_convert,
}


def apply_rules(rules: list[Rule], name: str, index: int, ctx: ApplyCtx) -> str:
    """按顺序应用所有启用的规则。index 是该文件在批次中的 0 基序号。"""
    out = name
    for rule in rules:
        if not rule.enabled:
            continue
        fn = _APPLIERS.get(rule.type)
        if fn is None:
            continue
        try:
            out = fn(rule.params, out, index, ctx)
        except Exception:
            # 单条规则出错不应让整个预览崩掉，保留该步之前的结果
            continue
    return out


def preview_rule(rule: Rule, sample: str = "示例文件名.txt") -> str:
    """给界面用的单条规则实时预览。"""
    try:
        return apply_rules([rule], sample, 0,
                           ApplyCtx(now=datetime.now(), parent="文件夹"))
    except Exception:
        return sample
