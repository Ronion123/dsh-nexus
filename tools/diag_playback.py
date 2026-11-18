# -*- coding: utf-8 -*-
"""Diagnose the exact shape of /playback?wait=ended so the swap waits for real."""
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
        return e.code, {"_error": e.read().decode("utf-8", "replace")[:300]}


# reset to red
req("/pet-display", "POST", {"id": "nexus", "display": "both"})
req("/pet-display", "POST", {"id": "nexus-blue", "display": "none"})

print("=== 点播形态切换 ===")
st, started = req("/anim?pet=nexus&surface=any", "POST", {"name": "形态切换"})
print("  status:", st, "body:", started)
pb = started.get("playbackId")
if not pb:
    sys.exit("no playbackId")

print("\n=== 立即查询（无 wait） ===")
st, plain = req("/playback/%s" % urllib.parse.quote(pb))
print("  status:", st, "body:", plain)

print("\n=== wait=ended&timeout=15000 ===")
t0 = time.time()
st, waited = req("/playback/%s?wait=ended&timeout=15000" % urllib.parse.quote(pb))
elapsed = time.time() - t0
print("  status:", st)
print("  elapsed: %.2f s" % elapsed)
print("  body:", json.dumps(waited, ensure_ascii=False)[:600])

print("\n=== 结论 ===")
status = (waited.get("playback") or {}).get("status") if isinstance(waited, dict) else None
print("  playback.status =", status)
print("  matched =", waited.get("matched") if isinstance(waited, dict) else None)
if elapsed > 0.5:
    print("  等待确实发生（>0.5s）")
else:
    print("  警告：几乎立即返回，可能没有真正等待")
