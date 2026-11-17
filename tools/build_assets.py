# -*- coding: utf-8 -*-
"""
Build the dsh-nexus pet-pack assets from the new transparent source art.

Sources (all already RGBA / transparent — no background keying needed):
  * 透明背景Q版英雄循环动画.gif      12-frame real loop animation  -> idle
  * 超人风格角色九格动作动画组.gif     9 distinct action poses        -> action clips
  * 五姿态赛博英雄贴纸合集.webp        overview sheet               -> character art
  * <pose>_herness.png (x5)          5 high-res transparent poses   -> form clips + memes

Design rules for fidelity:
  * One shared scale per source group, derived from the group's median content height,
    so the artist's relative proportions between poses are preserved.
  * Vertical poses: centre X, feet on the floor line (dsh-pet FEET_Y baseline).
  * Wide poses (aspect > 1.25, e.g. flight / horizontal blasts): centre both axes.
  * The loop GIF keeps its fixed union bbox so its natural motion is not re-anchored
    frame by frame (that would jitter the animation).
  * Motion on still poses is a 2px breathing bob only — no warping of the artwork.
"""
import os
import shutil
import subprocess
import sys
from collections import Counter
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
WORKSPACE = os.path.dirname(BUNDLE)

PACK = os.path.join(BUNDLE, "pet-pack")
CFG_DIR = os.path.join(PACK, "config")
ANIM_DIR = os.path.join(PACK, "animation")
MEME_DIR = os.path.join(PACK, "memes")
SRC_STILL = os.path.join(BUNDLE, "assets", "poses")
SRC_LOOP = os.path.join(BUNDLE, "assets", "loop")
FRAME_TMP = os.path.join(BUNDLE, "_frames")

FFMPEG = (
    r"C:\Users\Ronin\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
)

CANVAS_W, CANVAS_H = 640, 360
FLOOR_Y = 336
TARGET_H = 296                # shared character height for vertical poses
BOB = 2                       # breathing amplitude in px
POSE_FPS = 25 / 2             # 12.5 fps for generated pose loops
LOOP_FPS = 25 / 4             # 6.25 fps = the GIF's native 160 ms frames

SOURCES = {
    "stand": "站立姿势_herness.png",
    "battle": "战斗姿势_herness.png",
    "beam": "必杀光线姿势_herness.png",
    "flight": "飞行姿势_herness.png",
    "shift": "形态切换_herness.png",
}
SHEET = "五姿态赛博英雄贴纸合集.webp"
GIF_LOOP = "透明背景Q版英雄循环动画.gif"
GIF_NINE = "超人风格角色九格动作动画组.gif"

# GIF nine-grid frame index -> (animation name, label used in the menu)
NINE_ACTIONS = {
    0: "起手式",
    1: "连击式",
    2: "展开式",
    3: "横击式",
    4: "蓄势式",
    5: "爆发式",
    6: "回旋式",
    7: "疾飞式",
    8: "展翼式",
}

# Five PNG poses -> (animation name, meme name)
POSE_CLIPS = {
    "stand": ("形态-站立", "站立"),
    "battle": ("形态-战斗", "战斗"),
    "beam": ("形态-必杀光线", "必杀光线"),
    "flight": ("形态-飞行", "飞行"),
    "shift": ("形态切换", "形态切换"),
}

# Derived event / interaction clips: name -> source pose key
EVENT_CLIPS = {
    "转向-回身": "battle",
    "拖拽-浮空": "flight",
    "点击-形态闪现": "shift",
    "点击-光束": "beam",
    "点击-迎击": "battle",
    "移动-飞行巡航": "flight",
    "思考": "stand",
    "忙碌": "battle",
    "清点归档": "stand",
    "踱步张望": "battle",
    "雀跃庆祝": "beam",
    "垂头叹气": "shift",
    "碎碎念": "stand",
    "入睡": "stand",
    "睡觉循环": "stand",
    "醒来": "battle",
    "余额-充足": "stand",
    "余额-正常": "battle",
    "余额-告急": "shift",
    "余额-耗尽": "shift",
}


def content_bbox(img):
    bbox = img.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("source image has no opaque pixels")
    return bbox


