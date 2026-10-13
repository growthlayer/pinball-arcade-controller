#!/usr/bin/env python3
"""Case DMD socket (GX16-8) seen from the SOLDER-CUP side, with what goes in each cup. Run: python3 docs/gx16_case_solder.py"""
import math
from PIL import Image, ImageDraw, ImageFont
W, H = 1560, 900
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
def F(s, b=False):
    for p in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if b else []) + ["/System/Library/Fonts/Supplemental/Arial.ttf"]:
        try: return ImageFont.truetype(p, s)
        except OSError: pass
    return ImageFont.load_default()
d.text((40, 25), "Case DMD socket - SOLDER-CUP side (from inside the case)", font=F(34, True), fill="black")
d.text((40, 72), "Key at the top. From this side pin 1 is RIGHT of the key and the numbers run CLOCKWISE (mirror of the front).", font=F(20), fill="#444")
cx, cy, R = 360, 450, 215
d.ellipse([cx-R-30, cy-R-30, cx+R+30, cy+R+30], fill="#b0b8bf", outline="#555", width=4)
d.ellipse([cx-R, cy-R, cx+R, cy+R], fill="#3a3a3a")
d.rectangle([cx-22, cy-R-34, cx+22, cy-R+18], fill="#ffcc33", outline="#555", width=3)
d.text((cx, cy-R-75), "KEY", font=F(22, True), fill="#b07800", anchor="mm")
WIRE = {1: ("#e53935", "+12 V lead"), 2: ("#e53935", "bridge to 1"), 3: ("#111111", "0 V lead"), 4: ("#111111", "bridge to 3"),
        5: ("#e53935", "USB red"), 6: ("#9e9e9e", "USB white"), 7: ("#43a047", "USB green"), 8: ("#111111", "USB black")}
pos = {}
for i in range(7):
    a = math.radians(-90 + 360 / 7 * (i + 0.5))          # solder side: pin 1 right of the key, clockwise
    pos[i + 1] = (cx + 0.66 * R * math.cos(a), cy + 0.66 * R * math.sin(a))
pos[8] = (cx, cy)
d.line([pos[1], pos[2]], fill="#e53935", width=10); d.line([pos[3], pos[4]], fill="#cccccc", width=10)
for n, (x, y) in pos.items():
    c, lab = WIRE[n]
    d.ellipse([x-30, y-30, x+30, y+30], fill="#d9b14a", outline=c, width=6)
    d.text((x, y), str(n), font=F(30, True), fill="black", anchor="mm")
    if n == 8: d.text((cx, cy+50), lab, font=F(17, True), fill="white", anchor="mm"); continue
    lx, ly = cx + (x - cx) * 2.05, cy + (y - cy) * 2.05
    d.text((lx, ly), lab, font=F(18, True), fill=c if c != "#111111" else "#111", anchor="mm")
x0, y = 800, 130
d.text((x0, y), "Cup  →  wire", font=F(26, True), fill="black"); y += 48
ROWS = [("1", "+12 V", "red 18-20 AWG lead (long, end taped) - to the +12 V Wago later / bench supply +", "#e53935"),
        ("2", "+12 V", "short bare bridge from cup 1", "#e53935"),
        ("3", "0 V", "black 18-20 AWG lead (long, end taped) - to the GND Wago later / bench supply −", "#111"),
        ("4", "0 V", "short bare bridge from cup 3", "#111"),
        ("5", "USB +5 V", "USB-A cable RED", "#e53935"),
        ("6", "USB D−", "USB-A cable WHITE", "#777"),
        ("7", "USB D+", "USB-A cable GREEN", "#2e7d32"),
        ("8", "USB GND", "USB-A cable BLACK (not the 0 V lead!)", "#111")]
for n, sig, wire, c in ROWS:
    d.rounded_rectangle([x0, y, W-40, y+62], 10, fill="#f4f6f8")
    d.text((x0+18, y+14), n, font=F(28, True), fill="black")
    d.text((x0+70, y+8), sig, font=F(20, True), fill=c)
    d.text((x0+70, y+35), wire, font=F(16), fill="#444")
    y += 72
d.text((x0, y+6), "Heat-shrink every cup. Keep 1-2 and 3-4 apart. USB-A cable ~30 cm (reaches hub A4).", font=F(17, True), fill="#c62828")
d.text((40, 820), "Check after soldering: from the FRONT the beep tests in gx16_test.png must pass (1-2 beep, 3-4 beep, nothing else shorted).", font=F(18), fill="#444")
im.save(__file__.replace(".py", ".png"))
