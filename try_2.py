import tkinter as tk

# Original data (status-based lines)
data = {
    '1': {'id': 1, 'position_start': [805.0, 190.0], 'position_end': [805.0, 568.0], 'point': 10, 'ownedBy': 10, 'status': 1},
    '2': {'id': 2, 'position_start': [805.0, 2263.0], 'position_end': [805.0, 1885.0], 'point': 10, 'ownedBy': 0, 'status': 0},
    '3': {'id': 3, 'position_start': [1654.0, 190.0], 'position_end': [1220.0, 190.0], 'point': 10, 'ownedBy': 0, 'status': 0},
    '4': {'id': 4, 'position_start': [1654.0, 2263.0], 'position_end': [1220.0, 2263.0], 'point': 10, 'ownedBy': 0, 'status': 0},
    '5': {'id': 5, 'position_start': [1668.0, 665.0], 'position_end': [1900.0, 180.0], 'point': 10, 'ownedBy': 0, 'status': 0},
    '6': {'id': 6, 'position_start': [1668.0, 1768.0], 'position_end': [2268.0, 2262.0], 'point': 10, 'ownedBy': 0, 'status': 0},
    '7': {'id': 7, 'position_start': [1670.0, 1225.0], 'position_end': [190.0, 666.0], 'point': 15, 'ownedBy': 0, 'status': 0},
    '8': {'id': 8, 'position_start': [800.0, 1225.0], 'position_end': [2070.0, 660.0], 'point': 15, 'ownedBy': 0, 'status': 0},
    '9': {'id': 9, 'position_start': [2275.0, 1230.0], 'position_end': [196.0, 2270.0], 'point': 20, 'ownedBy': 0, 'status': 0},
    '10': {'id': 10, 'position_start': [196.0, 1232.0], 'position_end': [2236.0, 190.0], 'point': 20, 'ownedBy': 0, 'status': 0}
}

# Extra points (nodes)
extra_points = [
    [2248, 187], [1230, 1400], [1400, 1225], [1668, 670], [200, 670],
    [1230, 670], [1900, 187], [1668, 1225], [1668, 1765], [200, 1225],
    [1230, 1765], [1230, 2268], [1668, 2268], [200, 2268], [2262, 1225],
    [2262, 1765], [200, 187], [1230, 187], [1060, 1225], [2262, 2268],
    [2070, 670], [800, 670], [800, 1225], [800, 1890], [1110, 1375],
    [800, 2268], [1230, 1040], [800, 187]
]

# New line strings
line_strings = [
    {'name': '', 'start': [200, 187], 'end': [800, 187]},
    {'name': '', 'start': [800, 187], 'end': [1230, 187]},
    {'name': '', 'start': [1230, 187], 'end': [1900, 187]},
    {'name': '', 'start': [1900, 187], 'end': [2248, 187]},
    {'name': '', 'start': [200, 670], 'end': [800, 670]},
    {'name': '', 'start': [800, 670], 'end': [1230, 670]},
    {'name': '', 'start': [1230, 670], 'end': [1668, 670]},
    {'name': '', 'start': [1668, 670], 'end': [2070, 670]},
    {'name': '', 'start': [200, 670], 'end': [200, 1225]},
    {'name': '', 'start': [200, 1225], 'end': [200, 2268]},
    {'name': '', 'start': [200, 1225], 'end': [800, 1225]},
    {'name': '', 'start': [800, 1225], 'end': [1060, 1225]},
    {'name': '', 'start': [1400, 1225], 'end': [1668, 1225]},
    {'name': '', 'start': [1668, 1225], 'end': [2262, 1225]},
    {'name': '', 'start': [800, 187], 'end': [800, 670]},
    {'name': '', 'start': [800, 670], 'end': [800, 1225]},
    {'name': '', 'start': [800, 1225], 'end': [800, 1890]},
    {'name': '', 'start': [800, 1890], 'end': [800, 2268]},
    {'name': '', 'start': [1900, 187], 'end': [2070, 670]},
    {'name': '', 'start': [2070, 670], 'end': [2262, 1225]},
    {'name': '', 'start': [2262, 1225], 'end': [2262, 1765]},
    {'name': '', 'start': [2262, 1765], 'end': [2262, 2268]},
    {'name': '', 'start': [1230, 187], 'end': [1230, 670]},
    {'name': '', 'start': [1230, 670], 'end': [1230, 1040]},
    {'name': '', 'start': [1230, 1400], 'end': [1230, 1765]},
    {'name': '', 'start': [1230, 1765], 'end': [1230, 2268]},
    {'name': '', 'start': [1668, 670], 'end': [1668, 1225]},
    {'name': '', 'start': [1668, 1225], 'end': [1668, 1765]},
    {'name': '', 'start': [1668, 1765], 'end': [1668, 2268]},
    {'name': '', 'start': [200, 2268], 'end': [800, 2268]},
    {'name': '', 'start': [800, 2268], 'end': [1230, 2268]},
    {'name': '', 'start': [1230, 2268], 'end': [1668, 2268]},
    {'name': '', 'start': [1668, 2268], 'end': [2262, 2268]},
    {'name': '', 'start': [1230, 1765], 'end': [1668, 1765]},
    {'name': '', 'start': [1668, 1765], 'end': [2262, 1765]},
    {'name': '', 'start': [800, 1890], 'end': [1110, 1375]},
    {'name': '', 'start': [1110, 1375], 'end': [1060, 1225]},
    {'name': '', 'start': [1110, 1375], 'end': [1230, 1400]},
    {'name': '', 'start': [1060, 1225], 'end': [1230, 1400]},
    {'name': '', 'start': [1230, 1400], 'end': [1400, 1225]},
    {'name': '', 'start': [1400, 1225], 'end': [1230, 1040]},
    {'name': '', 'start': [1230, 1040], 'end': [1230, 1040]},  # degenerate line
    {'name': '', 'start': [1060, 1225], 'end': [1230, 1040]}
]

# Scale factor (fit into medium window)
SCALE = 0.3

# Colors for status lines
def get_color(status, owned_by):
    if status == 1:
        return "green"
    elif owned_by != 0:
        return "blue"
    else:
        return "gray"

# GUI setup
root = tk.Tk()
root.title("Pretty JSON Viewer (Lines + Points + LineStrings)")

canvas = tk.Canvas(root, width=900, height=700, bg="white")
canvas.pack(fill="both", expand=True)

# Draw status-based lines
for obj in data.values():
    x1, y1 = [coord * SCALE for coord in obj["position_start"]]
    x2, y2 = [coord * SCALE for coord in obj["position_end"]]
    color = get_color(obj["status"], obj["ownedBy"])
    canvas.create_line(x1, y1, x2, y2, fill=color, width=3)
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    canvas.create_text(mid_x, mid_y, text=f'ID:{obj["id"]}\nPt:{obj["point"]}', fill="black")

# Draw extra points
for idx, (x, y) in enumerate(extra_points, start=1):
    x_scaled, y_scaled = x * SCALE, y * SCALE
    r = 4
    canvas.create_oval(x_scaled-r, y_scaled-r, x_scaled+r, y_scaled+r, fill="red")
    canvas.create_text(x_scaled+8, y_scaled, text=f"P{idx}", anchor="w", fill="black")

# Draw line strings
for line in line_strings:
    x1, y1 = [coord * SCALE for coord in line["start"]]
    x2, y2 = [coord * SCALE for coord in line["end"]]
    canvas.create_line(x1, y1, x2, y2, fill="black", width=2, dash=(4, 2))  # dashed black lines

root.mainloop()
