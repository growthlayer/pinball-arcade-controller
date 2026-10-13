#!/usr/bin/env python3
"""Drive the status display with fake game data, to check the screen without the PC side.

Usage:  .venv-esp/bin/python status-display/tools/demo.py [port]
Without a port it tries every /dev/cu.usbmodem* and keeps the one that answers HELLO.
"""
import glob, math, sys, time
import serial  # pyserial - installed with esptool in .venv-esp


def find_port():
    for p in ([sys.argv[1]] if len(sys.argv) > 1 else sorted(glob.glob("/dev/cu.usbmodem*"))):
        try:
            s = serial.Serial(p, 115200, timeout=1)
            time.sleep(0.3)
            s.reset_input_buffer()
            s.write(b"HELLO\n")
            if s.readline().decode(errors="ignore").startswith("STATUS-DISPLAY"):
                return s
            s.close()
        except serial.SerialException:
            pass
    sys.exit("status display not found")


s = find_port()
print("found", s.port)


def send(line):
    s.write((line + "\n").encode())


send("CLEAR")
send("TABLE Medieval Madness")
heat, t0 = [0.0, 0.0], time.time()
while True:
    t = time.time() - t0
    phase = int(t) % 20
    send(f"NUDGE {int(90 * math.sin(t * 2.1) * (phase > 12))} {int(60 * math.sin(t * 1.3))}")
    mashing = phase < 8                       # fake: hammer the flippers for 8 s, then rest
    heat = [min(100.0, h + 1.2) if mashing and (i == 0 or phase % 2) else max(0.0, h - 0.4) for i, h in enumerate(heat)]
    send(f"HEAT {int(heat[0])} {int(heat[1])}")
    send(f"TILT {0 if phase < 14 else 1 if phase < 16 else 2 if phase < 18 else 3}")
    send(f"MSG {'mashing both flippers' if mashing else 'resting'}")
    time.sleep(0.05)
