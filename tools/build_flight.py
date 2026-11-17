# -*- coding: utf-8 -*-
"""Build direction-aware flight clips for drag / throw / ceiling bounce.

dsh-pet mirrors a clip with CSS scaleX(-1) when facing='right', so one left-facing
asset already covers both directions. But the throw physics keeps whatever clip the
drag started with, and a ceiling bounce reverses vertical motion only — the sprite
should keep showing the flight pose with the correct horizontal heading.

To make the heading explicit (and independent of CSS mirroring quirks), we encode
both a left- and a right-facing flight clip and expose them as separate drag pool
entries; the client picks by direction at runtime through our scheduler.
"""
import os
import subprocess
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

B = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
ANIM = os.path.join(B, "pet-pack", "animation")
POSE = os.path.join(B, "assets", "poses")
TMP = os.path.join(B, "_frames_dir")
FFMPEG = (r"C:\Users\Ronin\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")

CANVAS_W, CANVAS_H = 640, 360
FPS = 12.5
FRAMES = 20
BOB = 4          # a touch more than the idle bob: reads as gliding


def bob(base, count=FRAMES, amp=BOB):
    import math
    out = []
    for i in range(count):
        t = i / float(count)
        dy = int(round(-amp * (0.5 - 0.5 * math.cos(2 * math.pi * t))))
        f = Image.new("RGBA", base.size, (0, 0, 0, 0))
        f.alpha_composite(base, (0, dy))
        out.append(f)
    return out


def encode(frames, name):
    d = os.path.join(TMP, name)
    os.makedirs(d, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(os.path.join(d, "f%03d.png" % i))
    out_path = os.path.join(ANIM, name + ".webm")
    subprocess.run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", "%.6f" % FPS, "-i", os.path.join(d, "f%03d.png"),
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
        "-b:v", "0", "-crf", "28", "-deadline", "good", "-cpu-used", "4",
        "-row-mt", "1", "-an", out_path,
    ], check=True)
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    return out_path


left = Image.open(os.path.join(POSE, "flight_left.png")).convert("RGBA")
right = Image.open(os.path.join(POSE, "flight_right.png")).convert("RGBA")

for name, img in (("拖拽-飞行向左", left), ("拖拽-飞行向右", right)):
    p = encode(bob(img), name)
    print("%-16s %7d bytes" % (name, os.path.getsize(p)))

import shutil
shutil.rmtree(TMP, ignore_errors=True)
print("\nclips in pack:", len([f for f in os.listdir(ANIM) if f.endswith(".webm")]))
