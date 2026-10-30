import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "ui", "icons")
app = QGuiApplication(sys.argv)
names = ["folder","up","down","refresh","undo","plus","gear","play","cross"]
sizes = [16, 32, 48]
colw = 56
W = 10 + colw * len(names)
H = 10 + sum(s + 10 for s in sizes)
sheet = QImage(W, H, QImage.Format_ARGB32); sheet.fill(QColor("#ffffff"))
p = QPainter(sheet)
y = 8
for s in sizes:
    x = 8
    for n in names:
        f = f"{n}.png" if s <= 16 else f"{n}@2x.png"
        img = QImage(os.path.join(BASE, f)).scaled(s, s, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawImage(x, y, img)
        x += colw
    y += s + 10
p.end(); sheet.save(os.path.join(BASE, "_preview.png"))
print("ok", W, H)
