"""
Form checker - processes an uploaded video, runs MediaPipe pose estimation
per frame, calculates the relevant joint angle for the given exercise, and
counts reps via a simple state machine (angle crosses "down" threshold,
then back "up" = one rep).

Start with squat only when testing - get the full pipeline working end to
end on one exercise before trusting it on deadlift/push-up.
"""

import math
import cv2
import mediapipe as mp

from modules.exercise_rules import EXERCISE_RULES, LANDMARKS, get_feedback, get_verdict

mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    """Angle at point b, formed by points a-b-c, in degrees (0-180).
    Each point is a (x, y) tuple. Uses the standard atan2-difference method:
    the angle between vector b->a and vector b->c."""
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) -
        math.atan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle


def extract_landmark_coords(pose_landmarks, landmark_name):
    """Pulls (x, y) for one named landmark out of a MediaPipe pose result.
    Coordinates are normalized (0-1 relative to frame size) - fine for angle
    calculation since angles are scale-invariant."""
    idx = LANDMARKS[landmark_name]
    lm = pose_landmarks.landmark[idx]
    return (lm.x, lm.y)


def process_video(video_path, exercise_type, frame_skip=1):
    """Runs the full pipeline on an uploaded video.

    Args:
        video_path: path to the uploaded video file
        exercise_type: one of 'squat', 'deadlift', 'push_up'
        frame_skip: process every Nth frame (1 = every frame; raise this
            for faster processing on long videos at some cost to precision)

    Returns:
        list of dicts, one per detected rep:
        {"rep_number": int, "peak_angle": float, "verdict": str, "feedback": str}
    """
    if exercise_type not in EXERCISE_RULES:
        raise ValueError(f"Unknown exercise_type: '{exercise_type}'. Expected one of {list(EXERCISE_RULES.keys())}.")

    rules = EXERCISE_RULES[exercise_type]
    point_a_name, point_b_name, point_c_name = rules["primary_angle"]
    down_threshold = rules["down_threshold"]
    up_threshold = rules["up_threshold"]

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")

    results_log = []
    rep_count = 0
    stage = "up"           # tracks whether we're currently in the "up" or "down" phase
    current_rep_peak = None  # most extreme (smallest) angle seen during the current "down" phase

    frame_index = 0

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break  # end of video

            frame_index += 1
            if frame_index % frame_skip != 0:
                continue

            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pose_result = pose.process(image_rgb)

            if pose_result.pose_landmarks is None:
                continue  # person not detected in this frame, skip it

            landmarks = pose_result.pose_landmarks
            try:
                point_a = extract_landmark_coords(landmarks, point_a_name)
                point_b = extract_landmark_coords(landmarks, point_b_name)
                point_c = extract_landmark_coords(landmarks, point_c_name)
            except (IndexError, KeyError):
                continue  # a required landmark wasn't detected this frame

            angle = calculate_angle(point_a, point_b, point_c)

            # --- Rep counting state machine ---
            if stage == "up" and angle < down_threshold:
                stage = "down"
                current_rep_peak = angle
            elif stage == "down":
                if current_rep_peak is None or angle < current_rep_peak:
                    current_rep_peak = angle  # track the deepest point reached
                if angle > up_threshold:
                    # Completed a full down-then-up cycle = one rep
                    rep_count += 1
                    feedback = get_feedback(exercise_type, current_rep_peak)
                    verdict = get_verdict(exercise_type, current_rep_peak)
                    results_log.append({
                        "rep_number": rep_count,
                        "peak_angle": round(current_rep_peak, 1),
                        "verdict": verdict,
                        "feedback": feedback
                    })
                    stage = "up"
                    current_rep_peak = None

    cap.release()
    return results_log