## 易名匣 / Renamivo v1.3.0

Windows 上的批量文件改名工具。先预览、后执行、随时撤销。

### 下载
- **Renamivo-Single.exe**（46 MB）— 单文件版，下载后双击即可运行，无需安装。
  支持 Windows 10 / 11（x64）。

### 功能
- 左侧目录树 + 右侧规则链，实时预览「原名 → 新名」
- 四种规则：**添加**（前缀/后缀，支持 `{n}` 序号、`{date}` 时间、`{name}` 原名等占位符）、**删除**（文字 / 正则 / 按位置 / 括号内容）、**替换**（含正则分组引用）、**转换**（大小写、全半角、空格整理、去重音、统一扩展名）
- 规则卡片可拖动排序，规则组可保存复用，关窗自动记住上次规则
- 筛选：搜索（支持正则）、按类型、只看变更、只看勾选，含子文件夹递归
- 中英双语，自动跟随系统语言
- 安全：冲突检测、两阶段改名（大小写改名 / 环形互换都能处理）、失败自动回滚、断电可恢复、一键撤销

### 注意
- 这是**未签名**的可执行文件，Windows SmartScreen 可能提示「未知发布者」，选择「更多信息 → 仍要运行」即可。
  部分开启了「智能应用控制」的系统会直接拦截未签名程序，这种情况下请自行关闭该功能或从源码运行。
- 源码运行：`pip install PySide6` 后执行 `python -m renamer`。

### 从源码打包
```cmd
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe PySide6 pyinstaller
.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --onefile ^
  --name Renamivo-Single --icon assets\icon.ico --add-data "assets;assets" run.pyw
```

MIT License © 2026 Hunpo827
