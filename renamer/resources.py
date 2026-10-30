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


def desktop_dir() -> str:
    """当前用户的桌面目录。用系统 API 取，OneDrive 重定向过的桌面也能拿到。"""
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            # CSIDL_DESKTOPDIRECTORY = 0x10
            ctypes.windll.shell32.SHGetFolderPathW(None, 0x0010, None, 0, buf)
            if buf.value and os.path.isdir(buf.value):
                return buf.value
        except Exception:
            pass
    for cand in (os.path.join(os.path.expanduser("~"), "Desktop"),
                 os.path.join(os.path.expanduser("~"), "桌面")):
        if os.path.isdir(cand):
            return cand
    return os.path.expanduser("~")
