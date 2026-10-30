"""打包后仍能找到图标等随附资源。"""

from __future__ import annotations

import os
import sys


def resource(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, rel)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, rel)


def app_dir() -> str:
    """程序所在目录：打包后是 exe 所在文件夹，源码运行时是项目根目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
