"""
One-off script to import the Kaggle "Gym Progress Tracking Dataset (200 Days)"
CSV into the daily_logs table, under one demo user.

"""

import sys
import pandas as pd

sys.path.append('.')
from modules.database import insert_user, insert_daily_log

CSV_PATH = "data/gym_progress_dataset.csv"


def preview_columns():
    """Run this first, standalone, before touching the insert logic below."""
    df = pd.read_csv(CSV_PATH)
    print("Columns found in CSV:")
    print(list(df.columns))
    print("\nFirst 3 rows:")
    print(df.head(3))
    return df


def import_seed_data():
    df = pd.read_csv(CSV_PATH)

    column_map = {
        "date": "Day",
        "weight": "Weight_kg",
        "calories": "Calories_Intake",
        "protein": "Protein_Intake_g",
        "workout_duration": "Workout_Duration_min",
        "steps_walked": "Steps_Walked"
    }

    # Check the CSV's actual column names (the values), not our internal keys
    missing_cols = [csv_col for csv_col in column_map.values() if csv_col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"These CSV columns were expected but not found: {missing_cols}. "
            f"Run preview_columns() first and fix column_map above."
        )

    demo_user_id = insert_user(
        name="Seed Demo User",
        age=25,
        gender="female",
        height_cm=165,
        weight_kg=float(df.iloc[0][column_map["weight"]]),
        activity_level="moderately_active",
        goal="fat_loss",
        dietary_pref=None
    )
    print(f"Created demo user with user_id: {demo_user_id}")

    inserted_count = 0
    skipped_count = 0

    for _, row in df.iterrows():
        try:
            log_date = pd.to_datetime(row[column_map["date"]]).date()

            workout_completed = False
            if "workout_duration" in column_map:
                duration_val = row[column_map["workout_duration"]]
                workout_completed = bool(duration_val and duration_val > 0)

            insert_daily_log(
                user_id=demo_user_id,
                log_date=log_date,
                weight_kg=float(row[column_map["weight"]]),
                calories_consumed=int(row[column_map["calories"]]),
                protein_g=float(row[column_map["protein"]]) if "protein" in column_map else None,
                carbs_g=None,
                fat_g=None,
                workout_completed=workout_completed,
                steps_walked=int(row[column_map["steps_walked"]]) if "steps_walked" in column_map else None,
                notes="Imported from Kaggle seed dataset"
            )
            inserted_count += 1

        except Exception as e:
            print(f"Skipped row {row.get(column_map['date'], '?')}: {e}")
            skipped_count += 1

    print(f"\nDone. Inserted: {inserted_count}, Skipped: {skipped_count}")
    return demo_user_id


if __name__ == "__main__":
    # Step 1: run preview_columns() alone first to confirm column names.
    preview_columns()

    # Step 2: once confirmed, run the real import.
    import_seed_data()