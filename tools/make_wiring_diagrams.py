# ============================================================
#  Pictorial wiring diagrams: every component drawn as it looks,
#  wires routed on a grid - straight runs, square corners, a bridge
#  where two wires cross, a dot where wires join.
#  Two sets, each with a complete page and one page per step (the
#  other wires faded) plus a connection chart on the right:
#    images/wiring.svg, wiring_1_power.svg ... wiring_6_nudge.svg   (the controller)
#    images/wiring_marquee.svg                                     (the marquee module)
#  and PNGs of each if Chrome or Edge is installed.
#      python tools/make_wiring_diagrams.py
# ============================================================
import heapq, os, shutil, subprocess, tempfile
from xml.sax.saxutils import escape as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "images")
G = 23                                      # routing grid pitch (px)
COLS, ROWS = 120, 80
TOP = 190                                   # room for the title and the step text
PANEL = 820                                 # connection chart on the right

C = dict(red="#d62828", blk="#222222", org="#f08c00", blu="#1c64d6", grn="#1f9d55", olv="#7a8b1e",
         pur="#8e44ad", brn="#9c5a1c", yel="#e9c400", usb="#7d7d85", wht="#b9b9c2", gry="#8a8a8a", cyn="#0aa3b5")

def px(i):
    return i * G

def dims():
    W = COLS * G
    H = TOP + ROWS * G + 90
    return W, H, W + PANEL

# ---------------- component drawing helpers ----------------
pins = {}                                   # name -> (col, row, dcol, drow)
labels = {}                                 # name -> words for the connection chart
boxes = []                                  # obstacles in px (x0, y0, x1, y1)
NOGO = set()                                # extra blocked grid cells
DIRS = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}

def pin(name, c, r, d, label=None):
    pins[name] = (c, r) + DIRS[d]
    labels[name] = label or name

def box(x0, y0, x1, y1):
    boxes.append((x0, y0, x1, y1))

def rect(o, x, y, w, h, fill, stroke="#333", rx=8, sw=2):
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

def t(o, x, y, s, size=16, col="#222", anchor="middle", bold=False, mono=False):
    fam = "Consolas,monospace" if mono else "Segoe UI,Arial,sans-serif"
    o.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{col}" text-anchor="{anchor}"'
             f'{" font-weight=\"bold\"" if bold else ""}>{E(s)}</text>')

def gold(o, x, y, s=14, on=True):
    o.append(f'<rect x="{x - s / 2}" y="{y - s / 2}" width="{s}" height="{s}" fill="{"#c9a227" if on else "#ccc"}" stroke="#7a6212" stroke-width="1"/>')

def block(o, c0, r0, c1, r1, fill, stroke, title, sub=(), tcol="#fff", scol=None, title_row=None, size=20):
    """a component body on the grid, with a title and sub-lines; registers it as an obstacle"""
    x0, y0, x1, y1 = px(c0), px(r0), px(c1), px(r1)
    rect(o, x0, y0, x1 - x0, y1 - y0, fill, stroke, 10, 3); box(x0, y0, x1, y1)
    ty = px(title_row) if title_row is not None else (y0 + y1) / 2 - 8 * len(sub)
    t(o, (x0 + x1) / 2, ty, title, size, tcol, bold=True)
    for k, s in enumerate(sub):
        t(o, (x0 + x1) / 2, ty + 24 + k * 20, s, 14, scol or tcol)
    return x0, y0, x1, y1

def side_pins(o, prefix, c, rows, d, names, pretty, col_on="#fff", size=14, square=14):
    """pins along one edge: c = edge column, rows = row per pin, d = 'L'/'R'/'U'/'D' (wire leaves this way)"""
    for r, n in zip(rows, names):
        x, y = px(c), px(r)
        gold(o, x, y, square)
        if d in "LR":
            inward = -1 if d == "R" else 1
            t(o, x + inward * 14, y + 5, n, size, col_on, "end" if d == "R" else "start", True, True)
        pin(f"{prefix}.{n}", c, r, d, f"{pretty} {n}")

def side_pins_h(o, prefix, r, cols, d, names, pretty, col_on="#fff", size=13):
    for c, n in zip(cols, names):
        x, y = px(c), px(r)
        gold(o, x, y, 14)
        inward = 1 if d == "U" else -1
        t(o, x, y + inward * 26 + (4 if inward > 0 else 0), n, size, col_on, "middle", True, True)
        pin(f"{prefix}.{n}", c, r, d, f"{pretty} {n}")

# ================= the controller =================
GX_NAMES = ["1 +12V", "2 +12V", "3 0V", "4 0V", "5 VBUS", "6 D-", "7 D+", "8 GND"]

def gx16(o, prefix, c0, r0, edge, title, sub):
    """GX16-8 socket seen from the solder-cup side; pins 1-8 on one edge (edge = 'R' or 'L'), pitch 2 rows"""
    c1 = c0 + 11
    x0, y0, x1, y1 = px(c0), px(r0), px(c1), px(r0 + 18)
    rect(o, x0, y0, x1 - x0, y1 - y0, "#3b3f46", "#16181b", 12, 3); box(x0, y0, x1, y1)
    cx, cy = (x0 + x1) / 2 + (-40 if edge == "R" else 40), y0 + 150
    o.append(f'<circle cx="{cx}" cy="{cy}" r="78" fill="#b9bcc2" stroke="#666" stroke-width="3"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="60" fill="#2a2a2a"/>')
    import math
    for k in range(7):
        a = math.radians(-90 + 360 / 7 * k + 25)
        o.append(f'<circle cx="{cx + 40 * math.cos(a):.1f}" cy="{cy + 40 * math.sin(a):.1f}" r="7" fill="#d9b44a"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="#d9b44a"/>')
    t(o, cx, y1 - 72, title, 17, "#fff", bold=True)
    for k, s in enumerate(sub):
        t(o, cx, y1 - 48 + k * 19, s, 12, "#cfd3da")
    rows = [r0 + 1 + 2 * k for k in range(8)]
    side_pins(o, prefix, c1 if edge == "R" else c0, rows, edge, GX_NAMES, title.split(" (")[0], size=13)

