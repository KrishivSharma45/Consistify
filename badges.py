# Import tkinter (Python's built-in GUI library) and give it the short name "tk"
import tkinter as tk
# Import date so the unlocked date can be shown nicely ("31 Oct 2026")
from datetime import date

# Import our own database.py (badges, streaks), the shared colors and the reusable widgets
import database
import theme
import ui

# One emoji per milestone
BADGE_EMOJIS = {3: "🌱", 7: "🔥", 14: "⚡", 30: "🏅", 50: "💎", 100: "👑"}
THIN_BAR = 6        # height of the progress bar on a locked card (pixels)
THICK_BAR = 10      # height of the progress bar on the "Next up" card
RING_SIZE = 110     # the header's progress ring
STAGGER = 70        # milliseconds between one card appearing and the next


# Draw a progress bar on a canvas: a BORDER track across the whole canvas and an ACCENT fill for `fraction` of it
def draw_progress_bar(bar, fraction, height):
    if not bar.winfo_exists():
        return
    bar.delete("all")
    width = bar.winfo_width()
    bar.create_rectangle(0, 0, width, height, fill=theme.BORDER, outline="")
    if fraction > 0:
        bar.create_rectangle(0, 0, width * fraction, height, fill=theme.ACCENT, outline="")


# Create a progress bar canvas that draws itself whenever it gets its (or a new) width
def create_progress_bar(parent, fraction, height):
    bar = tk.Canvas(parent, height=height, bg=parent.cget("bg"), highlightthickness=0)
    bar.bind("<Configure>", lambda event: draw_progress_bar(bar, fraction, height))
    return bar


# Give a widget and everything inside it the hand cursor, and make all of them run `on_click` when clicked
def make_clickable(widget, on_click):
    widget.config(cursor="hand2")
    widget.bind("<Button-1>", lambda event: on_click())
    for child in widget.winfo_children():
        make_clickable(child, on_click)


# Give a widget and everything inside it the hand cursor (for locked cards, which aren't clickable)
def set_hand_cursor(widget):
    widget.config(cursor="hand2")
    for child in widget.winfo_children():
        set_hand_cursor(child)


# One animation step of the header ring: draw it at `progress` (0 to 1) of X/6 and count the number up with it
def grow_header_ring(canvas, number, unlocked, total, progress):
    middle = RING_SIZE / 2
    ui.draw_ring(canvas, middle, middle, (RING_SIZE - 12) / 2, 12, unlocked / total * progress)
    canvas.itemconfig(number, text=str(round(unlocked * progress)) + "/" + str(total))


