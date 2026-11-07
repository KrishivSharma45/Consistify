# Reusable widgets shared by several pages (plain functions, no classes)

# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import tkinter's font tool, so a button can measure its text and size itself
import tkinter.font as tkfont
# Import math (cos and sin) and random, to send each confetti piece off in its own direction
import math
import random
# Import sys to check whether we are running on a Mac (the mouse wheel works differently there)
import sys

# Import the app's shared colors and font
import theme

CONFETTI_PIECES = 120     # how many pieces burst out
CONFETTI_GRAVITY = 0.35   # how much faster every piece falls each frame (pixels per frame, added each frame)
CONFETTI_DRAG = 0.99      # each frame the sideways speed keeps 99% of itself, like air slowing it down
CONFETTI_FRAME = 16       # milliseconds between frames (about 60 frames a second)
CONFETTI_TIME = 2500      # milliseconds before the celebration closes by itself

CARD_PADDING = 20         # space inside every card
PAGE_MARGIN = 40          # space between a scroll page's cards and the left/right edges
PAGE_GAP = 16             # space between two rows of cards on a scroll page
PAGE_WHEEL_PIXELS = 40    # how far one mouse-wheel notch scrolls a scroll page


# Create a card (CARD background, 1px BORDER outline, 20px padding) with an optional bold title and muted
# subtitle; return it (the caller packs or grids it). bg/border/thickness change the look (e.g. for badges)
def create_card(parent, title=None, subtitle=None, bg=theme.CARD, border=theme.BORDER, thickness=1):
    card = tk.Frame(parent, bg=bg, highlightthickness=thickness, highlightbackground=border, padx=CARD_PADDING, pady=CARD_PADDING)
    if title is not None:
        title_label = tk.Label(card, text=title, font=(theme.FONT, 12, "bold"), fg=theme.TEXT, bg=bg)
        title_label.pack(anchor="w")
    if subtitle is not None:
        subtitle_label = tk.Label(card, text=subtitle, font=(theme.FONT, 9), fg=theme.MUTED, bg=bg)
        subtitle_label.pack(anchor="w")
    if title is not None or subtitle is not None:
        # A little space between the heading and whatever the card shows
        tk.Frame(card, bg=bg, height=12).pack()
    return card


# Run on_step(fraction) with fraction going smoothly from 0 to 1 over `steps` frames, then stop.
# It stops early, safely, if `widget` is destroyed (e.g. the page was closed) while it runs
def animate(widget, on_step, steps=24, delay=16, step=1):
    if not widget.winfo_exists():
        return
    # "Ease out": quick at first, gentle at the end
    on_step(1 - (1 - step / steps) ** 3)
    if step < steps:
        widget.winfo_toplevel().after(delay, lambda: animate(widget, on_step, steps, delay, step + 1))


# Draw a thick progress ring on a canvas: a full grey track, and an arc for `fraction` of it, starting at the top
def draw_ring(canvas, middle_x, middle_y, radius, thickness, fraction, color=theme.ACCENT, track=theme.BORDER, tag="ring"):
    canvas.delete(tag)
    box = (middle_x - radius, middle_y - radius, middle_x + radius, middle_y + radius)
    # The track: a circle drawn only as a thick outline
    canvas.create_oval(*box, outline=track, width=thickness, tags=tag)
    if fraction > 0:
        # style="arc" draws just the curved line; start=90 is 12 o'clock and a negative extent goes clockwise.
        # 359.9 instead of 360, because Tk draws nothing for an arc of exactly 360 degrees
        canvas.create_arc(*box, start=90, extent=-359.9 * min(1, fraction), style="arc", outline=color, width=thickness, tags=tag)


# Draw a rounded pill with text in it (e.g. "🔥 4") on its own small canvas and return the canvas
def create_pill(parent, text, text_color, fill, font_size=9):
    font = tkfont.Font(family=theme.FONT, size=font_size, weight="bold")
    width = font.measure(text) + 18
    height = font.metrics("linespace") + 6
    pill = tk.Canvas(parent, width=width, height=height, bg=parent.cget("bg"), highlightthickness=0)
    # radius = half the height makes both ends fully round
    pill.create_polygon(rounded_rectangle_points(0, 0, width, height, height / 2), smooth=True, fill=fill, outline="")
    pill.create_text(width / 2, height / 2, text=text, fill=text_color, font=font)
    return pill


