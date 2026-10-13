# ============================================================
#  "How it all connects" overview: one card per part (with its
#  Blender thumbnail from images/part_*.png), labels beside the
#  wires, arrows for the direction of power and signals.
#      python tools/make_overview.py
#  Writes images/overview.svg and images/overview.png (PNG needs
#  Chrome or Edge).
# ============================================================
import base64, io, os, shutil, subprocess, tempfile
from xml.sax.saxutils import escape as E
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
W, H = 1900, 1390
TOP = 120                                # room for the title

COL = {"power": "#d62828", "data": "#1c64d6", "ctrl": "#e07b00", "usb": "#7b3fbf", "button": "#1f9d55", "audio": "#0aa3b5"}

def thumb(name, size=170):
    im = Image.open(os.path.join(IMG, f"part_{name}.png")).convert("RGB")
    bg = Image.new("RGB", im.size, im.getpixel((2, 2)))
    bbox = ImageChops.difference(im, bg).point(lambda v: 255 if v > 12 else 0).getbbox() or (0, 0) + im.size
    im = im.crop(bbox)
    im.thumbnail((size * 2, size * 2))
    sq = Image.new("RGB", (max(im.size),) * 2, im.getpixel((1, 1)))
    sq.paste(im, ((sq.width - im.width) // 2, (sq.height - im.height) // 2))
    buf = io.BytesIO(); sq.resize((size * 2, size * 2)).save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def icon(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

PC = icon('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#eef1fb"/>'
          '<rect x="14" y="18" width="72" height="48" rx="4" fill="#2b2f3a"/><rect x="19" y="23" width="62" height="38" fill="#7aa0e8"/>'
          '<rect x="44" y="66" width="12" height="10" fill="#2b2f3a"/><rect x="30" y="76" width="40" height="5" rx="2" fill="#2b2f3a"/></svg>')
BRICK = icon('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#fbeeee"/>'
             '<rect x="18" y="30" width="54" height="36" rx="6" fill="#2b2b2e"/><path d="M72 48 C 84 48 84 70 92 72" stroke="#2b2b2e" stroke-width="4" fill="none"/>'
             '<text x="45" y="54" font-family="Segoe UI" font-size="14" fill="#fff" text-anchor="middle" font-weight="bold">12V</text></svg>')
ISO = icon('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#e9f6f7"/>'
           '<rect x="20" y="30" width="60" height="40" rx="6" fill="#0e7c86"/><rect x="8" y="42" width="14" height="16" fill="#bbb"/>'
           '<rect x="78" y="42" width="14" height="16" fill="#bbb"/><path d="M50 32 L50 68" stroke="#fff" stroke-width="3" stroke-dasharray="5 4"/></svg>')

o = []
def t(x, y, s, size=18, col="#222", anchor="start", bold=False, mono=False):
    fam = "Consolas,monospace" if mono else "Segoe UI,Arial,sans-serif"
    o.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{col}" text-anchor="{anchor}"'
             f'{" font-weight=\"bold\"" if bold else ""}>{E(s)}</text>')

def card(x0, y0, x1, y1, title, sub, img=None, tint="#ffffff"):
    o.append(f'<rect x="{x0 + 4}" y="{y0 + 6}" width="{x1 - x0}" height="{y1 - y0}" rx="16" fill="#000" opacity="0.06"/>')
    o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="16" fill="{tint}" stroke="#c9ccd6" stroke-width="2"/>')
    tx = x0 + 24
    if img:
        s = min(y1 - y0 - 24, 150)
        o.append(f'<clipPath id="c{x0}{y0}"><rect x="{x0 + 12}" y="{y0 + 12}" width="{s}" height="{s}" rx="10"/></clipPath>')
        o.append(f'<image href="{img}" x="{x0 + 12}" y="{y0 + 12}" width="{s}" height="{s}" clip-path="url(#c{x0}{y0})" preserveAspectRatio="xMidYMid slice"/>')
        tx = x0 + 12 + s + 16
    my = y0 + min(y1 - y0, 174) / 2
    t(tx, my - 6, title, 21, "#111", bold=True)
    for k, line in enumerate(sub.split("\n")):
        t(tx, my + 20 + k * 21, line, 15, "#555")

def wire(pts, kind, dashed=False, arrow=False, w=5):
    d = "M" + " L".join(f"{x} {y}" for x, y in pts)
    extra = ' stroke-dasharray="14 10"' if dashed else ""
    mk = ' marker-end="url(#arr_%s)"' % kind if arrow else ""
    o.append(f'<path d="{d}" fill="none" stroke="#fafbfc" stroke-width="{w + 10}" stroke-linejoin="round"/>')
    o.append(f'<path d="{d}" fill="none" stroke="{COL[kind]}" stroke-width="{w}" stroke-linejoin="round"{extra}{mk}/>')

def tag(x, y, s, kind):
    wpx = len(s) * 8.4 + 18
    o.append(f'<rect x="{x - wpx / 2}" y="{y - 17}" width="{wpx}" height="26" rx="13" fill="#fff" stroke="{COL[kind]}" stroke-width="1.5"/>')
    t(x, y + 2, s, 15, COL[kind], "middle", True)

# ---------- wires first (cards drawn over their ends) ----------
# outside: PC USB + 12 V supply -> the tether -> IN socket
wire([(40, 105), (18, 105), (18, 560), (34, 560)], "usb", arrow=True)
wire([(210, 380), (210, 476)], "power", arrow=True); tag(210, 428, "12 V, 6 A+", "power")
# USB chain: IN -> isolator -> hub
wire([(210, 630), (210, 714)], "usb", arrow=True); tag(210, 672, "USB (pins 5-8)", "usb")
wire([(210, 850), (210, 934)], "usb", arrow=True)
# 12 V bus out of the IN socket
wire([(380, 520), (470, 520)], "power")
wire([(470, 300), (470, 1000)], "power")
wire([(470, 300), (554, 300)], "power", arrow=True)
wire([(470, 520), (554, 520)], "power", arrow=True)
wire([(470, 1000), (386, 1000)], "power", arrow=True); tag(442, 1100, "12→5 V buck", "power")
wire([(470, 300), (470, 12), (1490, 12), (1490, 300), (1534, 300)], "power", arrow=True); tag(1240, 12, "12 V out on the DMD socket", "power")
tag(470, 410, "12 V bus", "power")
# USB from the hub
wire([(380, 1050), (510, 1050)], "usb")
wire([(510, 105), (510, 1180)], "usb")
wire([(510, 105), (554, 105)], "usb", arrow=True)
wire([(510, 785), (554, 785)], "usb", arrow=True)
wire([(510, 1025), (554, 1025)], "usb", arrow=True)
wire([(510, 1180), (1490, 1180), (1490, 560), (1534, 560)], "usb", arrow=True)
wire([(1700, 1180), (1700, 1106)], "usb", arrow=True)
wire([(1490, 1180), (1700, 1180)], "usb")
tag(1000, 1180, "USB from the hub", "usb")
# controls, flippers, sound, nudge
wire([(1080, 105), (906, 105)], "button", arrow=True); tag(990, 87, "buttons + joystick", "button")
wire([(730, 170), (730, 244)], "ctrl", arrow=True); tag(730, 208, "flipper → TRIG", "ctrl")
wire([(900, 315), (1074, 315)], "power", arrow=True); tag(990, 297, "12 V, 0.1 s", "power")
wire([(900, 535), (1074, 535)], "audio", arrow=True); tag(990, 517, "speaker", "audio")
wire([(730, 720), (730, 606)], "audio", arrow=True); tag(730, 664, "line out", "audio")
wire([(900, 1025), (1074, 1025)], "data"); tag(990, 1007, "I²C", "data")

# ---------- cards ----------
card(40, 40, 380, 170, "PC", "Visual Pinball X,\nRetroBat …", PC, "#f4f6fd")
card(40, 250, 380, 380, "12 V supply", "≥ 6 A, plus the PC's USB,\non one GX16 tether", BRICK, "#fdf4f4")
card(40, 480, 380, 630, "IN socket", "GX16-8: 12 V + USB", thumb("gx16"))
card(40, 720, 380, 850, "USB isolator", "breaks the ground loop\n480 Mbps", ISO, "#eef8f8")
card(40, 940, 380, 1100, "7-port USB hub", "inside, on the cover", thumb("hub"))
card(560, 40, 900, 170, "Zero-delay encoder", "the game controller", thumb("encoder"))
card(560, 250, 900, 380, "2 timer relays", "XY-J02, 0.1 s pulse", thumb("relays"))
card(560, 470, 900, 600, "Amplifier", "XH-M543 (TPA3116)", thumb("amp"))
card(560, 720, 900, 850, "USB sound card", "PCM2704 + ground-\nloop isolator", thumb("dac"))
card(560, 960, 900, 1100, "Raspberry Pi Pico", "runs Pinscape Pico:\nnudge as a gamepad", thumb("pico"))
card(1080, 40, 1420, 170, "Buttons + joystick", "6 + coin/start + 2 flippers", thumb("buttons"))
card(1080, 250, 1420, 380, "2 solenoids", "JF-1039 knock on\neach flip", thumb("solenoids"))
card(1080, 470, 1420, 600, "Exciter", "50 mm, under the palms:\nyou feel the table", thumb("exciter"))
card(1080, 960, 1420, 1100, "LIS3DH", "accelerometer\n(nudge + tilt)", thumb("lis3dh"))
card(1540, 250, 1860, 620, "LED marquee", "2 × 64 × 32 panels\n+ ESP32 (ZeDMD)\nslides onto the back", thumb("marquee", 200))
card(1540, 960, 1860, 1100, "T-Display-S3", "status: nudge,\ncoil heat, tilt", thumb("tdisplay"))

# ---------- title, legend ----------
head = [f'<rect width="{W}" height="{H}" fill="#fafbfc"/>']
for k, c in COL.items():
    head.append(f'<marker id="arr_{k}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
                f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>')
o2 = o; o = head
t(40, 48, "Pinball controller — how it all connects", 30, "#111", bold=True)
t(40, 78, "Overview only — exact terminals and wire colours are in the Step 3 wiring pictures.", 17, "#666")
leg = [("power", "12 V power (arrow = direction)"), ("usb", "USB"), ("button", "buttons"), ("ctrl", "flipper trigger"),
       ("audio", "sound"), ("data", "I²C")]
for i, (k, s) in enumerate(leg):
    x = 40 + i * 300; y = H - 32
    o.append(f'<line x1="{x}" y1="{y}" x2="{x + 36}" y2="{y}" stroke="{COL[k]}" stroke-width="6" stroke-linecap="round"/>')
    t(x + 46, y + 6, s, 16, "#333")
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>'
       + "".join(x for x in o if x.startswith("<marker")) + "</defs>"
       + "".join(x for x in o if not x.startswith("<marker"))
       + f'<g transform="translate(0,{TOP})">' + "".join(o2) + "</g></svg>")
out = os.path.join(IMG, "overview.svg")
open(out, "w", encoding="utf-8").write(svg)
print("wrote images/overview.svg")

exe = next((p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome") if os.path.exists(p)),
           shutil.which("chromium") or shutil.which("google-chrome"))
if exe:
    tmp = tempfile.mkdtemp()
    html = os.path.join(tmp, "o.html")
    open(html, "w", encoding="utf-8").write(
        f'<html><body style="margin:0"><img src="file:///{out.replace(os.sep, "/")}" width="{W}"></body></html>')
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={W},{H}",
                    f"--screenshot={os.path.join(IMG, 'overview.png')}", "file:///" + html.replace(os.sep, "/")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote images/overview.png")
