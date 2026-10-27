"""Laundromat washer-extractor, following the user's laundromat-bank photo and
Dexter T-450 class dimensions (see docs/references/washer.md):
759 W x 1226 H x 724 D mm, satin brushed stainless, polished door bezel with a
black handle bar, tilted black control panel with green LED readout.
Machines stand side by side with no gaps, so the sides are plain. Front faces -Y,
origin at the floor (the plinth top in the scene). Brand is fictional.
"""
import importlib
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.expanduser("~/Documents/GitHub/ArtGameCollab2.mds/blender/hotel_laundry"))
import laundry_lib as L  # noqa: E402
importlib.reload(L)

NAME = "WasherExtractor"     # kept so the Unity references stay valid

W, D, H = 0.759, 0.724, 1.226
FRONT = -D / 2
Z_PANEL = 1.0                # control housing bottom
LEAN = 0.08                  # control face leans back this much at the top
DOOR_Z = 0.56
BEZEL_R = 0.27
OPEN_R = 0.2
DRUM_R = 0.29


def materials():
    return {
        "steel": L.material("Stainless_Satin", metallic=1.0, tex="stainless_satin", normal_strength=0.35,
                            vertex_color=True),
        "sticker": L.material("Sticker_White", base=(0.88, 0.87, 0.82), roughness=0.55, vertex_color=True),
        "sticker_yellow": L.material("Sticker_Yellow", base=(0.95, 0.75, 0.05), roughness=0.5),
        "sticker_red": L.material("Sticker_Red", base=(0.7, 0.05, 0.04), roughness=0.45),
        "sticker_blue": L.material("Sticker_Blue", base=(0.05, 0.22, 0.55), roughness=0.45),
        "ink": L.material("Ink_Black", base=(0.02, 0.02, 0.02), roughness=0.6),
        "ink_white": L.material("Ink_White", base=(0.95, 0.95, 0.95), roughness=0.5),
        "plate": L.material("Plate_Silver", base=(0.72, 0.72, 0.7), metallic=0.85, roughness=0.35),
        "tape": L.material("Tape_Residue", base=(0.72, 0.66, 0.5), roughness=0.75, alpha=0.6),
        "residue": L.material("Soap_Residue", base=(0.62, 0.72, 0.85), roughness=0.8, alpha=0.55),
        "cloth": L.material("Cloth_Load", base=(0.55, 0.6, 0.68), tex="towel", normal_strength=1.0,
                            vertex_color=True),
        "polished": L.material("Stainless_Polished", base=(0.9, 0.9, 0.91), metallic=1.0, roughness=0.09),
        "panel": L.material("Panel_BlackGloss", base=(0.012, 0.012, 0.014), roughness=0.16, coat=1.0),
        "handle": L.material("Handle_Black", base=(0.02, 0.02, 0.022), roughness=0.4, tex="plastic_matte",
                             normal_strength=0.3),
        "led": L.material("LED_Green", base=(0.1, 0.8, 0.3), emission=(0.15, 1.0, 0.35), emission_strength=3.0),
        "led_off": L.material("LED_Dark", base=(0.01, 0.04, 0.02), roughness=0.1, coat=1.0),
        "print": L.material("Print_White", base=(0.88, 0.89, 0.9), roughness=0.35),
        "button": L.material("Button_Grey", base=(0.35, 0.36, 0.37), metallic=0.6, roughness=0.3),
        "glass": L.material("Glass_DoorTint", base=(0.04, 0.045, 0.045), roughness=0.03, alpha=0.45, ior=1.52),
        "rubber": L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5),
        "drum": L.material("Drum_Perforated", metallic=1.0, tex="drum_perforated", normal_strength=1.0),
        "gap": L.material("Gap_Dark", base=(0.03, 0.03, 0.032), roughness=0.6),
    }


