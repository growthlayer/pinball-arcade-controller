#!/usr/bin/env python3
"""Marquee service - the one owner of the ZeDMD marquee (its CP2102 COM port, found by itself).

  RetroBat closed          -> the synthwave show (render.show())
  browsing RetroBat        -> the selected game's marquee art (roms/<sys>/images/<rom>-marquee.png, else the
                              MarqueeManager topper), or its name in neon when there is no art; system names in neon
  arcade/console game      -> keeps showing that game's marquee while you play
  pinball game (VPX etc.)  -> lets go of the port so dmd-extensions drives the real game DMD; takes it back afterwards

RetroBat's ESEventPush.bat hooks (game-selected / system-selected / game-start / game-end) write ESEvent.arg; we
poll it. Run windowless via start_marquee.pyw (Startup folder).   python marquee_service.py [COMx]   (RetroBat: RETROBAT_DIR or auto)
"""
import ctypes, math, os, re, sys, time
from pathlib import Path
import numpy as np
import psutil
from serial.tools import list_ports
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

PORT_ARG = sys.argv[1] if len(sys.argv) > 1 else None     # default: the first CP2102 (VID 10C4) COM port

def find_port():
    """the ZeDMD's COM port name, or None while it is unplugged"""
    for p in list_ports.comports():
        if (PORT_ARG and p.device.upper() == PORT_ARG.upper()) or (not PORT_ARG and p.vid == 0x10C4):
            return p.device
    return None

def find_retrobat():
    """RETROBAT_DIR if set, else the first X:/RetroBat that exists"""
    env = os.environ.get("RETROBAT_DIR")
    if env:
        return Path(env)
    for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        if Path(f"{drive}:/RetroBat/emulationstation").exists():
            return Path(f"{drive}:/RetroBat")
    return Path("C:/RetroBat")

RB = find_retrobat()
DLL = os.environ.get("ZEDMD_DLL", str(RB / "emulators" / "vpinball" / "VPinMAME" / "zedmd64.dll"))
ARG = RB / "plugins" / "MarqueeManager" / "ESEvent.arg"
ROMS = RB / "roms"
TV_BOOST_FILE = Path(r"C:\Program Files\EqualizerAPO\config\pinball_tv.txt")   # optional: Include it in Equalizer APO's config for the room speakers
TV_BOOST_DB = 18                       # PinMAME's ROM audio is far quieter on the TV than everything else
# +18 dB alone pushed loud moments past full scale and the TV briefly muted; LoudMax (free look-ahead brickwall
# limiter, VSTPlugins\LoudMax64.dll) catches the peaks at about -1 dBFS. Params are normalised 0..1.
TV_LIMITER = "\n".join((                  # the TV is an 8-channel device; pinball audio is stereo (L R)
    "Channel: L R",
    r'VSTPlugin: Library "VSTPlugins\LoudMax64.dll" Thresh 1 Output 0.97 "Fader Link" 0 "ISP Detection" 1',
    "Channel: all"))
