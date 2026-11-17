# -*- coding: utf-8 -*-
"""Static validation of the complete dsh-nexus bundle."""
import os, json, sys, re
from xml.etree import ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []

for rel in ["package.json", "locale/en.json", "locale/zh.json",
            "pet-pack/config/nexus-config.json"]:
    try:
        json.load(open(os.path.join(B, rel), encoding="utf-8"))
        print("JSON OK  ", rel)
    except Exception as e:
        errors.append("JSON %s: %s" % (rel, e))

pkg = json.load(open(os.path.join(B, "package.json"), encoding="utf-8"))
_scope, _sep, _bare = pkg.get("name", "").partition("/")
if _bare != "dsh-nexus":
    errors.append("package name must be dsh-nexus (got %r)" % pkg.get("name"))
if pkg.get("dsh", {}).get("bundle", {}).get("patch") != "./cordis.patch.yml":
    errors.append("missing dsh.bundle.patch")
if not pkg.get("icon"):
    errors.append("missing icon")
for key in [".", "./cordis.patch.yml", "./locale/*.json", "./icon"]:
    if key not in pkg.get("exports", {}):
        errors.append("missing export " + key)
for key in ["index.js", "cordis.patch.yml", "locale", "docs", "icon.svg", "pet-pack"]:
    if key not in pkg.get("files", []):
        errors.append("missing files entry " + key)

patch = open(os.path.join(B, "cordis.patch.yml"), encoding="utf-8").read()
if not re.search(r"^\s*- id:\s*dsh-nexus\s*$", patch, re.M):
    errors.append("patch entry id missing or has trailing comment")
if "name: 'dsh-nexus'" not in patch:
    errors.append("patch name missing")

for loc, detail in [("en.json", "docs/DETAIL.md"), ("zh.json", "docs/DETAIL.zh.md")]:
    d = json.load(open(os.path.join(B, "locale", loc), encoding="utf-8"))
    meta = d.get("meta", {})
    for k in ("title", "description", "detail"):
        if not meta.get(k):
            errors.append("%s missing meta.%s" % (loc, k))
    if meta.get("detail") != detail:
        errors.append("%s detail mismatch" % loc)
    if not os.path.isfile(os.path.join(B, meta.get("detail", ""))):
        errors.append("%s detail file missing" % loc)

for doc in ["docs/DETAIL.md", "docs/DETAIL.zh.md"]:
    text = open(os.path.join(B, doc), encoding="utf-8").read().strip()
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) != 1 or not lines[0].startswith("!["):
        errors.append("%s not a single image line" % doc)
        continue
    m = re.search(r"\]\(([^)]+)\)", lines[0])
    if not m:
        errors.append("%s image target missing" % doc)
        continue
    target = os.path.join(os.path.dirname(os.path.join(B, doc)), m.group(1))
    if not os.path.isfile(target):
        errors.append("%s image missing: %s" % (doc, m.group(1)))
    else:
        try:
            ET.parse(target)
            print("SVG OK  ", m.group(1), os.path.getsize(target), "bytes")
        except Exception as e:
            errors.append("%s SVG parse: %s" % (doc, e))

try:
    ET.parse(os.path.join(B, "icon.svg"))
    print("SVG OK   icon.svg")
except Exception as e:
    errors.append("icon.svg parse: " + str(e))

icon_size = os.path.getsize(os.path.join(B, "icon.svg"))
preview_size = os.path.getsize(os.path.join(B, "docs", "preview.svg"))
print("icon.svg %d bytes; preview.svg %d bytes" % (icon_size, preview_size))
if icon_size > 256 * 1024:
    errors.append("icon too big")
if preview_size > 1024 * 1024:
    errors.append("preview too big")

for rel in ["index.js", "cordis.patch.yml", "icon.svg", "locale/en.json",
            "locale/zh.json", "docs/DETAIL.md", "docs/DETAIL.zh.md", "docs/preview.svg",
            "README.md"]:
    if not os.path.isfile(os.path.join(B, rel)):
        errors.append("missing file " + rel)

PACK = os.path.join(B, "pet-pack")
n_webm = len([f for f in os.listdir(os.path.join(PACK, "animation")) if f.endswith(".webm")])
n_png = len([f for f in os.listdir(os.path.join(PACK, "memes")) if f.endswith(".png")])
print("pet-pack: %d webm, %d memes, avatar=%s, character=%s" % (
    n_webm, n_png,
    os.path.isfile(os.path.join(PACK, "config", "nexus-avatar.png")),
    os.path.isfile(os.path.join(PACK, "config", "nexus-character.png"))))
if n_webm != 35:
    errors.append("unexpected webm count: %d" % n_webm)
if n_png != 5:
    errors.append("unexpected meme count: %d" % n_png)

print()
print("ERRORS:", errors if errors else "NONE - bundle is valid")
sys.exit(1 if errors else 0)
