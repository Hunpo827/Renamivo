"""把用户提供的 logo 转成 Windows 图标（含各尺寸 ICO）。"""
import os
from PIL import Image

SRC = r"C:\Users\huang\AppData\Local\hermes\attachments\ChatGPT 图像 2026年10月31日 03_30_53.png"
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

im = Image.open(SRC).convert("RGBA")
alpha = im.getchannel("A")
bbox = alpha.point(lambda v: 255 if v > 10 else 0).getbbox()
art = im.crop(bbox)
w, h = art.size
print("art", art.size)

side = max(w, h)
pad = int(side * 0.06)
canvas_size = side + pad * 2
canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
canvas.paste(art, ((canvas_size - w) // 2, (canvas_size - h) // 2), art)

master = canvas.resize((512, 512), Image.LANCZOS)
master.save(os.path.join(BASE, "icon.png"))

sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
ico = master.resize((256, 256), Image.LANCZOS)
ico.save(os.path.join(BASE, "icon.ico"), format="ICO", sizes=sizes)

# 预览条：小尺寸也看看
strip = Image.new("RGBA", (sum(s[0] for s in sizes) + 8 * len(sizes), 256), (255, 255, 255, 255))
x = 4
for s in sizes:
    small = master.resize(s, Image.LANCZOS)
    tile = Image.new("RGBA", (s[0], 256), (255, 255, 255, 255))
    tile.paste(small, (0, (256 - s[1]) // 2), small)
    strip.paste(tile, (x, 0))
    x += s[0] + 8
strip.save(os.path.join(BASE, "icon_preview.png"))
print("icon.png / icon.ico / icon_preview.png done", os.path.getsize(os.path.join(BASE, "icon.ico")))
