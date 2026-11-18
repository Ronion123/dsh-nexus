# -*- coding: utf-8 -*-
"""Full acceptance test for the dual-form pack."""
import json
import sys
import time
import urllib.error
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
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode("utf-8", "replace")[:200]}


def head(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path), timeout=15) as r:
            return r.status, len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception:
        return None, 0


fails = []

print("=== 1. 两只宠物都在 ===")
_, cfg = req("/config")
pets = {p["id"]: p for c in cfg.values() for p in c.get("pets", [])}
for pid in ("nexus", "nexus-blue"):
    ok = pid in pets
    print("  %-11s %s display=%s" % (pid, "OK" if ok else "MISSING",
                                     pets.get(pid, {}).get("display")))
    if not ok:
        fails.append("missing pet " + pid)

print("\n=== 2. 红色素材可访问 ===")
for clip in ("形态切换", "待机-呼吸循环", "拖拽-飞行向左"):
    st, n = head("/thumb/nexus/%s.webm" % urllib.parse.quote(clip))
    print("  %-16s %s %sB" % (clip, st, n))
    if st != 200:
        fails.append("red clip " + clip)

print("\n=== 3. 蓝色素材可访问 ===")
for clip in ("蓝奈-待机-呼吸循环", "蓝奈-形态-必杀弓箭", "蓝奈-拖拽-飞行向左"):
    st, n = head("/thumb/nexus-blue/%s.webm" % urllib.parse.quote(clip))
    print("  %-20s %s %sB" % (clip, st, n))
    if st != 200:
        fails.append("blue clip " + clip)

print("\n=== 4. 贴纸（两个形态） ===")
for root, name in (("nexus", "站立"), ("nexus-blue", "蓝奈-站立")):
    st, n = head("/pic/memes/%s/%s.png" % (root, urllib.parse.quote(name)))
    print("  %-11s %-12s %s %sB" % (root, name, st, n))
    if st != 200:
        fails.append("meme " + root)

print("\n=== 5. 单向形态转换 ===")
# reset to red
req("/pet-display", "POST", {"id": "nexus", "display": "both"})
req("/pet-display", "POST", {"id": "nexus-blue", "display": "none"})
_, started = req("/anim?pet=nexus&surface=any", "POST", {"name": "形态切换"})
pb = started.get("playbackId")
print("  点播:", started)
if not pb:
    fails.append("anim start")
else:
    t0 = time.time()
    _, done = req("/playback/%s?wait=ended&timeout=10000" % urllib.parse.quote(pb))
    status = (done.get("playback") or {}).get("status") or done.get("status")
    elapsed = time.time() - t0
    print("  等待动画播完: status=%s 耗时=%.2fs" % (status, elapsed))
    if status != "ended":
        fails.append("shift not ended")
    if elapsed < 0.8:
        fails.append("did not actually wait (%.2fs)" % elapsed)
    for pid, disp in (("nexus-blue", "both"), ("nexus", "none")):
        req("/pet-display", "POST", {"id": pid, "display": disp})
    time.sleep(0.4)
    _, cfg2 = req("/config")
    v = {p["id"]: p["display"] for c in cfg2.values() for p in c.get("pets", [])}
    print("  切换后: nexus=%s nexus-blue=%s" % (v.get("nexus"), v.get("nexus-blue")))
    if not (v.get("nexus") == "none" and v.get("nexus-blue") == "both"):
        fails.append("swap failed")

print("\n=== 6. 单向性：蓝色无形态切换 ===")
blue = cfg.get("nexus-blue", {})
acts = [a for c in blue.get("animations", {}).get("categories", []) for a in c.get("actions", [])]
has_shift = [a for a in acts if "形态切换" in a]
print("  蓝色动作数:", len(acts), "| 含形态切换:", has_shift or "无")
if has_shift:
    fails.append("blue has form-shift clip")

# restore red so the desktop is in a sane state
req("/pet-display", "POST", {"id": "nexus", "display": "both"})
req("/pet-display", "POST", {"id": "nexus-blue", "display": "none"})
print("\n(已复位为红色形态)")

print("\n=== 结果 ===")
print("FAILURES:", fails if fails else "NONE - 全部通过")
sys.exit(1 if fails else 0)
