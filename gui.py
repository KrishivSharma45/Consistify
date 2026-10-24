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

# Theme colors, stored once at the top so every widget uses the same values
BG_COLOR = "#0d1117"       # dark background
TEXT_COLOR = "#e6edf3"     # light text
ACCENT_COLOR = "#39d353"   # green accent
ENTRY_BG = "#161b22"       # slightly lighter dark, so the Entry box is visible
BORDER_COLOR = "#30363d"   # soft grey border for the habit list area


# Create the main window, give it a title, a size, and a dark background
def create_window():
    window = tk.Tk()
    window.title("Consistify")
    window.geometry("900x600")
    window.configure(bg=BG_COLOR)
    return window


# Create the big title and the small subtitle at the top of the window
def create_header(window):
    title_label = tk.Label(
        window,
        text="Consistify",
        font=("Segoe UI", 28, "bold"),
        fg=ACCENT_COLOR,
        bg=BG_COLOR,
    )
    title_label.pack(pady=(30, 0))

    subtitle_label = tk.Label(
        window,
        text="Build habits that stick",
        font=("Segoe UI", 12),
        fg=TEXT_COLOR,
        bg=BG_COLOR,
    )
    subtitle_label.pack(pady=(5, 20))


# Create one row holding the text box, the "Add Habit" button and the "Export CSV" button side by side
def create_input_row(window):
    input_frame = tk.Frame(window, bg=BG_COLOR)
    input_frame.pack(pady=10)

    habit_entry = tk.Entry(
        input_frame,
        width=40,
        font=("Segoe UI", 12),
        bg=ENTRY_BG,
        fg=TEXT_COLOR,
        insertbackground=TEXT_COLOR,
        relief="flat",
    )
    habit_entry.pack(side="left", padx=(0, 10), ipady=6)

    add_button = tk.Button(
        input_frame,
        text="Add Habit",
        font=("Segoe UI", 11, "bold"),
        bg=ACCENT_COLOR,
        fg=BG_COLOR,
        activebackground=ACCENT_COLOR,
        relief="flat",
        padx=15,
        pady=5,
    )
    add_button.pack(side="left")

    export_button = tk.Button(
        input_frame,
        text="Export CSV",
        font=("Segoe UI", 11, "bold"),
        bg=ENTRY_BG,
        fg=ACCENT_COLOR,
        activebackground=BORDER_COLOR,
        activeforeground=ACCENT_COLOR,
        relief="flat",
        padx=15,
        pady=5,
        command=on_export_click,
    )
    export_button.pack(side="left", padx=(10, 0))

    return habit_entry, add_button


# Create an empty bordered area that will hold the habit list later
def create_habit_list_area(window):
    habit_list_frame = tk.Frame(
        window,
        bg=BG_COLOR,
        highlightbackground=BORDER_COLOR,
        highlightthickness=1,
    )
    habit_list_frame.pack(fill="both", expand=True, padx=40, pady=20)
    return habit_list_frame


# Remove every row from the habit list area, then draw one row per habit from the database
def refresh_habit_list(habit_list_frame):
    for child in habit_list_frame.winfo_children():
        child.destroy()

    today = date.today().isoformat()

    for habit_id, name in database.get_all_habits():
        row_frame = tk.Frame(habit_list_frame, bg=BG_COLOR)
        row_frame.pack(fill="x", padx=15, pady=5)

        done_var = tk.BooleanVar(value=database.is_done(habit_id, today))
        done_checkbox = tk.Checkbutton(
            row_frame,
            variable=done_var,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=TEXT_COLOR,
            highlightthickness=0,
            command=lambda habit_id=habit_id, done_var=done_var: on_check_click(
                habit_id, done_var, habit_list_frame
            ),
        )
        done_checkbox.pack(side="left")

        name_label = tk.Label(
            row_frame,
            text=name,
            font=("Segoe UI", 12),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
        )
        name_label.pack(side="left")

        streak_label = tk.Label(
            row_frame,
            text="🔥 " + str(database.get_streak(habit_id)) + " day streak",
            font=("Segoe UI", 10),
            fg=ACCENT_COLOR,
            bg=BG_COLOR,
        )
        streak_label.pack(side="left", padx=(15, 0))

        delete_button = tk.Button(
            row_frame,
            text="Delete",
            font=("Segoe UI", 9),
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            activebackground=BORDER_COLOR,
            activeforeground=TEXT_COLOR,
            relief="flat",
            padx=8,
            command=lambda habit_id=habit_id: on_delete_click(habit_id, habit_list_frame),
        )
        delete_button.pack(side="right")


# Add the habit typed in the Entry box, warn if it already exists, then redraw the list
def on_add_click(habit_entry, habit_list_frame):
    name = habit_entry.get().strip()
    if name == "":
        return

    if not database.add_habit(name):
        messagebox.showwarning("Consistify", "Habit already exists")

    habit_entry.delete(0, tk.END)
    refresh_habit_list(habit_list_frame)


# Mark or unmark a habit as done today, depending on its checkbox, then redraw the list
def on_check_click(habit_id, done_var, habit_list_frame):
    today = date.today().isoformat()

    if done_var.get():
        database.mark_done(habit_id, today)
    else:
        database.unmark_done(habit_id, today)

    refresh_habit_list(habit_list_frame)


# Ask where to save the report, then write the CSV there (do nothing if cancelled)
def on_export_click():
    filename = filedialog.asksaveasfilename(
        title="Save report",
        initialfile="consistify_report.csv",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
    )
    if not filename:
        return

    database.export_to_csv(filename)
    messagebox.showinfo("Consistify", "Report saved!")


# Delete one habit from the database, then redraw the list
def on_delete_click(habit_id, habit_list_frame):
    database.delete_habit(habit_id)
    refresh_habit_list(habit_list_frame)


# Run this block only when gui.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    window = create_window()
    create_header(window)
    habit_entry, add_button = create_input_row(window)
    habit_list_frame = create_habit_list_area(window)

    add_button.config(command=lambda: on_add_click(habit_entry, habit_list_frame))
    habit_entry.bind("<Return>", lambda event: on_add_click(habit_entry, habit_list_frame))

    refresh_habit_list(habit_list_frame)
    window.mainloop()