def lever_bar(o, prefix, c0, r0, r1, colour, title, left_rows, right_rows):
    """a row of lever connectors joined together = one bus. Pins L<k> on the left edge, R<k> on the right."""
    x0, y0, x1, y1 = px(c0), px(r0), px(c0 + 2), px(r1)
    rect(o, x0, y0, x1 - x0, y1 - y0, "#f3f3f3", "#888", 6); box(x0, y0, x1, y1)
    for r in range(r0 + 1, r1, 2):
        o.append(f'<rect x="{x0 + 8}" y="{px(r) - 8}" width="{x1 - x0 - 16}" height="16" rx="3" fill="{colour}"/>')
    t(o, (x0 + x1) / 2, y0 - 10, title, 14, "#333", bold=True)
    for k, r in enumerate(left_rows):
        pin(f"{prefix}.L{k}", c0, r, "L", title)
    for k, r in enumerate(right_rows):
        pin(f"{prefix}.R{k}", c0 + 2, r, "R", title)

def relay(o, prefix, c0, r0, side):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 16, r0 + 10, "#1d4fa8", "#0c2f6f", f"XY-J02 timer relay — {side}",
                           ("mode P1.1, OP 00.1 (0.1 s)",), "#fff", "#cdd9f5", title_row=r0 + 3)
    rect(o, x0 + 120, y0 + 120, 120, 50, "#111", "#000", 4)
    t(o, x0 + 180, y0 + 156, "00.1", 30, "#ff3b2f", bold=True, mono=True)
    side_pins(o, prefix, c0, [r0 + 2, r0 + 4, r0 + 6, r0 + 8], "L", ["+", "-", "TRIG", "GND"], f"{side} relay")
    side_pins(o, prefix, c0 + 16, [r0 + 3, r0 + 5, r0 + 7], "R", ["NO", "COM", "NC"], f"{side} relay")

def solenoid(o, prefix, c0, r0, side):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 14, r0 + 8, "#6e7480", "#3c4048", f"Solenoid {side} — JF-1039 12 V",
                           (), "#fff", title_row=r0 + 2)
    rect(o, x0 + 70, y0 + 70, 160, 44, "#2546a8", "#122a6b", 6)
    o.append(f'<rect x="{x0 + 230}" y="{y0 + 86}" width="70" height="12" fill="#c9ccd1"/>')
    # flyback diode symbol across the coil, band (cathode) toward +
    dx, dy = x0 + 46, y0 + 92
    o.append(f'<path d="M{dx - 14} {dy - 26} L {dx + 14} {dy - 26} L {dx} {dy + 2} Z" fill="#222" transform="rotate(180 {dx} {dy - 12})"/>')
    o.append(f'<line x1="{dx - 14}" y1="{dy - 28}" x2="{dx + 14}" y2="{dy - 28}" stroke="#fff" stroke-width="5"/>')
    t(o, x0 + 150, y1 - 14, "1N5408 across the coil — band (cathode) to +", 13, "#eee")
    side_pins(o, prefix, c0, [r0 + 3, r0 + 6], "L", ["+", "-"], f"{side} solenoid")

def amp(o, c0, r0):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 18, r0 + 18, "#1f4aa0", "#0c2f6f", "XH-M543 amplifier",
                           ("TPA3116D2 · left channel only", "L trimmer ~ 1/3 to start"), "#fff", "#cdd9f5", title_row=r0 + 8)
    rect(o, x0 + 150, y0 + 250, 120, 80, "#151515", "#000", 4)
    side_pins(o, "amp", c0, [r0 + 2, r0 + 4], "L", ["VIN+", "GND"], "amp")
    side_pins(o, "amp", c0, [r0 + 12, r0 + 14, r0 + 16], "L", ["IN L", "IN G", "IN R"], "amp")
    side_pins(o, "amp", c0 + 18, [r0 + 4, r0 + 6], "R", ["L+", "L-"], "amp OUT")

def exciter(o, c0, r0):
    x0, y0, x1, y1 = px(c0), px(r0), px(c0 + 10), px(r0 + 8)
    rect(o, x0, y0, x1 - x0, y1 - y0, "#2a2a2e", "#111", 12, 3); box(x0, y0, x1, y1)
    cx, cy = x0 + 140, (y0 + y1) / 2
    o.append(f'<circle cx="{cx}" cy="{cy}" r="62" fill="#111" stroke="#555" stroke-width="3"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="34" fill="#b9bcc2"/>')
    t(o, cx, y1 - 10, "50 mm exciter 4 Ω", 14, "#ddd", bold=True)
    side_pins(o, "exc", c0, [r0 + 3, r0 + 5], "L", ["+", "-"], "exciter", size=14)

def buck(o, c0, r0):
    block(o, c0, r0, c0 + 8, r0 + 7, "#6b4fa0", "#3e2a68", "12→5 V buck", ("feeds the hub",), "#fff", "#e3d9f5",
          title_row=r0 + 3)
    side_pins_h(o, "buck", r0, [c0 + 2, c0 + 6], "U", ["IN+", "IN-"], "hub buck")
    side_pins(o, "buck", c0, [r0 + 5], "L", ["OUT+"], "hub buck")
    side_pins(o, "buck", c0 + 8, [r0 + 5], "R", ["OUT-"], "hub buck")

def hub(o, c0, r0):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 14, r0 + 24, "#1f7a3a", "#0f4f24", "7-port USB hub",
                           ("FE2.1, 84 × 44", "5 V jack: wires soldered"), "#fff", "#cfe8d4", title_row=r0 + 11)
    side_pins_h(o, "hub", r0, [c0 + 4], "U", ["UP"], "hub upstream")
    side_pins(o, "hub", c0 + 14, [r0 + 2, r0 + 4], "R", ["5V+", "5V-"], "hub 5 V jack")
    for k, n in enumerate(["P1", "P2", "P3", "P4", "P5"]):
        r = r0 + 14 + 2 * k
        rect(o, x1 - 34, px(r) - 10, 30, 20, "#c8c8cc", "#666", 3)
        pin(f"hub.{n}", c0 + 14, r, "R", f"hub port {k + 1}")
    rect(o, x0 + 4, px(r0 + 18) - 10, 30, 20, "#c8c8cc", "#666", 3)
    pin("hub.P0", c0, r0 + 18, "L", "hub port 6")

def usb_socket(o, c0, r0):
    block(o, c0, r0, c0 + 8, r0 + 9, "#2a2a2e", "#111", "USB-A female", ("on the tether's", "USB wires"), "#fff", "#bbb",
          title_row=r0 + 4, size=16)
    side_pins_h(o, "usba", r0, [c0 + 1, c0 + 3, c0 + 5, c0 + 7], "U", ["G", "D+", "D-", "V"], "USB-A socket", size=12)
    pin("usba.out", c0 + 4, r0 + 9, "D", "USB-A socket")

