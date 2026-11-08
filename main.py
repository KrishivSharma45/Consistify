# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk

# Import our own files: the database and every page of the app
import auth
import badges
import database
import gui
import heatmap
import settings
import splash
import theme
import ui
import welcome

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700

# The one window, and who is logged in (None when nobody is)
app = {"window": None, "user_id": None, "username": None}


# Set the window's size and move it to the middle of the screen
def center_window(window):
    x = (window.winfo_screenwidth() - WINDOW_WIDTH) // 2
    y = (window.winfo_screenheight() - WINDOW_HEIGHT) // 2
    window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")


# Remove everything from the window, then build a new page in it
def show_page(build_function):
    for child in app["window"].winfo_children():
        child.destroy()
    build_function(app["window"])


# Open the short intro animation; when it ends (or is skipped), open the Welcome page
def show_splash():
    show_page(lambda parent: splash.build_splash_page(parent, show_welcome))


# Open the Welcome page; "Get Started" and "Sign Up" open Sign Up, "Log In" opens Log In
def show_welcome():
    show_page(lambda parent: welcome.build_welcome_page(parent, show_signup, show_login, show_signup))


# Open the auth page in Log In mode; a correct login calls on_login, "Back to home" opens the Welcome page
def show_login():
    show_page(lambda parent: auth.build_auth_page(parent, on_login, "login", on_back=show_welcome))


# Open the auth page in Sign Up mode
def show_signup():
    show_page(lambda parent: auth.build_auth_page(parent, on_login, "signup", on_back=show_welcome))


# Remember who logged in, then open the Dashboard
def on_login(user_id, username):
    app["user_id"] = user_id
    app["username"] = username
    show_page(build_dashboard)


# Forget the user and go back to the Welcome page
def on_logout():
    app["user_id"] = None
    app["username"] = None
    show_welcome()


# The account no longer exists, so log out (forget the user) and go back to the Welcome page
def on_account_deleted():
    on_logout()


# Color one sidebar item: active (accent bar + lighter background + accent text), hovered, or normal
def paint_nav_item(item, hovered=False):
    if item["active"]:
        background, text_color, bar_color = theme.BORDER, theme.ACCENT, theme.ACCENT
    elif hovered:
        background, text_color, bar_color = theme.BORDER, theme.TEXT, theme.BORDER
    else:
        background, text_color, bar_color = theme.CARD, theme.TEXT, theme.CARD
    item["frame"].config(bg=background)
    item["label"].config(bg=background, fg=text_color)
    # The bar takes its own color: accent when active, otherwise the same as the background (so it's invisible)
    item["bar"].config(bg=bar_color)


# The mouse left an item (or moved onto its text): go back to normal only if it really left the whole item
def leave_nav_item(item):
    x, y = item["frame"].winfo_pointerxy()
    if not ui.is_inside(item["frame"].winfo_containing(x, y), item["frame"]):
        paint_nav_item(item)


# Create one sidebar item: a 3px bar on the left edge and the text; return a dictionary of its parts
def create_nav_item(sidebar, text, command):
    frame = tk.Frame(sidebar, bg=theme.CARD, cursor="hand2")
    bar = tk.Frame(frame, bg=theme.CARD, width=3)
    bar.pack(side="left", fill="y")
    label = tk.Label(frame, text=text, font=(theme.FONT, 11), fg=theme.TEXT, bg=theme.CARD, anchor="w", padx=17, pady=8, cursor="hand2")
    label.pack(side="left", fill="x", expand=True)

    item = {"frame": frame, "bar": bar, "label": label, "active": False}
    # Clicking the item or its text does the same thing
    for part in (frame, label):
        part.bind("<Button-1>", lambda event: command())
    frame.bind("<Enter>", lambda event: paint_nav_item(item, hovered=True))
    frame.bind("<Leave>", lambda event: leave_nav_item(item))
    return item


# A small, spaced-out uppercase heading in the sidebar, like "M E N U"
def create_section_label(sidebar, text):
    # tkinter has no letter-spacing option, so a space between every letter fakes it
    return tk.Label(sidebar, text=" ".join(text), font=(theme.FONT, 8, "bold"), fg=theme.MUTED, bg=theme.CARD)


