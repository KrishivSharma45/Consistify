import tkinter as tk
# Import math for cos and sin, which find the middle of each donut slice
import math
from datetime import date, timedelta

import database
# Import the app's shared colors and font, and our reusable widgets (cards, rings, pills, scroll page)
import theme
import ui

# 90-day heatmap
NUMBER_OF_DAYS = 90
HEAT_LEFT = 32         # space on the left for "Mon", "Wed", "Fri"
HEAT_TOP = 18          # space on top for the month names
HEAT_GAP = 3           # space between squares
LEGEND_HEIGHT = 28     # space under the grid for "Less [] More"

# Weekly bar chart (in pixels)
CHART_WIDTH = 420
CHART_HEIGHT = 170
CHART_TOP = 26       # space above the tallest bar, for its value
CHART_BOTTOM = 22    # space under the bars, for the day names
BAR_WIDTH = 28
BAR_RADIUS = 10      # how round the top corners of a bar are (smoothing curves about half of this)
GROW_STEPS = 20      # the grow animation takes 20 steps...
GROW_DELAY = 20      # ...20 milliseconds apart, so about 400 ms in total

# Donut chart and consistency ring (in pixels)
DONUT_SIZE = 170     # outer diameter of the donut
DONUT_HOLE = 0.62    # the hole is 62% as wide as the donut
DONUT_POP = 7        # how far a slice moves outward when hovered
RING_SIZE = 150      # outer diameter of the consistency ring
RING_THICKNESS = 14
# Slice colors, used in this order: the accent, its lighter hover color, then the heatmap shades strongest to weakest
DONUT_COLORS = [theme.ACCENT, theme.ACCENT_HOVER, theme.HEATMAP[3], theme.HEATMAP[2], theme.HEATMAP[1], theme.MUTED]


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
        text = text + "  ·  " + ", ".join(names)

    info_label.config(text=text)


# Change the mouse pointer when it moves over or off a square
def set_cursor(canvas, cursor_name):
    canvas.config(cursor=cursor_name)


# Turn a number of days into text: "1 day" or "5 days"
def day_text(number):
    if number == 1:
        return "1 day"
    return str(number) + " days"


# ---------------------------------------------------------------- data

# Ask the database how many of one user's habits were done on each of the last 90 days: {"2026-11-07": 2, ...}
def get_counts_from_database(user_id):
    counts = {}
    today = date.today()
    for days_ago in range(NUMBER_OF_DAYS):
        day = today - timedelta(days=days_ago)
        counts[day.isoformat()] = database.get_count_for_date(day.isoformat(), user_id)
    return counts