def isolator(o, c0, r0):
    block(o, c0, r0, c0 + 9, r0 + 7, "#0e7c86", "#06464c", "USB isolator", ("480 Mbps (ADuM3165)",), "#fff", "#c8f0f3",
          title_row=r0 + 3, size=17)
    pin("iso.in", c0 + 4, r0, "U", "USB isolator IN")
    pin("iso.out", c0 + 4, r0 + 7, "D", "USB isolator OUT")

def encoder(o, c0, r0):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 10, r0 + 36, "#1f7a3a", "#0f4f24", "Zero-delay", ("USB encoder",),
                           "#fff", "#cfe8d4", title_row=r0 + 17)
    t(o, (x0 + x1) / 2, px(r0 + 20), "(slot names as", 12, "#cfe8d4"); t(o, (x0 + x1) / 2, px(r0 + 20) + 16, "printed on the back)", 12, "#cfe8d4")
    for k, (n, _) in enumerate(CONTROLS):
        r = r0 + 2 + 3 * k
        gold(o, x0, px(r), 14)
        t(o, x0 + 14, px(r) + 5, n, 13, "#fff", "start", True, True)
        pin(f"enc.{n}", c0, r, "L", f"encoder {n}")
    for n, r in (("ST mid", r0 + 6), ("SE mid", r0 + 10)):
        gold(o, x1, px(r), 14)
        t(o, x1 - 14, px(r) + 5, n, 13, "#ffe08a", "end", True, True)
        pin(f"enc.{n}", c0 + 10, r, "R", f"encoder {n.split()[0]} slot middle pin")
    rect(o, x1 - 34, px(r0 + 30) - 12, 30, 24, "#c8c8cc", "#666", 3)
    pin("enc.usb", c0 + 10, r0 + 30, "R", "encoder USB (soldered cable)")

CONTROLS = [("JOY", "Joystick (5-pin lead)"), ("K3", "Bottom row, left"), ("K4", "Top row, left"),
            ("L1", "Bottom row, middle"), ("R1", "Top row, middle"), ("L2", "Bottom row, right"),
            ("R2", "Top row, right"), ("SE", "Right flipper"), ("ST", "Left flipper"),
            ("K11", "Coin"), ("K12", "Start")]

def controls(o, c0, r0):
    t(o, px(c0), px(r0) - 26, "Panel buttons — each on its 3-wire lead", 14, "#444", "start", True)
    for k, (slot, name) in enumerate(CONTROLS):
        r = r0 + 2 + 3 * k
        cx, cy = px(c0 + 2), px(r)
        fill = "#ffd23f" if "flipper" in name else "#e33" if name in ("Coin", "Start") else "#ddd"
        if slot == "JOY":
            o.append(f'<circle cx="{cx}" cy="{cy}" r="26" fill="#c22" stroke="#811" stroke-width="3"/>')
        else:
            o.append(f'<circle cx="{cx}" cy="{cy}" r="26" fill="{fill}" stroke="#888" stroke-width="3"/>')
        box(cx - 28, cy - 28, cx + 28, cy + 28)
        t(o, cx + 40, cy - 10, name, 13, "#333", "start", True)
        pin(f"btn.{slot}", c0 + 4, r, "R", name)

def dac(o, c0, r0):
    block(o, c0, r0, c0 + 9, r0 + 5, "#202024", "#000", "PCM2704 USB DAC", (), "#fff", title_row=r0 + 3, size=16)
    pin("dac.usb", c0, r0 + 2, "L", "sound card USB")
    pin("dac.out", c0 + 9, r0 + 2, "R", "sound card 3.5 mm out")

def gli(o, c0, r0):
    block(o, c0, r0, c0 + 8, r0 + 8, "#3a3a40", "#111", "Ground-loop", ("isolator 3.5 mm",), "#fff", "#ccc",
          title_row=r0 + 3, size=15)
    pin("gli.in", c0, r0 + 2, "L", "ground-loop isolator IN")
    side_pins(o, "gli", c0 + 8, [r0 + 4, r0 + 6, r0 + 8], "R", ["L", "G", "R"], "isolator lead (3.5 mm → bare)", size=12)

def pico(o, c0, r0):
    block(o, c0, r0, c0 + 14, r0 + 14, "#1f7a3a", "#0f4f24", "Pi Pico", ("Pinscape Pico", "pins up"),
          "#fff", "#cfe8d4", title_row=r0 + 11)
    pin("pico.usb", c0, r0 + 11, "L", "Pico micro-USB")
    side_pins(o, "pico", c0 + 14, [r0 + 2, r0 + 4, r0 + 6, r0 + 8], "R", ["GP4 (6)", "GP5 (7)", "3V3 (36)", "GND (38)"],
              "Pico", size=13)

def lis3dh(o, c0, r0):
    block(o, c0, r0, c0 + 9, r0 + 14, "#5b2a86", "#2e1150", "LIS3DH", ("accelerometer", "3.3 V only"), "#fff", "#e3d0f5",
          title_row=r0 + 6)
    side_pins(o, "lis", c0, [r0 + 1, r0 + 3, r0 + 5, r0 + 7, r0 + 9, r0 + 11], "L",
              ["SDA", "SCL", "VCC", "GND", "CS", "SDO"], "LIS3DH", size=13)

def tdisplay(o, c0, r0):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 12, r0 + 8, "#111", "#000", "", (), "#fff")
    rect(o, x0 + 30, y0 + 20, x1 - x0 - 60, 110, "#06080f", "#333", 4)
    t(o, (x0 + x1) / 2, y0 + 70, "T-Display-S3", 18, "#0cf", bold=True)
    t(o, (x0 + x1) / 2, y0 + 96, "status screen", 13, "#9ab")
    t(o, (x0 + x1) / 2, y1 - 14, "USB-C solder breakout", 12, "#bbb")
    pin("td.usb", c0, r0 + 4, "L", "T-Display (USB-C breakout)")

def usb_pigtail(o, c0, r0):
    block(o, c0, r0, c0 + 7, r0 + 9, "#2a2a2e", "#111", "USB-A", ("plug pigtail",), "#fff", "#bbb", title_row=r0 + 4, size=16)
    pin("pig.in", c0, r0 + 8, "L", "USB-A pigtail (in a hub port)")
    side_pins(o, "pig", c0 + 7, [r0 + 1, r0 + 3, r0 + 5, r0 + 7], "R", ["red", "white", "green", "black"], "USB-A pigtail",
              size=12)

