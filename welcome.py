# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import tkinter's font tool, so we can measure how wide a piece of text will be
import tkinter.font as tkfont
# Import math for sin and cos, which move the squares around the title in an oval
import math
# Import random to pick the shades of the decorative heatmap squares
import random
# Import sys to check whether we are running on a Mac (the mouse wheel works differently there)
import sys

# Colors for this page: change them here and the whole page follows
BACKGROUND = "#3E2723"     # page background (dark brown)
GRID_LINE = "#241614"      # the grid lines on the background (a blackish brown, softer than pure black)
PINK = "#E38792"           # main text color and buttons
PINK_HOVER = "#cc6f7b"     # slightly deeper pink under the mouse, so the change is visible
HIGHLIGHT = "#fff8f0"      # highlighted words (a warm white)
GREY = "#cdb9b3"           # body text (light, so it's readable on the dark background)
CARD = "#4a2f2b"           # feature card background
BORDER = "#5e423d"         # card borders and thin lines

# 5 shades for the decorative heatmap and the orbiting squares, from empty to full (the last one is PINK)
PINK_SHADES = ["#4f3530", "#74474a", "#9e5f66", "#c4737d", "#E38792"]

NAVBAR_HEIGHT = 64
GRID_SIZE = 32       # size of one square of the background grid (pixels)
HERO_GAP = 80        # empty space between the big title and the tagline (the orbit passes through it)

# Size settings for the decorative heatmap (in pixels)
DECOR_ROWS = 7
DECOR_COLUMNS = 30
DECOR_SQUARE = 12
DECOR_GAP = 3

# Smooth scrolling and mouse wheel settings
SCROLL_STEPS = 25    # how many small steps one smooth scroll takes
SCROLL_DELAY = 15    # milliseconds between those steps
SCROLL_MARGIN = 30   # stop this many pixels above a section, so its heading isn't squashed under the navbar
WHEEL_PIXELS = 40    # how far one notch of the mouse wheel scrolls

# Orbit animation settings
ORBIT_SQUARES = 16   # how many squares circle the title
ORBIT_SPEED = 0.012  # how far (in radians) they move each frame
ORBIT_DELAY = 30     # milliseconds between frames (about 33 frames a second)
ORBIT_SCALE = 1.45   # how much bigger than the title the oval is


# Draw faint vertical and horizontal lines every GRID_SIZE pixels, like graph paper
def draw_grid(canvas, width, height):
    for x in range(0, int(width), GRID_SIZE):
        canvas.create_line(x, 0, x, height, fill=GRID_LINE, tags="grid")
    for y in range(0, int(height), GRID_SIZE):
        canvas.create_line(0, y, width, y, fill=GRID_LINE, tags="grid")


# Draw several pieces of text side by side on a canvas, each in its own color; return the total width
def draw_mixed_text(canvas, x, y, parts, font, anchor="center", tags=""):
    # parts is a list of (text, color) pairs, e.g. [("Build habits that ", PINK), ("stick.", HIGHLIGHT)]
    total_width = 0
    for text, color in parts:
        total_width = total_width + font.measure(text)

    if anchor == "center":
        left = x - total_width / 2
    else:
        left = x

    for text, color in parts:
        canvas.create_text(left, y, text=text, fill=color, font=font, anchor="w", tags=tags)
        left = left + font.measure(text)

    return total_width


# Recolor a button's border, background and text (used by the hover effect)
def paint_button(border, label, colors):
    border_color, background, text_color = colors
    border.config(bg=border_color)
    label.config(bg=background, fg=text_color)


# Create a button from a Label inside a 1-pixel frame, so we can choose the border color
def create_button(parent, text, filled, command, font_size=11):
    if filled:
        normal = (PINK, PINK, BACKGROUND)
        hover = (PINK_HOVER, PINK_HOVER, BACKGROUND)
    else:
        normal = (HIGHLIGHT, BACKGROUND, HIGHLIGHT)
        hover = (PINK, BACKGROUND, PINK)

    border = tk.Frame(parent)
    label = tk.Label(border, text=text, font=("Segoe UI", font_size, "bold"), padx=18, pady=6, cursor="hand2")
    label.pack(padx=1, pady=1)
    paint_button(border, label, normal)

    label.bind("<Button-1>", lambda event: command())
    label.bind("<Enter>", lambda event: paint_button(border, label, hover))
    label.bind("<Leave>", lambda event: paint_button(border, label, normal))
    return border


# Change a canvas text item's color and the mouse pointer (used by the navbar hover effect)
def hover_text(canvas, item, color, cursor):
    canvas.itemconfig(item, fill=color)
    canvas.config(cursor=cursor)


