import sqlite3
from datetime import date, timedelta


# Open a connection to the habits.db file (created automatically if missing)
def get_connection():
    conn = sqlite3.connect("habits.db")
    return conn


# Create the habits and logs tables if they don't already exist
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            habit_id INTEGER,
            date TEXT,
            UNIQUE(habit_id, date)
        )
    """)

    conn.commit()
    conn.close()


# Add a new habit; return True if added, False if the name already exists
def add_habit(name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO habits (name) VALUES (?)", (name,))
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


# Return a list of (id, name) for every habit, ordered by id
def get_all_habits():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM habits ORDER BY id")
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


# Return how many habits were done on a date
def get_count_for_date(date_str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM logs WHERE date = ?", (date_str,))
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


# Return a list of the names of habits done on a date
def get_habits_done_on(date_str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT habits.name FROM habits "
        "JOIN logs ON habits.id = logs.habit_id "
        "WHERE logs.date = ? ORDER BY habits.id",
        (date_str,),
    )
    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    names = []
    for row in rows:
        names.append(row[0])
    return names


if __name__ == "__main__":
    create_tables()
    print("Tables created")

    add_habit("Reading")
    for habit_id, name in get_all_habits():
        if name == "Reading":
            reading_id = habit_id

    today = date.today()
    mark_done(reading_id, today.isoformat())
    mark_done(reading_id, (today - timedelta(days=1)).isoformat())
    mark_done(reading_id, (today - timedelta(days=2)).isoformat())

    print(get_streak(reading_id))
    print(is_done(reading_id, today.isoformat()))
    print(get_count_for_date(today.isoformat()))

    print(get_best_streak(reading_id))
    print(get_completion_percent(reading_id))
    print(get_habits_done_on(today.isoformat()))
