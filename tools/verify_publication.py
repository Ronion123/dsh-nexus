# -*- coding: utf-8 -*-
"""Final end-to-end check: live index, icon, npm package, tarball."""
import json
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

CHECKS = [
    ("index (raw)", "https://raw.githubusercontent.com/Ronion123/dsh-nexus/v1.0.0/site/index.json"),
    ("icon  (raw)", "https://raw.githubusercontent.com/Ronion123/dsh-nexus/v1.0.0/site/icons/dsh-nexus.svg"),
    ("npm packument", "https://registry.npmjs.org/@roninxr%2fdsh-nexus"),
    ("npm tarball", "https://registry.npmjs.org/@roninxr/dsh-nexus/-/dsh-nexus-1.0.0.tgz"),
]

for label, url in CHECKS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dsh-nexus-final"})
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read()
            print("%-14s %-3s %-30s %8d B" % (label, r.status,
                                              r.headers.get("Content-Type"), len(body)))
            if label == "index (raw)":
                j = json.loads(body)
                p = j["plugins"][0]
                print("               name=%s" % p["name"])
                print("               ver=%s ts=%s"
                      % (p["versions"][0]["version"], p["versions"][0]["publishTimestamp"]))
                print("               icon=%s" % p["icon"])
            if label == "npm packument":
                j = json.loads(body)
                print("               versions=%s" % ", ".join(j["versions"].keys()))
                print("               latest=%s" % j["dist-tags"]["latest"])
    except urllib.error.HTTPError as e:
        print("%-14s %-3s %s" % (label, e.code, url))
    except Exception as e:
        print("%-14s ERR %s" % (label, e))
