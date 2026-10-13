"""Windowless launcher for exciter_relay.py (run with pythonw.exe from the Startup folder).
Output goes to %LOCALAPPDATA%\\pinball-status\\exciter.log; a second copy exits if one is already running."""
import os, sys, socket
from pathlib import Path

log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "pinball-status"
log_dir.mkdir(parents=True, exist_ok=True)
log = open(log_dir / "exciter.log", "a", buffering=1, encoding="utf-8")
sys.stdout = sys.stderr = log

guard = socket.socket()                  # single instance: hold a local port for the life of the process
try:
    guard.bind(("127.0.0.1", 47835))
except OSError:
    print("already running - exiting")
    sys.exit(0)

here = Path(__file__).resolve().parent
os.chdir(here)
sys.path.insert(0, str(here))
import time
print(f"--- start {time.strftime('%Y-%m-%d %H:%M:%S')}")
import exciter_relay
exciter_relay.main()
