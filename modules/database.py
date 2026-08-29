import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import json

load_dotenv()


def get_connection():
    """Opens a new MySQL connection using credentials from environment variables.
    Caller is responsible for closing it (use in a try/finally or context manager)."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "workout_planner_db"),
            use_pure=True
        )
        return connection
    except Error as e:
        raise ConnectionError(f"Failed to connect to MySQL: {e}")


def insert_user(name, age, gender, height_cm, weight_kg, activity_level, goal, dietary_pref=None):
    """Inserts a new user and returns the new user_id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO users (name, age, gender, height_cm, weight_kg, activity_level, goal, dietary_pref)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, age, gender, height_cm, weight_kg, activity_level, goal, dietary_pref))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def insert_daily_log(user_id, log_date, weight_kg=None, calories_consumed=None,
                      protein_g=None, carbs_g=None, fat_g=None,
                      workout_completed=False, notes=None, steps_walked=None):
    """Inserts one daily log entry. Relies on the unique_user_date constraint
    to prevent duplicate entries for the same user+date."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO daily_logs
                (user_id, log_date, weight_kg, calories_consumed, protein_g, carbs_g, fat_g,
                 workout_completed, notes, steps_walked)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, log_date, weight_kg, calories_consumed,
                                protein_g, carbs_g, fat_g, workout_completed, notes, steps_walked))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def get_user_by_id(user_id):
    """Returns a single user as a dict, or None if not found."""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def get_logs_for_user(user_id, limit=None):
    """Returns all daily_logs rows for a user, most recent first.
    Optional limit for pagination/recent-only queries."""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM daily_logs WHERE user_id = %s ORDER BY log_date DESC"
        params = [user_id]
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def insert_plan(user_id, calorie_target, protein_target, carb_target, fat_target, workout_split):
    """Saves a generated plan. workout_split is a dict — stored as JSON."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO plans (user_id, calorie_target, protein_target, carb_target, fat_target, workout_split)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            user_id, calorie_target, protein_target, carb_target, fat_target,
            json.dumps(workout_split)
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def get_latest_plan(user_id):
    """Returns the most recently created plan for a user, with workout_split
    parsed back into a dict. Returns None if the user has no plan yet."""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM plans WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        plan = cursor.fetchone()
        if plan and plan.get("workout_split"):
            plan["workout_split"] = json.loads(plan["workout_split"])
        return plan
    finally:
        cursor.close()
        connection.close()


def insert_form_check(user_id, exercise_type, rep_number, peak_angle, verdict, feedback, session_id=None):
    """Saves the result of one detected rep from the form checker."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO form_checks (user_id, session_id, exercise_type, rep_number, peak_angle, verdict, feedback)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, session_id, exercise_type, rep_number, peak_angle, verdict, feedback))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()