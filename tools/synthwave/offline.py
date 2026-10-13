#!/usr/bin/env python3
"""The marquee's OFFLINE show: what the ESP32 plays by itself whenever the PC isn't talking to it.

Same look as the PC-driven neon show (render.py: sky, sun, grid, chrome, bloom, the CRT / wipe / scanline /
glitch transitions and phosphor afterglow), but every scene says the PC isn't connected - a flickering
NO SIGNAL neon sign, WAITING FOR PC with a radar sweep, an unplugged neon USB lead, and a synthwave
colour-bar NO INPUT screen. tools/synthwave/make_offline_firmware.py turns it into frames for the ESP32.

  python tools/synthwave/offline.py [outdir]     -> LED-look preview GIFs + contact sheet
"""
import math, random, sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render import (W, H, FPS, XX, YY, PINK, HOT, CYAN, PURPLE, YELLOW, RED, WHITE, ORANGE,  # noqa: E402
                    tmask, glow, blit, chrome, seg, poly, disc, ring, bloom, sky, sun, mountains, grid,
                    TRANS, TRANSITIONS, AFTERGLOW, led_preview)

TEAL = (0, 235, 170)


def neon_word(fb, txt, x, y, col, core, size=13, t=0.0, faulty=(), seed=0, spacing=1):
    """a neon-tube word: glow + bright core, letters listed in `faulty` buzz and drop out like a dying tube"""
    cx = x
    for i, ch in enumerate(txt):
        if ch == " ":
            cx += size // 3
            continue
        m = tmask(ch, size=size, spacing=0)
        k = 1.0
        if i in faulty:                                                  # irregular buzz: mostly on, short dropouts
            r = random.Random(int(t * 18) * 131 + i * 7 + seed)
            k = 0.12 if r.random() < 0.22 else (0.65 if r.random() < 0.2 else 1.0)
        g, pad = glow(m, 1.8, 1.7)
        blit(fb, g * k, cx - pad, y - pad, col)
        blit(fb, m * k, cx, y, core)
        cx += m.shape[1] + spacing
    return cx


