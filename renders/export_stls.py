# Export what the Blender renders need from the OpenSCAD model:
#   renders/build/r_case.stl, r_cover.stl, r_marquee.stl  (printed parts, assembled position)
#   renders/build/layout.json                              (every component position, from the .scad)
#     python renders/export_stls.py [path\to\openscad.exe]
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files\OpenSCAD\openscad.exe"
SCAD = os.path.join(ROOT, "model", "pinball_controller_v2.scad")
OUT = os.path.join(ROOT, "renders", "build")
os.makedirs(OUT, exist_ok=True)

def run(part, ext="stl"):
    out = os.path.join(OUT, f"{part}.{ext}")
    r = subprocess.run([EXE, "-o", out, "-D", f'part="{part}"', SCAD], capture_output=True, text=True)
    print("ok  " if r.returncode == 0 else "FAIL", part)
    return out

with ThreadPoolExecutor(4) as ex:
    list(ex.map(run, ["r_case", "r_cover", "r_marquee"]))
echo = open(run("r_echo", "echo"), encoding="utf8").read()
lay = json.loads(re.search(r"RJSON(\{.*\})", echo).group(1))
json.dump(lay, open(os.path.join(OUT, "layout.json"), "w"), indent=1)
print("layout.json:", len(lay), "keys")
