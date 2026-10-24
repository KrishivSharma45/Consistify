# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import messagebox, tkinter's ready-made pop-up message windows
from tkinter import messagebox

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


# Create one row holding the text box and the "Add Habit" button side by side
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

    for habit_id, name in database.get_all_habits():
        row_frame = tk.Frame(habit_list_frame, bg=BG_COLOR)
        row_frame.pack(fill="x", padx=15, pady=5)

        name_label = tk.Label(
            row_frame,
            text=name,
            font=("Segoe UI", 12),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
        )
        name_label.pack(side="left")

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
