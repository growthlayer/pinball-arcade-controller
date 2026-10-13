# Slice every ready-made 3MF with Bambu Studio's CLI and report time, filament and warnings.
#    python tools/check_print_files.py [printer folder, default bambu-a1] [path\to\bambu-studio.exe]
import glob, json, os, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = sys.argv[1] if len(sys.argv) > 1 else "bambu-a1"
EXE = sys.argv[2] if len(sys.argv) > 2 else r"C:\Program Files\Bambu Studio\bambu-studio.exe"

for f in sorted(glob.glob(os.path.join(ROOT, "print", FOLDER, "*.3mf"))):
    out = tempfile.mkdtemp(prefix="pbslice_")
    subprocess.run([EXE, "--slice", "0", "--outputdir", out, f], cwd=out,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = os.path.join(out, "result.json")
    for _ in range(600):                        # the GUI build returns before it finishes
        if os.path.exists(res):
            break
        time.sleep(0.5)
    time.sleep(1)
    try:
        r = json.load(open(res))
        for p in r.get("sliced_plates", []):
            g = sum(x.get("total_used_g", 0) for x in p.get("filaments", []))
            print(f"{os.path.basename(f):22} plate {p.get('id')}: {p['total_predication'] / 3600:5.1f} h {g:6.0f} g  "
                  f"{p.get('warning_message', '') or 'ok'}")
        if r.get("return_code", 0) != 0:
            print(f"{os.path.basename(f):22} FAIL {r.get('error_string')}")
    except Exception as e:
        print(f"{os.path.basename(f):22} no result ({e})")
    shutil.rmtree(out, ignore_errors=True)
