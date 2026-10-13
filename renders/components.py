# ============================================================
#  Blender models of every pinball-controller component, to real
#  dimensions, placed where model/pinball_controller_v2.scad puts them.
#  Case frame, mm: x = left -> right as the player sees it, y = front
#  (0) -> back (230), z = up, cover underside at z = 0. Positions come
#  from the .scad itself (renders/build/layout.json, written by
#  renders/export_stls.py), so the renders follow the model.
#
#  Each part is a group (an Empty with children) so it can be moved for
#  the exploded view or rendered on its own. Used by renders/render.py.
# ============================================================
import bpy, math, os, json
from mathutils import Vector

MM = 0.001
# ---------- materials ----------
_mats = {}
def mat(name, color, rough=0.5, metal=0.0, **kw):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        if k in b.inputs:
            b.inputs[k].default_value = v
    _mats[name] = m
    return m

def M():
    return dict(
        pla=mat("Printed PLA", (0.008, 0.008, 0.009), 0.72, **{"Specular IOR Level": 0.25}),
        pcb_g=mat("PCB green", (0.02, 0.22, 0.07), 0.35),
        pcb_k=mat("PCB black", (0.012, 0.012, 0.014), 0.35),
        pcb_b=mat("PCB blue", (0.02, 0.09, 0.35), 0.35),
        pcb_r=mat("PCB red", (0.45, 0.02, 0.02), 0.35),
        chip=mat("IC black", (0.015, 0.015, 0.016), 0.45),
        silver=mat("Tin", (0.80, 0.80, 0.82), 0.25, 1.0),
        gold=mat("Gold", (0.95, 0.70, 0.30), 0.25, 1.0),
        brass=mat("Brass", (0.85, 0.62, 0.28), 0.3, 1.0),
        steel=mat("Steel", (0.55, 0.56, 0.58), 0.35, 1.0),
        plastic_k=mat("Plastic black", (0.02, 0.02, 0.022), 0.45),
        plastic_w=mat("Plastic white", (0.85, 0.85, 0.82), 0.4),
        term_b=mat("Terminal blue", (0.05, 0.25, 0.75), 0.4),
        term_g=mat("Terminal green", (0.05, 0.45, 0.12), 0.4),
        trim=mat("Trimpot blue", (0.05, 0.25, 0.85), 0.3),
        foil=mat("LiPo foil", (0.78, 0.79, 0.80), 0.18, 0.9),
        kapton=mat("Kapton", (0.90, 0.55, 0.05), 0.3, 0.0, **{"Transmission Weight": 0.3}),
        wire_r=mat("Wire red", (0.70, 0.03, 0.03), 0.5),
        wire_k=mat("Wire black", (0.02, 0.02, 0.02), 0.5),
        wire_y=mat("Wire yellow", (0.85, 0.65, 0.02), 0.5),
        wire_bl=mat("Wire blue", (0.03, 0.18, 0.75), 0.5),
        wire_gr=mat("Wire green", (0.03, 0.5, 0.15), 0.5),
        wire_pu=mat("Wire purple", (0.4, 0.08, 0.6), 0.5),
        wire_br=mat("Wire brown", (0.35, 0.18, 0.06), 0.5),
        wire_w=mat("Wire white", (0.85, 0.85, 0.85), 0.5),
        housing=mat("Trackball housing", (0.014, 0.014, 0.016), 0.55),
        rubber=mat("Rubber", (0.03, 0.03, 0.03), 0.85),
        ring=mat("Black ring", (0.01, 0.01, 0.01), 0.35),
        ball=mat("Trackball", (0.92, 0.92, 0.95), 0.12, 0.0, **{"Subsurface Weight": 0.35,
                 "Subsurface Radius": (0.02, 0.02, 0.03), "Coat Weight": 0.6,
                 "Emission Color": (0.55, 0.22, 1.0, 1), "Emission Strength": 0.8}),
        clear=mat("Clear acrylic", (0.95, 0.95, 0.97), 0.05, 0.0, **{"Transmission Weight": 0.95, "IOR": 1.49}),
        cap=mat("Button cap", (0.95, 0.95, 0.95), 0.25, 0.0, **{"Emission Color": (1, 1, 1, 1), "Emission Strength": 0.25}),
        glass=mat("E-paper glass", (0.82, 0.82, 0.78), 0.55),
        silk=mat("Silkscreen", (0.95, 0.95, 0.95), 0.5),
        led=mat("LED", (0.9, 0.1, 0.1), 0.2, 0.0, **{"Emission Color": (1, 0.1, 0.1, 1), "Emission Strength": 2.0}),
        slot=mat("USB slot", (0.03, 0.03, 0.04), 0.5),
        fpc=mat("FPC", (0.85, 0.55, 0.12), 0.35),
    )

