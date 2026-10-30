# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import tkinter's font tool, so we can measure how wide a piece of text will be
import tkinter.font as tkfont
# Import math for sin and cos, which move the phrases around the title in an oval
import math
# Import random to pick the shades of the decorative heatmap squares
import random
# Import sys to check whether we are running on a Mac (the mouse wheel works differently there)
import sys

# Import the app's shared colors and font
import theme
# Import our reusable widgets (the rounded buttons)
import ui

NAVBAR_HEIGHT = 56
GRID_SIZE = 32       # size of one square of the background grid (pixels)
HERO_TOP = 36        # space between the navbar and the pill badge at the top of the hero

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

# Orbit animation settings: four phrases travel around the title on an oval
ORBIT_PHRASES = ["One day at a time", "Never break the chain", "Small wins daily", "Stay consistent"]
ORBIT_SPEED = 0.008  # how far (in radians) they move each frame; a full lap takes about 24 seconds
ORBIT_DELAY = 30     # milliseconds between frames (about 33 frames a second)
ORBIT_DIM = 0.6      # how much a phrase fades at the very back of the oval (0 = not at all, 1 = invisible)

# Typewriter animation settings
TYPE_HABITS = ["Read 10 pages", "Hit the gym", "Solve 1 LeetCode problem", "Drink 3L water"]
TYPE_DELAY = 90      # milliseconds between typed letters
DELETE_DELAY = 45    # milliseconds between deleted letters (deleting is faster than typing)
TYPE_PAUSE = 1400    # how long a finished habit stays on screen before it is deleted
NEXT_PAUSE = 400     # short pause on the empty line before the next habit starts


# Draw faint vertical and horizontal lines every GRID_SIZE pixels, like graph paper
def draw_grid(canvas, width, height):
    for x in range(0, int(width), GRID_SIZE):
        canvas.create_line(x, 0, x, height, fill=theme.BORDER, tags="grid")
    for y in range(0, int(height), GRID_SIZE):
        canvas.create_line(0, y, width, y, fill=theme.BORDER, tags="grid")


# Draw several pieces of text side by side on a canvas, each in its own color; return the total width
def draw_mixed_text(canvas, x, y, parts, font, anchor="center", tags=""):
    # parts is a list of (text, color) pairs, e.g. [("Build habits that ", theme.ACCENT), ("stick.", theme.TEXT)]
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


# Highlight a navbar link (accent color + its underline showing) or set it back to normal
def paint_link(navbar, link, highlighted):
    if highlighted:
        navbar.itemconfig(link["text"], fill=theme.ACCENT)
        navbar.itemconfig(link["underline"], state="normal")
    else:
        navbar.itemconfig(link["text"], fill=theme.TEXT)
        navbar.itemconfig(link["underline"], state="hidden")


# The mouse moved onto a link: highlight it and show the hand pointer
def on_link_enter(navbar, state, name):
    navbar.config(cursor="hand2")
    paint_link(navbar, state["links"][name], True)


# The mouse left a link: keep it highlighted only if its section is the one in view
def on_link_leave(navbar, state, name):
    navbar.config(cursor="")
    paint_link(navbar, state["links"][name], state["active_section"] == name)


# Draw a navbar link with a hidden 2px underline just below it, and remember both in state["links"]
def draw_link(navbar, state, x, y, text, anchor, name, command):
    item = navbar.create_text(x, y, text=text, fill=theme.TEXT, font=(theme.FONT, 11), anchor=anchor)
    # bbox gives the text's (left, top, right, bottom); the underline goes 2 pixels under the bottom
    left, top, right, bottom = navbar.bbox(item)
    underline = navbar.create_line(left, bottom + 2, right, bottom + 2, fill=theme.ACCENT, width=2, state="hidden")

    for part in (item, underline):
        navbar.tag_bind(part, "<Button-1>", lambda event: command())
        navbar.tag_bind(part, "<Enter>", lambda event: on_link_enter(navbar, state, name))
        navbar.tag_bind(part, "<Leave>", lambda event: on_link_leave(navbar, state, name))

    state["links"][name] = {"text": item, "underline": underline}
    paint_link(navbar, state["links"][name], state["active_section"] == name)