def scale_group(images, target_h=TARGET_H):
    """One scale factor per group: keep the artist's relative pose sizes."""
    heights = sorted(content_bbox(im)[3] - content_bbox(im)[1] for im in images)
    median = heights[len(heights) // 2]
    return target_h / float(median)


def place(img, scale, shared_bbox=None):
    """Scale then place on the 640x360 stage."""
    if shared_bbox is None:
        bbox = content_bbox(img)
        sprite = img.crop(bbox)
    else:
        sprite = img.crop(shared_bbox)
    w = max(1, int(round(sprite.width * scale)))
    h = max(1, int(round(sprite.height * scale)))
    if w > CANVAS_W * 0.92 or h > CANVAS_H * 0.94:
        fit = min(CANVAS_W * 0.92 / w, CANVAS_H * 0.94 / h)
        w = max(1, int(round(w * fit)))
        h = max(1, int(round(h * fit)))
    sprite = sprite.resize((w, h), Image.LANCZOS)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    aspect = w / float(h)
    x = (CANVAS_W - w) // 2
    if aspect > 1.25:
        y = (CANVAS_H - h) // 2          # wide pose: centre vertically
    else:
        y = FLOOR_Y - h                  # vertical pose: feet on the floor line
    y = max(0, min(CANVAS_H - h, y))
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def bob_frames(base, count=20, bob=BOB):
    """Gentle vertical breathing; upward-only so feet never sink below the floor."""
    import math
    out = []
    for i in range(count):
        t = i / float(count)
        dy = int(round(-bob * (0.5 - 0.5 * math.cos(2 * math.pi * t))))
        frame = Image.new("RGBA", base.size, (0, 0, 0, 0))
        frame.alpha_composite(base, (0, dy))
        out.append(frame)
    return out


def encode(frames, name, fps, out_dir=ANIM_DIR):
    tmp = os.path.join(FRAME_TMP, name)
    os.makedirs(tmp, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(os.path.join(tmp, "f%03d.png" % i))
    out_path = os.path.join(out_dir, name + ".webm")
    cmd = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", ("%.6f" % fps),
        "-i", os.path.join(tmp, "f%03d.png"),
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
        "-b:v", "0", "-crf", "28", "-deadline", "good", "-cpu-used", "4",
        "-row-mt", "1", "-an", out_path,
    ]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return out_path


def load_gif(path):
    im = Image.open(path)
    frames = []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        frames.append(im.convert("RGBA").copy())
    return frames, im.info.get("duration", 160)


def main():
    for d in (CFG_DIR, ANIM_DIR, MEME_DIR, SRC_STILL, SRC_LOOP, FRAME_TMP):
        os.makedirs(d, exist_ok=True)

    # ---- 1. loop GIF: preserve its own motion, one shared transform ----------
    loop_frames, loop_ms = load_gif(os.path.join(WORKSPACE, GIF_LOOP))
    xs0 = min(content_bbox(f)[0] for f in loop_frames)
    ys0 = min(content_bbox(f)[1] for f in loop_frames)
    xs1 = max(content_bbox(f)[2] for f in loop_frames)
    ys1 = max(content_bbox(f)[3] for f in loop_frames)
    union = (xs0, ys0, xs1, ys1)
    loop_scale = TARGET_H / float(ys1 - ys0)
    placed_loop = [place(f, loop_scale, shared_bbox=union) for f in loop_frames]
    for i, f in enumerate(placed_loop):
        f.save(os.path.join(SRC_LOOP, "f%02d.png" % i))
    encode(placed_loop, "待机-呼吸循环", LOOP_FPS)
    print("loop GIF: %d frames, %d ms/frame, union=%s" %
          (len(loop_frames), loop_ms, union))

    # ---- 2. nine-grid GIF: 9 distinct action poses, one shared scale --------
    nine_frames, _ = load_gif(os.path.join(WORKSPACE, GIF_NINE))
    nine_scale = scale_group(nine_frames)
    print("nine-grid scale: %.4f" % nine_scale)
    for idx, name in sorted(NINE_ACTIONS.items()):
        base = place(nine_frames[idx], nine_scale)
        base.save(os.path.join(SRC_STILL, "nine_%02d.png" % idx))
        encode(bob_frames(base), name, POSE_FPS)
        print("  action %d -> %s" % (idx, name))

    # ---- 3. five high-res PNG poses: one shared scale -----------------------
    pngs = {}
    for key, fname in SOURCES.items():
        pngs[key] = Image.open(os.path.join(WORKSPACE, fname)).convert("RGBA")
    png_scale = scale_group(list(pngs.values()))
    print("png-pose scale: %.4f" % png_scale)
    placed = {}
    for key, img in pngs.items():
        base = place(img, png_scale)
        placed[key] = base
        base.save(os.path.join(SRC_STILL, key + ".png"))

    for key, (anim_name, meme_name) in POSE_CLIPS.items():
        encode(bob_frames(placed[key]), anim_name, POSE_FPS)
        placed[key].save(os.path.join(MEME_DIR, meme_name + ".png"))
        print("  pose %-7s -> %s / meme %s" % (key, anim_name, meme_name))

    # ---- 4. derived event clips -------------------------------------------
    for name, key in EVENT_CLIPS.items():
        encode(bob_frames(placed[key]), name, POSE_FPS)
    print("derived event clips:", len(EVENT_CLIPS))

    # ---- 5. avatar / character sheet ---------------------------------------
    av = placed["stand"].crop(content_bbox(placed["stand"]))
    av.thumbnail((240, 240), Image.LANCZOS)
    avatar = Image.new("RGBA", (256, 256), (14, 20, 38, 255))
    avatar.alpha_composite(av, ((256 - av.width) // 2, (256 - av.height) // 2))
    avatar.convert("RGB").save(os.path.join(CFG_DIR, "nexus-avatar.png"))

    sheet = Image.open(os.path.join(WORKSPACE, SHEET)).convert("RGBA")
    sheet.thumbnail((900, 900), Image.LANCZOS)
    sheet.save(os.path.join(CFG_DIR, "nexus-character.png"), optimize=True)

    print("\nclips:", len(os.listdir(ANIM_DIR)),
          "memes:", len(os.listdir(MEME_DIR)))
    shutil.rmtree(FRAME_TMP, ignore_errors=True)
    print("DONE")


if __name__ == "__main__":
    main()
