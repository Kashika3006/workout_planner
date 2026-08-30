"""
Per-exercise rules: which landmarks to track, what angle range counts as
"down" vs "up" for rep counting, and what feedback to give based on the
peak angle reached in a rep.

Thresholds here are starting points based on common coaching cues, not
derived from a dataset - document this honestly in your README. Tune them
by testing against your own recorded reps.

MediaPipe Pose landmark indices used (left side - assumes the camera
mostly sees the person's left side; a real production version would
pick whichever side is more visible per frame):
    LEFT_SHOULDER = 11
    LEFT_ELBOW    = 13
    LEFT_WRIST    = 15
    LEFT_HIP      = 23
    LEFT_KNEE     = 25
    LEFT_ANKLE    = 27
"""

LANDMARKS = {
    "LEFT_SHOULDER": 11,
    "LEFT_ELBOW": 13,
    "LEFT_WRIST": 15,
    "LEFT_HIP": 23,
    "LEFT_KNEE": 25,
    "LEFT_ANKLE": 27,
}

# Each exercise defines:
#   primary_angle: the 3 landmarks (a, b, c) whose angle at b drives rep counting
#   down_threshold: angle (degrees) below which we consider the rep "at the bottom"
#   up_threshold: angle (degrees) above which we consider the rep "at the top"
#   feedback_rules: ordered list of (condition_fn, message) - first match wins
EXERCISE_RULES = {
    "squat": {
        "primary_angle": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"),  # knee angle
        "down_threshold": 100,
        "up_threshold": 160,
        "feedback_rules": [
            (lambda peak_angle: peak_angle > 110, "Shallow depth - try to get your hip crease below knee level."),
            (lambda peak_angle: peak_angle <= 110, "Good depth."),
        ],
    },
    "deadlift": {
        "primary_angle": ("LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE"),  # hip hinge angle
        "down_threshold": 100,
        "up_threshold": 160,
        "feedback_rules": [
            (lambda peak_angle: peak_angle > 120, "Limited hip hinge - you may be squatting the deadlift rather than hinging."),
            (lambda peak_angle: peak_angle <= 120, "Good hip hinge depth."),
        ],
    },
    "push_up": {
        "primary_angle": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"),  # elbow angle
        "down_threshold": 90,
        "up_threshold": 160,
        "feedback_rules": [
            (lambda peak_angle: peak_angle > 100, "Not reaching full depth - aim for elbows near 90 degrees at the bottom."),
            (lambda peak_angle: peak_angle <= 100, "Good depth."),
        ],
    },
}


def get_feedback(exercise_type, peak_angle):
    """Runs the feedback rules for an exercise against the peak angle reached
    in a rep, returns the first matching message."""
    rules = EXERCISE_RULES[exercise_type]["feedback_rules"]
    for condition_fn, message in rules:
        if condition_fn(peak_angle):
            return message
    return "No specific feedback."  # shouldn't normally hit this if rules cover the full range


def get_verdict(exercise_type, peak_angle):
    """Short verdict label (for display/storage), separate from the longer feedback text."""
    down_threshold = EXERCISE_RULES[exercise_type]["down_threshold"]
    if peak_angle <= down_threshold:
        return "good_depth"
    elif peak_angle <= down_threshold + 20:
        return "borderline_depth"
    else:
        return "shallow"