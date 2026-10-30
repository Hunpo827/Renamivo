<div align="center">

<img src="assets/icon.png" width="96" alt="Renamivo">

# Renamivo

A small batch file renamer for Windows.

[![Release](https://github.com/Hunpo827/Renamivo/actions/workflows/release.yml/badge.svg)](https://github.com/Hunpo827/Renamivo/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4.svg)](#download)

**English** · [简体中文](README.md)

</div>

![Main window](docs/images/main-en.png)

Two things make batch renaming annoying: you can't see what you're about to get, and you can't take
it back afterwards.

This tool is built around those two problems. You write the rules, the file list shows you every new
name before anything happens, and once you're happy you apply it. If the result isn't right, undo it.

## Using it

Pick a folder on the left (it opens on your desktop by default), stack rules on the right, and the
list below updates as you type. Rules run top to bottom and can be dragged into a different order.

- **Add** — insert text at the start, before the extension, or after it. `{n}` gives you a sequence
  number, `{date}` the current date, plus `{name}`, `{ext}`, `{orig}` and `{parent}`. Want
  `part-003` or `[003]`? Just type it around the token.
- **Delete** — literal text, a regex match, N characters from either end, or whatever sits inside
  brackets.
- **Replace** — with regex support and `\1` / `$1` backreferences.
- **Convert** — case, full/half width, whitespace cleanup, accents, and forcing an extension.

By default only the name part is touched, so your `JPG` stays `JPG`. Switch the scope to change the
extension itself.

## Safety

Duplicates, illegal characters and reserved Windows names (`CON`, `COM1`, …) are flagged red in the
preview and never reach the disk.

Renames go through a temporary name first, which is what makes case-only renames
(`a.txt → A.txt`) and swap-cycles work on Windows. If anything fails midway, everything rolls back.
The last 30 batches can be undone with one click.

## Download

Grab `Renamivo-Single.exe` from [Releases](https://github.com/Hunpo827/Renamivo/releases/latest) and
double-click it. No installation, Windows 10 / 11.

The binary isn't code-signed, so SmartScreen may warn about an unknown publisher — choose
"More info → Run anyway". Systems with Smart App Control enabled will block it outright; run from
source in that case.

## Running from source

```cmd
git clone https://github.com/Hunpo827/Renamivo.git
cd Renamivo
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe PySide6
.venv\Scripts\python.exe -m renamer
```

The core logic (`renamer/core/`) has no Qt dependency and is tested on its own:
`python -m pytest tests -q`.

Building and releasing happen in GitHub Actions — push a tag and it runs the tests, builds the exe
and publishes the release. For a local build, PyInstaller with the flags from
`.github/workflows/release.yml`.

## License

[Apache License 2.0](LICENSE) © 2026 Hunpo827
