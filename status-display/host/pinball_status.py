#!/usr/bin/env python3
"""PC helper for the status display: reads the controller, models tilt and coil heat, feeds the T-Display.

  python pinball_status.py --list     show gamepads + live axes/buttons (find the flipper buttons)
  python pinball_status.py            run (uses config.json beside this file)
  python pinball_status.py --sim      fake nudges and flipper presses - test the display without the controller

Needs: pip install pygame pyserial
Runs on Windows (the game PC) and macOS (bench). The table name comes from the VPX window title (Windows only).
"""
import argparse, json, math, os, random, re, sys, time
from pathlib import Path

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"   # keep reading while VPX has focus
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
import serial
from serial.tools import list_ports

DEFAULTS = {
    "port": None,                      # e.g. "COM7"; None = find the display by asking every port HELLO
    "nudge": {"device": ["pinscape"], "axis_x": 0, "axis_y": 1, "invert_x": False, "invert_y": False,
              "full_scale": 1.0},      # axis value that maps to 100 on the meter
    "flippers": {"device": ["dragonrise", "generic usb joystick", "usb gamepad"],
                 "left_button": None, "right_button": None},   # set with --list
    "coil": {"pulse_s": 0.1,           # XY-J02 one-shot per press (P1.1, OP 0.1 s)
             "overheat_duty": 0.45,    # sustained on-time fraction that reads 100 (README: ~45 % overheats)
             "tau_s": 90},             # thermal time constant of the estimate
    "tilt": {"threshold": 60,          # nudge magnitude (0-100) that counts as a hard nudge
             "window_s": 4.0},         # hard nudges within this window: 1-2 = warnings, 3 = TILT
    "table_from_window": True,
}


