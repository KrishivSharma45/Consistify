# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk

# Import our own files: the database and every page of the app
import auth
import badges
import database
import gui
import heatmap
import settings
import theme
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


# Create one full-width sidebar button
def create_sidebar_button(sidebar, text, command):
    button = tk.Button(
        sidebar,
        text=text,
        font=(theme.FONT, 11),
        bg=theme.CARD,
        fg=theme.TEXT,
        activebackground=theme.BORDER,
        activeforeground=theme.TEXT,
        relief="flat",
        anchor="w",
        padx=20,
        pady=8,
        cursor="hand2",
        command=command,
    )
    return button


# Highlight the chosen sidebar button, then fill the content area with that tab
def show_tab(tab_name, content, buttons):
    for name, button in buttons.items():
        if name == tab_name:
            button.config(bg=theme.BORDER, fg=theme.ACCENT)
        else:
            button.config(bg=theme.CARD, fg=theme.TEXT)

    for child in content.winfo_children():
        child.destroy()

    if tab_name == "today":
        gui.create_habit_section(content, app["user_id"])
    elif tab_name == "badges":
        badges.build_badges_page(content, app["user_id"])
    elif tab_name == "settings":
        settings.build_settings_page(content, app["user_id"], app["username"], on_account_deleted)
    else:
        # Rebuilt every time the tab is opened, so the heatmap, weekly chart and stats always show fresh data
        heatmap_holder = tk.Frame(content, bg=theme.BG)
        heatmap_holder.pack(pady=30)
        # Top row: the 90-day heatmap on the left, this week's bar chart next to it
        top_row = tk.Frame(heatmap_holder, bg=theme.BG)
        top_row.pack()
        heatmap_column = tk.Frame(top_row, bg=theme.BG)
        heatmap_column.pack(side="left", anchor="n")
        heatmap.create_heatmap_section(heatmap_column, app["user_id"])
        heatmap.draw_weekly_chart(top_row, app["user_id"]).pack(side="left", anchor="n", padx=(24, 0), pady=10)
        heatmap.create_stats_section(heatmap_holder, app["user_id"])


# Build the Dashboard: a sidebar on the left and a content area on the right
def build_dashboard(parent):
    sidebar = tk.Frame(parent, bg=theme.CARD, width=200)
    sidebar.pack(side="left", fill="y")
    # Without this, the sidebar would shrink or grow to fit its buttons instead of staying 200px wide
    sidebar.pack_propagate(False)

    content = tk.Frame(parent, bg=theme.BG)
    content.pack(side="right", fill="both", expand=True)

    title_label = tk.Label(sidebar, text="Consistify", font=(theme.FONT, 18, "bold"), fg=theme.ACCENT, bg=theme.CARD)
    title_label.pack(anchor="w", padx=20, pady=(25, 0))

    hello_label = tk.Label(sidebar, text="Hi, " + app["username"] + " 👋", font=(theme.FONT, 11), fg=theme.TEXT, bg=theme.CARD)
    hello_label.pack(anchor="w", padx=20, pady=(0, 25))

    buttons = {}
    buttons["today"] = create_sidebar_button(sidebar, "✅ Today", lambda: show_tab("today", content, buttons))
    buttons["progress"] = create_sidebar_button(sidebar, "🟩 Progress", lambda: show_tab("progress", content, buttons))
    buttons["badges"] = create_sidebar_button(sidebar, "🏆 Badges", lambda: show_tab("badges", content, buttons))
    buttons["settings"] = create_sidebar_button(sidebar, "⚙️ Settings", lambda: show_tab("settings", content, buttons))
    logout_button = create_sidebar_button(sidebar, "🚪 Logout", on_logout)

    buttons["today"].pack(fill="x")
    buttons["progress"].pack(fill="x")
    buttons["badges"].pack(fill="x")
    logout_button.pack(side="bottom", fill="x", pady=(0, 20))
    # Packed at the bottom AFTER Logout, so it sits just above Logout
    buttons["settings"].pack(side="bottom", fill="x")

    show_tab("today", content, buttons)


# Run this block only when main.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    app["window"] = tk.Tk()
    app["window"].title("Consistify")
    app["window"].configure(bg=theme.BG)
    center_window(app["window"])

    show_welcome()
    app["window"].mainloop()
