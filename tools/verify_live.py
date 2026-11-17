# -*- coding: utf-8 -*-
"""Verify every dsh-nexus endpoint on the live DSH Web GUI."""
import json, sys, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:50958/dsh-pet-7340"


def req(path, method="GET", payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(r, timeout=25) as resp:
        return resp.status, resp.headers.get("Content-Type"), resp.read()


st, _, body = req("/config")
cfg = json.loads(body)
print("GET /config:", st, "entries:", list(cfg.keys()))
n = cfg["nexus"]
print("  pet:", n["pets"][0]["name"], "| display:", n["pets"][0]["display"], "| size:", n["pets"][0]["size"])
a = n["animations"]
print("  idle:", a["idle"], "| clicks:", len(a["clicks"]))
print("  categories:", [(c["id"], c["weight"], len(c["actions"])) for c in a["categories"]])
print("  events:", {k: len(v) for k, v in a["events"].items()})
print("  sleep sets:", len(a.get("sleep", [])))
print("  memes:", len(n["memes"]), "| workStatusTexts:", len(n.get("workStatusTexts", [])), "groups")
persona = n.get("whisperPrompt", "")
print("  persona length:", len(persona), "| quotes present:",
      all(q in persona for q in ["宿命啊", "万家灯火", "绝不放弃希望"]))

names = []
def push(seq):
    for x in seq:
        if isinstance(x, str) and x and x not in names:
            names.append(x)
for k in ("idle", "turn", "drag", "clicks"):
    push(a[k])
push([m.get("name") for m in a["moves"]["actions"]])
for c in a["categories"]:
    push(c["actions"])
for pool in a["events"].values():
    for slot in pool:
        push(slot if isinstance(slot, list) else [slot])
for s in a.get("sleep", []):
    for ph in ("start", "loop", "end"):
        push(s[ph])

print("\n--- thumb endpoints (%d) ---" % len(names))
bad = []
for name in names:
    url = "/thumb/nexus/" + urllib.parse.quote(name) + ".webm"
    try:
        st, ct, data = req(url, "HEAD")
        if not (st == 200 and ct == "video/webm"):
            bad.append((name, st, ct))
    except Exception as e:
        bad.append((name, str(e)))
print("all reachable:", "YES" if not bad else bad)

print("\n--- assets ---")
for label, path in [
    ("avatar", "/logo?root=nexus"),
    ("character", "/character?root=nexus"),
    ("meme 站立", "/pic/memes/nexus/" + urllib.parse.quote("站立") + ".png"),
    ("meme 必杀光线", "/pic/memes/nexus/" + urllib.parse.quote("必杀光线") + ".png"),
]:
    try:
        st, ct, data = req(path)
        print("  %-14s %s %s %d bytes" % (label, st, ct, len(data)))
    except Exception as e:
        print("  %-14s ERROR %s" % (label, e))

print("\n--- /anim point-play ---")
for name in ["待机-呼吸循环", "起手式", "展翼式", "形态切换", "不存在-测试"]:
    st, _, body = req("/anim?pet=nexus&surface=any", "POST", {"name": name})
    print("  %-14s -> %s" % (name, json.loads(body)))

print("\nRESULT:", "ALL GOOD" if not bad else "FAILURES")
sys.exit(1 if bad else 0)
