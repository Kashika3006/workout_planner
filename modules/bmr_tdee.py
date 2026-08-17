def calculate_bmr(weight_kg, height_cm, age, gender):
    gender = gender.strip().lower()
    if gender not in ("male", "female"):
        raise ValueError(f"Invalid gender: '{gender}'. Expected 'male' or 'female'.")

    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return bmr

def calculate_tdee(bmr, activity_level):
    activity_multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    activity_level = activity_level.strip().lower().replace(" ", "_")
    if activity_level not in activity_multipliers:
        raise ValueError(
            f"Invalid activity level: '{activity_level}'. "
            f"Expected one of {list(activity_multipliers.keys())}."
        )
    return bmr * activity_multipliers[activity_level]  # Default to sedentary if activity level is not recognized

def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return bmi