#!/usr/bin/env python3
"""Manual test: play the synthwave show on the marquee (ZeDMD, its CP2102 port found by itself) live from the PC, looping, 30 fps (stop the marquee
service first - it owns the port).
Uses libzedmd (zedmd64.dll from dmd-extensions) on an explicit port so it never probes the status
screen's port.   python tools/synthwave/play_marquee.py [COMx] [seconds, 0 = forever]"""
import ctypes, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402  (scene functions)

from marquee_service import DLL                      # noqa: E402  (RetroBat's zedmd64.dll, or ZEDMD_DLL)
from serial.tools import list_ports                 # noqa: E402
port = (sys.argv[1] if len(sys.argv) > 1 else
        next((p.device for p in list_ports.comports() if p.vid == 0x10C4), "COM3")).encode()
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 0

import os
os.add_dll_directory(os.path.dirname(DLL))           # libserialport64.dll sits beside zedmd64.dll
z_dll = ctypes.CDLL(DLL)
z_dll.ZeDMD_GetInstance.restype = ctypes.c_void_p
for fn, args in (("ZeDMD_SetDevice", [ctypes.c_void_p, ctypes.c_char_p]), ("ZeDMD_Open", [ctypes.c_void_p]),
                 ("ZeDMD_SetFrameSize", [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]),
                 ("ZeDMD_RenderRgb888", [ctypes.c_void_p, ctypes.c_void_p]), ("ZeDMD_Close", [ctypes.c_void_p])):
    getattr(z_dll, fn).argtypes = args
z_dll.ZeDMD_Open.restype = ctypes.c_bool

z = z_dll.ZeDMD_GetInstance()
z_dll.ZeDMD_SetDevice(z, port)
if not z_dll.ZeDMD_Open(z):
    sys.exit(f"could not open ZeDMD on {port.decode()}")
z_dll.ZeDMD_SetFrameSize(z, 128, 32)
print("marquee open on", port.decode(), flush=True)

t_end = time.time() + secs if secs else None
try:
    for name, frame in render.show():           # scenes + transitions, exactly as the service plays them
        t0 = time.perf_counter()
        z_dll.ZeDMD_RenderRgb888(z, np.ascontiguousarray(frame).ctypes.data)
        if t_end and time.time() > t_end:
            break
        time.sleep(max(0, 1 / render.FPS - (time.perf_counter() - t0)))
except KeyboardInterrupt:
    pass
finally:
    z_dll.ZeDMD_Close(z)