def controller_components(o):
    gx16(o, "in", 1, 2, "R", "IN (tether)", ("12 V + USB from the PC end",))
    lever_bar(o, "p12", 30, 1, 13, "#d62828", "+12 V", [2, 4, 8, 10], [2, 4, 6, 8, 10, 12])
    lever_bar(o, "gnd", 30, 16, 28, "#222", "0 V", [17, 19, 23, 25], [17, 19, 21, 23, 25, 27])
    relay(o, "rl", 42, 2, "LEFT")
    relay(o, "rr", 42, 16, "RIGHT")
    solenoid(o, "sl", 68, 2, "LEFT")
    solenoid(o, "sr", 68, 16, "RIGHT")
    buck(o, 46, 33)
    amp(o, 72, 31)
    exciter(o, 102, 33)
    usb_socket(o, 14, 23)
    isolator(o, 14, 35)
    hub(o, 36, 48)
    encoder(o, 12, 46)
    controls(o, 1, 46)
    dac(o, 60, 64)
    gli(o, 76, 62)
    pico(o, 87, 50)
    lis3dh(o, 112, 50)
    tdisplay(o, 60, 50)
    usb_pigtail(o, 94, 68)
    gx16(o, "dmd", 111, 66, "L", "DMD (marquee)", ("12 V + USB to the marquee",))

CONTROLLER_WIRES = [
    # 3.1 power
    ("in.1 +12V", "p12.L0", "red", "power", "12V"), ("in.2 +12V", "p12.L1", "red", "power", "12V"),
    ("in.3 0V", "gnd.L0", "blk", "power", "GND"), ("in.4 0V", "gnd.L1", "blk", "power", "GND"),
    ("p12.R0", "rl.+", "red", "power", "12V"), ("p12.R1", "rl.COM", "red", "power", "12V"),
    ("p12.R2", "rr.+", "red", "power", "12V"), ("p12.R3", "rr.COM", "red", "power", "12V"),
    ("p12.R4", "amp.VIN+", "red", "power", "12V"), ("p12.R5", "buck.IN+", "red", "power", "12V"),
    ("gnd.R0", "rl.-", "blk", "power", "GND"), ("gnd.R1", "rr.-", "blk", "power", "GND"),
    ("gnd.R4", "amp.GND", "blk", "power", "GND"), ("gnd.R5", "buck.IN-", "blk", "power", "GND"),
    ("buck.OUT+", "hub.5V+", "red", "power", "5VH"), ("buck.OUT-", "hub.5V-", "blk", "power", "GNDH"),
    ("dmd.1 +12V", "p12.L2", "red", "power", "12V"), ("dmd.2 +12V", "p12.L3", "red", "power", "12V"),
    ("dmd.3 0V", "gnd.L2", "blk", "power", "GND"), ("dmd.4 0V", "gnd.L3", "blk", "power", "GND"),
    # 3.2 flippers
    ("enc.ST mid", "rl.TRIG", "org", "flippers", "TRIGL"), ("enc.SE mid", "rr.TRIG", "org", "flippers", "TRIGR"),
    ("rl.GND", "rl.-", "blk", "flippers", "GND"), ("rr.GND", "rr.-", "blk", "flippers", "GND"),
    ("rl.NO", "sl.+", "pur", "flippers", "SOLL"), ("rr.NO", "sr.+", "pur", "flippers", "SOLR"),
    ("sl.-", "gnd.R2", "blk", "flippers", "GND"), ("sr.-", "gnd.R3", "blk", "flippers", "GND"),
    # 3.3 controls
] + [(f"btn.{s}", f"enc.{s}", "gry", "controls", f"B{s}") for s, _ in CONTROLS] + [
    # 3.4 USB
    ("in.5 VBUS", "usba.V", "red", "usb", "TV"), ("in.6 D-", "usba.D-", "wht", "usb", "TDM"),
    ("in.7 D+", "usba.D+", "grn", "usb", "TDP"), ("in.8 GND", "usba.G", "blk", "usb", "TG"),
    ("usba.out", "iso.in", "usb", "usb", "U1"), ("iso.out", "hub.UP", "usb", "usb", "U2"),
    ("hub.P0", "enc.usb", "usb", "usb", "U3"), ("hub.P1", "td.usb", "usb", "usb", "U4"),
    ("hub.P2", "dac.usb", "usb", "usb", "U5"), ("hub.P3", "pico.usb", "usb", "usb", "U6"),
    ("hub.P4", "pig.in", "usb", "usb", "U7"),
    ("pig.red", "dmd.5 VBUS", "red", "usb", "DV"), ("pig.white", "dmd.6 D-", "wht", "usb", "DDM"),
    ("pig.green", "dmd.7 D+", "grn", "usb", "DDP"), ("pig.black", "dmd.8 GND", "blk", "usb", "DG"),
    # 3.5 sound
    ("dac.out", "gli.in", "usb", "sound", "A1"),
    ("gli.L", "amp.IN L", "wht", "sound", "AL"), ("gli.G", "amp.IN G", "blk", "sound", "AG"),
    ("gli.R", "amp.IN R", "red", "sound", "AR"),
    ("amp.L+", "exc.+", "cyn", "sound", "SP+"), ("amp.L-", "exc.-", "blk", "sound", "SP-"),
    # 3.6 nudge
    ("pico.GP4 (6)", "lis.SDA", "blu", "nudge", "SDA"), ("pico.GP5 (7)", "lis.SCL", "pur", "nudge", "SCL"),
    ("pico.3V3 (36)", "lis.VCC", "org", "nudge", "3V3"), ("pico.GND (38)", "lis.GND", "blk", "nudge", "G3"),
    ("lis.CS", "lis.VCC", "org", "nudge", "3V3"), ("lis.SDO", "lis.GND", "blk", "nudge", "G3"),
]

CONTROLLER_STEPS = {"power": "3.1  Power", "flippers": "3.2  Flipper solenoids", "controls": "3.3  Buttons + joystick",
                    "usb": "3.4  USB", "sound": "3.5  Sound (exciter)", "nudge": "3.6  Nudge"}

