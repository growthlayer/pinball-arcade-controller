#!/usr/bin/env python3
"""Cable plan: hand-laid channels (straight runs through the gaps), verified against every component, with
zip-tie mounts where the bundles need holding. Coordinates = case coords, mm (x right, y back / front = 0).

Every run and every tie footprint is checked against the component list with a clearance; any collision is
printed as ERROR and the script exits non-zero. Output: docs/routing_cover.png, docs/routing_case.png,
print/tie_points.json (read by the .scad).
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

W, D = 254, 230
INNER = (5.5, 5.5, 248.5, 224.5)
RUN_CLEAR, TIE_CLEAR = 1.5, 1.0
MOUNT = (10, 7)          # tie mount: across the cable x along it (mm)

COVER_OBS = [
    ("amp", ("box", 93, 161, 120, 212)), ("relay L", ("box", 21, 83, 8, 46)), ("relay R", ("box", 171, 233, 12, 50)),
    ("Pico", ("box", 179.5, 200.5, 84.5, 135.5)), ("Pico USB plug", ("box", 184, 196, 60, 84.5)), ("LIS3DH", ("box", 215, 235, 105, 135)),
    ("7-port hub", ("box", 23.2, 67.2, 53.2, 137.2)), ("hub plugs", ("box", 67.2, 100, 55, 112)), ("buck", ("box", 120, 142, 25, 42)),
    ("sol L", ("box", 33, 72, 150, 170)), ("sol L rod", ("box", 11, 33, 154, 166)),
    ("sol R", ("box", 182, 221, 150, 170)), ("sol R rod", ("box", 221, 243, 154, 166)),
    ("J1", ("box", 172, 196, 180, 196)),
    ("cradle pad L", ("box", 21, 84, 148, 172)), ("cradle pad R", ("box", 170, 233, 148, 172)),
    ("corner LF", ("box", 5, 19, 5, 19)), ("corner RF", ("box", 235, 249, 5, 19)), ("corner LB", ("box", 5, 19, 211, 225)),
    ("corner RB", ("box", 235, 249, 211, 225)), ("mid tab F", ("box", 121, 133, 5, 17)), ("mid tab B", ("box", 121, 133, 213, 225)),
    ("striker L", ("box", 5, 11, 148, 172)), ("striker R", ("box", 243, 249, 148, 172)),
]
CASE_OBS = [
    *[(f"B{i+1}", ("cyl", x, y, 17)) for i, (x, y) in enumerate([(138.1, 116.99), (138.1, 71.99), (178.1, 136.99),
                                                                (178.1, 91.99), (218.1, 156.99), (218.1, 111.99)])],
    ("coin", ("cyl", 81, 203.25, 17)), ("start", ("cyl", 173, 203.25, 17)),
    ("flip L", ("box", 5, 41, 174, 204)), ("flip R", ("box", 213, 249, 174, 204)),
    ("joystick", ("box", 30, 84, 68.5, 163.5)), ("encoder", ("box", 109, 145, 136.35, 222.35)),
    ("exciter", ("cyl", 110, 34, 25)), ("exc pillar L", ("box", 73.5, 82.5, 29.5, 38.5)), ("exc pillar R", ("box", 137.5, 146.5, 29.5, 38.5)),
    ("T-Display", ("box", 152.5, 208.7, 11, 53)),
    ("GX16 DMD", ("box", 187, 207, 203, 225)), ("GX16", ("box", 212, 232, 203, 225)),
    ("corner LF", ("box", 5, 19, 5, 19)), ("corner RF", ("box", 235, 249, 5, 19)), ("corner LB", ("box", 5, 19, 211, 225)),
    ("corner RB", ("box", 235, 249, 211, 225)),
]

# channels: (net, colour, polyline). Drop points (case -> cover): D1 back-right above J1, D2 back-left (NC-L),
# D3 front-centre (exciter), D4 front-right (T-Display USB), D5 back-centre (encoder USB).
RED, ORG, TEAL, BLUE, PURP, GRN, PINK = "#cc2222", "#e07b00", "#008b8b", "#1560bd", "#8a2be2", "#2e8b57", "#d33682"
COVER_RUNS = [
    ("12 V + GND, NC-R (J1 -> relays, amp, buck)", RED, [(174, 178), (165.5, 176), (165.5, 146), (171, 141), (171, 58), (106, 52), (86, 52), (86, 42)]),
    ("12 V -> relay R input", RED, [(171, 58), (171, 50)]),
    ("12 V -> buck", RED, [(131, 55), (131, 44)]),
    ("12 V -> amp power", RED, [(165.5, 160), (163, 160)]),
    ("buck 5 V -> hub jack", RED, [(119, 34), (106, 52), (86, 52), (84, 49), (14, 49), (14, 64), (21, 64)]),
    ("NC-L (drops at the back-left) -> relay L", ORG, [(45, 180), (88, 180), (88, 144), (14, 144), (14, 49)]),
    ("relay L -> solenoid L", PURP, [(19, 30), (14, 30), (14, 144), (76, 144), (76, 148)]),
    ("relay R -> solenoid R", PURP, [(235, 30), (242, 30), (242, 146), (178, 146), (178, 148)]),
    ("exciter (drops front-centre) -> amp OUT", TEAL, [(100, 30), (108, 30), (108, 118)]),
    ("DAC 3.5 mm -> amp IN", GRN, [(102, 62), (108, 62), (108, 118)]),
    ("USB: tether (GX16 IN) + marquee (GX16 DMD) -> hub", BLUE, [(222, 201), (200, 204), (165.5, 204), (165.5, 146), (167, 141), (167, 66), (106, 66), (102, 66)]),
    ("USB: tether continues to the hub input (left edge)", BLUE, [(106, 66), (106, 52), (86, 52), (84, 49), (14, 49), (14, 66), (21, 66)]),
    ("USB: encoder (drops back-centre) -> hub", BLUE, [(140, 219), (163, 219), (165.5, 204)]),
    ("USB: T-Display (drops front-right) + Pico -> hub", BLUE, [(242, 60), (242, 55), (169, 55), (167, 60), (167, 66)]),
    ("I2C Pico -> LIS3DH", PINK, [(201, 118), (214, 118)]),
]
COVER_TIES = [  # (x, y, cable direction deg) - slot runs ACROSS the cable
    (170, 141, 90), (170, 100, 90),            # main 12 V / trunk down the right avenue
    (140, 64, 0),                              # USB bundle heading to the hub ports
    (14, 60, 90),                              # 5 V + tether USB turning up the left avenue to the hub input
    (14, 100, 90), (70, 180, 0),               # left avenue + behind the hub: sol L, NC-L
    (242, 100, 90),                            # right side: sol R
    (205, 204, 0), (150, 219, 0),              # back street: tether + marquee USB; encoder USB drop
    (242, 70, 90),                             # T-Display USB drop
    (108, 95, 90),                             # exciter + audio up to the amp
]
CASE_RUNS = [
    ("button harness R (B1-B6, start, flipper R) -> encoder", "#d33", [(160, 150), (156, 176), (147, 180)]),
    ("cluster wires gather", "#d33", [(158, 72), (158, 150)]),
    ("start + flipper R -> encoder", "#d33", [(211, 189), (198, 178), (156, 176)]),
    ("button harness L (coin, flipper L, joystick) -> encoder", "#d33", [(43, 186), (100, 180), (107, 180)]),
    ("joystick harness", "#d33", [(86, 116), (96, 120), (100, 178)]),
    ("NC-L -> drop D2", ORG, [(43, 184), (45, 180)]),
    ("NC-R + 12 V -> drop D1 (J1)", ORG, [(211, 194), (198, 190)]),
    ("T-Display USB -> drop D4", BLUE, [(209, 32), (228, 32), (242, 45), (242, 60)]),
    ("encoder USB (soldered, exits the back) -> drop D5", BLUE, [(127, 223), (140, 223)]),
]
CASE_TIES = [(152, 178, 180), (100, 180, 0), (52, 186, 0), (198, 178, 150), (95, 125, 80), (228, 40, 45)]


def inflate(s, c):
    return ("box", s[1] - c, s[2] + c, s[3] - c, s[4] + c) if s[0] == "box" else ("cyl", s[1], s[2], s[3] + c)


def inside(s, x, y):
    return (s[1] <= x <= s[2] and s[3] <= y <= s[4]) if s[0] == "box" else math.hypot(x - s[1], y - s[2]) <= s[3]


def check(layer, obs, runs, ties):
    errs = []
    for name, _, pts in runs:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 1.0))
            for k in range(1, n):                      # skip the exact endpoints (they touch the terminal)
                x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                if not (INNER[0] <= x <= INNER[2] and INNER[1] <= y <= INNER[3]):
                    errs.append(f"{layer}: run '{name}' leaves the case at ({x:.0f},{y:.0f})"); break
                hit = [on for on, s in obs if inside(inflate(s, RUN_CLEAR), x, y)]
                hit = [h for h in hit if not any(inside(inflate(s, 2), p[0], p[1]) for on, s in obs if on == h for p in (pts[0], pts[-1]))]
                if hit: errs.append(f"{layer}: run '{name}' hits {hit[0]} at ({x:.0f},{y:.0f})"); break
    for x, y, a in ties:
        ar = math.radians(a)
        for u in (-1, -0.5, 0, 0.5, 1):
            for v in (-1, 0, 1):
                px = x + u * MOUNT[0] / 2 * -math.sin(ar) + v * MOUNT[1] / 2 * math.cos(ar)
                py = y + u * MOUNT[0] / 2 * math.cos(ar) + v * MOUNT[1] / 2 * math.sin(ar)
                if not (INNER[0] + 0.5 <= px <= INNER[2] - 0.5 and INNER[1] + 0.5 <= py <= INNER[3] - 0.5):
                    errs.append(f"{layer}: tie at ({x},{y}) pokes into the wall"); break
                hit = [on for on, s in obs if inside(inflate(s, TIE_CLEAR), px, py)]
                if hit: errs.append(f"{layer}: tie at ({x},{y}) hits {hit[0]}"); break
    return errs


def draw(fname, title, obs, runs, ties, prefix, drops):
    K, M = 3.4, 50
    F = lambda s, b=False: ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial%s.ttf" % (" Bold" if b else ""), s)
    im = Image.new("RGB", (int(W * K) + 2 * M + 330, int(D * K) + 2 * M + 30), "white"); d = ImageDraw.Draw(im)
    P = lambda x, y: (M + x * K, M + (D - y) * K)
    d.rounded_rectangle([M, M, M + W * K, M + D * K], 18, outline="#345", width=3)
    d.text((M, 10), title, font=F(19, True), fill="#111")
    d.text((M + W * K / 2, M - 6), "BACK (ports)", font=F(14, True), fill="#333", anchor="mb")
    d.text((M + W * K / 2, M + D * K + 6), "FRONT (palm rest)", font=F(14, True), fill="#333", anchor="mt")
    for n, s in obs:
        if s[0] == "box":
            d.rectangle([P(s[1], s[4]), P(s[2], s[3])], fill="#eee", outline="#999", width=2); c = P((s[1] + s[2]) / 2, (s[3] + s[4]) / 2)
        else:
            c = P(s[1], s[2]); r = s[3] * K; d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill="#eee", outline="#999", width=2)
        if not n.startswith(("corner", "mid tab", "striker", "exc pillar", "Pico USB", "hub plugs")): d.text(c, n, font=F(12), fill="#333", anchor="mm")
    for name, col, pts in runs:
        d.line([P(*p) for p in pts], fill=col, width=5, joint="curve")
    for k, (x, y, a) in enumerate(ties):
        c = P(x, y); ar = math.radians(a)
        ax, ay = math.cos(ar) * MOUNT[1] / 2 * K, -math.sin(ar) * MOUNT[1] / 2 * K
        bx, by = -math.sin(ar) * MOUNT[0] / 2 * K, -math.cos(ar) * MOUNT[0] / 2 * K
        d.polygon([(c[0] - ax - bx, c[1] - ay - by), (c[0] + ax - bx, c[1] + ay - by), (c[0] + ax + bx, c[1] + ay + by), (c[0] - ax + bx, c[1] - ay + by)],
                  fill="#ff0", outline="#000", width=2)
        d.text((c[0] + 12, c[1] - 16), f"{prefix}{k + 1}", font=F(13, True), fill="#000")
    for lab, (x, y) in drops.items():
        c = P(x, y); d.ellipse([c[0] - 8, c[1] - 8, c[0] + 8, c[1] + 8], outline="#000", width=3)
        d.text((c[0] - 10, c[1] + 10), lab, font=F(12, True), fill="#000", anchor="rt")
    lx, ly = M + W * K + 20, M
    d.text((lx, ly), "Runs", font=F(15, True), fill="#111"); ly += 24
    seen = set()
    for name, col, _ in runs:
        if name in seen: continue
        seen.add(name); d.line([(lx, ly + 8), (lx + 26, ly + 8)], fill=col, width=5)
        for i, part in enumerate([name[j:j + 34] for j in range(0, len(name), 34)]):
            d.text((lx + 34, ly + i * 15), part, font=F(12), fill="#333")
        ly += 16 * max(1, (len(name) + 33) // 34) + 6
    ly += 8; d.rectangle([lx, ly, lx + 22, ly + 16], fill="#ff0", outline="#000", width=2)
    d.text((lx + 30, ly), "zip-tie mount - slot runs ACROSS\nthe cable; tie wraps the bundle", font=F(12), fill="#333")
    ly += 40; d.ellipse([lx + 3, ly, lx + 19, ly + 16], outline="#000", width=3)
    d.text((lx + 30, ly), "drop point: wire goes between\ncase and cover here", font=F(12), fill="#333")
    im.save(fname)


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    errs = check("cover", COVER_OBS, COVER_RUNS, COVER_TIES) + check("case", CASE_OBS, CASE_RUNS, CASE_TIES)
    for e in errs: print("ERROR", e)
    drops = {"D1": (198, 190), "D2": (45, 180), "D3": (100, 30), "D4": (242, 60), "D5": (140, 218)}
    draw("docs/routing_cover.png", "COVER - cable channels and zip-tie mounts (seen from above)", COVER_OBS, COVER_RUNS, COVER_TIES, "C", drops)
    draw("docs/routing_case.png", "CASE - under the top panel (seen from above, through the panel)", CASE_OBS, CASE_RUNS, CASE_TIES, "T", drops)
    json.dump({"cover": [dict(x=x, y=y, angle=a) for x, y, a in COVER_TIES],
               "case": [dict(x=x, y=y, angle=a) for x, y, a in CASE_TIES]}, open("print/tie_points.json", "w"), indent=1)
    with open("model/tie_points.scad", "w") as f:
        f.write("// GENERATED by docs/cable_router.py - do not edit by hand. [x, y, cable direction deg] in case coords\n")
        f.write("tie_cover = " + json.dumps([[x, y, a] for x, y, a in COVER_TIES]) + ";\n")
        f.write("tie_case  = " + json.dumps([[x, y, a] for x, y, a in CASE_TIES]) + ";\n")
    print(f"cover: {len(COVER_RUNS)} runs, {len(COVER_TIES)} ties | case: {len(CASE_RUNS)} runs, {len(CASE_TIES)} ties | {len(errs)} errors")
    sys.exit(1 if errs else 0)
