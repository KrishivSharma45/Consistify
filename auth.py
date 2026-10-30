# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import tkinter's font tool, so we can measure text and shrink the headline to fit
import tkinter.font as tkfont
# Import random to pick how bright each square of the decorative heatmap gets
import random

# Import our own database.py so we can create users and check logins
import database
# Import the app's shared colors and font
import theme
# Import our reusable widgets (the rounded button)
import ui

FORM_WIDTH = 360     # width of the login/signup form on the right (pixels)
LEFT_PADDING = 60    # space between the left edge and the text on the left half
HEADLINE_MAX = 30    # the headline's biggest font size; it shrinks below this if the left half is narrow
HEADLINE_MIN = 16    # ...but never below this

# Decorative heatmap on the left half
DECOR_ROWS = 7
DECOR_COLUMNS = 16
DECOR_SQUARE = 14
DECOR_GAP = 4
FILL_DELAY = 60      # milliseconds between two squares lighting up
FILL_PAUSE = 1500    # how long the full heatmap stays on screen before it starts again


# Put several Labels side by side so one line of text can have more than one color
def create_mixed_text(parent, parts, font, bg):
    line = tk.Frame(parent, bg=bg)
    # parts is a list of (text, color) pairs, e.g. [("Show up ", theme.TEXT), ("today", theme.ACCENT)]
    for text, color in parts:
        label = tk.Label(line, text=text, fg=color, bg=bg, font=font, padx=0, bd=0)
        label.pack(side="left")
    return line


# Light up the next square of the decorative heatmap, or start again once all are lit
def animate_heatmap(canvas, squares, levels, progress):
    # Stop for good once the page has been closed
    if not canvas.winfo_exists():
        return

    if progress["index"] == len(squares):
        # Everything is lit: empty the grid and start filling again
        for square in squares:
            canvas.itemconfig(square, fill=theme.BG)
        progress["index"] = 0
        delay = FILL_DELAY
    else:
        square = squares[progress["index"]]
        canvas.itemconfig(square, fill=theme.HEATMAP[levels[progress["index"]]])
        progress["index"] = progress["index"] + 1
        # After the very last square, wait a while so the full grid can be seen
        if progress["index"] == len(squares):
            delay = FILL_PAUSE
        else:
            delay = FILL_DELAY

    canvas.winfo_toplevel().after(delay, lambda: animate_heatmap(canvas, squares, levels, progress))