def add(name, bm, mat, col, parent, bev=None, uv=None, texel=0.5, smooth=35.0):
    obj = L.link(L.mesh_object(name, bm, mat, smooth), col, parent)
    if uv == "box":
        L.box_uv(obj, texel)
    if bev:
        L.bevel(obj, *bev)
        L.weighted_normals(obj)
    L.triangulate(obj)
    return obj


def build_cabinet(m, col, root):
    add("Cabinet", L.box_bm(W, D, Z_PANEL, (0, 0, Z_PANEL / 2), skip=("-y",)), m["steel"], col, root,
        bev=(0.004, 2), uv="box")
    panel = L.link(L.mesh_object("FrontPanel", L.box_bm(W - 0.002, 0.014, Z_PANEL - 0.004,
                                                        (0, FRONT - 0.007, Z_PANEL / 2)), m["steel"]), col, root)
    L.boolean_cut(panel, L.cylinder_bm(OPEN_R, 0.1, 64, (0, FRONT, DOOR_Z), axis="Y"))
    L.box_uv(panel)
    L.bevel(panel, 0.004, 2)
    L.weighted_normals(panel)
    L.triangulate(panel)
    # Kick-panel seam and screws.
    add("KickSeam", L.box_bm(W - 0.03, 0.003, 0.004, (0, FRONT - 0.015, 0.16)), m["gap"], col, root)
    for i, x in enumerate((-0.33, 0.33)):
        for j, z in enumerate((0.06, 0.93)):
            add(f"Screw_{i}{j}", L.cylinder_bm(0.005, 0.003, 16, (x, FRONT - 0.0155, z), axis="Y"), m["polished"],
                col, root)

    # Control housing: stainless box whose front leans back; black glass face on it.
    bm = L.box_bm(W, D, H - Z_PANEL, (0, 0, (H + Z_PANEL) / 2))
    for v in bm.verts:
        if v.co.z > Z_PANEL + 0.01 and v.co.y < 0:
            v.co.y += LEAN
    add("ControlHousing", bm, m["steel"], col, root, bev=(0.004, 2), uv="box")
    add("TopCap", L.box_bm(W, D - LEAN + 0.01, 0.012, (0, LEAN / 2, H + 0.006)), m["steel"], col, root,
        bev=(0.003, 2), uv="box")


def build_controls(m, col, root):
    tilt = math.atan2(LEAN, H - Z_PANEL)
    frame = L.root_empty("ControlFace", col)
    frame.parent = root
    frame.location = (0, FRONT + LEAN / 2 - 0.001, (H + Z_PANEL) / 2)
    frame.rotation_euler = (-tilt, 0, 0)
    frame.empty_display_size = 0.05
    fh = H - Z_PANEL - 0.03
    add("Face", L.box_bm(W - 0.03, 0.004, fh, (0, -0.002, 0)), m["panel"], col, frame, bev=(0.002, 2))
    # LED readout window with green digits.
    add("LEDWindow", L.box_bm(0.15, 0.002, 0.06, (-0.21, -0.005, 0.03)), m["led_off"], col, frame)
    L.text_mesh("LEDDigits", "28", 0.045, m["led"], col, frame, bold=True, location=(-0.21, -0.0065, 0.03))
    L.text_mesh("LEDLabel", "MINUTES REMAINING", 0.0075, m["print"], col, frame, location=(-0.21, -0.0045, -0.012))
    labels = ["HOT", "WARM", "COLD", "START"]
    for i, lab in enumerate(labels):
        x = -0.06 + i * 0.05
        add(f"Button_{lab}", L.rounded_plate_bm(0.034, 0.022, 0.006, 0.006, (x, -0.004, 0.035), 4), m["button"],
            col, frame, bev=(0.0015, 2))
        L.text_mesh(f"ButtonLabel_{lab}", lab, 0.0075, m["print"], col, frame, location=(x, -0.0045, 0.008))
    # Card reader on the right.
    add("Reader", L.rounded_plate_bm(0.09, 0.11, 0.01, 0.018, (0.27, -0.004, 0.0), 6), m["handle"], col, frame,
        bev=(0.002, 2))
    add("ReaderSlot", L.box_bm(0.065, 0.004, 0.006, (0.27, -0.023, 0.03)), m["gap"], col, frame)
    add("ReaderScreen", L.box_bm(0.05, 0.002, 0.025, (0.27, -0.023, -0.012)), m["led_off"], col, frame)
    L.text_mesh("PanelBrand", "aqualux  COMMERCIAL", 0.011, m["print"], col, frame, bold=True,
                location=(-0.02, -0.0045, -0.05))


