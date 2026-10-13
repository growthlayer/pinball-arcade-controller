#!/usr/bin/env python3
"""Writes exciter_test.wav: ~24 s of the sounds the exciter is for, peaking at -1 dBFS (= the loudest a game can send).
 1) bass sweep 25 -> 160 Hz (find rattles / the box's resonance)   2) 6 flipper thumps   3) rolling-ball rumble   4) 3 big hits"""
import math, random, struct, wave
SR = 44100; out = []
def add(seq): out.extend(seq)
def silence(s): add([0.0] * int(SR * s))
# 1) log sweep, 8 s
n = int(SR * 8); ph = 0
for i in range(n):
    f = 25 * (160 / 25) ** (i / n); ph += 2 * math.pi * f / SR
    env = min(1, i / 2000, (n - i) / 2000); add([0.9 * env * math.sin(ph)])
silence(0.6)
# 2) flipper thumps: 55 Hz burst with a fast decay + a click
for k in range(6):
    m = int(SR * 0.25)
    for i in range(m):
        t = i / SR; add([0.95 * math.exp(-t * 18) * math.sin(2 * math.pi * 55 * t) + (0.4 * math.exp(-t * 400) * (random.random() * 2 - 1))])
    silence(0.35)
# 3) rolling ball: low-passed noise with a slow wobble, 6 s
m = int(SR * 6); y = 0
for i in range(m):
    y += 0.02 * ((random.random() * 2 - 1) - y)
    t = i / SR; env = min(1, t / 0.5, (6 - t) / 0.5)
    add([env * 6.0 * y * (0.7 + 0.3 * math.sin(2 * math.pi * 3 * t))])
silence(0.6)
# 4) three big hits (bumper / slingshot): 40 Hz + 80 Hz, slower decay
for k in range(3):
    m = int(SR * 0.6)
    for i in range(m):
        t = i / SR; e = math.exp(-t * 7); add([e * (0.6 * math.sin(2 * math.pi * 40 * t) + 0.35 * math.sin(2 * math.pi * 80 * t))])
    silence(0.5)
pk = max(abs(v) for v in out); g = 0.891 / pk            # normalise to -1 dBFS
with wave.open("exciter_test.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<hh", int(v * g * 32767), int(v * g * 32767)) for v in out))
print(f"exciter_test.wav: {len(out)/SR:.1f} s")
