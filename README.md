<div align="center">

<img src="assets/icon.png" width="96" alt="Renamivo">

# 易名匣 · Renamivo

Windows 上批量改文件名的小工具。

[![Release](https://github.com/Hunpo827/Renamivo/actions/workflows/release.yml/badge.svg)](https://github.com/Hunpo827/Renamivo/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4.svg)](#下载)

[English](README.en.md) · **简体中文**

</div>

![主界面](docs/images/main-zh.png)

改文件名烦人的地方就两个：改之前不知道会变成什么样，改错了回不去。

这个工具就盯着这两点。规则写好后先在列表里预览出每一个新名字，看着顺眼了再执行，执行完还能撤销。

## 怎么用

左边点一个文件夹（打开时默认停在桌面），右边加规则，下面的列表会实时显示每个文件的新名字。四条规则从上往下依次生效，顺序可以拖动调整。

- **添加** —— 在文件名开头、扩展名前或扩展名后插入内容，支持 `{n}` 序号和 `{date}` 日期，也能用 `{name}`、`{ext}`、`{orig}`、`{parent}`。想写成 `第3章`、`[003]`，把这几个字直接打进去就行。
- **删除** —— 删指定文字、按正则删、从两头删掉几个字符、删括号里的内容。
- **替换** —— 支持正则，`\1` 和 `$1` 都能引用分组。
- **转换** —— 大小写、全角半角、空格整理、去重音、统一扩展名。

默认只动文件名那一段，扩展名不会被误伤；要改扩展名就把范围切过去。

## 安全

重名、非法字符、`CON`/`COM1` 这类系统保留名，在预览阶段就会标红，写不进磁盘。

真正改名时先把文件转成临时名字，再改成目标名字——所以只改大小写（`a.txt → A.txt`）、两个文件互换名字这种别扭的情况都能正确处理。中途出错会全部回滚，改完 30 批以内都能一键撤销。

## 下载

到 [Releases](https://github.com/Hunpo827/Renamivo/releases/latest) 下 `Renamivo-Single.exe`，双击就能跑，不用安装。Windows 10 / 11。

程序没有代码签名，SmartScreen 可能会提示"未知发布者"，点「更多信息 → 仍要运行」即可。开启了「智能应用控制」的系统会直接拦下来，那种情况只能用源码跑。

## 自己跑

```cmd
git clone https://github.com/Hunpo827/Renamivo.git
cd Renamivo
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe PySide6
.venv\Scripts\python.exe -m renamer
```

核心逻辑（`renamer/core/`）不依赖 Qt，可以单独跑测试：`python -m pytest tests -q`。

打包和发版都交给 GitHub Actions 了，推个 tag 就会自动跑测试、打包、发 Release。本地打包用 PyInstaller，参数见 `.github/workflows/release.yml`。

## 协议

[Apache License 2.0](LICENSE) © 2026 Hunpo827