# Build the "trophy shelf" header card: title, count and a motivating line on the left, a progress ring on the right
def create_header_card(parent, unlocked, total):
    card = ui.create_card(parent)
    left = tk.Frame(card, bg=theme.CARD)
    left.pack(side="left", fill="y")
    tk.Label(left, text="Your badges", font=(theme.FONT, 22, "bold"), fg=theme.TEXT, bg=theme.CARD).pack(anchor="w")
    tk.Label(left, text=str(unlocked) + " of " + str(total) + " unlocked", font=(theme.FONT, 11), fg=theme.ACCENT, bg=theme.CARD).pack(anchor="w", pady=(2, 6))
    if unlocked == total:
        line = "Every badge is yours. Legendary consistency!"
    else:
        line = "Keep your streak alive to unlock the next one."
    tk.Label(left, text=line, font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w")

    ring = tk.Canvas(card, width=RING_SIZE, height=RING_SIZE, bg=theme.CARD, highlightthickness=0)
    ring.pack(side="right")
    number = ring.create_text(RING_SIZE / 2, RING_SIZE / 2, text="0/" + str(total), fill=theme.TEXT, font=(theme.FONT, 16, "bold"))
    # The ring fills up from 0 when the page opens
    ui.animate(ring, lambda progress: grow_header_ring(ring, number, unlocked, total, progress), steps=36)
    return card


# Build the "Next up" card for the first locked milestone (or a message when everything is unlocked)
def create_next_up_card(parent, locked, best_streak):
    card = ui.create_card(parent, border=theme.ACCENT, thickness=2)
    if len(locked) == 0:
        tk.Label(card, text="👑 You've unlocked everything!", font=(theme.FONT, 16, "bold"), fg=theme.ACCENT, bg=theme.CARD).pack(anchor="w")
        return card

    goal = locked[0]
    # Never show more progress than the goal itself
    shown = min(best_streak, goal)
    tk.Label(card, text=BADGE_EMOJIS[goal], font=(theme.FONT, 36), fg=theme.ACCENT, bg=theme.CARD).pack(side="left", padx=(0, 20))

    right = tk.Frame(card, bg=theme.CARD)
    right.pack(side="left", fill="x", expand=True)
    tk.Label(right, text="NEXT UP", font=(theme.FONT, 8, "bold"), fg=theme.ACCENT, bg=theme.CARD).pack(anchor="w")
    tk.Label(right, text=str(goal) + "-day streak", font=(theme.FONT, 15, "bold"), fg=theme.TEXT, bg=theme.CARD).pack(anchor="w")
    tk.Label(right, text=str(shown) + " / " + str(goal) + " days", font=(theme.FONT, 10), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w", pady=(0, 8))
    create_progress_bar(right, shown / goal, THICK_BAR).pack(fill="x")
    days_left = goal - shown
    if days_left == 1:
        to_go = "1 day to go"
    else:
        to_go = str(days_left) + " days to go"
    tk.Label(right, text=to_go, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w", pady=(6, 0))
    return card


# Build the card for an unlocked badge: orange-tinted, 2px accent border, emoji, title, habit, date, "✓ Unlocked"
def create_unlocked_card(grid, milestone, habit_name, unlocked_date, page_parent):
    card = ui.create_card(grid, bg=theme.ACCENT_SOFT, border=theme.ACCENT, thickness=2)
    tk.Label(card, text=BADGE_EMOJIS[milestone], font=(theme.FONT, 30), fg=theme.ACCENT, bg=theme.ACCENT_SOFT).pack(anchor="w")
    tk.Label(card, text=str(milestone) + "-day streak", font=(theme.FONT, 13, "bold"), fg=theme.TEXT, bg=theme.ACCENT_SOFT).pack(anchor="w", pady=(8, 0))
    tk.Label(card, text="Earned with " + habit_name, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.ACCENT_SOFT).pack(anchor="w")
    # The database stores "2026-10-31"; strftime turns it into "31 Oct 2026"
    nice_date = date.fromisoformat(unlocked_date).strftime("%d %b %Y")
    tk.Label(card, text="Unlocked " + nice_date, font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.ACCENT_SOFT).pack(anchor="w")
    ui.create_pill(card, "✓ Unlocked", theme.BG, theme.ACCENT).pack(anchor="w", pady=(10, 0))

    # Hover: the border brightens; click: celebrate this badge again
    ui.add_hover_border(card, theme.ACCENT, theme.ACCENT_HOVER, 2)
    make_clickable(card, lambda: ui.show_confetti(
        page_parent, BADGE_EMOJIS[milestone] + " " + str(milestone) + "-day streak", subtitle="Earned with " + habit_name
    ))
    return card


# Build the card for a locked badge: a grey lock, the goal, and a bar showing how close the best streak is
def create_locked_card(grid, milestone, best_streak):
    card = ui.create_card(grid)
    tk.Label(card, text="🔒", font=(theme.FONT, 30), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w")
    tk.Label(card, text=str(milestone) + "-day streak", font=(theme.FONT, 13, "bold"), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w", pady=(8, 0))
    tk.Label(card, text="Reach a " + str(milestone) + "-day streak", font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w")

    # Progress = best current streak / milestone, but never more than 100% (and the text never above the goal)
    shown = min(best_streak, milestone)
    create_progress_bar(card, shown / milestone, THIN_BAR).pack(fill="x", pady=(10, 4))
    tk.Label(card, text=str(shown) + " / " + str(milestone) + " days", font=(theme.FONT, 9), fg=theme.MUTED, bg=theme.CARD).pack(anchor="w")

    ui.add_hover_border(card, theme.BORDER, theme.MUTED, 1)
    set_hand_cursor(card)
    return card


# Show the cards one after another: card number i appears i x STAGGER milliseconds after the page opens
def stagger_in(page_widget, placements):
    for i in range(len(placements)):
        place_card = placements[i]
        page_widget.winfo_toplevel().after(i * STAGGER, lambda place_card=place_card: show_if_open(page_widget, place_card))


# Put one card on screen, unless the page was closed in the meantime
def show_if_open(page_widget, place_card):
    if page_widget.winfo_exists():
        place_card()


# Build the whole Badges page inside the parent: header, "Next up" and the grid of all six badges
def build_badges_page(parent, user_id):
    page = ui.create_scroll_page(parent)

    # badges: milestone -> (habit_name, unlocked_date), so we can look up whether each milestone is unlocked
    badges = {}
    for milestone, habit_name, unlocked_date in database.get_badges(user_id):
        badges[milestone] = (habit_name, unlocked_date)
    locked = [milestone for milestone in database.MILESTONES if milestone not in badges]
    best_streak = database.get_current_best_streak(user_id)

    header_row = ui.add_page_row(page)
    next_row = ui.add_page_row(page)
    grid = ui.add_page_row(page)
    # Three equal columns for the badge cards
    for column in range(3):
        grid.columnconfigure(column, weight=1, uniform="badge")

    # Every card is built now but put on screen later, one after another (a lambda for each placement)
    header = create_header_card(header_row, len(badges), len(database.MILESTONES))
    next_up = create_next_up_card(next_row, locked, best_streak)
    placements = [
        lambda: header.pack(fill="x"),
        lambda: next_up.pack(fill="x"),
    ]
    for i in range(len(database.MILESTONES)):
        milestone = database.MILESTONES[i]
        if milestone in badges:
            habit_name, unlocked_date = badges[milestone]
            card = create_unlocked_card(grid, milestone, habit_name, unlocked_date, parent)
        else:
            card = create_locked_card(grid, milestone, best_streak)
        # i // 3 is the row (0, 0, 0, 1, 1, 1) and i % 3 the column (0, 1, 2, 0, 1, 2)
        placements.append(lambda card=card, row=i // 3, column=i % 3: card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6))

    stagger_in(page["canvas"], placements)
    return page


# Run this block only when badges.py is started directly (not when imported)
if __name__ == "__main__":
    database.create_tables()

    # Log in as a test user (create_user just returns False if "demo" already exists)
    database.create_user("demo", "demo123")
    user_id = database.check_login("demo", "demo123")

    window = tk.Tk()
    window.title("Consistify - Badges")
    # The same size as the dashboard's content area in main.py (1100 wide minus the 200px sidebar, 700 tall)
    window.geometry("900x700")
    window.configure(bg=theme.BG)

    build_badges_page(window, user_id)
    window.mainloop()