def build_door(m, col, root):
    y0 = FRONT - 0.014
    door = L.root_empty("Door", col)
    door.parent = root
    hx = -BEZEL_R + 0.01          # hinges on the left, handle on the right
    door.location = (hx, y0 - 0.02, DOOR_Z)
    door.empty_display_size = 0.05

    def local(bm):
        bmesh.ops.translate(bm, vec=Vector((-hx, -(y0 - 0.02), -DOOR_Z)), verts=bm.verts)
        return bm

    center = (0, 0, DOOR_Z)
    # Polished bezel: flat front face, rounded outer edge, chamfered inner edge.
    bezel = [(BEZEL_R - 0.002, 0.0), (BEZEL_R + 0.001, -0.01), (BEZEL_R - 0.002, -0.024), (BEZEL_R - 0.012, -0.033),
             (BEZEL_R - 0.03, -0.037), (0.212, -0.037), (0.203, -0.033), (0.196, -0.024), (0.193, -0.012),
             (0.193, 0.0)]
    add("DoorBezel", local(L.revolve_bm([(r, y0 + y) for r, y in bezel], 96, True, center)), m["polished"], col,
        door, smooth=32)
    gasket = [(0.195, -0.012), (0.186, -0.02), (0.178, -0.016), (0.176, -0.006), (0.19, -0.004)]
    add("DoorGasket", local(L.revolve_bm([(r, y0 + y) for r, y in gasket], 64, True, center)), m["rubber"], col,
        door, smooth=60)
    glass = [(0.0, -0.022)] + [(0.18 * t, -0.022 + 0.01 * t * t) for t in (0.4, 0.75, 1.0)]
    add("DoorGlass", local(L.revolve_bm([(r, y0 + y) for r, y in glass], 64, False, center)), m["glass"], col, door,
        smooth=85)
    # Black handle bar across the right half of the door, on two standoffs.
    bar = L.rounded_plate_bm(0.3, 0.036, 0.016, 0.034, (0.16, y0 - 0.06, DOOR_Z), 6)
    add("HandleBar", local(bar), m["handle"], col, door, bev=(0.004, 2))
    for i, x in enumerate((0.06, 0.25)):
        add(f"HandlePost_{i}", local(L.box_bm(0.024, 0.03, 0.024, (x, y0 - 0.045, DOOR_Z))), m["handle"], col, door,
            bev=(0.005, 2))
    for i, z in enumerate((DOOR_Z - 0.17, DOOR_Z + 0.17)):
        add(f"Hinge_{i}", L.box_bm(0.03, 0.03, 0.06, (-BEZEL_R + 0.005, y0 - 0.012, z)), m["polished"], col, root,
            bev=(0.006, 2))