CONTROLLER_PAGES = [
    ("wiring", None, "Pinball controller — complete wiring",
     "Every connection inside the box. Colours are a suggestion; what matters is which terminal goes where.", None),
    ("wiring_1_power", "power", "Step 3.1 — Power",
     "12 V arrives on the IN socket (pins 1-2 +12 V, 3-4 0 V) and is shared out on two lever-connector bars.",
     ["1. IN pins 1 + 2 → +12 V bar; pins 3 + 4 → 0 V bar (18-20 AWG; two pins each because a double flip draws ~5 A).",
      "2. +12 V bar → each relay's + and COM, the amp's VIN+ and the hub buck's IN+.   0 V bar → each relay's −, the amp GND, the buck IN−.",
      "3. Buck OUT → the hub's 5 V jack (set/check 5.0 V first).   4. DMD socket pins 1-2 / 3-4 → the same bars (12 V out to the marquee)."]),
    ("wiring_2_flippers", "flippers", "Step 3.2 — Flipper solenoids",
     "Each flipper button's own encoder signal triggers a timer relay; the relay fires its solenoid for 0.1 s.",
     ["1. Solder a wire to the MIDDLE pin of the encoder's ST slot (left flipper) and SE slot (right flipper) — 0 V at rest, 5 V pressed.",
      "2. ST middle → LEFT relay TRIG, SE middle → RIGHT relay TRIG.   3. On each relay, jumper its GND screw to its − screw.",
      "4. Relay NO → solenoid +;  solenoid − → 0 V bar.   5. 1N5408 across each solenoid, band (cathode) on +.  COM is already on +12 V."]),
    ("wiring_3_controls", "controls", "Step 3.3 — Buttons and joystick",
     "Standard zero-delay encoder wiring: each button's 3-wire lead into its slot, the joystick's 5-wire lead into its header.",
     ["Slot names are printed on the back of the encoder.  The flipper buttons go in the side walls: LEFT → ST, RIGHT → SE.",
      "Top row (back, left → right) K4 / R1 / R2;  bottom row K3 / L1 / L2;  coin K11, start K12.  K1 and K2 stay free."]),
    ("wiring_4_usb", "usb", "Step 3.4 — USB",
     "The tether's USB pins become a USB-A socket; the isolator breaks the ground loop between the PC and the 12 V side.",
     ["1. IN pins 5-8 → a USB-A female (red V, white D−, green D+, black G).   2. USB isolator → the hub's upstream port.",
      "3. Hub ports: encoder (soldered cable), T-Display, sound card, Pico, and a USB-A plug pigtail whose 4 wires go to DMD pins 5-8.",
      "Never skip the isolator: without it the solenoid current shares the USB ground and kills hubs."]),
    ("wiring_5_sound", "sound", "Step 3.5 — Sound for the exciter",
     "The PC sends table sounds to the USB sound card; the amp drives the exciter under the palm rest.",
     ["1. Sound card 3.5 mm → ground-loop isolator → 3.5 mm-to-bare lead: white = L, red = R, black = GND → the amp's input plug.",
      "2. Amp OUT L+ / L− → exciter + / −.  Only the left channel is used.   3. Start with the L trimmer about a third up."]),
    ("wiring_6_nudge", "nudge", "Step 3.6 — Nudge (accelerometer)",
     "Pinscape Pico reads the LIS3DH over I²C. 3.3 V only — nothing on the module's 5 V pin.",
     ["Pico 3V3 (36) → VCC, GND (38) → GND, GP4 (6) → SDA, GP5 (7) → SCL.   On the module: CS → VCC (selects I²C), SDO → GND (address 0x18).",
      "Mount the module square to the box; the config maps its axes."]),
]

CONTROLLER_LEGEND = [("red", "+12 V / +5 V"), ("blk", "0 V / GND"), ("org", "trigger / 3.3 V"), ("pur", "relay → solenoid / SCL"),
                     ("cyn", "speaker"), ("wht", "audio L / USB D−"), ("grn", "USB D+"), ("blu", "I²C SDA"),
                     ("gry", "button lead"), ("usb", "USB / 3.5 mm cable")]

# ================= the marquee =================
HUB75 = [("R1", "25"), ("G1", "26"), ("B1", "27"), ("GND", "GND"), ("R2", "14"), ("G2", "12"), ("B2", "13"), ("E", None),
         ("A", "23"), ("B", "19"), ("C", "5"), ("D", "17"), ("CLK", "16"), ("LAT", "4"), ("OE", "15"), ("GND2", "GND2")]

def esp32(o, c0, r0):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 18, r0 + 38, "#1d2a3a", "#0b121b", "ESP32 (WROOM-32)",
                           ("runs ZeDMD", "powered by its USB only"), "#fff", "#b9c7d8", title_row=r0 + 18)
    rect(o, px(c0 + 4) - 24, y1 - 30, 48, 26, "#c8c8cc", "#666", 4)
    pin("esp.usb", c0 + 4, r0 + 38, "D", "ESP32 USB")
    names = [g for _, g in HUB75 if g]
    rows = [r0 + 2 + 2 * k for k in range(len(names))]
    for r, n in zip(rows, names):
        gold(o, x1, px(r), 13)
        lab = f"GPIO {n}" if n.isdigit() else "GND"
        t(o, x1 - 14, px(r) + 5, lab, 13, "#fff", "end", True, True)
        pin(f"esp.{n}", c0 + 18, r, "R", f"ESP32 {lab}")

def panel(o, prefix, c0, r0, name, hub_in=True):
    x0, y0, x1, y1 = block(o, c0, r0, c0 + 26, r0 + 36, "#151515", "#000", name, ("P2.5 64 × 32 HUB75",), "#fff", "#aaa",
                           title_row=r0 + 32)
    for k in range(10):
        for j in range(5):
            o.append(f'<circle cx="{x0 + 260 + k * 26}" cy="{y0 + 70 + j * 26}" r="7" fill="#ff2975" opacity="0.8"/>')
    if hub_in:
        rect(o, x0 + 6, y0 + 20, 90, px(2 + 2 * 16) - 4, "#f2f2f2", "#999", 4)
        for k, (n, _) in enumerate(HUB75):
            r = r0 + 2 + 2 * k
            gold(o, x0, px(r), 13)
            t(o, x0 + 14, px(r) + 5, f"{k + 1} {n.rstrip('2') if n == 'GND2' else n}", 12, "#333", "start", True, True)
            pin(f"{prefix}.{n}", c0, r, "L", f"{name} J1 pin {k + 1} ({'GND' if n == 'GND2' else n})")
    pin(f"{prefix}.pwr+", c0 + 22, r0 + 36, "D", f"{name} POWER +5 V")
    pin(f"{prefix}.pwr-", c0 + 24, r0 + 36, "D", f"{name} POWER GND")
    t(o, px(c0 + 23), y1 - 8, "POWER", 12, "#f66", bold=True)
    pin(f"{prefix}.J2", c0 + 26, r0 + 4, "R", f"{name} J2 (out)")

