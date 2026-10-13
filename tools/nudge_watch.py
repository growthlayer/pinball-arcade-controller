#!/usr/bin/env python3
"""Live nudge readout from the Pinscape Pico gamepad (1209:EAEB).
For each bump prints the direction of the FIRST strong acceleration sample (the push itself, before the box
rings and bounces back) plus the peak X/Y. Gamepad report: id 3, 4 button bytes, then int16 x, y, z, rx, ry.
Run: .venv-esp/bin/python tools/nudge_watch.py [seconds]"""
import sys, time, struct, hid
p = [d for d in hid.enumerate(0x1209, 0xEAEB) if d['usage_page'] == 1 and d['usage'] == 5][0]['path']
h = hid.device(); h.open_path(p); h.set_nonblocking(True)
end = time.time() + (float(sys.argv[1]) if len(sys.argv) > 1 else 60); t0 = time.time()
TH = 3000                                            # counts (of +-32767) that count as a bump
first = peak = None; last = 0
def name(x, y): return ("RIGHT" if x > 0 else "LEFT") if abs(x) >= abs(y) else ("BACK" if y > 0 else "FRONT")
print("watching - bump the box", flush=True)
while time.time() < end:
    r = h.read(64)
    if not r: time.sleep(0.002); continue
    if r[0] != 3: continue
    x, y = struct.unpack_from('<hh', bytes(r), 5)
    now = time.time()
    if max(abs(x), abs(y)) > TH:
        if first is None: first = (x, y); peak = (x, y)
        elif max(abs(x), abs(y)) > max(map(abs, peak)): peak = (x, y)
        last = now
    elif first is not None and now - last > 0.35:   # bump over (0.35 s quiet)
        print(f"{now-t0:6.1f}s  push: {name(*first):5}  first x={first[0]:+6d} y={first[1]:+6d}   peak x={peak[0]:+6d} y={peak[1]:+6d}", flush=True)
        first = peak = None