DMDLOG = RB / "emulators" / "vpinball" / "DmdDevice.log"
TOPPERS = RB / "plugins" / "MarqueeManager" / "images"
DMD_SYSTEMS = {"vpinball", "fpinball", "pinballfx", "pinballfx2", "pinballfx3", "pinballm", "zaccariapinball"}
DMD_PROCS = ("vpinballx", "futurepinball", "pinballfx", "pinballm")      # process-name prefixes that own the DMD
W, H, FPS = render.W, render.H, render.FPS


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------ device
class Marquee:
    def __init__(self):
        os.add_dll_directory(os.path.dirname(DLL))       # libserialport64 + sockpp64 sit beside zedmd64
        d = self.d = ctypes.CDLL(DLL)
        d.ZeDMD_GetInstance.restype = ctypes.c_void_p
        for fn, args in (("ZeDMD_SetDevice", [ctypes.c_void_p, ctypes.c_char_p]), ("ZeDMD_Open", [ctypes.c_void_p]),
                         ("ZeDMD_SetFrameSize", [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]),
                         ("ZeDMD_RenderRgb888", [ctypes.c_void_p, ctypes.c_void_p]), ("ZeDMD_Close", [ctypes.c_void_p])):
            getattr(d, fn).argtypes = args
        d.ZeDMD_Open.restype = ctypes.c_bool
        self.z, self.retry_at, self.fails, self.seen_at = None, 0.0, 0, None
        # libzedmd reports transport errors ("StreamBytes failed", "Full frame forced, error ...") through a log
        # callback. If the ESP32 reboots while the port stays present, frames go nowhere and the marquee stays dark -
        # these messages are the only sign, so they trigger a clean reconnect.
        self.link_error_at, self.log_n = 0.0, 0
        d.ZeDMD_FormatLogMessage.restype = ctypes.c_char_p
        d.ZeDMD_FormatLogMessage.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p]
        cbtype = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p)
        def on_log(fmt, args, user):
            try:
                msg = (d.ZeDMD_FormatLogMessage(fmt, args, user) or fmt or b"").decode("utf-8", "replace")
            except Exception:
                msg = (fmt or b"").decode("utf-8", "replace")
            low = msg.lower()
            # only errors from the frame stream count (the handshake logs a harmless "response error" on connect)
            if "streambytes failed" in low or "full frame forced" in low or "libserialport error" in low:
                self.link_error_at = time.time()
            if self.log_n < 200:                            # keep the log readable
                self.log_n += 1
                log("libzedmd:", msg.strip())
        self._cb = cbtype(on_log)                          # keep a reference: ctypes callbacks must not be freed
        d.ZeDMD_SetLogCallback.argtypes = [ctypes.c_void_p, cbtype, ctypes.c_void_p]

    # Every open resets the ESP32, and ZeDMD needs ~8 s to boot (it starts with a red/green/blue panel test).
    # Retrying every 5 s reset it mid-boot forever - the marquee sat on RED and never answered. So: wait for the
    # port to settle after it appears, and back off 15 -> 30 -> 60 s between failed attempts.
    BOOT_GRACE, BACKOFF = 10.0, (15.0, 30.0, 60.0)

    def open(self):
        now = time.time()
        if self.z or now < self.retry_at:
            return bool(self.z)
        port = find_port()
        if not port:
            self.seen_at = None
            self.retry_at = now + 2
            return False
        if self.seen_at is None:                           # port just (re)appeared: let the ESP32 finish booting
            self.seen_at = now
            self.retry_at = now + self.BOOT_GRACE
            log(port, "appeared - waiting", int(self.BOOT_GRACE), "s for ZeDMD to boot")
            return False
        z = self.d.ZeDMD_GetInstance()
        self.d.ZeDMD_SetLogCallback(z, self._cb, None)
        self.d.ZeDMD_SetDevice(z, port.encode())
        if not self.d.ZeDMD_Open(z):
            wait = self.BACKOFF[min(self.fails, len(self.BACKOFF) - 1)]
            self.fails += 1
            log("could not open", port, f"- next try in {int(wait)} s (lets the ESP32 finish booting)")
            self.retry_at = now + wait
            return False
        self.d.ZeDMD_SetFrameSize(z, W, H)
        self.z, self.fails, self.link_error_at = z, 0, 0.0
        log("marquee open on", port)
        return True

    def close(self):
        if self.z:
            self.d.ZeDMD_Close(self.z)
            self.z = None
            log("marquee released")

    def send(self, frame):
        if self.z and self.link_error_at and time.time() - self.link_error_at < 2:
            log("marquee stopped acknowledging frames - reconnecting")
            self.link_error_at = 0.0
            self.close()
            self.seen_at, self.fails = None, 0            # treat as a fresh boot: wait for it, then reopen
            return
        if self.open():
            f = np.ascontiguousarray(frame, np.uint8)
            self.d.ZeDMD_RenderRgb888(self.z, f.ctypes.data)


# ------------------------------------------------------------------ RetroBat events
def read_event():
    """event=game-selected&param1="vpinball"&param2="R:/.../x.vpx"&param3="Name" -> dict"""
    try:
        raw = ARG.read_bytes().decode("oem", errors="replace").strip()
    except OSError:
        return None
    ev = {"event": (re.match(r"event=([\w-]+)", raw) or [None, ""])[1]}
    for k, v in re.findall(r"param(\d+)=\"(.*?)\"(?=&param|\s*$)", raw):
        ev[f"p{k}"] = v.replace("|A", "&").replace("|v", ",").replace("|p", "+").replace('""', '"')
    return ev


