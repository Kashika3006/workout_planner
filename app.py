"""
Main Flask application. Wires together:
  modules/bmr_tdee.py, diet_logic.py, workout_logic.py  -> plan generation
  modules/database.py                                    -> persistence
  modules/analytics.py                                    -> dashboard charts

Run with: python app.py
Then visit http://localhost:5000
"""

import os
from flask import send_file
from werkzeug.utils import secure_filename
from modules.forecasting import fit_and_forecast, generate_forecast_chart, get_forecast_summary
from modules.form_checker import process_video
from modules.database import insert_form_check
from modules.pdf_generator import generate_pdf_report

from flask import Flask, render_template, request, redirect, url_for, flash
from modules.database import (
        insert_user, insert_plan, get_user_by_id, get_latest_plan,
        get_logs_for_user, find_user_by_name
    )
from modules.bmr_tdee import calculate_bmr, calculate_tdee, calculate_bmi
from modules.diet_logic import get_diet_plan
from modules.workout_logic import get_workout_split
from modules.database import insert_user, insert_plan, get_user_by_id, get_latest_plan, get_logs_for_user
from modules.analytics import get_weekly_adherence, get_rolling_weight_trend, get_weekly_activity

app = Flask(__name__)
app.secret_key = "dev-only-change-this-before-any-real-deployment"  # fine for local dev, not for production

 
UPLOAD_FOLDER = "uploads_temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
 

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if request.method == "GET":
        return render_template("onboarding.html")

    # POST - form submitted
    try:
        name = request.form["name"]
        age = int(request.form["age"])
        gender = request.form["gender"]
        height_cm = float(request.form["height_cm"])
        weight_kg = float(request.form["weight_kg"])
        activity_level = request.form["activity_level"]
        goal = request.form["goal"]
        experience_level = request.form["experience_level"]
        dietary_pref = request.form.get("dietary_pref") or None

        # Run the core planner pipeline - this is the same logic
        # your master_test.ipynb Part 1 already validated.
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = calculate_tdee(bmr, activity_level)
        diet_plan = get_diet_plan(tdee, goal)
        workout_split = get_workout_split(goal, experience_level)

        # Persist: create the user, then save their generated plan
        user_id = insert_user(
            name=name, age=age, gender=gender, height_cm=height_cm, weight_kg=weight_kg,
            activity_level=activity_level, goal=goal, dietary_pref=dietary_pref
        )
        insert_plan(
            user_id=user_id,
            calorie_target=diet_plan["calorie_target"],
            protein_target=diet_plan["protein_g"],
            carb_target=diet_plan["carbs_g"],
            fat_target=diet_plan["fat_g"],
            workout_split=workout_split
        )

        return redirect(url_for("dashboard", user_id=user_id))

    except (ValueError, KeyError) as e:
        # ValueError comes from your modules' validation (bad gender/goal/etc)
        # KeyError means a form field was missing entirely
        flash(f"Something was invalid in that form: {e}")
        return redirect(url_for("onboarding"))


@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash("No user found with that ID.")
        return redirect(url_for("home"))

    plan = get_latest_plan(user_id)
    recent_logs = get_logs_for_user(user_id, limit=10)

    # Analytics - only meaningful once a user has several days of logs.
    # For a brand-new user (no logs yet), these will just return empty data,
    # which the template handles by showing a "no data yet" message.
    try:
        adherence_df = get_weekly_adherence(user_id)
        adherence_data = adherence_df.to_dict(orient="records")
    except Exception:
        adherence_data = []

    try:
        rolling_df = get_rolling_weight_trend(user_id)
        weight_trend_data = rolling_df.to_dict(orient="records")
    except Exception:
        weight_trend_data = []

    return render_template(
        "dashboard.html",
        user=user,
        plan=plan,
        recent_logs=recent_logs,
        adherence_data=adherence_data,
        weight_trend_data=weight_trend_data
    )

@app.route("/forecast/<int:user_id>")
def forecast(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash("No user found with that ID.")
        return redirect(url_for("home"))
 
    try:
        model, forecast_df = fit_and_forecast(user_id, periods_days=28)
        summary_text = get_forecast_summary(forecast_df)
 
        # Save the chart as a static image the template can display
        chart_path = f"static/forecasts/{user_id}.png"
        os.makedirs("static/forecasts", exist_ok=True)
        generate_forecast_chart(model, forecast_df, save_path=chart_path)
 
        return render_template(
            "forecast.html",
            user=user,
            summary=summary_text,
            chart_url=url_for("static", filename=f"forecasts/{user_id}.png")
        )
 
    except ValueError as e:
        # Raised when there's under 14 days of weight history
        return render_template("forecast.html", user=user, summary=None, error=str(e))
 
 
@app.route("/form-check/<int:user_id>", methods=["GET", "POST"])
def form_check(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash("No user found with that ID.")
        return redirect(url_for("home"))
 
    if request.method == "GET":
        return render_template("form_check.html", user=user, results=None)
 
    # POST - video uploaded
    video_file = request.files.get("video")
    exercise_type = request.form.get("exercise_type")
 
    if not video_file or video_file.filename == "":
        flash("No video file selected.")
        return redirect(url_for("form_check", user_id=user_id))
 
    filename = secure_filename(video_file.filename)
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video_file.save(video_path)
 
    try:
        results = process_video(video_path, exercise_type=exercise_type, frame_skip=2)
 
        # Save each rep's result to the database
        for rep in results:
            insert_form_check(
                user_id=user_id,
                exercise_type=exercise_type,
                rep_number=rep["rep_number"],
                peak_angle=rep["peak_angle"],
                verdict=rep["verdict"],
                feedback=rep["feedback"]
            )
 
        return render_template("form_check.html", user=user, results=results, exercise_type=exercise_type)
 
    finally:
        # Clean up the uploaded video file regardless of success/failure -
        # don't let temp video files pile up on disk
        if os.path.exists(video_path):
            os.remove(video_path)
 
 
@app.route("/report/<int:user_id>")
def report(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash("No user found with that ID.")
        return redirect(url_for("home"))
 
    os.makedirs("static/reports", exist_ok=True)
    output_path = f"static/reports/report_{user_id}.pdf"
    generate_pdf_report(user_id, output_path)
 
    return send_file(output_path, as_attachment=True, download_name=f"{user['name']}_fitness_report.pdf")

@app.route("/find-dashboard", methods=["POST"])
def find_dashboard():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Enter your name to find your dashboard.")
        return redirect(url_for("home"))
 
    user = find_user_by_name(name)
    if not user:
        flash(f"No plan found for '{name}'. Create a new plan instead.")
        return redirect(url_for("home"))
 
    return redirect(url_for("dashboard", user_id=user["user_id"]))

if __name__ == "__main__":
    app.run(debug=True)