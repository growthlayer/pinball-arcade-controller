#!/usr/bin/env python3
"""Live readout of the Zero Delay encoder (DragonRise 0079:0006): prints every button / stick change with a time stamp.
Run: .venv-esp/bin/python tools/encoder_watch.py [seconds]"""
import sys, time, hid
dev = hid.device(); dev.open(0x0079, 0x0006); dev.set_nonblocking(True)
end = time.time() + (float(sys.argv[1]) if len(sys.argv) > 1 else 180); t0 = time.time(); prev = None
def decode(r):
    x, y = r[3], r[4]
    stick = ("LEFT " if x < 64 else "RIGHT " if x > 192 else "") + ("UP" if y < 64 else "DOWN" if y > 192 else "")
    bits = r[5] >> 4 | r[6] << 4                        # 12 buttons: byte5 high nibble = 1-4, byte6 = 5-12
    return stick.strip(), [i + 1 for i in range(12) if bits >> i & 1], r
base = None; prev_ax = ''
print("watching - press things", flush=True)
while time.time() < end:
    r = dev.read(64)
    if not r: time.sleep(0.005); continue
    if base is None: base = list(r); print("rest state:", bytes(r).hex(), flush=True); prev = list(r); continue
    ax = " ".join(f"a{i}={'LO' if r[i] < 64 else 'HI'}" for i in range(5) if not 64 <= r[i] <= 192)   # stick: axis bytes 0-4 pinned low/high
    if ax != prev_ax:
        print(f"{time.time()-t0:6.1f}s  stick: {ax or 'centre'}  [{bytes(r[:5]).hex()}]", flush=True); prev_ax = ax
    if r[5:8] != prev[5:8]:
        ch = [f"byte{i} bit{b} {'ON ' if (r[i]^base[i])>>b&1 else 'off'}" for i in (5, 6, 7) for b in range(8) if (r[i]^prev[i])>>b&1]
        active = [f"b{i}.{b}" for i in (5, 6, 7) for b in range(8) if (r[i]^base[i])>>b&1]
        print(f"{time.time()-t0:6.1f}s  changed: {', '.join(ch):40}  pressed now: {active or '-'}", flush=True)
        prev = list(r)
