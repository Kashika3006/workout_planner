CREATE DATABASE IF NOT EXISTS workout_planner_db;
USE workout_planner_db;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    height_cm DECIMAL(5,2) NOT NULL,
    weight_kg DECIMAL(5,2) NOT NULL,
    activity_level VARCHAR(20) NOT NULL,
    goal VARCHAR(20) NOT NULL,
    dietary_pref VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    weight_kg DECIMAL(5,2),
    calories_consumed INT,
    protein_g DECIMAL(6,2),
    carbs_g DECIMAL(6,2),
    fat_g DECIMAL(6,2),
    workout_completed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    steps_walked INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_date (user_id, log_date)
);

CREATE TABLE workout_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_date DATE NOT NULL,
    split_type VARCHAR(20),
    total_volume_kg DECIMAL(8,2),
    duration_min INT,
    rpe_avg DECIMAL(3,1),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calorie_target INT,
    protein_target DECIMAL(6,2),
    carb_target DECIMAL(6,2),
    fat_target DECIMAL(6,2),
    workout_split JSON,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
