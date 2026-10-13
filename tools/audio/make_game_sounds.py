#!/usr/bin/env python3
"""Writes game_sounds.wav: ~35 s of synthesised playfield sounds in a game-like order, at the loudness a table plays them.
launch -> ball rolling -> flipper hits -> pop-bumper burst -> slingshots -> ramp roll -> flipper rally -> drain."""
import math, random, struct, wave
SR = 44100; buf = [0.0] * (SR * 36)
random.seed(7)
def mix(t0, sig):
    i0 = int(t0 * SR)
    for i, v in enumerate(sig):
        if 0 <= i0 + i < len(buf): buf[i0 + i] += v
def env_dec(n, rate): return [math.exp(-i / SR * rate) for i in range(n)]
def noise_lp(n, k):
    y = 0; out = []
    for _ in range(n): y += k * ((random.random() * 2 - 1) - y); out.append(y)
    return out
def flipper(g=1.0):                                   # coil clack + body thud
    n = int(SR * 0.22); e1 = env_dec(n, 250); e2 = env_dec(n, 22)
    return [g * (0.5 * e1[i] * (random.random() * 2 - 1) + 0.9 * e2[i] * math.sin(2 * math.pi * 62 * i / SR)) for i in range(n)]
def bumper(g=1.0):                                    # pop: sharp snap + ringing thump
    n = int(SR * 0.3); e1 = env_dec(n, 600); e2 = env_dec(n, 14)
    return [g * (0.7 * e1[i] * (random.random() * 2 - 1) + 0.8 * e2[i] * math.sin(2 * math.pi * 48 * i / SR) + 0.25 * e2[i] * math.sin(2 * math.pi * 180 * i / SR)) for i in range(n)]
def sling(g=1.0):
    n = int(SR * 0.18); e1 = env_dec(n, 300); e2 = env_dec(n, 30)
    return [g * (0.5 * e1[i] * (random.random() * 2 - 1) + 0.7 * e2[i] * math.sin(2 * math.pi * 75 * i / SR)) for i in range(n)]
def roll(sec, g=1.0, pitch=1.0):                      # ball rolling on wood: low rumble with bumpy texture
    n = int(SR * sec); r = noise_lp(n, 0.012 * pitch); out = []
    for i in range(n):
        t = i / SR; e = min(1, t / 0.15, (sec - t) / 0.2)
        out.append(g * 5.0 * r[i] * e * (0.92 + 0.08 * math.sin(2 * math.pi * 2.3 * pitch * t)))   # gentle drift, no 'train' chug
    return out
def launch():                                         # plunger release: spring twang + thump
    n = int(SR * 0.5); e = env_dec(n, 9)
    return [0.6 * e[i] * math.sin(2 * math.pi * 95 * i / SR) * (1 + 0.3 * math.sin(2 * math.pi * 9 * i / SR)) + 0.6 * math.exp(-i / SR * 300) * (random.random() * 2 - 1) for i in range(n)]
def drain():                                          # ball drops into the trough: two thunks
    out = []
    for g, f in ((1.0, 45), (0.6, 52)):
        n = int(SR * 0.3); e = env_dec(n, 16)
        out += [g * e[i] * math.sin(2 * math.pi * f * i / SR) for i in range(n)] + [0.0] * int(SR * 0.12)
    return out
t = 0.5
mix(t, launch()); mix(t + 0.3, roll(2.5, 0.8, 1.4))                      # launch + up the shooter lane
t = 3.5
for k in range(4): mix(t + k * 0.12, bumper(0.9 + 0.1 * random.random())) # pop-bumper burst
mix(t + 0.1, roll(1.2, 0.5))
t = 5.5; mix(t, roll(3.0, 0.9))                                           # rolling down the playfield
mix(t + 2.6, flipper()); mix(t + 2.9, roll(1.5, 0.7, 1.2))                # flipper hit, ball goes back up
t = 10
for k in range(3): mix(t + k * 0.55, sling(1.0)); mix(t + k * 0.55 + 0.1, roll(0.4, 0.5))  # slingshots
t = 12.5; mix(t, roll(3.5, 1.0, 1.6))                                     # ramp roll (faster, louder)
mix(t + 3.6, bumper(0.7))
t = 17
for k in range(6): mix(t + k * 0.9 + random.random() * 0.2, flipper(0.85 + 0.15 * random.random()))  # flipper rally
mix(t, roll(5.5, 0.6))
t = 23.5
for k in range(8): mix(t + k * 0.09, bumper(0.8))                          # big bumper frenzy
mix(t + 1.0, roll(2.5, 0.8)); mix(t + 3.2, flipper()); mix(t + 3.5, roll(2.0, 0.7, 1.3))
t = 30; mix(t, roll(1.8, 0.6)); mix(t + 1.9, drain())                     # drain
pk = max(abs(v) for v in buf); g = 0.891 / pk
with wave.open("game_sounds.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<hh", int(v * g * 32767), int(v * g * 32767)) for v in buf))
print("game_sounds.wav", len(buf) / SR, "s")
