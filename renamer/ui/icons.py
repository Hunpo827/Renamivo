"""统一的线性图标（16px 栅格，深/白两套）。"""

from __future__ import annotations

import os

from PySide6.QtGui import QIcon

from ..resources import resource

ICON_SIZE = 16

_cache: dict[tuple[str, bool], QIcon] = {}


def icon(name: str, light: bool = False) -> QIcon:
    """light=True 取白色版本，用在蓝色按钮上。"""
    key = (name, light)
    cached = _cache.get(key)
    if cached is not None:
        return cached
    suffix = "_w" if light else ""
    ic = QIcon()
    for fname in (f"{name}{suffix}.png", f"{name}{suffix}@2x.png"):
        path = resource(os.path.join("assets", "ui", "icons", fname))
        if os.path.exists(path):
            ic.addFile(path)
    _cache[key] = ic
    return ic