def mq_buck(o, c0, r0):
    block(o, c0, r0, c0 + 12, r0 + 8, "#555a63", "#222", "12 → 5 V converter, 10 A", ("set / check 5.0 V first",),
          "#fff", "#ddd", title_row=r0 + 3, size=17)
    side_pins(o, "mb", c0, [r0 + 5, r0 + 7], "L", ["IN+", "IN-"], "converter")
    side_pins(o, "mb", c0 + 12, [r0 + 5, r0 + 7], "R", ["OUT+", "OUT-"], "converter")

def usbc_breakout(o, c0, r0):
    block(o, c0, r0, c0 + 7, r0 + 9, "#2a2a2e", "#111", "USB-C", ("solder", "breakout"), "#fff", "#bbb", title_row=r0 + 4, size=16)
    side_pins(o, "ucb", c0, [r0 + 1, r0 + 3, r0 + 5, r0 + 7], "L", ["V", "D-", "D+", "G"], "USB-C breakout", size=12)
    pin("ucb.out", c0 + 4, r0, "U", "USB-C breakout")

def marquee_components(o):
    gx16(o, "mq", 1, 44, "R", "DMD (marquee end)", ("link cable from the case",))
    usbc_breakout(o, 20, 47)
    esp32(o, 12, 3)
    panel(o, "p1", 46, 3, "LED panel 1 — LEFT")
    panel(o, "p2", 82, 3, "LED panel 2 — RIGHT", hub_in=False)
    pin("p2.J1", 82, 7, "L", "panel 2 J1 (in)")
    t(o, px(46) + 110, px(3 + 2 + 2 * 7) + 5, "← E: leave open", 12, "#c00", "start", True)
    mq_buck(o, 66, 47)

MARQUEE_WIRES = [
    ("mq.1 +12V", "mb.IN+", "red", "power", "12V"), ("mq.2 +12V", "mb.IN+", "red", "power", "12V"),
    ("mq.3 0V", "mb.IN-", "blk", "power", "GND"), ("mq.4 0V", "mb.IN-", "blk", "power", "GND"),
    ("mb.OUT+", "p1.pwr+", "red", "power", "5V"), ("mb.OUT+", "p2.pwr+", "red", "power", "5V"),
    ("mb.OUT-", "p1.pwr-", "blk", "power", "G5"), ("mb.OUT-", "p2.pwr-", "blk", "power", "G5"),
    ("mq.5 VBUS", "ucb.V", "red", "usb", "UV"), ("mq.6 D-", "ucb.D-", "wht", "usb", "UDM"),
    ("mq.7 D+", "ucb.D+", "grn", "usb", "UDP"), ("mq.8 GND", "ucb.G", "blk", "usb", "UG"),
    ("ucb.out", "esp.usb", "usb", "usb", "USB"),
    ("p1.J2", "p2.J1", "usb", "data", "RIB"),
] + [(f"esp.{g}", f"p1.{n}", "blk" if g.startswith("GND") else "org" if n in ("R1", "G1", "B1", "R2", "G2", "B2") else "blu",
       "data", f"H{n}") for n, g in HUB75 if g]

MARQUEE_PAGES = [
    ("wiring_marquee", None, "Marquee — wiring",
     "Inside the marquee trays, seen from the front with the panels out. One GX16-8 cable from the case brings 12 V and USB.",
     ["Socket pins 1-2 / 3-4 → the 10 A converter's IN.  Converter OUT → the panels' supplied power harness (one plug per panel).",
      "Pins 5-8 → USB-C solder breakout → ESP32.  The ESP32 runs on its USB only.  Panel 1 J2 → panel 2 J1 with the supplied ribbon.",
      "16 jumpers ESP32 → panel 1 J1 (ZeDMD classic map).  Leave E (pin 8) unconnected.  Keep the panels' 12 V up whenever the USB is plugged in."]),
]
MARQUEE_STEPS = {"power": "Power", "usb": "USB", "data": "Panel data (HUB75)"}
MARQUEE_LEGEND = [("red", "+12 V / +5 V"), ("blk", "0 V / GND"), ("org", "HUB75 colour"), ("blu", "HUB75 row / clock"),
                  ("wht", "USB D−"), ("grn", "USB D+"), ("usb", "USB / ribbon")]

# ---------------- grid router ----------------
BEND, CROSS, NEAR_BOX, SHARE, CLASH = 4.0, 30.0, 1.5, 0.15, 2000.0

