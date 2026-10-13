#!/usr/bin/env python3
"""Assembly clearance audit: every component + its plugs/cable zones, installed, checked against everything else.

Coordinates = case coords (mm): x 0..254 left->right, y 0..230 front->back, z 0..85 bottom->top.
Top panel underside z = 81; cover top z = 4.2 (cover sits in the rebate). Positions come from the .scad
(numbers dumped 2026-09-30); envelopes are measured where noted, otherwise conservative estimates (src='est').
Run: python3 docs/assembly_audit.py   -> prints CLASH / TIGHT pairs and writes docs/assembly_audit.png
"""
import math
from itertools import combinations

TIGHT = 3.0          # report pairs closer than this (mm)
Z_PANEL, Z_COVER = 81.0, 4.2

parts = []           # (name, group, shape, src)  shape = ('box', x0,x1,y0,y1,z0,z1) | ('cyl', cx,cy,r,z0,z1)
def box(n, g, x0, x1, y0, y1, z0, z1, src="meas"): parts.append((n, g, ("box", x0, x1, y0, y1, z0, z1), src))
def cyl(n, g, cx, cy, r, z0, z1, src="meas"):     parts.append((n, g, ("cyl", cx, cy, r, z0, z1), src))

# ------------------------------------------------ hanging from the top panel ("panel")
six = [(138.1, 116.99), (138.1, 71.99), (178.1, 136.99), (178.1, 91.99), (218.1, 156.99), (218.1, 111.99)]
for i, (x, y) in enumerate(six):
    cyl(f"button {i+1} nut", "panel", x, y, 17, 75, Z_PANEL, "M28 nut ~Ø34 (maker drawing)")
    cyl(f"button {i+1} body+built-in switch+spades", "panel", x, y, 14.5, 41, 75, "Ø28 body, 40 deep incl. spades (meas + drawing)")
for n, (x, y) in (("coin", (81, 203.25)), ("start", (173, 203.25))):
    cyl(f"{n} button nut", "panel", x, y, 17, 75, Z_PANEL, "drawing")
    cyl(f"{n} button body+switch", "panel", x, y, 14.5, 41, 75, "drawing")
box("flipper L button (side wall)", "panel", 5, 41, 174.1, 204.1, 35, 65, "btn 36 long, est")
box("flipper R button (side wall)", "panel", 213, 249, 174.1, 204.1, 35, 65, "est")
box("joystick plate", "panel", 30, 84, 68.53, 163.53, 79.4, Z_PANEL, "54 x 95 (maker drawing)")
box("joystick body+switches+harness", "panel", 32, 82, 85.03, 147.03, 44.4, 79.4, "35 below plate, ~62 long (drawing); 50 across est")
# encoder: posts 29.4 x 80.3 at centre (127, 179.35); board ~37 x 90 (photo est); USB-B socket at the FRONT end
box("encoder board+JST sockets", "panel", 109, 145, 136.35, 222.35, 66, 75, "86 x 36 MEASURED")
box("encoder JST plugs + wire bends", "panel", 109, 145, 136.35, 222.35, 48, 66, "est")
box("encoder USB-B socket only (cable soldered, no plug)", "panel", 119, 131, 133.35, 136.35, 62, 73.4, "socket overhang est")
cyl("exciter pad + ring", "panel", 110, 34, 19.3, 73, Z_PANEL, "pad 33.5 meas")
cyl("exciter body (hangs free)", "panel", 110, 34, 25, 51, 73, "Ø50 x 30 total meas")
box("exciter catch pillar L", "panel", 110-32-4.5, 110-32+4.5, 29.5, 38.5, 49, Z_PANEL, "model")
box("exciter catch pillar R", "panel", 110+32-4.5, 110+32+4.5, 29.5, 38.5, 49, Z_PANEL, "model")
box("exciter catch bridge", "panel", 110-36.5, 110+36.5, 21, 47, 45, 49, "model")
box("T-Display board (in pocket)", "panel", 152.5, 208.7, 19.1, 44.9, 72.5, 82.5, "meas")
box("T-Display clamp", "panel", 158.6, 198.6, 11, 53, 69.5, 72.5, "meas")
box("T-Display USB-C plug (straight)", "panel", 208.7, 243, 27, 37, 73, 80, "est 34 incl. boot")
# back wall (inner face y = 225)
box("GX16 DMD socket (marquee link) + solder cups + wires", "wall", 187, 207, 195, 225, 12, 32, "22 deep meas (same part as the IN socket)")
box("GX16 socket body + solder cups + wires", "wall", 212, 232, 195, 225, 12, 32, "22 deep meas")
box("cable anchor", "wall", 185, 192, 217, 225, 35, 51, "model (+4 x, +3 z over the DMD socket nut)")
# case structure standing up from the rebate
for x0 in (5, 235):
    for y0 in (5, 211):
        box(f"corner post ({'L' if x0 < 100 else 'R'}{'F' if y0 < 100 else 'B'})", "case", x0, x0 + 14, y0, y0 + 14, Z_COVER, 33.2, "model")
