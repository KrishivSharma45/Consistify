import tkinter as tk
import random

# Size settings for the heatmap (in pixels)
SQUARE_SIZE = 14
GAP = 3
PADDING = 10


# Return the color for a given number of habits done in one day
def get_color(count):
    if count == 0:
        return "#161b22"
    elif count == 1:
        return "#0e4429"
    elif count == 2:
        return "#006d32"
    elif count == 3:
        return "#26a641"
    else:
        return "#39d353"


# Draw one square per day on the canvas, 7 days in each column
def draw_heatmap(canvas, counts):
    for i in range(len(counts)):
        column = i // 7
        row = i % 7

        x1 = PADDING + column * (SQUARE_SIZE + GAP)
        y1 = PADDING + row * (SQUARE_SIZE + GAP)
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE

        color = get_color(counts[i])
        canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")


if __name__ == "__main__":
    window = tk.Tk()
    window.title("Consistify - Heatmap")
    window.configure(bg="#0d1117")

    # 240 x 140 is just big enough for 13 columns and 7 rows of squares
    canvas = tk.Canvas(window, width=240, height=140, bg="#0d1117", highlightthickness=0)
    canvas.pack(padx=20, pady=20)

    # Make 90 fake days, each with a random count from 0 to 4
    fake_counts = []
    for day in range(90):
        fake_counts.append(random.randint(0, 4))

    draw_heatmap(canvas, fake_counts)
    window.mainloop()