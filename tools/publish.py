# -*- coding: utf-8 -*-
"""
Publish helper for dsh-nexus.

Reads the GitHub owner and npm scope from publish.config.json, fills the
placeholders in every manifest, validates the bundle, and writes the format-1
plugin market index used by DSH's Discover tab.

Usage:
    python tools/publish.py --scope your-npm-name --owner your-github-name
    python tools/publish.py --check        # validate only, change nothing

Nothing here logs you in to npm or contacts GitHub: authentication stays yours.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

BUNDLE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(BUNDLE, "publish.config.json")
PLACEHOLDER = "PLACEHOLDER"

# Live publication facts for this repository. The index URL pins a tag so its
# contents never change under users' feet; bump TAG when publishing a release.
REPO = "https://github.com/Ronion123/dsh-nexus"
TAG = "v1.0.0"
INDEX_URL = "https://raw.githubusercontent.com/Ronion123/dsh-nexus/%s/site/index.json" % TAG

# Files that carry the two placeholders.
TEXT_FILES = [
    "package.json",
    "README.md",
    "locale/en.json",
    "locale/zh.json",
]


def load_config():
    if os.path.isfile(CONFIG):
        with open(CONFIG, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def substitute(scope, owner, write=True):
    """Replace the placeholders in every manifest that carries them."""
    changed = []
    for rel in TEXT_FILES:
        path = os.path.join(BUNDLE, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new = text.replace("@" + PLACEHOLDER + "/", "@" + scope + "/")
        new = new.replace("github.com/" + PLACEHOLDER + "/", "github.com/" + owner + "/")
        new = new.replace(PLACEHOLDER + "/dsh-nexus", owner + "/dsh-nexus")
        if new != text:
            changed.append(rel)
            if write:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
    return changed


def unresolved():
    """Return files that still contain the placeholder."""
    hits = []
    for rel in TEXT_FILES:
        path = os.path.join(BUNDLE, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            if PLACEHOLDER in fh.read():
                hits.append(rel)
    return hits


def run(cmd, cwd=BUNDLE, check=True):
    print("$ " + " ".join(cmd))
    # npm on Windows is a .cmd shim; capture_output with text mode can yield None
    # stdout on some shells, so normalize both streams.
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=False,
                            encoding="utf-8", errors="replace")
    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    if out:
        print(out)
    if err:
        print(err)
    if check and result.returncode != 0:
        raise SystemExit("command failed: " + " ".join(cmd))
    return result


def npm_pack_dry_run():
    """Ask npm what would actually be published; catches missing files."""
    npm = shutil_which("npm.cmd") or shutil_which("npm")
    if not npm:
        print("! npm not found on PATH - skipping pack check")
        return
    result = run([npm, "pack", "--dry-run", "--json"], check=False)
    if result.returncode != 0:
        print("! npm pack --dry-run failed")
        return
    try:
        data = json.loads(result.stdout)
    except ValueError:
        print("! could not parse npm pack output")
        return
    if not data:
        return
    files = data[0].get("files", [])
    names = [f["path"] for f in files]
    print("npm would publish %d files, %.2f MB" %
          (len(names), sum(f.get("size", 0) for f in files) / 1048576.0))
    must = ["index.js", "cordis.patch.yml", "icon.svg", "LICENSE",
            "locale/en.json", "locale/zh.json", "docs/DETAIL.md",
            "docs/DETAIL.zh.md", "docs/preview.svg",
            "pet-pack/config/nexus-config.json"]
    missing = [m for m in must if m not in names]
    if missing:
        print("! MISSING from package: " + ", ".join(missing))
    else:
        print("all required files are in the package")
    webm = [n for n in names if n.endswith(".webm")]
    print("animation clips in package:", len(webm))


def shutil_which(name):
    from shutil import which
    return which(name)


def build_index():
    """Write the format-1 market index and its icon into site/."""
    pkg = json.load(open(os.path.join(BUNDLE, "package.json"), encoding="utf-8"))
    site = os.path.join(BUNDLE, "site")
    icons = os.path.join(site, "icons")
    os.makedirs(icons, exist_ok=True)

    # Copy the icon beside the index so a relative reference resolves.
    icon_src = os.path.join(BUNDLE, "icon.svg")
    icon_dst = os.path.join(icons, "dsh-nexus.svg")
    with open(icon_src, "rb") as src, open(icon_dst, "wb") as dst:
        dst.write(src.read())

    version = pkg["version"]
    index = {
        "format": 1,
        "title": {"en": "Ronin's DSH pets", "zh": "Ronin 的 DSH 桌宠"},
        "description": {
            "en": "Character packs for the DeepSeek Harness desktop pet.",
            "zh": "DeepSeek Harness 桌宠角色包。",
        },
        "metadata": {
            "categories": {
                "pet": {"title": {"en": "Desktop pets", "zh": "桌宠"}},
            },
            "labels": {
                "open-source": {"title": {"en": "Open source", "zh": "开源"}},
                "chinese": {"title": {"en": "Chinese UI", "zh": "中文界面"}},
            },
            "sortKeys": {},
        },
        "plugins": [
            {
                "name": pkg["name"],
                "title": {"en": "Nexus pet", "zh": "奈克赛斯桌宠"},
                "description": {
                    "en": "A chibi Ultraman Nexus desktop pet for dsh-pet, built from "
                          "a 12-frame transparent loop animation, a nine-pose action sheet, "
                          "and five pose illustrations. Installs as a dsh-pet character pack; "
                          "requires dsh-pet to be enabled.",
                    "zh": "Q 版奥特战士奈克赛斯桌宠，由 12 帧透明循环动画、九格动作组与五张姿势立绘组成。"
                          "作为 dsh-pet 种类包安装，需要先启用 dsh-pet。",
                },
                "icon": "icons/dsh-nexus.svg",
                "author": pkg.get("author", ""),
                "homepage": pkg.get("homepage", ""),
                "repository": {
                    "url": (pkg.get("repository", {}).get("url", "")
                            .replace("git+", "").replace(".git", "")),
                },
                "metadata": {
                    "category": "pet",
                    "keywords": pkg.get("keywords", []),
                    "labels": ["open-source", "chinese"],
                    "sortKeys": {},
                },
                "versions": [
                    {
                        "version": version,
                        "publishTimestamp": 0,  # filled by finalize_index()
                        "source": {"type": "npm"},
                        "engines": {"dsh": ">=0.2.0-rc.1"},
                    }
                ],
            }
        ],
    }
    out = os.path.join(site, "index.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("wrote", out)
    print("wrote", icon_dst)
    return out


def validate_index(path):
    """Validate with DSH's own parser when it can be required."""
    validator = None
    candidates = [
        "C:/Ronin/software/DeepSeek Harness/resources/app.asar/dsh/node_modules/"
        "@deepseek-ai/dsh-plugin-market-index/lib/index.js",
    ]
    for c in candidates:
        if os.path.isfile(c):
            validator = c
            break
    if validator is None:
        print("! validator not found - index written but not verified")
        return False
    script = (
        "const m = require(process.argv[1]);"
        "const fs = require('node:fs');"
        "const raw = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));"
        "const out = m.parseMarketIndex(raw, 'https://example.invalid/index.json');"
        "console.log('validated plugins:', out.plugins.length);"
        "console.log('names:', out.plugins.map(p => p.name).join(', '));"
        "console.log('versions:', out.plugins[0].versions.map(v => v.version).join(', '));"
        "console.log('icon resolved:', out.plugins[0].icon);"
    )
    exe = "C:/Ronin/software/DeepSeek Harness/DeepSeek Harness.exe"
    env = dict(os.environ, ELECTRON_RUN_AS_NODE="1")
    result = subprocess.run([exe, "-e", script, validator, path],
                            capture_output=True, text=True, env=env)
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip())
    return result.returncode == 0


