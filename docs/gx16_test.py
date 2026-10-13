#!/usr/bin/env python3
"""GX16-8 face diagram + continuity test list for the marquee link. Run: python3 docs/gx16_test.py"""
import math
from PIL import Image, ImageDraw, ImageFont
W, H = 1560, 960
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
def F(s, b=False):
    for p in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if b else []) + ["/System/Library/Fonts/Supplemental/Arial.ttf"]:
        try: return ImageFont.truetype(p, s)
        except OSError: pass
    return ImageFont.load_default()
d.text((40, 25), "GX16-8 link socket - which pin is which, and what to test", font=F(34, True), fill="black")
d.text((40, 72), "Looking straight at the pins (the front you plug the cable into).", font=F(20), fill="#444")
cx, cy, R = 360, 470, 215
d.ellipse([cx-R-30, cy-R-30, cx+R+30, cy+R+30], fill="#b0b8bf", outline="#555", width=4)      # metal shell
d.ellipse([cx-R, cy-R, cx+R, cy+R], fill="#3a3a3a")                                          # insulator
d.rectangle([cx-22, cy-R-34, cx+22, cy-R+18], fill="#ffcc33", outline="#555", width=3)       # key
d.text((cx-170, cy-R-115), "KEY (notch / rib in the shell) - at the top", font=F(20, True), fill="#b07800")
COL = {1: "#e53935", 2: "#e53935", 3: "#111", 4: "#111", 5: "#e53935", 6: "#aaaaaa", 7: "#43a047", 8: "#111"}
NAME = {1: "+12 V", 2: "+12 V", 3: "0 V", 4: "0 V", 5: "USB 5V", 6: "D-", 7: "D+", 8: "USB GND"}
pos = {}
for i in range(7):
    a = math.radians(-90 - 360 / 7 * (i + 0.5))         # pin 1 just LEFT of the key, counting anticlockwise (the sockets used here, beep-tested 2026-10-06)
    pos[i + 1] = (cx + 0.66 * R * math.cos(a), cy + 0.66 * R * math.sin(a))
pos[8] = (cx, cy)
for n, (x, y) in pos.items():
    d.ellipse([x-30, y-30, x+30, y+30], fill="#d9b14a", outline="white", width=3)
    d.text((x, y), str(n), font=F(30, True), fill="black", anchor="mm")
    lx, ly = cx + (x - cx) * 2.05, (cy + (y - cy) * 2.05) if n != 8 else cy + 52
    if n == 8: lx = cx
    d.text((lx, ly), NAME[n], font=F(19, True), fill=COL[n] if COL[n] != "#111" else "white" if n == 8 else "#111", anchor="mm")
d.text((40, 800), "Pin 8 = centre. Pin 1 is LEFT of the key, 7 is right of it.", font=F(18, True), fill="#444")
d.text((40, 826), "Confirmed on your sockets by the beep test (1-2, 3-4 pairs).", font=F(18), fill="#444")
d.text((40, 852), "Numbers run anticlockwise looking at the pins; on the", font=F(18), fill="#444")
d.text((40, 878), "solder-cup side they run clockwise.", font=F(18), fill="#444")
x0, y = 790, 140
d.text((x0, y), "Meter on  →|·))  , nothing plugged in", font=F(24, True), fill="black"); y += 50
TESTS = [("1", "1 ↔ 2", "BEEP", "#2e7d32", "your cup bridge (+12 V pair)"),
         ("2", "3 ↔ 4", "BEEP", "#2e7d32", "your cup bridge (0 V pair)"),
         ("3", "1 ↔ 3", "no steady beep", "#c62828", "12 V not shorted to 0 V (a short chirp\n= converter capacitor charging - OK)"),
         ("4", "6 ↔ 7", "no beep", "#c62828", "D- and D+ not bridged"),
         ("5", "5 ↔ 8", "no steady beep", "#c62828", "USB 5 V not shorted (0.3-0.7 V reading OK)"),
         ("6", "1 ↔ 5", "OL", "#c62828", "12 V side not crossed onto USB 5 V"),
         ("7", "3 ↔ 8", "BEEP (with panels wired)", "#2e7d32", "grounds meet through ESP32 → panel → converter\n- normal; OL only if the panel harness is unplugged")]
for n, pair, want, c, why in TESTS:
    d.rounded_rectangle([x0, y, W-40, y+78], 10, fill="#f4f6f8")
    d.text((x0+18, y+14), n, font=F(26, True), fill="#888")
    d.text((x0+60, y+12), pair, font=F(28, True), fill="black")
    d.text((x0+200, y+12), want, font=F(24, True), fill=c)
    d.text((x0+200, y+44), why.split("\n")[0], font=F(17), fill="#555")
    if "\n" in why: d.text((x0+200, y+62), why.split("\n")[1], font=F(15), fill="#555")
    y += 90
d.text((x0, y+5), "Any beep where it says no beep / OL = stop and tell me the pins.", font=F(20, True), fill="#c62828")
im.save(__file__.replace(".py", ".png"))
