def calculate_calorie_target(tdee, goal):
    goal = goal.strip().lower().replace(" ", "_")
    calorie_adjustments = {
        "muscle_gain": 300,
        "fat_loss": -500,
        "maintenance": 0
    }
    if goal not in calorie_adjustments:
        raise ValueError(f"Invalid goal: '{goal}'. Expected one of {list(calorie_adjustments.keys())}.")

    return tdee + calorie_adjustments[goal]


def calculate_macros(calorie_target, goal):
    goal = goal.strip().lower().replace(" ", "_")
    macro_splits = {
        "muscle_gain": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
        "fat_loss": {"protein": 0.40, "carbs": 0.30, "fat": 0.30},
        "maintenance": {"protein": 0.30, "carbs": 0.40, "fat": 0.30}
    }
    if goal not in macro_splits:
        raise ValueError(f"Invalid goal: '{goal}'. Expected one of {list(macro_splits.keys())}.")

    split = macro_splits[goal]

    # Protein and carbs = 4 kcal/g, fat = 9 kcal/g
    protein_g = (calorie_target * split["protein"]) / 4
    carbs_g = (calorie_target * split["carbs"]) / 4
    fat_g = (calorie_target * split["fat"]) / 9

    return {
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1)
    }


def get_diet_plan(tdee, goal):
    calorie_target = calculate_calorie_target(tdee, goal)
    macros = calculate_macros(calorie_target, goal)

    return {
        "calorie_target": round(calorie_target),
        "protein_g": macros["protein_g"],
        "carbs_g": macros["carbs_g"],
        "fat_g": macros["fat_g"]
    }