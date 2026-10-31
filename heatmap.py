import tkinter as tk
# Import tkinter's font tool, so the hover label can measure itself and stay inside the chart
import tkinter.font as tkfont
from datetime import date, timedelta

import database
# Import the app's shared colors and font
import theme

# Size settings for the heatmap (in pixels)
SQUARE_SIZE = 14
GAP = 3
NUMBER_OF_DAYS = 90
LEFT_MARGIN = 30
TOP_MARGIN = 20

# Size settings for the weekly bar chart (in pixels)
CHART_WIDTH = 420
CHART_HEIGHT = 170
CHART_TOP = 26       # space above the tallest bar, for the hover label
CHART_BOTTOM = 22    # space under the bars, for the day names
BAR_WIDTH = 28
BAR_RADIUS = 10      # how round the top corners of a bar are (smoothing curves about half of this)
GROW_STEPS = 20      # the grow animation takes 20 steps...
GROW_DELAY = 20      # ...20 milliseconds apart, so about 400 ms in total


# Return the color for a given number of habits done in one day (theme.HEATMAP holds the 5 shades)
def get_color(count):
    if count == 0:
        return theme.HEATMAP[0]
    elif count == 1:
        return theme.HEATMAP[1]
    elif count == 2:
        return theme.HEATMAP[2]
    elif count == 3:
        return theme.HEATMAP[3]
    else:
        return theme.HEATMAP[4]


# Show the clicked day's date, count and the names of the habits done that day
def show_day(info_label, date_text, count, user_id):
    if count == 1:
        word = "habit"
    else:
        word = "habits"
    text = f"{date_text}: {count} {word} done"

    names = database.get_habits_done_on(date_text, user_id)
    if len(names) > 0:
        text = text + "\n" + ", ".join(names)

    info_label.config(text=text)


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
        canvas.create_text(0, middle, text=name, fill=theme.MUTED, font=("Arial", 9), anchor="w")


# Draw the "Less [5 color boxes] More" legend under the grid
def draw_legend(canvas):
    top = TOP_MARGIN + 7 * (SQUARE_SIZE + GAP) + 10
    middle = top + SQUARE_SIZE / 2

    canvas.create_text(LEFT_MARGIN, middle, text="Less", fill=theme.MUTED, font=("Arial", 9), anchor="w")

    for level in range(5):
        x1 = LEFT_MARGIN + 30 + level * (SQUARE_SIZE + GAP)
        canvas.create_rectangle(x1, top, x1 + SQUARE_SIZE, top + SQUARE_SIZE, fill=get_color(level), outline="")

    more_x = LEFT_MARGIN + 30 + 5 * (SQUARE_SIZE + GAP) + 3
    canvas.create_text(more_x, middle, text="More", fill=theme.MUTED, font=("Arial", 9), anchor="w")


# Draw one clickable square per day for the last 90 days, one row per weekday
def draw_heatmap(canvas, counts, info_label, user_id):
    today = date.today()
    first_day = today - timedelta(days=NUMBER_OF_DAYS - 1)

    for i in range(NUMBER_OF_DAYS):
        day = first_day + timedelta(days=i)
        date_text = day.strftime("%Y-%m-%d")
        count = counts.get(date_text, 0)

        x1, y1 = get_square_position(day, first_day)
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE

        # Give today's square a light border so it is easy to find
        if day == today:
            border = theme.TEXT
        else:
            border = ""

        square = canvas.create_rectangle(x1, y1, x2, y2, fill=get_color(count), outline=border)
        canvas.tag_bind(square, "<Button-1>", lambda event, d=date_text, c=count: show_day(info_label, d, c, user_id))
        canvas.tag_bind(square, "<Enter>", lambda event: set_cursor(canvas, "hand2"))
        canvas.tag_bind(square, "<Leave>", lambda event: set_cursor(canvas, ""))

        # On the 1st of a month, write the month name ("Sep", "Oct") above that column
        if day.day == 1:
            canvas.create_text(x1, TOP_MARGIN - 10, text=day.strftime("%b"), fill=theme.MUTED, font=("Arial", 9), anchor="w")

    draw_weekday_labels(canvas)
    draw_legend(canvas)


# Ask the database how many of one user's habits were done on each of the last 90 days
def get_counts_from_database(user_id):
    counts = {}
    today = date.today()

    for days_ago in range(NUMBER_OF_DAYS):
        day = today - timedelta(days=days_ago)
        date_text = day.strftime("%Y-%m-%d")
        counts[date_text] = database.get_count_for_date(date_text, user_id)

    return counts


# Wipe the canvas and redraw the heatmap with fresh numbers from the database
def refresh_heatmap(canvas, info_label, user_id):
    canvas.delete("all")
    counts = get_counts_from_database(user_id)
    draw_heatmap(canvas, counts, info_label, user_id)


