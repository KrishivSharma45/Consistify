# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk

# Import our own files: the database, the habit section and the heatmap
import database
import gui
import heatmap

BG_COLOR = "#0d1117"   # dark background, the same one gui.py and heatmap.py use


# Redraw the heatmap with fresh data and reset its info text, since the old text may be out of date
def refresh_heatmap_section(canvas, info_label):
    heatmap.refresh_heatmap(canvas, info_label)
    info_label.config(text="Click a square to see details")


# Run this block only when main.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    window = tk.Tk()
    window.title("Consistify")
    window.geometry("1300x700")
    window.configure(bg=BG_COLOR)

    # Two side-by-side areas: habits on the left, heatmap on the right
    left_frame = tk.Frame(window, bg=BG_COLOR)
    left_frame.pack(side="left", fill="both", expand=True)
    right_frame = tk.Frame(window, bg=BG_COLOR)
    right_frame.pack(side="right", fill="y", padx=(0, 30), pady=(110, 0))

    # Build the heatmap first, so the habit section can be given a way to redraw it
    canvas, info_label = heatmap.create_heatmap_section(right_frame)
    gui.create_habit_section(
        left_frame,
        on_change=lambda: refresh_heatmap_section(canvas, info_label),
    )

    window.mainloop()
