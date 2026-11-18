# -*- coding: utf-8 -*-
"""
Build the blue-form (蓝色青年形态) pet pack assets.

The blue form is a one-way transformation FROM the red form. Layout mirrors the
red pack so the two read as the same character:

  蓝奈站立 / 战斗 / 必杀光线 / 必杀弓箭 / 飞行   -> five form clips + stickers
  蓝奈-1.gif           9 frames @220ms          -> idle loop
  蓝奈动画九帧格-2.gif   9 frames @300ms          -> nine action clips

Placement rules match build_assets.py: one shared scale per source group, feet on
the floor line for vertical poses, centred for wide ones, fixed union bbox for the
loop GIF so its own motion is not re-anchored frame by frame.

The blue form deliberately has NO form-shift clip: the transition is red -> blue
only, and the shift animation belongs to the red form.
"""
import os
import shutil
import subprocess
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
WORKSPACE = os.path.dirname(BUNDLE)
PACK = os.path.join(BUNDLE, "pet-pack")
ANIM = os.path.join(PACK, "animation")
MEME = os.path.join(PACK, "memes")
SRC_BLUE = os.path.join(BUNDLE, "assets", "poses-blue")
TMP = os.path.join(BUNDLE, "_frames_blue")

FFMPEG = (r"C:\Users\Ronin\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")

CANVAS_W, CANVAS_H = 640, 360
FLOOR_Y = 336
TARGET_H = 296
BOB = 2
POSE_FPS = 25 / 2

BLUE_POSES = {
    "stand": "蓝奈站立.png",
    "battle": "蓝奈战斗.png",
    "beam": "蓝奈必杀光线姿势.png",
    "arrow": "蓝奈必杀弓箭姿势_herness.png",
    "flight": "蓝奈飞行姿势.png",
}
GIF_LOOP = "蓝奈-1.gif"
GIF_NINE = "蓝奈动画九帧格-2.gif"

# Nine distinct action poses in the blue grid.
NINE_ACTIONS = {
    0: "蓝奈-起手式",
    1: "蓝奈-连击式",
    2: "蓝奈-展开式",
    3: "蓝奈-横击式",
    4: "蓝奈-蓄势式",
    5: "蓝奈-爆发式",
    6: "蓝奈-回旋式",
    7: "蓝奈-疾飞式",
    8: "蓝奈-展翼式",
}

# pose key -> (clip name, meme name)
POSE_CLIPS = {
    "stand": ("蓝奈-形态-站立", "蓝奈-站立"),
    "battle": ("蓝奈-形态-战斗", "蓝奈-战斗"),
    "beam": ("蓝奈-形态-必杀光线", "蓝奈-必杀光线"),
    "arrow": ("蓝奈-形态-必杀弓箭", "蓝奈-必杀弓箭"),
    "flight": ("蓝奈-形态-飞行", "蓝奈-飞行"),
}

EVENT_CLIPS = {
    "蓝奈-转向-回身": "battle",
    "蓝奈-拖拽-飞行向左": "flight",
    "蓝奈-拖拽-飞行向右": "flight",
    "蓝奈-点击-光束": "beam",
    "蓝奈-点击-迎击": "battle",
    "蓝奈-点击-弓箭": "arrow",
    "蓝奈-移动-飞行巡航": "flight",
    "蓝奈-思考": "stand",
    "蓝奈-忙碌": "battle",
    "蓝奈-清点归档": "stand",
    "蓝奈-踱步张望": "battle",
    "蓝奈-雀跃庆祝": "arrow",
    "蓝奈-垂头叹气": "stand",
    "蓝奈-碎碎念": "stand",
    "蓝奈-入睡": "stand",
    "蓝奈-睡觉循环": "stand",
    "蓝奈-醒来": "battle",
    "蓝奈-余额-充足": "stand",
    "蓝奈-余额-正常": "battle",
    "蓝奈-余额-告急": "beam",
    "蓝奈-余额-耗尽": "arrow",
}


def bbox(img):
    b = img.getchannel("A").getbbox()
    if b is None:
        raise RuntimeError("empty sprite")
    return b