def load_config():
    cfg = json.loads(json.dumps(DEFAULTS))
    p = Path(__file__).with_name("config.json")
    if p.exists():
        for k, v in json.loads(p.read_text()).items():
            if isinstance(v, dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


# ---------------------------------------------------------------- display link
class Display:
    def __init__(self, port):
        self.want, self.s, self.next_try = port, None, 0

    def _open(self):
        # Only probe Espressif native-USB ports (VID 0x303A = the T-Display-S3). Never poke other serial devices:
        # the marquee's ZeDMD ESP32 (CP2102, VID 0x10C4) sits on the same PC, and a stray HELLO corrupts it
        # (it broke an esptool flash on 2026-09-28).
        ports = [self.want] if self.want else [p.device for p in list_ports.comports() if p.vid == 0x303A]
        for dev in ports:
            try:
                s = serial.Serial(dev, 115200, timeout=0.5, write_timeout=0.5)
                time.sleep(0.2)
                s.reset_input_buffer()
                s.write(b"HELLO\n")
                if s.readline().decode(errors="ignore").startswith("STATUS-DISPLAY"):
                    print("display on", dev)
                    return s
                s.close()
            except (serial.SerialException, OSError):
                pass
        return None

    def send(self, *lines):
        if not self.s and time.time() >= self.next_try:
            self.s = self._open()
            self.next_try = time.time() + 3
        if not self.s:
            return False
        try:
            self.s.write("".join(l + "\n" for l in lines).encode())
            return True
        except (serial.SerialException, OSError):
            print("display lost - retrying")
            self.s = None
            return False


# ---------------------------------------------------------------- models
class CoilHeat:
    """First-order thermal estimate: heat settles at 100 * duty / overheat_duty with time constant tau."""
    def __init__(self, c):
        self.pulse, self.full, self.tau, self.h = c["pulse_s"], c["overheat_duty"], c["tau_s"], 0.0

    def step(self, presses, dt):
        on = presses * self.pulse
        self.h += ((100.0 / self.full) * on - self.h * dt) / self.tau
        self.h = max(0.0, min(100.0, self.h))
        return int(self.h)


class Tilt:
    def __init__(self, c):
        self.thr, self.win, self.hits, self.above = c["threshold"], c["window_s"], [], False

    def step(self, mag, now):
        if mag >= self.thr and not self.above:
            self.hits.append(now)
        self.above = mag >= self.thr * 0.8          # hysteresis: one shove = one hit
        self.hits = [t for t in self.hits if now - t < self.win]
        return min(3, len(self.hits))


def vpx_table_name():
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes
    user32, found = ctypes.windll.user32, []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                m = re.search(r"([^\\/\[\]]+?)\.vpx", buf.value, re.I)
                if m:
                    found.append(m.group(1).strip())
        return True

    user32.EnumWindows(cb, 0)
    return found[0] if found else None


# ---------------------------------------------------------------- input
def find_joystick(names):
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        if any(n.lower() in j.get_name().lower() for n in names):
            return j
    return None


def list_mode():
    pygame.init()
    pygame.joystick.init()
    js = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    if not js:
        print("no gamepads found")
        return
    for i, j in enumerate(js):
        print(f"[{i}] {j.get_name()!r}: {j.get_numaxes()} axes, {j.get_numbuttons()} buttons")
    print("\npress buttons / nudge the box (Ctrl-C to stop)")
    while True:
        for e in pygame.event.get():
            if e.type == pygame.JOYBUTTONDOWN:
                print(f"{js[e.instance_id if e.instance_id < len(js) else 0].get_name()}: button {e.button}")
            elif e.type == pygame.JOYAXISMOTION and abs(e.value) > 0.2:
                print(f"axis {e.axis} = {e.value:+.2f}")
        time.sleep(0.01)


def run(cfg, sim):
    pygame.init()
    pygame.joystick.init()
    disp = Display(cfg["port"])
    heat_l, heat_r, tilt = CoilHeat(cfg["coil"]), CoilHeat(cfg["coil"]), Tilt(cfg["tilt"])
    nud, fl = cfg["nudge"], cfg["flippers"]
    jn = jf = None
    table, last_table_check, last = None, 0, time.time()
    next_scan, last_flip = 0.0, -9.0
    if not sim and (fl["left_button"] is None or fl["right_button"] is None):
        print("flipper buttons not set in config.json - run with --list to find them; heat stays at 0")

    while True:
        now = time.time()
        dt, last = now - last, now
        if not sim and (jn is None or jf is None) and now >= next_scan:
            # joystick.quit() invalidates EVERY open joystick, so re-find both (keeping a stale one crashed
            # get_axis with "Joystick not initialized" every 4 s - the T-Display flickered on each restart)
            next_scan = now + 2.0
            pygame.joystick.quit(); pygame.joystick.init()
            jn, jf = find_joystick(nud["device"]), find_joystick(fl["device"])

        pl = pr = 0
        raw = 0.0
        try:
            events = pygame.event.get()
        except (SystemError, pygame.error) as ex:      # SDL chokes when the Pinscape re-enumerates mid-read
            print("joystick event error - reopening:", ex)
            jn = jf = None
            events = []
        for e in events:
            if e.type == pygame.JOYBUTTONDOWN and jf is not None and e.instance_id == jf.get_instance_id():
                pl += e.button == fl["left_button"]
                pr += e.button == fl["right_button"]
            elif e.type == pygame.JOYDEVICEREMOVED:
                jn = jf = None

        if sim:
            phase = now % 30
            x = int(80 * math.sin(now * 3.0)) if 20 < phase < 26 else int(8 * math.sin(now))
            y = int(10 * math.sin(now * 1.7))
            rate = 5.0 if phase < 12 else 0.8                    # presses per second
            pl += random.random() < rate * dt
            pr += random.random() < rate * dt * 0.7
        else:
            x = y = 0
            raw = 0.0
            if jn is not None:
                try:
                    raw = max(abs(jn.get_axis(nud["axis_x"])), abs(jn.get_axis(nud["axis_y"])))
                    fx = jn.get_axis(nud["axis_x"]) / nud["full_scale"] * (-1 if nud["invert_x"] else 1)
                    fy = jn.get_axis(nud["axis_y"]) / nud["full_scale"] * (-1 if nud["invert_y"] else 1)
                    x, y = int(max(-1, min(1, fx)) * 100), int(max(-1, min(1, -fy)) * 100)
                except pygame.error:                         # device went away mid-read: rescan
                    jn = jf = None

        if pl or pr:
            last_flip = now
        # each coil knock jolts the case ~0.3-0.4 on the accelerometer (measured 2026-10-12) - not a nudge, so it
        # must not count toward DANGER/TILT for ~0.5 s after a flipper press (the knock lands ~0.1 s after it)
        # A coil knock jolts the case 0.27-0.42 (measured). Two guards, both always on, because the encoder can be
        # listed yet deliver no presses (low-speed device behind a 12 Mbps USB isolator):
        #  - nothing counts for 0.5 s after a flipper press we DID see;
        #  - only a jolt stronger than any knock (raw >= 0.5) counts at all.
        strong = raw >= cfg["tilt"].get("raw_min", 0.5)
        mag = 100 if strong and now - last_flip >= 0.5 else 0
        lines = [f"NUDGE {x} {y}", f"HEAT {heat_l.step(pl, dt)} {heat_r.step(pr, dt)}",
                 f"TILT {tilt.step(mag, now)}"]
        if now - last_table_check > 2:
            last_table_check = now
            table = "Simulated table" if sim else (vpx_table_name() if cfg["table_from_window"] else None)
            lines.append(f"TABLE {table or 'Pinball controller'}")
            state = "sim" if sim else ("nudge ok" if jn else "no nudge dev") + " · " + ("flippers ok" if jf else "no flippers")
            lines.append(f"MSG {state}")
        disp.send(*lines)
        time.sleep(0.05)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="show gamepads and live input")
    ap.add_argument("--sim", action="store_true", help="fake input, to test the display")
    a = ap.parse_args()
    try:
        list_mode() if a.list else run(load_config(), a.sim)
    except KeyboardInterrupt:
        pass
