#!/usr/bin/env python3
"""Draws docs/marquee_layout.png - where everything sits in the marquee trays (numbers from the .scad, 2026-10-01).
Head coords: x across (0 = seam, - = left from the front), y = depth from the LED face (0) to the back (56.4),
z = height from the bottom outside (0..92)."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

S = 4.0                                   # px per mm
W_MM, X0 = 332, -166
img = Image.new("RGB", (1640, 960), "white")
d = ImageDraw.Draw(img)
def font(n, b=False):
    for f in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if b else []) + ["/System/Library/Fonts/Supplemental/Arial.ttf"]:
        try: return ImageFont.truetype(f, n)
        except OSError: pass
    return ImageFont.load_default()
F, FB, FT = font(15), font(16, True), font(22, True)

def view(ox, oy, title):
    d.text((ox, oy - 34), title, font=FB, fill="#111")
    return lambda x, y: (ox + (x - X0) * S, oy + y * S)

def rect(P, x0, y0, x1, y1, fill, outline="#333", w=2):
    a, b = P(x0, y0), P(x1, y1)
    d.rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])], fill=fill, outline=outline, width=w)

def label(P, x, y, s, col="#111", anchor="la", f=None):
    d.text(P(x, y), s, font=f or F, fill=col, anchor=anchor)

d.text((820, 22), "Marquee trays - where everything goes", font=FT, fill="#111", anchor="ma")

# ---------------- TOP SECTION (looking down, cut through the middle) ----------------
P = view(55, 110, "1. Seen from ABOVE, cut through the middle - LED face at the top, back at the bottom (mm)")
rect(P, -166, -1, 166, 56.4, "#cfd8dc", "#455a64", 3)                      # tray shell
rect(P, -163.8, 0, 163.8, 54, "white", "#455a64", 1)                        # cavity (incl. end relief)
for sx in (-1, 1):
    rect(P, sx * 160 if sx < 0 else 0, 0, 0 if sx < 0 else 160, 15, "#263238")   # panels
    rect(P, sx * 160 if sx < 0 else 0, 15, 0 if sx < 0 else 160, 33, "#eceff1", "#90a4ae", 1)
label(P, -80, 7.5, "LED panel 1 (left from the front)  15 mm", "#fff", "mm")
label(P, 80, 7.5, "LED panel 2  15 mm", "#fff", "mm")
label(P, -42.5, 24, "plugs 18", "#607d8b", "mm")
label(P, 42.5, 24, "plugs 18", "#607d8b", "mm")
for x in (-92.5, -67.5, -17.5, 17.5, 67.5, 92.5):                            # screw tubes
    rect(P, x - 5, 15, x + 5, 56.4, "#b0bec5", "#546e7a", 1)
rect(P, -123, 15, -113, 33, "#ffcc80", "#e65100", 2); label(P, -118, 34, "J1 (in)", "#e65100", "ma")
rect(P, -156.8, 19, -155.2, 48, "#2e7d32", "#1b5e20", 1)                     # ESP32 board
for yy in (21.2, 45.8): rect(P, -163.8, yy - 2.25, -156.8, yy + 2.25, "#a5d6a7", "#2e7d32", 1)   # standoffs
rect(P, -155.2, 19, -132.7, 48, "#c8e6c9", "#2e7d32", 1)                     # headers + jumpers
label(P, -144, 33.5, "ESP32", "#1b5e20", "mm", FB)
rect(P, 131.8, 36, 163.8, 54, "#9e9e9e", "#424242", 2); label(P, 147.8, 45, "buck", "#fff", "mm", FB)
rect(P, 45, 32, 65, 54, "#bdbdbd", "#424242", 2); label(P, 55, 43, "GX16", "#111", "mm", FB)
rect(P, 47, 54, 63, 56.4, "white", "#424242", 1)
d.line([P(0, -1), P(0, 56.4)], fill="#d32f2f", width=2); label(P, 1.5, 49, "seam (open inside)", "#d32f2f")
# depth dimension
xd = 172
for y, s in ((0, "0"), (15, "15"), (33, "33"), (54, "54"), (56.4, "")):
    d.line([P(xd - 2, y), P(xd + 2, y)], fill="#111", width=2)
d.line([P(xd, -1), P(xd, 56.4)], fill="#111", width=2)
label(P, xd + 4, 7, "panel", anchor="lm"); label(P, xd + 4, 24, "panel plugs", anchor="lm")
label(P, xd + 4, 43, "wiring room 21", anchor="lm"); label(P, xd + 4, 57, "back 2.4  = 57 deep", anchor="lm")

# ---------------- BACK-REMOVED VIEW (from behind would mirror it; drawn as seen from the FRONT through the panels) ----
P2 = view(55, 470, "2. Seen from the FRONT with the panels removed (heights in mm) - electronics go in through this opening first")
def Q(x, z): return P2(x, 92 - z)
def r2(x0, z0, x1, z1, fill, outline="#333", w=2): rect(P2, x0, 92 - z1, x1, 92 - z0, fill, outline, w)
r2(-166, 0, 166, 92, "#cfd8dc", "#455a64", 3); r2(-163.8, 5.7, 163.8, 86.3, "white", "#455a64", 1)
for x, z in ((-92.5, 78.5), (-17.5, 78.5), (-17.5, 13.5), (-67.5, 13.5), (17.5, 78.5), (67.5, 78.5), (17.5, 13.5), (92.5, 13.5)):
    d.ellipse([Q(x - 5, z + 5), Q(x + 5, z - 5)], fill="#b0bec5", outline="#546e7a", width=2)
    d.ellipse([Q(x - 1.7, z + 1.7), Q(x + 1.7, z - 1.7)], fill="white")
label(P2, -17.5, 92 - 70, "screw tubes = panel rests here", "#37474f", "mm")
r2(-156.8, 26, -132.7, 78, "#c8e6c9", "#2e7d32", 2); label(P2, -144.7, 92 - 52, "ESP32", "#1b5e20", "mm", FB)
label(P2, -144.7, 92 - 46, "on its end", "#1b5e20", "mm")
r2(-154, 8, -146, 26, "#90caf9", "#1565c0", 1); label(P2, -142, 92 - 14, "USB-C (angled)", "#1565c0", "lm")
r2(-123, 36, -113, 56, "#ffcc80", "#e65100", 2); label(P2, -110, 92 - 46, "J1 on panel 1's back", "#e65100", "lm")
r2(131.8, 6, 163.8, 69, "#9e9e9e", "#424242", 2); label(P2, 147.8, 92 - 40, "buck", "#fff", "mm", FB); label(P2, 147.8, 92 - 46, "flat on the back", "#fff", "mm")
d.ellipse([Q(45, 28), Q(65, 8)], fill="#bdbdbd", outline="#424242", width=2); label(P2, 55, 92 - 18, "GX16", "#111", "mm", FB)
d.line([Q(0, 0), Q(0, 92)], fill="#d32f2f", width=2)
d.line([Q(-150, 9), Q(-150, 7), Q(45, 7), Q(52, 10)], fill="#1565c0", width=3)
label(P2, -60, 92 - 3.5, "USB pigtail along the floor", "#1565c0", "mm")
d.line([Q(62, 24), Q(75, 34), Q(131.8, 34)], fill="#c62828", width=3); label(P2, 108, 92 - 39, "12 V to the buck", "#c62828", "mm")
label(P2, -80, 92 - 88.5, "LEFT tray", "#455a64", "mm", FB); label(P2, 80, 92 - 88.5, "RIGHT tray", "#455a64", "mm", FB)

out = Path(__file__).with_name("marquee_layout.png"); img.save(out); print("wrote", out)
