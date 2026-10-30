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


# Build the whole habit section (header, input row, habit list) for one user inside any window or frame
def create_habit_section(parent, user_id, on_change=None):
    create_header(parent)
    habit_entry, add_button = create_input_row(parent, user_id)
    habit_list_frame = create_habit_list_area(parent)

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
