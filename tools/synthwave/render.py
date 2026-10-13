#!/usr/bin/env python3
"""Synthwave idle show for the 128x32 marquee (v2).

Every scene is procedural (fn(fb, t) -> RGB float frame) and drawn with anti-aliased, sub-pixel lines into a
separate neon layer that gets a real bloom, so motion is smooth on the 128x32 panel instead of stepping a
pixel at a time. show() strings the scenes together with CRT / scanline / glitch / neon-wipe transitions and
a little phosphor afterglow; play_marquee.py streams exactly those frames to the ZeDMD.

  python tools/synthwave/render.py [outdir]     -> LED-look preview GIFs + contact sheet
"""
import functools, math, random, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 128, 32, 30
FONTS = Path("C:/Windows/Fonts")
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

# palette
PINK, HOT, CYAN, PURPLE, ORANGE, YELLOW = (255, 41, 117), (255, 0, 160), (0, 240, 255), (120, 20, 200), (255, 120, 40), (255, 220, 60)
RED, WHITE = (255, 25, 50), (255, 255, 255)


# ------------------------------------------------------------------ text
def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def text_mask(txt, f, spacing=0):
    x0, y0, x1, y1 = f.getbbox(txt)
    im = Image.new("L", (x1 - x0 + 2 + spacing * len(txt), y1 - y0 + 2), 0)
    d = ImageDraw.Draw(im)
    if spacing:
        x = 1
        for ch in txt:
            d.text((x - x0, 1 - y0), ch, font=f, fill=255)
            x += f.getbbox(ch)[2] - f.getbbox(ch)[0] + spacing
    else:
        d.text((1 - x0, 1 - y0), txt, font=f, fill=255)
    return np.asarray(im, np.float32) / 255.0


@functools.lru_cache(None)
def tmask(txt, fname="impact.ttf", size=14, spacing=1):
    return text_mask(txt, font(fname, size), spacing)


def glow(mask, radius=2.0, strength=1.6):
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    pad = int(radius * 3)
    im = im.crop((-pad, -pad, im.width + pad, im.height + pad))
    g = np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255.0
    return np.clip(g * strength, 0, 1), pad


@functools.lru_cache(None)
def tglow(txt, fname="impact.ttf", size=14, spacing=1, radius=2.0, strength=1.6):
    return glow(tmask(txt, fname, size, spacing), radius, strength)


def blit(fb, mask, x, y, color):
    """alpha-blend a mask in a colour (or an (h,w,3) colour image) at x, y"""
    h, w = mask.shape
    xa, ya, xb, yb = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if xa >= xb or ya >= yb:
        return
    m = mask[ya - y:yb - y, xa - x:xb - x, None]
    c = color[ya - y:yb - y, xa - x:xb - x] if isinstance(color, np.ndarray) and color.ndim == 3 else np.array(color, np.float32)
    fb[ya:yb, xa:xb] = fb[ya:yb, xa:xb] * (1 - m) + c * m


def chrome(h, w, top=(120, 220, 255), mid=(255, 255, 255), bot=(255, 40, 160)):
    """classic synthwave chrome: sky-blue top, white horizon line, hot-pink bottom"""
    t = np.linspace(0, 1, h)[:, None]
    top, mid, bot = (np.array(c, np.float32) for c in (top, mid, bot))
    col = np.where(t < 0.5, top + (mid - top) * (t / 0.5) ** 1.6, bot + (mid - bot) * (1 - (t - 0.5) / 0.5) ** 3)
    col = np.where((t > 0.48) & (t < 0.56), np.array(WHITE, np.float32), col)
    return np.repeat(col[:, None, :], w, axis=1)


# ------------------------------------------------------------------ anti-aliased primitives (lighten blend)
def _lit(L, ya, yb, xa, xb, m, col):
    reg = L[ya:yb, xa:xb]
    np.maximum(reg, np.asarray(col, np.float32) * m[..., None], out=reg)