def art_for(system, rom):
    if not rom:
        return None
    stem = Path(rom).stem
    for p in (Path(rom).parent / "images" / f"{stem}-marquee.png", ROMS / system / "images" / f"{stem}-marquee.png",
              ROMS / system / "images" / f"{stem}-marquee.jpg", TOPPERS / system / f"{stem}-topper.png"):
        if p.is_file():
            return p
    return None


def dmd_link_dead():
    """dmd-extensions never reconnects after the ZeDMD drops off USB (controller hub reset): the log then repeats
    'StreamBytes failed' every ~0.1 s and the ZeDMD falls back to its built-in idle screen."""
    try:
        if time.time() - DMDLOG.stat().st_mtime > 3:
            return False
        with open(DMDLOG, "rb") as f:
            f.seek(max(0, DMDLOG.stat().st_size - 600))
            tail = f.read().decode("utf-8", "replace").strip().splitlines()
        return bool(tail) and "StreamBytes failed" in tail[-1]
    except OSError:
        return False


def tv_boost(on):
    """Equalizer APO re-reads its config on change: boost the room speakers only while a table runs.
    Optional - does nothing unless pinball_tv.txt already exists (create it once and Include it in config.txt)."""
    if not TV_BOOST_FILE.exists():
        return
    try:
        TV_BOOST_FILE.write_text("# written by the pinball marquee service: TV boost while a table runs\n"
                                 f"Preamp: {TV_BOOST_DB if on else 0} dB\n" + (TV_LIMITER + "\n" if on else ""),
                                 encoding="ascii")
        log("TV boost", f"+{TV_BOOST_DB} dB" if on else "off")
    except OSError as e:
        log("TV boost write failed:", e)


# ------------------------------------------------------------------ VPX focus
# VPX reads the controller only while its window is in front. Windows won't let a newly started VPX take focus
# from whatever app the user last clicked (e.g. a chat window on the same screen) - so for the first seconds of a
# table we push its window to the front ourselves, and after a USB reset we bounce focus so it re-acquires input.
import ctypes.wintypes as wt
_u = ctypes.windll.user32
_u.GetForegroundWindow.restype = wt.HWND
_ENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def _pid_of(h):
    pid = wt.DWORD()
    _u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    return pid.value


def vpx_window(pids):
    """the table's player window (class VPPlayer) - NOT the minimised editor window, which grabs focus at launch"""
    best, area = None, 0
    for h in vpx_windows(pids):
        c = ctypes.create_unicode_buffer(64)
        _u.GetClassNameW(h, c, 64)
        if c.value == "VPPlayer":
            return h
        r = wt.RECT()
        _u.GetWindowRect(h, ctypes.byref(r))
        a = (r.right - r.left) * (r.bottom - r.top)
        if not _u.IsIconic(h) and a > 200 * 200 and a > area:
            best, area = h, a
    return best


def describe(h):
    t, c, r = ctypes.create_unicode_buffer(128), ctypes.create_unicode_buffer(64), wt.RECT()
    _u.GetWindowTextW(h, t, 128); _u.GetClassNameW(h, c, 64); _u.GetWindowRect(h, ctypes.byref(r))
    return f"{t.value!r}/{c.value} {r.right - r.left}x{r.bottom - r.top}@{r.left},{r.top} pid{_pid_of(h)}"


def vpx_windows(pids):
    out = []
    _u.EnumWindows(_ENUM(lambda h, _: (out.append(h) if _u.IsWindowVisible(h) and _pid_of(h) in pids else None) or True), 0)
    return out


def force_front(h):
    _u.keybd_event(0x12, 0, 0, 0)                      # a synthetic Alt tap grants this process foreground rights
    _u.keybd_event(0x12, 0, 2, 0)
    _u.ShowWindow(h, 9 if _u.IsIconic(h) else 5)
    _u.BringWindowToTop(h)
    return bool(_u.SetForegroundWindow(h))


def vpx_has_focus(h):
    return _u.GetForegroundWindow() == h


FOCUS_OK_TO_TAKE = {"emulationstation.exe", "explorer.exe", "emulatorlauncher.exe", "retrobat.exe"}


