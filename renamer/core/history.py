"""改名历史，用于撤销。"""

from __future__ import annotations

import uuid
from datetime import datetime

from .config import HISTORY_PATH, load_json, save_json

MAX_BATCHES = 30


def load_history() -> list[dict]:
    data = load_json(HISTORY_PATH(), {"batches": []})
    if isinstance(data, list):
        return data
    return data.get("batches", [])


def add_batch(records: list[dict]) -> str:
    """records: [{'old':..., 'new':...}]，old/new 都是绝对路径。"""
    if not records:
        return ""
    batches = load_history()
    bid = uuid.uuid4().hex[:8]
    batches.append({
        "id": bid,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(records),
        "records": records,
    })
    save_json(HISTORY_PATH(), {"batches": batches[-MAX_BATCHES:]})
    return bid


def get_batch(bid: str) -> dict | None:
    for b in load_history():
        if b.get("id") == bid:
            return b
    return None


def drop_batch(bid: str) -> None:
    batches = [b for b in load_history() if b.get("id") != bid]
    save_json(HISTORY_PATH(), {"batches": batches})
