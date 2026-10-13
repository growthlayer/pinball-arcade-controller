#!/usr/bin/env python3
"""Writes one short file per playfield sound (sounds/NN_name.wav), each repeated 3x, for going through them one at a time.
Uses the same synth voices as make_game_sounds.py."""
import os, struct, wave, importlib.util, sys
spec = importlib.util.spec_from_file_location("g", os.path.join(os.path.dirname(__file__) or ".", "make_game_sounds.py"))
src = open(spec.origin).read().split("t = 0.5")[0]            # just the voice functions, not the sequence
g = {}; exec(src, g)
SR = g["SR"]
def rep(sig, gap=0.6, n=3): out = []; [out.extend(sig + [0.0] * int(SR * gap)) for _ in range(n)]; return out
sounds = [("01_launch", rep(g["launch"]() + g["roll"](1.5, 0.8, 1.4))),
          ("02_rolling", g["roll"](4.0, 0.9)),
          ("03_flipper", rep(g["flipper"](), 0.8)),
          ("04_pop_bumper", rep(g["bumper"](), 0.8)),
          ("05_slingshot", rep(g["sling"](), 0.8)),
          ("06_ramp", g["roll"](3.5, 1.0, 1.6)),
          ("07_bumper_frenzy", sum([g["bumper"](0.8) + [0.0] * int(SR * 0.05) for _ in range(8)], [])),
          ("08_drain", rep(g["drain"](), 0.8, 2))]
os.makedirs("sounds", exist_ok=True)
pk = max(max(abs(v) for v in s) for _, s in sounds)
for name, s in sounds:
    gain = 0.891 / pk
    with wave.open(f"sounds/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<hh", int(v * gain * 32767), int(v * gain * 32767)) for v in s))
    print(name, f"{len(s)/SR:.1f}s")
