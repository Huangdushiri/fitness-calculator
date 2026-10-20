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


# 碳循环：碳水/脂肪在高/中/低碳日之间的相对比例（以中碳日为 1）
CARB_RATIOS = {"高碳日": 50 / 35, "中碳日": 1.0, "低碳日": 15 / 35}
FAT_RATIOS = {"高碳日": 15 / 35, "中碳日": 1.0, "低碳日": 50 / 35}

# 每周各类日的天数：2 高碳日、3 中碳日、2 低碳日
CARB_CYCLE_COUNTS = {"高碳日": 2, "中碳日": 3, "低碳日": 2}


def _week_norm(ratios):
    """归一化系数：使一周（7 天）各类日加权总量 = 7 × 每日基准值。

    输入的倍数代表「每日平均摄入」，因此一周总量应精确等于 7 × 倍数 × 体重。
    """
    total_units = sum(CARB_CYCLE_COUNTS[d] * ratios[d] for d in CARB_CYCLE_COUNTS)
    return 7 / total_units


def carb_cycling(weight_kg, carbs_g_per_kg, protein_g_per_kg, fat_g_per_kg):
    """碳循环饮食计划。

    输入碳水 / 蛋白质 / 脂肪的体重倍数（g/kg），它们代表「每日平均摄入」：
        每日平均 = 倍数 × 体重
    每周 2 高碳日 + 3 中碳日 + 2 低碳日，碳水与脂肪按固定比例分配到各天，
    使一周总量精确等于 7 × 倍数 × 体重；蛋白质三种日恒定。

    碳水  高碳日 : 中碳日 : 低碳日 = 50% : 35% : 15%
    脂肪  高碳日 : 中碳日 : 低碳日 = 15% : 35% : 50%

    返回 (daily, weekly)，其中 daily 为各类日的字典，weekly 为每周合计。
    """
    protein = protein_g_per_kg * weight_kg
    carbs_mid = carbs_g_per_kg * weight_kg * _week_norm(CARB_RATIOS)
    fat_mid = fat_g_per_kg * weight_kg * _week_norm(FAT_RATIOS)

    daily = {}
    for name in CARB_CYCLE_COUNTS:
        carbs = carbs_mid * CARB_RATIOS[name]
        fat = fat_mid * FAT_RATIOS[name]
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
