# -*- coding: utf-8 -*-
"""Verify generated clips: filenames, alpha via libvpx decode, dimensions, size."""
import os, subprocess, sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
BUNDLE = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
ANIM = os.path.join(BUNDLE, "pet-pack", "animation")
MEME = os.path.join(BUNDLE, "pet-pack", "memes")
CFG = os.path.join(BUNDLE, "pet-pack", "config")
FFMPEG = (r"C:\Users\Ronin\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

print("=== animation clips (%d) ===" % len(os.listdir(ANIM)))
total = 0
for f in sorted(os.listdir(ANIM)):
    p = os.path.join(ANIM, f)
    size = os.path.getsize(p)
    total += size
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                        "stream=width,height", "-of", "default=nw=1", p],
                       capture_output=True, text=True)
    dims = " ".join(r.stdout.split())
    print("  %-18s %8d B  %s" % (f, size, dims))
print("total clip bytes: %.2f MB" % (total / 1048576.0))

print("\n=== alpha check (libvpx decoder) ===")
for f in sorted(os.listdir(ANIM))[:3] + ["待机-呼吸循环.webm"]:
    if f not in os.listdir(ANIM):
        continue
    p = os.path.join(ANIM, f)
    tmp = os.path.join(BUNDLE, "_alpha.png")
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                    "-c:v", "libvpx-vp9", "-i", p, "-frames:v", "1",
                    "-c:v", "png", "-pix_fmt", "rgba", tmp], check=True)
    im = Image.open(tmp).convert("RGBA")
    h = im.getchannel("A").histogram()
    tot = im.width * im.height
    print("  %-18s transparent=%.1f%% opaque=%.1f%%" %
          (f, 100.0 * h[0] / tot, 100.0 * sum(h[200:]) / tot))
os.remove(os.path.join(BUNDLE, "_alpha.png"))

print("\n=== memes ===")
for f in sorted(os.listdir(MEME)):
    im = Image.open(os.path.join(MEME, f))
    print("  %-14s %s %s" % (f, im.mode, im.size))

print("\n=== config assets ===")
for f in sorted(os.listdir(CFG)):
    p = os.path.join(CFG, f)
    im = Image.open(p) if f.endswith(".png") else None
    print("  %-22s %8d B %s" % (f, os.path.getsize(p), im.size if im else ""))