def route_all():
    blocked = set()
    near = set()
    for (x0, y0, x1, y1) in boxes:
        for c in range(COLS):
            for r in range(ROWS):
                x, y = px(c), px(r)
                if x0 - 6 <= x <= x1 + 6 and y0 - 6 <= y <= y1 + 6:
                    blocked.add((c, r))
                elif x0 - G - 6 <= x <= x1 + G + 6 and y0 - G - 6 <= y <= y1 + G + 6:
                    near.add((c, r))
    blocked |= NOGO
    stub = {}                                   # stub cell -> net
    for a, b, col, grp, net in WIRES:
        for p in (a, b):
            c, r, dc, dr = pins[p]
            stub[(c + dc, r + dr)] = net
            blocked.discard((c + dc, r + dr))
    occ = {}                                    # cell -> {net: set("h"/"v"/"x" for bend/end)}

    def add(path, net, on=True):
        for k, cell in enumerate(path):
            marks = set()
            if k > 0:
                marks.add("h" if path[k - 1][1] == cell[1] else "v")
            if k + 1 < len(path):
                marks.add("h" if path[k + 1][1] == cell[1] else "v")
            if len(marks) > 1 or k in (0, len(path) - 1):
                marks.add("x")
            d = occ.setdefault(cell, {})
            if on:
                d.setdefault(net, [set(), 0])
                d[net][0] |= marks; d[net][1] += 1
            else:
                d[net][1] -= 1
                if d[net][1] == 0:
                    del d[net]

    def astar(a, b, net):
        ca, ra, dca, dra = pins[a]
        cb, rb, dcb, drb = pins[b]
        s, g = (ca + dca, ra + dra), (cb + dcb, rb + drb)
        start_dir = (dca, dra)
        end_dir = (-dcb, -drb)                  # direction of travel into pin b
        h = lambda cell: abs(cell[0] - g[0]) + abs(cell[1] - g[1])
        best = {(s, start_dir): 0.0}
        prev = {}
        pq = [(h(s), 0.0, s, start_dir)]
        while pq:
            f, cost, cell, d = heapq.heappop(pq)
            if cost > best.get((cell, d), 1e18):
                continue
            if cell == g:
                tot = cost + (BEND if d != end_dir else 0)
                final = (cell, d)
                # accept the first goal pop (bend into the pin is small vs. alternatives)
                path = [cell]
                st = final
                while st in prev:
                    st = prev[st]; path.append(st[0])
                return path[::-1], tot
            others = {n: v for n, v in occ.get(cell, {}).items() if n != net}
            for nd in DIRS.values():
                if nd == (-d[0], -d[1]):
                    continue
                nc = (cell[0] + nd[0], cell[1] + nd[1])
                if not (0 <= nc[0] < COLS and 0 <= nc[1] < ROWS) or nc in blocked:
                    continue
                if nc in stub and stub[nc] != net:
                    continue
                o2 = {n: v for n, v in occ.get(nc, {}).items() if n != net}
                orient = "h" if nd[1] == 0 else "v"
                step = 1.0
                if nd != d and others:          # bending on a cell another wire uses
                    step += CLASH
                if o2:
                    if any(orient in v[0] or "x" in v[0] for v in o2.values()):
                        step += CLASH           # would run along / touch another wire
                    else:
                        step += CROSS
                if net in occ.get(nc, {}):
                    step = min(step, SHARE + (CROSS if o2 else 0))
                if nc in near:
                    step += NEAR_BOX
                if nd != d:
                    step += BEND
                nc_cost = cost + step
                if nc_cost < best.get((nc, nd), 1e18):
                    best[(nc, nd)] = nc_cost
                    prev[(nc, nd)] = (cell, d)
                    heapq.heappush(pq, (nc_cost + h(nc), nc_cost, nc, nd))
        raise RuntimeError(f"no route {a} -> {b}")

    def manhattan(w):
        a, b = pins[w[0]], pins[w[1]]
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    order = sorted(range(len(WIRES)), key=lambda i: manhattan(WIRES[i]))
    paths = {}
    for i in order:
        a, b, col, grp, net = WIRES[i]
        paths[i], _ = astar(a, b, net)
        add(paths[i], net)
    for _ in range(4):                          # rip up and reroute
        for i in order:
            a, b, col, grp, net = WIRES[i]
            add(paths[i], net, False)
            paths[i], _ = astar(a, b, net)
            add(paths[i], net)
    clashes = 0
    for cell, d in occ.items():
        if len(d) > 1:
            marks = [v[0] for v in d.values()]
            if any("x" in m for m in marks) or sum("h" in m for m in marks) > 1 or sum("v" in m for m in marks) > 1:
                clashes += 1; print("clash at", cell, list(d))
    print("clashes:", clashes)
    return paths, occ

# ---------------- drawing ----------------
def polyline(i, path):
    a, b = WIRES[i][0], WIRES[i][1]
    ca, ra, _, _ = pins[a]; cb, rb, _, _ = pins[b]
    pts = [(ca, ra)] + list(path) + [(cb, rb)]
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        p0, p1, p2 = out[-1], pts[k], pts[k + 1]
        if (p0[0] == p1[0] == p2[0]) or (p0[1] == p1[1] == p2[1]):
            continue
        out.append(p1)
    out.append(pts[-1])
    return [(px(c), px(r)) for c, r in out]

def path_d(pts, hops, R=10, HR=9):
    """Square route with rounded corners; hops = list of (x, y) where this wire bridges another."""
    d = f"M{pts[0][0]} {pts[0][1]}"
    n = len(pts)
    for k in range(1, n):
        (x0, y0), (x1, y1) = pts[k - 1], pts[k]
        horiz = y0 == y1
        sgn = 1 if (x1 > x0 if horiz else y1 > y0) else -1
        # segment start/end trimmed for the corners
        s0 = (x0, y0) if k == 1 else ((x0 + sgn * R, y0) if horiz else (x0, y0 + sgn * R))
        e1 = (x1, y1) if k == n - 1 else ((x1 - sgn * R, y1) if horiz else (x1, y1 - sgn * R))
        hs = [(hx, hy) for hx, hy in hops if (hy == y0 and min(x0, x1) + R + HR < hx < max(x0, x1) - R - HR) if horiz]
        hs += [(hx, hy) for hx, hy in hops if (not horiz and hx == x0 and min(y0, y1) + R + HR < hy < max(y0, y1) - R - HR)]
        hs.sort(key=lambda p: sgn * (p[0] if horiz else p[1]))
        for hx, hy in hs:
            if horiz:
                d += f" L {hx - sgn * HR} {hy} A {HR} {HR} 0 0 {1 if sgn > 0 else 0} {hx + sgn * HR} {hy}"
            else:
                d += f" L {hx} {hy - sgn * HR} A {HR} {HR} 0 0 {1 if sgn > 0 else 0} {hx} {hy + sgn * HR}"
        d += f" L {e1[0]} {e1[1]}"
        if k < n - 1:
            x2, y2 = pts[k + 1]
            nx = (x1 + (R if x2 > x1 else -R), y1) if y1 == y2 else (x1, y1 + (R if y2 > y1 else -R))
            d += f" Q {x1} {y1} {nx[0]} {nx[1]}"
    return d

def segments(pts):
    return [(pts[k - 1], pts[k]) for k in range(1, len(pts))]

def crossings(pa, pb):
    """Points where a segment of pa crosses a segment of pb at right angles (interiors only)."""
    out = []
    for (a0, a1) in segments(pa):
        for (b0, b1) in segments(pb):
            ha, hb = a0[1] == a1[1], b0[1] == b1[1]
            if ha == hb:
                continue
            h0, h1, v0, v1 = (a0, a1, b0, b1) if ha else (b0, b1, a0, a1)
            x, y = v0[0], h0[1]
            if min(h0[0], h1[0]) < x < max(h0[0], h1[0]) and min(v0[1], v1[1]) < y < max(v0[1], v1[1]):
                out.append((x, y))
    return out

def junctions(paths):
    dots = []
    bynet = {}
    for i, p in paths.items():
        bynet.setdefault(WIRES[i][4], []).append(i)
    for net, idx in bynet.items():
        if len(idx) < 2:
            continue
        dirs = {}
        for i in idx:
            cells = [pins[WIRES[i][0]][:2]] + paths[i] + [pins[WIRES[i][1]][:2]]
            for k, cell in enumerate(cells):
                for j in (k - 1, k + 1):
                    if 0 <= j < len(cells):
                        dirs.setdefault(cell, set()).add((cells[j][0] - cell[0], cells[j][1] - cell[1]))
        for cell, ds in dirs.items():
            if len(ds) >= 3:
                dots.append((px(cell[0]), px(cell[1]), WIRES[idx[0]][2], net))
    return dots