# Called by the canvas whenever the visible part of the page changes; highlights the link of the section in view
def on_page_scroll(navbar, canvas, state, first, last):
    if not navbar.winfo_exists():
        return

    # first is how far down the page the top of the view is, as a fraction (0 = top, 1 = bottom)
    view_top = float(first) * state["page_height"]
    # A section counts as "in view" once its top passes a line one third of the way down the screen
    reading_line = view_top + canvas.winfo_height() / 3

    active = None
    sections = state["sections"]
    if "features" in sections and reading_line >= sections["features"] - SCROLL_MARGIN:
        active = "features"
    elif "about" in sections and reading_line >= sections["about"] - SCROLL_MARGIN:
        active = "about"

    # Only repaint when the section in view actually changes
    if active != state["active_section"]:
        state["active_section"] = active
        for name in state["links"]:
            paint_link(navbar, state["links"][name], name == active)


# Draw the logo: a tiny 2x2 grid of heatmap squares, then "Consistify"
def draw_logo(navbar, state, x, middle_y):
    square = 8
    gap = 2
    top = middle_y - square - gap / 2
    shades = [theme.HEATMAP[2], theme.HEATMAP[4], theme.HEATMAP[1], theme.HEATMAP[3]]
    for i in range(4):
        # i // 2 is the row (0, 0, 1, 1) and i % 2 is the column (0, 1, 0, 1)
        left = x + (i % 2) * (square + gap)
        y1 = top + (i // 2) * (square + gap)
        navbar.create_rectangle(left, y1, left + square, y1 + square, fill=shades[i], outline="", tags="logo")

    text_x = x + 2 * square + gap + 10
    draw_mixed_text(navbar, text_x, middle_y, [("Consist", theme.ACCENT), ("ify", theme.TEXT)], state["fonts"]["logo"], anchor="w", tags="logo")


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


# Blend two "#rrggbb" colors: amount 0 gives color_a, 1 gives color_b, 0.5 gives halfway between
def mix_colors(color_a, color_b, amount):
    mixed = "#"
    # Red, green and blue are each two hex digits: characters 1-2, 3-4 and 5-6
    for start in (1, 3, 5):
        a = int(color_a[start:start + 2], 16)
        b = int(color_b[start:start + 2], 16)
        value = round(a + (b - a) * amount)
        mixed = mixed + format(value, "02x")
    return mixed


# Put every orbiting phrase at its place on the oval for the current angle
def move_orbit(canvas, state):
    orbit = state["orbit"]
    phrases = state["orbit_items"]

    for i in range(len(phrases)):
        # Spread the phrases evenly: with 4 phrases, each is a quarter turn (90 degrees) after the last
        angle = state["angle"] + i * 2 * math.pi / len(phrases)
        x = orbit["x"] + orbit["rx"] * math.cos(angle)
        y = orbit["y"] + orbit["ry"] * math.sin(angle)
        canvas.coords(phrases[i], x, y)

        # sin is -1 at the top of the oval (the "back") and +1 at the bottom (the "front"),
        # so phrases fade towards the background color as they go round the back
        fade = ORBIT_DIM * (1 - math.sin(angle)) / 2
        canvas.itemconfig(phrases[i], fill=mix_colors(state["orbit_colors"][i], theme.BG, fade))


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


# Type one more letter, or delete one, then ask after() to do the next step
def type_step(canvas, state):
    # Stop for good once the page has been closed
    if not canvas.winfo_exists():
        return

    typing = state["typing"]
    habit = TYPE_HABITS[typing["habit"]]

    if not typing["deleting"]:
        typing["letters"] = typing["letters"] + 1
        delay = TYPE_DELAY
        if typing["letters"] == len(habit):
            # The whole habit is shown: wait a while, then start deleting
            typing["deleting"] = True
            delay = TYPE_PAUSE
    else:
        typing["letters"] = typing["letters"] - 1
        delay = DELETE_DELAY
        if typing["letters"] == 0:
            # The line is empty: move on to the next habit (back to the first after the last)
            typing["deleting"] = False
            typing["habit"] = (typing["habit"] + 1) % len(TYPE_HABITS)
            delay = NEXT_PAUSE

    # habit[:letters] is the first `letters` characters; "|" at the end looks like a text cursor
    canvas.itemconfig(state["typed_item"], text=habit[:typing["letters"]] + "|")
    canvas.winfo_toplevel().after(delay, lambda: type_step(canvas, state))


# Draw a rectangle with rounded corners (a "pill" when radius is half its height)
def draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius, fill, outline):
    # Each corner is listed 3 times; smooth=True bends the outline into curves through these points,
    # which rounds the corners while keeping the straight edges straight
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    canvas.create_polygon(points, smooth=True, fill=fill, outline=outline)


