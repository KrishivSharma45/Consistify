# Reusable widgets shared by several pages (plain functions, no classes)

# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import tkinter's font tool, so a button can measure its text and size itself
import tkinter.font as tkfont
# Import math (cos and sin) and random, to send each confetti piece off in its own direction
import math
import random

# Import the app's shared colors and font
import theme

CONFETTI_PIECES = 120     # how many pieces burst out
CONFETTI_GRAVITY = 0.35   # how much faster every piece falls each frame (pixels per frame, added each frame)
CONFETTI_DRAG = 0.99      # each frame the sideways speed keeps 99% of itself, like air slowing it down
CONFETTI_FRAME = 16       # milliseconds between frames (about 60 frames a second)
CONFETTI_TIME = 2500      # milliseconds before the celebration closes by itself


# Return the corner points of a rounded rectangle; with smooth=True, tkinter bends the outline through them
def rounded_rectangle_points(x1, y1, x2, y2, radius):
    # Each corner point is listed 3 times: the curve hugs a point more tightly the more often it appears,
    # so the straight edges stay straight and only the corners get rounded
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
    canvas.create_text(size / 2, size / 2, text=emoji, font=(theme.FONT, int(size / 3)))
    return canvas


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


# Cover the parent with a celebration: a burst of falling confetti and a big message; return the canvas
def show_confetti(parent, message):
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
    canvas.create_text(middle_x, middle_y + 46, text="See you tomorrow 🔥", fill=theme.MUTED, font=(theme.FONT, 13))

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
