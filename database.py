import csv
import hashlib
import hmac
import os
import sqlite3
from datetime import date, timedelta

# How many times the password is hashed; higher is slower for attackers (and for us)
PASSWORD_ITERATIONS = 100000

# Streak lengths (in days) that unlock a badge
MILESTONES = [3, 7, 14, 30, 50, 100]


# Open a connection to the habits.db file (created automatically if missing)
def get_connection():
    conn = sqlite3.connect("habits.db")
    return conn


# Create the users, habits, logs and badges tables if they don't already exist
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            UNIQUE(user_id, name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            habit_id INTEGER,
            date TEXT,
            UNIQUE(habit_id, date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            user_id INTEGER,
            milestone INTEGER,
            habit_name TEXT,
            unlocked_date TEXT,
            UNIQUE(user_id, milestone)
        )
    """)

    conn.commit()
    conn.close()


# Create a new user with a salted, hashed password; return False if the username is taken
def create_user(username, password):
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash.hex(), salt.hex()),
        )
        conn.commit()
        created = True
    except sqlite3.IntegrityError:
        created = False

    conn.close()
    return created


# Return the user's id if the username and password are correct, else None
def check_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, password_hash, salt FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()

    conn.commit()
    conn.close()

    if row is None:
        return None

    user_id, stored_hash, stored_salt = row
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(stored_salt), PASSWORD_ITERATIONS
    )

    if hmac.compare_digest(password_hash.hex(), stored_hash):
        return user_id
    return None


# Add a new habit for a user; return True if added, False if that user already has it
def add_habit(user_id, name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO habits (user_id, name) VALUES (?, ?)",
            (user_id, name),
        )
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        added = False

    conn.close()
    return added


# Delete a habit and all of its log rows
def delete_habit(habit_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM logs WHERE habit_id = ?", (habit_id,))
    cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))

    conn.commit()
    conn.close()


# Return a list of (id, name) for every habit of one user, ordered by id
def get_all_habits(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name FROM habits WHERE user_id = ? ORDER BY id",
        (user_id,),
    )
    habits = cursor.fetchall()

    conn.commit()
    conn.close()
    return habits


# Mark a habit as done on a date (does nothing if already marked)
def mark_done(habit_id, date_str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO logs (habit_id, date) VALUES (?, ?)",
        (habit_id, date_str),
    )

    conn.commit()
    conn.close()


# Remove the done mark for a habit on a date
def unmark_done(habit_id, date_str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM logs WHERE habit_id = ? AND date = ?",
        (habit_id, date_str),
    )

    conn.commit()
    conn.close()


# Return True if the habit is marked done on that date, else False
def is_done(habit_id, date_str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM logs WHERE habit_id = ? AND date = ?",
        (habit_id, date_str),
    )
    row = cursor.fetchone()

    conn.commit()
    conn.close()
    return row is not None


# Count how many days in a row the habit was done, ending today (or yesterday)
def get_streak(habit_id):
    conn = get_connection()
    cursor = conn.cursor()

    day = date.today()

    cursor.execute(
        "SELECT 1 FROM logs WHERE habit_id = ? AND date = ?",
        (habit_id, day.isoformat()),
    )
    if cursor.fetchone() is None:
        day = day - timedelta(days=1)

    streak = 0
    while True:
        cursor.execute(
            "SELECT 1 FROM logs WHERE habit_id = ? AND date = ?",
            (habit_id, day.isoformat()),
        )
        if cursor.fetchone() is None:
            break
        streak = streak + 1
        day = day - timedelta(days=1)

    conn.commit()
    conn.close()
    return streak


# Return how many of one user's habits were done on a date
def get_count_for_date(date_str, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM logs "
        "JOIN habits ON habits.id = logs.habit_id "
        "WHERE logs.date = ? AND habits.user_id = ?",
        (date_str, user_id),
    )
    count = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return count


# Return the longest run of consecutive done days ever logged for a habit
def get_best_streak(habit_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT date FROM logs WHERE habit_id = ? ORDER BY date",
        (habit_id,),
    )
    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    if len(rows) == 0:
        return 0

    best = 1
    current = 1
    previous_day = date.fromisoformat(rows[0][0])

    for row in rows[1:]:
        this_day = date.fromisoformat(row[0])
        if this_day - previous_day == timedelta(days=1):
            current = current + 1
        else:
            current = 1
        if current > best:
            best = current
        previous_day = this_day

    return best


# Return the percent (0-100) of the last `days` days, including today, that were done
def get_completion_percent(habit_id, days=30):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today()
    start_day = today - timedelta(days=days - 1)

    cursor.execute(
        "SELECT COUNT(*) FROM logs WHERE habit_id = ? AND date >= ? AND date <= ?",
        (habit_id, start_day.isoformat(), today.isoformat()),
    )
    done_days = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return round(done_days * 100 / days)


# Return a list of the names of one user's habits done on a date
def get_habits_done_on(date_str, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT habits.name FROM habits "
        "JOIN logs ON habits.id = logs.habit_id "
        "WHERE logs.date = ? AND habits.user_id = ? ORDER BY habits.id",
        (date_str, user_id),
    )
    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    names = []
    for row in rows:
        names.append(row[0])
    return names


# Write a CSV report with one row of stats per habit of one user and return the filename
def export_to_csv(user_id, filename="consistify_report.csv"):
    conn = get_connection()
    cursor = conn.cursor()

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Habit",
            "Current Streak",
            "Best Streak",
            "Completion % (30 days)",
            "Total Days Done",
        ])

        for habit_id, name in get_all_habits(user_id):
            cursor.execute(
                "SELECT COUNT(*) FROM logs WHERE habit_id = ?",
                (habit_id,),
            )
            total_days = cursor.fetchone()[0]

            writer.writerow([
                name,
                get_streak(habit_id),
                get_best_streak(habit_id),
                get_completion_percent(habit_id),
                total_days,
            ])

    conn.commit()
    conn.close()
    return filename


# Return the highest current streak among one user's habits (0 if the user has no habits)
def get_current_best_streak(user_id):
    best = 0
    for habit_id, name in get_all_habits(user_id):
        streak = get_streak(habit_id)
        if streak > best:
            best = streak
    return best


# Unlock every milestone the user has now reached but didn't have yet; return the new ones as (milestone, habit_name)
def check_new_badges(user_id):
    # Work out every habit's current streak first, longest first, so a badge is named after the best habit
    streaks = []
    for habit_id, name in get_all_habits(user_id):
        streaks.append((get_streak(habit_id), name))
    streaks.sort(reverse=True)

    conn = get_connection()
    cursor = conn.cursor()

    # The milestones this user has already unlocked
    cursor.execute("SELECT milestone FROM badges WHERE user_id = ?", (user_id,))
    unlocked = []
    for row in cursor.fetchall():
        unlocked.append(row[0])

    new_badges = []
    today = date.today().isoformat()
    for milestone in MILESTONES:
        if milestone in unlocked:
            continue
        for streak, name in streaks:
            if streak >= milestone:
                # INSERT OR IGNORE + UNIQUE(user_id, milestone): if this badge somehow exists already, nothing is added
                cursor.execute(
                    "INSERT OR IGNORE INTO badges (user_id, milestone, habit_name, unlocked_date) VALUES (?, ?, ?, ?)",
                    (user_id, milestone, name, today),
                )
                # rowcount is 1 if a row was really inserted, 0 if it was ignored
                if cursor.rowcount == 1:
                    new_badges.append((milestone, name))
                break

    conn.commit()
    conn.close()
    return new_badges


# Return the user's unlocked badges as (milestone, habit_name, unlocked_date), smallest milestone first
def get_badges(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT milestone, habit_name, unlocked_date FROM badges WHERE user_id = ? ORDER BY milestone",
        (user_id,),
    )
    badges = cursor.fetchall()

    conn.commit()
    conn.close()
    return badges


if __name__ == "__main__":
    create_tables()
    print("Tables created")

    print(create_user("demo", "demo123"))
    print(check_login("demo", "wrong password"))

    user_id = check_login("demo", "demo123")
    print(user_id)

    add_habit(user_id, "Reading")
    for habit_id, name in get_all_habits(user_id):
        if name == "Reading":
            reading_id = habit_id

    # Done today, yesterday and the day before: a 3-day streak
    today = date.today()
    mark_done(reading_id, today.isoformat())
    mark_done(reading_id, (today - timedelta(days=1)).isoformat())
    mark_done(reading_id, (today - timedelta(days=2)).isoformat())

    print(get_all_habits(user_id))
    print(get_streak(reading_id))

    # The first call unlocks the 3-day badge; the second finds nothing new
    print(check_new_badges(user_id))
    print(check_new_badges(user_id))
    print(get_badges(user_id))
    print(get_current_best_streak(user_id))