# ---------- primitives (sizes and positions in mm) ----------
def _finish(ob, m, parent, name, bevel):
    if name:
        ob.name = name
    if m:
        ob.data.materials.append(m)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = bevel * MM; bv.segments = 2; bv.limit_method = "ANGLE"
    if parent:
        ob.parent = parent
    return ob

def box(size, loc, m, bevel=0.0, rot=(0, 0, 0), parent=None, name=""):
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(v * MM for v in loc),
                                    rotation=tuple(math.radians(r) for r in rot))
    ob = bpy.context.object
    ob.scale = tuple(v * MM for v in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(ob, m, parent, name, bevel)

def cyl(d, h, loc, m, rot=(0, 0, 0), verts=48, parent=None, name="", bevel=0.0, d2=None):
    if d2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=d / 2 * MM, depth=h * MM,
                                            location=tuple(v * MM for v in loc),
                                            rotation=tuple(math.radians(r) for r in rot))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=d / 2 * MM, radius2=d2 / 2 * MM,
                                        depth=h * MM, location=tuple(v * MM for v in loc),
                                        rotation=tuple(math.radians(r) for r in rot))
    ob = bpy.context.object
    bpy.ops.object.shade_smooth()
    return _finish(ob, m, parent, name, bevel)

def text(s, size, loc, m, rot=(0, 0, 0), parent=None, align="CENTER"):
    bpy.ops.object.text_add(location=tuple(v * MM for v in loc),
                            rotation=tuple(math.radians(r) for r in rot))
    ob = bpy.context.object
    ob.data.body = s; ob.data.size = size * MM; ob.data.align_x = align; ob.data.align_y = "CENTER"
    ob.data.extrude = 0.02 * MM
    ob.data.materials.append(m)
    if parent:
        ob.parent = parent
    return ob