# Draw the small rounded badge above the title, centered at x with its top at y; return its bottom y
def draw_badge(canvas, state, x, top):
    font = state["fonts"]["badge"]
    text = "🔥 Your streak starts today"
    width = font.measure(text) + 32
    height = font.metrics("linespace") + 12

    draw_rounded_rectangle(canvas, x - width / 2, top, x + width / 2, top + height, height / 2, theme.CARD, theme.ACCENT)
    canvas.create_text(x, top + height / 2, text=text, fill=theme.ACCENT, font=font)
    return top + height


# Draw "Today's habit: " plus the typewriter text, centered at x, with its middle at y
def draw_typewriter(canvas, state, x, y):
    font = state["fonts"]["typewriter"]
    prefix = "Today's habit: "

    # Center the line as if the longest habit were showing, so the start never moves while typing
    longest = max(font.measure(habit) for habit in TYPE_HABITS)
    left = x - (font.measure(prefix) + longest) / 2

    canvas.create_text(left, y, text=prefix, fill=theme.MUTED, font=font, anchor="w")
    typing = state["typing"]
    habit = TYPE_HABITS[typing["habit"]]
    state["typed_item"] = canvas.create_text(
        left + font.measure(prefix), y, text=habit[:typing["letters"]] + "|", fill=theme.ACCENT, font=font, anchor="w"
    )


# Work out the oval for the phrases, so that no phrase can ever touch the title
def plan_orbit(state, title_width, title_height, page_width):
    phrase_font = state["fonts"]["phrase"]
    widest = max(phrase_font.measure(phrase) for phrase in ORBIT_PHRASES)
    phrase_height = phrase_font.metrics("linespace")

    # A phrase's middle must stay outside this box: the title, grown by half a phrase on every side
    box_x = title_width / 2 + widest / 2 + 10
    box_y = title_height / 2 + phrase_height / 2 + 6

    # Make the oval wider than the box, but not so wide that phrases go off the window
    rx = min(box_x * 1.3, page_width / 2 - widest / 2 - 20)
    rx = max(rx, box_x * 1.05)
    # Then choose the height so the box's corners land exactly on the oval: (box_x/rx)² + (box_y/ry)² = 1.
    # With the corners on the oval, the whole box is inside it, so the phrases always go round it
    ry = box_y / math.sqrt(1 - (box_x / rx) ** 2)
    return rx, ry, phrase_height


# Draw the hero from the top down: badge, orbit + title, tagline, typewriter, button; return its bottom y
def draw_hero(canvas, state, width):
    fonts = state["fonts"]
    middle_x = width / 2

    badge_bottom = draw_badge(canvas, state, middle_x, HERO_TOP)

    title_width = fonts["title"].measure("Consistify")
    title_height = fonts["title"].metrics("linespace")
    rx, ry, phrase_height = plan_orbit(state, title_width, title_height, width)

    # Put the title just low enough that a phrase at the very top of the oval clears the badge
    title_y = badge_bottom + 12 + phrase_height / 2 + ry
    draw_mixed_text(canvas, middle_x, title_y, [("Consist", theme.ACCENT), ("ify", theme.TEXT)], fonts["title"])

    # The tagline starts just below the lowest point a phrase can reach
    tagline_height = fonts["tagline"].metrics("linespace")
    tagline_y = title_y + ry + phrase_height / 2 + 12 + tagline_height / 2
    draw_mixed_text(canvas, middle_x, tagline_y, [("Build habits that ", theme.ACCENT), ("stick.", theme.TEXT)], fonts["tagline"])

    typewriter_height = fonts["typewriter"].metrics("linespace")
    typewriter_y = tagline_y + tagline_height / 2 + 10 + typewriter_height / 2
    draw_typewriter(canvas, state, middle_x, typewriter_y)

    button = state["get_started"]
    button_y = typewriter_y + typewriter_height / 2 + 26 + button.winfo_reqheight() / 2
    canvas.create_window(middle_x, button_y, window=button)

    # Create the four phrases (alternating the two theme colors), then put them in place
    state["orbit"] = {"x": middle_x, "y": title_y, "rx": rx, "ry": ry}
    state["orbit_items"] = []
    state["orbit_colors"] = []
    for i in range(len(ORBIT_PHRASES)):
        if i % 2 == 0:
            color = theme.ACCENT
        else:
            color = theme.TEXT
        phrase = canvas.create_text(0, 0, text=ORBIT_PHRASES[i], fill=color, font=fonts["phrase"])
        state["orbit_items"].append(phrase)
        state["orbit_colors"].append(color)
    move_orbit(canvas, state)

    return button_y + button.winfo_reqheight() / 2 + 50


