# -*- coding: utf-8 -*-
"""End-to-end test of the one-way red -> blue transformation (correct API shapes)."""
import json
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:50474/dsh-pet-7340"


def req(path, method="GET", payload=None, timeout=90):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def visibility():
    cfg = req("/config")
    return {p["id"]: p["display"] for c in cfg.values() for p in c.get("pets", [])}


v = visibility()
print("=== 1. 切换前 ===")
print("  nexus      =", v.get("nexus"))
print("  nexus-blue =", v.get("nexus-blue"))

# make the test repeatable: restore red first
if v.get("nexus-blue") == "both":
    print("  (复位：先恢复红色)")
    req("/pet-display", "POST", {"id": "nexus", "display": "both"})
    req("/pet-display", "POST", {"id": "nexus-blue", "display": "none"})
    v = visibility()
    print("  nexus      =", v.get("nexus"))
    print("  nexus-blue =", v.get("nexus-blue"))

assert v.get("nexus") == "both" and v.get("nexus-blue") == "none", "前置状态不对"

print("\n=== 2. 播放红色「形态切换」动画 ===")
t0 = time.time()
started = req("/anim?pet=nexus&surface=any", "POST", {"name": "形态切换"})
print("  anim:", started)
pb = started.get("playbackId")
assert started.get("ok") and pb, "点播失败"

print("\n=== 3. 等待动画播完 ===")
done = req("/playback/%s?wait=ended&timeout=10000" % urllib.parse.quote(pb))
elapsed = time.time() - t0
status = (done.get("playback") or {}).get("status") or done.get("status")
print("  status:", status)
print("  等待耗时: %.2f 秒" % elapsed)
if status != "ended":
    print("  FAIL: 动画未播完就继续了（会造成割裂）")
    sys.exit(1)

print("\n=== 4. 切换显示 ===")
for petId, display in (("nexus-blue", "both"), ("nexus", "none")):
    out = req("/pet-display", "POST", {"id": petId, "display": display})
    print("  %-11s -> %-5s : ok=%s" % (petId, display, out.get("ok", "?")))

time.sleep(0.5)
print("\n=== 5. 切换后 ===")
v = visibility()
print("  nexus      =", v.get("nexus"))
print("  nexus-blue =", v.get("nexus-blue"))
ok = v.get("nexus") == "none" and v.get("nexus-blue") == "both"
print("\n结果:", "PASS - 已单向切换为蓝色" if ok else "FAIL")

print("\n=== 6. 单向性确认 ===")
cfg = req("/config")
blue = cfg.get("nexus-blue", {})
names = []
for c in blue.get("animations", {}).get("categories", []):
    names.extend(c.get("actions", []))
for pool in blue.get("animations", {}).get("idle", []):
    names.append(pool)
print("  蓝色可用形态动作:", len(names))
print("  含「形态切换」的:", [n for n in names if "形态切换" in n] or "无（符合单向设计）")

sys.exit(0 if ok else 1)
