# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import tkinter's font tool, so we can measure "Consist" and put "ify" right after it
import tkinter.font as tkfont
# Import random to pick each square's final shade
import random
# Import time to measure how many milliseconds the animation has been running
import time

# Import our own files: the database (to create the tables), the shared colors and the blend helper
import database
import theme
import ui

# The grid of squares
GRID_ROWS = 7
GRID_COLUMNS = 12
SQUARE = 14            # size of one square (pixels)
SQUARE_GAP = 4         # space between two squares
SQUARE_RADIUS = 4      # how round the corners of a square are
# Each square's final shade is picked from this list; more 3s and 4s means mostly strong shades
FINAL_SHADES = [1, 2, 3, 3, 4, 4, 4]

# Timings (milliseconds)
FRAME_DELAY = 16       # time between two frames (about 60 frames a second)
WAVE_TIME = 800        # phase 1: the whole grid fills in
SHADE_TIME = 60        # how long a square stays on each shade before stepping up to the next one
DIAGONALS = GRID_ROWS + GRID_COLUMNS - 2   # the last diagonal's number (row 6 + column 11 = 17)
# How much later each diagonal starts than the one before it, so the last square finishes right at WAVE_TIME
WAVE_DELAY = (WAVE_TIME - 4 * SHADE_TIME) / DIAGONALS
TITLE_FADE = 350       # phase 2: "Consistify" fades in over this long...
TAGLINE_START = 250    # ...the tagline starts fading this long after the title...
TAGLINE_FADE = 350     # ...and takes this long, so phase 2 lasts 600 ms
TEXT_TIME = 600        # phase 2's length
HOLD_TIME = 300        # phase 3: everything stays on screen this long before on_done()
LOAD_TIME = WAVE_TIME + TEXT_TIME   # the loading bar fills during phases 1 and 2

# Layout (pixels, measured down from the top of the grid)
TITLE_SIZE = 34
TAGLINE_SIZE = 12
TITLE_GAP = 20         # empty space between the bottom of the grid and the top of the title
TAGLINE_GAP = 2        # empty space between the title and the tagline
BAR_GAP = 28           # empty space between the tagline and the loading bar
BAR_WIDTH = 220
BAR_HEIGHT = 4


# Return how far (0 to 1) a fade that begins at `start` and lasts `length` has got after `elapsed` ms
def fade_progress(elapsed, start, length):
    return max(0, min(1, (elapsed - start) / length))


