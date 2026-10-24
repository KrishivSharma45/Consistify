import tkinter as tk
from datetime import date, timedelta

import database

# Size settings for the heatmap (in pixels)
SQUARE_SIZE = 14
GAP = 3
PADDING = 10
NUMBER_OF_DAYS = 90

# Theme colors, the same values the rest of the team uses
BG_COLOR = "#0d1117"
TEXT_COLOR = "#e6edf3"
MUTED_COLOR = "#8b949e"


# Return the color for a given number of habits done in one day
def get_color(count):
    if count == 0:
        return "#161b22"
    elif count == 1:
        return "#0e4429"
    elif count == 2:
        return "#006d32"
    elif count == 3:
        return "#26a641"
    else:
        return "#39d353"


# Show the clicked day's date and count in the info label
def show_day(info_label, date_text, count):
    if count == 1:
        word = "habit"
    else:
        word = "habits"
    info_label.config(text=f"{date_text}: {count} {word} done")


# Change the mouse pointer when it moves over or off a square
def set_cursor(canvas, cursor_name):
    canvas.config(cursor=cursor_name)


# Draw the "Less [5 color boxes] More" legend under the grid
def draw_legend(canvas):
    top = PADDING + 7 * (SQUARE_SIZE + GAP) + 10
    middle = top + SQUARE_SIZE / 2

    canvas.create_text(PADDING, middle, text="Less", fill=MUTED_COLOR, font=("Arial", 9), anchor="w")

    for level in range(5):
        x1 = PADDING + 30 + level * (SQUARE_SIZE + GAP)
        canvas.create_rectangle(x1, top, x1 + SQUARE_SIZE, top + SQUARE_SIZE, fill=get_color(level), outline="")

    more_x = PADDING + 30 + 5 * (SQUARE_SIZE + GAP) + 3
    canvas.create_text(more_x, middle, text="More", fill=MUTED_COLOR, font=("Arial", 9), anchor="w")


# Draw one clickable square per day for the last 90 days, 7 days in each column
def draw_heatmap(canvas, counts, info_label):
    today = date.today()

    for i in range(NUMBER_OF_DAYS):
        day = today - timedelta(days=NUMBER_OF_DAYS - 1 - i)
        date_text = day.strftime("%Y-%m-%d")
        count = counts.get(date_text, 0)

        column = i // 7
        row = i % 7

        x1 = PADDING + column * (SQUARE_SIZE + GAP)
        y1 = PADDING + row * (SQUARE_SIZE + GAP)
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE

        square = canvas.create_rectangle(x1, y1, x2, y2, fill=get_color(count), outline="")
        canvas.tag_bind(square, "<Button-1>", lambda event, d=date_text, c=count: show_day(info_label, d, c))
        canvas.tag_bind(square, "<Enter>", lambda event: set_cursor(canvas, "hand2"))
        canvas.tag_bind(square, "<Leave>", lambda event: set_cursor(canvas, ""))

    draw_legend(canvas)


# Ask the database how many habits were done on each of the last 90 days
def get_counts_from_database():
    counts = {}
    today = date.today()

    for days_ago in range(NUMBER_OF_DAYS):
        day = today - timedelta(days=days_ago)
        date_text = day.strftime("%Y-%m-%d")
        counts[date_text] = database.get_count_for_date(date_text)

    return counts


# Wipe the canvas and redraw the heatmap with fresh numbers from the database
def refresh_heatmap(canvas, info_label):
    canvas.delete("all")
    counts = get_counts_from_database()
    draw_heatmap(canvas, counts, info_label)


# Build the whole heatmap section (title, grid, info label) inside any window or frame
def create_heatmap_section(parent):
    section = tk.Frame(parent, bg=BG_COLOR)
    section.pack(pady=10)

    title_label = tk.Label(section, text="Last 90 days", bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 12, "bold"))
    title_label.pack(anchor="w")

    # 240 x 170 fits 13 columns, 7 rows, and the legend underneath
    canvas = tk.Canvas(section, width=240, height=170, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    info_label = tk.Label(section, text="Click a square to see details", bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 10))
    info_label.pack()

    refresh_heatmap(canvas, info_label)
    return canvas, info_label


if __name__ == "__main__":
    database.create_tables()

    window = tk.Tk()
    window.title("Consistify - Heatmap")
    window.configure(bg=BG_COLOR, padx=20, pady=20)

    canvas, info_label = create_heatmap_section(window)

    # A test button that redraws the heatmap, like main.py will do after a checkbox is ticked
    refresh_button = tk.Button(window, text="Refresh", command=lambda: refresh_heatmap(canvas, info_label))
    refresh_button.pack(pady=(10, 0))

    window.mainloop()