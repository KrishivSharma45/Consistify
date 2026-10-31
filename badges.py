# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import date so the unlocked date can be shown nicely ("31 Oct 2026")
from datetime import date

# Import our own database.py (badges, streaks), the shared colors and the reusable widgets
import database
import theme
import ui

# One emoji per milestone
BADGE_EMOJIS = {3: "🌱", 7: "🔥", 14: "⚡", 30: "🏅", 50: "💎", 100: "👑"}
BAR_HEIGHT = 6     # height of the progress bar on a locked card (pixels)


# Draw a locked card's progress bar: a BORDER track across the canvas and an ACCENT fill for `fraction` of it
def draw_badge_bar(bar, fraction):
    bar.delete("all")
    width = bar.winfo_width()
    bar.create_rectangle(0, 0, width, BAR_HEIGHT, fill=theme.BORDER, outline="")
    if fraction > 0:
        bar.create_rectangle(0, 0, width * fraction, BAR_HEIGHT, fill=theme.ACCENT, outline="")


# Build the card for an unlocked badge: big emoji, title, habit name and date, 2px accent border
def create_unlocked_card(grid, row, column, milestone, habit_name, unlocked_date):
    card = tk.Frame(grid, bg=theme.CARD, padx=16, pady=16)
    card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
    ui.add_hover_border(card, theme.ACCENT, theme.ACCENT_HOVER, 2)

    emoji = tk.Label(card, text=BADGE_EMOJIS[milestone], font=(theme.FONT, 30), fg=theme.ACCENT, bg=theme.CARD)
    emoji.pack(anchor="w")
    title = tk.Label(card, text=str(milestone) + "-day streak", font=(theme.FONT, 13, "bold"), fg=theme.TEXT, bg=theme.CARD)
    title.pack(anchor="w", pady=(8, 0))
    habit = tk.Label(card, text=habit_name, font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD)
    habit.pack(anchor="w")

    # The database stores "2026-10-31"; strftime turns it into "31 Oct 2026"
    nice_date = date.fromisoformat(unlocked_date).strftime("%d %b %Y")
    when = tk.Label(card, text="Unlocked " + nice_date, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    when.pack(anchor="w")


# Build the card for a locked badge: a lock, the goal, and a bar showing how close the best streak is
def create_locked_card(grid, row, column, milestone, best_streak):
    card = tk.Frame(grid, bg=theme.CARD, padx=16, pady=16)
    card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
    ui.add_hover_border(card, theme.BORDER, theme.ACCENT, 1)

    lock = tk.Label(card, text="🔒", font=(theme.FONT, 30), fg=theme.MUTED, bg=theme.CARD)
    lock.pack(anchor="w")
    title = tk.Label(card, text=str(milestone) + "-day streak", font=(theme.FONT, 13, "bold"), fg=theme.MUTED, bg=theme.CARD)
    title.pack(anchor="w", pady=(8, 0))
    goal = tk.Label(card, text="Reach a " + str(milestone) + "-day streak", font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD)
    goal.pack(anchor="w")

    # Progress = best current streak / milestone, but never more than 100% (and the text never above the goal)
    shown = min(best_streak, milestone)
    fraction = shown / milestone
    bar = tk.Canvas(card, height=BAR_HEIGHT, bg=theme.CARD, highlightthickness=0)
    bar.pack(fill="x", pady=(10, 4))
    # The bar's real width is only known once it is on screen, so draw it whenever its size changes
    bar.bind("<Configure>", lambda event: draw_badge_bar(bar, fraction))
    count = tk.Label(card, text=str(shown) + " / " + str(milestone) + " days", font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    count.pack(anchor="w")


# Build the whole Badges page inside the parent: header plus a 3-per-row grid of all milestones
def build_badges_page(parent, user_id):
    page = tk.Frame(parent, bg=theme.BG, padx=40, pady=30)
    page.pack(fill="both", expand=True)

    # badges: milestone -> (habit_name, unlocked_date), so we can look up whether each milestone is unlocked
    badges = {}
    for milestone, habit_name, unlocked_date in database.get_badges(user_id):
        badges[milestone] = (habit_name, unlocked_date)
    best_streak = database.get_current_best_streak(user_id)

    header = tk.Frame(page, bg=theme.BG)
    header.pack(fill="x", pady=(0, 16))
    title = tk.Label(header, text="Your badges", font=(theme.FONT, 22, "bold"), fg=theme.TEXT, bg=theme.BG)
    title.pack(side="left")
    count_text = str(len(badges)) + " of " + str(len(database.MILESTONES)) + " unlocked"
    count = tk.Label(header, text=count_text, font=(theme.FONT, 11), fg=theme.MUTED, bg=theme.BG)
    count.pack(side="left", padx=(14, 0), pady=(8, 0))

    grid = tk.Frame(page, bg=theme.BG)
    grid.pack(fill="x")
    # Three equal columns
    for column in range(3):
        grid.columnconfigure(column, weight=1, uniform="badge")

    for i in range(len(database.MILESTONES)):
        milestone = database.MILESTONES[i]
        # i // 3 is the row (0, 0, 0, 1, 1, 1) and i % 3 the column (0, 1, 2, 0, 1, 2)
        row = i // 3
        column = i % 3
        if milestone in badges:
            habit_name, unlocked_date = badges[milestone]
            create_unlocked_card(grid, row, column, milestone, habit_name, unlocked_date)
        else:
            create_locked_card(grid, row, column, milestone, best_streak)

    return page


# Run this block only when badges.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    # Log in as a test user (create_user just returns False if "demo" already exists)
    database.create_user("demo", "demo123")
    user_id = database.check_login("demo", "demo123")

    window = tk.Tk()
    window.title("Consistify - Badges")
    # The same size as the dashboard's content area in main.py (1100 wide minus the 200px sidebar, 700 tall)
    window.geometry("900x700")
    window.configure(bg=theme.BG)

    build_badges_page(window, user_id)
    window.mainloop()