# Draw the About section starting at y = top; return the y where it ends
def draw_about(canvas, state, top, width):
    heading_font = state["fonts"]["heading"]
    y = top + 60
    state["sections"]["about"] = y

    heading_height = heading_font.metrics("linespace")
    draw_mixed_text(canvas, width / 2, y + heading_height / 2, [("Why ", theme.ACCENT), ("habits", theme.TEXT), (" matter", theme.ACCENT)], heading_font)
    y = y + heading_height + 20

    lines = [
        "Consistify is a simple desktop habit tracker: tick off your habits each day and watch them add up.",
        "Small actions repeated every day beat big bursts of motivation.",
        "Seeing your streak grow makes it easier to keep going tomorrow.",
    ]
    for line in lines:
        # width=900 wraps a long line onto a second line instead of running off the window
        item = canvas.create_text(width / 2, y, text=line, fill=theme.MUTED, font=(theme.FONT, 13), width=900, justify="center", anchor="n")
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
            canvas.create_rectangle(x1, y1, x1 + DECOR_SQUARE, y1 + DECOR_SQUARE, fill=theme.HEATMAP[level], outline="")


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
        heading_item = canvas.create_text(x, top + 18, text=heading, fill=theme.ACCENT, font=(theme.FONT, 13, "bold"), anchor="nw")
        heading_bottom = canvas.bbox(heading_item)[3]
        text_item = canvas.create_text(x, heading_bottom + 6, text=text, fill=theme.MUTED, font=(theme.FONT, 10), width=card_width - 40, anchor="nw")
        lowest = max(lowest, canvas.bbox(text_item)[3])

    # Then draw all three card boxes the same height, tall enough for the tallest text
    bottom = lowest + 18
    for i in range(len(cards)):
        x = left + i * (card_width + card_gap)
        canvas.create_rectangle(x, top, x + card_width, bottom, fill=theme.CARD, outline=theme.BORDER, tags="card")

    return bottom


# Draw the Features section starting at y = top; return the y where the page ends
def draw_features(canvas, state, top, width):
    heading_font = state["fonts"]["heading"]
    y = top + 60
    state["sections"]["features"] = y

    heading_height = heading_font.metrics("linespace")
    draw_mixed_text(canvas, width / 2, y + heading_height / 2, [("Everything you need to ", theme.ACCENT), ("stay consistent", theme.TEXT)], heading_font)
    y = y + heading_height + 30

    decor_width = DECOR_COLUMNS * (DECOR_SQUARE + DECOR_GAP) - DECOR_GAP
    decor_height = DECOR_ROWS * (DECOR_SQUARE + DECOR_GAP) - DECOR_GAP
    draw_decorative_heatmap(canvas, width / 2 - decor_width / 2, y)
    y = y + decor_height + 30

    y = draw_feature_cards(canvas, y, width)

    # A thin line, then the footer text
    y = y + 70
    canvas.create_line(60, y, width - 60, y, fill=theme.BORDER)
    footer = canvas.create_text(
        width / 2, y + 20, text="Made by Krishiv Sharma, Keerthy Sarayuu & Shaan Vyas",
        fill=theme.MUTED, font=(theme.FONT, 9), anchor="n",
    )
    return canvas.bbox(footer)[3] + 20