def focus_is_strandable(pids):
    """only take focus back from VPX's own (hidden editor) window, RetroBat or the desktop - never from an app the
    user switched to on purpose (Alt-Tab / Task Switching, a browser, the Claude window...)"""
    fg = _u.GetForegroundWindow()
    if not fg:
        return True
    pid = _pid_of(fg)
    if pid in pids:
        return True
    try:
        return psutil.Process(pid).name().lower() in FOCUS_OK_TO_TAKE
    except psutil.Error:
        return False


def keep_vpx_in_front(vpx, fs):
    """called every 0.5 s with {pid: start time} of running pinball players"""
    if not vpx:
        fs.update(tries=0, bounce_at=0.0, player=None)
        return
    pids = set(vpx)
    now = time.time()
    h = vpx_window(pids)
    if h and h != fs.get("player"):
        fs.update(player=h, seen=now, tries=0)             # a new player window: the table is up
    if h and now - fs["seen"] < 60 and fs["tries"] < 40 and not vpx_has_focus(h) and focus_is_strandable(pids):
        fs["tries"] += 1
        fg = _u.GetForegroundWindow()
        log("player window not in front - bringing it forward:", force_front(h), "| fg was", describe(fg))
    # USB reset (the marquee's CP2102 vanishes and comes back with the rest of the hub): VPX's DirectInput only
    # re-acquires the encoder on a focus change, so bounce focus once everything is back
    esp = any(p.vid == 0x10C4 for p in list_ports.comports())
    if esp and not fs["esp"]:
        fs["bounce_at"] = now + 2.0
        log("controller hub came back during a table - refocusing VPX in 2 s")
    fs["esp"] = esp
    if fs["bounce_at"] and now >= fs["bounce_at"]:
        fs["bounce_at"] = 0.0
        h = vpx_window(pids)
        if h:
            force_front(_u.GetShellWindow())
            time.sleep(0.15)
            log("refocused VPX:", force_front(h))


# ------------------------------------------------------------------ content generators (yield HxWx3 floats)
def art_scene(path):
    """marquee art fitted to 128x32; letterbox filled with a blurred, dimmed copy; a glint sweeps by every 6 s"""
    src = Image.open(path).convert("RGB")
    fit = src.copy()
    fit.thumbnail((W, H), Image.LANCZOS)
    bg = src.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    base = np.asarray(bg, np.float32) * 0.25
    x0, y0 = (W - fit.width) // 2, (H - fit.height) // 2
    base[y0:y0 + fit.height, x0:x0 + fit.width] = np.asarray(fit, np.float32)
    i = 0
    while True:
        t = (i / FPS) % 6.0
        pos = render.XX + render.YY * 0.8
        band = np.clip(1 - np.abs(pos - (t * 60 - 20)) / 4, 0, 1)[..., None] * 0.35
        yield base + (255 - base) * band
        i += 1


def text_scene(text, sub=None):
    """name in neon over a slow synthwave floor; long names scroll"""
    text = text.upper()
    m = render.tmask(text, size=15 if len(text) < 14 else 13)
    g, pad = render.tglow(text, size=15 if len(text) < 14 else 13, radius=1.8, strength=1.6)
    h, w = m.shape
    i = 0
    while True:
        t = i / FPS
        fb = np.zeros((H, W, 3), np.float32)
        neon = np.zeros_like(fb)
        render.sky(fb, t, 25, seed=9, drift=0.4)
        render.grid(fb, neon, 25, t, speed=0.6, col=render.PURPLE)
        render.bloom(fb, neon, 0.7)
        x = (W - w) // 2 if w <= W - 4 else int(W - (t * 30) % (w + W))
        y = 4
        render.blit(fb, g, x - pad, y - pad, render.HOT)
        render.blit(fb, m, x, y, render.chrome(h, w))
        yield fb
        i += 1


def show_scene():
    for _, f in render.show():
        yield f.astype(np.float32)