# Create a small stat card: an icon tile, then a big number and a label beside it; return (card, number label)
def create_stat_tile(parent, icon, label_text):
    card = create_card(parent)
    # Top row: the icon and the big number side by side
    top = tk.Frame(card, bg=theme.CARD)
    top.pack(anchor="w")
    icon_tile(top, icon, size=36).pack(side="left", padx=(0, 10))
    number = tk.Label(top, text="0", font=(theme.FONT, 18, "bold"), fg=theme.TEXT, bg=theme.CARD)
    number.pack(side="left")
    # The label goes underneath, so it can use the card's full width and never gets cut off
    label = tk.Label(card, text=label_text, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD)
    label.pack(anchor="w", pady=(8, 0))
    return card, number


# Put the page's rows one under another (with gaps) on its canvas, draw the grid behind them and update the scroll size
def layout_scroll_page(page):
    canvas = page["canvas"]
    if not canvas.winfo_exists():
        return
    width = canvas.winfo_width()
    y = PAGE_GAP + 8
    for frame, item in page["rows"]:
        canvas.coords(item, PAGE_MARGIN, y)
        canvas.itemconfigure(item, width=max(1, width - 2 * PAGE_MARGIN))
        y = y + frame.winfo_reqheight() + PAGE_GAP
    # The grid is drawn on this canvas (so it scrolls with the page) and shows in the gaps between rows
    canvas.delete("grid")
    draw_grid_lines(canvas, width, max(y, canvas.winfo_height()))
    canvas.tag_lower("grid")
    canvas.configure(scrollregion=(0, 0, width, y))


# Scroll a scroll page with the mouse wheel (Windows sends steps of 120 per notch, a Mac small numbers)
def scroll_page_wheel(canvas, event):
    if not canvas.winfo_exists():
        return
    top, bottom = canvas.yview()
    # Nothing to scroll if the whole page already fits
    if top <= 0 and bottom >= 1:
        return
    if sys.platform == "darwin":
        notches = -event.delta / 10
    else:
        notches = -event.delta / 120
    canvas.yview_scroll(int(notches * PAGE_WHEEL_PIXELS), "units")


# Create a page that scrolls: a canvas where each row of cards is its own window, so the grid shows between rows
def create_scroll_page(parent):
    canvas = tk.Canvas(parent, bg=theme.BG, highlightthickness=0, yscrollincrement=1)
    canvas.pack(fill="both", expand=True)
    page = {"canvas": canvas, "rows": []}
    canvas.bind("<Configure>", lambda event: layout_scroll_page(page))
    canvas.bind_all("<MouseWheel>", lambda event: scroll_page_wheel(canvas, event))
    return page


# Add a new (empty) row to a scroll page and return its frame; put the row's cards inside it
def add_page_row(page):
    canvas = page["canvas"]
    row = tk.Frame(canvas, bg=theme.BG)
    item = canvas.create_window(0, 0, window=row, anchor="nw")
    page["rows"].append((row, item))
    # Whenever a row changes size (cards appear, text wraps), lay the whole page out again
    row.bind("<Configure>", lambda event: layout_scroll_page(page))
    return row


# Return the corner points of a rounded rectangle; with smooth=True, tkinter bends the outline through them
def rounded_rectangle_points(x1, y1, x2, y2, radius):
    # Each corner is one point, with a point `radius` away from it along each edge on either side.
    # smooth=True bends the outline into a curve around each corner point, while the points along
    # each edge are in a straight line, so the edges stay straight and only the corners get rounded
    return [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]


# Redraw the button's shape and center its text whenever the canvas changes size (e.g. full-width buttons)
def resize_button(canvas, radius, event):
    # Keep 1 pixel free on every side so the outline is never cut off
    points = rounded_rectangle_points(1, 1, event.width - 2, event.height - 2, radius)
    canvas.coords("shape", *points)
    canvas.coords("label", event.width / 2, event.height / 2)


# Recolor the button: the shape's fill and outline, and the text
def paint_button(canvas, colors):
    fill, outline, text_color = colors
    canvas.itemconfig("shape", fill=fill, outline=outline)
    canvas.itemconfig("label", fill=text_color)


