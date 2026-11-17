# -*- coding: utf-8 -*-
"""Generate the Nexus icon set that replaces dsh-pet's generic artwork.

Produces:
  assets/icon/logo.png            plugin logo + tray badge + window/taskbar icon
  assets/icon/notify-*.png        system-notification icons (square, readable at 32px)

Source art: the supplied transparent pose PNGs. Each output is composited onto a
dark rounded tile so a 16-32px tray badge stays legible (a bare white-on-white
sprite disappears in the notification area).
"""
import os
import sys
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")

B = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
POSES = os.path.join(B, "assets", "poses")
OUT = os.path.join(B, "assets", "icon")
os.makedirs(OUT, exist_ok=True)

TILE = (18, 26, 46)          # deep navy, matches the pack's UI accent
ACCENT = (78, 132, 214)      # azure rim


def tile(size, pad_ratio=0.10, radius_ratio=0.22, bg=TILE, rim=True):
    """A rounded dark tile with an optional accent rim."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * radius_ratio)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=bg + (255,))
    if rim:
        w = max(1, int(size * 0.018))
        d.rounded_rectangle([w, w, size - 1 - w, size - 1 - w],
                            radius=max(1, r - w), outline=ACCENT + (200,), width=w)
    return img


def emblem(src_pose, size, pad_ratio=0.10, bg=TILE):
    """Crop a pose's content and centre it on a dark tile."""
    base = tile(size, pad_ratio=pad_ratio, bg=bg)
    sprite = Image.open(os.path.join(POSES, src_pose)).convert("RGBA")
    bbox = sprite.getchannel("A").getbbox()
    if bbox:
        sprite = sprite.crop(bbox)
    box = int(size * (1 - 2 * pad_ratio))
    sprite.thumbnail((box, box), Image.LANCZOS)
    x = (size - sprite.width) // 2
    y = (size - sprite.height) // 2
    base.alpha_composite(sprite, (x, y))
    return base


# --- 1. logo: used by /logo, tray, window icon, taskbar ---------------------
# 512 is plenty for a tray badge and every window/taskbar size Electron asks for.
emblem("stand.png", 512, pad_ratio=0.12).save(os.path.join(OUT, "logo.png"))
print("logo.png", os.path.getsize(os.path.join(OUT, "logo.png")), "bytes")

# A smaller tray-friendly variant is not needed separately: Electron scales the
# 512px master. Keeping one file avoids a second thing to keep in sync.

# --- 2. notification icons --------------------------------------------------
# One per event kind dsh-pet can raise; pose chosen to read as that event.
NOTIFY = {
    "notify-done": ("beam.png", 0.10),        # finished: the finishing-beam pose
    "notify-error": ("shift.png", 0.12),      # error: the tense form shift
    "notify-truncated": ("shift.png", 0.12),  # truncated: same tense reading
    "notify-approval": ("battle.png", 0.12),  # needs approval: combat stance
    "notify-question": ("stand.png", 0.10),   # waiting for an answer: standing
    "notify-test": ("stand.png", 0.10),       # test notification: standing
}

for name, (pose, pad) in NOTIFY.items():
    img = emblem(pose, 256, pad_ratio=pad)
    path = os.path.join(OUT, name + ".png")
    img.save(path, optimize=True)
    print("%-18s %7d bytes" % (name + ".png", os.path.getsize(path)))
