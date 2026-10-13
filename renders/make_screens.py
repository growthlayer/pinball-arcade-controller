# Screen images for the renders: the marquee showing a frame of the neon show (LED-dot look)
# and the T-Display status screen.   python renders/make_screens.py
import os, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "synthwave"))
import render as R
BUILD = os.path.join(ROOT, "renders", "build"); os.makedirs(BUILD, exist_ok=True)

for name, fn, t in [("marquee_title", R.scene_pinball_title, 2.6), ("marquee_sunset", R.scene_sunset, 3.0)]:
    R.led_preview(R.frame_of(fn, t), scale=10).save(os.path.join(BUILD, name + ".png"))

# T-Display-S3 status screen, 320 x 170 (landscape)
im = Image.new("RGB", (320, 170), (6, 8, 16)); d = ImageDraw.Draw(im)
f = lambda s, b=False: ImageFont.truetype("segoeuib.ttf" if b else "segoeui.ttf", s)
d.text((10, 6), "TABLE", font=f(13, True), fill=(0, 200, 255))
d.text((10, 22), "Attack from Mars", font=f(22, True), fill=(255, 255, 255))
d.text((10, 58), "NUDGE", font=f(13, True), fill=(0, 200, 255))
cx, cy, r = 62, 112, 40
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(60, 90, 140), width=2)
d.line([cx - r, cy, cx + r, cy], fill=(40, 60, 100)); d.line([cx, cy - r, cx, cy + r], fill=(40, 60, 100))
d.ellipse([cx + 14 - 7, cy - 9 - 7, cx + 14 + 7, cy - 9 + 7], fill=(255, 210, 40))
d.text((122, 58), "FLIPPER COIL HEAT", font=f(13, True), fill=(0, 200, 255))
for i, (lab, v, col) in enumerate([("L", 0.35, (60, 220, 90)), ("R", 0.55, (240, 200, 40))]):
    y = 82 + i * 30
    d.text((122, y), lab, font=f(16, True), fill="white")
    d.rectangle([142, y + 3, 310, y + 19], outline=(70, 80, 100))
    d.rectangle([144, y + 5, 144 + int(164 * v), y + 17], fill=col)
d.text((122, 142), "CLEAR", font=f(16, True), fill=(60, 220, 90))
im.save(os.path.join(BUILD, "tdisplay.png"))
print("screens written to", BUILD)
