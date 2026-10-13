# ============================================================
#  Product renders for the README / MakerWorld (Blender 4.2+ / 5.x),
#  using the dimension-accurate component models in components.py.
#
#  Inputs (from the repo root):
#    python renders/export_stls.py     printed parts + layout.json from the .scad
#    python renders/make_screens.py    marquee + status-display screen images
#  Render:
#    blender -b -P renders/render.py -- <repo root> <samples> <shots>
#  shots: comma list of hero,top,rear,exploded,cutaway,layout,thumbs (default all)
#  Then:  python renders/annotate.py <repo root>   (page colour + numbered callouts)
# ============================================================
import bpy, math, os, sys, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = argv[0] if argv else os.getcwd()
SAMPLES = int(argv[1]) if len(argv) > 1 else 160
SHOTS = (argv[2] if len(argv) > 2 else "hero,top,rear,exploded,cutaway,layout,thumbs").split(",")
sys.path.insert(0, os.path.join(ROOT, "renders"))
import components as C

BUILD = os.path.join(ROOT, "renders", "build")
OUT = os.path.join(ROOT, "images")
MM = C.MM

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
vt = [i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items]
scene.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"
for attr in dir(scene.render):                 # no date / path stamps in the PNGs
    if attr.startswith("use_stamp"):
        try:
            setattr(scene.render, attr, False)
        except Exception:
            pass
try:
    cp = bpy.context.preferences.addons["cycles"].preferences
    for t in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            cp.compute_device_type = t; cp.get_devices()
            if any(d.type == t for d in cp.devices):
                break
        except Exception:
            pass
    for d in cp.devices:
        d.use = True
    scene.cycles.device = "GPU"
except Exception as e:
    print("GPU setup failed, using CPU:", e)

# ---------- scene ----------
groups, mt = C.build_all(BUILD)
L = C.L
OX, OY = L["W"] / 2, L["D"] / 2                 # case coords -> world (mm)

floor_m = C.mat("Floor", (0.78, 0.78, 0.8), 0.45)
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -0.5 * MM))
floor = bpy.context.object; floor.data.materials.append(floor_m)
floor.is_shadow_catcher = True                  # transparent film + shadows only:
scene.render.film_transparent = True            # composited onto the page colour by annotate.py

def area(name, loc, rot, size, energy, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    l = bpy.context.object; l.name = name
    l.data.size = size; l.data.energy = energy; l.data.color = color
    return l

area("key", (-0.75, -0.75, 1.0), (math.radians(45), 0, math.radians(-40)), 1.2, 80)
area("fill", (0.95, -0.5, 0.5), (math.radians(65), 0, math.radians(60)), 1.5, 26, (0.92, 0.95, 1.0))
area("rim", (0.2, 1.0, 0.75), (math.radians(-55), 0, math.radians(170)), 0.8, 60)
world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.82, 0.83, 0.86, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.15

target = bpy.data.objects.new("target", None); scene.collection.objects.link(target)

def descendants(ob):
    out = []
    for c in ob.children:
        out.append(c); out += descendants(c)
    return out

def show(keys):
    for k, g in groups.items():
        for c in descendants(g):
            c.hide_render = k not in keys

def reset_layout():
    for g in groups.values():
        g.location = (0, 0, 0); g.rotation_euler = (0, 0, 0)
    case = bpy.data.objects["Case"]
    for m in list(case.modifiers):
        case.modifiers.remove(m)
    floor.location.z = -0.5 * MM

def camera(name, loc, tgt, lens=50, res=(1920, 1280)):
    target.location = tgt
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.001
    cam = bpy.data.objects.new(name, cd); scene.collection.objects.link(cam)
    cam.location = loc
    tc = cam.constraints.new("TRACK_TO"); tc.target = target
    tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    return cam

def render(name):
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)

def callouts(cam, anchors, fname):
    """anchors: n -> (group, (x, y, z) case mm) -> pixel positions for annotate.py"""
    bpy.context.view_layer.update()
    W, Hh = scene.render.resolution_x, scene.render.resolution_y
    pts = {}
    for n, (k, p) in anchors.items():
        w = Vector(((p[0] - OX) * MM, (p[1] - OY) * MM, p[2] * MM)) + groups[k].location
        v = world_to_camera_view(scene, cam, w)
        pts[n] = (round(v.x * W), round((1 - v.y) * Hh))
    os.makedirs(BUILD, exist_ok=True)
    json.dump(pts, open(os.path.join(BUILD, fname), "w"))

ALL = {k for k in groups if not k.startswith("t_")}
H = L["H"]; pcb = L["pcbs"]
mq = L["mq_origin"]

# ---------- assembled shots ----------
if "hero" in SHOTS:
    reset_layout(); show(ALL)
    camera("hero", (0.40, -0.66, 0.50), (0.0, 0.03, 0.085), lens=44); render("hero")
if "top" in SHOTS:
    reset_layout(); show(ALL)
    camera("top", (0.0, -0.12, 0.95), (0.0, 0.03, 0.0), lens=50, res=(1600, 1600)); render("render_top")
if "rear" in SHOTS:
    reset_layout(); show(ALL)
    camera("rear", (-0.42, 0.68, 0.30), (0.0, 0.08, 0.07), lens=46); render("render_rear")

