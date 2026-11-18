# -*- coding: utf-8 -*-
"""
Validate every pet pack config against dsh-pet's rules.

dsh-pet resolves assets per ASSET ROOT, which is the config file's name prefix:

    pet/<root>-config.json      the kind definition
    pet/<root>-animation/       clips  (no fallback to a shared directory)
    pet/<root>-memes/           stickers

The bundle therefore ships one source directory per root. This script derives that
mapping from the config names, so adding a form needs no change here.
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

BUNDLE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(BUNDLE, "pet-pack")
CFG_DIR = os.path.join(PACK, "config")

CONFIGS = sorted(
    f for f in os.listdir(CFG_DIR)
    if re.match(r"^.+?-config\.json$", f) and not f.startswith(".")
)

# Asset root -> source directory inside the bundle.
# `nexus` / `nexus-blue` ship as `animation`/`memes` and `blue-animation`/`blue-memes`
# for readability, so record the mapping explicitly instead of guessing.
SOURCE_DIRS = {
    "nexus": ("animation", "memes"),
    "nexus-blue": ("blue-animation", "blue-memes"),
}

errors = []


def animations_valid(a):
    for key in ("idle", "turn", "drag", "clicks", "categories"):
        if not isinstance(a.get(key), list):
            return "animations.%s must be array" % key
    m = a.get("moves")
    if not isinstance(m, dict) or not isinstance(m.get("default"), dict) \
            or not isinstance(m.get("actions"), list):
        return "animations.moves shape invalid"
    ev = a.get("events")
    if not isinstance(ev, dict) or isinstance(ev, list):
        return "animations.events must be object"
    for pool, slots in ev.items():
        if not isinstance(slots, list) or not slots:
            return "events.%s empty" % pool
        for slot in slots:
            if isinstance(slot, str):
                if not slot:
                    return "events.%s empty string" % pool
            elif isinstance(slot, list):
                if not slot or any(not isinstance(s, str) or not s for s in slot):
                    return "events.%s bad slot" % pool
            else:
                return "events.%s bad type" % pool
    if not isinstance(ev.get("balance"), list) or not ev.get("balance"):
        return "events.balance required"
    s = a.get("sleep")
    if s is not None:
        if not isinstance(s, list) or not s:
            return "sleep invalid"
        for entry in s:
            for phase in ("start", "loop", "end"):
                pool = entry.get(phase) if isinstance(entry, dict) else None
                if not isinstance(pool, list) or not pool \
                        or any(not isinstance(x, str) or not x for x in pool):
                    return "sleep.%s invalid" % phase
    return None


def collect_names(a):
    names = []

    def push(seq):
        for n in seq:
            if isinstance(n, str) and n and n not in names:
                names.append(n)

    for key in ("idle", "turn", "drag", "clicks"):
        push(a[key])
    push([x.get("name") for x in a["moves"]["actions"]])
    for c in a["categories"]:
        push(c["actions"])
    for pool in a["events"].values():
        for slot in pool:
            push(slot if isinstance(slot, list) else [slot])
    for entry in a.get("sleep", []):
        for phase in ("start", "loop", "end"):
            push(entry[phase])
    return names


print("configs:", CONFIGS)
all_clips = set()
all_memes = set()

for cfg_name in CONFIGS:
    root = cfg_name[: -len("-config.json")]
    path = os.path.join(CFG_DIR, cfg_name)
    cfg = json.load(open(path, encoding="utf-8"))
    print("\n--- %s  (asset root: %s) ---" % (cfg_name, root))

    if root not in SOURCE_DIRS:
        errors.append("%s: no source dir mapping for root %r" % (cfg_name, root))
        continue
    anim_src, meme_src = (os.path.join(PACK, d) for d in SOURCE_DIRS[root])
    if not os.path.isdir(anim_src):
        errors.append("%s: clip dir missing %s" % (cfg_name, SOURCE_DIRS[root][0]))
        continue
    if not os.path.isdir(meme_src):
        errors.append("%s: meme dir missing %s" % (cfg_name, SOURCE_DIRS[root][1]))
        continue

    clips = set(f[:-5] for f in os.listdir(anim_src) if f.endswith(".webm"))
    memes = set(f[:-4] for f in os.listdir(meme_src) if f.endswith(".png"))
    all_clips |= clips
    all_memes |= memes
    print("  available clips: %d | stickers: %d" % (len(clips), len(memes)))

    a = cfg.get("animations")
    if not isinstance(a, dict):
        errors.append("%s: animations missing" % cfg_name)
        continue
    bad = animations_valid(a)
    if bad:
        errors.append("%s: %s" % (cfg_name, bad))

    w = cfg.get("animationWeights")
    if not isinstance(w, dict) or any(
            not isinstance(w.get(k), (int, float)) or w[k] < 0 for k in ("idle", "turn", "move")):
        errors.append("%s: animationWeights invalid" % cfg_name)

    names = collect_names(a)
    missing = [n for n in names if n not in clips]
    if missing:
        errors.append("%s: missing clips %s" % (cfg_name, missing))
    print("  clips referenced: %d | missing: %s" % (len(names), missing or "none"))

    total = sum(w.values()) + sum(c["weight"] for c in a["categories"]) if isinstance(w, dict) else -1
    print("  weight total: %s" % total)
    if total != 100:
        errors.append("%s: weight total %s != 100" % (cfg_name, total))

    pool = cfg.get("memes")
    if not isinstance(pool, dict) or not pool:
        errors.append("%s: memes missing" % cfg_name)
    else:
        absent = [k for k in pool if k not in memes]
        if absent:
            errors.append("%s: meme files missing %s" % (cfg_name, absent))
        print("  memes: %d | missing: %s" % (len(pool), absent or "none"))

    pets = cfg.get("pets")
    if not isinstance(pets, list) or not pets:
        errors.append("%s: pets empty" % cfg_name)
    else:
        for p in pets:
            if p.get("display") not in ("web", "desktop", "both", "none"):
                errors.append("%s: bad display %s" % (cfg_name, p.get("display")))
            if not p.get("id"):
                errors.append("%s: empty pet id" % cfg_name)
        print("  pets: %s" % ", ".join("%s(%s)" % (p.get("id"), p.get("display")) for p in pets))

print("\ntotal clips across pack: %d | stickers: %d" % (len(all_clips), len(all_memes)))
print("\nERRORS:", errors if errors else "NONE - all pack configs are valid")
sys.exit(1 if errors else 0)