def finalize_index(publish_timestamp=None):
    """Set the real publish timestamp so the index matches what npm recorded."""
    path = os.path.join(BUNDLE, "site", "index.json")
    if not os.path.isfile(path):
        return
    import time
    data = json.load(open(path, encoding="utf-8"))
    ts = publish_timestamp or int(time.time())
    for plugin in data["plugins"]:
        for version in plugin["versions"]:
            if not version["publishTimestamp"]:
                version["publishTimestamp"] = ts
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("publishTimestamp set to", ts)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", help="npm user or org name used as the package scope")
    ap.add_argument("--owner", help="GitHub owner name for homepage and repository URLs")
    ap.add_argument("--check", action="store_true", help="validate only; change nothing")
    ap.add_argument("--index-only", action="store_true", help="rebuild the market index only")
    args = ap.parse_args()

    cfg = load_config()

    if args.check:
        hits = unresolved()
        print("unresolved placeholders:", hits or "none")
        run([sys.executable, os.path.join(BUNDLE, "tools", "validate_bundle.py")],
            check=False)
        run([sys.executable, os.path.join(BUNDLE, "tools", "validate_pack.py")],
            check=False)
        npm_pack_dry_run()
        return 0 if not hits else 1

    if args.index_only:
        build_index()
        finalize_index()
        validate_index(os.path.join(BUNDLE, "site", "index.json"))
        return 0

    scope = args.scope or cfg.get("scope")
    owner = args.owner or cfg.get("owner")
    if not scope or not owner:
        print("need --scope and --owner (or set them in publish.config.json)")
        return 2

    cfg.update({"scope": scope, "owner": owner})
    save_config(cfg)

    changed = substitute(scope, owner)
    print("substituted placeholders in:", changed or "nothing (already set)")
    hits = unresolved()
    if hits:
        print("! still unresolved in:", hits)
        return 1

    run([sys.executable, os.path.join(BUNDLE, "tools", "validate_bundle.py")])
    run([sys.executable, os.path.join(BUNDLE, "tools", "validate_pack.py")])
    npm_pack_dry_run()

    build_index()
    finalize_index()
    validate_index(os.path.join(BUNDLE, "site", "index.json"))

    print("\nNext steps (they need your credentials, so they are not automated):")
    print("  cd " + BUNDLE)
    print("  npm login")
    print("  npm publish --access public")
    print("  git add . && git commit -m 'chore: release' && git push")
    print("  git tag -a %s -m 'release' && git push origin %s" % (TAG, TAG))
    print("\nIndex URL (pin a tag; bump TAG in this script for the next release):")
    print("  " + INDEX_URL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