def _box(x0, y0, x1, y1, p):
    xa, xb = max(0, int(math.floor(min(x0, x1) - p))), min(W, int(math.ceil(max(x0, x1) + p)) + 1)
    ya, yb = max(0, int(math.floor(min(y0, y1) - p))), min(H, int(math.ceil(max(y0, y1) + p)) + 1)
    return xa, xb, ya, yb


def seg(L, x0, y0, x1, y1, col, w=1.0, a=1.0):
    xa, xb, ya, yb = _box(x0, y0, x1, y1, w / 2 + 1)
    if xa >= xb or ya >= yb:
        return
    yy, xx = YY[ya:yb, xa:xb], XX[ya:yb, xa:xb]
    dx, dy = x1 - x0, y1 - y0
    l2 = dx * dx + dy * dy
    u = np.clip(((xx - x0) * dx + (yy - y0) * dy) / l2, 0, 1) if l2 > 1e-9 else 0.0
    d = np.hypot(xx - x0 - u * dx, yy - y0 - u * dy)
    _lit(L, ya, yb, xa, xb, np.clip(w / 2 + 0.5 - d, 0, 1) * a, col)


def poly(L, pts, col, w=1.0, a=1.0):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg(L, x0, y0, x1, y1, col, w, a)


def disc(L, cx, cy, r, col, a=1.0):
    xa, xb, ya, yb = _box(cx, cy, cx, cy, r + 1)
    if xa < xb and ya < yb:
        d = np.hypot(XX[ya:yb, xa:xb] - cx, YY[ya:yb, xa:xb] - cy)
        _lit(L, ya, yb, xa, xb, np.clip(r + 0.5 - d, 0, 1) * a, col)


def ring(L, cx, cy, r, col, w=1.0, a=1.0):
    xa, xb, ya, yb = _box(cx, cy, cx, cy, r + w + 1)
    if xa < xb and ya < yb:
        d = np.hypot(XX[ya:yb, xa:xb] - cx, YY[ya:yb, xa:xb] - cy)
        _lit(L, ya, yb, xa, xb, np.clip(w / 2 + 0.5 - abs(d - r), 0, 1) * a, col)


def rect(fb, x0, y0, x1, y1, col):
    fb[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = col


def blur(a, r):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32)


def bloom(fb, neon, k=1.0, r=1.8):
    """neon tubes: the line itself plus a soft halo"""
    np.maximum(fb, neon, out=fb)
    fb += blur(neon, r) * k


# ------------------------------------------------------------------ world pieces
def sky(fb, t, hz, seed=7, drift=1.0):
    """deep-night gradient, magenta haze on the horizon, two parallax star layers that twinkle"""
    s = np.clip(YY / max(hz, 1), 0, 1)[..., None]
    fb[:] = np.array((3, 0, 18)) + np.array((42, 0, 72)) * s
    haze = np.exp(-np.clip(hz - YY, 0, None) / 3.5) * (YY < hz)
    fb += np.array((170, 20, 120), np.float32) * haze[..., None] * 0.55
    rnd = random.Random(seed)
    for n, spd, br in ((22, 0.6, 0.55), (10, 2.0, 1.0)):
        for _ in range(n):
            sx, sy, ph = rnd.uniform(0, W), rnd.uniform(0, max(1, hz - 5)), rnd.random() * 6.28
            if sy >= H:
                continue
            x = (sx - t * spd * drift) % W
            b = br * (0.4 + 0.6 * max(0, math.sin(t * 2.5 + ph)) ** 2) * 255
            xi, f = int(x), x - int(x)
            for xx, k in ((xi, 1 - f), ((xi + 1) % W, f)):
                fb[int(sy), xx] = np.maximum(fb[int(sy), xx], b * k)