box("mid tab front", "case", 121, 133, 5, 17, Z_COVER, 31.2, "model")
box("mid tab back", "case", 121, 133, 213, 225, Z_COVER, 31.2, "model")
box("striker L", "case", 5, 11, 148, 172, Z_COVER, 40, "est")
box("striker R", "case", 243, 249, 148, 172, Z_COVER, 40, "est")

# ------------------------------------------------ standing on the cover ("cover")
box("amp (on posts)", "cover", 93, 161, 120, 212, Z_COVER, 29.2, "meas")
box("relay L", "cover", 21, 83, 8, 46, Z_COVER, 26.2, "meas")
box("relay R", "cover", 171, 233, 12, 50, Z_COVER, 26.2, "meas")
box("Pico pins-up + Dupont housings", "cover", 179.5, 200.5, 84.5, 135.5, Z_COVER, 34.7, "7 posts + header 8.5 + housings 14")
box("Pico micro-USB plug (front)", "cover", 184, 196, 52, 84.5, 6, 13, "est")
box("LIS3DH + jumpers", "cover", 215, 235, 105, 135, Z_COVER, 33, "est")
box("7-port hub (v2 posts)", "cover", 23.2, 67.2, 53.2, 137.2, Z_COVER, 25, "board meas; height est")
box("hub USB-A plugs (5 front ports)", "cover", 67.2, 105, 53, 112, 9, 24, "est 38")
box("DAC stick + 3.5 mm plug (front port)", "cover", 105, 130, 53, 68, 9, 20, "est (beyond the port plugs)")
box("hub 5 V jack wires + micro-USB (left)", "cover", 12, 23.2, 53, 76, 9, 20, "est")
box("JZK buck", "cover", 120, 142, 25, 42, Z_COVER, 10, "est")
box("solenoid L cradle pad", "cover", 21, 84, 148, 172, Z_COVER, 6.2, "model")
box("solenoid R cradle pad", "cover", 170, 233, 148, 172, Z_COVER, 6.2, "model")
box("solenoid L body", "cover", 33, 72, 150.1, 170.1, 6.2, 32.2, "meas")
box("solenoid L rod+plunger", "cover", 11, 33, 155, 165, 12, 26, "meas")
box("solenoid L wires (rear)", "cover", 72, 84, 152, 168, 10, 30, "est")
box("solenoid R body", "cover", 182, 221, 150.1, 170.1, 6.2, 32.2, "meas")
box("solenoid R rod+plunger", "cover", 221, 243, 155, 165, 12, 26, "meas")
box("solenoid R wires (rear)", "cover", 170, 182, 152, 168, 10, 30, "est")


def gap(a, b):
    """clearance between two shapes (negative = overlap depth, approximate)"""
    def xy_gap(s, t):
        if s[0] == "box" and t[0] == "box":
            dx = max(t[1] - s[2], s[1] - t[2]); dy = max(t[3] - s[4], s[3] - t[4])
            if dx < 0 and dy < 0: return max(dx, dy)
            return math.hypot(max(dx, 0), max(dy, 0))
        if s[0] == "cyl" and t[0] == "cyl":
            return math.hypot(s[1] - t[1], s[2] - t[2]) - s[3] - t[3]
        c, b_ = (s, t) if s[0] == "cyl" else (t, s)
        px = min(max(c[1], b_[1]), b_[2]); py = min(max(c[2], b_[3]), b_[4])
        d = math.hypot(c[1] - px, c[2] - py)
        if b_[1] <= c[1] <= b_[2] and b_[3] <= c[2] <= b_[4]: d = -min(c[1] - b_[1], b_[2] - c[1], c[2] - b_[3], b_[4] - c[2])
        return d - c[3]
    za = a[-2:]; zb = b[-2:]
    dz = max(zb[0] - za[1], za[0] - zb[1])
    g = xy_gap(a, b)
    if dz < 0 and g < 0: return max(dz, g)
    if dz < 0: return g
    if g < 0: return dz
    return math.hypot(g, dz)


def run():
    issues = []
    for (na, ga, sa, ra), (nb, gb, sb, rb) in combinations(parts, 2):
        if na.split(" ")[0] == nb.split(" ")[0] and ga == gb and na.split(" ")[1:2] == nb.split(" ")[1:2]:
            continue                                   # skip a part against its own sub-zones
        g = gap(sa, sb)
        if g < TIGHT: issues.append((g, na, nb, ra, rb))
    issues.sort()
    for g, na, nb, ra, rb in issues:
        tag = "CLASH" if g < 0 else "TIGHT"
        print(f"{tag:5} {g:6.1f} mm  {na}  <->  {nb}   [{ra} | {rb}]")
    return issues


if __name__ == "__main__":
    run()
