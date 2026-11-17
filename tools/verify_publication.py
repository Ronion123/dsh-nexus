# -*- coding: utf-8 -*-
"""Final verification: live index, npm package, README consistency."""
import json
import re
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

RAW_INDEX = "https://raw.githubusercontent.com/Ronion123/dsh-nexus/v1.0.1/site/index.json"
RAW_ICON = "https://raw.githubusercontent.com/Ronion123/dsh-nexus/v1.0.1/site/icons/dsh-nexus.svg"
PACKUMENT = "https://registry.npmjs.org/@roninxr%2fdsh-nexus"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dsh-nexus-verify"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.status, r.read()


print("=== live index (raw, v1.0.1) ===")
try:
    st, body = get(RAW_INDEX)
    j = json.loads(body)
    p = j["plugins"][0]
    print("status:", st)
    print("name  :", p["name"])
    print("icon  :", p["icon"])
    print("repo  :", p["repository"]["url"])
    for v in p["versions"]:
        print("  ver %-8s ts=%s" % (v["version"], v["publishTimestamp"]))
except Exception as e:
    print("FAIL:", e)

print("\n=== icon ===")
try:
    st, body = get(RAW_ICON)
    print("status:", st, "bytes:", len(body))
except Exception as e:
    print("FAIL:", e)

print("\n=== npm package ===")
try:
    st, body = get(PACKUMENT)
    j = json.loads(body)
    print("versions:", ", ".join(j["versions"].keys()))
    print("latest  :", j["dist-tags"]["latest"])
    readme = j.get("readme", "")
    urls = re.findall(r"https://[^\s`)]*index\.json", readme)
    print("README index URL:", urls[0] if urls else "(none)")
    print("README shows correct scope:", "@roninxr" in readme)
    print("README has stale scope    :", "ronion123" in readme)
    print("README has stale jsdelivr :", "jsdelivr" in readme)
except Exception as e:
    print("FAIL:", e)
