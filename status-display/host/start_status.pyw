"""Windowless launcher for pinball_status.py (run with pythonw.exe, e.g. from the Startup folder).
Output goes to %LOCALAPPDATA%\\pinball-status\\status.log; a second copy exits if one is already running."""
import os, sys, socket
from pathlib import Path

log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "pinball-status"
log_dir.mkdir(parents=True, exist_ok=True)
log = open(log_dir / "status.log", "a", buffering=1, encoding="utf-8")
sys.stdout = sys.stderr = log

guard = socket.socket()                  # single instance: hold a local port for the life of the process
try:
    guard.bind(("127.0.0.1", 47833))
except OSError:
    print("already running - exiting")
    sys.exit(0)

here = Path(__file__).resolve().parent
os.chdir(here)
sys.path.insert(0, str(here))
import time
print(f"--- start {time.strftime('%Y-%m-%d %H:%M:%S')}")
import pinball_status
while True:                             # never leave the T-Display on its idle screen because of one bad read
    try:
        pinball_status.run(pinball_status.load_config(), sim=False)
    except Exception:
        import traceback
        traceback.print_exc()
        print(f"--- restarting {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(3)