def wire(points, m, d=1.6, parent=None):
    cu = bpy.data.curves.new("wire", "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = d / 2 * MM; cu.bevel_resolution = 3
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = Vector(p) * MM
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new("wire", cu); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(m)
    if parent:
        ob.parent = parent
    return ob

def group(name):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    return e


def M_pinball():
    m = M()
    m.update(
        pla=mat("Printed PLA matte", (0.012, 0.012, 0.014), 0.78, **{"Specular IOR Level": 0.22}),
        cover=mat("Printed PLA cover", (0.02, 0.02, 0.022), 0.8, **{"Specular IOR Level": 0.2}),
        cap_w=mat("Cap white", (0.92, 0.92, 0.9), 0.22, 0.0, **{"Coat Weight": 0.5}),
        cap_r=mat("Cap red", (0.75, 0.02, 0.02), 0.22, 0.0, **{"Coat Weight": 0.5}),
        cap_y=mat("Cap yellow", (0.95, 0.65, 0.02), 0.22, 0.0, **{"Coat Weight": 0.5}),
        ball=mat("Joystick ball", (0.75, 0.01, 0.015), 0.12, 0.0, **{"Coat Weight": 1.0}),
        relay=mat("Relay blue", (0.04, 0.16, 0.6), 0.3),
        seg=mat("7-seg red", (1.0, 0.05, 0.02), 0.3, 0.0, **{"Emission Color": (1, 0.08, 0.03, 1), "Emission Strength": 3.0}),
        heatsink=mat("Heatsink", (0.02, 0.02, 0.025), 0.4, 0.8),
        cap_el=mat("Electrolytic", (0.65, 0.66, 0.7), 0.3, 0.6),
        coil=mat("Coil tape", (0.08, 0.12, 0.55), 0.45),
        label=mat("Label", (0.95, 0.95, 0.92), 0.5),
        purple=mat("PCB purple", (0.25, 0.05, 0.4), 0.35),
        aluminium=mat("Aluminium", (0.8, 0.8, 0.82), 0.3, 1.0),
        lcd=mat("LCD black", (0.005, 0.005, 0.008), 0.08),
    )
    return m

L = {}                                    # layout.json from the .scad (filled by build_all)

def screen_mat(name, png, strength):
    sm = bpy.data.materials.new(name); sm.use_nodes = True
    nt = sm.node_tree; b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(png)
    b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 0.7
    b.inputs["Specular IOR Level"].default_value = 0.0
    return sm

# ---------- buttons / joystick ----------
def arcade_button(mt, g, x, y, cap, d=28.0, z=None, side=0):
    """28 mm arcade button: bezel + plunger outside, body + microswitch inside.
    side = 0: in the top panel; -1 / +1: in the left / right side wall (pointing out)."""
    t = L["top_t"]
    if side == 0:
        z = L["H"]
        cyl(d + 5, 2.6, (x, y, z + 1.3), cap, parent=g, bevel=0.8)
        cyl(d - 6, 4.0, (x, y, z + 4.2), cap, parent=g, bevel=1.2)
        cyl(d - 1, 22, (x, y, z - t - 11), mt["plastic_k"], parent=g)
        box((14, 14, 12), (x, y, z - t - 28), mt["plastic_k"], 0.6, parent=g)
    else:
        xo = 0 if side < 0 else L["W"]
        cyl(d + 5, 2.6, (xo + side * 1.3, y, z), cap, rot=(0, 90, 0), parent=g, bevel=0.8)
        cyl(d - 6, 4.0, (xo + side * 4.2, y, z), cap, rot=(0, 90, 0), parent=g, bevel=1.2)
        cyl(d - 1, 22, (xo - side * 16, y, z), mt["plastic_k"], rot=(0, 90, 0), parent=g)
        box((12, 14, 14), (xo - side * 33, y, z), mt["plastic_k"], 0.6, parent=g)
    return g

def buttons(mt, g):
    for x, y in L["six"]:
        arcade_button(mt, g, x, y, mt["cap_w"])
    for x, y in L["start"]:
        arcade_button(mt, g, x, y, mt["cap_r"])
    for s in (-1, 1):
        arcade_button(mt, g, 0, L["flip_y"], mt["cap_y"], z=L["flip_z"], side=s)
    return g

def joystick(mt, g):
    x, y = L["joy"]; H = L["H"]; t = L["top_t"]
    pw, pd = L["joy_plate"]
    box((pw, pd, 1.6), (x, y, H - t - 0.8), mt["steel"], 0.3, parent=g, name="joystick plate")
    box((44, 44, 33), (x, y, H - t - 1.6 - 16.5), mt["plastic_k"], 1.0, parent=g, name="joystick body")
    cyl(40, 1.2, (x, y, H + 0.6), mt["plastic_k"], parent=g, name="dust washer")
    for sx in (-20, 20):                                  # 4 countersunk M4 screws, 40 x 81 pattern
        for sy in (-40.5, 40.5):
            cyl(7.5, 0.6, (x + sx, y + sy, H + 0.05), mt["steel"], parent=g)
    cyl(9.5, 32, (x, y, H + 14), mt["steel"], parent=g, name="shaft")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=17 * MM, segments=64, ring_count=32,
                                         location=(x * MM, y * MM, (H + 42) * MM))
    b = bpy.context.object; bpy.ops.object.shade_smooth(); _finish(b, mt["ball"], g, "ball top", 0)
    return g

# ---------- boards on the cover (rows: centre x, centre y, underside z, w, d, h) ----------
def relay_xyj02(mt, g, row, mirror=1):
    x, y, z, w, d, _ = row; t = 1.6
    box((w, d, t), (x, y, z + t / 2), mt["relay"], 0.3, parent=g, name="XY-J02 PCB")
    zt = z + t
    box((19, 15.5, 15.5), (x + mirror * (w / 2 - 17), y + 6, zt + 7.75), mt["relay"], 0.6, parent=g, name="relay")
    box((19, 10, 7.5), (x - mirror * 4, y + 6, zt + 3.75), mt["plastic_k"], 0.3, parent=g, name="display")
    for i in range(3):
        box((3.4, 6.5, 0.1), (x - mirror * 4 - 5.8 + i * 5.8, y + 6, zt + 7.55), mt["seg"], parent=g)
    for i in range(4):
        box((6, 6, 3.5), (x - 15 + i * 10, y - d / 2 + 6, zt + 1.75), mt["plastic_k"], 0.3, parent=g)
        cyl(3.5, 1.2, (x - 15 + i * 10, y - d / 2 + 6, zt + 4.0), mt["plastic_k"], parent=g)
    for i in range(4):                                  # + / - / TRIG / GND
        box((7.5, 5, 10), (x - mirror * (w / 2 - 4.5), y - 7.5 + i * 5, zt + 5), mt["term_b"], 0.3, parent=g)
    for i in range(3):                                  # NO / COM / NC
        box((7.5, 5, 10), (x + mirror * (w / 2 - 4.5), y - 5 + i * 5, zt + 5), mt["term_b"], 0.3, parent=g)
    return g