# Count every check-in (log row) this user has ever made. database.py has no function for this, and it must not
# be changed, so this only READS, with a ? placeholder, through database.get_connection
def get_total_checkins(user_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM logs JOIN habits ON habits.id = logs.habit_id WHERE habits.user_id = ?",
        (user_id,),
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total


# Return [(habit name, check-ins in the last 30 days), ...] for every habit of this user
def get_habit_counts_30(user_id):
    today = date.today()
    result = []
    for habit_id, name in database.get_all_habits(user_id):
        count = 0
        for days_ago in range(30):
            if database.is_done(habit_id, (today - timedelta(days=days_ago)).isoformat()):
                count = count + 1
        result.append((name, count))
    return result


# Return the highest best-ever streak among this user's habits (0 if there are none)
def get_longest_streak(user_id):
    best = 0
    for habit_id, name in database.get_all_habits(user_id):
        best = max(best, database.get_best_streak(habit_id))
    return best


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


# ---------------------------------------------------------------- small heatmap (used by the Today page)

# Draw a small heatmap of the last `days` days on an existing canvas: `columns` squares per row,
# oldest at the top-left, today at the bottom-right with a light outline (wipes the canvas first, so it can redraw).
# empty_color is used for days with nothing done (HEATMAP[0] can be the same color as a card, which would hide them)
def draw_mini_heatmap(canvas, user_id, days=30, columns=6, square=24, gap=5, empty_color=None):
    canvas.delete("all")
    today = date.today()
    for i in range(days):
        # i = 0 is the oldest day (days - 1 days ago); the last i is today
        day = today - timedelta(days=days - 1 - i)
        count = database.get_count_for_date(day.isoformat(), user_id)
        # i // columns is the row and i % columns the column
        x1 = (i % columns) * (square + gap)
        y1 = (i // columns) * (square + gap)
        border = theme.TEXT if day == today else ""
        color = get_color(count)
        if count == 0 and empty_color is not None:
            color = empty_color
        canvas.create_rectangle(x1, y1, x1 + square, y1 + square, fill=color, outline=border)


# Create a canvas just big enough for a small heatmap, draw it, and return the canvas
def create_mini_heatmap(parent, user_id, days=30, columns=6, square=24, gap=5, empty_color=None):
    rows = (days + columns - 1) // columns
    width = columns * (square + gap) - gap
    height = rows * (square + gap) - gap
    # +1 so today's 1px outline on the right/bottom edge isn't cut off
    canvas = tk.Canvas(parent, width=width + 1, height=height + 1, bg=parent.cget("bg"), highlightthickness=0)
    draw_mini_heatmap(canvas, user_id, days, columns, square, gap, empty_color)
    return canvas


# ---------------------------------------------------------------- 90-day heatmap card

# Draw the 90-day heatmap with squares sized to fill the canvas width (called again whenever the card is resized)
def draw_heatmap(canvas, counts, info_label, user_id):
    canvas.delete("all")
    width = canvas.winfo_width()
    today = date.today()
    first_day = today - timedelta(days=NUMBER_OF_DAYS - 1)
    # One column per week; first_day.weekday() is how far into its week the first day falls
    columns = (NUMBER_OF_DAYS - 1 + first_day.weekday()) // 7 + 1
    # Each "cell" is a square plus its gap; the cells share the width left over after the weekday labels
    cell = max(8, (width - HEAT_LEFT) / columns)
    square = cell - HEAT_GAP

    # Make the canvas exactly tall enough for 7 rows plus the month names and the legend
    needed = int(HEAT_TOP + 7 * cell + LEGEND_HEIGHT)
    if abs(int(canvas.cget("height")) - needed) > 1:
        canvas.config(height=needed)

    for i in range(NUMBER_OF_DAYS):
        day = first_day + timedelta(days=i)
        count = counts.get(day.isoformat(), 0)
        # The row is the weekday (Mon = 0 at the top), the column is the week
        column = (i + first_day.weekday()) // 7
        x1 = HEAT_LEFT + column * cell
        y1 = HEAT_TOP + day.weekday() * cell
        # Empty days use BORDER, because HEATMAP[0] is the same color as the card
        if count > 0:
            color = get_color(count)
        else:
            color = theme.BORDER
        if day == today:
            square_item = canvas.create_rectangle(x1, y1, x1 + square, y1 + square, fill=color, outline=theme.ACCENT, width=2)
        else:
            square_item = canvas.create_rectangle(x1, y1, x1 + square, y1 + square, fill=color, outline="")
        canvas.tag_bind(square_item, "<Button-1>", lambda event, d=day.isoformat(), c=count: show_day(info_label, d, c, user_id))
        canvas.tag_bind(square_item, "<Enter>", lambda event: set_cursor(canvas, "hand2"))
        canvas.tag_bind(square_item, "<Leave>", lambda event: set_cursor(canvas, ""))

        # Month names above the column of each month's first day (and above the very first column)
        if day.day == 1 or i == 0:
            canvas.create_text(x1, HEAT_TOP - 9, text=day.strftime("%b"), fill=theme.MUTED, font=(theme.FONT, 8), anchor="w")

    for row, name in [(0, "Mon"), (2, "Wed"), (4, "Fri")]:
        canvas.create_text(0, HEAT_TOP + row * cell + square / 2, text=name, fill=theme.MUTED, font=(theme.FONT, 8), anchor="w")

    # "Less [5 boxes] More" under the grid
    legend_y = HEAT_TOP + 7 * cell + 8
    canvas.create_text(HEAT_LEFT, legend_y + 6, text="Less", fill=theme.MUTED, font=(theme.FONT, 8), anchor="w")
    legend_colors = [theme.BORDER, theme.HEATMAP[1], theme.HEATMAP[2], theme.HEATMAP[3], theme.HEATMAP[4]]
    for level in range(5):
        x1 = HEAT_LEFT + 32 + level * 15
        canvas.create_rectangle(x1, legend_y, x1 + 12, legend_y + 12, fill=legend_colors[level], outline="")
    canvas.create_text(HEAT_LEFT + 32 + 5 * 15 + 4, legend_y + 6, text="More", fill=theme.MUTED, font=(theme.FONT, 8), anchor="w")


# Build the "Last 90 days" card: the heatmap (it fills the card's width) and a line for the clicked day's details
def create_heatmap_card(parent, user_id, counts):
    card = ui.create_card(parent, "Last 90 days", "Click a square to see the habits done that day")
    canvas = tk.Canvas(card, height=200, bg=theme.CARD, highlightthickness=0)
    canvas.pack(fill="x")
    info_label = tk.Label(card, text="", font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD, wraplength=420, justify="left")
    info_label.pack(anchor="w", pady=(6, 0))
    # The canvas's width is only known once it's on screen (and changes on resize), so draw it from <Configure>
    canvas.bind("<Configure>", lambda event: draw_heatmap(canvas, counts, info_label, user_id))
    return card


# ---------------------------------------------------------------- donut card

# Set every slice to `fraction` of its final size, so the donut sweeps in from 12 o'clock
def set_donut_slices(canvas, slices, total, fraction):
    done_so_far = 0
    for piece in slices:
        # Clockwise from the top: start at 90 degrees minus everything already drawn, extent negative
        start = 90 - 360 * done_so_far / total * fraction
        extent = -min(359.9, 360 * piece["count"] / total) * fraction
        canvas.itemconfigure(piece["item"], start=start, extent=extent)
        done_so_far = done_so_far + piece["count"]


# Hovering a slice: slide it a few pixels outward (along its middle angle) and show its numbers
def on_slice_enter(canvas, piece, label, total):
    if piece["moved"]:
        return
    # The middle of the slice, in degrees: 0 is 3 o'clock and angles go counter-clockwise, like in maths
    middle = math.radians(piece["middle"])
    # cos gives the sideways part; the canvas's y grows DOWNWARDS, so the up/down part is minus sin
    canvas.move(piece["item"], DONUT_POP * math.cos(middle), -DONUT_POP * math.sin(middle))
    piece["moved"] = True
    percent = round(piece["count"] * 100 / total)
    label.config(text=piece["name"] + ": " + str(piece["count"]) + " (" + str(percent) + "%)", fg=theme.TEXT)


# Leaving a slice: slide it back into place
def on_slice_leave(canvas, piece, label):
    if not piece["moved"]:
        return
    middle = math.radians(piece["middle"])
    canvas.move(piece["item"], -DONUT_POP * math.cos(middle), DONUT_POP * math.sin(middle))
    piece["moved"] = False
    label.config(text="Hover a slice for details", fg=theme.MUTED)


# Build the "Habit share" card: a donut with one slice per habit (check-ins in the last 30 days) and a legend
def create_donut_card(parent, user_id):
    card = ui.create_card(parent, "Habit share", "Check-ins per habit, last 30 days")
    data = [(name, count) for name, count in get_habit_counts_30(user_id) if count > 0]
    # Biggest slice first
    data.sort(key=lambda pair: pair[1], reverse=True)
    total = sum(count for name, count in data)

    size = DONUT_SIZE + 2 * DONUT_POP
    middle = size / 2
    radius = DONUT_SIZE / 2
    canvas = tk.Canvas(card, width=size, height=size, bg=theme.CARD, highlightthickness=0)
    canvas.pack()

    if total == 0:
        # Empty state: just the grey ring and a message
        ui.draw_ring(canvas, middle, middle, radius - 14, 28, 0)
        canvas.create_text(middle, middle, text="No data yet", fill=theme.MUTED, font=(theme.FONT, 10))
        tk.Label(card, text="Tick some habits and they'll show up here.", font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD).pack(pady=(8, 0))
        return card

    box = (middle - radius, middle - radius, middle + radius, middle + radius)
    hover_label = tk.Label(card, text="Hover a slice for details", font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    slices = []
    done_so_far = 0
    for i in range(len(data)):
        name, count = data[i]
        color = DONUT_COLORS[i % len(DONUT_COLORS)]
        # style="pieslice" draws a filled wedge from the centre; it starts with no size and grows in
        item = canvas.create_arc(*box, start=90, extent=0, style="pieslice", fill=color, outline=theme.CARD, width=2)
        # The final middle angle of this slice (used to push it outward on hover)
        slice_middle = 90 - 360 * (done_so_far + count / 2) / total
        piece = {"item": item, "name": name, "count": count, "middle": slice_middle, "moved": False}
        slices.append(piece)
        canvas.tag_bind(item, "<Enter>", lambda event, piece=piece: on_slice_enter(canvas, piece, hover_label, total))
        canvas.tag_bind(item, "<Leave>", lambda event, piece=piece: on_slice_leave(canvas, piece, hover_label))
        done_so_far = done_so_far + count

    # The hole: a card-colored circle drawn on top of the middle of the pie turns it into a donut.
    # state="disabled" so the hole never "steals" the mouse from the slices around it
    hole = radius * DONUT_HOLE
    canvas.create_oval(middle - hole, middle - hole, middle + hole, middle + hole, fill=theme.CARD, outline=theme.CARD, state="disabled")
    canvas.create_text(middle, middle - 10, text=str(total), fill=theme.TEXT, font=(theme.FONT, 18, "bold"), state="disabled")
    canvas.create_text(middle, middle + 18, text="check-ins", fill=theme.MUTED, font=(theme.FONT, 9), state="disabled")

    hover_label.pack(pady=(6, 8))
    # Legend: a colored dot, the habit name and its count, one line per slice
    for i in range(len(data)):
        name, count = data[i]
        line = tk.Frame(card, bg=theme.CARD)
        line.pack(fill="x", pady=1)
        dot = tk.Canvas(line, width=10, height=10, bg=theme.CARD, highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=DONUT_COLORS[i % len(DONUT_COLORS)], outline="")
        dot.pack(side="left", padx=(0, 8))
        tk.Label(line, text=name, font=(theme.FONT, 9), fg=theme.TEXT, bg=theme.CARD).pack(side="left")
        tk.Label(line, text=str(count), font=(theme.FONT, 9, "bold"), fg=theme.MUTED, bg=theme.CARD).pack(side="right")

    # Grow the slices in from nothing
    ui.animate(canvas, lambda fraction: set_donut_slices(canvas, slices, total, fraction), steps=30)
    return card


# ---------------------------------------------------------------- weekly bar chart card

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


# Move every bar (and the number above it) to `fraction` of its final height (0 = flat, 1 = full)
def set_bar_heights(chart, bars, fraction):
    for bar in bars:
        height = bar["height"] * fraction
        top = bar["base"] - height
        # A bar can't have corners rounder than half its own height
        radius = min(BAR_RADIUS, height / 2)
        chart.coords(bar["item"], *rounded_top_points(bar["left"], top, bar["left"] + BAR_WIDTH, bar["base"], radius))
        chart.coords(bar["value"], bar["left"] + BAR_WIDTH / 2, top - 9)


# Grow the bars one small step towards full height, then ask after() for the next step
def grow_bars(chart, bars, step):
    if not chart.winfo_exists():
        return

    # "Ease out": fast at first, slow at the end, so the bars settle gently at their height
    eased = 1 - (1 - step / GROW_STEPS) ** 3
    set_bar_heights(chart, bars, eased)

    if step < GROW_STEPS:
        chart.winfo_toplevel().after(GROW_DELAY, lambda: grow_bars(chart, bars, step + 1))


# Build a card with a bar chart of the last 7 days (value above each bar, dashed average line); return the card
def draw_weekly_chart(parent, user_id):
    week = get_week_counts(user_id)
    total = sum(count for day, count in week)

    # The subtitle: the total and the best day of the week
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
    card = ui.create_card(parent, "This week", summary)

    chart = tk.Canvas(card, width=CHART_WIDTH, height=CHART_HEIGHT, bg=theme.CARD, highlightthickness=0)
    chart.pack(anchor="w")

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

        # Today's bar and day name are in the accent color, the other days in a heatmap shade
        if is_today:
            color, label_color = theme.ACCENT, theme.ACCENT
        else:
            color, label_color = theme.HEATMAP[3], theme.MUTED
        # Start flat (the grow animation gives it its height); count / habits of the plot height, at most 100%
        item = chart.create_polygon(rounded_top_points(left, base, left + BAR_WIDTH, base, 0), smooth=True, fill=color, outline="")
        value = chart.create_text(left + BAR_WIDTH / 2, base - 9, text=str(count), fill=theme.TEXT, font=(theme.FONT, 9, "bold"))
        bars.append({"item": item, "value": value, "left": left, "base": base, "height": plot_height * min(1, count / habit_count)})

        chart.create_text(left + BAR_WIDTH / 2, base + 12, text=day.strftime("%a"), fill=label_color, font=(theme.FONT, 9))

    # The weekly average as a dashed line, at the height a bar of the average size would reach
    average = total / 7
    average_y = base - plot_height * min(1, average / habit_count)
    # dash=(4, 3): draw 4 pixels, skip 3, and repeat
    chart.create_line(0, average_y, CHART_WIDTH - 26, average_y, fill=theme.MUTED, dash=(4, 3))
    chart.create_text(CHART_WIDTH, average_y, text="avg", fill=theme.MUTED, font=(theme.FONT, 8), anchor="e")

    grow_bars(chart, bars, 1)
    return card


# ---------------------------------------------------------------- consistency ring card

# Build the "Consistency" card: a thick ring showing the % of the last 30 days with at least one habit done
def create_consistency_card(parent, counts):
    card = ui.create_card(parent, "Consistency", "Days with at least 1 habit done")
    today = date.today()
    active = 0
    for days_ago in range(30):
        if counts.get((today - timedelta(days=days_ago)).isoformat(), 0) > 0:
            active = active + 1
    fraction = active / 30
    percent = round(fraction * 100)

    middle = RING_SIZE / 2
    radius = (RING_SIZE - RING_THICKNESS) / 2
    canvas = tk.Canvas(card, width=RING_SIZE, height=RING_SIZE, bg=theme.CARD, highlightthickness=0)
    canvas.pack()
    number = canvas.create_text(middle, middle, text="0%", fill=theme.TEXT, font=(theme.FONT, 24, "bold"))
    tk.Label(card, text=str(active) + " of 30 days", font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD).pack(pady=(8, 0))

    ui.animate(canvas, lambda progress: grow_ring(canvas, number, middle, radius, fraction, percent, progress), steps=36)
    return card


# One animation step: redraw the ring at `progress` (0 to 1) of its final size and count the % up with it
def grow_ring(canvas, number, middle, radius, fraction, percent, progress):
    ui.draw_ring(canvas, middle, middle, radius, RING_THICKNESS, fraction * progress)
    canvas.itemconfig(number, text=str(round(percent * progress)) + "%")


# ---------------------------------------------------------------- habits table card

# Color one table row: a slightly lighter background while hovered, the card color otherwise
def paint_table_row(row, hovered):
    background = theme.BORDER if hovered else theme.CARD
    for widget in row["parts"]:
        widget.config(bg=background)
    # The progress bar's track is BORDER, so on a hovered row it uses the darker BG to stay visible
    row["percent"]["track"] = theme.BG if hovered else theme.BORDER
    draw_table_bar(row["percent"])


# The mouse left a table row (or moved onto something inside it): un-hover only if it really left the row
def leave_table_row(row):
    x, y = row["frame"].winfo_pointerxy()
    if not ui.is_inside(row["frame"].winfo_containing(x, y), row["frame"]):
        paint_table_row(row, False)


# Draw a row's "last 30 days" bar: a thin track across the canvas and an ACCENT fill for the habit's %
def draw_table_bar(bar_info):
    bar = bar_info["canvas"]
    if not bar.winfo_exists():
        return
    bar.delete("all")
    width = bar.winfo_width()
    bar.create_rectangle(0, 0, width, 6, fill=bar_info["track"], outline="")
    if bar_info["fraction"] > 0:
        bar.create_rectangle(0, 0, width * bar_info["fraction"], 6, fill=theme.ACCENT, outline="")


# Set up a table row's 4 columns (the same weights in every row, so the columns line up from row to row)
def setup_table_columns(frame):
    for column, weight in enumerate([3, 2, 2, 3]):
        frame.columnconfigure(column, weight=weight, uniform="table")


# Return a "🔥 N" pill: accent on the orange tint when N > 0, grey otherwise
def streak_pill(parent, number):
    if number > 0:
        return ui.create_pill(parent, "🔥 " + str(number), theme.ACCENT, theme.ACCENT_SOFT)
    return ui.create_pill(parent, "🔥 0", theme.MUTED, theme.BORDER)


# Build the habits table card: each habit's current streak, best streak and last-30-days completion
def create_habit_table_card(parent, user_id):
    card = ui.create_card(parent, "Habits", "Sorted by how often you did them in the last 30 days")

    rows_data = []
    for habit_id, name in database.get_all_habits(user_id):
        rows_data.append({
            "name": name,
            "current": database.get_streak(habit_id),
            "best": database.get_best_streak(habit_id),
            "percent": database.get_completion_percent(habit_id),
        })
    if len(rows_data) == 0:
        tk.Label(card, text="No habits yet. Add some on the Today tab.", font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w")
        return card
    # Highest "last 30 days" first
    rows_data.sort(key=lambda info: info["percent"], reverse=True)

    header = tk.Frame(card, bg=theme.CARD)
    header.pack(fill="x", pady=(0, 6))
    setup_table_columns(header)
    for column, text in enumerate(["Habit", "Current streak", "Best streak", "Last 30 days"]):
        tk.Label(header, text=text, font=(theme.FONT, 9, "bold"), fg=theme.MUTED, bg=theme.CARD).grid(row=0, column=column, sticky="w", padx=8)

    for i in range(len(rows_data)):
        info = rows_data[i]
        # A 1px line between rows (and under the header)
        tk.Frame(card, bg=theme.BORDER, height=1).pack(fill="x")

        frame = tk.Frame(card, bg=theme.CARD, pady=8)
        frame.pack(fill="x")
        setup_table_columns(frame)

        # The top habit gets a crown (only if it was actually done at least once)
        name_text = info["name"]
        if i == 0 and info["percent"] > 0:
            name_text = "👑 " + name_text
        name = tk.Label(frame, text=name_text, font=(theme.FONT, 10), fg=theme.TEXT, bg=theme.CARD)
        name.grid(row=0, column=0, sticky="w", padx=8)
        current = streak_pill(frame, info["current"])
        current.grid(row=0, column=1, sticky="w", padx=8)
        best = streak_pill(frame, info["best"])
        best.grid(row=0, column=2, sticky="w", padx=8)

        # Last 30 days: a thin bar that stretches across the column, with the % next to it
        cell = tk.Frame(frame, bg=theme.CARD)
        cell.grid(row=0, column=3, sticky="ew", padx=8)
        percent_label = tk.Label(cell, text=str(info["percent"]) + "%", font=(theme.FONT, 9, "bold"), fg=theme.TEXT, bg=theme.CARD, width=4, anchor="e")
        percent_label.pack(side="right")
        bar = tk.Canvas(cell, height=6, bg=theme.CARD, highlightthickness=0)
        bar.pack(side="left", fill="x", expand=True, padx=(0, 6))
        bar_info = {"canvas": bar, "fraction": info["percent"] / 100, "track": theme.BORDER}
        bar.bind("<Configure>", lambda event, bar_info=bar_info: draw_table_bar(bar_info))

        row = {"frame": frame, "parts": [frame, name, current, best, cell, percent_label, bar], "percent": bar_info}
        frame.bind("<Enter>", lambda event, row=row: paint_table_row(row, True))
        frame.bind("<Leave>", lambda event, row=row: leave_table_row(row))
    return card


# ---------------------------------------------------------------- the whole page

# Build the Progress page inside parent: summary tiles, heatmap + donut, weekly chart + ring, habits table
def build_progress_page(parent, user_id):
    page = ui.create_scroll_page(parent)
    counts = get_counts_from_database(user_id)

    # Row 1: four equal summary tiles
    row1 = ui.add_page_row(page)
    for column in range(4):
        row1.columnconfigure(column, weight=1, uniform="summary")
    today = date.today()
    last_30 = 0
    for days_ago in range(30):
        last_30 = last_30 + counts.get((today - timedelta(days=days_ago)).isoformat(), 0)
    # Active days counts the last 90 days; the average uses the last 30
    tiles = [
        ("✅", "Total check-ins", str(get_total_checkins(user_id))),
        ("📅", "Active days", str(sum(1 for count in counts.values() if count > 0))),
        # :.1f means "with 1 decimal place", e.g. 1.4
        ("📊", "Avg per day", f"{last_30 / 30:.1f}"),
        ("🔥", "Longest streak", str(get_longest_streak(user_id))),
    ]
    for column in range(4):
        icon, label, value = tiles[column]
        tile, number = ui.create_stat_tile(row1, icon, label)
        number.config(text=value)
        # 4px on each side keeps all four tiles exactly the same width
        tile.grid(row=0, column=column, sticky="nsew", padx=4)

    # Rows 2 and 3: two cards side by side, sharing the width 3 : 2 (about 60% / 40%) with a 16px gap
    row2 = ui.add_page_row(page)
    row3 = ui.add_page_row(page)
    for row in (row2, row3):
        row.columnconfigure(0, weight=3, uniform="split")
        row.columnconfigure(1, weight=2, uniform="split")
    create_heatmap_card(row2, user_id, counts).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    create_donut_card(row2, user_id).grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    draw_weekly_chart(row3, user_id).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    create_consistency_card(row3, counts).grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    # Row 4: the habits table across the full width
    row4 = ui.add_page_row(page)
    create_habit_table_card(row4, user_id).pack(fill="x")
    return page


if __name__ == "__main__":
    database.create_tables()

    # Log in as a test user (create_user just returns False if "demo" already exists)
    database.create_user("demo", "demo123")
    user_id = database.check_login("demo", "demo123")

    window = tk.Tk()
    window.title("Consistify - Progress")
    # The same size as the dashboard's content area in main.py
    window.geometry("900x700")
    window.configure(bg=theme.BG)

    build_progress_page(window, user_id)
    window.mainloop()
