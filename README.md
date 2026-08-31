# FitPlan AI - AI-Powered Personalized Workout & Diet Planner

A Flask web application that generates personalized diet and workout plans, tracks progress through SQL-based analytics, forecasts weight trends with time-series modeling, and analyzes exercise form from uploaded video using computer vision.

Built as a final project for the Edunet Foundation / IBM SkillsBuild internship.

---

## Problem Statement

Most fitness apps offer generic, one-size-fits-all plans that ignore an individual's actual metabolic data and logged history. Users struggle with consistency because plans are static and don't adapt to real progress. Few free tools combine diet planning, workout programming, progress forecasting, and exercise form feedback in a single system - and fewer still apply real data science techniques (SQL analytics, time-series forecasting, computer vision) beyond static rule tables.

## Features

- **Personalized plan generation** - BMR/TDEE calculated via the Mifflin-St Jeor equation, adjusted for activity level, with a goal-based macronutrient split (muscle gain / fat loss / maintenance) and a 7-day workout split matched to training experience.
- **SQL analytics dashboard** - weekly adherence rate, 7-day rolling average weight trend, and weekly activity summary, computed directly via MySQL window functions and aggregate queries.
- **Weight trend forecasting** - a Prophet time-series model projects weight trend 28 days forward with a confidence interval, using the user's own logged history.
- **Computer vision form checker** - uploaded exercise videos (squat, deadlift, push-up) are analyzed frame-by-frame via MediaPipe Pose estimation; a geometric angle calculation and rule-based state machine count reps and give per-rep depth feedback.
- **PDF report export** - a downloadable report combining the diet plan, workout split, adherence summary, and forecast.
- **Dashboard lookup** - returning users can find their dashboard by name (no full authentication system - see Limitations).

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL |
| Core logic | Pure Python (BMR/TDEE, diet, workout modules) |
| Analytics | SQL window functions, pandas, SciPy (Pearson correlation) |
| Forecasting | Facebook Prophet |
| Computer vision | MediaPipe Pose, OpenCV |
| Reporting | ReportLab (PDF generation) |
| Frontend | Jinja2 templates, custom CSS |

## Project Structure

```
workout_planner/
├── app.py                       # Flask routes
├── requirements.txt
├── .env.example
├── modules/
│   ├── bmr_tdee.py               # BMR / TDEE / BMI calculations
│   ├── diet_logic.py             # Macro split by goal
│   ├── workout_logic.py          # Weekly workout split generator
│   ├── database.py                # MySQL connection + CRUD
│   ├── analytics.py               # SQL analytics queries (pandas-wrapped)
│   ├── forecasting.py             # Prophet forecasting
│   ├── exercise_rules.py          # Per-exercise angle thresholds
│   ├── form_checker.py            # Video processing + rep counting
│   └── pdf_generator.py           # PDF report builder
├── templates/                     # Jinja2 HTML templates
├── static/css/                    # Stylesheet
├── sql/
│   ├── create_tables.sql
│   ├── add_form_checks_table.sql
│   └── analytics_queries.sql      # Reference copy of the analytics SQL
├── data/                          # Seed dataset (CSV)
├── import_seed_data.py            # One-off seed data import script
└── master_test.ipynb              # Consolidated test notebook (all modules)
```

## Database Schema

Five tables, linked by foreign keys with cascading deletes:

- **users** - profile, stats, goal, activity level
- **daily_logs** - one row per user per day: weight, calories, macros, steps, workout completion
- **workout_sessions** - logged training sessions
- **plans** - generated diet/workout plan per user, workout split stored as JSON
- **form_checks** - per-rep results from the CV form checker (exercise type, peak angle, verdict, feedback)

## How to Run

### Prerequisites

- **Python 3.11 specifically.** MediaPipe does not yet support newer Python versions (e.g. 3.14) - installing it on an unsupported version can silently install a broken package rather than failing outright.
- MySQL Server installed locally.
- A recorded exercise video if testing the form checker (side-angle, a few reps).

### Setup

```bash
git clone <your-repo-url>
cd workout_planner

py -3.11 -m venv venv
.\venv\Scripts\activate        # Windows PowerShell
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

### Database setup

Run in MySQL Workbench or CLI:

```
sql/create_tables.sql
sql/add_form_checks_table.sql
```

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=workout_planner_db
```

