import os, sys, random
base = r"C:\Users\huang\Documents\batch-renamer\demo"
files = [
    "产品图片 (1).jpg", "产品图片 (2).jpg", "产品图片 (3).jpg",
    "产品图片（12）.JPG", "IMG_0001 副本.png", "IMG_0002 副本.png",
    "报价单 2024-03-07.xlsx", "报价单 2024-04-11.xlsx",
    "ＴＥＳＴ　ｆｉｌｅ（全角）.PDF", "manual  final.pdf",
    "  前后有空格.txt", "README", "logo.svg", "视频片段.mp4",
]
os.makedirs(base, exist_ok=True)
for f in files:
    p = os.path.join(base, f)
    try:
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("x" * random.randint(100, 900000))
    except OSError as e:
        print("skip", f, e)
sub = os.path.join(base, "2024年存档")
os.makedirs(sub, exist_ok=True)
for i in range(1, 6):
    with open(os.path.join(sub, f"扫描件_{i:03d}.tif"), "w") as fh:
        fh.write("y")
print(len(os.listdir(base)), "entries")
