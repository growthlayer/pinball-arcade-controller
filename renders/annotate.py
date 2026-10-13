# Put the transparent Blender renders on the page colour; number the exploded view and the
# cover layout. Run after render.py:   python renders/annotate.py <repo root>
import json, os, sys, glob
from PIL import Image, ImageDraw, ImageFont
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
IMG = os.path.join(ROOT, "images"); BUILD = os.path.join(ROOT, "renders", "build")
BG = (245, 245, 247); RED = (220, 60, 40)

# one numbering for the exploded view, the layout and the README parts list
NAMES = {1: "Case (printed)", 2: "Cover - the electronics plate (printed)", 3: "Marquee trays + plate (printed)",
         4: "6 action buttons + coin / start", 5: "2 flipper buttons (side walls)", 6: "Joystick",
         7: "Zero-delay USB encoder", 8: "50 mm exciter (under the panel)", 9: "T-Display-S3 status screen",
         10: "XH-M543 amplifier", 11: "2 x XY-J02 timer relays", 12: "2 x JF-1039 solenoids",
         13: "7-port USB hub", 14: "PCM2704 USB sound card", 15: "Raspberry Pi Pico (Pinscape)",
         16: "LIS3DH accelerometer", 17: "2 x P2.5 64x32 LED panels", 18: "2 x GX16-8 sockets (IN, DMD)"}

def font(bold, size):
    return ImageFont.truetype("segoeuib.ttf" if bold else "segoeui.ttf", size)

def flatten(src, dst):
    im = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", im.size, BG + (255,))
    Image.alpha_composite(bg, im).convert("RGB").save(dst, optimize=True)

def badge(d, x, y, n, r=21):
    d.ellipse([x - r, y - r, x + r, y + r], fill=RED, outline="white", width=3)
    d.text((x, y), str(n), font=font(True, 22), fill="white", anchor="mm")

def key(d, x, y, n, w):
    d.ellipse([x, y + 4, x + 30, y + 34], fill=RED)
    d.text((x + 15, y + 19), str(n), font=font(True, 17), fill="white", anchor="mm")
    d.text((x + 42, y + 2), NAMES[n], font=font(False, 25), fill=(40, 40, 40))

for f in ["hero", "render_top", "render_rear", "cutaway"] + [os.path.basename(p)[:-4] for p in glob.glob(os.path.join(IMG, "part_*.png"))]:
    p = os.path.join(IMG, f + ".png")
    if os.path.exists(p) and Image.open(p).mode == "RGBA":
        flatten(p, p)

raw = os.path.join(IMG, "exploded_raw.png")
if os.path.exists(raw):
    pts = {int(k): v for k, v in json.load(open(os.path.join(BUILD, "callouts.json"))).items()}
    src = Image.open(raw).convert("RGBA")
    l, t, r, b = src.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    m = 70; l, t, r, b = max(l - m, 0), max(t - m, 0), min(r + m, src.width), min(b + m, src.height)
    base = Image.alpha_composite(Image.new("RGBA", src.size, BG + (255,)), src).convert("RGB").crop((l, t, r, b))
    TOP = 520; Wd = max(base.width, 1400)
    im = Image.new("RGB", (Wd, base.height + TOP), BG); ox = (Wd - base.width) // 2; im.paste(base, (ox, TOP))
    d = ImageDraw.Draw(im)
    for n, (x, y) in pts.items():
        badge(d, x - l + ox, y - t + TOP, n)
    d.text((60, 40), "Pinball controller - exploded view", font=font(True, 40), fill=(30, 30, 30))
    shown = sorted(pts)
    for i, n in enumerate(shown):
        half = (len(shown) + 1) // 2
        cx, cy = (60 if i < half else Wd // 2 + 30), 110 + (i % half) * 44
        key(d, cx, cy, n, im.width)
    im.save(os.path.join(IMG, "exploded.png"), optimize=True)
    os.remove(raw)

raw = os.path.join(IMG, "layout_raw.png")
if os.path.exists(raw):
    pts = {int(k): v for k, v in json.load(open(os.path.join(BUILD, "layout_callouts.json"))).items()}
    src = Image.open(raw).convert("RGBA")
    l, t, r, b = src.getchannel("A").point(lambda a: 255 if a > 200 else 0).getbbox()
    m = 60; l, t, r, b = max(l - m, 0), max(t - m, 0), min(r + m, src.width), min(b + m, src.height)
    bg = Image.new("RGBA", src.size, BG + (255,))
    base = Image.alpha_composite(bg, src).convert("RGB").crop((l, t, r, b))
    TOP, KEY = 110, 230
    im = Image.new("RGB", (max(base.width, 1200), base.height + TOP + KEY), BG); im.paste(base, ((im.width - base.width) // 2, TOP))
    d = ImageDraw.Draw(im)
    for n, (x, y) in pts.items():
        badge(d, x - l + (im.width - base.width) // 2, y + TOP - t, n)
    d.text((40, 30), "The cover - every board, seen from above (front edge at the bottom)", font=font(True, 34), fill=(30, 30, 30))
    y0 = TOP + base.height + 20
    for i, n in enumerate(sorted(pts)):
        key(d, 40 + (i // 4) * (im.width // 2), y0 + (i % 4) * 44, n, im.width)
    im.save(os.path.join(IMG, "layout_cover.png"), optimize=True)
    os.remove(raw)
print("annotated")
