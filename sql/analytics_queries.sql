-- analytics_queries.sql
-- Reference SQL for the workout planner's analytics layer.
-- Replace <demo_user_id> with the actual user_id before running in Workbench.
-- These are wrapped in Python functions in modules/analytics.py — this file
-- is the readable, standalone reference version for documentation/portfolio.


-- ============================================================
-- 1. Weekly adherence: how many days logged + workouts completed per week
-- ============================================================
SELECT
    YEARWEEK(log_date) AS week,
    COUNT(*) AS days_logged,
    SUM(workout_completed) AS workouts_completed,
    ROUND(SUM(workout_completed) / COUNT(*) * 100, 1) AS adherence_pct
FROM daily_logs
WHERE user_id = <demo_user_id>
GROUP BY YEARWEEK(log_date)
ORDER BY week;


-- ============================================================
-- 2. 7-day rolling average weight (smooths daily noise into a trend)
-- ============================================================
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
WHERE user_id = <demo_user_id>
ORDER BY log_date;


-- ============================================================
-- 3. Weekly activity + intake: total steps and average calories per week
-- ============================================================
SELECT
    YEARWEEK(log_date) AS week,
    SUM(steps_walked) AS total_steps,
    ROUND(AVG(calories_consumed), 0) AS avg_calories
FROM daily_logs
WHERE user_id = <demo_user_id>
GROUP BY YEARWEEK(log_date)
ORDER BY week;