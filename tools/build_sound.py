# -*- coding: utf-8 -*-
"""Build the war-cry wav and a mirrored (left/right) flight clip pair.

Source: 战吼.mp3 -> assets/sound/click-duck.wav (used by the installer).
Also produce flight clips for both facings so drag/throw can show the right one.
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

B = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
SRC = r"C:\Users\Ronin\Desktop\桌宠设计\战吼.mp3"
SOUND_DIR = os.path.join(B, "assets", "sound")
POSE_DIR = os.path.join(B, "assets", "poses")

FFMPEG = (r"C:\Users\Ronin\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")

os.makedirs(SOUND_DIR, exist_ok=True)

# --- 1. war cry -> wav, silence trimmed, loudness normalised ---------------
out_wav = os.path.join(SOUND_DIR, "click-duck.wav")
flt = (
    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,"
    "areverse,"
    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,"
    "areverse,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)
subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-i", SRC, "-af", flt, "-ar", "44100", "-ac", "1",
                "-c:a", "pcm_s16le", out_wav], check=True)
print("wav:", os.path.getsize(out_wav), "bytes")

# --- 2. mirrored flight pose for both facings ------------------------------
# The flight art faces left by default; dsh-pet mirrors with scaleX(-1) when
# facing=right. We only need the base asset, but keep a pre-flipped copy so the
# pack can show motion detail on either side without relying on CSS mirroring.
from PIL import Image

flight = Image.open(os.path.join(POSE_DIR, "flight.png")).convert("RGBA")
print("flight pose:", flight.size)
flight.save(os.path.join(POSE_DIR, "flight_left.png"))
flight.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(POSE_DIR, "flight_right.png"))
print("wrote flight_left.png / flight_right.png")