def word_width(txt, size=13, spacing=1):
    return sum((size // 3) if ch == " " else tmask(ch, size=size, spacing=0).shape[1] + spacing for ch in txt) - spacing


# ------------------------------------------------------------------ scenes (t = seconds inside the scene)
def scene_no_signal(fb, t):
    """the sunset world with the power gone: a cold sun, a slow grid, and a dying NO SIGNAL neon sign"""
    neon = np.zeros_like(fb)
    hz = 21
    sky(fb, t, hz, seed=3, drift=0.3)
    ring(neon, 64, 18, 8, (110, 40, 190), w=1.0, a=0.9)                  # the sun is off: just its outline
    mountains(fb, neon, hz, t, speed=0.6)
    grid(fb, neon, hz, t, speed=0.35, col=PURPLE)
    bloom(fb, neon, 0.8)
    txt = "NO SIGNAL"
    x = (W - word_width(txt)) // 2
    neon_word(fb, txt, x, 2, HOT, (255, 200, 240), t=t, faulty=(4, 7), seed=1)


def scene_waiting(fb, t):
    """WAITING FOR PC with counting dots and a radar beam sweeping the grid for a connection"""
    neon = np.zeros_like(fb)
    hz = 17
    sky(fb, t, hz, seed=9, drift=0.5)
    grid(fb, neon, hz, t, speed=0.8, col=CYAN)
    beam = (t * 0.9) % 1.0                                                # sweep left -> right
    bx = -20 + beam * (W + 40)
    sweep = np.clip(1 - np.abs(XX - bx) / 10, 0, 1) * (YY >= hz)
    neon += np.array((0, 255, 200), np.float32)[None, None] * sweep[..., None] * 0.55
    seg(neon, bx, hz, bx, H, (180, 255, 240), w=1.0)
    bloom(fb, neon, 0.9)
    txt = "WAITING FOR PC"
    m = tmask(txt, size=11, spacing=1)
    h, w = m.shape
    x = (W - w - 9) // 2
    g, pad = glow(m, 1.6, 1.5)
    blit(fb, g * (0.75 + 0.25 * math.sin(t * 3)), x - pad, 2 - pad, CYAN)
    blit(fb, m, x, 2, chrome(h, w))
    for i in range(3):                                                    # . .. ... counting up
        if int(t * 2.5) % 4 > i:
            disc(fb, x + w + 2 + i * 3.2, 2 + h - 3, 0.9, (220, 255, 250))


def scene_unplugged(fb, t):
    """a neon USB lead that keeps reaching for its socket - sparks, but no connection"""
    neon = np.zeros_like(fb)
    sky(fb, t, H + 2, seed=21, drift=0.2)
    fb *= 0.7
    cy = 22
    gap = 5 + 9 * (0.5 + 0.5 * math.sin(t * 2.1))                        # plug drifts in and out
    sx = 76                                                              # socket face
    px = sx - gap                                                        # plug tip
    # cable from the left edge to the plug, sagging and swaying
    pts = [(-2, cy + 2 + math.sin(t * 1.3) * 1.5), (px - 34, cy + 5), (px - 18, cy + 1), (px - 15, cy)]
    poly(neon, pts, (255, 60, 200), w=1.4)
    # plug: body + metal tip
    seg(neon, px - 15, cy - 3, px - 4, cy - 3, HOT, w=1.0); seg(neon, px - 15, cy + 3, px - 4, cy + 3, HOT, w=1.0)
    seg(neon, px - 15, cy - 3, px - 15, cy + 3, HOT, w=1.0); seg(neon, px - 4, cy - 3, px - 4, cy + 3, HOT, w=1.0)
    seg(neon, px - 4, cy - 2, px, cy - 2, (255, 220, 250), w=1.0); seg(neon, px - 4, cy + 2, px, cy + 2, (255, 220, 250), w=1.0)
    seg(neon, px, cy - 2, px, cy + 2, (255, 220, 250), w=1.0)
    # socket on the right with its cable leaving to the right edge
    for dy in (-4, 4):
        seg(neon, sx, cy + dy, sx + 12, cy + dy, CYAN, w=1.0)
    seg(neon, sx + 12, cy - 4, sx + 12, cy + 4, CYAN, w=1.0)
    seg(neon, sx, cy - 4, sx, cy - 2.5, CYAN, w=1.0); seg(neon, sx, cy + 2.5, sx, cy + 4, CYAN, w=1.0)
    poly(neon, [(sx + 12, cy), (sx + 22, cy + 3), (W + 2, cy + 1 + math.sin(t * 1.1))], (0, 200, 255), w=1.4)
    # sparks jump the gap when it's narrow
    if gap < 8:
        r = random.Random(int(t * 20))
        for _ in range(3):
            y0 = cy + r.uniform(-2, 2)
            pts = [(px + 0.5, y0)] + [(px + gap * f, y0 + r.uniform(-2.5, 2.5)) for f in (0.35, 0.7)] + [(sx - 0.5, cy + r.uniform(-2, 2))]
            poly(neon, pts, (220, 230, 255), w=0.7, a=0.9)
    bloom(fb, neon, 1.0, 1.6)
    txt = "PC OFFLINE"
    x = (W - word_width(txt, 12)) // 2
    neon_word(fb, txt, x, 1, (255, 140, 40), (255, 235, 200), size=12, t=t, faulty=(1,), seed=5)


BARS = [(235, 215, 255), (255, 230, 80), (0, 235, 255), (0, 235, 140), (255, 40, 200), (255, 50, 80), (70, 60, 255)]


def scene_no_input(fb, t):
    """a synthwave colour-bar test card on a CRT that has lost its input: static, a rolling bar, NO INPUT"""
    rng = np.random.default_rng(int(t * FPS) + 99)
    bw = W / len(BARS)
    for i, c in enumerate(BARS):
        fb[:22, int(i * bw):int((i + 1) * bw)] = np.array(c, np.float32) * 0.95
    fb[22:] = (12, 0, 30)
    for i, c in enumerate(BARS[::-1]):                                    # reversed mini bars along the bottom
        fb[22:25, int(i * bw):int((i + 1) * bw)] = np.array(c, np.float32) * 0.45
    noise = rng.random((H, W)).astype(np.float32)
    amt = 0.12 + 0.22 * max(0, math.sin(t * 1.7)) ** 2                         # static swells and fades
    fb[:] = fb * (1 - amt) + noise[..., None] * 255 * amt * np.array((0.9, 0.75, 1.0), np.float32)
    roll = (t * 14) % (H + 10) - 5                                        # dark band rolling up the tube
    fb *= (1 - 0.45 * np.clip(1 - np.abs(YY - (H - roll)) / 4, 0, 1))[..., None]
    for y in range(0, H, 2):                                              # scanlines
        fb[y] *= 0.82
    # the NO INPUT box
    txt = "NO INPUT"
    m = tmask(txt, size=11, spacing=1)
    h, w = m.shape
    x, y = (W - w) // 2, 9
    fb[y - 3:y + h + 2, x - 5:x + w + 5] = (6, 0, 18)
    box = np.zeros_like(fb)
    seg(box, x - 5, y - 3, x + w + 4, y - 3, CYAN, w=1.0); seg(box, x - 5, y + h + 1, x + w + 4, y + h + 1, CYAN, w=1.0)
    seg(box, x - 5, y - 3, x - 5, y + h + 1, CYAN, w=1.0); seg(box, x + w + 4, y - 3, x + w + 4, y + h + 1, CYAN, w=1.0)
    bloom(fb, box, 0.7, 1.2)
    blink = 1.0 if (t * 1.6) % 1 < 0.75 else 0.25
    g, pad = glow(m, 1.4, 1.5)
    blit(fb, g * blink, x - pad, y - pad, HOT)
    blit(fb, m * blink, x, y, (255, 225, 245))
    vig = np.clip(1 - (((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.8)) ** 2), 0.35, 1)
    fb *= vig[..., None]


SCENES = [("no_signal", scene_no_signal, 6), ("waiting", scene_waiting, 6),
          ("unplugged", scene_unplugged, 6), ("no_input", scene_no_input, 5)]


def frame_of(fn, t):
    fb = np.zeros((H, W, 3), np.float32)
    fn(fb, t)
    return fb


def show(loop=True):
    """yields (scene name, uint8 frame); with loop=False exactly one seamless cycle (the last transition
    leads back into the first scene, so the cycle repeats without a seam)"""
    prev, last, k = SCENES[-1][1:], None, 0
    while True:
        for name, fn, secs in SCENES:
            for i in range(int(secs * FPS)):
                f = frame_of(fn, i / FPS)
                if i < TRANS:
                    p = (i + 1) / (TRANS + 1)
                    f = TRANSITIONS[k % len(TRANSITIONS)](frame_of(prev[0], prev[1] + i / FPS), f, p, i)
                if last is not None:
                    f = np.maximum(f, last * AFTERGLOW)
                last = np.clip(f, 0, 255)
                yield name, last.astype(np.uint8)
            k += 1
            prev = (fn, secs)
        if not loop:
            return


if __name__ == "__main__":
    OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("previews_offline")
    OUT.mkdir(parents=True, exist_ok=True)
    frames, names = [], []
    for name, f in show(loop=False):
        frames.append(f); names.append(name)
    print(len(frames), "frames")
    sheet = Image.new("RGB", (W * 4 + 20, (H * 4 + 10) * len(SCENES) + 10), (20, 20, 20))
    for n, (name, _, _) in enumerate(SCENES):
        idx = [i for i, s in enumerate(names) if s == name]
        gif = [led_preview(frames[i], 5) for i in idx[::2]]
        gif[0].save(OUT / f"{n + 1}_{name}.gif", save_all=True, append_images=gif[1:], duration=1000 // 15, loop=0)
        mid = Image.fromarray(frames[idx[len(idx) * 2 // 3]]).resize((W * 4, H * 4), Image.NEAREST)
        sheet.paste(mid, (10, 10 + n * (H * 4 + 10)))
    sheet.save(OUT / "contact_sheet.png")
    full = [led_preview(f, 4) for f in frames[::2]]
    full[0].save(OUT / "full_show.gif", save_all=True, append_images=full[1:], duration=1000 // 15, loop=0)
    print("written to", OUT)