# Clear the scroll canvas and draw the whole page again at its current size
def draw_page(canvas, state, event):
    canvas.delete("all")
    width = event.width

    # The hero is only as tall as its contents, and the About section starts right after it
    hero_bottom = draw_hero(canvas, state, width)
    y = draw_about(canvas, state, hero_bottom, width)
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
    draw_logo(navbar, state, 30, middle_y)
    navbar.tag_bind("logo", "<Button-1>", lambda event: scroll_to_section(canvas, state, "hero"))
    navbar.tag_bind("logo", "<Enter>", lambda event: navbar.config(cursor="hand2"))
    navbar.tag_bind("logo", "<Leave>", lambda event: navbar.config(cursor=""))

    # "About" ends just left of the middle and "Features" starts just right of it
    draw_link(navbar, state, width / 2 - 16, middle_y, "About", "e", "about", lambda: scroll_to_section(canvas, state, "about"))
    draw_link(navbar, state, width / 2 + 16, middle_y, "Features", "w", "features", lambda: scroll_to_section(canvas, state, "features"))

    signup = state["signup_button"]
    navbar.create_window(width - 30, middle_y, window=signup, anchor="e")
    navbar.create_window(width - 30 - signup.winfo_reqwidth() - 10, middle_y, window=state["login_button"], anchor="e")


# Build the whole landing page inside the parent and return the page frame
def build_welcome_page(parent, on_get_started, on_login, on_signup):
    page = tk.Frame(parent, bg=theme.BG)
    page.pack(fill="both", expand=True)

    # 1) The navbar is packed first, so it always keeps the top strip of the page
    navbar = tk.Canvas(page, height=NAVBAR_HEIGHT, bg=theme.CARD, highlightthickness=0)
    navbar.pack(side="top", fill="x")
    navbar_line = tk.Frame(page, bg=theme.BORDER, height=1)
    navbar_line.pack(side="top", fill="x")

    # 2) The scroll area fills everything below it; the whole page is drawn on this one Canvas
    # yscrollincrement=1 lets the page move 1 pixel at a time, so the smooth scroll isn't jumpy
    canvas = tk.Canvas(page, bg=theme.BG, highlightthickness=0, yscrollincrement=1)
    canvas.pack(side="top", fill="both", expand=True)

    # One dictionary holding everything the drawing and animation functions share
    state = {
        "fonts": {
            "title": tkfont.Font(family=theme.FONT, size=56, weight="bold"),
            "tagline": tkfont.Font(family=theme.FONT, size=22),
            "heading": tkfont.Font(family=theme.FONT, size=26, weight="bold"),
            "logo": tkfont.Font(family=theme.FONT, size=18, weight="bold"),
            "phrase": tkfont.Font(family=theme.FONT, size=11, slant="italic"),
            "badge": tkfont.Font(family=theme.FONT, size=10),
            "typewriter": tkfont.Font(family=theme.FONT, size=14),
        },
        "get_started": ui.rounded_button(canvas, "Get Started →", on_get_started, "filled", width=230, height=54, radius=12, font_size=14),
        # No width/height given, so these two size themselves to their text
        "login_button": ui.rounded_button(navbar, "Log in", on_login, "ghost", radius=8, font_size=10),
        "signup_button": ui.rounded_button(navbar, "Sign up", on_signup, "filled", radius=8, font_size=10),
        # The navbar links, and which section is in view right now (None while the hero is showing)
        "links": {},
        "active_section": None,
        "sections": {"hero": 0},
        "page_height": 1,
        "angle": 0,
        "orbit_items": [],
        # Which habit the typewriter is on, how many of its letters are showing, and whether it is deleting
        "typing": {"habit": 0, "letters": 0, "deleting": False},
    }

    # Redraw whenever a canvas gets its size (when the page opens, and when the window is resized)
    canvas.bind("<Configure>", lambda event: draw_page(canvas, state, event))
    navbar.bind("<Configure>", lambda event: draw_navbar(navbar, canvas, state, event))

    # bind_all catches the wheel anywhere in the window
    canvas.bind_all("<MouseWheel>", lambda event: on_mouse_wheel(canvas, event))

    # The canvas calls yscrollcommand every time its view moves: wheel, smooth scroll or resize
    canvas.configure(yscrollcommand=lambda first, last: on_page_scroll(navbar, canvas, state, first, last))

    animate_orbit(canvas, state)
    # Start typing a little later, once the page has been drawn and "typed_item" exists
    canvas.winfo_toplevel().after(500, lambda: type_step(canvas, state))
    return page


# Run this block only when welcome.py is started directly (not when imported)
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Consistify - Welcome")
    window.geometry("1100x700")
    window.configure(bg=theme.BG)

    build_welcome_page(
        window,
        lambda: print("Get Started clicked"),
        lambda: print("Log In clicked"),
        lambda: print("Sign Up clicked"),
    )
    window.mainloop()