# Draw the empty decorative heatmap and start the animation that fills it in
def create_decorative_heatmap(parent):
    width = DECOR_COLUMNS * (DECOR_SQUARE + DECOR_GAP) - DECOR_GAP
    height = DECOR_ROWS * (DECOR_SQUARE + DECOR_GAP) - DECOR_GAP
    canvas = tk.Canvas(parent, width=width, height=height, bg=theme.CARD, highlightthickness=0)

    # A fixed seed gives the same pattern every time; later columns tend to be brighter, like growing progress
    random_numbers = random.Random(3)
    squares = []
    levels = []
    # Go column by column (one column = one week), top to bottom, the order a real heatmap fills in
    for column in range(DECOR_COLUMNS):
        for row in range(DECOR_ROWS):
            x1 = column * (DECOR_SQUARE + DECOR_GAP)
            y1 = row * (DECOR_SQUARE + DECOR_GAP)
            # Empty squares use the page background, because theme.HEATMAP[0] is the same as this panel's color
            square = canvas.create_rectangle(x1, y1, x1 + DECOR_SQUARE, y1 + DECOR_SQUARE, fill=theme.BG, outline="")
            squares.append(square)
            levels.append(min(4, random_numbers.randint(1, 3) + column // 8))

    animate_heatmap(canvas, squares, levels, {"index": 0})
    return canvas


# When the left half changes size, shrink the headline until it fits and let the smaller lines wrap
def fit_left_text(headline_font, wrapping_labels, event):
    available = event.width - LEFT_PADDING - 40
    # Start big, then go down one size at a time until the longest headline line fits.
    # Changing the Font object's size updates every label that uses it
    size = HEADLINE_MAX
    headline_font.configure(size=size)
    while size > HEADLINE_MIN and headline_font.measure("Thank yourself tomorrow.") > available:
        size = size - 1
        headline_font.configure(size=size)

    for label in wrapping_labels:
        label.config(wraplength=available)


# Build the left half: logo, headline, two lines of text, the filling heatmap and a footer
def build_left_half(left):
    logo = create_mixed_text(left, [("Consist", theme.ACCENT), ("ify", theme.TEXT)], (theme.FONT, 16, "bold"), theme.CARD)
    logo.place(x=40, y=28)

    # The middle block: anchor="w" with rely=0.5 puts its left edge at the vertical middle
    block = tk.Frame(left, bg=theme.CARD)
    block.place(x=LEFT_PADDING, rely=0.5, anchor="w")

    # tkinter has no letter-spacing option, so a space between every letter fakes the "spaced out" look
    eyebrow = tk.Label(block, text=" ".join("BUILD THE HABIT"), font=(theme.FONT, 9, "bold"), fg=theme.MUTED, bg=theme.CARD)
    eyebrow.pack(anchor="w", pady=(0, 10))

    # A Font object (not a plain tuple), so fit_left_text can change its size later
    headline_font = tkfont.Font(family=theme.FONT, size=HEADLINE_MAX, weight="bold")
    line_one = create_mixed_text(block, [("Show up ", theme.TEXT), ("today", theme.ACCENT), (".", theme.TEXT)], headline_font, theme.CARD)
    line_one.pack(anchor="w")
    line_two = tk.Label(block, text="Thank yourself tomorrow.", font=headline_font, fg=theme.TEXT, bg=theme.CARD)
    line_two.pack(anchor="w", pady=(0, 14))

    wrapping_labels = []
    for text in ("Track your habits, protect your streaks,", "and watch your consistency turn into a heatmap."):
        line = tk.Label(block, text=text, font=(theme.FONT, 11), fg=theme.MUTED, bg=theme.CARD, justify="left")
        line.pack(anchor="w")
        wrapping_labels.append(line)

    heatmap_canvas = create_decorative_heatmap(block)
    heatmap_canvas.pack(anchor="w", pady=(26, 0))

    footer = tk.Label(
        left,
        text="🔒 Passwords hashed with PBKDF2 · Your data stays on your device",
        font=(theme.FONT, 9),
        fg=theme.MUTED,
        bg=theme.CARD,
        justify="left",
    )
    # rely=1 is the bottom edge; anchor="sw" puts the label's bottom-left corner there, then y=-24 lifts it up
    footer.place(x=40, rely=1, y=-24, anchor="sw")
    wrapping_labels.append(footer)

    # <Configure> happens when the left half gets its size, and again whenever the window is resized
    left.bind("<Configure>", lambda event: fit_left_text(headline_font, wrapping_labels, event))


# Make an entry's outline the accent color while it has focus, and the border color when it doesn't
def set_outline(outline, color):
    outline.config(bg=color)


# Show or hide the password: show="" shows the real letters, show="•" hides them behind dots
def toggle_password(entry, eye):
    if entry.cget("show") == "":
        entry.config(show="•")
        eye.config(fg=theme.MUTED)
    else:
        entry.config(show="")
        eye.config(fg=theme.ACCENT)


# Create a small uppercase label and an entry box with a 1px outline (plus an 👁 toggle for passwords)
def create_field(form, label_text, is_password=False):
    field = tk.Frame(form, bg=theme.BG)
    field.pack(fill="x", pady=(0, 14))

    label = tk.Label(field, text=label_text, font=(theme.FONT, 8, "bold"), fg=theme.MUTED, bg=theme.BG)
    label.pack(anchor="w", pady=(0, 4))

    # The outline is a frame 1 pixel bigger than what's inside it, so its color shows as a thin border
    outline = tk.Frame(field, bg=theme.BORDER)
    outline.pack(fill="x")
    inside = tk.Frame(outline, bg=theme.CARD)
    inside.pack(fill="x", padx=1, pady=1)

    entry = tk.Entry(
        inside,
        font=(theme.FONT, 12),
        bg=theme.CARD,
        fg=theme.TEXT,
        insertbackground=theme.TEXT,
        relief="flat",
    )
    entry.pack(side="left", fill="x", expand=True, padx=(10, 0), ipady=7)

    if is_password:
        entry.config(show="•")
        eye = tk.Label(inside, text="👁", font=(theme.FONT, 11), fg=theme.MUTED, bg=theme.CARD, cursor="hand2")
        eye.pack(side="right", padx=10)
        eye.bind("<Button-1>", lambda event: toggle_password(entry, eye))

    # <FocusIn> happens when the user clicks into (or tabs into) the entry, <FocusOut> when they leave it
    entry.bind("<FocusIn>", lambda event: set_outline(outline, theme.ACCENT))
    entry.bind("<FocusOut>", lambda event: set_outline(outline, theme.BORDER))

    return field, entry


# Show a message under the form in the given color (theme.ERROR for errors, theme.SUCCESS for success)
def show_message(page, text, color):
    page["message_label"].config(text=text, fg=color)


# Switch the form between "login" and "signup" mode by changing texts and showing or hiding Confirm Password
def set_mode(page, mode):
    page["mode"] = mode
    show_message(page, "", theme.ERROR)
    page["password_entry"].delete(0, tk.END)
    page["confirm_entry"].delete(0, tk.END)

    if mode == "login":
        page["confirm_field"].pack_forget()
        page["heading"].config(text="Welcome back")
        page["subtitle"].config(text="Log in to keep your streak alive.")
        ui.set_button_text(page["submit_button"], "Log in")
        page["switch_link"].config(text="New here? Create an account")
    else:
        page["confirm_field"].pack(fill="x", pady=(0, 14), before=page["message_label"])
        page["heading"].config(text="Create your account")
        page["subtitle"].config(text="Start your first streak today.")
        ui.set_button_text(page["submit_button"], "Create account")
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
            show_message(page, "Please fill in all fields", theme.ERROR)
            return

        user_id = database.check_login(username, password)
        if user_id is None:
            show_message(page, "Incorrect username or password", theme.ERROR)
            return

        show_message(page, "", theme.ERROR)
        on_login_success(user_id, username)

    else:
        if username == "" or password == "" or confirm == "":
            show_message(page, "Please fill in all fields", theme.ERROR)
            return
        if len(password) < 6:
            show_message(page, "Password must be at least 6 characters", theme.ERROR)
            return
        if password != confirm:
            show_message(page, "Passwords do not match", theme.ERROR)
            return
        if not database.create_user(username, password):
            show_message(page, "Username already taken", theme.ERROR)
            return

        set_mode(page, "login")
        show_message(page, "Account created! Please log in.", theme.SUCCESS)
        page["password_entry"].focus_set()


# Create a text link that changes color under the mouse and runs command when clicked
def create_link(parent, text, color, hover_color, command, underline=False):
    if underline:
        font = (theme.FONT, 10, "underline")
    else:
        font = (theme.FONT, 10)
    link = tk.Label(parent, text=text, font=font, fg=color, bg=theme.BG, cursor="hand2")
    link.bind("<Button-1>", lambda event: command())
    link.bind("<Enter>", lambda event: link.config(fg=hover_color))
    link.bind("<Leave>", lambda event: link.config(fg=color))
    return link


# Build the right half: back link and the login/signup form; return the page dictionary
def build_right_half(right, on_login_success, on_back):
    if on_back is not None:
        back_link = create_link(right, "← Back to home", theme.MUTED, theme.ACCENT, on_back)
        # relx=1 is the right edge; anchor="ne" puts the link's top-right corner there, x=-40 moves it in
        back_link.place(relx=1, x=-40, y=28, anchor="ne")

    # The form is FORM_WIDTH wide and sits in the middle of the right half
    form = tk.Frame(right, bg=theme.BG)
    form.place(relx=0.5, rely=0.5, anchor="center", width=FORM_WIDTH)

    heading = tk.Label(form, font=(theme.FONT, 22, "bold"), fg=theme.TEXT, bg=theme.BG)
    heading.pack(anchor="w")
    subtitle = tk.Label(form, font=(theme.FONT, 11), fg=theme.MUTED, bg=theme.BG)
    subtitle.pack(anchor="w", pady=(2, 24))

    username_field, username_entry = create_field(form, "USERNAME")
    password_field, password_entry = create_field(form, "PASSWORD", is_password=True)
    confirm_field, confirm_entry = create_field(form, "CONFIRM PASSWORD", is_password=True)

    # wraplength stops a long message from making the form wider
    message_label = tk.Label(form, text="", font=(theme.FONT, 10), bg=theme.BG, wraplength=FORM_WIDTH)
    message_label.pack(pady=(0, 8))

    # fill="x" stretches the button across the form; ui.py redraws its rounded shape to the new width
    # (the lambda looks up `page` only when clicked, after the dictionary below exists)
    submit_button = ui.rounded_button(
        form, "Log in", lambda: on_submit(page, on_login_success), "filled", width=FORM_WIDTH, height=46, font_size=12
    )
    submit_button.pack(fill="x")

    # One dictionary that holds the current mode and every widget the other functions need
    page = {
        "mode": "login",
        "heading": heading,
        "subtitle": subtitle,
        "username_entry": username_entry,
        "password_entry": password_entry,
        "confirm_field": confirm_field,
        "confirm_entry": confirm_entry,
        "message_label": message_label,
        "submit_button": submit_button,
    }

    page["switch_link"] = create_link(form, "", theme.ACCENT, theme.ACCENT_HOVER, lambda: on_switch_click(page), underline=True)
    page["switch_link"].pack(pady=(16, 0))

    for entry in (username_entry, password_entry, confirm_entry):
        entry.bind("<Return>", lambda event: on_submit(page, on_login_success))

    return page


# Build the split-screen login/signup page inside the parent and return the page frame
def build_auth_page(parent, on_login_success, start_mode="login", on_back=None):
    page_frame = tk.Frame(parent, bg=theme.BG)
    page_frame.pack(fill="both", expand=True)

    # relwidth=0.5 makes each half exactly half as wide as the page, whatever the window size;
    # relheight=1 makes both halves as tall as the page. The right half starts at relx=0.5, the middle
    left = tk.Frame(page_frame, bg=theme.CARD)
    left.place(relx=0, rely=0, relwidth=0.5, relheight=1)
    right = tk.Frame(page_frame, bg=theme.BG)
    right.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

    build_left_half(left)
    page = build_right_half(right, on_login_success, on_back)

    set_mode(page, start_mode)
    page["username_entry"].focus_set()
    return page_frame


# Print who logged in (used only by the test window below)
def print_login(user_id, username):
    print("Logged in:", user_id, username)


# Print that the back link was clicked (used only by the test window below)
def print_back():
    print("Back to home clicked")


# Run this block only when auth.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    window = tk.Tk()
    window.title("Consistify - Login")
    window.geometry("1100x700")
    window.configure(bg=theme.BG)

    build_auth_page(window, print_login, on_back=print_back)
    window.mainloop()
