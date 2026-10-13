#!/usr/bin/env python3
"""GX16-8 junction-box (PINBALL) socket: pin face with the key at the BOTTOM + beep/voltage tests and expected results.
Run: python docs/gx16_box_test.py  ->  docs/gx16_box_test.png"""
import math, os
from PIL import Image, ImageDraw, ImageFont


def F(s, b=False):
    for p in (["C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if b else
              ["C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]):
        if os.path.exists(p):
            return ImageFont.truetype(p, s)
    return ImageFont.load_default()


W, H = 1900, 1180
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
d.text((40, 22), "Junction box PINBALL socket (GX16-8) - test before plugging the tether in", font=F(34, True), fill="black")
d.text((40, 68), "Looking straight at the PINS, key at the BOTTOM.  Same layout as the controller's IN socket.", font=F(20), fill="#444")

# ---- pin face
cx, cy, R = 430, 540, 250
d.ellipse([cx-R-34, cy-R-34, cx+R+34, cy+R+34], fill="#b0b8bf", outline="#555", width=4)
d.ellipse([cx-R, cy-R, cx+R, cy+R], fill="#3a3a3a")
d.rectangle([cx-26, cy+R-20, cx+26, cy+R+40], fill="#ffcc33", outline="#555", width=3)
d.text((cx, cy+R+75), "KEY (notch / rib in the shell)", font=F(22, True), fill="#b07800", anchor="mm")
NAME = {1: "+12 V", 2: "+12 V", 3: "0 V", 4: "0 V", 5: "USB 5V", 6: "D-", 7: "D+", 8: "USB GND"}
COL = {1: "#e53935", 2: "#e53935", 3: "#111", 4: "#111", 5: "#e53935", 6: "#777", 7: "#2e7d32", 8: "#fff"}
pos = {}
for i in range(7):        # beep-tested: key at TOP -> pin 1 left of key, anticlockwise; here rotated 180 deg
    a = math.radians(-90 - 360 / 7 * (i + 0.5) + 180)
    pos[i + 1] = (cx + 0.66 * R * math.cos(a), cy + 0.66 * R * math.sin(a))
pos[8] = (cx, cy)
for n, (x, y) in pos.items():
    d.ellipse([x-36, y-36, x+36, y+36], fill="#e57373" if n in (1, 2) else "#d9b14a", outline="white", width=3)
    d.text((x, y), str(n), font=F(34, True), fill="black", anchor="mm")
    if n == 8:
        d.text((x, y + 60), NAME[n], font=F(22, True), fill="white", anchor="mm")
    else:
        d.text((cx + (x - cx) * 1.95, cy + (y - cy) * 1.95), NAME[n], font=F(24, True), fill=COL[n], anchor="mm")
d.text((40, 1100), "Pin 8 = centre. Key at the bottom: pin 1 just RIGHT of the key, numbers run anticlockwise.", font=F(19), fill="#444")
d.text((40, 1128), "Cable PLUG with holes (not pins) = mirror image.", font=F(19), fill="#444")

# ---- tests
GREEN, RED, GREY = "#2e7d32", "#c62828", "#555"
x0, y = 900, 110


def head(t, sub):
    global y
    d.rectangle([x0 - 12, y - 6, W - 30, y + 62], fill="#eceff1")
    d.text((x0, y), t, font=F(25, True), fill="black")
    d.text((x0, y + 33), sub, font=F(18), fill="#444")
    y += 78


def row(test, expect, col, note=""):
    global y
    d.text((x0, y), test, font=F(22, True), fill="black")
    d.text((x0 + 430, y), expect, font=F(22, True), fill=col)
    if note:
        d.text((x0 + 680, y + 3), note, font=F(17), fill=GREY)
    y += 34


head("A  BEEP test - power OFF", "Box supply unplugged from the wall; inside the box unplug this socket's USB lead from the hub; tether out.")
row("1 <-> 2", "BEEP", GREEN, "+12 V pair")
row("3 <-> 4", "BEEP", GREEN, "0 V pair")
row("1 <-> box +12 V screw", "BEEP", GREEN, "12 V feed")
row("3 <-> box 0 V screw", "BEEP", GREEN, "0 V feed")
row("5,6,7,8 <-> USB-A plug", "BEEP each", GREEN, "red=5, white=6, green=7, black=8")
row("1 or 2 <-> 5, 6, 7, 8", "NO BEEP", RED, "12 V onto USB = what killed the hubs")
row("1 or 2 <-> 3 or 4", "NO BEEP", RED, "short across the supply")
row("5 <-> 6, 7, 8   and  6 <-> 7", "NO BEEP", RED, "USB wires touching")
row("3 or 4 <-> 5, 6, 7", "NO BEEP", RED, "")
row("8 <-> 3 or 4", "either OK", GREY, "")
d.text((x0, y), "Wiggle the wires behind the socket during every NO BEEP test.", font=F(18, True), fill=RED); y += 46

head("B  VOLTS - power ON, USB lead still unplugged", "Meter on DC V.  BLACK probe on pin 3 (0 V), RED probe on each pin:")
row("Pin 1, pin 2", "~12 V", GREEN)
row("Pin 5, 6, 7, 8", "~0 V", GREEN, "near 12 V = STOP, unplug power")
y += 12

head("C  VOLTS - USB lead plugged into the NEW hub", "Hub powered and on the PC.  BLACK on pin 3, RED on each pin:")
row("Pin 1, pin 2", "~12 V", GREEN)
row("Pin 5", "~5 V", GREEN, "USB power from the hub")
row("Pin 6, pin 7", "0 - 3.3 V", GREEN, "data lines")
row("Pin 8", "~0 V", GREEN)
row("Any of 5-8", "never above ~5 V", RED, "")
y += 14
d.text((x0, y), "All three pass -> plug the tether in and tell Claude to check the PC.", font=F(21, True), fill=GREEN)
im.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gx16_box_test.png"))
print("written")