def build_drum(m, col, root):
    y1, y2 = FRONT + 0.01, FRONT + 0.55
    lip = [(OPEN_R, FRONT - 0.001), (OPEN_R - 0.01, FRONT + 0.015), (DRUM_R - 0.01, FRONT + 0.03)]
    add("TubFront", L.revolve_bm(lip, 64, False, (0, 0, DOOR_Z)), m["steel"], col, root, smooth=60, uv="box")
    bm = L.cylinder_bm(DRUM_R, y2 - y1, 64, (0, (y1 + y2) / 2, DOOR_Z), axis="Y", caps=False)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    drum = add("Drum", bm, m["drum"], col, root, smooth=60)
    me, tile = drum.data, 0.12
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        us = []
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a = math.atan2(co.z - DOOR_Z, co.x)
            us.append(a)
            uv.data[li].uv = (a * DRUM_R / tile, co.y / tile)
        if max(us) - min(us) > math.pi:
            for li in poly.loop_indices:
                if uv.data[li].uv[0] < 0:
                    uv.data[li].uv[0] += 2 * math.pi * DRUM_R / tile
    back = add("DrumBack", L.cylinder_bm(DRUM_R, 0.004, 64, (0, y2, DOOR_Z), axis="Y"), m["drum"], col, root)
    L.box_uv(back, texel=tile)
    for i in range(3):
        a = math.radians(90 + 120 * i)
        bm = L.box_bm(0.05, y2 - y1 - 0.04, 0.04, (0, (y1 + y2) / 2, 0))
        bmesh.ops.transform(bm, matrix=Matrix.Translation((math.cos(a) * (DRUM_R - 0.018), 0,
                                                            DOOR_Z + math.sin(a) * (DRUM_R - 0.018)))
                            @ Matrix.Rotation(-a + math.radians(90), 4, "Y"), verts=bm.verts)
        add(f"Lifter_{i}", bm, m["steel"], col, root, bev=(0.012, 2), uv="box")


STEEL_GRIME = dict(seed=17, floor=0.0, floor_band=0.35, floor_dark=0.7, stain=0.22, stain_scale=0.25)


def sticker(name, w, h, x, z, mat, col, root, lines=(), size=0.007, ink=None, y_off=0.0, rot=0.0, header=None):
    """A flat vinyl sticker on the front panel with a few lines of text."""
    y = FRONT - 0.0145 - 0.0004 - y_off
    bm = L.rounded_plate_bm(w, h, min(w, h) * 0.08, 0.0006, (x, y, z), 4)
    if rot:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(x, y, z), matrix=Matrix.Rotation(math.radians(rot), 3, "Y"))
    o = add(name, bm, mat, col, root)
    L.grime(o, seed=hash(name) % 97, floor=0.0, floor_band=0.4, floor_dark=0.8, stain=0.25, stain_scale=0.05)
    zt = z + h / 2 - size * 1.4
    if header:
        L.text_mesh(name + "_H", header, size * 1.3, ink, col, root, bold=True, location=(x, y - 0.0007, zt))
        zt -= size * 2.0
    for i, t in enumerate(lines):
        L.text_mesh(f"{name}_{i}", t, size, ink, col, root, location=(x, y - 0.0007, zt - i * size * 1.6))
    return o


