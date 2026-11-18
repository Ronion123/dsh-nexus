# -*- coding: utf-8 -*-
"""Generate the blue-form pet pack config from the red one.

The blue form is a SEPARATE pet instance (nexus-blue) that stays hidden until the
red form plays its form-shift clip. Keeping it a separate instance is deliberate:
dsh-pet resolves asset root from the config FILENAME prefix, so a single pet
cannot swap art sets at runtime. Two instances plus a timed hand-off give the
same visible result — the shift animation finishes, then blue stands in place.
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
B = r"C:\Users\Ronin\Desktop\桌宠设计\dsh-nexus"
CFG_DIR = os.path.join(B, "pet-pack", "config")

red = json.load(open(os.path.join(CFG_DIR, "nexus-config.json"), encoding="utf-8"))

blue = {
    "whisperPrompt": red["whisperPrompt"],
    "memes": {
        "蓝奈-站立": "蓝色青年形态站姿，沉稳待命",
        "蓝奈-战斗": "蓝色青年形态战斗架势，迎战",
        "蓝奈-必杀光线": "蓝色青年形态放出必杀光线",
        "蓝奈-必杀弓箭": "蓝色青年形态拉弓射出光箭，适合全力一击",
        "蓝奈-飞行": "蓝色青年形态疾飞巡航",
    },
    "workStatusTexts": red["workStatusTexts"],
    "sleepRefuseTexts": red["sleepRefuseTexts"],
    "sleepStartTexts": red["sleepStartTexts"],
    "sleepEndTexts": red["sleepEndTexts"],
    "chatAnimationEnabled": red["chatAnimationEnabled"],
    "chatImageEnabled": red["chatImageEnabled"],
    "whisperImageEnabled": red["whisperImageEnabled"],
    "chatImageLimit": red["chatImageLimit"],
    "pets": [
        {
            "id": "nexus-blue",
            "name": "奈克赛斯·蓝色青年",
            "size": 462,
            "balanceEnabled": True,
            "whisperEnabled": True,
            "workStatusEnabled": True,
            "fixedEnabled": False,
            # Hidden until the red form's shift animation completes.
            "display": "none",
            "position": {
                "corner": "bottom-right",
                "marginX": 28,
                "marginY": 96,
            },
        }
    ],
    "animations": {
        "idle": ["蓝奈-待机-呼吸循环"],
        "turn": ["蓝奈-转向-回身"],
        "drag": ["蓝奈-拖拽-飞行向左", "蓝奈-拖拽-飞行向右"],
        "clicks": ["蓝奈-点击-光束", "蓝奈-点击-迎击", "蓝奈-点击-弓箭"],
        "moves": {
            "default": {"minDist": 60, "maxDist": 240, "margin": 20, "leadSec": 2, "tailSec": 2},
            "actions": [
                {"name": "蓝奈-移动-飞行巡航",
                 "params": {"minDist": 100, "maxDist": 320, "leadSec": 1.5, "tailSec": 3}}
            ],
        },
        "categories": [
            {
                "id": "蓝奈·九式连招",
                "weight": 58,
                "actions": [
                    "蓝奈-起手式", "蓝奈-连击式", "蓝奈-展开式", "蓝奈-横击式",
                    "蓝奈-蓄势式", "蓝奈-爆发式", "蓝奈-回旋式", "蓝奈-疾飞式",
                    "蓝奈-展翼式",
                ],
            },
            {
                "id": "蓝奈·形态",
                "weight": 24,
                # No form-shift clip: blue cannot return to red.
                "actions": [
                    "蓝奈-形态-站立", "蓝奈-形态-战斗", "蓝奈-形态-必杀光线",
                    "蓝奈-形态-必杀弓箭", "蓝奈-形态-飞行",
                ],
            },
            {"id": "蓝奈·光之动作", "weight": 8, "actions": ["蓝奈-待机-呼吸循环", "蓝奈-点击-光束"]},
            {"id": "蓝奈·飞行", "weight": 0,
             "actions": ["蓝奈-拖拽-飞行向左", "蓝奈-拖拽-飞行向右"]},
        ],
        "events": {
            "balance": [
                "蓝奈-余额-充足", "蓝奈-余额-充足", "蓝奈-余额-正常",
                "蓝奈-余额-正常", "蓝奈-余额-告急", "蓝奈-余额-耗尽",
            ],
            "whisper": ["蓝奈-碎碎念"],
            "workStatus": [
                "蓝奈-思考", "蓝奈-忙碌", "蓝奈-清点归档",
                "蓝奈-踱步张望", "蓝奈-雀跃庆祝", "蓝奈-垂头叹气",
            ],
        },
        "sleep": [{"start": ["蓝奈-入睡"], "loop": ["蓝奈-睡觉循环"], "end": ["蓝奈-醒来"]}],
    },
    "animationWeights": {"idle": 10, "turn": 0, "move": 0},
}

out = os.path.join(CFG_DIR, "nexus-blue-config.json")
json.dump(blue, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(out, "a", encoding="utf-8").write("\n")
print("wrote", os.path.basename(out))
print("blue pet id:", blue["pets"][0]["id"], "| display:", blue["pets"][0]["display"])
print("categories:", [(c["id"], c["weight"]) for c in blue["animations"]["categories"]])
print("weight total:", sum(blue["animationWeights"].values())
      + sum(c["weight"] for c in blue["animations"]["categories"]))