# Build the whole heatmap section (title, grid, info label) for one user inside any window or frame
def create_heatmap_section(parent, user_id):
    section = tk.Frame(parent, bg=theme.BG)
    section.pack(pady=10)

    title_label = tk.Label(section, text="Last 90 days", bg=theme.BG, fg=theme.TEXT, font=("Arial", 12, "bold"))
    title_label.pack(anchor="w")

    # 280 x 180 fits the weekday labels, up to 14 week columns, the month labels and the legend
    canvas = tk.Canvas(section, width=280, height=180, bg=theme.BG, highlightthickness=0)
    canvas.pack()

    # wraplength=260 moves long text onto a new line instead of stretching the window
    info_label = tk.Label(section, text="Click a square to see details", bg=theme.BG, fg=theme.TEXT, font=("Arial", 10), wraplength=260)
    info_label.pack()

    refresh_heatmap(canvas, info_label, user_id)
    return canvas, info_label


# Turn a number of days into text: "1 day" or "5 days"
def day_text(number):
    if number == 1:
        return "1 day"
    return str(number) + " days"


# Build a table with each habit's current streak, best streak and 30-day completion %
def create_stats_section(parent, user_id):
    section = tk.Frame(parent, bg=theme.CARD, highlightbackground=theme.BORDER, highlightthickness=1, padx=20, pady=15)
    section.pack(fill="x", pady=(15, 0))

    title_label = tk.Label(section, text="Stats", bg=theme.CARD, fg=theme.TEXT, font=("Arial", 12, "bold"))
    title_label.pack(anchor="w", pady=(0, 8))

    habits = database.get_all_habits(user_id)
    if len(habits) == 0:
        empty_label = tk.Label(section, text="No habits yet. Add some on the Today tab.", bg=theme.CARD, fg=theme.MUTED, font=("Arial", 10))
        empty_label.pack(anchor="w")
        return section

    # A grid of labels: row 0 holds the headings, then one row per habit
    table = tk.Frame(section, bg=theme.CARD)
    table.pack(anchor="w")

    headings = ["Habit", "Current streak", "Best streak", "Last 30 days"]
    for column in range(len(headings)):
        heading_label = tk.Label(table, text=headings[column], bg=theme.CARD, fg=theme.MUTED, font=("Arial", 9, "bold"))
        heading_label.grid(row=0, column=column, sticky="w", padx=(0, 30), pady=(0, 6))

    row = 1
    for habit_id, name in habits:
        values = [
            name,
            day_text(database.get_streak(habit_id)),
            day_text(database.get_best_streak(habit_id)),
            str(database.get_completion_percent(habit_id)) + "%",
        ]
        for column in range(len(values)):
            # The percent column is in the accent color so it stands out
            if column == 3:
                color = theme.ACCENT
            else:
                color = theme.TEXT
            value_label = tk.Label(table, text=values[column], bg=theme.CARD, fg=color, font=("Arial", 10))
            value_label.grid(row=row, column=column, sticky="w", padx=(0, 30), pady=2)
        row = row + 1

    return section


# Return the last 7 days as a list of (date, count), oldest first and today last
def get_week_counts(user_id):
    today = date.today()
    week = []
    # days_ago goes 6, 5, 4, 3, 2, 1, 0, so the list starts 6 days ago and ends with today
    for days_ago in range(6, -1, -1):
        day = today - timedelta(days=days_ago)
        count = database.get_count_for_date(day.isoformat(), user_id)
        week.append((day, count))
    return week


# Return the points of a bar with rounded top corners and square bottom corners (for create_polygon smooth=True)
def rounded_top_points(x1, y1, x2, y2, radius):
    # With smooth=True a single corner point gets curved, so each top corner is one point with
    # neighbors `radius` away on both sides. A point repeated 3 times is not curved, so the bottom stays square
    return [
        x1, y2, x1, y2, x1, y2,
        x1, y1 + radius, x1, y1, x1 + radius, y1,
        x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2, x2, y2, x2, y2,
    ]


# Move every bar to `fraction` of its final height (0 = flat, 1 = full)
def set_bar_heights(chart, bars, fraction):
    for bar in bars:
        height = bar["height"] * fraction
        top = bar["base"] - height
        # A bar can't have corners rounder than half its own height
        radius = min(BAR_RADIUS, height / 2)
        chart.coords(bar["item"], *rounded_top_points(bar["left"], top, bar["left"] + BAR_WIDTH, bar["base"], radius))


# Grow the bars one small step towards full height, then ask after() for the next step
def grow_bars(chart, bars, step):
    if not chart.winfo_exists():
        return

    # "Ease out": fast at first, slow at the end, so the bars settle gently at their height
    eased = 1 - (1 - step / GROW_STEPS) ** 3
    set_bar_heights(chart, bars, eased)

    if step < GROW_STEPS:
        chart.winfo_toplevel().after(GROW_DELAY, lambda: grow_bars(chart, bars, step + 1))