# ------------------------------------------------------------------ main loop
def main():
    mq = Marquee()
    content_key, content, last, frozen = None, None, None, None
    trans, tk = 0, 0
    ev, ev_mtime, procs, next_poll = None, 0.0, {}, 0.0
    in_game = None                         # (system, rom) between game-start and game-end
    dmd_dead_since, next_dmd_check = 0.0, 0.0
    boosted = None
    fs = {"tries": 0, "esp": True, "bounce_at": 0.0, "player": None, "seen": 0.0}  # focus-keeper state
    log("marquee service up")
    while True:
        t0 = time.perf_counter()
        if t0 >= next_poll:
            next_poll = t0 + 0.5
            procs, vpx = {}, {}
            for p in psutil.process_iter(["name", "create_time"]):
                n = (p.info["name"] or "").lower()
                procs[n] = p.info["create_time"] or 0
                if n.startswith(DMD_PROCS):
                    vpx[p.pid] = p.info["create_time"] or 0
            keep_vpx_in_front(vpx, fs)
            esp_now = any(p.vid == 0x10C4 for p in list_ports.comports())
            if not esp_now and (mq.z or mq.fails or mq.seen_at):
                if mq.z:                                   # marquee dropped off USB: drop the dead handle so we reopen
                    log("marquee ESP32 gone from USB - closing the stale handle")
                    mq.close()
                # a replug restarts the ESP32: forget the back-off so the fresh boot is picked up promptly
                mq.fails, mq.seen_at, mq.retry_at = 0, None, 0.0
            try:
                mt = ARG.stat().st_mtime
            except OSError:
                mt = 0
            if mt != ev_mtime:
                ev_mtime, ev = mt, read_event()
                log("event", ev)
                if ev and ev["event"] in ("game-start", "game-end"):
                    # these hooks pass (rom path, rom name, game name) - no system id; take it from roms\<system>\
                    rom = ev.get("p1", "")
                    parts = [s.lower() for s in Path(rom).parts]
                    ev = {"event": ev["event"], "p1": parts[parts.index("roms") + 1] if "roms" in parts[:-1] else "",
                          "p2": rom, "p3": ev.get("p3", "")}
                if ev and ev["event"] == "game-start":
                    in_game = (ev.get("p1", ""), ev.get("p2", ""))
                elif ev and ev["event"] in ("game-end", "system-selected", "game-selected"):
                    in_game = None
        es_start = procs.get("emulationstation.exe")
        pin_running = any(n.startswith(DMD_PROCS) for n in procs)
        pin_game = in_game is not None and in_game[0] in DMD_SYSTEMS
        if pin_running != boosted:
            boosted = pin_running
            tv_boost(boosted)
        if not (pin_running or pin_game):
            dmd_dead_since = 0.0
        elif dmd_dead_since and ev and ev["event"] == "game-start" and ev_mtime > dmd_dead_since:
            dmd_dead_since = 0.0                           # a new table is starting: hand the marquee back
        if (pin_running or pin_game) and not dmd_dead_since and t0 >= next_dmd_check:
            next_dmd_check = t0 + 1.0
            if dmd_link_dead():
                dmd_dead_since = time.time()
                log("game DMD link died (USB reset) - taking the marquee back for the rest of the game")
        if (pin_running or pin_game) and not dmd_dead_since:   # the game's own DMD owns the marquee
            if mq.z:
                mq.close()
            content_key = None
            time.sleep(0.5)
            continue
        cur = ev
        if dmd_dead_since:                                 # game DMD lost: show the running table's art
            cur = {"event": "game-start", "p1": in_game[0], "p2": in_game[1], "p3": ev.get("p3", "")} if in_game else None
        if cur and (dmd_dead_since or (es_start and ev_mtime >= es_start - 2)):
            sysid, rom, name = cur.get("p1", ""), cur.get("p2", ""), cur.get("p3", "")
            if cur["event"] == "system-selected":
                key = ("sys", sysid)
            else:
                key = ("game", sysid, rom)
        else:
            key = ("show",)
        if key != content_key:
            content_key = key
            if key[0] == "show":
                content = show_scene()
            elif key[0] == "sys":
                content = text_scene(sysid)
            else:
                art = art_for(sysid, rom)
                content = art_scene(art) if art else text_scene(name or Path(rom).stem)
            log("showing", key, "art" if key[0] == "game" and art_for(sysid, rom) else "")
            frozen, trans, tk = last, (10 if last is not None else 0), tk + 1
        frame = next(content)
        if trans:                                          # quick neon wipe / glitch between contents
            p = 1 - (trans - 1) / 11
            frame = (render.t_wipe, render.t_glitch)[tk % 2](frozen, frame, p, tk * 31 + trans)
            trans -= 1
        last = np.clip(frame, 0, 255)
        mq.send(last.astype(np.uint8))
        time.sleep(max(0, 1 / FPS - (time.perf_counter() - t0)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
