"""极简双语（中/英）。

约定：源码里直接写中文作为 key，英文查表。这样代码本身可读，
漏翻的地方最多显示成中文，不会出现 "missing.key"。

语言选择：auto（跟随系统）/ zh / en。
系统语言匹配不上时按需求默认英文。
"""

from __future__ import annotations

import os
import sys

LANG_AUTO = "auto"
LANG_ZH = "zh"
LANG_EN = "en"

LANGUAGES = {
    LANG_ZH: "中文",
    LANG_EN: "English",
}

_current = LANG_EN

# ---------------------------------------------------------------- 系统语言

def system_language() -> str:
    """读 Windows 的界面语言；非中文一律归到英文。"""
    if sys.platform == "win32":
        try:
            import ctypes
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            primary = lcid & 0x3FF          # 0x04=中文 0x09=英文
            if primary == 0x04:
                return LANG_ZH
            if primary == 0x09:
                return LANG_EN
            return LANG_EN
        except Exception:
            pass
    lang = ""
    try:
        import locale
        lang = (locale.getlocale()[0] or "") or ""
    except Exception:
        pass
    lang = lang or os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
    lang = lang.lower()
    if lang.startswith("zh"):
        return LANG_ZH
    if lang.startswith("en"):
        return LANG_EN
    return LANG_EN


def resolve_language(setting: str) -> str:
    if setting in (LANG_ZH, LANG_EN):
        return setting
    return system_language()


def set_language(lang: str) -> None:
    global _current
    _current = lang if lang in (LANG_ZH, LANG_EN) else LANG_EN


def current_language() -> str:
    return _current


def join_list(items) -> str:
    """中文用顿号，英文用逗号。"""
    return ("、" if _current == LANG_ZH else ", ").join(items)


def tr(text: str, **kw) -> str:
    """中文原文 -> 当前语言。只有传了占位符参数才做格式化。"""
    if _current == LANG_ZH:
        out = text
    else:
        out = _EN.get(text, text)
    if kw:
        try:
            return out.format(**kw)
        except (KeyError, IndexError, ValueError):
            return out
    return out