def amp_xhm543(mt, g, row):
    x, y, z, w, d, _ = row; t = 1.6                    # 68 x 92, long axis along y
    box((w, d, t), (x, y, z + t / 2), mt["pcb_b"], 0.3, parent=g, name="XH-M543 PCB")
    zt = z + t
    box((24, 40, 2), (x, y + 4, zt + 1), mt["heatsink"], parent=g, name="heatsink")
    for i in range(9):
        box((1.2, 40, 16), (x - 11 + i * 2.75, y + 4, zt + 10), mt["heatsink"], parent=g)
    for dx, dy in [(-20, 36), (0, 36), (20, 36), (-20, -32), (0, -32), (20, -32)]:
        cyl(10, 17, (x + dx, y + dy, zt + 8.5), mt["cap_el"], parent=g, bevel=0.5)
    for dy in (-12, 14):
        cyl(12, 8, (x - 26, y + dy, zt + 4), mt["plastic_k"], parent=g)
    box((10, 15, 11), (x + 27, y - 40, zt + 5.5), mt["term_g"], 0.3, parent=g)
    for dy in (-20, 26):
        box((10, 15, 11), (x - 28, y + dy, zt + 5.5), mt["term_g"], 0.3, parent=g)
    cyl(7, 6, (x + 27, y + 30, zt + 3), mt["trim"], parent=g)
    return g

def usb_hub(mt, g, row):
    x, y, z, w, d, _ = row; t = 1.6                    # 44 x 84, ports face +x
    box((w, d, t), (x, y, z + t / 2), mt["pcb_g"], 0.3, parent=g, name="hub PCB")
    zt = z + t
    for i in range(7):
        yy = y - 33 + i * 11
        box((14, 13.2, 6.5), (x + w / 2 - 6, yy, zt + 3.25), mt["silver"], 0.3, parent=g)
        box((1.5, 11, 4.5), (x + w / 2 + 0.6, yy, zt + 3.25), mt["slot"], parent=g)
        cyl(5, 8, (x + w / 2 - 18, yy, zt + 4), mt["cap_el"], parent=g)
    box((9, 9, 1.4), (x - 6, y, zt + 0.7), mt["chip"], 0.1, parent=g, name="hub IC")
    box((10, 14, 11), (x - w / 2 + 5, y - 30, zt + 5.5), mt["plastic_k"], 0.4, parent=g, name="5 V jack")
    box((6, 8, 3), (x - w / 2 + 3, y + 30, zt + 1.5), mt["silver"], 0.3, parent=g, name="micro-USB in")
    return g

def dac_stick(mt, g, row):
    """PCM2704 USB DAC stick in the hub's front port"""
    x, y, z, w, d, _ = row
    yy = y - 33; zt = z + 1.6
    box((12, 12, 4.5), (x + w / 2 + 6, yy, zt + 3.25), mt["silver"], 0.2, parent=g)
    box((26, 17, 9), (x + w / 2 + 25, yy, zt + 3.25), mt["plastic_k"], 1.5, parent=g, name="PCM2704 DAC")
    cyl(6, 5, (x + w / 2 + 40, yy, zt + 3.25), mt["silver"], rot=(0, 90, 0), parent=g)
    return g

def pico_h(mt, g, row):
    """Raspberry Pi Pico H, pins up, USB toward the front"""
    x, y, z, w, d, _ = row; t = 1.0
    box((21, 51, t), (x, y, z + t / 2), mt["pcb_g"], 0.3, parent=g, name="Pico PCB")
    zt = z + t
    for side in (-1, 1):
        xr = x + side * 8.89
        box((2.5, 50.8, 2.5), (xr, y, zt + 1.25), mt["plastic_k"], 0.2, parent=g)
        for i in range(20):
            box((0.64, 0.64, 6.0), (xr, y - 24.13 + i * 2.54, zt + 5.5), mt["gold"], parent=g)
    box((7, 7, 0.9), (x, y + 2, z - 0.45), mt["chip"], 0.1, parent=g, name="RP2040")
    box((8, 5.6, 2.6), (x, y - 24.3, z - 1.3), mt["silver"], 0.2, parent=g, name="micro-USB")
    return g

