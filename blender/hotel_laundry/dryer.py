"""Laundromat stack dryer (two dryer pockets, one above the other), matching the
stainless laundromat washer bank (docs/references/washer.md, dryer section):
~790 W x 1950 H x 960 D mm body, satin stainless front, polished door bezels with
vertical grips, black control band between the pockets, lint drawers, warning
stickers and an exhaust duct up to the ceiling. Front faces -Y, origin at floor.
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

NAME = "TumbleDryer"          # kept so the Unity references stay valid

W, D, H = 0.79, 0.96, 1.95
FRONT = -D / 2
POCKETS = {"Lower": 0.6, "Upper": 1.43}     # door centre heights
BAND = (0.98, 1.06)                         # control band between the pockets
BEZEL_R = 0.255
GLASS_R = 0.2
DRUM_R = 0.34
CEILING = 3.2
STEEL_GRIME = dict(seed=23, floor=0.0, floor_band=0.45, floor_dark=0.5, stain=0.32, stain_scale=0.2, drip=0.25)


def materials():
    return {
        "steel": L.material("Stainless_Aged", metallic=1.0, tex="stainless_aged", normal_strength=0.35,
                            vertex_color=True),
        "polished": L.material("Stainless_Polished", base=(0.9, 0.9, 0.91), metallic=1.0, roughness=0.09),
        "panel": L.material("Panel_BlackAged", tex="plastic_black_aged", normal_strength=0.4, coat=0.6),
        "handle": L.material("Handle_BlackWorn", tex="plastic_black_aged", normal_strength=0.5),
        "led": L.material("LED_Red", base=(0.8, 0.1, 0.05), emission=(1.0, 0.15, 0.06), emission_strength=3.0),
        "led_off": L.material("LED_Dark", base=(0.01, 0.04, 0.02), roughness=0.1, coat=1.0),
        "glass": L.material("Glass_DoorTint", base=(0.04, 0.045, 0.045), roughness=0.03, alpha=0.45, ior=1.52),
        "galv": L.material("Drum_Galvanized", base=(0.6, 0.61, 0.6), metallic=1.0, tex="drum_perforated",
                           normal_strength=1.0),
        "rubber": L.material("Rubber_Aged", tex="rubber_aged", normal_strength=0.6),
        "gap": L.material("Gap_Dark", base=(0.03, 0.03, 0.032), roughness=0.6),
        "duct": L.material("Duct_Galvanized", base=(0.5, 0.51, 0.5), metallic=0.9, roughness=0.5, vertex_color=True),
        "foil": L.material("Duct_Foil", base=(0.75, 0.75, 0.74), metallic=0.9, roughness=0.35, vertex_color=True),
        "sticker": L.material("Sticker_WhiteWorn", tex="sticker_aged", vertex_color=True),
        "sticker_yellow": L.material("Sticker_YellowWorn", tex="sticker_aged", tint=(1.0, 0.78, 0.08)),
        "sticker_red": L.material("Sticker_RedWorn", tex="sticker_aged", tint=(0.75, 0.07, 0.05)),
        "ink": L.material("Ink_Black", base=(0.02, 0.02, 0.02), roughness=0.6),
        "ink_white": L.material("Ink_White", base=(0.95, 0.95, 0.95), roughness=0.5),
        "print": L.material("Print_White", base=(0.88, 0.89, 0.9), roughness=0.35),
        "lint": L.material("Lint_Grey", base=(0.55, 0.53, 0.52), tex="towel", normal_strength=1.5),
        "cloth": L.material("Cloth_Load", base=(0.55, 0.6, 0.68), tex="towel", normal_strength=1.0, vertex_color=True),
    }


def add(name, bm, mat, col, parent, bev=None, uv=None, texel=0.5, smooth=35.0, dirt=None):
    obj = L.link(L.mesh_object(name, bm, mat, smooth), col, parent)
    if uv == "box":
        L.box_uv(obj, texel)
    if dirt is not None:
        L.grime(obj, **dirt)
    if bev:
        L.bevel(obj, *bev)
        L.weighted_normals(obj)
    L.triangulate(obj)
    return obj


def sticker(name, w, h, x, z, mat, col, root, lines=(), size=0.007, ink=None, header=None, rot=0.0):
    y = FRONT - 0.0145 - 0.0015      # >= 1.5 mm off the panel (no z-fighting)
    bm = L.rounded_plate_bm(w, h, min(w, h) * 0.08, 0.0006, (x, y, z), 4)
    if rot:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(x, y, z), matrix=Matrix.Rotation(math.radians(rot), 3, "Y"))
    o = add(name, bm, mat, col, root)
    L.grime(o, seed=hash(name) % 97, floor=0.0, floor_band=0.4, floor_dark=0.8, stain=0.25, stain_scale=0.05)
    zt = z + h / 2 - size * 1.4
    if header:
        L.text_mesh(name + "_H", header, size * 1.3, ink, col, root, bold=True, location=(x, y - 0.0012, zt))
        zt -= size * 2.0
    for i, t in enumerate(lines):
        L.text_mesh(f"{name}_{i}", t, size, ink, col, root, location=(x, y - 0.0012, zt - i * size * 1.6))


def build_cabinet(m, col, root):
    add("Cabinet", L.box_bm(W, D, H, (0, 0, H / 2), skip=("-y",)), m["steel"], col, root, bev=(0.004, 2), uv="box",
        dirt=STEEL_GRIME)
    panel = L.link(L.mesh_object("FrontPanel", L.box_bm(W - 0.002, 0.014, H - 0.004, (0, FRONT - 0.007, H / 2)),
                                 m["steel"]), col, root)
    for z in POCKETS.values():
        L.boolean_cut(panel, L.cylinder_bm(GLASS_R + 0.012, 0.1, 64, (0, FRONT, z), axis="Y"))
    L.box_uv(panel)
    L.grime(panel, **STEEL_GRIME)
    L.bevel(panel, 0.004, 2)
    L.weighted_normals(panel)
    L.triangulate(panel)
    y = FRONT - 0.0145
    # Black control band with two LED readouts and a shared card reader.
    zc = sum(BAND) / 2
    add("ControlBand", L.box_bm(W - 0.02, 0.006, BAND[1] - BAND[0], (0, y - 0.003, zc)), m["panel"], col, root,
        bev=(0.002, 2))
    for i, (x, lab) in enumerate(((-0.24, "UPPER"), (0.0, "LOWER"))):
        add(f"LED_{lab}", L.box_bm(0.11, 0.002, 0.04, (x, y - 0.0065, zc + 0.006)), m["led_off"], col, root)
        L.text_mesh(f"LEDDigits_{lab}", "12" if i == 0 else "00", 0.03, m["led"], col, root, bold=True,
                    location=(x, y - 0.0102, zc + 0.006))
        L.text_mesh(f"LEDLabel_{lab}", lab + "  MIN", 0.0075, m["print"], col, root, location=(x, y - 0.0085, zc - 0.028))
    add("Reader", L.rounded_plate_bm(0.08, 0.07, 0.01, 0.015, (0.27, y - 0.006, zc), 6), m["handle"], col, root,
        bev=(0.002, 2))
    add("ReaderSlot", L.box_bm(0.06, 0.004, 0.005, (0.27, y - 0.0215, zc + 0.012)), m["gap"], col, root)
    # Lint drawers: one per pocket, below each door, with a pull and key lock.
    for name, z in (("Lower", 0.16), ("Upper", 1.11)):
        add(f"LintSeam_{name}", L.box_bm(W - 0.08, 0.003, 0.004, (0, y - 0.0015, z + 0.055)), m["gap"], col, root)
        add(f"LintPull_{name}", L.rounded_plate_bm(0.16, 0.022, 0.009, 0.012, (0, y - 0.006, z), 6), m["handle"],
            col, root, bev=(0.002, 2))
        add(f"LintLock_{name}", L.cylinder_bm(0.01, 0.008, 20, (0.3, y - 0.004, z), axis="Y"), m["polished"], col,
            root)
        add(f"LintKeyHole_{name}", L.box_bm(0.002, 0.002, 0.008, (0.3, y - 0.0085, z)), m["gap"], col, root)
    for i, (x, z) in enumerate(((-0.37, 0.03), (0.37, 0.03), (-0.37, 1.92), (0.37, 1.92))):
        add(f"Screw_{i}", L.cylinder_bm(0.005, 0.003, 16, (x, y - 0.0015, z), axis="Y"), m["polished"], col, root)


def build_pocket(m, col, root, name, z):
    y0 = FRONT - 0.014
    center = (0, 0, z)
    # Drum (galvanised, perforated) with lifters.
    y1, y2 = FRONT + 0.01, FRONT + 0.72
    bm = L.cylinder_bm(DRUM_R, y2 - y1, 64, (0, (y1 + y2) / 2, z), axis="Y", caps=False)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    drum = add(f"Drum{name}", bm, m["galv"], col, root, smooth=60)
    me, tile = drum.data, 0.12
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        us = []
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a = math.atan2(co.z - z, co.x)
            us.append(a)
            uv.data[li].uv = (a * DRUM_R / tile, co.y / tile)
        if max(us) - min(us) > math.pi:
            for li in poly.loop_indices:
                if uv.data[li].uv[0] < 0:
                    uv.data[li].uv[0] += 2 * math.pi * DRUM_R / tile
    back = add(f"DrumBack{name}", L.cylinder_bm(DRUM_R, 0.004, 64, (0, y2, z), axis="Y"), m["galv"], col, root)
    L.box_uv(back, texel=tile)
    add(f"DrumLip{name}", L.revolve_bm([(GLASS_R + 0.012, FRONT - 0.001), (DRUM_R, FRONT + 0.02)], 64, False, center),
        m["steel"], col, root, uv="box")
    for i in range(3):
        a = math.radians(30 + 120 * i)
        bm = L.box_bm(0.06, y2 - y1 - 0.04, 0.05, (0, (y1 + y2) / 2, 0))
        bmesh.ops.transform(bm, matrix=Matrix.Translation((math.cos(a) * (DRUM_R - 0.022), 0,
                                                            z + math.sin(a) * (DRUM_R - 0.022)))
                            @ Matrix.Rotation(-a + math.radians(90), 4, "Y"), verts=bm.verts)
        add(f"Lifter{name}_{i}", bm, m["galv"], col, root, bev=(0.015, 2), uv="box")

    # Door: pivot on the left hinge so it can swing in Unity.
    door = L.root_empty(f"Door{name}", col)
    door.parent = root
    hx = -BEZEL_R + 0.01
    door.location = (hx, y0 - 0.02, z)
    door.empty_display_size = 0.05

    def local(bm):
        bmesh.ops.translate(bm, vec=Vector((-hx, -(y0 - 0.02), -z)), verts=bm.verts)
        return bm

    bezel = [(BEZEL_R - 0.002, 0.0), (BEZEL_R + 0.001, -0.01), (BEZEL_R - 0.002, -0.022), (BEZEL_R - 0.012, -0.03),
             (BEZEL_R - 0.03, -0.033), (GLASS_R + 0.02, -0.033), (GLASS_R + 0.01, -0.028), (GLASS_R + 0.004, -0.018),
             (GLASS_R + 0.002, 0.0)]
    add(f"DoorBezel{name}", local(L.revolve_bm([(r, y0 + y) for r, y in bezel], 96, True, center)), m["polished"],
        col, door, smooth=32)
    glass = [(0.0, -0.02)] + [(GLASS_R * t, -0.02 + 0.008 * t * t) for t in (0.4, 0.75, 1.0)]
    add(f"DoorGlass{name}", local(L.revolve_bm([(r, y0 + y) for r, y in glass], 64, False, center)), m["glass"], col,
        door, smooth=85)
    grip = L.rounded_plate_bm(0.03, 0.16, 0.014, 0.03, (BEZEL_R - 0.035, y0 - 0.052, z), 6)
    add(f"DoorGrip{name}", local(grip), m["handle"], col, door, bev=(0.004, 2))
    for i, dz in enumerate((-0.15, 0.15)):
        add(f"Hinge{name}_{i}", L.box_bm(0.028, 0.03, 0.055, (-BEZEL_R + 0.004, y0 - 0.012, z + dz)), m["polished"],
            col, root, bev=(0.005, 2))

    # Someone's load still in the drum (shown on some machines in Unity).
    load = L.root_empty(f"Load{name}", col)
    load.parent = root
    from mathutils import noise
    pile = L.box_bm(0.45, 0.5, 0.2, (0, FRONT + 0.38, z - DRUM_R + 0.11))
    bmesh.ops.subdivide_edges(pile, edges=pile.edges[:], cuts=8, use_grid_fill=True)
    for v in pile.verts:
        v.co += v.normal * 0.04 * noise.fractal(v.co * 8.0 + Vector((z, 0, 0)), 0.6, 2.0, 4)
        v.co.z -= 0.07 * (2 * v.co.x / 0.45) ** 2
    o = add(f"LoadCloth{name}", pile, m["cloth"], col, load, uv="box", texel=0.25, smooth=80)
    L.grime(o, seed=int(z * 10), floor=-10, stain=0.3, stain_scale=0.08)


def build_details(m, col, root):
    sticker("Price", 0.12, 0.05, -0.25, 1.82, m["sticker_red"], col, root, header="DRY  $0.25",
            lines=["PER 8 MINUTES"], size=0.0068, ink=m["ink_white"], rot=-1.0)
    sticker("LintWarn", 0.12, 0.07, 0.27, 1.8, m["sticker"], col, root, header="CLEAN LINT SCREEN",
            lines=["BEFORE EACH USE", "FIRE HAZARD"], size=0.0055, ink=m["ink"])
    sticker("FireWarn", 0.1, 0.06, -0.29, 0.92, m["sticker_yellow"], col, root, header="WARNING",
            lines=["DO NOT DRY RUBBER,", "FOAM OR OILY RAGS"], size=0.0045, ink=m["ink"])
    sticker("TempKey", 0.08, 0.05, 0.3, 0.92, m["sticker"], col, root, header="TEMP",
            lines=["HIGH  COTTON", "MED   PERM PRESS", "LOW   DELICATE"], size=0.0048, ink=m["ink"])
    sticker("NoChildren", 0.09, 0.03, 0.29, 0.34, m["sticker"], col, root, header="DO NOT LET",
            lines=["CHILDREN PLAY IN DRYER"], size=0.0045, ink=m["sticker_red"])
    # Exhaust: collar on the top rear, foil flex connector, rigid duct up to the ceiling.
    yd = D / 2 - 0.16
    add("ExhaustCollar", L.cylinder_bm(0.1, 0.08, 32, (0.18, yd, H + 0.04)), m["duct"], col, root,
        dirt=dict(seed=301, floor=-10, stain=0.4, stain_scale=0.3))
    from mathutils import noise
    flex = L.cylinder_bm(0.105, 0.3, 32, (0.18, yd, H + 0.23), caps=False)
    bmesh.ops.subdivide_edges(flex, edges=[e for e in flex.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.01],
                              cuts=14)
    for v in flex.verts:
        k = math.sin((v.co.z - H) * 140)
        r = Vector((v.co.x - 0.18, v.co.y - yd, 0))
        if r.length > 0:
            v.co += r.normalized() * 0.006 * k
    add("ExhaustFlex", flex, m["foil"], col, root, smooth=60, dirt=dict(seed=304, floor=-10, stain=0.5, stain_scale=0.1))
    add("ExhaustDuct", L.cylinder_bm(0.1, CEILING - H - 0.38, 32, (0.18, yd, (CEILING + H + 0.38) / 2), caps=False),
        m["duct"], col, root, dirt=dict(seed=302, floor=-10, stain=0.5, stain_scale=0.3, drip=0.4))
    for i, zz in enumerate((H + 0.4, H + 0.9)):
        add(f"DuctBand_{i}", L.cylinder_bm(0.104, 0.02, 32, (0.18, yd, zz)), m["duct"], col, root,
            dirt=dict(seed=303 + i, floor=-10, stain=0.3))
    # Lint caught in the lower drawer seam.
    add("LintTuft", L.box_bm(0.1, 0.008, 0.012, (-0.12, FRONT - 0.016, 0.218)), m["lint"], col, root,
        bev=(0.004, 2), uv="box", texel=0.1)


def run():
    L.clear_collection(NAME)
    col = L.collection(NAME)
    col.hide_viewport = False
    col.hide_render = False
    root = L.root_empty(NAME, col)
    m = materials()
    build_cabinet(m, col, root)
    for name, z in POCKETS.items():
        build_pocket(m, col, root, name, z)
    build_details(m, col, root)
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for obj in col.all_objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(dg).data
            ev.calc_loop_triangles()
            tris += len(ev.loop_triangles)
    return {"objects": len(col.all_objects), "triangles": tris}