# Draw a text link on the navbar that turns pink under the mouse and runs command when clicked
def draw_link(canvas, x, y, text, anchor, command):
    item = canvas.create_text(x, y, text=text, fill=HIGHLIGHT, font=("Segoe UI", 11), anchor=anchor)
    canvas.tag_bind(item, "<Button-1>", lambda event: command())
    canvas.tag_bind(item, "<Enter>", lambda event: hover_text(canvas, item, PINK, "hand2"))
    canvas.tag_bind(item, "<Leave>", lambda event: hover_text(canvas, item, HIGHLIGHT, ""))


# Scroll the page with the mouse wheel (Windows sends steps of 120, a Mac sends small numbers)
def on_mouse_wheel(canvas, event):
    # The wheel is bound for the whole app, so do nothing once this page has been closed
    if not canvas.winfo_exists():
        return

    if sys.platform == "darwin":
        notches = -event.delta / 10
    else:
        notches = -event.delta / 120
    # One "unit" is 1 pixel (yscrollincrement=1), so this moves WHEEL_PIXELS per notch
    canvas.yview_scroll(int(notches * WHEEL_PIXELS), "units")


# Move the page a little closer to its target, then ask after() to do the next step
def animate_scroll(canvas, start, end, step):
    if not canvas.winfo_exists():
        return

    progress = step / SCROLL_STEPS
    # "Ease out": big moves at the start, tiny moves at the end, so it glides to a stop
    eased = 1 - (1 - progress) ** 3
    canvas.yview_moveto(start + (end - start) * eased)

    if step < SCROLL_STEPS:
        # Ask the main window (not the canvas) to wait, so leaving the page mid-scroll causes no error
        canvas.winfo_toplevel().after(SCROLL_DELAY, lambda: animate_scroll(canvas, start, end, step + 1))


# Smoothly scroll the page so the named section ("hero", "about" or "features") is at the top
def scroll_to_section(canvas, state, name):
    top, bottom = canvas.yview()
    end = (state["sections"][name] - SCROLL_MARGIN) / state["page_height"]
    # Don't go above the top, and the last section can't reach the very top, so stop where the page ends
    end = max(0, min(end, 1 - (bottom - top)))
    animate_scroll(canvas, top, end, 1)


# Put every orbiting square at its place on the oval for the current angle
def move_orbit(canvas, state):
    orbit = state["orbit"]
    squares = state["orbit_items"]

    for i in range(len(squares)):
        # Spread the squares evenly around the oval: each one is a bit further round than the last
        angle = state["angle"] + i * 2 * math.pi / len(squares)
        x = orbit["x"] + orbit["rx"] * math.cos(angle)
        y = orbit["y"] + orbit["ry"] * math.sin(angle)
        # Bigger at the bottom of the oval, smaller at the top, so the ring looks tilted towards you
        half_size = 4 + 3 * (1 + math.sin(angle)) / 2
        canvas.coords(squares[i], x - half_size, y - half_size, x + half_size, y + half_size)


# Move the orbit a tiny step, then ask after() to do it again, forever (until the page closes)
def animate_orbit(canvas, state):
    if not canvas.winfo_exists():
        return

    state["angle"] = state["angle"] + ORBIT_SPEED
    if len(state["orbit_items"]) > 0:
        move_orbit(canvas, state)

    # Ask the main window (not the canvas) to wait: when the page is closed the canvas is destroyed,
    # and a timer belonging to a destroyed canvas would print an "invalid command name" error
    canvas.winfo_toplevel().after(ORBIT_DELAY, lambda: animate_orbit(canvas, state))


# Draw the hero: the big title exactly in the middle, the orbit around it, tagline and button below
def draw_hero(canvas, state, width, height):
    fonts = state["fonts"]
    middle_x = width / 2
    middle_y = height / 2

    title_width = draw_mixed_text(canvas, middle_x, middle_y, [("Consist", PINK), ("ify", HIGHLIGHT)], fonts["title"])
    title_height = fonts["title"].metrics("linespace")
    tagline_height = fonts["tagline"].metrics("linespace")

    # Work out each y from the real text heights, so nothing overlaps at any screen scaling
    tagline_y = middle_y + title_height / 2 + HERO_GAP + tagline_height / 2
    draw_mixed_text(canvas, middle_x, tagline_y, [("Build habits that ", PINK), ("stick.", HIGHLIGHT)], fonts["tagline"])

    button = state["get_started"]
    button_y = tagline_y + tagline_height / 2 + 30 + button.winfo_reqheight() / 2
    canvas.create_window(middle_x, button_y, window=button)

    # The oval the squares travel on. To pass outside even the corners of the title,
    # it must be about 1.45 times the title's half-width and half-height
    state["orbit"] = {
        "x": middle_x,
        "y": middle_y,
        "rx": title_width / 2 * ORBIT_SCALE,
        "ry": title_height / 2 * ORBIT_SCALE,
    }
    state["orbit_items"] = []
    for i in range(ORBIT_SQUARES):
        # Use the 4 colored shades in turn (skip shade 0, which is the "empty" color)
        square = canvas.create_rectangle(0, 0, 0, 0, fill=PINK_SHADES[1 + i % 4], outline="")
        state["orbit_items"].append(square)
    move_orbit(canvas, state)


