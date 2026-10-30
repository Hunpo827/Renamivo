import os
from PIL import Image, ImageDraw

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "ui")
os.makedirs(BASE, exist_ok=True)
COLOR = (87, 96, 106, 255)      # #57606a
HOVER = (31, 35, 40, 255)


def triangle(name, up: bool, size=(7, 4), color=COLOR, scale=8):
    w, h = size
    im = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if up:
        pts = [(0, h * scale), (w * scale, h * scale), (w * scale / 2, 0)]
    else:
        pts = [(0, 0), (w * scale, 0), (w * scale / 2, h * scale)]
    d.polygon(pts, fill=color)
    im = im.resize(size, Image.LANCZOS)
    im.save(os.path.join(BASE, name))
    # 2x
    im2 = Image.new("RGBA", (w * 2 * scale, h * 2 * scale), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(im2)
    if up:
        p2 = [(0, h * 2 * scale), (w * 2 * scale, h * 2 * scale), (w * scale, 0)]
    else:
        p2 = [(0, 0), (w * 2 * scale, 0), (w * scale, h * 2 * scale)]
    d2.polygon(p2, fill=color)
    im2 = im2.resize((w * 2, h * 2), Image.LANCZOS)
    im2.save(os.path.join(BASE, name.replace(".png", "@2x.png")))


triangle("up.png", True)
triangle("down.png", False)
triangle("up_hover.png", True, color=HOVER)
triangle("down_hover.png", False, color=HOVER)
print(sorted(os.listdir(BASE)))
