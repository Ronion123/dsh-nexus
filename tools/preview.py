# -*- coding: utf-8 -*-
"""Compose the detail preview (5 poses + 9 action frames) and check the icon."""
import os, base64, sys
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
BUNDLE = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
POSES = os.path.join(BUNDLE, "assets", "poses")
LOOP = os.path.join(BUNDLE, "assets", "loop")
DOCS = os.path.join(BUNDLE, "docs")
os.makedirs(DOCS, exist_ok=True)

W, H = 640, 300
board = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(board)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=(int(15 + 9 * t), int(21 + 11 * t), int(40 + 16 * t), 255))
d.rounded_rectangle([6, 6, W - 7, H - 7], radius=14, outline=(96, 136, 214, 170), width=2)

try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 13)
except Exception:
    font = ImageFont.load_default()


def paste_fit(path, box, label=None):
    im = Image.open(path).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop(bbox)
    im.thumbnail((box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
    x = box[0] + (box[2] - box[0] - im.width) // 2
    y = box[1] + (box[3] - box[1] - im.height) // 2
    board.alpha_composite(im, (x, y))
    if label:
        bb = d.textbbox((0, 0), label, font=font)
        d.text((box[0] + (box[2] - box[0] - (bb[2] - bb[0])) // 2, box[3] + 2),
               label, fill=(200, 218, 252, 255), font=font)


# Row 1: the five transparent PNG poses
poses = [("stand", "站立"), ("battle", "战斗"), ("beam", "必杀光线"),
         ("flight", "飞行"), ("shift", "形态切换")]
cell = W // 5
for i, (key, label) in enumerate(poses):
    paste_fit(os.path.join(POSES, key + ".png"),
              (i * cell + 4, 4, (i + 1) * cell - 4, 4 + 150), label)

# Row 2: a strip of the idle loop frames
loop_files = sorted(f for f in os.listdir(LOOP) if f.endswith(".png"))
pick = loop_files[::max(1, len(loop_files) // 6)][:6]
sub = W // max(1, len(pick))
for i, f in enumerate(pick):
    paste_fit(os.path.join(LOOP, f), (i * sub + 2, 186, (i + 1) * sub - 2, 292))
bb = d.textbbox((0, 0), "待机循环动画（原 GIF 12 帧）", font=font)
d.text(((W - (bb[2] - bb[0])) // 2, 168), "待机循环动画（原 GIF 12 帧）",
       fill=(180, 202, 245, 255), font=font)

png_path = os.path.join(DOCS, "preview.png")
board.convert("RGB").save(png_path, optimize=True)
b64 = base64.b64encode(open(png_path, "rb").read()).decode("ascii")
svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="300" '
       'viewBox="0 0 640 300">\n  <image href="data:image/png;base64,' + b64 +
       '" width="640" height="300"/>\n</svg>\n')
open(os.path.join(DOCS, "preview.svg"), "w", encoding="utf-8").write(svg)
print("preview.png", os.path.getsize(png_path))
print("preview.svg", os.path.getsize(os.path.join(DOCS, "preview.svg")))
