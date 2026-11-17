# -*- coding: utf-8 -*-
"""Verify the directional flight control channel works end to end."""
import json
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:50958/dsh-pet-7340"


def post_anim(name, facing):
    payload = json.dumps({"name": name, "facing": facing}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/anim?pet=nexus&surface=any", data=payload, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, json.loads(r.read())


print("=== directional flight via /anim (what client.js sends) ===")
for facing, clip in (("left", "拖拽-飞行向左"), ("right", "拖拽-飞行向右")):
    st, body = post_anim(clip, facing)
    print("  facing=%-5s clip=%-14s -> %s %s" % (facing, clip, st, body))

print("\n=== rejection checks ===")
try:
    st, body = post_anim("拖拽-飞行向左", "up")
    print("  bad facing:", body)
except Exception as e:
    print("  bad facing rejected:", e)

print("\n=== config exposes the pool the client uses ===")
with urllib.request.urlopen(BASE + "/config", timeout=25) as r:
    cfg = json.loads(r.read())
a = cfg["nexus"]["animations"]
print("  drag pool:", a["drag"])
print("  flight category:", [c for c in a["categories"] if c["id"] == "飞行"])

# rest as left-facing idle
post_anim("待机-呼吸循环", "left")
print("\nrestored to idle")