def lis3dh(mt, g, row):
    x, y, z, w, d, _ = row
    box((17.8, 25.4, 1.6), (x, y, z + 0.8), mt["purple"], 0.3, parent=g, name="LIS3DH")
    box((3, 3, 1), (x, y + 2, z + 2.1), mt["chip"], parent=g)
    box((2.5, 20, 2.5), (x - 7, y, z + 2.85), mt["plastic_k"], parent=g)
    return g

def solenoid(mt, g, s):
    """JF-1039 pull solenoid: U frame, taped coil, plunger + spring toward its side wall"""
    x, y, z, side = s; bl, bw, bh = L["sol_body"]
    cx, cy, cz = x + bl / 2, y + bw / 2, z + bh / 2
    box((bl, bw, 1.5), (cx, cy, z + 0.75), mt["steel"], 0.2, parent=g)
    for e in (-1, 1):
        box((1.5, bw, bh), (cx + e * (bl / 2 - 0.75), cy, cz), mt["steel"], 0.2, parent=g)
    cyl(min(bw, bh) - 2, bl - 4, (cx, cy, cz + 1), mt["coil"], rot=(0, 90, 0), parent=g, name="JF-1039 coil")
    out = -1 if side == 0 else 1
    xe = x if side == 0 else x + bl
    r = L["sol_rod"]
    cyl(5, r, (xe + out * r / 2, cy, cz + 1), mt["steel"], rot=(0, 90, 0), parent=g)
    cyl(9, 7, (xe + out * 5, cy, cz + 1), mt["steel"], rot=(0, 90, 0), parent=g, name="spring")
    box((4, 9, 3), (xe + out * (r - 2), cy, cz + 1), mt["silver"], parent=g, name="fork")
    return g

# ---------- top-panel parts ----------
def encoder(mt, g):
    x, y = L["enc"]; z = L["enc_z"]
    box((36, 92, 1.6), (x, y, z + 0.8), mt["pcb_g"], 0.3, parent=g, name="Zero-Delay encoder")
    for i in range(6):
        box((5, 12, 6), (x - 13, y - 38 + i * 15, z - 3), mt["plastic_w"], 0.2, parent=g)
    box((12, 16, 11), (x + 10, y - 38, z - 5.5), mt["silver"], 0.3, parent=g, name="USB-B")
    return g

def exciter(mt, g):
    x, y = L["exc"]; H = L["H"]; t = L["top_t"]; eh = L["exc_h"]
    cyl(L["exc_pad"], 3, (x, y, H - t - 1.5), mt["aluminium"], parent=g)
    cyl(L["exc_d"], eh - 8, (x, y, H - t - eh + (eh - 8) / 2), mt["plastic_k"], parent=g, bevel=1.5, name="exciter")
    return g

def tdisplay(mt, g, png):
    x, y = L["td"]; bw, bd = L["td_board"]; z = L["td_z"]
    box((bw, bd, 5.4), (x, y, z - 2.7), mt["lcd"], 0.3, parent=g, name="T-Display")
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x * MM, y * MM, (z + 0.05) * MM))
    s = bpy.context.object; s.name = "T-Display screen"
    s.scale = (bw * 0.84 * MM, bd * 0.72 * MM, 1)
    s.data.materials.append(screen_mat("T-Display screen", png, 0.9)); s.parent = g
    return g

def gx16(mt, g, single=False):
    for x in (L["gx"][:1] if single else L["gx"]):
        yo = L["D"]
        cyl(19, 3, (x, yo + 1.5, L["gx_z"]), mt["steel"], rot=(90, 0, 0), parent=g, verts=6)
        cyl(15.5, 12, (x, yo + 6, L["gx_z"]), mt["steel"], rot=(90, 0, 0), parent=g)
        cyl(11, 0.6, (x, yo + 12.1, L["gx_z"]), mt["plastic_k"], rot=(90, 0, 0), parent=g)
        for k in range(8):
            a = 2 * math.pi * k / 7 if k < 7 else 0
            r = 3.4 if k < 7 else 0
            cyl(1.2, 0.8, (x + r * math.cos(a), yo + 12.4, L["gx_z"] + r * math.sin(a)), mt["gold"], rot=(90, 0, 0),
                parent=g, verts=12)
    return g

