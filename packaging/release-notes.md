## Renamivo v1.3.0 — batch file renamer for Windows

Pick a folder, stack rules, watch the live `old → new` preview, then apply. Nothing is written until
you confirm, and every batch can be undone.

**Download `Renamivo-Single.exe` (~47 MB)** — single file, no installation, Windows 10 / 11 (x64).

### Highlights
- Four rule types: **Add** (prefix/suffix with `{n}` sequence and `{date}` timestamps), **Delete** (text, regex, by position, bracketed content), **Replace** (with regex groups), **Convert** (case, full/half width, spaces, accents, extension)
- Rules run top to bottom and can be dragged to reorder; rule groups can be saved and reloaded
- Live preview with conflict detection — illegal names, reserved names, duplicates and existing targets are flagged before anything happens
- Two-phase rename: case-only renames and `a ↔ b` swaps work; failures roll back automatically; crashes are recoverable
- One-click undo for the last 30 batches
- Bilingual UI (Chinese / English), follows the system language
- Search, type filter, changed-only, recursive subfolders

### Note
The executable is unsigned. SmartScreen may warn about an unknown publisher ("More info → Run
anyway"); systems with Smart Control enabled may block it entirely — run from source in that case.

---

## 易名匣 / Renamivo v1.3.0

Windows 批量文件改名工具：先预览、后执行、随时撤销。

**下载 `Renamivo-Single.exe`（约 47 MB）** —— 单文件、免安装，支持 Windows 10 / 11（x64）。

### 主要功能
- 四种规则：**添加**（前缀/后缀，支持 `{n}` 序号与 `{date}` 时间）、**删除**（文字/正则/按位置/括号内容）、**替换**（含正则分组引用）、**转换**（大小写、全半角、空格、去重音、统一扩展名）
- 规则从上到下依次执行，可拖动排序；规则组可保存复用，关窗记住上次规则
- 实时预览 + 冲突检测：非法字符、系统保留名、批内重名、目标已存在，执行前就标红
- 两阶段改名：大小写改名、环形互换都能正确执行；失败自动回滚；断电可恢复
- 撤销最近 30 批改名
- 中英双语界面，跟随系统语言
- 搜索、按类型筛选、只看变更、含子文件夹递归

### 说明
程序未签名，SmartScreen 可能提示未知发布者（选择「更多信息 → 仍要运行」）；开启「智能应用控制」的系统可能直接拦截，这种情况请用源码运行。

**Apache License 2.0** © 2026 Hunpo827