def build_details(m, col, root):
    """Everything that says real people use and service this machine."""
    # How-to-use instructions on the right of the door.
    sticker("HowTo", 0.085, 0.24, 0.318, 0.62, m["sticker"], col, root, header="HOW TO USE",
            lines=["1 LOAD CLOTHES", "  DO NOT OVERLOAD", "2 ADD SOAP TO", "  TOP DISPENSER", "3 CLOSE DOOR",
                   "4 SELECT TEMP", "5 TAP ROOM KEY", "  OR CARD", "6 PRESS START", "", "REMOVE CLOTHES",
                   "PROMPTLY"], size=0.0052, ink=m["ink"])
    # Caution label, lower left.
    y = FRONT - 0.0145 - 0.0004
    tri = bmesh.new()
    v = [tri.verts.new((-0.335, y, 0.28)), tri.verts.new((-0.285, y, 0.28)), tri.verts.new((-0.31, y, 0.323))]
    tri.faces.new(v)
    add("CautionTri", tri, m["sticker_yellow"], col, root)
    L.text_mesh("CautionMark", "!", 0.026, m["ink"], col, root, bold=True, location=(-0.31, y - 0.0007, 0.293))
    sticker("Caution", 0.08, 0.05, -0.31, 0.24, m["sticker_yellow"], col, root, header="CAUTION",
            lines=["DO NOT OPEN", "DOOR WHILE", "RUNNING"], size=0.0045, ink=m["ink"])
    # Price sticker, top left of the front.
    sticker("Price", 0.11, 0.045, -0.24, 0.94, m["sticker_red"], col, root, header="WASH  $4.50",
            lines=["HOT / WARM / COLD"], size=0.0065, ink=m["ink_white"], rot=1.5)
    sticker("NoDyes", 0.07, 0.03, 0.31, 0.38, m["sticker"], col, root, header="NO DYES",
            lines=["NO TINTS"], size=0.0055, ink=m["sticker_red"])
    # Room-key card sticker on the reader side of the panel.
    sticker("TapKey", 0.07, 0.035, 0.31, 0.95, m["sticker_blue"], col, root, header="TAP KEY",
            lines=["▲ READER"], size=0.006, ink=m["ink_white"])
    # Rating plate, key lock on the service panel, leftover tape from an old note.
    add("SerialPlate", L.box_bm(0.07, 0.0012, 0.035, (0.29, y - 0.0003, 0.1)), m["plate"], col, root)
    for i, t in enumerate(["MODEL WX450", "SN 2610-0447", "208-240V 60Hz"]):
        L.text_mesh(f"Serial_{i}", t, 0.0042, m["ink"], col, root, location=(0.29, y - 0.0012, 0.11 - i * 0.008))
    add("KeyLock", L.cylinder_bm(0.012, 0.01, 24, (-0.3, y - 0.004, 0.09), axis="Y"), m["polished"], col, root,
        bev=(0.002, 2, 30))
    add("KeyHole", L.box_bm(0.0025, 0.002, 0.009, (-0.3, y - 0.0095, 0.09)), m["gap"], col, root)
    for i, (x, z, r) in enumerate(((-0.05, 0.965, 3.0), (0.12, 0.97, -2.0))):
        bm = L.box_bm(0.06, 0.0006, 0.014, (x, y - 0.0002, z))
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(x, y, z), matrix=Matrix.Rotation(math.radians(r), 3, "Y"))
        add(f"TapeResidue_{i}", bm, m["tape"], col, root)

    # Top soap dispenser: hinged lid with a finger notch, dried residue dribbling over the edge.
    zt = H + 0.012
    add("SoapLid", L.rounded_plate_bm(0.24, 0.17, 0.012, 0.008, (-0.21, 0.06, 0.0), 6), m["steel"], col, root,
        bev=(0.002, 2), uv="box")
    lid = bpy.data.objects["SoapLid"]
    lid.rotation_euler = (math.radians(-90), 0, 0)
    lid.location = (0, 0.0, zt)
    add("SoapNotch", L.box_bm(0.05, 0.012, 0.004, (-0.21, -0.025, zt + 0.009)), m["gap"], col, root)
    add("SoapHinge", L.cylinder_bm(0.005, 0.22, 16, (-0.21, 0.145, zt + 0.005), axis="X"), m["polished"], col, root)
    L.text_mesh("SoapLabel", "SOAP • BLEACH • SOFTENER", 0.0085, m["ink"], col, root,
                location=(-0.21, 0.04, zt + 0.0092), rotation=(0, 0, 0))
    for i, (x, w, ln) in enumerate(((-0.27, 0.03, 0.05), (-0.2, 0.018, 0.035), (-0.14, 0.04, 0.025))):
        add(f"Residue_{i}", L.rounded_plate_bm(w, ln, w * 0.4, 0.0008, (x, -0.02 - ln / 2, zt + 0.0006), 4),
            m["residue"], col, root)
        bpy.data.objects[f"Residue_{i}"].rotation_euler = (math.radians(-90), 0, 0)

    # Somebody's load left in the drum (Unity shows it on some machines only).
    load = L.root_empty("Load", col)
    load.parent = root
    pile = _cloth_pile(0.38, 0.4, 0.16, (0, FRONT + 0.3, DOOR_Z - DRUM_R + 0.09))
    o = add("LoadCloth", pile, m["cloth"], col, load, uv="box", texel=0.25, smooth=80)
    L.grime(o, seed=5, floor=-10, stain=0.35, stain_scale=0.08)