# Draw the About section starting at y = top; return the y where it ends
def draw_about(canvas, state, top, width):
    heading_font = state["fonts"]["heading"]
    y = top + 60
    state["sections"]["about"] = y

    heading_height = heading_font.metrics("linespace")
    draw_mixed_text(canvas, width / 2, y + heading_height / 2, [("Why ", PINK), ("habits", HIGHLIGHT), (" matter", PINK)], heading_font)
    y = y + heading_height + 20

    lines = [
        "Consistify is a simple desktop habit tracker: tick off your habits each day and watch them add up.",
        "Small actions repeated every day beat big bursts of motivation.",
        "Seeing your streak grow makes it easier to keep going tomorrow.",
    ]
    for line in lines:
        # width=900 wraps a long line onto a second line instead of running off the window
        item = canvas.create_text(width / 2, y, text=line, fill=GREY, font=("Segoe UI", 13), width=900, justify="center", anchor="n")
        y = canvas.bbox(item)[3] + 6

    return y + 60


# Draw a grid of little squares that gets brighter from left to right, like progress growing
def draw_decorative_heatmap(canvas, left, top):
    # A fixed seed gives the same "random" pattern every time the page opens
    random_numbers = random.Random(7)

    for column in range(DECOR_COLUMNS):
        for row in range(DECOR_ROWS):
            # Left columns get a bonus of 0, the right-most columns a bonus of 2
            bonus = column * 3 // DECOR_COLUMNS
            level = random_numbers.randint(0, 2) + bonus

            x1 = left + column * (DECOR_SQUARE + DECOR_GAP)
            y1 = top + row * (DECOR_SQUARE + DECOR_GAP)
            canvas.create_rectangle(x1, y1, x1 + DECOR_SQUARE, y1 + DECOR_SQUARE, fill=PINK_SHADES[level], outline="")


# Draw the three feature cards in a row starting at y = top; return the y where they end
def draw_feature_cards(canvas, top, width):
    cards = [
        ("🔥 Streaks", "See how many days in a row you've kept each habit going."),
        ("🟩 Heatmap", "Your last 90 days at a glance: the brighter, the better."),
        ("📊 Stats & Export", "Best streaks and completion rates, saved to a CSV file."),
    ]
    card_width = 270
    card_gap = 16
    left = width / 2 - (3 * card_width + 2 * card_gap) / 2

    # First write the text in each card, remembering how low the lowest text goes
    lowest = top
    for i in range(len(cards)):
        heading, text = cards[i]
        x = left + i * (card_width + card_gap) + 20
        heading_item = canvas.create_text(x, top + 18, text=heading, fill=PINK, font=("Segoe UI", 13, "bold"), anchor="nw")
        heading_bottom = canvas.bbox(heading_item)[3]
        text_item = canvas.create_text(x, heading_bottom + 6, text=text, fill=GREY, font=("Segoe UI", 10), width=card_width - 40, anchor="nw")
        lowest = max(lowest, canvas.bbox(text_item)[3])

    # Then draw all three card boxes the same height, tall enough for the tallest text
    bottom = lowest + 18
    for i in range(len(cards)):
        x = left + i * (card_width + card_gap)
        canvas.create_rectangle(x, top, x + card_width, bottom, fill=CARD, outline=BORDER, tags="card")

    return bottom


# Draw the Features section starting at y = top; return the y where the page ends
def draw_features(canvas, state, top, width):
    heading_font = state["fonts"]["heading"]
    y = top + 60
    state["sections"]["features"] = y

    heading_height = heading_font.metrics("linespace")
    draw_mixed_text(canvas, width / 2, y + heading_height / 2, [("Everything you need to ", PINK), ("stay consistent", HIGHLIGHT)], heading_font)
    y = y + heading_height + 30

    decor_width = DECOR_COLUMNS * (DECOR_SQUARE + DECOR_GAP) - DECOR_GAP
    decor_height = DECOR_ROWS * (DECOR_SQUARE + DECOR_GAP) - DECOR_GAP
    draw_decorative_heatmap(canvas, width / 2 - decor_width / 2, y)
    y = y + decor_height + 30

    y = draw_feature_cards(canvas, y, width)

    # A thin line, then the footer text
    y = y + 70
    canvas.create_line(60, y, width - 60, y, fill=BORDER)
    footer = canvas.create_text(
        width / 2, y + 20, text="Made by Krishiv Sharma, Keerthy Sarayuu & Shaan Vyas",
        fill=GREY, font=("Segoe UI", 9), anchor="n",
    )
    return canvas.bbox(footer)[3] + 20