def sun(fb, neon, cx, cy, r, t):
    """gradient sun with the classic drifting scanline cut-outs (anti-aliased, so they glide)"""
    d = np.hypot(XX - cx, YY - cy)
    inside = np.clip(r + 0.5 - d, 0, 1)
    v = np.clip((YY - (cy - r)) / (2 * r), 0, 1)
    col = np.stack([np.full_like(v, 255), 235 - 215 * v, 50 + 130 * v], -1)
    ph = (YY - cy + t * 5) % 5
    w = 0.5 + 2.4 * np.clip((YY - cy) / r, 0, 1)
    cut = np.clip(np.minimum(ph + 0.5, w) - np.maximum(ph - 0.5, 0), 0, 1) + np.clip(np.minimum(ph + 0.5, 5 + w) - np.maximum(ph - 0.5, 5), 0, 1)
    m = inside * (1 - np.clip(cut, 0, 1) * (YY > cy - 0.2 * r))
    fb[:] = fb * (1 - m[..., None]) + col * m[..., None]
    np.maximum(neon, col * m[..., None] * 0.55, out=neon)


def mountains(fb, neon, hz, t, speed=1.0):
    """two parallax ridges; the front one has a neon rim and hides whatever glows behind it"""
    for depth, (fill, edge, amp, off) in enumerate((((45, 5, 80), (130, 40, 210), 1.0, 0.0), ((18, 0, 38), (255, 40, 200), 1.25, 3.0))):
        xs = np.arange(W, dtype=np.float32) + t * speed * (1 + depth * 1.5) + off * 40
        h = amp * (1.5 + 2.2 * np.abs(np.sin(xs * 0.071 + off)) + 1.6 * np.abs(np.sin(xs * 0.193 + 1.7 + off))
                   + np.maximum(0, 3.2 * np.sin(xs * 0.031 + 0.6 + off) - 1.2))
        top = hz - h
        m = np.clip(YY - top[None, :] + 0.5, 0, 1) * (YY < hz)
        fb[:] = fb * (1 - m[..., None]) + np.array(fill, np.float32) * m[..., None]
        neon *= (1 - m[..., None])
        em = np.clip(1 - np.abs(YY - top[None, :]), 0, 1) * (YY < hz)
        np.maximum(neon, np.array(edge, np.float32) * em[..., None] * (0.55 + 0.45 * depth), out=neon)


def grid(fb, neon, hz, t, speed=1.0, col=HOT, reflect=False):
    """perspective floor: lines rush toward the viewer, verticals fan out; optional sun reflection"""
    dh = H - hz
    snap = fb.copy() if reflect else None
    fb[hz:] = (8, 0, 26)
    if reflect:
        for y in range(hz, H):
            src = int(hz - 1 - (y - hz) * 1.6)
            if src >= 0:
                fb[y] += np.roll(snap[src], int(round(math.sin(y * 1.7 + t * 7) * 1.3)), axis=0) * 0.22 * (1 - (y - hz) / dh)
    gl = np.zeros_like(fb)
    for i in range(12):
        z = (i + (t * speed) % 1.0) / 12
        seg(gl, 0, hz + dh * z ** 2.3, W - 1, hz + dh * z ** 2.3, col, w=0.5 + 0.7 * z, a=0.2 + 0.6 * z)
    for k in range(-12, 13):
        seg(gl, W / 2 + k * 3.5, hz, W / 2 + k * 22, H + 2, col, w=0.9)
    ramp = (np.clip((YY - hz) / dh, 0, 1) ** 0.8 * (YY >= hz))[..., None]
    np.maximum(neon, gl * (0.2 + 0.8 * ramp) * (YY >= hz)[..., None], out=neon)
    seg(neon, 0, hz, W - 1, hz, (255, 150, 235), w=1.0)


