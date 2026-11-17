# -*- coding: utf-8 -*-
"""
Remove the '蓝毛小女仆' (main) pet and rebrand dsh-pet's shared artwork.

Three icon seats, all package files that dsh-pet serves directly:
  assets/logo.png          /logo  -> settings avatar, tray badge, window/taskbar icon
  assets/pic/notify-*.png  /pic/* -> system notification icons
  (the pet's own avatar comes from pet/<root>-avatar.png, already Nexus)

The main pet is hidden by fixing its `display` to 'none' in the user config
rather than deleting the entry: dsh-pet expects a `main` entry, and removing it
would make the merger fall back to the built-in defaults and bring the maid back.
"""
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

B = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
USER_ROOT = r"C:\Users\Ronin\.dsh\dsh-pet"
DSH_PET = r"C:\Users\Ronin\.dsh\profiles\desktop\node_modules\dsh-pet"
ICON_SRC = os.path.join(B, "assets", "icon")

# ---------- 1. hide the maid: keep the entry, force display=none ------------
cfg_path = os.path.join(USER_ROOT, "main-config.jsonc")
raw = open(cfg_path, encoding="utf-8").read()
cfg = json.loads(raw)

before = None
for pet in cfg.get("pets", []):
    if pet.get("id") == "main":
        before = pet.get("display")
        pet["display"] = "none"
        # Rename it so any UI that still lists it is not misleading.
        pet["name"] = "（已停用）蓝毛小女仆"
print("main pet display:", before, "-> none")

json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(cfg_path, "a", encoding="utf-8").write("\n")

# ---------- 2. replace shared artwork --------------------------------------
pairs = [(os.path.join(ICON_SRC, "logo.png"),
          os.path.join(DSH_PET, "assets", "logo.png"))]
for name in ("notify-done", "notify-error", "notify-truncated",
             "notify-approval", "notify-question", "notify-test"):
    pairs.append((os.path.join(ICON_SRC, name + ".png"),
                  os.path.join(DSH_PET, "assets", "pic", name + ".png")))

for src, dst in pairs:
    if not os.path.isfile(src):
        print("SKIP missing source:", src)
        continue
    backup = dst + ".dsh-nexus-original"
    if not os.path.exists(backup) and os.path.exists(dst):
        shutil.copyfile(dst, backup)
    shutil.copyfile(src, dst)
    print("replaced %-24s %7d bytes" % (os.path.basename(dst), os.path.getsize(dst)))

print("\ndone")
