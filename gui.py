# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import messagebox, tkinter's ready-made pop-up message windows
from tkinter import messagebox
# Import filedialog, tkinter's ready-made "Open" and "Save As" windows
from tkinter import filedialog
# Import date so we can get today's date
from datetime import date

# Import our own database.py so we can save and load habits
import database
# Import the app's shared colors and font
import theme
# Import our reusable widgets (for the rounded rectangle shape of the progress bar)
import ui

BAR_HEIGHT = 12        # height of the progress bar (pixels)
FILL_STEPS = 15        # the fill animation takes 15 small steps...
FILL_DELAY = 20        # ...20 milliseconds apart, so about 300 ms in total


# Create the main window, give it a title, a size, and a dark background
def create_window():
    window = tk.Tk()
    window.title("Consistify")
    window.geometry("900x600")
    window.configure(bg=theme.BG)
    return window


# Create the big title and the small subtitle at the top of the window
def create_header(window):
    title_label = tk.Label(
        window,
        text="Consistify",
        font=(theme.FONT, 28, "bold"),
        fg=theme.ACCENT,
        bg=theme.BG,
    )
    title_label.pack(pady=(30, 0))

    subtitle_label = tk.Label(
        window,
        text="Build habits that stick",
        font=(theme.FONT, 12),
        fg=theme.TEXT,
        bg=theme.BG,
    )
    subtitle_label.pack(pady=(5, 20))


# Create one row holding the text box, the "Add Habit" button and the "Export CSV" button side by side
def create_input_row(window, user_id):
    input_frame = tk.Frame(window, bg=theme.BG)
    input_frame.pack(pady=10)

    habit_entry = tk.Entry(
        input_frame,
        width=40,
        font=(theme.FONT, 12),
        bg=theme.CARD,
        fg=theme.TEXT,
        insertbackground=theme.TEXT,
        relief="flat",
    )
    habit_entry.pack(side="left", padx=(0, 10), ipady=6)

    add_button = tk.Button(
        input_frame,
        text="Add Habit",
        font=(theme.FONT, 11, "bold"),
        bg=theme.ACCENT,
        fg=theme.BG,
        activebackground=theme.ACCENT,
        relief="flat",
        padx=15,
        pady=5,
    )
    add_button.pack(side="left")

    export_button = tk.Button(
        input_frame,
        text="Export CSV",
        font=(theme.FONT, 11, "bold"),
        bg=theme.CARD,
        fg=theme.ACCENT,
        activebackground=theme.BORDER,
        activeforeground=theme.ACCENT,
        relief="flat",
        padx=15,
        pady=5,
        command=lambda: on_export_click(user_id),
    )
    export_button.pack(side="left", padx=(10, 0))

    return habit_entry, add_button


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
    card = tk.Frame(window, bg=theme.CARD, highlightthickness=1, highlightbackground=theme.BORDER, padx=16, pady=16)
    card.pack(fill="x", padx=40, pady=(0, 10))

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


# Create an empty bordered area that will hold the habit list later
def create_habit_list_area(window):
    habit_list_frame = tk.Frame(
        window,
        bg=theme.BG,
        highlightbackground=theme.BORDER,
        highlightthickness=1,
    )
    habit_list_frame.pack(fill="both", expand=True, padx=40, pady=20)
    return habit_list_frame


