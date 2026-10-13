#!/usr/bin/env python3
"""Mock pinball DMD show for the marquee (128x32): writes dmd_demo.raw (RGB888 frames, 30 fps) for zedmd_play.
Classic orange DMD look: everything is drawn in grey levels, then quantised to 4 dot brightnesses and tinted orange."""
import math, random
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H, FPS = 128, 32, 30
FB = "/System/Library/Fonts/Supplemental/"
big = ImageFont.truetype(FB + "Arial Black.ttf", 21)
mid = ImageFont.truetype(FB + "Arial Bold.ttf", 14)
small = ImageFont.truetype(FB + "Verdana Bold.ttf", 8)
ORANGE = (255, 88, 0)
frames = []

def canvas(): return Image.new("L", (W, H), 0)
def text(img, xy, s, font, fill=255, anchor="la"): ImageDraw.Draw(img).text(xy, s, font=font, fill=fill, anchor=anchor)
def push(img, n=1, color=ORANGE):
    q = img.point(lambda v: 0 if v < 40 else 85 if v < 110 else 170 if v < 190 else 255)   # 4 dot levels, like a real DMD
    rgb = Image.merge("RGB", [q.point(lambda v, c=c: v * c // 255) for c in color])
    frames.extend([rgb.tobytes()] * n)

# 1. title slides in, sparkle, subtitle
for i in range(40):
    im = canvas(); x = int(W - (W + 4) * min(1, i / 28) ** 0.6) + 2
    text(im, (x + 62, 13), "PINBALL", big, anchor="mm"); push(im)
for i in range(45):
    im = canvas(); text(im, (64, 12), "PINBALL", big, anchor="mm")
    text(im, (64, 28), "CONTROLLER", small, fill=170 if (i // 6) % 2 else 255, anchor="mm")
    d = ImageDraw.Draw(im); random.seed(i)
    for _ in range(6): d.point((random.randrange(W), random.randrange(H)), fill=255)
    push(im)
# 2. game screen: player / ball / counting score
score = 0
for i in range(150):
    score += random.Random(i).choice([10, 50, 100, 250, 1000, 5000]) * (25 if i % 37 == 0 else 1)
    im = canvas(); text(im, (1, 0), "PLAYER 1", small); text(im, (127, 0), "BALL 1", small, anchor="ra")
    text(im, (64, 21), f"{score:,}", big, anchor="mm"); push(im)
# 3. JACKPOT: expanding rings then flashing text
for i in range(36):
    im = canvas(); d = ImageDraw.Draw(im)
    for k in range(3):
        r = (i * 3 + k * 14) % 70
        d.ellipse([64 - r * 1.6, 16 - r / 2, 64 + r * 1.6, 16 + r / 2], outline=255 - k * 70)
    push(im)
for i in range(60):
    im = canvas(); on = (i // 5) % 2 == 0
    text(im, (64, 15), "JACKPOT!", big, fill=255 if on else 120, anchor="mm")
    if on:
        d = ImageDraw.Draw(im); [d.line([(64, 16), (64 + 70 * math.cos(a), 16 + 30 * math.sin(a))], fill=85) for a in [j * math.pi / 8 + i * 0.1 for j in range(16)]]
        text(im, (64, 15), "JACKPOT!", big, anchor="mm")
    push(im)
for i in range(50):
    im = canvas(); text(im, (64, 9), "JACKPOT", mid, anchor="mm"); text(im, (64, 24), "5,000,000", mid, fill=255 if i % 10 < 7 else 110, anchor="mm"); push(im)
# 4. high scores scroll up
lines = ["HIGH SCORES", "1. MRK  48,210,550", "2. AAA  31,870,100", "3. PIN  22,415,300", "4. DMD  19,000,000", "GRAND CHAMPION", "MRK"]
for y in range(0, len(lines) * 11 + 34, 1):
    im = canvas()
    for k, s in enumerate(lines): text(im, (64, 34 + k * 11 - y), s, small, anchor="mt")
    push(im, 2)
# 5. insert coins / free play blink
for i in range(90):
    im = canvas(); text(im, (64, 10), "INSERT COINS" if (i // 15) % 2 == 0 else "FREE PLAY", mid, anchor="mm")
    text(im, (64, 26), "PRESS START", small, fill=255 if (i // 8) % 2 else 0, anchor="mm"); push(im)
# 6. wipe out
for i in range(32):
    im = canvas(); text(im, (64, 15), "FREE PLAY", mid, anchor="mm")
    ImageDraw.Draw(im).rectangle([0, 32 - i, W, H], fill=0); push(im)
Path(__file__).with_name("dmd_demo.raw").write_bytes(b"".join(frames))
print(len(frames), "frames,", round(len(frames) / FPS, 1), "s")