# Draw a rounded button on its own small Canvas and return that Canvas (pack or place it like any widget).
# Leave width or height as None and the button sizes itself to fit its text
def rounded_button(parent, text, command, style="filled", width=None, height=None, radius=10, font_size=11):
    font = tkfont.Font(family=theme.FONT, size=font_size, weight="bold")
    if width is None:
        width = font.measure(text) + 36
    if height is None:
        height = font.metrics("linespace") + 14

    # The Canvas takes the parent's background, so outside the rounded corners it looks transparent
    canvas = tk.Canvas(parent, width=width, height=height, bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")

    # Each style is (fill, outline, text color), for normally and for under the mouse
    if style == "filled":
        normal = (theme.ACCENT, theme.ACCENT, theme.BG)
        hover = (theme.ACCENT_HOVER, theme.ACCENT_HOVER, theme.BG)
    elif style == "danger":
        # A ghost button in the error color, which fills in red under the mouse (for destructive actions)
        normal = ("", theme.ERROR, theme.ERROR)
        hover = (theme.ERROR, theme.ERROR, theme.BG)
    else:
        # "ghost": an empty fill ("") lets the background show through, leaving only the outline
        normal = ("", theme.TEXT, theme.TEXT)
        hover = ("", theme.ACCENT, theme.ACCENT)

    points = rounded_rectangle_points(1, 1, width - 2, height - 2, radius)
    canvas.create_polygon(points, smooth=True, width=1, tags="shape")
    canvas.create_text(width / 2, height / 2, text=text, font=font, tags="label")
    paint_button(canvas, normal)

    # <Enter> fires when the mouse moves onto the canvas, <Leave> when it moves off
    canvas.bind("<Enter>", lambda event: paint_button(canvas, hover))
    canvas.bind("<Leave>", lambda event: paint_button(canvas, normal))
    canvas.bind("<Button-1>", lambda event: command())
    canvas.bind("<Configure>", lambda event: resize_button(canvas, radius, event))
    return canvas


# Change the text on a rounded button made by rounded_button
def set_button_text(button, text):
    button.itemconfig("label", text=text)


# Draw an emoji inside a small rounded square (an "icon tile") and return its Canvas
def icon_tile(parent, emoji, size=36, radius=8):
    canvas = tk.Canvas(parent, width=size, height=size, bg=parent.cget("bg"), highlightthickness=0)
    points = rounded_rectangle_points(1, 1, size - 2, size - 2, radius)
    canvas.create_polygon(points, smooth=True, fill=theme.BG, outline=theme.BORDER)
    # fill gives the emoji its color (without it, Tk draws it black, which is invisible on a dark tile)
    canvas.create_text(size / 2, size / 2, text=emoji, fill=theme.ACCENT, font=(theme.FONT, int(size / 3)))
    return canvas


# Draw the grid lines on a canvas: a vertical line every GRID_SIZE pixels across, a horizontal one every GRID_SIZE down
def draw_grid_lines(canvas, width, height, tags="grid"):
    for x in range(0, int(width) + 1, theme.GRID_SIZE):
        canvas.create_line(x, 0, x, height, fill=theme.GRID, width=1, tags=tags)
    for y in range(0, int(height) + 1, theme.GRID_SIZE):
        canvas.create_line(0, y, width, y, fill=theme.GRID, width=1, tags=tags)


# Wipe the old lines and draw them again at the canvas's new size
def redraw_grid(canvas, event):
    canvas.delete("grid")
    draw_grid_lines(canvas, event.width, event.height)


# Put a grid-paper background behind everything in the parent and return its canvas
def draw_grid_background(parent):
    canvas = tk.Canvas(parent, bg=theme.BG, highlightthickness=0)
    # relwidth/relheight=1: the canvas is always exactly as big as the parent, even after a resize
    canvas.place(x=0, y=0, relwidth=1, relheight=1)
    # Send it below every other widget in the parent. For a Canvas, canvas.lower() lowers a drawing
    # *inside* the canvas, so we call the general widget version, tk.Misc.lower, on it instead
    tk.Misc.lower(canvas)
    # The canvas follows the parent's size, so when the parent is resized the canvas gets a <Configure> too
    canvas.bind("<Configure>", lambda event: redraw_grid(canvas, event))
    return canvas


# True if `widget` is `ancestor` itself or sits somewhere inside it
def is_inside(widget, ancestor):
    while widget is not None:
        if widget == ancestor:
            return True
        widget = widget.master
    return False


# Change a card's border color and thickness (a thicker border makes the card look slightly bigger)
def set_border(card, color, thickness):
    card.config(highlightbackground=color, highlightthickness=thickness)


# Give a card a border that changes color and grows by 1px while the mouse is over it
def add_hover_border(card, normal_color, hover_color, normal_thickness):
    set_border(card, normal_color, normal_thickness)
    card.bind("<Enter>", lambda event: set_border(card, hover_color, normal_thickness + 1))
    # Tk also sends <Leave> when the mouse moves onto a label inside the card, so first check
    # where the pointer really is, and only go back to normal if it has left the card completely
    card.bind("<Leave>", lambda event: leave_card(card, normal_color, normal_thickness))


# The mouse left a card (or moved onto something inside it): reset the border only if it really left
def leave_card(card, normal_color, normal_thickness):
    x, y = card.winfo_pointerxy()
    if not is_inside(card.winfo_containing(x, y), card):
        set_border(card, normal_color, normal_thickness)


# Move every confetti piece one frame, remove pieces that left the screen, then ask after() for the next frame
def animate_confetti(canvas, pieces):
    # Stop if the celebration was closed (by the timer or a click) or the page was closed
    if not canvas.winfo_exists():
        return

    width = canvas.winfo_width()
    height = canvas.winfo_height()
    # Loop over a copy (pieces[:]) because pieces are removed from the real list inside the loop
    for piece in pieces[:]:
        # Gravity: every frame the downward speed grows a little, so pieces slow on the way up and speed up falling
        piece["vy"] = piece["vy"] + CONFETTI_GRAVITY
        piece["vx"] = piece["vx"] * CONFETTI_DRAG
        canvas.move(piece["item"], piece["vx"], piece["vy"])

        left, top, right, bottom = canvas.coords(piece["item"])
        if top > height or right < 0 or left > width:
            canvas.delete(piece["item"])
            pieces.remove(piece)

    canvas.winfo_toplevel().after(CONFETTI_FRAME, lambda: animate_confetti(canvas, pieces))


# Close the celebration: destroying the canvas also stops its animation
def close_confetti(canvas):
    if canvas.winfo_exists():
        canvas.destroy()


# Cover the parent with a celebration: a burst of falling confetti, a big message and a smaller subtitle; return the canvas
def show_confetti(parent, message, subtitle="See you tomorrow 🔥"):
    # A canvas laid over the whole parent: relwidth/relheight=1 make it exactly as big as the parent
    canvas = tk.Canvas(parent, bg=theme.BG, highlightthickness=0, cursor="hand2")
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
    # Put it above every other widget in the parent. A Canvas's own tkraise()/lift() raise items *inside*
    # the canvas, so we call the general widget version, tk.Misc.tkraise, on it instead
    tk.Misc.tkraise(canvas)
    parent.update_idletasks()
    width = parent.winfo_width()
    height = parent.winfo_height()
    middle_x = width / 2
    middle_y = height / 2

    colors = [theme.ACCENT, theme.ACCENT_HOVER, theme.SUCCESS, theme.TEXT] + theme.HEATMAP
    pieces = []
    for i in range(CONFETTI_PIECES):
        size = random.randint(4, 9)
        color = random.choice(colors)
        # Half the pieces are little rectangles, half are little circles
        if random.random() < 0.5:
            item = canvas.create_rectangle(middle_x, middle_y, middle_x + size, middle_y + size * 0.6, fill=color, outline="")
        else:
            item = canvas.create_oval(middle_x, middle_y, middle_x + size, middle_y + size, fill=color, outline="")

        # A random direction (angle) and speed; cos and sin split that speed into sideways and up/down parts
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 11)
        # The extra -4 gives every piece a kick upwards, so the burst rises before gravity pulls it down
        pieces.append({"item": item, "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed - 4})

    # The text is created after the confetti, so it is drawn on top of it
    canvas.create_text(middle_x, middle_y, text=message, fill=theme.TEXT, font=(theme.FONT, 28, "bold"))
    canvas.create_text(middle_x, middle_y + 46, text=subtitle, fill=theme.MUTED, font=(theme.FONT, 13))

    canvas.bind("<Button-1>", lambda event: close_confetti(canvas))
    canvas.winfo_toplevel().after(CONFETTI_TIME, lambda: close_confetti(canvas))
    animate_confetti(canvas, pieces)
    return canvas


# Show both button styles and a confetti button in a small test window when ui.py is run on its own
if __name__ == "__main__":
    window = tk.Tk()
    window.title("ui.py - rounded buttons")
    window.geometry("600x420")
    window.configure(bg=theme.BG, padx=40, pady=40)

    rounded_button(window, "Filled button", lambda: print("Filled clicked"), "filled", 180, 44).pack(pady=10)
    rounded_button(window, "Ghost button", lambda: print("Ghost clicked"), "ghost", 180, 44).pack(pady=10)
    rounded_button(window, "Confetti!", lambda: show_confetti(window, "🎉 All done for today!"), "filled", 180, 44).pack(pady=10)
    window.mainloop()