# Clear the scroll canvas and draw the whole page again at its current size
def draw_page(canvas, state, event):
    canvas.delete("all")
    width = event.width
    height = event.height

    # The hero is exactly as tall as the visible area, so the title sits in its middle
    draw_hero(canvas, state, width, height)
    y = draw_about(canvas, state, height, width)
    y = draw_features(canvas, state, y, width)
    state["page_height"] = y

    # The grid is drawn last but pushed to the very back; the card boxes go just above it
    draw_grid(canvas, width, y)
    canvas.tag_lower("card")
    canvas.tag_lower("grid")

    # Tell the canvas how tall the page is, so it knows how far it can scroll
    canvas.configure(scrollregion=(0, 0, width, y))


# Clear the navbar and draw it again: logo on the left, links in the middle, buttons on the right
def draw_navbar(navbar, canvas, state, event):
    navbar.delete("all")
    width = event.width
    middle_y = NAVBAR_HEIGHT / 2
    draw_grid(navbar, width, NAVBAR_HEIGHT)

    # Clicking the logo scrolls back to the top
    draw_mixed_text(navbar, 30, middle_y, [("Consist", PINK), ("ify", HIGHLIGHT)], state["fonts"]["logo"], anchor="w", tags="logo")
    navbar.tag_bind("logo", "<Button-1>", lambda event: scroll_to_section(canvas, state, "hero"))
    navbar.tag_bind("logo", "<Enter>", lambda event: navbar.config(cursor="hand2"))
    navbar.tag_bind("logo", "<Leave>", lambda event: navbar.config(cursor=""))

    # "About" ends just left of the middle and "Features" starts just right of it
    draw_link(navbar, width / 2 - 14, middle_y, "About", "e", lambda: scroll_to_section(canvas, state, "about"))
    draw_link(navbar, width / 2 + 14, middle_y, "Features", "w", lambda: scroll_to_section(canvas, state, "features"))

    signup = state["signup_button"]
    navbar.create_window(width - 30, middle_y, window=signup, anchor="e")
    navbar.create_window(width - 30 - signup.winfo_reqwidth() - 10, middle_y, window=state["login_button"], anchor="e")


# Build the whole landing page inside the parent and return the page frame
def build_welcome_page(parent, on_get_started, on_login, on_signup):
    page = tk.Frame(parent, bg=BACKGROUND)
    page.pack(fill="both", expand=True)

    # 1) The navbar is packed first, so it always keeps the top strip of the page
    navbar = tk.Canvas(page, height=NAVBAR_HEIGHT, bg=BACKGROUND, highlightthickness=0)
    navbar.pack(side="top", fill="x")
    navbar_line = tk.Frame(page, bg=BORDER, height=1)
    navbar_line.pack(side="top", fill="x")

    # 2) The scroll area fills everything below it; the whole page is drawn on this one Canvas
    # yscrollincrement=1 lets the page move 1 pixel at a time, so the smooth scroll isn't jumpy
    canvas = tk.Canvas(page, bg=BACKGROUND, highlightthickness=0, yscrollincrement=1)
    canvas.pack(side="top", fill="both", expand=True)

    # One dictionary holding everything the drawing and animation functions share
    state = {
        "fonts": {
            "title": tkfont.Font(family="Segoe UI", size=64, weight="bold"),
            "tagline": tkfont.Font(family="Segoe UI", size=22),
            "heading": tkfont.Font(family="Segoe UI", size=26, weight="bold"),
            "logo": tkfont.Font(family="Segoe UI", size=18, weight="bold"),
        },
        "get_started": create_button(canvas, "Get Started →", True, on_get_started, font_size=14),
        "login_button": create_button(navbar, "Log In", False, on_login),
        "signup_button": create_button(navbar, "Sign Up", True, on_signup),
        "sections": {"hero": 0},
        "page_height": 1,
        "angle": 0,
        "orbit_items": [],
    }

    # Redraw whenever a canvas gets its size (when the page opens, and when the window is resized)
    canvas.bind("<Configure>", lambda event: draw_page(canvas, state, event))
    navbar.bind("<Configure>", lambda event: draw_navbar(navbar, canvas, state, event))

    # bind_all catches the wheel anywhere in the window
    canvas.bind_all("<MouseWheel>", lambda event: on_mouse_wheel(canvas, event))

    animate_orbit(canvas, state)
    return page


# Run this block only when welcome.py is started directly (not when imported)
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Consistify - Welcome")
    window.geometry("1100x700")
    window.configure(bg=BACKGROUND)

    build_welcome_page(
        window,
        lambda: print("Get Started clicked"),
        lambda: print("Log In clicked"),
        lambda: print("Sign Up clicked"),
    )
    window.mainloop()