# ---------------- connection chart ----------------
def chart(focus, steps, H):
    W = COLS * G
    o = []
    x0 = W + 10
    rect(o, x0, 20, PANEL - 40, H - 130, "#ffffff", "#d6d6dc", 12, 2)
    t(o, x0 + 24, 64, "Connections" + ("" if not focus else " — this step"), 28, "#111", "start", True)
    t(o, x0 + 24, 94, "from  →  to", 18, "#666", "start")
    y = 112
    groups = [focus] if focus else list(steps)
    n_rows = sum(1 for w in WIRES if w[3] in groups) + (len(groups) * 1.3 if not focus else 0)
    RH = min(38, max(22, (H - 260) / max(n_rows, 1)))
    fs = 18 if RH >= 30 else 15
    for g in groups:
        if not focus:
            y += 8
            t(o, x0 + 24, y + 16, steps[g], fs + 2, "#333", "start", True)
            y += RH
        for k, (a, b, col, grp, net) in enumerate([w for w in WIRES if w[3] == g]):
            if k % 2 == 0:
                o.append(f'<rect x="{x0 + 12}" y="{y}" width="{PANEL - 64}" height="{RH}" fill="#f3f4f7"/>')
            o.append(f'<line x1="{x0 + 24}" y1="{y + RH / 2}" x2="{x0 + 54}" y2="{y + RH / 2}" stroke="{C[col]}" stroke-width="7" stroke-linecap="round"/>')
            t(o, x0 + 66, y + RH / 2 + 6, labels[a], fs, "#111", "start", True)
            t(o, x0 + 400, y + RH / 2 + 6, "→", fs, "#888", "middle")
            t(o, x0 + 418, y + RH / 2 + 6, labels[b], fs, "#222", "start")
            y += RH
    return o

def build(paths, comps, focus, title, subtitle, steps_text, steps, legend):
    W, H, WT = dims()
    o = []
    comps(o)
    polys = {i: polyline(i, p) for i, p in paths.items()}
    on = {i: focus is None or WIRES[i][3] == focus for i in paths}
    order = sorted(paths, key=lambda i: (on[i], WIRES[i][2] == "usb"))
    drawn = []
    for i in order:
        a, b, col, grp, net = WIRES[i]
        hops = []
        for j in drawn:
            if WIRES[j][4] != net:
                hops += crossings(polys[i], polys[j])
        drawn.append(i)
        d = path_d(polys[i], hops)
        w = 10 if col == "usb" else 6
        op = 1.0 if on[i] else 0.12
        o.append(f'<path d="{d}" fill="none" stroke="#fbfbfc" stroke-opacity="{op}" stroke-width="{w + 8}" stroke-linejoin="round"/>')
        o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity="{0.45 * op}" stroke-width="{w + 2.5}" stroke-linejoin="round"/>')
        o.append(f'<path d="{d}" fill="none" stroke="{C[col]}" stroke-opacity="{op}" stroke-width="{w}" stroke-linejoin="round"/>')
        if on[i]:
            for p in (polys[i][0], polys[i][-1]):
                o.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="5" fill="#fff" stroke="{C[col]}" stroke-width="3"/>')
    for x, y, col, net in junctions(paths):
        net_on = any(on[i] for i in paths if WIRES[i][4] == net)
        o.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{C[col]}" stroke="#fff" stroke-width="2" opacity="{1 if net_on else 0.12}"/>')
    head = [f'<rect width="{WT}" height="{H}" fill="#fbfbfc"/>'] + chart(focus, steps, H)
    t(head, 40, 50, title, 34, "#111", "start", True)
    t(head, 40, 84, subtitle, 18, "#555", "start")
    for k, s in enumerate(steps_text or []):
        t(head, 40, 118 + k * 24, s, 16, "#333", "start")
    for k, (c, s) in enumerate(legend):
        x = 40 + (k % 5) * 260; y = H - 62 + (k // 5) * 30
        head.append(f'<line x1="{x}" y1="{y}" x2="{x + 40}" y2="{y}" stroke="{C[c]}" stroke-width="7" stroke-linecap="round"/>')
        t(head, x + 52, y + 6, s, 16, "#333", "start")
    t(head, W - 40, H - 32, "bridge = wires cross, not joined     dot = wires joined", 16, "#555", "end")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WT}" height="{H}" viewBox="0 0 {WT} {H}">'
            + "".join(head) + f'<g transform="translate(0,{TOP})">' + "".join(o) + "</g></svg>")

def browser():
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.exists(p):
            return p
    return shutil.which("chromium") or shutil.which("google-chrome")

def run_set(comps, wires, pages, steps, legend, cols, rows):
    global WIRES, COLS, ROWS
    WIRES, COLS, ROWS = wires, cols, rows
    pins.clear(); labels.clear(); boxes.clear(); NOGO.clear()
    comps([])
    paths, _ = route_all()
    W, H, WT = dims()
    exe = browser()
    tmp = tempfile.mkdtemp(prefix="pbwire_")
    for name, focus, title, sub, steps_text in pages:
        svg = os.path.join(OUT, name + ".svg")
        open(svg, "w", encoding="utf-8").write(build(paths, comps, focus, title, sub, steps_text, steps, legend))
        print("wrote images/" + name + ".svg")
        if exe:
            html = os.path.join(tmp, name + ".html")
            open(html, "w", encoding="utf-8").write(
                f'<html><body style="margin:0"><img src="file:///{svg.replace(os.sep, "/")}" width="{WT}"></body></html>')
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={WT},{H}",
                            f"--screenshot={os.path.join(OUT, name + '.png')}", "file:///" + html.replace(os.sep, "/")],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("wrote images/" + name + ".png")
    shutil.rmtree(tmp, ignore_errors=True)

WIRES = []
if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["controller", "marquee"]
    if "controller" in which:
        run_set(controller_components, CONTROLLER_WIRES, CONTROLLER_PAGES, CONTROLLER_STEPS, CONTROLLER_LEGEND, 126, 86)
    if "marquee" in which:
        run_set(marquee_components, MARQUEE_WIRES, MARQUEE_PAGES, MARQUEE_STEPS, MARQUEE_LEGEND, 112, 62)
