# -*- coding: utf-8 -*-
"""所有计算逻辑：基础代谢、食物热量、碳水渐降(5:3:2)、碳循环。

本文件不依赖图形界面，可单独测试。
"""


def bmr(gender, weight_kg, height_cm, age):
    """基础代谢（Mifflin-St Jeor 公式）。

    男性：10×体重 + 6.25×身高 − 5×年龄 + 5
    女性：10×体重 + 6.25×身高 − 5×年龄 − 161
    """
    if gender == "男":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def food_nutrition(weight_g, carbs_per100, protein_per100, fat_per100):
    """根据食物重量（克）与每 100g 营养含量，计算热量与三大营养素。

    返回 (热量kcal, 碳水g, 蛋白质g, 脂肪g)。
    """
    factor = weight_g / 100.0
    carbs = carbs_per100 * factor
    protein = protein_per100 * factor
    fat = fat_per100 * factor
    kcal = 4 * carbs + 4 * protein + 9 * fat
    return kcal, carbs, protein, fat


def split_532(total_kcal):
    """碳水渐降（5:3:2）：按热量占比 碳水:蛋白:脂肪 = 0.5:0.3:0.2。

    返回 (碳水g, 蛋白质g, 脂肪g)。
    """
    carbs = total_kcal * 0.5 / 4
    protein = total_kcal * 0.3 / 4
    fat = total_kcal * 0.2 / 9
    return carbs, protein, fat


# 每周各类日的天数：2 高碳日、3 中碳日、2 低碳日
CARB_CYCLE_COUNTS = {"高碳日": 2, "中碳日": 3, "低碳日": 2}

# 碳水/脂肪每周总量在各天之间的占比
CARB_SHARES = {"高碳日": 0.5, "中碳日": 0.35, "低碳日": 0.15}
FAT_SHARES = {"高碳日": 0.15, "中碳日": 0.35, "低碳日": 0.5}


def carb_cycling(weight_kg, carbs_g_per_kg, protein_g_per_kg, fat_g_per_kg):
    """碳循环饮食计划。

    输入碳水 / 蛋白质 / 脂肪的体重倍数（g/kg），它们代表「每日平均摄入」：
    每周 2 高碳日 + 3 中碳日 + 2 低碳日。每周碳水/脂肪总量 = 7 × 倍数 × 体重，
    再按占比分配到各类日：每日 = 体重 × 倍数 × 7 × 占比 / 该类日天数。

    碳水  高碳日 : 中碳日 : 低碳日 = 50% : 35% : 15%
    脂肪  高碳日 : 中碳日 : 低碳日 = 15% : 35% : 50%

    蛋白质三种日恒定（= 倍数 × 体重）。

    返回 (daily, weekly)，其中 daily 为各类日的字典，weekly 为每周合计。
    """
    protein = protein_g_per_kg * weight_kg

    daily = {}
    for name in CARB_CYCLE_COUNTS:
        count = CARB_CYCLE_COUNTS[name]
        carbs = carbs_g_per_kg * weight_kg * 7 * CARB_SHARES[name] / count
        fat = fat_g_per_kg * weight_kg * 7 * FAT_SHARES[name] / count
        total_kcal = 4 * carbs + 4 * protein + 9 * fat
        daily[name] = {
            "total_kcal": total_kcal,
            "carbs": carbs,
            "protein": protein,
            "fat": fat,
        }

    weekly = {"total_kcal": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0}
    for name, count in CARB_CYCLE_COUNTS.items():
        d = daily[name]
        weekly["total_kcal"] += d["total_kcal"] * count
        weekly["carbs"] += d["carbs"] * count
        weekly["protein"] += d["protein"] * count
        weekly["fat"] += d["fat"] * count

    return daily, weekly