**Note:** if you hit a MySQL connection error where the process crashes silently rather than raising a catchable Python error, this is a known issue with `mysql-connector-python`'s C extension on some Windows + MySQL version combinations. It's already worked around here - `get_connection()` in `modules/database.py` uses `use_pure=True` to force the pure-Python driver.

### Seed data (optional, for demo purposes)

```bash
python import_seed_data.py
```

Imports a public Kaggle dataset (200 days of daily fitness logs) under one demo user, so analytics and forecasting have real historical data to work with immediately. This is disclosed here and in-app as partly synthetic demonstration data, not real user data.

### Run

```bash
python app.py
```

Visit `http://127.0.0.1:5000`. This URL only works on the machine running the server - it is not a public link.

### Testing

All core logic, database, forecasting, analytics, and form checker tests are consolidated in `master_test.ipynb`. Set `DEMO_USER_ID` at the top to your seeded demo user's ID, then run top to bottom. The form checker section requires real recorded exercise videos.

## Results

- **End-to-end pipeline verified** - onboarding generates and stores a plan, retrievable from the dashboard.
- **Forecast example:** starting weight 71.5 kg (Jan 1), projected to 70.7 kg by August 16 (28 days beyond a 200-day history), with a 95% confidence interval of 67.4–74.5 kg. The wide interval reflects genuinely high day-to-day volatility in the underlying data, not a modeling flaw.
- **Correlation analysis:** the seed dataset logged a workout on every single day, making weekly adherence constant at 100% - a correlation against weight change is mathematically undefined in that case, and this is documented rather than hidden. As a working substitute, weekly average calories vs. weight change was computed instead: Pearson r = -0.220, p = 0.261 (n = 28 weeks) - a direction consistent with expectations, but not statistically significant at this sample size.
- **Form checker:** rep counting was validated against real recorded video for all three supported exercises (squat, deadlift, push-up), with correct rep counts and depth verdicts on first attempt using the default thresholds in `exercise_rules.py`. This was validated on one video per exercise from one person/camera angle - not a claim of general accuracy across body types or filming conditions.

## Known Limitations

Documented deliberately rather than discovered by a reader:

- **No authentication system.** Returning-user lookup is by name only - a convenience, not security. Not suitable beyond a portfolio/demo context.
- **Seed data is partly synthetic.** The demo dataset is a public Kaggle dataset generated for educational use, not real user data - disclosed both here and in the seed import script.
- **Adherence was constant in the seed dataset**, making one planned correlation mathematically undefined (see Results above) - a property of the demo data, not a bug.
- **Form checker thresholds are starting points**, based on common coaching cues rather than derived from a dataset, and validated only on a small number of self-recorded test videos.
- **No connection pooling** - each database call opens and closes its own connection; fine at this scale, a known simplification.
- **No automatic cleanup for uploaded videos** - analyzed videos persist on disk indefinitely to support in-app playback; there is no expiry policy.
- **Prophet forecasts assume the current trend continues** - the model has no way to anticipate a deliberate future plan change, injury, or other disruption.

## Development Process

Built in eight phases: environment setup, core planner logic, MySQL schema and SQL analytics, Flask integration, time-series forecasting, computer vision form checker, full integration (PDF report, mobile responsiveness), and documentation. Each module was unit-tested independently - including deliberate edge-case and failure-path testing - before being integrated into the next phase, with tests consolidated into a single notebook (`master_test.ipynb`) for repeatability.

## Future Scope

- Extend the form checker with real-time webcam feedback and additional exercises.
- Add an ML-based injury/plateau risk classifier with SHAP explainability.
- Introduce an NLP-based conversational AI coach grounded in the user's own logged data.
- Add real user authentication for multi-user support.
- Replace synthetic seed data with a larger real-world logged dataset.

## References

- Prophet Documentation - facebook.github.io/prophet/docs/quick_start.html
- MediaPipe Pose Documentation - github.com/google-ai-edge/mediapipe
- Mifflin MD, St Jeor ST, et al. - *A new predictive equation for resting energy expenditure*
- Kaggle - Gym Progress Tracking Dataset (200 Days)
- MySQL 8.0 Reference Manual - Window Functions

## Author

**Kashika** - BCA, Indira Gandhi National Open University (IGNOU), New Delhi