# ---------------------------------------------------------------- 英文字典
_EN: dict[str, str] = {
    # ---- 通用
    "(空)": "(empty)",
    "示例文件名.txt": "sample-file.txt",
    "确定": "OK",
    "取消": "Cancel",
    "关闭": "Close",
    "提示": "Notice",
    "是否": "Yes",
    "易名匣": "Renamivo",
    "关于": "About",

    # ---- 顶栏
    "打开文件夹": "Open folder",
    "上一级": "Up",
    "刷新": "Refresh",

    "撤销改名": "Undo rename",
    "就绪": "Ready",
    "未打开文件夹": "No folder opened",
    "关于本软件": "About",
    "检查更新": "Check for updates",
    "GitHub 项目主页": "GitHub repository",
    "界面语言": "Language",
    "自动（跟随系统）": "Auto (system)",
    "语言": "Language",
    "帮助": "Help",
    "更多": "More",
    "设置": "Settings",

    # ---- 目录树
    "目录": "Folders",

    # ---- 规则面板
    "改名规则": "Rules",
    "按从上到下的顺序依次执行 · 拖动卡片可调整顺序":
        "Applied top to bottom · drag cards to reorder",
    "添加规则": "Add rule",
    "清空": "Clear",
    "存为预设": "Save preset",
    "存为规则组": "Save as group",

    "规则组": "Groups",
    "载入或删除保存过的规则组": "Load or delete a saved group",
    "把规则存下来，下次一键载入": "Save this rule set to reload later",
    "把这组规则存下来，下次一键载入": "Save this rule set to reload later",
    "给这组规则起个名字，下次从「规则组」里一键载入：":
        "Name this rule set so you can reload it from “Groups”:",
    "我的规则组": "My rules",
    "已保存": "Saved",
    "规则组「{name}」已保存。": "Rule group “{name}” saved.",
    "已存在": "Already exists",
    "规则组「{name}」已存在，要覆盖吗？": "A group named “{name}” exists. Overwrite it?",
    "删除规则组": "Delete group",
    "确定删除规则组「{name}」？": "Delete the rule group “{name}”?",
    "（还没有保存过规则组）": "(no saved groups yet)",
    "导入规则组": "Import rule group",
    "预设 ▾": "Presets ▾",
    "还没有规则。\n点右上角「添加规则」，比如「添加 → 文件名开头 → IMG_{n}」。":
        "No rules yet.\nClick “Add rule”, e.g. Add → beginning → IMG_{n}.",
    "（暂无预设）": "(no presets)",
    "从文件导入…": "Import from file…",
    "保存预设": "Save preset",
    "我的预设": "my preset",
    "预设文件 (*.json)": "Preset files (*.json)",
    "当前没有规则可保存。": "There are no rules to save.",
    "保存失败": "Save failed",
    "载入失败": "Load failed",
    "导入预设": "Import preset",

    # ---- 规则类型
    "添加": "Add",
    "删除": "Delete",
    "替换": "Replace",
    "转换": "Convert",
    "启用 / 停用这条规则": "Enable / disable this rule",
    "上移": "Move up",
    "下移": "Move down",
    "删除此规则": "Delete this rule",
    "（无变化）": "(no change)",
    "（已停用）": "(disabled)",

    # ---- 添加卡片
    "位置": "Position",
    "内容": "Text",
    "如 IMG_{n} 或 {date}-产品": "e.g. IMG_{n} or {date}-product",
    "序号": "Sequence",
    "起始": "Start",
    "步长": "Step",
    "位数": "Digits",
    "时间格式": "Date format",
    "时间": "Time",
    "可用占位符：": "Placeholders:",
    "当前主名": "Current stem",
    "扩展名": "Extension",
    "原文件名": "Original name",
    "上级文件夹名": "Parent folder",

    # ---- 删除卡片
    "范围": "Scope",
    "方式": "Mode",
    "删除指定文字": "Remove text",
    "正则表达式": "Regular expression",
    "按位置删除": "Remove by position",
    "删除括号内容": "Remove bracketed text",
    "清理残留空格": "Clean leftover spaces",
    "要删除的文字，如 副本": "Text to remove, e.g. copy",
    "忽略大小写": "Ignore case",
    "只删第一个": "First match only",
    r"正则，如 \(\d+\) 或 ^\d{8}_": r"regex, e.g. \(\d+\) or ^\d{8}_",
    "从": "From",
    "开头": "Start",
    "结尾": "End",
    "个字符": "characters",
    "括号类型": "Bracket type",
    "圆括号 ( )": "Round ( )",
    "方括号 [ ]": "Square [ ]",
    "花括号 { }": "Curly { }",
    "尖括号 < >": "Angle < >",
    "中文括号 （ ）": "CJK round （ ）",
    "中文方头 【 】": "CJK lenticular 【 】",
    "保留括号，只删里面的内容": "Keep the brackets, remove only the inside",

    # ---- 替换卡片
    "查找": "Find",
    "要被替换的内容": "Text to find",
    "替换为": "Replace with",
    "留空表示删除": "empty = delete",
    r"使用正则（替换处可用 \1 或 $1 引用分组）":
        r"Use regex (use \1 or $1 for groups)",
    "只替换第一个": "First match only",

    # ---- 转换卡片
    "大小写": "Case",
    "全/半角": "Width",
    "全部字符": "All characters",
    "仅字母数字": "Letters and digits",
    "仅符号": "Symbols only",
    "去首尾空格": "Trim spaces",
    "连续空格合一": "Collapse spaces",
    "删所有空格": "Remove all spaces",
    "去重音(á→a)": "Strip accents (á→a)",
    "扩展名改为": "Set extension",
    "留空不改": "keep",
    "对所有文件生效": "applies to all files",
    "不变": "Keep",
    "全部大写": "UPPER CASE",
    "全部小写": "lower case",
    "每个单词首字母大写": "Title Case",
    "仅首字母大写": "Capitalize",
    "全角 → 半角": "Full → half width",
    "半角 → 全角": "Half → full width",
    "文件名": "Name",
    "整个文件名": "Full filename",
    "文件名开头": "Beginning of name",
    "文件名结尾（扩展名前）": "End of name (before ext.)",
    "扩展名之后": "After extension",

    # ---- 规则描述
    "{pos}添加：{txt}": "{pos}: add {txt}",
    "从{sc}删除文字：{txt}": "Remove text from {sc}: {txt}",
    "从{sc}删除正则：{pat}": "Remove regex from {sc}: {pat}",
    "从{sc}{where}删除 {n} 个字符": "Remove {n} chars from {where} of {sc}",
    "删除{sc}中的 {br} {kind}": "Remove {br} {kind} in {sc}",
    "括号内内容": "contents",
    "括号及其内容": "brackets and contents",
    "{sc}中 {f} → {r}{regex}": "{sc}: {f} → {r}{regex}",
    "（正则）": " (regex)",
    "{sc}：{ops}": "{sc}: {ops}",
    "(未选择操作)": "(nothing selected)",
    "扩展名改为 .{ext}": "set extension to .{ext}",
    "去重音": "strip accents",
    "合并连续空格": "collapse spaces",
    "删除所有空格": "remove spaces",

    # ---- 文件列表
    "搜索文件名或新文件名…": "Search name or new name…",
    "把搜索内容当作正则表达式": "Treat the search text as a regular expression",
    "全部类型": "All types",
    "只看变更": "Changed only",
    "只看勾选": "Checked only",
    "含子文件夹": "Subfolders",
    "含文件夹": "Folders",
    "隐藏项": "Hidden",
    "递归扫描当前目录下的所有子文件夹": "Scan every subfolder recursively",
    "把子文件夹也列出来，可以一起改名": "List subfolders so they can be renamed too",
    "无扩展名": "No ext",
    "全选": "Select all",
    "全不选": "Select none",
    "反选": "Invert",
    "执行改名": "Rename",
    "执行改名 ({n})": "Rename ({n})",
    "共 {n} 项": "{n} items",
    "勾选 {n}": "{n} checked",
    "将改名 {n}": "{n} to rename",
    "冲突 {n}": "{n} conflicts",
    "无变化 {n}": "{n} unchanged",
    "名称": "Name",
    "子目录": "Subfolder",
    "新名称": "New name",
    "类型": "Type",
    "大小": "Size",
    "修改时间": "Modified",
    "状态": "Status",
    "文件夹": "Folder",
    "不处理": "Skipped",
    "将变更": "Will change",
    "无变化": "Unchanged",
    "冲突": "Conflict",
    "已改名": "Renamed",
    "非法": "Invalid",
    "在资源管理器中显示": "Show in Explorer",
    "复制文件名": "Copy name",
    "复制新文件名": "Copy new name",
    "复制完整路径": "Copy full path",
    "打开所在文件夹": "Open containing folder",
    "{path} — 共 {n} 项": "{path} — {n} items",

    # ---- 校验信息
    "文件名为空": "Empty filename",
    "含非法字符 {chars}": "Illegal characters: {chars}",
    "含控制字符": "Contains control characters",
    "结尾不能是空格或点": "Cannot end with a space or a dot",
    "不能以空格开头": "Cannot start with a space",
    "文件名过长（超过 255 字符）": "Name too long (over 255 characters)",
    "{stem} 是系统保留名": "{stem} is a reserved Windows name",
    "与本批次其他文件重名": "Duplicates another file in this batch",
    "目标文件名已存在": "Target name already exists",
    "目标文件名已被占用": "Target name is taken",

    # ---- 扫描
    "目录不存在或不可访问": "Folder does not exist or is not accessible",
    "无法读取 {path}：{err}": "Cannot read {path}: {err}",
    "文件数超过 {n}，只显示前 {n} 个": "More than {n} files, showing the first {n}",

    # ---- 执行
    "没有需要改名的文件": "Nothing to rename",
    "目标已存在: {name}": "Target already exists: {name}",
    "源文件不存在": "Source file is gone",
    "文件在执行前已被移走，已回滚": "A file disappeared before renaming; rolled back",
    "改名失败：{name} — {err}": "Rename failed: {name} — {err}",
    "写入目标名失败：{name} — {err}": "Could not write the new name: {name} — {err}",
    "已改名 {n} 个文件": "Renamed {n} files",
    "找不到 {name}，无法撤销": "Cannot find {name}; undo aborted",
    "原名称已被占用：{name}": "The original name is taken: {name}",
    "恢复完成，但有 {n} 个文件需要手工处理":
        "Recovery finished, but {n} files need manual attention",
    "已恢复到改名前的状态": "Restored to the state before renaming",

    # ---- 对话框
    "确认改名": "Confirm rename",
    "确定要把 {n} 个文件改名吗？": "Rename {n} files?",
    "改名后可以用顶部的「撤销改名」还原。":
        "You can revert this with “Undo rename” afterwards.",
    "开始改名": "Rename",
    "有项目会失败": "Some items will fail",
    "{n} 个项目存在冲突或非法字符，将被跳过。":
        "{n} items have conflicts or illegal characters and will be skipped.",
    "跳过它们，改另外 {n} 个": "Skip them and rename the other {n}",
    "返回检查": "Go back",
    "… 另有 {n} 个": "… and {n} more",
    "没有可执行的项目": "Nothing to execute",
    "请先添加规则，并勾选需要改名的文件。":
        "Add a rule first, then tick the files you want to rename.",
    "改名失败": "Rename failed",
    "已回滚到改名前的状态。": "Rolled back to the state before renaming.",
    "要把 {time} 改名的 {n} 个文件改回原名吗？":
        "Restore the original names for the {n} files renamed at {time}?",
    "撤销失败": "Undo failed",
    "已撤销 {n} 个文件的改名": "Restored {n} file names",
    "改名历史": "Rename history",
    "还没有改名记录。": "No rename records yet.",
    "改名历史（最近 30 批）": "Rename history (last 30 batches)",
    "出现异常": "Unexpected error",
    "程序遇到了一个意外错误，操作未完成。":
        "The program hit an unexpected error and the operation did not finish.",
    "上次的改名没有完成": "The previous rename did not finish",
    "检测到 {time} 开始的一次改名（{n} 个文件）没有正常结束。\n\n是否把它恢复到改名前的状态？":
        "A rename started at {time} ({n} files) did not finish.\n\n"
        "Restore those files to their previous names?",
    "恢复结果": "Recovery result",
    "已在浏览器中打开最新版下载页": "Opened the latest release page in your browser",
    "（没有可撤销的操作）": "(nothing to undo)",

    # ---- 结果
    "改名结果": "Rename result",
    "全部成功：{ok} 个文件已改名。": "All good: {ok} files renamed.",
    "成功 {ok} 个，失败 {fail} 个。": "{ok} succeeded, {fail} failed.",
    "跳过 {n} 个冲突项。": "{n} conflicting items were skipped.",
    "失败项：": "Failed items:",
    "文件": "File",
    "原因": "Reason",
    "在资源管理器中打开": "Open in Explorer",
    "完成": "Done",

    # ---- 关于
    "版本": "Version",
    "作者": "Author",
    "数据目录": "Data folder",
    "打开目录": "Open folder",
    "检查最新版本": "Get the latest version",
    "GitHub 仓库地址未配置": "No GitHub repository configured",
    "在 config.json 里填 github_repo，或在 renamer/meta.py 里改 GITHUB_REPO。":
        "Set github_repo in config.json, or GITHUB_REPO in renamer/meta.py.",
    "批量改名 Windows 文件名，先预览再执行，支持撤销。":
        "Batch-rename files on Windows. Preview first, undo any time.",
    "快捷键": "Shortcuts",
    "Ctrl+O 打开文件夹 · F5 刷新 · Ctrl+F 搜索":
        "Ctrl+O open folder · F5 refresh · Ctrl+F search",
    "安全机制": "Safety",
    "所有改名先预览；冲突会被拦下；执行中途出错自动回滚；随时可撤销。":
        "Every rename is previewed first; conflicts are blocked; "
        "failures roll back automatically; every batch can be undone.",
}