# Return which shade (0-4) a square on diagonal `diagonal` shows `elapsed` ms after the start
def square_shade(elapsed, diagonal, final_shade):
    # Squares further along the diagonal wave start later
    started = elapsed - diagonal * WAVE_DELAY
    if started < 0:
        return 0
    # One shade up every SHADE_TIME ms, but never past the square's own final shade
    return min(final_shade, 1 + int(started // SHADE_TIME))


# Draw the grid, the title, the tagline and the loading bar around (0, 0); return the dictionary of items
def draw_splash(canvas):
    grid_width = GRID_COLUMNS * (SQUARE + SQUARE_GAP) - SQUARE_GAP
    grid_height = GRID_ROWS * (SQUARE + SQUARE_GAP) - SQUARE_GAP
    title_font = tkfont.Font(family=theme.FONT, size=TITLE_SIZE, weight="bold")
    tagline_font = tkfont.Font(family=theme.FONT, size=TAGLINE_SIZE)
    # A text's real height ("linespace") changes with the screen's scaling, so the gaps are measured from it
    title_height = title_font.metrics("linespace")
    tagline_height = tagline_font.metrics("linespace")
    title_y = grid_height + TITLE_GAP + title_height / 2
    tagline_y = title_y + title_height / 2 + TAGLINE_GAP + tagline_height / 2
    bar_y = tagline_y + tagline_height / 2 + BAR_GAP
    # Everything is drawn with x = 0 in the middle and moved up by half its height, so (0, 0) is its center
    top = -bar_y / 2
    left = -grid_width / 2

    squares = []
    for row in range(GRID_ROWS):
        for column in range(GRID_COLUMNS):
            x1 = left + column * (SQUARE + SQUARE_GAP)
            y1 = top + row * (SQUARE + SQUARE_GAP)
            points = ui.rounded_rectangle_points(x1, y1, x1 + SQUARE, y1 + SQUARE, SQUARE_RADIUS)
            item = canvas.create_polygon(points, smooth=True, fill=theme.HEATMAP[0], outline="")
            # row + column is the same for every square on one diagonal, so it numbers the diagonals 0 to 17
            squares.append({"item": item, "diagonal": row + column, "final": random.choice(FINAL_SHADES), "shown": 0})

    # "Consist" and "ify" are two texts in two colors, so measure both to center them as one word
    first_width = title_font.measure("Consist")
    title_left = -(first_width + title_font.measure("ify")) / 2
    consist = canvas.create_text(title_left, top + title_y, text="Consist", anchor="w", font=title_font, fill=theme.BG)
    ify = canvas.create_text(title_left + first_width, top + title_y, text="ify", anchor="w", font=title_font, fill=theme.BG)
    tagline = canvas.create_text(0, top + tagline_y, text="Build habits that stick.", font=tagline_font, fill=theme.BG)

    # The bar is a thick line with round ends: the grey track, and the accent fill on top (hidden while at 0%)
    bar_left = -BAR_WIDTH / 2
    track = canvas.create_line(bar_left, top + bar_y, bar_left + BAR_WIDTH, top + bar_y, width=BAR_HEIGHT, fill=theme.BORDER, capstyle="round")
    fill = canvas.create_line(bar_left, top + bar_y, bar_left, top + bar_y, width=BAR_HEIGHT, fill=theme.ACCENT, capstyle="round", state="hidden")

    # Each text with the color it fades towards
    texts = [(consist, theme.ACCENT), (ify, theme.TEXT)]
    # The fonts are kept in the dictionary too: a Font object that Python throws away stops working on the canvas
    return {"squares": squares, "texts": texts, "tagline": tagline, "track": track, "fill": fill, "fonts": (title_font, tagline_font)}


# Keep everything in the middle of the canvas: move it by however far the middle moved
def center_splash(canvas, state, event):
    old_x, old_y = state["offset"]
    canvas.move("all", event.width / 2 - old_x, event.height / 2 - old_y)
    state["offset"] = (event.width / 2, event.height / 2)


# Set the loading bar's fill to `fraction` (0 to 1) of the track
def set_bar(canvas, items, fraction):
    x1, y, x2, _ = canvas.coords(items["track"])
    if fraction <= 0:
        canvas.itemconfigure(items["fill"], state="hidden")
        return
    canvas.itemconfigure(items["fill"], state="normal")
    canvas.coords(items["fill"], x1, y, x1 + (x2 - x1) * fraction, y)


# Draw one frame for the current time, then ask after() for the next one (until done or the page is gone)
def splash_frame(canvas, state):
    # Stop for good if the splash was skipped or the page was closed
    if state["done"] or not canvas.winfo_exists():
        return

    # The real "loading": make sure the database tables exist (once, on the first frame)
    if not state["loaded"]:
        database.create_tables()
        state["loaded"] = True

    elapsed = (time.perf_counter() - state["start"]) * 1000
    items = state["items"]

    # Phase 1: every square shows the shade its place in the wave has reached
    for square in items["squares"]:
        shade = square_shade(elapsed, square["diagonal"], square["final"])
        # Only recolor a square when its shade really changed
        if shade != square["shown"]:
            canvas.itemconfigure(square["item"], fill=theme.HEATMAP[shade])
            square["shown"] = shade

    # Phase 2: the title, then the tagline, blend from the background color to their real colors
    title_t = fade_progress(elapsed, WAVE_TIME, TITLE_FADE)
    for item, color in items["texts"]:
        canvas.itemconfigure(item, fill=ui.blend(theme.BG, color, title_t))
    tagline_t = fade_progress(elapsed, WAVE_TIME + TAGLINE_START, TAGLINE_FADE)
    canvas.itemconfigure(items["tagline"], fill=ui.blend(theme.BG, theme.MUTED, tagline_t))

    # The loading bar follows the clock for phases 1 and 2, then stays full
    set_bar(canvas, items, min(1, elapsed / LOAD_TIME))

    # Phase 3: once the hold is over, finish; otherwise draw the next frame soon
    if elapsed >= LOAD_TIME + HOLD_TIME:
        finish(state)
    else:
        canvas.winfo_toplevel().after(FRAME_DELAY, lambda: splash_frame(canvas, state))


# Call on_done(), but only the very first time (the end of the animation, a click or a key can all get here)
def finish(state):
    if state["done"]:
        return
    state["done"] = True
    state["on_done"]()


# Build the splash page inside the parent, start the animation, and call on_done() when it ends or is skipped
def build_splash_page(parent, on_done):
    canvas = tk.Canvas(parent, bg=theme.BG, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    state = {
        "items": draw_splash(canvas),
        "offset": (0, 0),
        "start": time.perf_counter(),
        "loaded": False,
        "done": False,
        "on_done": on_done,
    }

    canvas.bind("<Configure>", lambda event: center_splash(canvas, state, event))
    # Clicking anywhere or pressing any key skips the rest (the canvas needs the keyboard focus to get keys)
    canvas.bind("<Button-1>", lambda event: finish(state))
    canvas.bind("<Key>", lambda event: finish(state))
    canvas.focus_set()

    canvas.winfo_toplevel().after(FRAME_DELAY, lambda: splash_frame(canvas, state))
    return canvas


# Print that the splash finished and close the test window (used only by the test window below)
def test_done(window):
    print("Splash done")
    window.destroy()


# Run this block only when splash.py is started directly (not when imported)
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Consistify - Splash")
    window.geometry("1100x700")
    window.configure(bg=theme.BG)

    build_splash_page(window, lambda: test_done(window))
    window.mainloop()