def palm(L, x, y, hgt, sway, bright=1.0):
    """neon palm: pink trunk, cyan/green fronds"""
    tx, ty = x + sway * hgt * 0.15, y - hgt
    poly(L, [(x, y), (x + sway * hgt * 0.05, y - hgt * 0.5), (tx, ty)], (255, 60, 200), w=max(0.7, hgt / 12), a=bright)
    for ang in (-170, -135, -100, -70, -40, -8):
        a = math.radians(ang + sway * 8)
        ln = hgt * 0.55
        pts = [(tx + math.cos(a) * ln * f, ty + math.sin(a) * ln * f + (ln * f) ** 2 * 0.06) for f in (0, 0.5, 1)]
        poly(L, pts, (0, 235, 170), w=max(0.6, hgt / 16), a=bright)


# ------------------------------------------------------------------ scenes (t = seconds inside the scene)
def scene_sunset(fb, t):
    neon = np.zeros_like(fb)
    hz = 19
    sky(fb, t, hz)
    sun(fb, neon, 64, 11, 11, t)
    mountains(fb, neon, hz, t, speed=1.5)
    grid(fb, neon, hz, t, speed=1.2, reflect=True)
    bloom(fb, neon, 0.9)


def scene_pinball_title(fb, t):
    neon = np.zeros_like(fb)
    sky(fb, t, 24, seed=11, drift=0.4)
    grid(fb, neon, 24, t, speed=0.7, col=PURPLE)
    bloom(fb, neon, 0.8)
    m = tmask("PINBALL", size=20, spacing=1)
    h, w = m.shape
    a = min(1.0, t / 1.3)
    ang = (1 - (1 - a) ** 3) * 3 * math.pi                            # spins in 1.5 turns and settles
    sx = abs(math.cos(ang))
    w2 = max(1, int(round(w * sx)))
    ms = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((w2, h), Image.LANCZOS), np.float32) / 255
    x, y = (W - w2) // 2, 1 + int(round(math.sin(t * 1.4) * 1.0 * a))
    g, pad = glow(ms, 2.2, 1.4)
    pulse = 0.75 + 0.25 * math.sin(t * 3)
    blit(fb, g * pulse, x - pad, y - pad, HOT)
    face = chrome(h, w2) if math.cos(ang) >= 0 else chrome(h, w2, (255, 80, 200), (255, 200, 255), (120, 20, 200))
    blit(fb, ms, x, y, face)
    if a >= 1:
        sweep = ((t - 1.3) * 70) % (w + 60) - 30                        # light glint sweeping across
        xs = np.arange(w)[None, :]
        shine = np.clip(1 - abs(xs - sweep - np.arange(h)[:, None] * 0.6) / 3, 0, 1) * m
        blit(fb, shine * 0.9, x, y, WHITE)


