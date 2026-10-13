#!/usr/bin/env python3
"""USB path test: the PINBALL socket's USB-A plug (junction box) -> tether -> tether's CONTROLLER-end plug (holes).
Run: python docs/usb_tether_test.py -> docs/usb_tether_test.png"""
import math, os
from PIL import Image, ImageDraw, ImageFont


def F(s, b=False):
    for p in (["C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if b else
              ["C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]):
        if os.path.exists(p):
            return ImageFont.truetype(p, s)
    return ImageFont.load_default()


W, H = 1900, 1100
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
d.text((40, 22), "USB path test: junction-box USB-A plug  ->  tether  ->  tether's CONTROLLER-end plug", font=F(32, True), fill="black")
d.text((40, 66), "Tether plugged into the junction box, its other end loose. Power OFF. Meter on continuity (beep).", font=F(20), fill="#444")

# --- USB-A plug face
ux, uy = 70, 170
d.text((ux, uy - 40), "1) USB-A PLUG on the PINBALL socket's lead (in the junction box)", font=F(22, True), fill="black")
d.text((ux, uy - 12), "Looking into the plug, contacts facing up:", font=F(18), fill="#444")
d.rectangle([ux, uy + 20, ux + 560, uy + 250], fill="#c9ced3", outline="#555", width=4)       # metal shell
d.rectangle([ux + 30, uy + 120, ux + 530, uy + 220], fill="#f2f2f2", outline="#777", width=2)  # plastic tongue
cont = [("OUTER", ux + 70, "#e53935", "A"), ("inner", ux + 200, "#999", "B"), ("inner", ux + 330, "#2e7d32", "C"), ("OUTER", ux + 460, "#111", "D")]
for kind, x, c, tag in cont:
    long_ = kind == "OUTER"
    d.rectangle([x - 28, uy + 96, x + 28, uy + 120], fill="#d9b14a", outline="#8a6d1a", width=2)
    d.text((x, uy + 70), tag, font=F(30, True), fill="black", anchor="mm")
    d.text((x, uy + 268), "outer (longer)" if long_ else "inner (data)", font=F(17, True), fill="#444", anchor="mm")
d.text((ux, uy + 300), "A and D = outer contacts: one is +5 V, the other ground.", font=F(19), fill="#444")
d.text((ux, uy + 326), "B and C = inner contacts: the two data lines.", font=F(19), fill="#444")
d.text((ux, uy + 352), "(If the contacts face down, just flip the letters left-right.)", font=F(17), fill="#777")

# --- tether plug (holes) face, key at top: mirror of the pin face -> pin 1 RIGHT of key, clockwise
cx, cy, R = 1450, 380, 200
d.text((cx - 360, 108), "2) TETHER's CONTROLLER-end plug (the HOLES), key at the TOP", font=F(22, True), fill="black")
d.ellipse([cx-R-30, cy-R-30, cx+R+30, cy+R+30], fill="#b0b8bf", outline="#555", width=4)
d.ellipse([cx-R, cy-R, cx+R, cy+R], fill="#3a3a3a")
d.rectangle([cx-22, cy-R-36, cx+22, cy-R+16], fill="#ffcc33", outline="#555", width=3)
NAME = {1: "+12 V", 2: "+12 V", 3: "0 V", 4: "0 V", 5: "USB 5V", 6: "D-", 7: "D+", 8: "USB GND"}
pos = {}
for i in range(7):
    a = math.radians(-90 + 360 / 7 * (i + 0.5))     # mirror of the beep-tested pin face: 1 right of key, clockwise
    pos[i + 1] = (cx + 0.66 * R * math.cos(a), cy + 0.66 * R * math.sin(a))
pos[8] = (cx, cy)
for n, (x, y) in pos.items():
    usb = n in (5, 6, 7, 8)
    d.ellipse([x-30, y-30, x+30, y+30], fill="#1a1a1a", outline="#6cf" if usb else "#e57373", width=5)   # a hole
    d.text((x, y), str(n), font=F(28, True), fill="white", anchor="mm")
    if n != 8:
        d.text((cx + (x - cx) * 1.95, cy + (y - cy) * 1.95), NAME[n], font=F(20, True),
               fill="#1565c0" if usb else "#e53935", anchor="mm")
d.text((cx, cy + 50), "USB GND", font=F(18, True), fill="#6cf", anchor="mm")
d.text((cx - 300, cy + R + 78), "Holes = mirror of the socket: pin 1 RIGHT of the key, clockwise; 8 = centre.", font=F(17), fill="#444")
d.text((cx - 300, cy + R + 102), "Push a paperclip into each hole to probe it.", font=F(17), fill="#444")

# --- test table
x0, y = 70, 730
d.rectangle([x0 - 15, y - 10, W - 40, y + 40], fill="#eceff1")
d.text((x0, y), "TEST", font=F(23, True), fill="black"); d.text((x0 + 560, y), "EXPECTED", font=F(23, True), fill="black")
y += 56
rows = [("Outer contact A or D  <->  hole 5", "ONE of them beeps -> that one is +5 V", "#2e7d32"),
        ("The other outer contact  <->  hole 8", "BEEP (USB ground)", "#2e7d32"),
        ("Inner contact NEXT TO the +5 V one  <->  hole 6", "BEEP (D-)", "#2e7d32"),
        ("Inner contact NEXT TO ground  <->  hole 7", "BEEP (D+)", "#2e7d32"),
        ("Inner next to +5 V  <->  hole 7   (and the other inner <-> 6)", "NO BEEP - if it beeps, D+ and D- are SWAPPED", "#c62828"),
        ("Any USB contact  <->  hole 1 or 2", "NO BEEP - 12 V must never reach USB", "#c62828")]
for t, e, c in rows:
    d.text((x0, y), t, font=F(21, True), fill="black")
    d.text((x0 + 560 + 280, y), e, font=F(21, True), fill=c)
    y += 46
d.text((x0, y + 10), "Swapped -> swap white/green at ONE end.   A data line with no beep -> broken wire at that plug or the splice.   "
       "Wiggle both plugs while testing 6 and 7.", font=F(18, True), fill="#444")
im.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "usb_tether_test.png"))
print("written")
