"""
Analytics layer - wraps the SQL queries from sql/analytics_queries.sql
into Python functions that return pandas DataFrames, ready for further
analysis (e.g. correlation) or for feeding a dashboard.
"""

import pandas as pd
from modules.database import get_connection


def get_weekly_adherence(user_id):
    """Returns a DataFrame: week, days_logged, workouts_completed, adherence_pct."""
    query = """
        SELECT
            YEARWEEK(log_date) AS week,
            COUNT(*) AS days_logged,
            SUM(workout_completed) AS workouts_completed,
            ROUND(SUM(workout_completed) / COUNT(*) * 100, 1) AS adherence_pct
        FROM daily_logs
        WHERE user_id = %s
        GROUP BY YEARWEEK(log_date)
        ORDER BY week
    """
    connection = get_connection()
    try:
        return pd.read_sql(query, connection, params=(user_id,))
    finally:
        connection.close()


def get_rolling_weight_trend(user_id):
    """Returns a DataFrame: log_date, weight_kg, rolling_7day_avg."""
    query = """
        SELECT
            log_date,
            weight_kg,
            ROUND(
                AVG(weight_kg) OVER (
                    ORDER BY log_date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ), 2
            ) AS rolling_7day_avg
        FROM daily_logs
        WHERE user_id = %s
        ORDER BY log_date
    """
    connection = get_connection()
    try:
        return pd.read_sql(query, connection, params=(user_id,))
    finally:
        connection.close()


def get_weekly_activity(user_id):
    """Returns a DataFrame: week, total_steps, avg_calories."""
    query = """
        SELECT
            YEARWEEK(log_date) AS week,
            SUM(steps_walked) AS total_steps,
            ROUND(AVG(calories_consumed), 0) AS avg_calories
        FROM daily_logs
        WHERE user_id = %s
        GROUP BY YEARWEEK(log_date)
        ORDER BY week
    """
    connection = get_connection()
    try:
        return pd.read_sql(query, connection, params=(user_id,))
    finally:
        connection.close()

def get_weight_history(user_id):
    """Returns raw (log_date, weight_kg) pairs, ascending by date, with nulls
    dropped. This is the plain history Prophet needs as input - not the
    rolling average, which is a derived/smoothed view for a different purpose."""
    query = """
        SELECT log_date, weight_kg
        FROM daily_logs
        WHERE user_id = %s AND weight_kg IS NOT NULL
        ORDER BY log_date ASC
    """
    connection = get_connection()
    try:
        return pd.read_sql(query, connection, params=(user_id,))
    finally:
        connection.close()
 