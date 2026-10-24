import tkinter as tk
from datetime import date, timedelta

import database

# Size settings for the heatmap (in pixels)
SQUARE_SIZE = 14
GAP = 3
NUMBER_OF_DAYS = 90
LEFT_MARGIN = 30
TOP_MARGIN = 20

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


# Return the top-left (x, y) of a day's square: its row is its weekday, its column is its week
def get_square_position(day, first_day):
    days_since_start = (day - first_day).days
    column = (days_since_start + first_day.weekday()) // 7
    row = day.weekday()

    x = LEFT_MARGIN + column * (SQUARE_SIZE + GAP)
    y = TOP_MARGIN + row * (SQUARE_SIZE + GAP)
    return x, y


# Write "Mon", "Wed" and "Fri" to the left of their rows
def draw_weekday_labels(canvas):
    for row, name in [(0, "Mon"), (2, "Wed"), (4, "Fri")]:
        middle = TOP_MARGIN + row * (SQUARE_SIZE + GAP) + SQUARE_SIZE / 2
        canvas.create_text(0, middle, text=name, fill=MUTED_COLOR, font=("Arial", 9), anchor="w")


# Draw the "Less [5 color boxes] More" legend under the grid
def draw_legend(canvas):
    top = TOP_MARGIN + 7 * (SQUARE_SIZE + GAP) + 10
    middle = top + SQUARE_SIZE / 2

    canvas.create_text(LEFT_MARGIN, middle, text="Less", fill=MUTED_COLOR, font=("Arial", 9), anchor="w")

    for level in range(5):
        x1 = LEFT_MARGIN + 30 + level * (SQUARE_SIZE + GAP)
        canvas.create_rectangle(x1, top, x1 + SQUARE_SIZE, top + SQUARE_SIZE, fill=get_color(level), outline="")

    more_x = LEFT_MARGIN + 30 + 5 * (SQUARE_SIZE + GAP) + 3
    canvas.create_text(more_x, middle, text="More", fill=MUTED_COLOR, font=("Arial", 9), anchor="w")


# Draw one clickable square per day for the last 90 days, one row per weekday
def draw_heatmap(canvas, counts, info_label):
    today = date.today()
    first_day = today - timedelta(days=NUMBER_OF_DAYS - 1)

    for i in range(NUMBER_OF_DAYS):
        day = first_day + timedelta(days=i)
        date_text = day.strftime("%Y-%m-%d")
        count = counts.get(date_text, 0)

        x1, y1 = get_square_position(day, first_day)
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE

        square = canvas.create_rectangle(x1, y1, x2, y2, fill=get_color(count), outline="")
        canvas.tag_bind(square, "<Button-1>", lambda event, d=date_text, c=count: show_day(info_label, d, c))
        canvas.tag_bind(square, "<Enter>", lambda event: set_cursor(canvas, "hand2"))
        canvas.tag_bind(square, "<Leave>", lambda event: set_cursor(canvas, ""))

        # On the 1st of a month, write the month name ("Sep", "Oct") above that column
        if day.day == 1:
            canvas.create_text(x1, TOP_MARGIN - 10, text=day.strftime("%b"), fill=MUTED_COLOR, font=("Arial", 9), anchor="w")

    draw_weekday_labels(canvas)
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

    # 280 x 180 fits the weekday labels, up to 14 week columns, the month labels and the legend
    canvas = tk.Canvas(section, width=280, height=180, bg=BG_COLOR, highlightthickness=0)
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