# ---------- marquee head ----------
def marquee_head(mt, g, png):
    """LED panels + lit face, in head-local coords under an empty placed like the .scad's mq_place()"""
    ox, oy, oz = L["mq_origin"]
    h = bpy.data.objects.new("marquee head", None); bpy.context.scene.collection.objects.link(h)
    h.location = (ox * MM, oy * MM, oz * MM); h.rotation_euler = (math.radians(-L["mq_tilt"]), 0, 0); h.parent = g
    pw, ph, pt = L["mq_panel"]; pz = L["mq_pz"]
    box((pw, pt - 0.4, ph), (0, 0.4 + (pt - 0.4) / 2, pz + ph / 2), mt["pcb_k"], parent=h, name="LED panels")
    bpy.ops.mesh.primitive_plane_add(size=1)
    s = bpy.context.object; s.name = "Marquee screen"
    s.rotation_euler = (math.radians(90), 0, 0); s.scale = (pw * MM, ph * MM, 1)
    s.location = (0, 0.3 * MM, (pz + ph / 2) * MM)
    s.data.materials.append(screen_mat("Marquee LEDs", png, 2.2)); s.parent = h
    return g

# ---------- build ----------
def build_all(build_dir, marquee_png="marquee_sunset.png"):
    L.update(json.load(open(os.path.join(build_dir, "layout.json"))))
    mt = M_pinball()
    groups = {}
    def imp(name, label, parent, m):
        path = os.path.join(build_dir, name + ".stl")
        if hasattr(bpy.ops.wm, "stl_import"):
            bpy.ops.wm.stl_import(filepath=path)
        else:
            bpy.ops.import_mesh.stl(filepath=path)
        ob = bpy.context.selected_objects[0]
        ob.name = label; ob.scale = (MM, MM, MM)
        ob.data.materials.append(m); ob.parent = parent
        return ob
    groups["case"] = g = group("case");      imp("r_case", "Case", g, mt["pla"])
    groups["gx"] = gx16(mt, group("gx"))
    groups["cover"] = g = group("cover");    imp("r_cover", "Cover", g, mt["cover"])
    groups["marquee"] = g = group("marquee"); imp("r_marquee", "Marquee trays + plate", g, mt["pla"])
    marquee_head(mt, g, os.path.join(build_dir, marquee_png))
    groups["buttons"] = buttons(mt, group("buttons"))
    groups["joystick"] = joystick(mt, group("joystick"))
    groups["encoder"] = encoder(mt, group("encoder"))
    groups["exciter"] = exciter(mt, group("exciter"))
    groups["tdisplay"] = tdisplay(mt, group("tdisplay"), os.path.join(build_dir, "tdisplay.png"))
    p = L["pcbs"]
    groups["amp"] = amp_xhm543(mt, group("amp"), p[0])
    groups["relays"] = g = group("relays"); relay_xyj02(mt, g, p[1], 1); relay_xyj02(mt, g, p[2], -1)
    groups["pico"] = pico_h(mt, group("pico"), p[3])
    groups["lis3dh"] = lis3dh(mt, group("lis3dh"), p[4])
    groups["hub"] = usb_hub(mt, group("hub"), p[5])
    groups["dac"] = dac_stick(mt, group("dac"), p[5])
    groups["solenoids"] = g = group("solenoids")
    for s in L["sols"]:
        solenoid(mt, g, s)
    # single parts for the parts-list pictures (hidden in the assembled shots)
    groups["t_button"] = g = group("t_button"); arcade_button(mt, g, L["six"][0][0], L["six"][0][1], mt["cap_w"])
    groups["t_relay"] = g = group("t_relay"); relay_xyj02(mt, g, p[1], 1)
    groups["t_solenoid"] = g = group("t_solenoid"); solenoid(mt, g, L["sols"][1])
    groups["t_gx16"] = g = group("t_gx16"); gx16(mt, g, single=True)
    root = group("root"); root.location = (-L["W"] / 2 * MM, -L["D"] / 2 * MM, 0)
    for gg in groups.values():
        gg.parent = root
    return groups, mt
