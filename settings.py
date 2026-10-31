# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import messagebox, for the "are you sure?" popup before deleting the account
from tkinter import messagebox

# Import our own files: the database, the shared colors, the reusable widgets,
# and auth.py's create_field so the password boxes look and behave exactly like the login page
import auth
import database
import theme
import ui


# Create a card with a bold title; return the card so content can be added (border_color for the danger zone)
def create_card(parent, title, row, column, border_color=theme.BORDER, title_color=theme.TEXT):
    card = tk.Frame(parent, bg=theme.CARD, highlightthickness=1, highlightbackground=border_color, padx=20, pady=14)
    card.grid(row=row, column=column, sticky="nsew", padx=8, pady=6)
    title_label = tk.Label(card, text=title, font=(theme.FONT, 13, "bold"), fg=title_color, bg=theme.CARD)
    title_label.pack(anchor="w", pady=(0, 10))
    return card


# Add one "Label    value" line to the Account card
def add_info_row(card, label_text, value_text):
    row = tk.Frame(card, bg=theme.CARD)
    row.pack(fill="x", pady=3)
    label = tk.Label(row, text=label_text, font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD)
    label.pack(side="left")
    value = tk.Label(row, text=value_text, font=(theme.FONT, 10, "bold"), fg=theme.TEXT, bg=theme.CARD)
    value.pack(side="right")


# Check the change-password form, then change the password; show the result in the form's message label
def on_update_password(form, user_id):
    current = form["current"].get()
    new = form["new"].get()
    confirm = form["confirm"].get()

    if current == "" or new == "" or confirm == "":
        form["message"].config(text="Please fill in all fields", fg=theme.ERROR)
        return
    if len(new) < 6:
        form["message"].config(text="New password must be at least 6 characters", fg=theme.ERROR)
        return
    if new != confirm:
        form["message"].config(text="New passwords don't match", fg=theme.ERROR)
        return
    if new == current:
        form["message"].config(text="New password must be different", fg=theme.ERROR)
        return
    # change_password checks the current password itself and returns False if it's wrong
    if not database.change_password(user_id, current, new):
        form["message"].config(text="Current password is incorrect", fg=theme.ERROR)
        return

    for name in ("current", "new", "confirm"):
        form[name].delete(0, tk.END)
    form["message"].config(text="Password updated", fg=theme.SUCCESS)


# Check the password, ask "are you sure?", then delete the account and everything in it
def on_delete_account(danger, user_id, on_account_deleted):
    password = danger["password"].get()
    if password == "":
        danger["message"].config(text="Please enter your password", fg=theme.ERROR)
        return
    # Check the password first, so the user isn't asked "are you sure?" for a password that's wrong anyway
    if not database.verify_password(user_id, password):
        danger["message"].config(text="Password is incorrect", fg=theme.ERROR)
        return

    sure = messagebox.askyesno(
        "Delete account",
        "Delete your account and all your habits, history and badges?\n\nThis can't be undone.",
        icon="warning",
    )
    if not sure:
        return

    if database.delete_user(user_id, password):
        on_account_deleted()


# Build the Account card: username, number of habits, badges unlocked
def build_account_card(column_frame, user_id, username):
    card = create_card(column_frame, "Account", 0, 0)
    habit_count = len(database.get_all_habits(user_id))
    badge_count = len(database.get_badges(user_id))
    add_info_row(card, "Username", username)
    add_info_row(card, "Habits", str(habit_count))
    add_info_row(card, "Badges", str(badge_count) + " of " + str(len(database.MILESTONES)) + " badges unlocked")


# Build the Change password card: three password boxes, a message line and the update button
def build_password_card(parent, user_id):
    card = create_card(parent, "Change password", 0, 1)
    # bg=CARD behind the labels, entry_bg=BG inside the boxes, so the boxes stand out on the card
    current_field, current = auth.create_field(card, "CURRENT PASSWORD", is_password=True, bg=theme.CARD, entry_bg=theme.BG)
    new_field, new = auth.create_field(card, "NEW PASSWORD", is_password=True, bg=theme.CARD, entry_bg=theme.BG)
    confirm_field, confirm = auth.create_field(card, "CONFIRM NEW PASSWORD", is_password=True, bg=theme.CARD, entry_bg=theme.BG)

    message = tk.Label(card, text="", font=(theme.FONT, 10), bg=theme.CARD, wraplength=320, justify="left")
    message.pack(anchor="w", pady=(0, 8))

    form = {"current": current, "new": new, "confirm": confirm, "message": message}
    button = ui.rounded_button(card, "Update password", lambda: on_update_password(form, user_id), "filled", height=42)
    button.pack(fill="x")
    # Pressing Enter in any of the boxes also updates the password
    for entry in (current, new, confirm):
        entry.bind("<Return>", lambda event: on_update_password(form, user_id))


# Build the Danger zone card: a warning, a password box and the red "Delete account" button
def build_danger_card(column_frame, user_id, on_account_deleted):
    card = create_card(column_frame, "Danger zone", 1, 0, border_color=theme.ERROR, title_color=theme.ERROR)
    warning = tk.Label(
        card, text="Delete your account and all your data. This can't be undone.",
        font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD, wraplength=300, justify="left",
    )
    warning.pack(anchor="w", pady=(0, 12))

    password_field, password = auth.create_field(card, "PASSWORD", is_password=True, bg=theme.CARD, entry_bg=theme.BG)
    message = tk.Label(card, text="", font=(theme.FONT, 10), bg=theme.CARD)
    message.pack(anchor="w", pady=(0, 8))

    danger = {"password": password, "message": message}
    button = ui.rounded_button(card, "Delete account", lambda: on_delete_account(danger, user_id, on_account_deleted), "danger", height=40)
    button.pack(fill="x")


# Build the whole Settings page inside the parent
def build_settings_page(parent, user_id, username, on_account_deleted):
    page = tk.Frame(parent, bg=theme.BG, padx=32, pady=16)
    page.pack(fill="both", expand=True)

    header = tk.Label(page, text="Settings", font=(theme.FONT, 22, "bold"), fg=theme.TEXT, bg=theme.BG)
    header.pack(anchor="w", padx=8, pady=(0, 4))

    # Two equal columns: Account and Danger zone on the left, Change password on the right
    columns = tk.Frame(page, bg=theme.BG)
    columns.pack(fill="both", expand=True)
    columns.columnconfigure(0, weight=1, uniform="settings")
    columns.columnconfigure(1, weight=1, uniform="settings")

    left = tk.Frame(columns, bg=theme.BG)
    left.grid(row=0, column=0, sticky="nsew")
    left.columnconfigure(0, weight=1)
    build_account_card(left, user_id, username)
    build_danger_card(left, user_id, on_account_deleted)

    build_password_card(columns, user_id)
    return page


# Print that the account was deleted and close the window (used only by the test window below)
def test_account_deleted(window):
    print("Account deleted")
    window.destroy()


# Run this block only when settings.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    # Log in as a test user (create_user just returns False if "demo" already exists)
    database.create_user("demo", "demo123")
    user_id = database.check_login("demo", "demo123")

    window = tk.Tk()
    window.title("Consistify - Settings")
    window.geometry("900x700")
    window.configure(bg=theme.BG)

    build_settings_page(window, user_id, "demo", lambda: test_account_deleted(window))
    window.mainloop()
