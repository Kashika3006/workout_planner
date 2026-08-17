EXPERIENCE_SPLITS = {
    "beginner": ["full_body", "rest", "full_body", "rest", "full_body", "rest", "rest"],
    "intermediate": ["upper", "lower", "rest", "upper", "lower", "rest", "rest"],
    "advanced": ["push", "pull", "legs", "rest", "push", "pull", "legs"]
}

EXERCISES_BY_DAY_TYPE = {
    "full_body": ["Squat", "Bench Press", "Bent-over Row", "Overhead Press", "Plank"],
    "upper": ["Bench Press", "Bent-over Row", "Overhead Press", "Lat Pulldown", "Bicep Curl"],
    "lower": ["Squat", "Romanian Deadlift", "Leg Press", "Calf Raise", "Lunges"],
    "push": ["Bench Press", "Overhead Press", "Incline Dumbbell Press", "Tricep Pushdown"],
    "pull": ["Deadlift", "Bent-over Row", "Lat Pulldown", "Face Pull", "Bicep Curl"],
    "legs": ["Squat", "Romanian Deadlift", "Leg Press", "Calf Raise"],
    "rest": []
}

REP_SCHEMES = {
    "muscle_gain": {"sets": 4, "reps": "8-12", "rest_seconds": 90},
    "fat_loss": {"sets": 3, "reps": "12-15", "rest_seconds": 45},
    "maintenance": {"sets": 3, "reps": "8-12", "rest_seconds": 60}
}

DAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_workout_split(goal, experience_level):
    goal = goal.strip().lower().replace(" ", "_")
    experience_level = experience_level.strip().lower().replace(" ", "_")

    if goal not in REP_SCHEMES:
        raise ValueError(f"Invalid goal: '{goal}'. Expected one of {list(REP_SCHEMES.keys())}.")
    if experience_level not in EXPERIENCE_SPLITS:
        raise ValueError(
            f"Invalid experience level: '{experience_level}'. "
            f"Expected one of {list(EXPERIENCE_SPLITS.keys())}."
        )

    day_types = EXPERIENCE_SPLITS[experience_level]
    scheme = REP_SCHEMES[goal]

    weekly_plan = {}
    for day_label, day_type in zip(DAY_LABELS, day_types):
        if day_type == "rest":
            weekly_plan[day_label] = {"type": "rest", "exercises": []}
        else:
            weekly_plan[day_label] = {
                "type": day_type,
                "exercises": EXERCISES_BY_DAY_TYPE[day_type],
                "sets": scheme["sets"],
                "reps": scheme["reps"],
                "rest_seconds": scheme["rest_seconds"]
            }

    return weekly_plan