# Draw the logo: a tiny 2x2 grid of heatmap-colored squares, then "Consistify"
def create_logo(sidebar):
    row = tk.Frame(sidebar, bg=theme.CARD)
    icon = tk.Canvas(row, width=20, height=20, bg=theme.CARD, highlightthickness=0)
    shades = [theme.HEATMAP[2], theme.HEATMAP[4], theme.HEATMAP[1], theme.HEATMAP[3]]
    for i in range(4):
        # i % 2 is the column (0, 1, 0, 1) and i // 2 the row (0, 0, 1, 1)
        left = (i % 2) * 11
        top = (i // 2) * 11
        icon.create_rectangle(left, top, left + 9, top + 9, fill=shades[i], outline="")
    icon.pack(side="left", padx=(0, 10))
    name = tk.Label(row, text="Consistify", font=(theme.FONT, 14, "bold"), fg=theme.ACCENT, bg=theme.CARD)
    name.pack(side="left")
    return row


# Build the user card at the bottom of the sidebar: round avatar, username and best streak; return the streak label
def create_user_card(sidebar, username):
    card = tk.Frame(sidebar, bg=theme.BG, highlightthickness=1, highlightbackground=theme.BORDER, padx=10, pady=10)

    # Row 1: the avatar (an accent-colored circle with the username's first letter) and the username
    top = tk.Frame(card, bg=theme.BG)
    top.pack(fill="x")
    avatar = tk.Canvas(top, width=32, height=32, bg=theme.BG, highlightthickness=0)
    avatar.create_oval(1, 1, 31, 31, fill=theme.ACCENT, outline="")
    avatar.create_text(16, 16, text=username[:1].upper(), fill=theme.BG, font=(theme.FONT, 12, "bold"))
    avatar.pack(side="left", padx=(0, 10))
    name = tk.Label(top, text=username, font=(theme.FONT, 10, "bold"), fg=theme.TEXT, bg=theme.BG)
    name.pack(side="left")

    # Row 2: the best streak, on its own line so it has the card's full width
    streak = tk.Label(card, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.BG)
    streak.pack(anchor="w", pady=(6, 0))
    return card, streak


# Update "🔥 Best streak: N" on the user card (called when the dashboard opens and after every tick/add/delete)
def refresh_user_card(streak_label):
    if streak_label.winfo_exists():
        streak_label.config(text="🔥 Best streak: " + str(gui.get_overall_best_streak(app["user_id"])))


# Mark the chosen sidebar item as active, then fill the content area with that tab
def show_tab(tab_name, content, items, streak_label):
    for name, item in items.items():
        item["active"] = name == tab_name
        paint_nav_item(item)

    for child in content.winfo_children():
        child.destroy()
    # Clearing the content area also removed its grid background, so put a fresh one behind the new page
    ui.draw_grid_background(content)

    if tab_name == "today":
        # on_change runs after every tick, add and delete, so the best streak on the user card stays up to date
        gui.create_habit_section(content, app["user_id"], on_change=lambda: refresh_user_card(streak_label), username=app["username"])
    elif tab_name == "badges":
        badges.build_badges_page(content, app["user_id"])
    elif tab_name == "settings":
        settings.build_settings_page(content, app["user_id"], app["username"], on_account_deleted)
    else:
        # Rebuilt every time the tab is opened, so every chart on the Progress page shows fresh data
        heatmap.build_progress_page(content, app["user_id"])


# Build the Dashboard: a sidebar on the left and a content area on the right
def build_dashboard(parent):
    sidebar = tk.Frame(parent, bg=theme.CARD, width=200)
    sidebar.pack(side="left", fill="y")
    # Without this, the sidebar would shrink or grow to fit its buttons instead of staying 200px wide
    sidebar.pack_propagate(False)

    content = tk.Frame(parent, bg=theme.BG)
    content.pack(side="right", fill="both", expand=True)

    create_logo(sidebar).pack(anchor="w", padx=20, pady=(24, 22))

    # The user card is built first (its streak label is needed by the Today tab), packed further down
    user_card, streak_label = create_user_card(sidebar, app["username"])

    items = {}
    items["today"] = create_nav_item(sidebar, "✅  Today", lambda: show_tab("today", content, items, streak_label))
    items["progress"] = create_nav_item(sidebar, "🟩  Progress", lambda: show_tab("progress", content, items, streak_label))
    items["badges"] = create_nav_item(sidebar, "🏆  Badges", lambda: show_tab("badges", content, items, streak_label))
    items["settings"] = create_nav_item(sidebar, "⚙️  Settings", lambda: show_tab("settings", content, items, streak_label))
    # Logout is an item too, but never "active": it just logs out
    logout = create_nav_item(sidebar, "🚪  Logout", on_logout)

    # Top section: MENU and its three items
    create_section_label(sidebar, "MENU").pack(anchor="w", padx=20, pady=(0, 6))
    items["today"]["frame"].pack(fill="x")
    items["progress"]["frame"].pack(fill="x")
    items["badges"]["frame"].pack(fill="x")

    # Bottom section, packed from the bottom up: user card, Logout, Settings, then the ACCOUNT label above them
    user_card.pack(side="bottom", fill="x", padx=12, pady=(10, 16))
    logout["frame"].pack(side="bottom", fill="x")
    items["settings"]["frame"].pack(side="bottom", fill="x")
    create_section_label(sidebar, "ACCOUNT").pack(side="bottom", anchor="w", padx=20, pady=(0, 6))

    refresh_user_card(streak_label)
    show_tab("today", content, items, streak_label)


# Run this block only when main.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    app["window"] = tk.Tk()
    app["window"].title("Consistify")
    app["window"].configure(bg=theme.BG)
    center_window(app["window"])

    show_splash()
    app["window"].mainloop()