def scene_flippers(fb, t):
    """a ball rallies flipper -> bumper -> other flipper; flippers fire on contact, bumpers flash on hits"""
    neon = np.zeros_like(fb)
    sky(fb, t, H + 4, seed=5, drift=0.2)
    fb *= 0.45
    # playfield art
    arch = [(64 + 60 * math.cos(a), 31 - 29 * math.sin(a)) for a in np.linspace(0, math.pi, 25)]
    poly(neon, arch, PURPLE, w=1.0, a=0.8)
    seg(neon, 8, 12, 27, 22.5, CYAN, w=1.0); seg(neon, 120, 12, 101, 22.5, CYAN, w=1.0)
    # choreography: ballistic legs with gravity
    g = 46.0
    Lc, Rc, Bl, Br = (39, 23.5), (89, 23.5), (59.5, 13.5), (68.5, 13.5)
    legs = [(Lc, Bl, 0.42), (Bl, Rc, 0.9), (Rc, Br, 0.42), (Br, Lc, 0.9)]
    period = sum(l[2] for l in legs)
    starts = np.cumsum([0] + [l[2] for l in legs])

    def ball_at(tt):
        tt %= period
        for (A, B, T), s0 in zip(legs, starts):
            if tt < s0 + T:
                tau = tt - s0
                vx, vy = (B[0] - A[0]) / T, (B[1] - A[1]) / T - 0.5 * g * T
                return A[0] + vx * tau, A[1] + vy * tau + 0.5 * g * tau * tau
        return Lc

    tp = t % period
    def since(ev):                                                     # seconds since the event time (mod period)
        return (tp - ev) % period
    hitL, hitB1, hitR, hitB2 = starts[0], starts[1], starts[2], starts[3]
    bumper_flash = max(math.exp(-since(hitB1) * 7), math.exp(-since(hitB2) * 7))
    # bumpers
    for cx, cy, r, fl in ((64, 8, 4.5, bumper_flash), (46, 6, 2.6, math.exp(-since(hitB1 + 0.1) * 5)), (82, 6, 2.6, math.exp(-since(hitB2 + 0.1) * 5))):
        ring(neon, cx, cy, r, CYAN, w=1.2)
        disc(neon, cx, cy, r - 1.2, (255, 255, 255), a=fl)
        disc(neon, cx, cy, r - 1.2, HOT, a=0.35)
        ring(neon, cx, cy, r + 1 + 4 * (1 - fl), YELLOW, w=0.8, a=fl * 0.8)
    # flippers
    def flipper(px, py, rest, up, firing):
        a = math.radians(up if firing else rest)
        tx, ty = px + math.cos(a) * 15, py + math.sin(a) * 15
        seg(neon, px, py, tx, ty, HOT, w=2.6)
        disc(neon, px, py, 1.6, WHITE)
    lfire = since(hitL) < 0.14 or since(hitL) > period - 0.04
    rfire = since(hitR) < 0.14 or since(hitR) > period - 0.04
    flipper(26, 22, 26, -12, lfire)
    flipper(102, 22, 154, 192, rfire)
    # ball + rainbow trail
    pts = [ball_at(t - k * 0.018) for k in range(16)]
    for k in range(len(pts) - 1, 0, -1):
        hue = (t * 0.4 + k * 0.06) % 1
        c = tuple(255 * (0.5 + 0.5 * math.cos(6.28 * (hue + o))) for o in (0, .33, .67))
        seg(neon, *pts[k], *pts[k - 1], c, w=1.6 * (1 - k / 18), a=1 - k / 16)
    bloom(fb, neon, 1.0)
    bx, by = pts[0]
    disc(fb, bx, by, 1.5, (255, 255, 255))


def scene_insert_coin(fb, t):
    neon = np.zeros_like(fb)
    sky(fb, t, 27, seed=21)
    sun(fb, neon, 64, 38, 16, t)
    grid(fb, neon, 27, t, speed=0.8, col=PURPLE)
    # spinning gold coins either side
    for cx, ph in ((11, 0.0), (W - 12, 1.3)):
        rx, ry = 5.5 * abs(math.cos(t * 3.2 + ph)) + 0.6, 6.5
        q = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - 12.5) / ry) ** 2)
        m = np.clip((1 - q) * rx + 0.5, 0, 1)
        shade = 0.65 + 0.35 * np.clip((XX - cx) / rx, -1, 1) * math.copysign(1, math.cos(t * 3.2 + ph))
        col = np.stack([255 * shade, 200 * shade, 40 * shade], -1)
        fb[:] = fb * (1 - m[..., None]) + col * m[..., None]
        np.maximum(neon, col * m[..., None] * 0.6, out=neon)
        e = np.clip(1 - np.abs(q - 0.72) * rx * 1.2, 0, 1) * (rx > 2)
        np.maximum(fb, np.array((255, 245, 180)) * e[..., None] * 0.8, out=fb)
    bloom(fb, neon, 0.8)
    m = tmask("INSERT COIN", size=14, spacing=1)
    h, w = m.shape
    x, y = (W - w) // 2, 5
    flick = 1.0 if (t % 1.6) < 1.1 else (0.15 if int(t * 20) % 3 else 0.7)   # neon-tube flicker
    g, pad = tglow("INSERT COIN", size=14, spacing=1, radius=1.8, strength=1.8)
    blit(fb, g * flick, x - pad, y - pad, CYAN)
    blit(fb, m * flick, x, y, (210, 255, 255))


