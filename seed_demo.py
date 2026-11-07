# Fill the database with realistic demo data (for presentations and screenshots)
# Run it from the consistify folder:  py seed_demo.py
import random
from datetime import date, timedelta

import database

USERNAME = "demo"
PASSWORD = "demo123"

# How many days of history to create (today included)
DAYS = 90

# Each habit's normal chance of being done on a day: higher = more consistent
HABIT_CHANCES = {
    "LeetCode daily problem": 0.85,
    "GitHub contribution": 0.75,
    "TryHackMe": 0.55,
    "Gym": 0.70,
    "Read 10 pages": 0.80,
    "Drink 3L water": 0.90,
    "Java course": 0.50,
    "Meditate 10 min": 0.60,
}

# Habits that are done EVERY day for this many days (ending today), to build a real streak
FORCED_STREAKS = {"LeetCode daily problem": 35, "Gym": 10}

# On a "bad day" each habit only has this small chance of being done
BAD_DAY_CHANCE = 0.05


# Delete the old demo account (if any) and create a fresh one; return its user id, or None if that fails
def reset_demo_user():
    user_id = database.check_login(USERNAME, PASSWORD)
    if user_id is not None:
        database.delete_user(user_id, PASSWORD)
    database.create_user(USERNAME, PASSWORD)
    return database.check_login(USERNAME, PASSWORD)


# Add every demo habit and return a dictionary {habit name: habit id}
def add_demo_habits(user_id):
    for name in HABIT_CHANCES:
        database.add_habit(user_id, name)
    habit_ids = {}
    for habit_id, name in database.get_all_habits(user_id):
        habit_ids[name] = habit_id
    return habit_ids


# Return the chance for a habit on a day that is `days_ago` days before today (older days have a lower chance)
def chance_for_day(name, days_ago):
    chance = HABIT_CHANCES[name]
    if days_ago >= 60:
        # The first 30 days: still getting started
        chance = chance * 0.7
    elif days_ago < 30:
        # The last 30 days: the habit has stuck, so a little higher (never above 95%)
        chance = min(chance * 1.1, 0.95)
    return chance


# Decide whether a habit was done on a day; return True or False
def was_done(name, days_ago, bad_days):
    # Inside a forced streak: always done
    if name in FORCED_STREAKS and days_ago < FORCED_STREAKS[name]:
        return True
    # The day just before a forced streak is a miss, so the streak is exactly that long
    if name in FORCED_STREAKS and days_ago == FORCED_STREAKS[name]:
        return False
    if days_ago in bad_days:
        return random.random() < BAD_DAY_CHANCE
    # random.random() gives a number from 0 to 1, so it's below 0.8 about 80% of the time
    return random.random() < chance_for_day(name, days_ago)


# Mark the habits done over the last DAYS days and return how many check-ins were added
def fill_history(habit_ids):
    # 3 bad days, picked before the LeetCode streak starts so the streaks stay unbroken
    bad_days = random.sample(range(FORCED_STREAKS["LeetCode daily problem"] + 1, DAYS), 3)

    today = date.today()
    total = 0
    # From the oldest day (89 days ago) up to today (0 days ago)
    for days_ago in range(DAYS - 1, -1, -1):
        day = (today - timedelta(days=days_ago)).isoformat()
        for name, habit_id in habit_ids.items():
            if was_done(name, days_ago, bad_days):
                database.mark_done(habit_id, day)
                total = total + 1
    return total


# Print what was created
def print_summary(user_id, habit_ids, total):
    print("Demo data created")
    print("Habits:", len(habit_ids))
    print("Total check-ins:", total)
    print("LeetCode streak:", database.get_streak(habit_ids["LeetCode daily problem"]), "days")
    milestones = []
    for milestone, habit_name, unlocked_date in database.get_badges(user_id):
        milestones.append(str(milestone))
    print("Badges unlocked:", len(milestones), "(" + ", ".join(milestones) + " days)")
    print("Log in with demo / demo123")


# Build the whole demo account from scratch
def seed():
    # The same seed gives the same "random" numbers every run, so the demo data is always the same
    random.seed(42)
    database.create_tables()

    user_id = reset_demo_user()
    if user_id is None:
        print("Could not create the demo account. Does 'demo' exist with a different password?")
        return

    habit_ids = add_demo_habits(user_id)
    total = fill_history(habit_ids)
    database.check_new_badges(user_id)
    print_summary(user_id, habit_ids, total)


if __name__ == "__main__":
    seed()
