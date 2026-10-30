"""应用数据目录、配置读写。"""

from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "Renamivo"


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = Path(base) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_PATH = lambda: app_data_dir() / "config.json"
HISTORY_PATH = lambda: app_data_dir() / "history.json"
JOURNAL_PATH = lambda: app_data_dir() / "journal.json"
PRESET_DIR = lambda: (app_data_dir() / "presets")
LAST_RULES_PATH = lambda: (app_data_dir() / "last_rules.json")


def _atomic_write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load_json(path: Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(path, data)
    except Exception:
        pass


def load_config() -> dict:
    return load_json(CONFIG_PATH(), {})


def save_config(cfg: dict) -> None:
    save_json(CONFIG_PATH(), cfg)