def scale_group(images, target_h=TARGET_H):
    heights = sorted(bbox(im)[3] - bbox(im)[1] for im in images)
    return target_h / float(heights[len(heights) // 2])


def place(img, scale, shared_bbox=None):
    sprite = img.crop(shared_bbox if shared_bbox is not None else bbox(img))
    w = max(1, int(round(sprite.width * scale)))
    h = max(1, int(round(sprite.height * scale)))
    if w > CANVAS_W * 0.92 or h > CANVAS_H * 0.94:
        fit = min(CANVAS_W * 0.92 / w, CANVAS_H * 0.94 / h)
        w = max(1, int(round(w * fit)))
        h = max(1, int(round(h * fit)))
    sprite = sprite.resize((w, h), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    x = (CANVAS_W - w) // 2
    y = (CANVAS_H - h) // 2 if w / float(h) > 1.25 else FLOOR_Y - h
    y = max(0, min(CANVAS_H - h, y))
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def bob_frames(base, count=20, amp=BOB):
    import math
    out = []
    for i in range(count):
        t = i / float(count)
        dy = int(round(-amp * (0.5 - 0.5 * math.cos(2 * math.pi * t))))
        f = Image.new("RGBA", base.size, (0, 0, 0, 0))
        f.alpha_composite(base, (0, dy))
        out.append(f)
    return out


def encode(frames, name, fps):
    d = os.path.join(TMP, name)
    os.makedirs(d, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(os.path.join(d, "f%03d.png" % i))
    out = os.path.join(ANIM, name + ".webm")
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                    "-framerate", "%.6f" % fps, "-i", os.path.join(d, "f%03d.png"),
                    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
                    "-crf", "28", "-deadline", "good", "-cpu-used", "4",
                    "-row-mt", "1", "-an", out], check=True)
    shutil.rmtree(d, ignore_errors=True)
    return out


def load_gif(name):
    im = Image.open(os.path.join(WORKSPACE, name))
    frames = []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        frames.append(im.convert("RGBA").copy())
    return frames, im.info.get("duration", 160)


def main():
    for d in (ANIM, MEME, SRC_BLUE, TMP):
        os.makedirs(d, exist_ok=True)

    # 1. idle loop GIF: keep its own cadence under one fixed transform
    loop_frames, loop_ms = load_gif(GIF_LOOP)
    xs0 = min(bbox(f)[0] for f in loop_frames)
    ys0 = min(bbox(f)[1] for f in loop_frames)
    xs1 = max(bbox(f)[2] for f in loop_frames)
    ys1 = max(bbox(f)[3] for f in loop_frames)
    union = (xs0, ys0, xs1, ys1)
    loop_scale = TARGET_H / float(ys1 - ys0)
    placed = [place(f, loop_scale, shared_bbox=union) for f in loop_frames]
    encode(placed, "蓝奈-待机-呼吸循环", 1000.0 / loop_ms)
    print("idle loop: %d frames @%dms -> %s"
          % (len(loop_frames), loop_ms, "蓝奈-待机-呼吸循环"))

    # 2. nine-grid GIF: nine independent action poses
    nine_frames, _ = load_gif(GIF_NINE)
    nine_scale = scale_group(nine_frames)
    for idx, name in sorted(NINE_ACTIONS.items()):
        base = place(nine_frames[idx], nine_scale)
        base.save(os.path.join(SRC_BLUE, "nine_%02d.png" % idx))
        encode(bob_frames(base), name, POSE_FPS)
    print("nine actions:", len(NINE_ACTIONS))

    # 3. five PNG poses: one shared scale, clips + stickers
    pngs = {}
    for key, fname in BLUE_POSES.items():
        pngs[key] = Image.open(os.path.join(WORKSPACE, fname)).convert("RGBA")
    scale = scale_group(list(pngs.values()))
    placed_poses = {}
    for key, img in pngs.items():
        base = place(img, scale)
        placed_poses[key] = base
        base.save(os.path.join(SRC_BLUE, key + ".png"))
    for key, (clip, meme) in POSE_CLIPS.items():
        encode(bob_frames(placed_poses[key]), clip, POSE_FPS)
        placed_poses[key].save(os.path.join(MEME, meme + ".png"))
    print("pose clips:", len(POSE_CLIPS))

    # 4. derived event clips (directional flight needs a real mirror)
    for name, key in EVENT_CLIPS.items():
        src = placed_poses[key]
        if name.endswith("向右"):
            src = src.transpose(Image.FLIP_LEFT_RIGHT)
        encode(bob_frames(src), name, POSE_FPS)
    print("event clips:", len(EVENT_CLIPS))

    shutil.rmtree(TMP, ignore_errors=True)
    total = len([f for f in os.listdir(ANIM) if f.endswith(".webm")])
    print("\ntotal clips in pack:", total)


if __name__ == "__main__":
    main()