# Remove every row from the habit list area, then draw one row per habit from the database
def refresh_habit_list(habit_list_frame, user_id, on_change=None):
    for child in habit_list_frame.winfo_children():
        child.destroy()

    today = date.today().isoformat()

    for habit_id, name in database.get_all_habits(user_id):
        row_frame = tk.Frame(habit_list_frame, bg=theme.BG)
        row_frame.pack(fill="x", padx=15, pady=5)

        done_var = tk.BooleanVar(value=database.is_done(habit_id, today))
        done_checkbox = tk.Checkbutton(
            row_frame,
            variable=done_var,
            bg=theme.BG,
            fg=theme.TEXT,
            selectcolor=theme.CARD,
            activebackground=theme.BG,
            activeforeground=theme.TEXT,
            highlightthickness=0,
            command=lambda habit_id=habit_id, done_var=done_var: on_check_click(
                habit_id, done_var, habit_list_frame, user_id, on_change
            ),
        )
        done_checkbox.pack(side="left")

        name_label = tk.Label(
            row_frame,
            text=name,
            font=(theme.FONT, 12),
            fg=theme.TEXT,
            bg=theme.BG,
        )
        name_label.pack(side="left")

        streak_label = tk.Label(
            row_frame,
            text="🔥 " + str(database.get_streak(habit_id)) + " day streak",
            font=(theme.FONT, 10),
            fg=theme.ACCENT,
            bg=theme.BG,
        )
        streak_label.pack(side="left", padx=(15, 0))

        delete_button = tk.Button(
            row_frame,
            text="Delete",
            font=(theme.FONT, 9),
            bg=theme.CARD,
            fg=theme.TEXT,
            activebackground=theme.BORDER,
            activeforeground=theme.TEXT,
            relief="flat",
            padx=8,
            command=lambda habit_id=habit_id: on_delete_click(habit_id, habit_list_frame, user_id, on_change),
        )
        delete_button.pack(side="right")

    # Every add, delete, tick and untick ends up here, so this keeps the progress card up to date too
    if hasattr(habit_list_frame, "progress"):
        update_progress_card(habit_list_frame.progress, user_id)


# Add the habit typed in the Entry box, warn if it already exists, then redraw the list
def on_add_click(habit_entry, habit_list_frame, user_id, on_change=None):
    name = habit_entry.get().strip()
    if name == "":
        return

    if not database.add_habit(user_id, name):
        messagebox.showwarning("Consistify", "Habit already exists")

    habit_entry.delete(0, tk.END)
    refresh_habit_list(habit_list_frame, user_id, on_change)
    if on_change is not None:
        on_change()


# Mark or unmark a habit as done today, depending on its checkbox, then redraw the list
def on_check_click(habit_id, done_var, habit_list_frame, user_id, on_change=None):
    today = date.today().isoformat()

    if done_var.get():
        database.mark_done(habit_id, today)
    else:
        database.unmark_done(habit_id, today)

    refresh_habit_list(habit_list_frame, user_id, on_change)
    if on_change is not None:
        on_change()

    # A tick (not an untick) that leaves every habit done must have been the last one missing: celebrate.
    # habit_list_frame.master is the frame the habit section was built in (the dashboard's content area)
    done, total = get_today_progress(user_id)
    if done_var.get() and total > 0 and done == total:
        ui.show_confetti(habit_list_frame.master, "🎉 All done for today!")


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


# Build the whole habit section (header, progress card, input row, habit list) for one user inside any window or frame
def create_habit_section(parent, user_id, on_change=None):
    create_header(parent)
    progress = create_progress_card(parent)
    habit_entry, add_button = create_input_row(parent, user_id)
    habit_list_frame = create_habit_list_area(parent)
    # Attach the progress card to the list frame: every function that redraws the list already
    # receives habit_list_frame, so it can reach the card through it without an extra parameter
    habit_list_frame.progress = progress

    add_button.config(command=lambda: on_add_click(habit_entry, habit_list_frame, user_id, on_change))
    habit_entry.bind("<Return>", lambda event: on_add_click(habit_entry, habit_list_frame, user_id, on_change))

    refresh_habit_list(habit_list_frame, user_id, on_change)


# Run this block only when gui.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    # Log in as a test user (create_user just returns False if "demo" already exists)
    database.create_user("demo", "demo123")
    user_id = database.check_login("demo", "demo123")

    window = create_window()
    create_habit_section(window, user_id)
    window.mainloop()
