"""Windowless launcher for marquee_service.py (run with pythonw.exe from the Startup folder).
Output goes to %LOCALAPPDATA%\\pinball-status\\marquee.log; a second copy exits if one is already running."""
import os, sys, socket
from pathlib import Path

log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "pinball-status"
log_dir.mkdir(parents=True, exist_ok=True)
log = open(log_dir / "marquee.log", "a", buffering=1, encoding="utf-8")
sys.stdout = sys.stderr = log

guard = socket.socket()                  # single instance: hold a local port for the life of the process
try:
    guard.bind(("127.0.0.1", 47834))
except OSError:
    print("already running - exiting")
    sys.exit(0)

here = Path(__file__).resolve().parent
os.chdir(here)
sys.path.insert(0, str(here))
sys.argv = [sys.argv[0]]                 # the service finds the ZeDMD port itself
import time
print(f"--- start {time.strftime('%Y-%m-%d %H:%M:%S')}")
import marquee_service
marquee_service.tv_boost(False)          # never inherit a boost from a run that died mid-table
try:
    marquee_service.main()
finally:
    marquee_service.tv_boost(False)      # a TV left at +18 dB turns the noise floor into audible static
