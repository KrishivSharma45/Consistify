# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk

# Import our own database.py so we can create users and check logins
import database

# Theme colors, the same values gui.py uses, plus a red for error messages
BG_COLOR = "#0d1117"       # dark background
TEXT_COLOR = "#e6edf3"     # light text
ACCENT_COLOR = "#39d353"   # green accent
ENTRY_BG = "#161b22"       # slightly lighter dark, used for the card
BORDER_COLOR = "#30363d"   # soft grey border around the card
MUTED_COLOR = "#8b949e"    # grey for small labels
ERROR_COLOR = "#f85149"    # red for error messages


# Create a small grey label above an entry box, and the entry box itself
def create_field(card, label_text, hide_text=False):
    field_frame = tk.Frame(card, bg=ENTRY_BG)
    field_frame.pack(fill="x", pady=(0, 12))

    label = tk.Label(field_frame, text=label_text, font=("Segoe UI", 10), fg=MUTED_COLOR, bg=ENTRY_BG)
    label.pack(anchor="w")

    entry = tk.Entry(
        field_frame,
        width=32,
        font=("Segoe UI", 12),
        bg=BG_COLOR,
        fg=TEXT_COLOR,
        insertbackground=TEXT_COLOR,
        relief="flat",
    )
    if hide_text:
        entry.config(show="•")
    entry.pack(fill="x", ipady=6)

    return field_frame, entry


# Show a message on the card in the given color (red for errors, green for success)
def show_message(page, text, color):
    page["message_label"].config(text=text, fg=color)


# Switch the card between "login" and "signup" mode by changing texts and showing or hiding Confirm Password
def set_mode(page, mode):
    page["mode"] = mode
    show_message(page, "", ERROR_COLOR)
    page["password_entry"].delete(0, tk.END)
    page["confirm_entry"].delete(0, tk.END)

    if mode == "login":
        page["confirm_frame"].pack_forget()
        page["submit_button"].config(text="Log In")
        page["switch_link"].config(text="New here? Create an account")
    else:
        page["confirm_frame"].pack(fill="x", pady=(0, 12), before=page["message_label"])
        page["submit_button"].config(text="Sign Up")
        page["switch_link"].config(text="Already have an account? Log in")


# Flip to the other mode when the link at the bottom is clicked
def on_switch_click(page):
    if page["mode"] == "login":
        set_mode(page, "signup")
    else:
        set_mode(page, "login")


# Check the form, then log in or sign up depending on the current mode
def on_submit(page, on_login_success):
    username = page["username_entry"].get().strip()
    password = page["password_entry"].get()
    confirm = page["confirm_entry"].get()

    if page["mode"] == "login":
        if username == "" or password == "":
            show_message(page, "Please fill in all fields", ERROR_COLOR)
            return

        user_id = database.check_login(username, password)
        if user_id is None:
            show_message(page, "Incorrect username or password", ERROR_COLOR)
            return

        show_message(page, "", ERROR_COLOR)
        on_login_success(user_id, username)

    else:
        if username == "" or password == "" or confirm == "":
            show_message(page, "Please fill in all fields", ERROR_COLOR)
            return
        if len(password) < 6:
            show_message(page, "Password must be at least 6 characters", ERROR_COLOR)
            return
        if password != confirm:
            show_message(page, "Passwords do not match", ERROR_COLOR)
            return
        if not database.create_user(username, password):
            show_message(page, "Username already taken", ERROR_COLOR)
            return

        set_mode(page, "login")
        show_message(page, "Account created! Please log in.", ACCENT_COLOR)
        page["password_entry"].focus_set()


# Build the login/signup card in the middle of the parent frame and return the card
def build_auth_page(parent, on_login_success):
    card = tk.Frame(
        parent,
        bg=ENTRY_BG,
        highlightbackground=BORDER_COLOR,
        highlightthickness=1,
        padx=40,
        pady=30,
    )
    # relx/rely 0.5 = the middle of the parent; anchor="center" puts the card's middle there
    card.place(relx=0.5, rely=0.5, anchor="center")

    title_label = tk.Label(card, text="Consistify", font=("Segoe UI", 26, "bold"), fg=ACCENT_COLOR, bg=ENTRY_BG)
    title_label.pack()

    subtitle_label = tk.Label(card, text="Build habits that stick", font=("Segoe UI", 11), fg=TEXT_COLOR, bg=ENTRY_BG)
    subtitle_label.pack(pady=(0, 20))

    username_frame, username_entry = create_field(card, "Username")
    password_frame, password_entry = create_field(card, "Password", hide_text=True)
    confirm_frame, confirm_entry = create_field(card, "Confirm Password", hide_text=True)

    # wraplength stops a long message from making the card wider
    message_label = tk.Label(card, text="", font=("Segoe UI", 10), bg=ENTRY_BG, wraplength=300)
    message_label.pack(pady=(0, 8))

    submit_button = tk.Button(
        card,
        font=("Segoe UI", 12, "bold"),
        bg=ACCENT_COLOR,
        fg=BG_COLOR,
        activebackground=ACCENT_COLOR,
        relief="flat",
        pady=8,
    )
    submit_button.pack(fill="x")

    switch_link = tk.Label(card, font=("Segoe UI", 10, "underline"), fg=ACCENT_COLOR, bg=ENTRY_BG, cursor="hand2")
    switch_link.pack(pady=(15, 0))

    # One dictionary that holds the current mode and every widget the other functions need
    page = {
        "mode": "login",
        "username_entry": username_entry,
        "password_entry": password_entry,
        "confirm_frame": confirm_frame,
        "confirm_entry": confirm_entry,
        "message_label": message_label,
        "submit_button": submit_button,
        "switch_link": switch_link,
    }

    submit_button.config(command=lambda: on_submit(page, on_login_success))
    switch_link.bind("<Button-1>", lambda event: on_switch_click(page))
    for entry in (username_entry, password_entry, confirm_entry):
        entry.bind("<Return>", lambda event: on_submit(page, on_login_success))

    set_mode(page, "login")
    username_entry.focus_set()
    return card


# Print who logged in (used only by the test window below)
def print_login(user_id, username):
    print("Logged in:", user_id, username)


# Run this block only when auth.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    window = tk.Tk()
    window.title("Consistify - Login")
    window.geometry("1300x700")
    window.configure(bg=BG_COLOR)

    build_auth_page(window, print_login)
    window.mainloop()
