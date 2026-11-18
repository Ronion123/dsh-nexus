# -*- coding: utf-8 -*-
"""Find the working meme URL shape in dsh-pet 0.4.9 and verify both forms."""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:50474/dsh-pet-7340"


def head(path):
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception as e:
        return None, str(e)


BLUE = urllib.parse.quote("蓝奈-站立")
RED = urllib.parse.quote("站立")

print("=== 蓝色形态贴纸路径候选 ===")
for p in [
    f"/pic/memes/nexus-blue/{BLUE}.png",
    f"/pic/memes/{BLUE}.png",
    f"/pic/nexus-blue/{BLUE}.png",
    f"/pic/{BLUE}.png",
]:
    st, n = head(p)
    print("  %-45s -> %s %sB" % (p, st, n))

print("\n=== 红色形态贴纸（对照） ===")
for p in [
    f"/pic/memes/nexus/{RED}.png",
    f"/pic/memes/{RED}.png",
    f"/pic/{RED}.png",
]:
    st, n = head(p)
    print("  %-45s -> %s %sB" % (p, st, n))

print("\n=== 配置里的 memes 键与文件是否对齐 ===")
cfg = json.load(open(r"C:\Users\Ronin\.dsh\dsh-pet\pet\nexus-blue-config.json", encoding="utf-8"))
keys = list(cfg["memes"].keys())
print("  keys:", keys)
import os
files = sorted(os.listdir(r"C:\Users\Ronin\.dsh\dsh-pet\pet\nexus-blue-memes"))
print("  files:", [f[:-4] for f in files])
print("  match:", set(keys) == {f[:-4] for f in files})

print("\n=== 观察：dsh-pet 0.4.9 的 pic 路由 ===")
print("  /pic/<file> 会找 $DSH_HOME/dsh-pet/pic/<file> 或包内 assets/pic/<file>")
print("  旧的 /pic/memes/<root>/<name> 可能已不再由该路由处理")
