"""生成工具栏用的线性图标（16px 网格，深/白两色，含 @2x）。"""
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QGuiApplication, QImage, QPainter, QPainterPath,
                           QPen, QPolygonF)

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "ui", "icons")
os.makedirs(BASE, exist_ok=True)

DARK = QColor("#57606a")
WHITE = QColor("#ffffff")
N = 16.0          # 设计栅格
W = 1.45          # 线宽

app = QGuiApplication(sys.argv)


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return QPointF(cx + r * math.cos(a), cy - r * math.sin(a))


def arrow_head(p: QPainter, tip: QPointF, deg: float, color, size=3.6):
    """在 tip 处画一个朝向 deg 的 V 形箭头（描边，比实心三角更清晰）。"""
    left = polar(tip.x(), tip.y(), size, deg + 145)
    right = polar(tip.x(), tip.y(), size, deg - 145)
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPolyline(QPolygonF([left, tip, right]))


def arc_tip(rect: QRectF, end_deg: float, span: float):
    """弧线终点的坐标与切线朝向（屏幕角度，顺时针为正）。"""
    cx, cy = rect.center().x(), rect.center().y()
    r = rect.width() / 2.0
    tip = polar(cx, cy, r, end_deg)
    ahead = polar(cx, cy, r, end_deg + (4.0 if span > 0 else -4.0))
    ang = math.degrees(math.atan2(-(ahead.y() - tip.y()), ahead.x() - tip.x()))
    return tip, ang


def draw_folder(p, color):
    path = QPainterPath()
    path.moveTo(1.7, 12.6)
    path.lineTo(1.7, 4.6)
    path.quadTo(1.7, 3.6, 2.7, 3.6)
    path.lineTo(5.9, 3.6)
    path.lineTo(7.3, 5.2)
    path.lineTo(13.3, 5.2)
    path.quadTo(14.3, 5.2, 14.3, 6.2)
    path.lineTo(14.3, 12.6)
    path.quadTo(14.3, 13.6, 13.3, 13.6)
    path.lineTo(2.7, 13.6)
    path.quadTo(1.7, 13.6, 1.7, 12.6)
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPath(path)


def draw_up(p, color):
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPolyline(QPolygonF([QPointF(4.2, 10.0), QPointF(8, 6.2), QPointF(11.8, 10.0)]))


def draw_down(p, color):
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPolyline(QPolygonF([QPointF(4.2, 6.4), QPointF(8, 10.2), QPointF(11.8, 6.4)]))


def draw_refresh(p, color):
    rect = QRectF(3.0, 3.0, 10.0, 10.0)
    start, span = 55, -265
    path = QPainterPath()
    path.arcMoveTo(rect, start)
    path.arcTo(rect, start, span)
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap))
    p.drawPath(path)
    tip, ang = arc_tip(rect, start + span, span)
    arrow_head(p, tip, ang, color)


def draw_undo(p, color):
    rect = QRectF(3.0, 3.0, 10.0, 10.0)
    start, span = 125, 265
    path = QPainterPath()
    path.arcMoveTo(rect, start)
    path.arcTo(rect, start, span)
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap))
    p.drawPath(path)
    tip, ang = arc_tip(rect, start + span, span)
    arrow_head(p, tip, ang, color)


def draw_plus(p, color):
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(8, 3.6), QPointF(8, 12.4))
    p.drawLine(QPointF(3.6, 8), QPointF(12.4, 8))


def draw_gear(p, color):
    teeth = 6
    outer, root, hole = 7.2, 5.3, 2.55
    sector = 360.0 / teeth
    path = QPainterPath()
    first = True
    for i in range(teeth):
        a = i * sector
        pts = [polar(8, 8, root, a + sector * 0.02),
               polar(8, 8, outer, a + sector * 0.16),
               polar(8, 8, outer, a + sector * 0.34),
               polar(8, 8, root, a + sector * 0.48)]
        for pt in pts:
            if first:
                path.moveTo(pt)
                first = False
            else:
                path.lineTo(pt)
    path.closeSubpath()
    ring = QPainterPath()
    ring.addEllipse(QPointF(8, 8), hole, hole)
    path = path.subtracted(ring)
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawPath(path)
    p.setBrush(Qt.NoBrush)


def draw_play(p, color):
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawPolygon(QPolygonF([QPointF(4.6, 3.4), QPointF(12.6, 8.0), QPointF(4.6, 12.6)]))
    p.setBrush(Qt.NoBrush)


def draw_cross(p, color):
    p.setPen(QPen(color, W, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(4.4, 4.4), QPointF(11.6, 11.6))
    p.drawLine(QPointF(11.6, 4.4), QPointF(4.4, 11.6))


ICONS = {
    "folder": draw_folder,
    "up": draw_up,
    "down": draw_down,
    "refresh": draw_refresh,
    "undo": draw_undo,
    "plus": draw_plus,
    "gear": draw_gear,
    "play": draw_play,
    "cross": draw_cross,
}


def render(fn, color, size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(size / N, size / N)
    fn(p, color)
    p.end()
    return img


for name, fn in ICONS.items():
    for suffix, color in (("", DARK), ("_w", WHITE)):
        render(fn, color, 16).save(os.path.join(BASE, f"{name}{suffix}.png"))
        render(fn, color, 32).save(os.path.join(BASE, f"{name}{suffix}@2x.png"))

# 预览图：16px 与 32px 并排
sheet = QImage(16 * len(ICONS) + 8 * len(ICONS) + 16, 108, QImage.Format_ARGB32)
sheet.fill(QColor("#ffffff"))
p = QPainter(sheet)
x = 8
for name in ICONS:
    for i, sz in enumerate((16, 32)):
        p.drawImage(x, 8 + i * 40, QImage(os.path.join(BASE, f"{name}@2x.png" if sz == 32 else f"{name}.png"))
                    .scaled(sz, sz, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    x += sz + 8
p.end()
sheet.save(os.path.join(BASE, "_preview.png"))
print("icons:", len(ICONS) * 4, "files ->", BASE)