def scene_night_drive(fb, t):
    """outrun: drive into the sun, palms whipping past, taillights glowing"""
    neon = np.zeros_like(fb)
    hz, dh = 17, H - 17
    sky(fb, t, hz, seed=44, drift=0.5)
    sun(fb, neon, 64, 10, 10, t)
    mountains(fb, neon, hz, t, speed=2.5)
    fb[hz:] = (10, 0, 30)
    gl = np.zeros_like(fb)                                             # faint side grid
    for i in range(8):
        z = (i + (t * 2.2) % 1.0) / 8
        seg(gl, 0, hz + dh * z ** 2, W - 1, hz + dh * z ** 2, PURPLE, w=0.6 + 0.6 * z, a=0.3 + 0.5 * z)
    np.maximum(neon, gl * (YY >= hz)[..., None], out=neon)
    # road surface + edges + rushing centre dashes
    for y in range(hz, H):
        hw = 1.5 + (y - hz) / dh * 82
        fb[y, max(0, int(64 - hw)):min(W, int(64 + hw))] = (22, 0, 44)
        neon[y, max(0, int(64 - hw)):min(W, int(64 + hw))] = 0
    seg(neon, 62.5, hz, -20, H + 3, CYAN, w=1.3)
    seg(neon, 65.5, hz, 148, H + 3, CYAN, w=1.3)
    for i in range(6):
        z0 = ((i + t * 1.8) % 6) / 6
        z1 = min(1.0, z0 + 0.06)
        seg(neon, 64, hz + dh * z0 ** 2, 64, hz + dh * z1 ** 2, YELLOW, w=0.5 + 1.6 * z0, a=0.4 + 0.6 * z0)
    # roadside palms, far -> near
    for i in range(5):
        z = ((i / 5) + t * 0.32) % 1
        s = z ** 2.2
        y = hz + dh * s * 1.15
        for side in (-1, 1):
            x = 64 + side * (6 + 95 * s)
            palm(neon, x, y, 2 + 26 * s, math.sin(t * 2 + i) * 0.6, bright=0.35 + 0.65 * z)
    neon[hz - 1:hz, :] = np.maximum(neon[hz - 1:hz, :], 0)
    seg(neon, 0, hz, W - 1, hz, (255, 150, 235), w=1.0)
    # the car (rear view)
    c = int(round(64 + math.sin(t * 0.9) * 5))
    bob = 1 if int(t * 12) % 7 == 0 else 0
    neon[19:32, c - 13:c + 14] = 0
    rect(fb, c - 12, 24 + bob, c + 13, 29 + bob, (40, 0, 62))
    rect(fb, c - 8, 20 + bob, c + 9, 24 + bob, (26, 0, 48))
    rect(fb, c - 7, 21 + bob, c + 8, 23 + bob, (0, 100, 140))
    rect(fb, c - 12, 29 + bob, c - 6, 32, (6, 0, 12))
    rect(fb, c + 7, 29 + bob, c + 13, 32, (6, 0, 12))
    seg(neon, c - 12, 24 + bob, c + 12, 24 + bob, PINK, w=0.8, a=0.8)
    seg(neon, c - 11, 26 + bob, c - 4, 26 + bob, RED, w=1.4)
    seg(neon, c + 4, 26 + bob, c + 11, 26 + bob, RED, w=1.4)
    seg(neon, c - 3, 26 + bob, c + 3, 26 + bob, RED, w=0.7, a=0.5)
    bloom(fb, neon, 1.0)


