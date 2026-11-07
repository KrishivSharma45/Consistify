# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import messagebox, tkinter's ready-made pop-up message windows
from tkinter import messagebox
# Import filedialog, tkinter's ready-made "Open" and "Save As" windows
from tkinter import filedialog
# Import tkinter's font tool, so the streak pill can measure its text
import tkinter.font as tkfont
# Import ttk for the habit list's scrollbar (ttk scrollbars can be colored to match the theme)
from tkinter import ttk
# Import sys to check whether we are running on a Mac (the mouse wheel works differently there)
import sys
# Import date, datetime and timedelta for today's date, the current hour and the last 7 days
from datetime import date, datetime, timedelta

# Import our own database.py so we can save and load habits
import database
# Import the app's shared colors and font
import theme
# Import our reusable widgets (rounded shapes, buttons, confetti)
import ui
# Import heatmap.py for the small "Last 30 days" heatmap, and badges.py for each badge's emoji
import heatmap
import badges

PLACEHOLDER = "Add a new habit..."   # grey hint text shown in the empty Add box
CHECK_SIZE = 22                       # size of the round checkbox (pixels)
LIST_WHEEL_PIXELS = 40                # how far one mouse-wheel notch scrolls the habit list

# Short habit quotes for the "Quote of the day" card: (quote, author)
QUOTES = [
    ("We are what we repeatedly do.", "Will Durant"),
    ("Motivation is what gets you started. Habit is what keeps you going.", "Jim Ryun"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Success is the sum of small efforts, repeated day in and day out.", "Robert Collier"),
    ("First forget inspiration. Habit is more dependable.", "Octavia Butler"),
    ("You do not rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
    ("A journey of a thousand miles begins with a single step.", "Lao Tzu"),
    ("Every action you take is a vote for the type of person you wish to become.", "James Clear"),
    ("Habits change into character.", "Ovid"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese proverb"),
    ("Small steps every day add up to big results.", "Unknown"),
    ("Don't break the chain.", "Jerry Seinfeld"),
    ("Discipline is remembering what you want.", "David Campbell"),
    ("Progress, not perfection.", "Unknown"),
]

BAR_HEIGHT = 12        # height of the progress bar (pixels)
FILL_STEPS = 15        # the fill animation takes 15 small steps...
FILL_DELAY = 20        # ...20 milliseconds apart, so about 300 ms in total


# Create the main window, give it a title, a size, and a dark background
def create_window():
    window = tk.Tk()
    window.title("Consistify")
    # The same size as the dashboard's content area in main.py
    window.geometry("900x700")
    window.configure(bg=theme.BG)
    return window


# Return "Good morning ☀️", "Good afternoon ☀️" or "Good evening 🌙" (without the name), from the current hour
def get_greeting():
    # datetime.now().hour is a number from 0 (midnight) to 23 (11 pm)
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning", "☀️"
    elif 12 <= hour < 17:
        return "Good afternoon", "☀️"
    else:
        return "Good evening", "🌙"


# Create the header row: greeting and today's date on the left, the "Export CSV" button on the right
def create_page_header(window, user_id, username):
    header = tk.Frame(window, bg=theme.BG)
    header.pack(fill="x", padx=40, pady=(20, 10))

    left = tk.Frame(header, bg=theme.BG)
    left.pack(side="left")
    greeting, emoji = get_greeting()
    greeting_label = tk.Label(left, text=greeting + ", " + username + " " + emoji, font=(theme.FONT, 20, "bold"), fg=theme.TEXT, bg=theme.BG)
    greeting_label.pack(anchor="w")
    # e.g. "Saturday, 7 November" (%A is the weekday name, %B the month name)
    today = date.today()
    date_text = today.strftime("%A") + ", " + str(today.day) + " " + today.strftime("%B")
    date_label = tk.Label(left, text=date_text, font=(theme.FONT, 11), fg=theme.MUTED, bg=theme.BG)
    date_label.pack(anchor="w")

    export_button = ui.rounded_button(header, "Export CSV", lambda: on_export_click(user_id), "ghost", font_size=10)
    export_button.pack(side="right")


# Return the highest best-ever streak among one user's habits (0 if there are no habits)
def get_overall_best_streak(user_id):
    best = 0
    for habit_id, name in database.get_all_habits(user_id):
        best = max(best, database.get_best_streak(habit_id))
    return best


# Return this week's completion: habits done over the last 7 days out of (number of habits x 7), as a whole percent
def get_week_percent(user_id):
    habit_count = len(database.get_all_habits(user_id))
    if habit_count == 0:
        return 0

    done = 0
    for days_ago in range(7):
        day = date.today() - timedelta(days=days_ago)
        done = done + database.get_count_for_date(day.isoformat(), user_id)
    return round(done * 100 / (habit_count * 7))


# Create one stat card: an icon tile on the left, a big number and a small label on the right; return the number label
def create_stat_card(row, column, icon, label_text):
    card = tk.Frame(row, bg=theme.CARD, highlightthickness=1, highlightbackground=theme.BORDER, padx=16, pady=16)
    # 3px on each side of every card makes a 6px gap between cards and keeps all four exactly the same width
    card.grid(row=0, column=column, sticky="nsew", padx=3)

    ui.icon_tile(card, icon, size=36).pack(side="left", padx=(0, 12))
    text = tk.Frame(card, bg=theme.CARD)
    text.pack(side="left")
    number = tk.Label(text, text="0", font=(theme.FONT, 18, "bold"), fg=theme.TEXT, bg=theme.CARD)
    number.pack(anchor="w")
    label = tk.Label(text, text=label_text, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    label.pack(anchor="w")
    return number


# Create the row of 4 equal stat cards and return a dictionary of their number labels
def create_stats_row(window):
    row = tk.Frame(window, bg=theme.BG)
    # 37px + each card's own 3px = 40px, so the outer edges line up with the cards below
    row.pack(fill="x", padx=37, pady=(0, 10))
    # Four columns that always stay the same width
    for column in range(4):
        row.columnconfigure(column, weight=1, uniform="stats")

    return {
        "done": create_stat_card(row, 0, "✅", "Done today"),
        "best": create_stat_card(row, 1, "🔥", "Best streak"),
        "week": create_stat_card(row, 2, "📈", "This week"),
        "badges": create_stat_card(row, 3, "🏆", "Badges"),
    }


# Recalculate all four stat numbers from the database and show them
def update_stats_row(stats, user_id):
    done, total = get_today_progress(user_id)
    stats["done"].config(text=str(done) + "/" + str(total))
    stats["best"].config(text=str(get_overall_best_streak(user_id)))
    stats["week"].config(text=str(get_week_percent(user_id)) + "%")
    stats["badges"].config(text=str(len(database.get_badges(user_id))) + "/" + str(len(database.MILESTONES)))


# Show the grey placeholder in the Add box (used when it's empty and doesn't have focus)
def show_placeholder(entry):
    entry.delete(0, tk.END)
    entry.insert(0, PLACEHOLDER)
    entry.config(fg=theme.MUTED)
    # Remember that the text in the box is only the hint, not something the user typed
    entry.placeholder_on = True


# The user clicked (or tabbed) into the Add box: accent border, and remove the placeholder so they can type
def on_entry_focus_in(entry, outline):
    outline.config(bg=theme.ACCENT)
    if entry.placeholder_on:
        entry.delete(0, tk.END)
        entry.config(fg=theme.TEXT)
        entry.placeholder_on = False


# The user left the Add box: normal border, and bring the placeholder back if they left it empty
def on_entry_focus_out(entry, outline):
    outline.config(bg=theme.BORDER)
    if entry.get() == "":
        show_placeholder(entry)


# Return what the user typed in the Add box ("" if it's only showing the placeholder)
def get_entry_text(entry):
    if entry.placeholder_on:
        return ""
    return entry.get().strip()


# Create the add row: an outlined text box with a placeholder, and a "+ Add" button that calls on_add; return the entry
def create_input_row(window, on_add):
    input_frame = tk.Frame(window, bg=theme.BG)
    input_frame.pack(fill="x", pady=(0, 10))

    # The outline is a frame 1px bigger than the entry, so its color shows as a thin border (like auth.py)
    outline = tk.Frame(input_frame, bg=theme.BORDER)
    outline.pack(side="left", fill="x", expand=True, padx=(0, 10))
    habit_entry = tk.Entry(
        outline,
        font=(theme.FONT, 12),
        bg=theme.CARD,
        fg=theme.TEXT,
        insertbackground=theme.TEXT,
        relief="flat",
    )
    habit_entry.pack(fill="x", padx=1, pady=1, ipady=8, ipadx=8)
    show_placeholder(habit_entry)
    habit_entry.bind("<FocusIn>", lambda event: on_entry_focus_in(habit_entry, outline))
    habit_entry.bind("<FocusOut>", lambda event: on_entry_focus_out(habit_entry, outline))
    # Pressing Enter in the box adds the habit, the same as clicking "+ Add"
    habit_entry.bind("<Return>", lambda event: on_add())

    add_button = ui.rounded_button(input_frame, "+ Add", on_add, "filled", height=40, font_size=11)
    add_button.pack(side="left")

    return habit_entry


# Count today's habits: return (how many are done today, how many habits there are)
def get_today_progress(user_id):
    today = date.today().isoformat()
    habits = database.get_all_habits(user_id)

    done = 0
    for habit_id, name in habits:
        if database.is_done(habit_id, today):
            done = done + 1
    return done, len(habits)


# Create the "Today's progress" card (text, bar, message) and return a dictionary of its parts
def create_progress_card(window):
    card = tk.Frame(window, bg=theme.CARD, highlightthickness=1, highlightbackground=theme.BORDER, padx=16, pady=12)
    card.pack(fill="x", pady=(0, 10))

    # Row 1: title on the left, "3 / 5 done" on the right
    top_row = tk.Frame(card, bg=theme.CARD)
    top_row.pack(fill="x")
    title_label = tk.Label(top_row, text="Today's progress", font=(theme.FONT, 12, "bold"), fg=theme.TEXT, bg=theme.CARD)
    title_label.pack(side="left")
    count_label = tk.Label(top_row, font=(theme.FONT, 11), fg=theme.MUTED, bg=theme.CARD)
    count_label.pack(side="right")

    # Row 2: the bar (a Canvas that stretches across) with the percent next to it
    bar_row = tk.Frame(card, bg=theme.CARD)
    bar_row.pack(fill="x", pady=(10, 6))
    # width=5 keeps room for "100%", so the bar doesn't change length when the number does
    percent_label = tk.Label(bar_row, font=(theme.FONT, 11, "bold"), fg=theme.TEXT, bg=theme.CARD, width=5, anchor="e")
    percent_label.pack(side="right")
    bar = tk.Canvas(bar_row, height=BAR_HEIGHT, bg=theme.CARD, highlightthickness=0)
    bar.pack(side="left", fill="x", expand=True)

    # Row 3: the encouraging message
    message_label = tk.Label(card, font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD)
    message_label.pack(anchor="w")

    progress = {
        "bar": bar,
        "count_label": count_label,
        "percent_label": percent_label,
        "message_label": message_label,
        "shown": 0,        # how full the bar is drawn right now (0 to 1)
        "animation": 0,    # a number that changes every time a new fill animation starts
    }
    # Redraw the bar whenever it changes width (when the window opens or is resized)
    bar.bind("<Configure>", lambda event: draw_bar(progress))
    return progress


# Draw the bar: a rounded grey track across the whole canvas, and a rounded accent fill on top of it
def draw_bar(progress):
    bar = progress["bar"]
    bar.delete("all")
    width = bar.winfo_width()
    radius = BAR_HEIGHT / 2

    track = ui.rounded_rectangle_points(0, 0, width, BAR_HEIGHT, radius)
    bar.create_polygon(track, smooth=True, fill=theme.BORDER, outline="")

    # The fill is as wide as the done fraction of the track (e.g. 0.6 of 400px = 240px)
    fill_width = width * progress["shown"]
    if fill_width >= 1:
        # A very short fill can't have corners bigger than half its own width
        fill_radius = min(radius, fill_width / 2)
        fill = ui.rounded_rectangle_points(0, 0, fill_width, BAR_HEIGHT, fill_radius)
        bar.create_polygon(fill, smooth=True, fill=theme.ACCENT, outline="")


# Move the fill one small step from `start` towards `end`, then ask after() for the next step
def animate_fill(progress, start, end, step, animation):
    # Stop if the page was closed, or if a newer animation has started since this one
    if not progress["bar"].winfo_exists() or progress["animation"] != animation:
        return

    # "Ease out": quick at first, slow at the end, so the bar glides to its new size
    eased = 1 - (1 - step / FILL_STEPS) ** 3
    progress["shown"] = start + (end - start) * eased
    draw_bar(progress)

    if step < FILL_STEPS:
        progress["bar"].winfo_toplevel().after(FILL_DELAY, lambda: animate_fill(progress, start, end, step + 1, animation))


# Recount today's habits and update the card's text, message and (animated) bar
def update_progress_card(progress, user_id):
    done, total = get_today_progress(user_id)
    if total == 0:
        percent = 0
    else:
        percent = round(done * 100 / total)

    progress["count_label"].config(text=str(done) + " / " + str(total) + " done")
    progress["percent_label"].config(text=str(percent) + "%")

    if total == 0:
        message, color = "Add your first habit to get started", theme.MUTED
    elif done == 0:
        message, color = "Let's start: tick your first habit", theme.MUTED
    elif done < total:
        message, color = "Keep going, " + str(total - done) + " more to go!", theme.MUTED
    else:
        message, color = "🎉 All done for today!", theme.SUCCESS
    progress["message_label"].config(text=message, fg=color)

    # Start a new animation from wherever the bar is now to the new fraction
    progress["animation"] = progress["animation"] + 1
    animate_fill(progress, progress["shown"], percent / 100, 1, progress["animation"])


# Create one side-panel card with a bold title; return the card so content can be added
def create_side_card(parent, title):
    card = tk.Frame(parent, bg=theme.CARD, highlightthickness=1, highlightbackground=theme.BORDER, padx=16, pady=12)
    card.pack(fill="x", pady=(0, 10))
    tk.Label(card, text=title, font=(theme.FONT, 11, "bold"), fg=theme.TEXT, bg=theme.CARD).pack(anchor="w", pady=(0, 8))
    return card


# Draw the next-badge progress bar: a BORDER track across the canvas, an ACCENT fill for side["badge_fraction"] of it
def draw_badge_bar(side):
    bar = side["badge_bar"]
    bar.delete("all")
    width = bar.winfo_width()
    bar.create_rectangle(0, 0, width, 6, fill=theme.BORDER, outline="")
    if side["badge_fraction"] > 0:
        bar.create_rectangle(0, 0, width * side["badge_fraction"], 6, fill=theme.ACCENT, outline="")


# Build the right-hand panel: Last 30 days, Next badge and Quote of the day; return a dictionary of its parts
def create_side_panel(parent, user_id):
    # Card 1: a small heatmap of the last 30 days (heatmap.py draws it) and a total under it
    heat_card = create_side_card(parent, "Last 30 days")
    # empty_color=BORDER: in this theme HEATMAP[0] is the card's own color, so empty days would be invisible
    mini = heatmap.create_mini_heatmap(heat_card, user_id, days=30, columns=6, square=17, gap=4, empty_color=theme.BORDER)
    mini.pack(anchor="w")
    heat_total = tk.Label(heat_card, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    heat_total.pack(anchor="w", pady=(8, 0))

    # Card 2: the next locked badge and how close the best current streak is to it
    badge_card = create_side_card(parent, "Next badge")
    badge_title = tk.Label(badge_card, font=(theme.FONT, 11, "bold"), fg=theme.TEXT, bg=theme.CARD)
    badge_title.pack(anchor="w")
    badge_count = tk.Label(badge_card, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    badge_count.pack(anchor="w", pady=(2, 6))
    badge_bar = tk.Canvas(badge_card, height=6, bg=theme.CARD, highlightthickness=0)
    badge_bar.pack(fill="x")

    # Card 3: today's quote and its author
    quote_card = create_side_card(parent, "Quote of the day")
    quote = tk.Label(quote_card, font=(theme.FONT, 10, "italic"), fg=theme.TEXT, bg=theme.CARD, wraplength=220, justify="left")
    quote.pack(anchor="w")
    author = tk.Label(quote_card, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    author.pack(anchor="w", pady=(6, 0))

    side = {
        "mini": mini, "heat_total": heat_total,
        "badge_title": badge_title, "badge_count": badge_count, "badge_bar": badge_bar, "badge_fraction": 0,
        "quote": quote, "author": author,
    }
    # The bar's real width is only known once it's on screen, so draw it whenever its size changes
    badge_bar.bind("<Configure>", lambda event: draw_badge_bar(side))
    return side


# Return today's (quote, author): the day of the year picks one, so it changes daily but stays the same all day
def get_quote_of_the_day():
    # timetuple().tm_yday is the day of the year: 1 on 1 January ... 365 (or 366) on 31 December
    day_of_year = date.today().timetuple().tm_yday
    # % wraps the number around the list: day 16 with 15 quotes picks quote 1 again
    return QUOTES[day_of_year % len(QUOTES)]


# Recalculate everything in the side panel from the database and show it
def update_side_panel(side, user_id):
    # Last 30 days: redraw the small heatmap and count the total
    heatmap.draw_mini_heatmap(side["mini"], user_id, days=30, columns=6, square=17, gap=4, empty_color=theme.BORDER)
    total = 0
    for days_ago in range(30):
        total = total + database.get_count_for_date((date.today() - timedelta(days=days_ago)).isoformat(), user_id)
    side["heat_total"].config(text=str(total) + " habits done in 30 days")

    # Next badge: the first milestone this user hasn't unlocked yet
    unlocked = [milestone for milestone, habit_name, unlocked_date in database.get_badges(user_id)]
    locked = [milestone for milestone in database.MILESTONES if milestone not in unlocked]
    if len(locked) == 0:
        side["badge_title"].config(text="👑 All badges unlocked!")
        side["badge_count"].config(text="")
        side["badge_fraction"] = 1
    else:
        goal = locked[0]
        # The same "best current streak" the Badges page uses, never shown above the goal
        best = min(database.get_current_best_streak(user_id), goal)
        side["badge_title"].config(text=badges.BADGE_EMOJIS[goal] + " " + str(goal) + "-day streak")
        side["badge_count"].config(text=str(best) + " / " + str(goal) + " days")
        side["badge_fraction"] = best / goal
    draw_badge_bar(side)

    # Quote of the day
    text, who = get_quote_of_the_day()
    side["quote"].config(text="“" + text + "”")
    side["author"].config(text="— " + who)


# Give the list's scrollbar a slim look in the theme colors (ttk scrollbars can be styled; plain tk ones can't)
def style_list_scrollbar():
    style = ttk.Style()
    # "clam" is a ttk look whose colors can all be changed (the default Windows look ignores them)
    style.theme_use("clam")
    # Only a trough with a thumb in it: no arrow buttons at the ends
    style.layout("Habit.Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]}),
    ])
    style.configure(
        "Habit.Vertical.TScrollbar",
        background=theme.BORDER, troughcolor=theme.CARD, bordercolor=theme.CARD,
        lightcolor=theme.BORDER, darkcolor=theme.BORDER, arrowsize=8, gripcount=0,
    )
    # The thumb turns the accent color while dragged or under the mouse
    style.map("Habit.Vertical.TScrollbar", background=[("pressed", theme.ACCENT), ("active", theme.MUTED)])


# Show the scrollbar only when the list is taller than the card (first/last are how much of the list is visible, 0 to 1)
def update_list_scrollbar(scrollbar, canvas, first, last):
    scrollbar.set(first, last)
    if float(first) <= 0 and float(last) >= 1:
        scrollbar.pack_forget()
    elif not scrollbar.winfo_ismapped():
        # before=canvas: pack hands out space in order, and the canvas (expand=True) would otherwise have
        # taken all of it already, leaving the scrollbar 0 pixels wide
        scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2, before=canvas)


# Scroll the list with the mouse wheel, but only while the pointer is over the list card
def on_list_wheel(canvas, card, event):
    # The wheel is bound for the whole app, so do nothing once this page has been closed
    if not canvas.winfo_exists():
        return
    if not ui.is_inside(card.winfo_containing(event.x_root, event.y_root), card):
        return
    # Nothing to scroll if the whole list already fits
    top, bottom = canvas.yview()
    if top <= 0 and bottom >= 1:
        return
    # Windows reports 120 per wheel notch, a Mac small numbers; one "unit" is 1 pixel (yscrollincrement=1)
    if sys.platform == "darwin":
        notches = -event.delta / 10
    else:
        notches = -event.delta / 120
    canvas.yview_scroll(int(notches * LIST_WHEEL_PIXELS), "units")


# Create the bordered list card with a scrollable area inside; return the frame that holds the rows
def create_habit_list_area(window):
    # The card itself: a solid CARD with a 1px BORDER outline, filling the rest of the column
    card = tk.Frame(window, bg=theme.CARD, highlightbackground=theme.BORDER, highlightthickness=1)
    card.pack(fill="both", expand=True)

    style_list_scrollbar()
    scrollbar = ttk.Scrollbar(card, orient="vertical", style="Habit.Vertical.TScrollbar")
    # A Canvas can scroll; it shows a "window" onto a frame that can be taller than the card
    canvas = tk.Canvas(card, bg=theme.CARD, highlightthickness=0, yscrollincrement=1)
    canvas.pack(side="left", fill="both", expand=True)
    habit_list_frame = tk.Frame(canvas, bg=theme.CARD)
    window_id = canvas.create_window(0, 0, window=habit_list_frame, anchor="nw")

    # When the rows change, tell the canvas how tall they are, so it knows how far it can scroll
    habit_list_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    # When the card changes width, make the rows exactly as wide as the visible area
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
    # The scrollbar moves the canvas, and the canvas tells the scrollbar where it is (and whether it's needed)
    scrollbar.config(command=canvas.yview)
    canvas.configure(yscrollcommand=lambda first, last: update_list_scrollbar(scrollbar, canvas, first, last))
    canvas.bind_all("<MouseWheel>", lambda event: on_list_wheel(canvas, card, event))

    # Remember the card and canvas, for the empty state and for scrolling to a newly added habit
    habit_list_frame.card = card
    habit_list_frame.canvas = canvas
    return habit_list_frame


# Draw the round checkbox: an empty ring when not done, an accent circle with a "✓" when done
def draw_round_check(canvas, checked):
    canvas.delete("all")
    # 2px in from the edges so the ring's outline isn't cut off
    if checked:
        canvas.create_oval(2, 2, CHECK_SIZE - 2, CHECK_SIZE - 2, fill=theme.ACCENT, outline=theme.ACCENT)
        canvas.create_text(CHECK_SIZE / 2, CHECK_SIZE / 2, text="✓", fill=theme.BG, font=(theme.FONT, 10, "bold"))
    else:
        # MUTED instead of BORDER: BORDER is almost the card's color, and is the hovered row's color,
        # so a BORDER ring would vanish exactly when the mouse is over the row
        canvas.create_oval(2, 2, CHECK_SIZE - 2, CHECK_SIZE - 2, outline=theme.MUTED, width=1.5)


# Draw a rounded "🔥 N" streak pill on its own small canvas and return it (dim grey when the streak is 0)
def create_streak_pill(parent, streak):
    font = tkfont.Font(family=theme.FONT, size=9, weight="bold")
    text = "🔥 " + str(streak)
    # The pill is the text's size plus some room around it
    width = font.measure(text) + 18
    height = font.metrics("linespace") + 6

    if streak > 0:
        fill, text_color = theme.ACCENT_SOFT, theme.ACCENT
    else:
        fill, text_color = theme.BORDER, theme.MUTED
    pill = tk.Canvas(parent, width=width, height=height, bg=theme.CARD, highlightthickness=0)
    # radius = half the height makes both ends fully round, like a pill
    pill.create_polygon(ui.rounded_rectangle_points(0, 0, width, height, height / 2), smooth=True, fill=fill, outline="")
    pill.create_text(width / 2, height / 2, text=text, fill=text_color, font=font)
    return pill


# Color a habit row: a slightly lighter background (and a visible 🗑) while hovered, normal otherwise
def paint_row(row, hovered):
    background = theme.BORDER if hovered else theme.CARD
    for widget in row["parts"]:
        widget.config(bg=background)
    # The delete icon is "hidden" by drawing it in the same color as the row behind it
    row["delete"].config(bg=background, fg=theme.MUTED if hovered else background)


# The mouse left the row (or moved onto something inside it): un-hover only if it really left the row
def leave_row(row):
    x, y = row["frame"].winfo_pointerxy()
    if not ui.is_inside(row["frame"].winfo_containing(x, y), row["frame"]):
        paint_row(row, False)


# Flip a habit's done state, exactly like clicking the old Checkbutton did, then run the usual tick logic
def on_round_check_click(habit_id, done_var, habit_list_frame, user_id, on_change):
    done_var.set(not done_var.get())
    on_check_click(habit_id, done_var, habit_list_frame, user_id, on_change)


# Ask "are you sure?" before deleting a habit and its history
def confirm_delete(habit_id, name, habit_list_frame, user_id, on_change):
    if messagebox.askyesno("Delete habit?", 'Delete "' + name + '" and all of its history?'):
        on_delete_click(habit_id, habit_list_frame, user_id, on_change)


# Build one habit row (round checkbox, name, streak pill, hidden 🗑) inside the list card
def create_habit_row(habit_list_frame, habit_id, name, user_id, on_change):
    today = date.today().isoformat()
    done = database.is_done(habit_id, today)

    frame = tk.Frame(habit_list_frame, bg=theme.CARD, padx=14, pady=7)
    frame.pack(fill="x")

    # The round checkbox: a small Canvas that redraws itself as a ring or a ticked circle
    done_var = tk.BooleanVar(value=done)
    check = tk.Canvas(frame, width=CHECK_SIZE, height=CHECK_SIZE, bg=theme.CARD, highlightthickness=0, cursor="hand2")
    draw_round_check(check, done)
    check.pack(side="left", padx=(0, 12))
    check.bind("<Button-1>", lambda event: on_round_check_click(habit_id, done_var, habit_list_frame, user_id, on_change))

    # Done today: grey text with a line through it ("overstrike" draws that line)
    if done:
        name_label = tk.Label(frame, text=name, font=(theme.FONT, 12, "overstrike"), fg=theme.MUTED, bg=theme.CARD)
    else:
        name_label = tk.Label(frame, text=name, font=(theme.FONT, 12), fg=theme.TEXT, bg=theme.CARD)
    name_label.pack(side="left")

    pill = create_streak_pill(frame, database.get_streak(habit_id))
    pill.pack(side="left", padx=(12, 0))

    # Starts invisible (same color as the row); paint_row shows it while the mouse is over the row
    delete = tk.Label(frame, text="🗑", font=(theme.FONT, 12), fg=theme.CARD, bg=theme.CARD, cursor="hand2")
    delete.pack(side="right")
    delete.bind("<Button-1>", lambda event: confirm_delete(habit_id, name, habit_list_frame, user_id, on_change))
    # While the mouse is on the icon itself, it turns red
    delete.bind("<Enter>", lambda event: delete.config(fg=theme.ERROR))
    delete.bind("<Leave>", lambda event: delete.config(fg=theme.MUTED))

    row = {"frame": frame, "delete": delete, "parts": [frame, check, name_label, pill]}
    frame.bind("<Enter>", lambda event: paint_row(row, True))
    frame.bind("<Leave>", lambda event: leave_row(row))


# Show the "No habits yet" message in the middle of the empty list card
def create_empty_state(habit_list_frame):
    # Placed on the card itself (not the scrolling rows frame, which is only as tall as its rows)
    empty = tk.Frame(habit_list_frame.card, bg=theme.CARD)
    # relx/rely 0.5 with anchor="center" puts it in the exact middle of the card
    empty.place(relx=0.5, rely=0.5, anchor="center")
    habit_list_frame.empty = empty
    tk.Label(empty, text="🌱", font=(theme.FONT, 30), fg=theme.ACCENT, bg=theme.CARD).pack()
    tk.Label(empty, text="No habits yet", font=(theme.FONT, 13, "bold"), fg=theme.TEXT, bg=theme.CARD).pack(pady=(6, 2))
    tk.Label(empty, text="Add your first habit above to start a streak", font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD).pack()


# Remove every row from the habit list card, then draw one row per habit (or the empty state)
def refresh_habit_list(habit_list_frame, user_id, on_change=None):
    for child in habit_list_frame.winfo_children():
        child.destroy()
    # The empty-state message lives on the card, not in the rows frame, so remove it separately
    if hasattr(habit_list_frame, "empty") and habit_list_frame.empty.winfo_exists():
        habit_list_frame.empty.destroy()

    habits = database.get_all_habits(user_id)
    if len(habits) == 0:
        create_empty_state(habit_list_frame)

    for i in range(len(habits)):
        habit_id, name = habits[i]
        # A 1px line BETWEEN rows: before every row except the first, so there's none after the last
        if i > 0:
            tk.Frame(habit_list_frame, bg=theme.BORDER, height=1).pack(fill="x")
        create_habit_row(habit_list_frame, habit_id, name, user_id, on_change)

    # Every add, delete, tick and untick ends up here, so this keeps the progress card, stat cards and side panel up to date too
    if hasattr(habit_list_frame, "progress"):
        update_progress_card(habit_list_frame.progress, user_id)
    if hasattr(habit_list_frame, "stats"):
        update_stats_row(habit_list_frame.stats, user_id)
    if hasattr(habit_list_frame, "side"):
        update_side_panel(habit_list_frame.side, user_id)


# Add the habit typed in the Entry box, warn if it already exists, then redraw the list
def on_add_click(habit_entry, habit_list_frame, user_id, on_change=None):
    # get_entry_text ignores the grey placeholder, so clicking "+ Add" on an empty box does nothing
    name = get_entry_text(habit_entry)
    if name == "":
        return

    added = database.add_habit(user_id, name)
    if not added:
        messagebox.showwarning("Consistify", "Habit already exists")

    habit_entry.delete(0, tk.END)
    refresh_habit_list(habit_list_frame, user_id, on_change)
    if added:
        # New habits go at the bottom of the list, so scroll down to show it (once the new row has its size)
        habit_list_frame.update_idletasks()
        habit_list_frame.canvas.yview_moveto(1)
    if on_change is not None:
        on_change()


# Mark or unmark a habit as done today, depending on its checkbox, then redraw the list
def on_check_click(habit_id, done_var, habit_list_frame, user_id, on_change=None):
    today = date.today().isoformat()

    # Only a tick (not an untick) can unlock a badge or finish the day
    new_badges = []
    if done_var.get():
        database.mark_done(habit_id, today)
        # Save any new badges BEFORE redrawing, so the Badges stat card already counts them
        new_badges = database.check_new_badges(user_id)
    else:
        database.unmark_done(habit_id, today)

    refresh_habit_list(habit_list_frame, user_id, on_change)
    if on_change is not None:
        on_change()

    if not done_var.get():
        return

    # habit_list_frame.content is the frame the whole habit section was built in (the dashboard's content area),
    # so the celebration covers the whole page, not just the left column the list sits in
    content = habit_list_frame.content
    if len(new_badges) > 0:
        # A new badge beats "all done": only one kind of celebration at a time
        show_badge_celebrations(content, new_badges)
        return

    # A tick that leaves every habit done must have been the last one missing: celebrate
    done, total = get_today_progress(user_id)
    if total > 0 and done == total:
        ui.show_confetti(content, "🎉 All done for today!")


# Celebrate the first badge in the list, then the next one once that celebration has finished, and so on
def show_badge_celebrations(content, remaining):
    if len(remaining) == 0 or not content.winfo_exists():
        return

    milestone, habit_name = remaining[0]
    ui.show_confetti(content, "🏆 " + str(milestone) + "-day streak unlocked!", subtitle=habit_name)
    # Wait for this celebration to close by itself (plus a short pause) before showing the next badge
    content.winfo_toplevel().after(ui.CONFETTI_TIME + 300, lambda: show_badge_celebrations(content, remaining[1:]))


# Ask where to save the report, then write the CSV there (do nothing if cancelled)
def on_export_click(user_id):
    filename = filedialog.asksaveasfilename(
        title="Save report",
        initialfile="consistify_report.csv",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
    )
    if not filename:
        return

    database.export_to_csv(user_id, filename)
    messagebox.showinfo("Consistify", "Report saved!")


# Delete one habit from the database, then redraw the list
def on_delete_click(habit_id, habit_list_frame, user_id, on_change=None):
    database.delete_habit(habit_id)
    refresh_habit_list(habit_list_frame, user_id, on_change)
    if on_change is not None:
        on_change()


# Build the whole Today page for one user inside any window or frame: header and stat cards across the top,
# then two columns (progress, add row and habit list on the left; the side panel on the right)
def create_habit_section(parent, user_id, on_change=None, username="there"):
    create_page_header(parent, user_id, username)
    stats = create_stats_row(parent)

    # Two columns sharing the width 2 : 1 (weight=2 and weight=1; uniform makes the weights exact),
    # with 8px on each side of the middle, which makes the 16px gap
    body = tk.Frame(parent, bg=theme.BG)
    body.pack(fill="both", expand=True, padx=40, pady=(0, 16))
    body.columnconfigure(0, weight=2, uniform="body")
    body.columnconfigure(1, weight=1, uniform="body")
    body.rowconfigure(0, weight=1)
    left = tk.Frame(body, bg=theme.BG)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    right = tk.Frame(body, bg=theme.BG)
    right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    progress = create_progress_card(left)
    # The lambda only runs when "+ Add" is clicked, by which time habit_entry and habit_list_frame exist
    habit_entry = create_input_row(left, lambda: on_add_click(habit_entry, habit_list_frame, user_id, on_change))
    habit_list_frame = create_habit_list_area(left)
    side = create_side_panel(right, user_id)

    # Attach the cards to the list frame: every function that redraws the list already receives
    # habit_list_frame, so it can reach them through it without an extra parameter
    habit_list_frame.progress = progress
    habit_list_frame.stats = stats
    habit_list_frame.side = side
    # The whole page's frame, so celebrations can cover all of it
    habit_list_frame.content = parent

    refresh_habit_list(habit_list_frame, user_id, on_change)


# Run this block only when gui.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    # Log in as a test user (create_user just returns False if "demo" already exists)
    database.create_user("demo", "demo123")
    user_id = database.check_login("demo", "demo123")

    window = create_window()
    create_habit_section(window, user_id, username="demo")
    window.mainloop()
