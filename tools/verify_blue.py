# -*- coding: utf-8 -*-
"""Verify the blue-form clips exist, are 640x360, and carry real alpha."""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
B = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
ANIM = os.path.join(B, "pet-pack", "animation")
FFMPEG = (r"C:\Users\Ronin\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

blue = sorted(f for f in os.listdir(ANIM) if f.startswith("蓝奈") and f.endswith(".webm"))
red = sorted(f for f in os.listdir(ANIM) if f.endswith(".webm") and not f.startswith("蓝奈"))
print("blue clips: %d   red clips: %d   total: %d"
      % (len(blue), len(red), len(blue) + len(red)))

print("\n--- blue clip inventory ---")
total = 0
for f in blue:
    p = os.path.join(ANIM, f)
    size = os.path.getsize(p)
    total += size
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "stream=width,height",
                        "-of", "default=nw=1", p], capture_output=True, text=True)
    dims = " ".join(r.stdout.split())
    ok = "OK" if "width=640" in dims and "height=360" in dims else "BAD"
    print("  %-26s %7dB %s %s" % (f[:-5], size, dims, ok))
print("blue total: %.2f MB" % (total / 1048576.0))

# alpha spot-check
print("\n--- alpha spot check ---")
for f in [blue[0], [x for x in blue if "待机" in x][0]]:
    p = os.path.join(ANIM, f)
    tmp = os.path.join(B, "_a.png")
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                    "-c:v", "libvpx-vp9", "-i", p, "-frames:v", "1",
                    "-c:v", "png", "-pix_fmt", "rgba", tmp], check=True)
    from PIL import Image
    im = Image.open(tmp).convert("RGBA")
    h = im.getchannel("A").histogram()
    t = im.width * im.height
    print("  %-26s transparent=%.1f%% opaque=%.1f%%"
          % (f[:-5], 100.0 * h[0] / t, 100.0 * sum(h[200:]) / t))
    os.remove(tmp)

print("\n--- stickers ---")
meme = os.path.join(B, "pet-pack", "memes")
for f in sorted(os.listdir(meme)):
    if f.startswith("蓝奈"):
        print("  %-18s %d B" % (f, os.path.getsize(os.path.join(meme, f))))
