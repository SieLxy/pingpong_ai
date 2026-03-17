import numpy as np


def score_action(confidence: float, stats: dict) -> float:
    jitter = stats.get("mean_std", 0.0)
    raw = confidence * 100.0
    penalty = min(30.0, jitter * 10.0)
    return round(max(0.0, raw - penalty), 2)


def suggestion_for_label(label_name: str):
    tips = {
        "拉": ["保持重心前移，挥拍时肘部稳定", "摩擦球体上部，保证上旋"],
        "削": ["下降期触球，拍形稍后仰", "身体放松，注意小臂发力"],
        "挑": ["近网小幅度爆发，手腕快速前送", "上步及时，重心向前"],
        "挡": ["迎前挡球，拍型微闭合", "用身体移动对准来球"],
        "侧旋": ["转腰带动击球，刷球侧上方", "击球瞬间放松手腕增加旋转"],
    }
    for key, val in tips.items():
        if key in label_name:
            return val
    return ["保持重心稳定，眼睛盯球", "击球后及时回到准备姿势"]

