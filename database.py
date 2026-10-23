import sqlite3


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


if __name__ == "__main__":
    create_tables()
    print("Tables created")

    print(add_habit("LeetCode"))
    print(add_habit("Gym"))
    print(add_habit("Gym"))

    print(get_all_habits())

    for habit_id, name in get_all_habits():
        if name == "Gym":
            delete_habit(habit_id)

    print(get_all_habits())
