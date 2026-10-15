# ============================================================
#  Build the print files from the OpenSCAD model.
#
#    python tools/make_print_files.py [path\to\bambu-studio.exe] [path\to\openscad.exe]
#
#  1. print/stl/*.stl - every printed part, in print orientation
#  2. print/bambu-<printer>/*.3mf - ready-to-print Bambu Studio projects
#     for the A1, P1S and X1C: model + printer + plate + filament + each
#     part's process settings (walls, infill, brim) built in.
# ============================================================
import glob, json, os, shutil, subprocess, sys, tempfile, time, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files\Bambu Studio\bambu-studio.exe"
SCAD_EXE = sys.argv[2] if len(sys.argv) > 2 else r"C:\Program Files\OpenSCAD\openscad.exe"
SCAD = os.path.join(ROOT, "model", "pinball_controller_v2.scad")
BBL = os.path.join(os.path.dirname(EXE), "resources", "profiles", "BBL")
STL = os.path.join(ROOT, "print", "stl")

# STL name -> OpenSCAD part (all exported already in print orientation)
PARTS = {"case": "case_print", "cover": "cover", "marquee_tray_left": "marquee_tray_left",
         "marquee_tray_right": "marquee_tray_right", "marquee_plate": "marquee_plate",
         "td_clamp": "td_clamp", "exciter_bridge": "exc_bridge", "test_fit": "test_fit", "screw_test": "screw_test"}

PRINTERS = {          # folder: (machine, process base, filament)
    "a1":  ("Bambu Lab A1 0.4 nozzle", "0.20mm Standard @BBL A1", "Bambu PLA Matte @BBL A1"),
    "p1s": ("Bambu Lab P1S 0.4 nozzle", "0.20mm Standard @BBL X1C", "Bambu PLA Matte @BBL X1C"),
    "x1c": ("Bambu Lab X1 Carbon 0.4 nozzle", "0.20mm Standard @BBL X1C", "Bambu PLA Matte @BBL X1C"),
}
COMMON = {
    "wall_loops": "4", "top_shell_layers": "5", "bottom_shell_layers": "5",
    "sparse_infill_density": "20%", "sparse_infill_pattern": "gyroid",
    "enable_support": "0", "seam_position": "back", "elefant_foot_compensation": "0.15",
    "brim_type": "no_brim", "skirt_loops": "0", "curr_bed_type": "Textured PEI Plate",
}
PROCESSES = {         # process name -> overrides on COMMON
    "case": {},                                                    # 254 mm: no room for a brim
    "cover": {"brim_type": "outer_only", "brim_width": "4", "sparse_infill_density": "25%"},
    "small": {},
}
FILAMENT = {"filament_max_volumetric_speed": ["15"],               # the case's solid top panel needs the slower flow
            "textured_plate_temp_initial_layer": ["65"], "textured_plate_temp": ["55"]}
SETS = {              # 3MF name -> (process, STLs)
    "case": ("case", ["case"]),
    "cover": ("cover", ["cover"]),
    "marquee_trays": ("small", ["marquee_tray_left", "marquee_tray_right"]),
    "marquee_plate": ("small", ["marquee_plate"]),
    "small_parts": ("small", ["td_clamp", "exciter_bridge"]),
    "test_prints": ("small", ["test_fit", "screw_test"]),
}
META = {"Title": "Pinball controller - 3D-printed arcade + virtual pinball controller",
        "License": "CC BY-SA 4.0",
        "Description": "Build guide, wiring and parts list: github.com/growthlayer/visual-pinball-controller",
        "ProfileTitle": "0.20mm PLA Matte, 4 walls, gyroid, no supports"}

def export_stls():
    os.makedirs(STL, exist_ok=True)
    for name, part in PARTS.items():
        out = os.path.join(STL, name + ".stl")
        subprocess.run([SCAD_EXE, "-o", out, "-D", f'part="{part}"', SCAD], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("wrote", os.path.relpath(out, ROOT))

index = {}
def load_index():
    for kind in ("machine", "process", "filament"):
        for p in glob.glob(os.path.join(BBL, kind, "**", "*.json"), recursive=True):
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            if "name" in d:
                index[(kind, d["name"])] = d

def flat(kind, name):
    d = dict(index[(kind, name)])
    parent = d.pop("inherits", None)
    if parent:
        base = flat(kind, parent); base.update(d); d = base
    return d

def write(kind, name, extra, path, printer):
    d = flat(kind, name); d.update(extra)
    d.pop("inherits", None); d.pop("instantiation", None)
    d["from"] = "User" if extra else "system"
    if kind != "machine" and "compatible_printers" in d and printer not in d["compatible_printers"]:
        d["compatible_printers"] = list(d["compatible_printers"]) + [printer]
    json.dump(d, open(path, "w", encoding="utf-8"), indent=1)

def set_meta(path):
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "3D/3dmodel.model":
                t = data.decode("utf-8")
                for k, v in META.items():
                    t = t.replace(f'<metadata name="{k}"></metadata>', f'<metadata name="{k}">{v}</metadata>')
                data = t.encode("utf-8")
            zout.writestr(item, data)
    os.replace(tmp, path)

if __name__ == "__main__":
    export_stls()
    load_index()
    work = tempfile.mkdtemp(prefix="pb3mf_")
    for key, (machine, process, filament) in PRINTERS.items():
        prof = os.path.join(work, key); os.makedirs(prof, exist_ok=True)
        write("machine", machine, {}, os.path.join(prof, "machine.json"), machine)
        write("filament", filament, dict(FILAMENT, name=f"PLA Matte 15 flow ({key})"), os.path.join(prof, "filament.json"), machine)
        for pname, ov in PROCESSES.items():
            write("process", process, dict(COMMON, **ov, name=f"Pinball {pname} 0.20mm"),
                  os.path.join(prof, f"process_{pname}.json"), machine)
        out_dir = os.path.join(ROOT, "print", "bambu-" + key); os.makedirs(out_dir, exist_ok=True)
        for name, (pname, parts) in SETS.items():
            out = os.path.join(out_dir, name + ".3mf")
            if os.path.exists(out):
                os.remove(out)
            cmd = [EXE, "--orient", "0", "--arrange", "1",
                   "--load-settings", os.path.join(prof, "machine.json") + ";" + os.path.join(prof, f"process_{pname}.json"),
                   "--load-filaments", os.path.join(prof, "filament.json"),
                   "--export-3mf", out] + [os.path.join(STL, p + ".stl") for p in parts]
            subprocess.run(cmd, cwd=work)
            for _ in range(600):                    # the GUI build returns before it finishes
                if os.path.exists(out):
                    break
                time.sleep(0.5)
            time.sleep(1)
            set_meta(out)
            print("wrote", os.path.relpath(out, ROOT))
    shutil.rmtree(work, ignore_errors=True)