# ---------- cutaway: right half of the case removed ----------
if "cutaway" in SHOTS:
    reset_layout(); show(ALL - {"marquee", "gx"})
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.07, 0.0, 0.06))
    cutter = bpy.context.object; cutter.scale = (0.14, 0.40, 0.14); cutter.hide_render = True
    cutter.display_type = "WIRE"
    case = bpy.data.objects["Case"]
    bm = case.modifiers.new("cutaway", "BOOLEAN"); bm.object = cutter; bm.operation = "DIFFERENCE"
    for k in ("buttons", "joystick", "encoder", "tdisplay", "exciter"):     # keep only the left-half top parts
        for c in descendants(groups[k]):
            if c.type == "MESH":
                bpy.context.view_layer.update()
                if (c.matrix_world @ Vector(c.bound_box[0])).x > 0.0:
                    c.hide_render = True
    camera("cutaway", (0.62, -0.42, 0.42), (0.0, 0.0, 0.035), lens=42); render("cutaway")
    case.modifiers.remove(bm)

# ---------- exploded view ----------
if "exploded" in SHOTS:
    reset_layout(); show(ALL)
    up = 250
    offs = {"case": (0, 0, up), "gx": (0, 0, up), "buttons": (0, 0, up + 75), "joystick": (0, 0, up + 75),
            "encoder": (0, -70, 120), "exciter": (0, 0, 75), "tdisplay": (0, 0, 95),
            "marquee": (0, 160, up + 40)}
    for k, o in offs.items():
        groups[k].location = tuple(v * MM for v in o)
    floor.location.z = -1 * MM
    cam = camera("exploded", (-0.78, -1.20, 0.98), (0.0, 0.05, 0.20), lens=48, res=(1500, 2100))
    six = L["six"]
    anchors = {
        1: ("case", (20, 10, H - 20)), 2: ("cover", (12, 12, 4)), 3: ("marquee", (mq[0] - 120, mq[1] + 15, mq[2] - 20)),
        4: ("buttons", (six[0][0], six[0][1], H + 8)), 5: ("buttons", (-4, L["flip_y"], L["flip_z"])),
        6: ("joystick", (L["joy"][0], L["joy"][1], H + 58)), 7: ("encoder", (L["enc"][0], L["enc"][1] - 30, L["enc_z"])),
        8: ("exciter", (L["exc"][0] - 25, L["exc"][1], H - 25)), 9: ("tdisplay", (L["td"][0] + 20, L["td"][1], L["td_z"])),
        10: ("amp", (pcb[0][0], pcb[0][1] + 40, 30)), 11: ("relays", (pcb[1][0], pcb[1][1], 22)),
        12: ("solenoids", (L["sols"][0][0] + 20, L["sols"][0][1] + 10, 32)), 13: ("hub", (pcb[5][0] - 10, pcb[5][1] + 20, 14)),
        14: ("dac", (pcb[5][0] + 47, pcb[5][1] - 33, 18)), 15: ("pico", (pcb[3][0], pcb[3][1], 18)),
        16: ("lis3dh", (pcb[4][0], pcb[4][1], 12)), 17: ("marquee", (mq[0] + 60, mq[1] - 20, mq[2] + 60)),
    }
    callouts(cam, anchors, "callouts.json")
    render("exploded_raw")

# ---------- layout: the cover with every board, from above ----------
if "layout" in SHOTS:
    reset_layout(); show({"cover", "amp", "relays", "pico", "lis3dh", "hub", "dac", "solenoids"})
    cam = camera("layout", (0.0, -0.005, 0.70), (0.0, -0.005, 0.0), lens=50, res=(1600, 1500))
    anchors = {2: ("cover", (20, 200, 4)), 10: ("amp", (pcb[0][0], pcb[0][1], 40)), 11: ("relays", (pcb[1][0], pcb[1][1], 26)),
               12: ("solenoids", (L["sols"][1][0] + 20, L["sols"][1][1] + 10, 34)), 13: ("hub", (pcb[5][0], pcb[5][1], 18)),
               14: ("dac", (pcb[5][0] + 47, pcb[5][1] - 33, 20)), 15: ("pico", (pcb[3][0], pcb[3][1], 20)),
               16: ("lis3dh", (pcb[4][0], pcb[4][1], 12))}
    callouts(cam, anchors, "layout_callouts.json")
    render("layout_raw")

# ---------- one render per component ----------
if "thumbs" in SHOTS:
    reset_layout()
    items = [("t_button", "part_buttons"), ("joystick", "part_joystick"), ("encoder", "part_encoder"),
             ("exciter", "part_exciter"), ("tdisplay", "part_tdisplay"), ("amp", "part_amp"), ("t_relay", "part_relays"),
             ("t_solenoid", "part_solenoids"), ("hub", "part_hub"), ("dac", "part_dac"), ("pico", "part_pico"),
             ("lis3dh", "part_lis3dh"), ("t_gx16", "part_gx16"), ("case", "part_case"), ("cover", "part_cover"),
             ("marquee", "part_marquee")]
    for key, fname in items:
        show({key})
        g = groups[key]
        g.rotation_euler = (math.radians(180), 0, 0) if key == "encoder" else (0, 0, 0)
        obs = [o for o in descendants(g) if o.type in ("MESH", "CURVE", "FONT") and not o.hide_render]
        bpy.context.view_layer.update()
        corners = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
        lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        ctr = (lo + hi) / 2; rad = (hi - lo).length / 2
        floor.location.z = lo.z - 0.05 * MM
        d = Vector((0.85, -1.1, 0.95)).normalized()
        lens = 70; fov = 2 * math.atan(36 / 2 / lens)
        dist = rad / math.sin(fov / 2) * 1.05
        camera("thumb_" + key, tuple(ctr + d * dist), tuple(ctr), lens=lens, res=(900, 900))
        render(fname)
    floor.location.z = -0.5 * MM