def scene_high_score(fb, t):
    neon = np.zeros_like(fb)
    sky(fb, t, H + 4, seed=33, drift=0.3)
    fb *= 0.6
    # chasing marquee bulbs round the edge
    pts = [(x, 0) for x in range(W)] + [(W - 1, y) for y in range(1, H)] + [(x, H - 1) for x in range(W - 2, -1, -1)] + [(0, y) for y in range(H - 2, 0, -1)]
    off = int(t * 24)
    for i, (x, y) in enumerate(pts):
        if (i + off) % 6 < 2:
            neon[y, x] = YELLOW if (i // 6) % 2 else HOT
    bloom(fb, neon, 0.7, 1.2)
    head = tmask("HIGH SCORE", size=11)
    h, w = head.shape
    g, pad = tglow("HIGH SCORE", size=11, radius=1.5, strength=1.6)
    blit(fb, g, (W - w) // 2 - pad, 2 - pad, HOT)
    blit(fb, head, (W - w) // 2, 2, (255, 200, 240))
    score = min(1.0, t / 2.5) ** 0.5 * 48210550                       # count-up roll
    digits = tmask(f"{int(score):,}", size=13)
    h2, w2 = digits.shape
    g2, pad2 = glow(digits, 1.6, 1.5)
    blit(fb, g2, (W - w2) // 2 - pad2, 15 - pad2, CYAN)
    blit(fb, digits, (W - w2) // 2, 15, chrome(h2, w2))
    if t > 2.5:                                                        # landed: white flash on the digits
        blit(fb, digits * math.exp(-(t - 2.5) * 4), (W - w2) // 2, 15, WHITE)


def scene_tilt(fb, t):
    """TILT! - shaking, crackling with lightning"""
    neon = np.zeros_like(fb)
    fb[:] = np.array((25, 0, 10)) * (0.6 + 0.4 * math.sin(t * 14) ** 2)
    rnd = random.Random(int(t * 12))
    for _ in range(3):                                                 # lightning, re-rolled 12x a second
        x, y = rnd.uniform(10, W - 10), 0.0
        pts = [(x, y)]
        while y < H:
            x += rnd.uniform(-6, 6); y += rnd.uniform(3, 7)
            pts.append((x, y))
            if rnd.random() < 0.3:
                seg(neon, x, y, x + rnd.uniform(-10, 10), y + rnd.uniform(3, 8), (150, 120, 255), w=0.7, a=0.7)
        poly(neon, pts, (200, 200, 255), w=0.9)
    bloom(fb, neon, 1.0, 1.5)
    m = tmask("TILT", size=26, spacing=2)
    h, w = m.shape
    shake = (rnd.randint(-2, 2), rnd.randint(-1, 1)) if t < 0.8 or rnd.random() < 0.1 else (0, 0)
    x, y = (W - w) // 2 + shake[0], (H - h) // 2 + shake[1]
    flick = 1.0 if rnd.random() > 0.12 else 0.3
    g, pad = tglow("TILT", size=26, spacing=2, radius=2.4, strength=1.8)
    blit(fb, g * flick, x - pad, y - pad, RED)
    blit(fb, m * flick, x, y, (255, 215, 215))


SCENES = [("sunset", scene_sunset, 7), ("pinball", scene_pinball_title, 6), ("flippers", scene_flippers, 7),
          ("night_drive", scene_night_drive, 8), ("insert_coin", scene_insert_coin, 4),
          ("high_score", scene_high_score, 5), ("tilt", scene_tilt, 2.5)]


# ------------------------------------------------------------------ transitions + the show
TRANS = 15                                                             # frames
_RANK = np.argsort([int(f"{y:05b}"[::-1], 2) for y in range(H)]).argsort()   # interlaced row order


def t_crt(a, b, p, i):
    src, s = (a, 1 - 2 * p) if p < 0.5 else (b, 2 * p - 1)
    s = max(s, 0.04)
    rows = (np.arange(H) - H / 2 + 0.5) / s + H / 2 - 0.5
    ok = ((rows >= 0) & (rows <= H - 1)).astype(np.float32)[:, None, None]
    out = src[np.clip(np.round(rows).astype(int), 0, H - 1)] * ok * (1 + (1 - s) * 1.2)
    line = np.exp(-((np.arange(H) - H / 2 + 0.5) / 0.8) ** 2)[:, None, None]
    return out + 255 * line * (1 - s) ** 3


def t_scan(a, b, p, i):
    m = (_RANK < p * H)[:, None, None]
    edge = (np.abs(_RANK - p * H) < 1.5)[:, None, None]
    return np.where(m, b, a) + edge * np.array(CYAN, np.float32) * 0.5


def t_glitch(a, b, p, i):
    rng = np.random.default_rng(i * 7919 + 17)
    pick = (rng.random(H) < p)[:, None, None]
    out = np.where(pick, b, a)
    amp = 1 - abs(2 * p - 1)
    for y in np.nonzero(rng.random(H) < 0.45 * amp)[0]:
        out[y] = np.roll(out[y], int(rng.integers(-8, 9)), axis=0)
    out[..., 0] = np.roll(out[..., 0], int(round(2 * amp)), axis=1)
    out[..., 2] = np.roll(out[..., 2], -int(round(2 * amp)), axis=1)
    return out


def t_wipe(a, b, p, i):
    pos = XX + YY * 1.2
    edge = p * (W + H * 1.2 + 10) - 5
    m = np.clip(edge - pos, 0, 1)[..., None]
    band = np.clip(1 - np.abs(pos - edge) / 2.5, 0, 1)[..., None]
    return a * (1 - m) + b * m + band * np.array(HOT, np.float32)


TRANSITIONS = [t_crt, t_wipe, t_scan, t_glitch]
AFTERGLOW = 0.35                                                       # phosphor persistence


def frame_of(fn, t):
    fb = np.zeros((H, W, 3), np.float32)
    fn(fb, t)
    return fb


def show(loop=True):
    """yields (scene name, uint8 HxWx3 frame) forever (or one pass with loop=False)"""
    prev, last, k = None, None, 0
    while True:
        for name, fn, secs in SCENES:
            for i in range(int(secs * FPS)):
                f = frame_of(fn, i / FPS)
                if i < TRANS:
                    p = (i + 1) / (TRANS + 1)
                    if prev is None:
                        f = f * p
                    else:
                        f = TRANSITIONS[k % len(TRANSITIONS)](frame_of(prev[0], prev[1] + i / FPS), f, p, i)
                if last is not None:
                    f = np.maximum(f, last * AFTERGLOW)
                last = np.clip(f, 0, 255)
                yield name, last.astype(np.uint8)
            if prev is not None:
                k += 1
            prev = (fn, secs)
        if not loop:
            return


# ------------------------------------------------------------------ preview output
def led_preview(frame, scale=6):
    """round LED dots on black, like the real P2.5 panels"""
    img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST)
    yy, xx = np.mgrid[0:scale, 0:scale]
    dot = (np.sqrt((xx - (scale - 1) / 2) ** 2 + (yy - (scale - 1) / 2) ** 2) <= scale * 0.42).astype(np.float32)
    mask = np.tile(dot, (H, W))[..., None]
    return Image.fromarray((np.asarray(img, np.float32) * mask).astype(np.uint8))


if __name__ == "__main__":
    import time
    OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("previews")
    OUT.mkdir(parents=True, exist_ok=True)
    frames, names, t0 = [], [], time.perf_counter()
    for name, f in show(loop=False):
        frames.append(f); names.append(name)
    ms = (time.perf_counter() - t0) / len(frames) * 1000
    print(f"{len(frames)} frames, {ms:.1f} ms/frame (budget {1000 / FPS:.0f})", flush=True)
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