# Show "3 habits" just above a bar while the mouse is over its column
def show_bar_value(chart, bar):
    if bar["count"] == 1:
        text = "1 habit"
    else:
        text = str(bar["count"]) + " habits"
    top = bar["base"] - bar["height"]
    # Center the label over the bar, but never let it stick out past the left or right edge of the chart
    font = tkfont.Font(family="Arial", size=9, weight="bold")
    half_width = font.measure(text) / 2 + 2
    x = min(max(bar["left"] + BAR_WIDTH / 2, half_width), CHART_WIDTH - half_width)
    # state="disabled": the label is drawn but ignores the mouse. Otherwise, on a short bar, the label would
    # appear right under the pointer, count as "leaving" the column, get deleted, and reappear, forever
    chart.create_text(x, top - 8, text=text, fill=theme.TEXT, font=font, tags="hover_label", state="disabled")


# Hide the hover label again when the mouse leaves the column
def hide_bar_value(chart):
    chart.delete("hover_label")


# Build a card with a bar chart of the last 7 days; return the card (the caller packs it)
def draw_weekly_chart(parent, user_id):
    card = tk.Frame(parent, bg=theme.CARD, highlightthickness=1, highlightbackground=theme.BORDER, padx=16, pady=16)

    week = get_week_counts(user_id)
    total = sum(count for day, count in week)

    # Header: "This week" on the left, the total and best day on the right
    header = tk.Frame(card, bg=theme.CARD)
    header.pack(fill="x", pady=(0, 8))
    title_label = tk.Label(header, text="This week", bg=theme.CARD, fg=theme.TEXT, font=("Arial", 12, "bold"))
    title_label.pack(side="left")
    if total == 0:
        summary = "0 habits done"
    else:
        # max(..., key=...) picks the (day, count) pair with the biggest count
        best_day, best_count = max(week, key=lambda pair: pair[1])
        if total == 1:
            word = "habit"
        else:
            word = "habits"
        summary = str(total) + " " + word + " done · Best day: " + best_day.strftime("%A")
    summary_label = tk.Label(header, text=summary, bg=theme.CARD, fg=theme.MUTED, font=("Arial", 10))
    summary_label.pack(side="right", padx=(20, 0))

    chart = tk.Canvas(card, width=CHART_WIDTH, height=CHART_HEIGHT, bg=theme.CARD, highlightthickness=0)
    chart.pack()

    base = CHART_HEIGHT - CHART_BOTTOM          # the y of the bottom of the bars (the 0% line)
    plot_height = base - CHART_TOP              # how tall a 100% bar is
    # A full bar means every habit was done; max(1, ...) avoids dividing by 0 when there are no habits
    habit_count = max(1, len(database.get_all_habits(user_id)))

    # Guide lines at 0%, 50% and 100%
    for fraction in (0, 0.5, 1):
        y = base - plot_height * fraction
        chart.create_line(0, y, CHART_WIDTH, y, fill=theme.BORDER)

    slot_width = CHART_WIDTH / 7
    bars = []
    for i in range(7):
        day, count = week[i]
        is_today = i == 6
        left = i * slot_width + (slot_width - BAR_WIDTH) / 2
        column_tag = "column" + str(i)

        # An invisible (card-colored) rectangle covering the whole column, so even a short bar is easy to hover
        chart.create_rectangle(i * slot_width, CHART_TOP, (i + 1) * slot_width, base, fill=theme.CARD, outline="", tags=(column_tag, "slot"))

        # Today's bar and day name are in the accent color, the other days in the heatmap blue
        if is_today:
            color = theme.ACCENT
            label_color = theme.ACCENT
        else:
            color = theme.HEATMAP[3]
            label_color = theme.MUTED
        # Start flat (the grow animation gives it its height); count / habits of the plot height, at most 100%
        item = chart.create_polygon(rounded_top_points(left, base, left + BAR_WIDTH, base, 0), smooth=True, fill=color, outline="", tags=column_tag)
        bar = {"item": item, "left": left, "base": base, "count": count, "height": plot_height * min(1, count / habit_count)}
        bars.append(bar)

        chart.create_text(left + BAR_WIDTH / 2, base + 12, text=day.strftime("%a"), fill=label_color, font=("Arial", 9))

        chart.tag_bind(column_tag, "<Enter>", lambda event, bar=bar: show_bar_value(chart, bar))
        chart.tag_bind(column_tag, "<Leave>", lambda event: hide_bar_value(chart))

    # Push the invisible column rectangles to the very back, so the guide lines show on top of them
    chart.tag_lower("slot")

    grow_bars(chart, bars, 1)
    return card


if __name__ == "__main__":
    database.create_tables()

    # Log in as a test user (create_user just returns False if "demo" already exists)
    database.create_user("demo", "demo123")
    user_id = database.check_login("demo", "demo123")

    window = tk.Tk()
    window.title("Consistify - Heatmap")
    window.configure(bg=theme.BG, padx=20, pady=20)

    canvas, info_label = create_heatmap_section(window, user_id)
    draw_weekly_chart(window, user_id).pack(pady=(10, 0))
    create_stats_section(window, user_id)

    # A test button that redraws the heatmap, like main.py will do after a checkbox is ticked
    refresh_button = tk.Button(window, text="Refresh", command=lambda: refresh_heatmap(canvas, info_label, user_id))
    refresh_button.pack(pady=(10, 0))

    window.mainloop()