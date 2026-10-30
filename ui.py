# Reusable widgets shared by several pages (plain functions, no classes)

# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import tkinter's font tool, so a button can measure its text and size itself
import tkinter.font as tkfont

# Import the app's shared colors and font
import theme


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


# Show both button styles in a small test window when ui.py is run on its own
if __name__ == "__main__":
    window = tk.Tk()
    window.title("ui.py - rounded buttons")
    window.configure(bg=theme.BG, padx=40, pady=40)

    rounded_button(window, "Filled button", lambda: print("Filled clicked"), "filled", 180, 44).pack(pady=10)
    rounded_button(window, "Ghost button", lambda: print("Ghost clicked"), "ghost", 180, 44).pack(pady=10)
    window.mainloop()
