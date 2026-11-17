# -*- coding: utf-8 -*-
"""Validate the dsh-nexus pack config against dsh-pet's rules + asset coverage."""
import os, json, sys
sys.stdout.reconfigure(encoding="utf-8")

BUNDLE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(BUNDLE, "pet-pack")
CFG = os.path.join(PACK, "config", "nexus-config.json")
ANIM = os.path.join(PACK, "animation")
MEMES = os.path.join(PACK, "memes")

cfg = json.load(open(CFG, encoding="utf-8"))
a = cfg["animations"]
errors = []

# animationsValid shape (src/host/config/validate.ts)
for key in ("idle", "turn", "drag", "clicks", "categories"):
    if not isinstance(a.get(key), list):
        errors.append("animations.%s must be array" % key)
m = a.get("moves")
if not isinstance(m, dict) or not isinstance(m.get("default"), dict) or not isinstance(m.get("actions"), list):
    errors.append("animations.moves shape invalid")
moves_valid = True
if m and isinstance(m.get("default"), dict):
    d = m["default"]
    for k in ("minDist", "maxDist", "margin", "leadSec", "tailSec"):
        if not isinstance(d.get(k), (int, float)):
            moves_valid = False
    if not moves_valid:
        errors.append("moves.default fields must be numbers")
ev = a.get("events")
if not isinstance(ev, dict) or isinstance(ev, list):
    errors.append("animations.events must be object")
else:
    for pool, slots in ev.items():
        if not isinstance(slots, list) or len(slots) == 0:
            errors.append("events.%s empty/invalid" % pool)
        for slot in slots:
            if isinstance(slot, str):
                if not slot:
                    errors.append("events.%s empty string" % pool)
            elif isinstance(slot, list):
                if not slot or any(not isinstance(s, str) or not s for s in slot):
                    errors.append("events.%s bad array slot" % pool)
            else:
                errors.append("events.%s bad slot type" % pool)
    if not isinstance(ev.get("balance"), list) or len(ev["balance"]) == 0:
        errors.append("events.balance required")
if "sleep" in a:
    s = a["sleep"]
    if not isinstance(s, list) or len(s) == 0:
        errors.append("sleep invalid")
    for entry in s:
        for phase in ("start", "loop", "end"):
            pool = entry.get(phase) if isinstance(entry, dict) else None
            if not isinstance(pool, list) or len(pool) == 0 or any(not isinstance(x, str) or not x for x in pool):
                errors.append("sleep.%s invalid" % phase)
w = cfg.get("animationWeights")
if not isinstance(w, dict) or any(not isinstance(w.get(k), (int, float)) or w[k] < 0 for k in ("idle", "turn", "move")):
    errors.append("animationWeights invalid")

# collect animation names exactly like animationNames()
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
for pool in ev.values():
    for slot in pool:
        push(slot if isinstance(slot, list) else [slot])
push(a.get("baifan", []))
for entry in a.get("sleep", []):
    for phase in ("start", "loop", "end"):
        push(entry[phase])

on_disk = set(f[:-5] for f in os.listdir(ANIM) if f.endswith(".webm"))
missing = [n for n in names if n not in on_disk]
extra = sorted(on_disk - set(names))
print("animation names referenced:", len(names))
print("webm files on disk      :", len(on_disk))
print("missing files           :", missing)
print("unreferenced files      :", extra)

for key in cfg["memes"]:
    if not os.path.isfile(os.path.join(MEMES, key + ".png")):
        errors.append("meme missing: " + key)
for f in os.listdir(MEMES):
    if f.endswith(".png") and f[:-4] not in cfg["memes"]:
        errors.append("meme not in pool: " + f)

total = sum(w.values()) + sum(c["weight"] for c in a["categories"])
print("weight total            :", total, "(must be 100)")
if total != 100:
    errors.append("weight total != 100")

for p in cfg["pets"]:
    if p.get("display") not in ("web", "desktop", "both", "none"):
        errors.append("bad display")
    if not p.get("id"):
        errors.append("empty id")

# persona must carry the quotes
prompt = cfg.get("whisperPrompt", "")
quotes = ["宿命啊", "绝不是一种惩罚", "光是一种纽带", "万家灯火", "绝不放弃希望"]
for q in quotes:
    if q not in prompt:
        errors.append("persona missing quote: " + q)

print()
if missing:
    errors.append("missing clips")
print("ERRORS:", errors if errors else "NONE - config is valid")
sys.exit(1 if errors else 0)
