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


if __name__ == "__main__":
    create_tables()
    print("Tables created")