def _cloth_pile(w, d, h, center):
    from mathutils import noise
    bm = L.box_bm(w, d, h, center)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True)
    for v in bm.verts:
        n = noise.fractal(v.co * 9.0, 0.6, 2.0, 4)
        v.co += v.normal * 0.035 * n
        # sag into the curved drum bottom
        v.co.z -= 0.06 * (2 * (v.co.x - center[0]) / w) ** 2
    return bm


def build():
    L.clear_collection(NAME)
    col = L.collection(NAME)
    col.hide_viewport = False
    col.hide_render = False
    root = L.root_empty(NAME, col)
    m = materials()
    build_cabinet(m, col, root)
    build_controls(m, col, root)
    build_door(m, col, root)
    build_drum(m, col, root)
    build_details(m, col, root)
    for name in ("Cabinet", "FrontPanel", "ControlHousing"):
        L.grime(bpy.data.objects[name], **STEEL_GRIME)
    return _tris(col)


def _tris(col):
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for obj in col.all_objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(dg).data
            ev.calc_loop_triangles()
            tris += len(ev.loop_triangles)
    return {"objects": len(col.all_objects), "triangles": tris}


def render_bank(out_dir, dryer=False):
    """Three machines side by side (like the photo), lit softly, for comparison."""
    import runpy
    lib = runpy.run_path(os.path.expanduser("~/Documents/GitHub/ArtGameCollab2.mds/blender/hotel_laundry/props.py"),
                         run_name="lib")
    scene = bpy.context.scene
    for c in bpy.data.collections:
        c.hide_render = c.name not in (NAME, "_LookDev", "_Bank")
    lk = L.collection("_LookDev")
    L.clear_collection("_LookDev")
    L.link(L.mesh_object("Floor", L.box_bm(8, 8, 0.01, (0, 0, -0.005)),
                         L.material("LookDev_Floor", base=(0.5, 0.5, 0.48), roughness=0.5)), lk)
    bank = L.collection("_Bank")
    L.clear_collection("_Bank")
    src = bpy.data.objects[NAME]
    for i, x in enumerate((-W, W)):
        inst = bpy.data.objects.new(f"BankCopy_{i}", None)
        inst.instance_type = "COLLECTION"
        inst.instance_collection = bpy.data.collections[NAME]
        inst.location = (x, 0, 0)
        bank.objects.link(inst)
    world = bpy.data.worlds.get("LookDev")
    scene.world = world
    cam_data = bpy.data.cameras.get("BankCam") or bpy.data.cameras.new("BankCam")
    cam_data.lens = 32
    cam = L.link(bpy.data.objects.new("BankCam", cam_data), lk)
    cam.location = (-1.6, -1.9, 1.35)
    cam.rotation_euler = (Vector((0.35, 0, 0.7)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    for i, (x, y) in enumerate(((-1.5, -1.5), (1.5, -1.5))):
        ld = bpy.data.lights.new(f"BankKey_{i}", "AREA")
        ld.energy = 180
        ld.size = 2.0
        lo = L.link(bpy.data.objects.new(f"BankKey_{i}", ld), lk)
        lo.location = (x, y, 2.8)
        lo.rotation_euler = (Vector((0, 0, 0.8)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x, scene.render.resolution_y = 1500, 1000
    scene.view_settings.exposure = 0.0
    scene.render.filepath = os.path.join(out_dir, f"{NAME}_bank.png")
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath
