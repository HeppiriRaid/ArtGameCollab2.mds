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
COLLAR_R = 0.292            # pressed collar in the front panel around the door
TRIM_R = 0.264              # door's outer chrome trim
BEZEL_R = TRIM_R            # (older name, used by stickers/notes layout)
OPEN_R = 0.2
DRUM_R = 0.29


def materials():
    return {
        "steel": L.material("Stainless_Aged", metallic=1.0, tex="stainless_aged", normal_strength=0.35,
                            vertex_color=True),
        "sticker": L.material("Sticker_WhiteWorn", tex="sticker_aged", vertex_color=True),
        "sticker_yellow": L.material("Sticker_YellowWorn", tex="sticker_aged", tint=(1.0, 0.78, 0.08)),
        "sticker_red": L.material("Sticker_RedWorn", tex="sticker_aged", tint=(0.75, 0.07, 0.05)),
        "sticker_blue": L.material("Sticker_BlueWorn", tex="sticker_aged", tint=(0.07, 0.25, 0.6)),
        "ink": L.material("Ink_Black", base=(0.02, 0.02, 0.02), roughness=0.6),
        "ink_white": L.material("Ink_White", base=(0.95, 0.95, 0.95), roughness=0.5),
        "plate": L.material("Plate_Silver", base=(0.72, 0.72, 0.7), metallic=0.85, roughness=0.35),
        "tape": L.material("Tape_Residue", base=(0.72, 0.66, 0.5), roughness=0.75, alpha=0.6),
        "residue": L.material("Soap_Residue", base=(0.62, 0.72, 0.85), roughness=0.8, alpha=0.55),
        "cloth": L.material("Cloth_Load", base=(0.55, 0.6, 0.68), tex="towel", normal_strength=1.0,
                            vertex_color=True),
        "polished": L.material("Stainless_Polished", base=(0.9, 0.9, 0.91), metallic=1.0, roughness=0.09),
        "panel": L.material("Panel_BlackAged", tex="plastic_black_aged", normal_strength=0.4, coat=0.6),
        "handle": L.material("Handle_BlackWorn", tex="plastic_black_aged", normal_strength=0.5),
        "led": L.material("LED_Green", base=(0.1, 0.8, 0.3), emission=(0.15, 1.0, 0.35), emission_strength=3.0),
        "led_off": L.material("LED_Dark", base=(0.01, 0.04, 0.02), roughness=0.1, coat=1.0),
        "print": L.material("Print_White", base=(0.88, 0.89, 0.9), roughness=0.35),
        "button": L.material("Button_Grey", base=(0.35, 0.36, 0.37), metallic=0.6, roughness=0.3),
        "glass": L.material("Glass_DoorTint", base=(0.04, 0.045, 0.045), roughness=0.03, alpha=0.4, ior=1.52),
        "glass_inner": L.material("Glass_Bowl", base=(0.03, 0.035, 0.035), roughness=0.06, alpha=0.3, ior=1.52),
        "frost": L.material("Glass_FrostBand", base=(0.5, 0.52, 0.52), roughness=0.55, alpha=0.65),
        "rubber": L.material("Rubber_Aged", tex="rubber_aged", normal_strength=0.6),
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


def screw(name, x, y, z, col, root, m, r=0.0045, axis="Y"):
    """Countersunk Phillips screw head: domed head plus a recessed cross."""
    head = L.revolve_bm([(0.0, -0.0022), (r * 0.6, -0.002), (r, -0.0008), (r, 0.0), (0.0, 0.0)], 16, True, (0, 0, 0))
    bmesh.ops.translate(head, vec=Vector((x, y, z)), verts=head.verts)
    add(name, head, m["polished"], col, root, smooth=60)
    for k, (sx, sz) in enumerate(((r * 1.1, r * 0.25), (r * 0.25, r * 1.1))):
        add(f"{name}_x{k}", L.box_bm(sx, 0.0008, sz, (x, y - 0.0022, z)), m["gap"], col, root)


def build_cabinet(m, col, root, lod=0):
    add("Cabinet", L.box_bm(W, D, Z_PANEL, (0, 0, Z_PANEL / 2), skip=("-y",)), m["steel"], col, root,
        bev=(0.004, 2), uv="box")
    # Front panel: sheet with a big opening; its pressed door collar is a separate part.
    panel = L.link(L.mesh_object("FrontPanel", L.box_bm(W - 0.002, 0.014, Z_PANEL - 0.17,
                                                        (0, FRONT - 0.007, (Z_PANEL + 0.17) / 2)), m["steel"]), col,
                   root)
    L.boolean_cut(panel, L.cylinder_bm(COLLAR_R - 0.004, 0.1, 64, (0, FRONT, DOOR_Z), axis="Y"))
    L.box_uv(panel)
    L.bevel(panel, 0.004, 2)
    L.weighted_normals(panel)
    L.triangulate(panel)
    y0 = FRONT - 0.014
    # Pressed collar: raised lip, trough, then rolled down into the opening. Its
    # back sits inside the panel thickness (no coplanar faces with the panel).
    collar = [(COLLAR_R, 0.004), (COLLAR_R, -0.002), (COLLAR_R - 0.005, -0.006), (COLLAR_R - 0.016, -0.008),
              (COLLAR_R - 0.026, -0.006), (COLLAR_R - 0.032, -0.002), (COLLAR_R - 0.036, 0.004),
              (COLLAR_R - 0.04, 0.014), (COLLAR_R - 0.044, 0.03), (COLLAR_R - 0.03, 0.03)]
    add("DoorCollar", L.revolve_bm([(r, y0 + y) for r, y in collar], 96 if lod == 0 else 40, True, (0, 0, DOOR_Z)),
        m["steel"], col, root, smooth=40, uv="box")
    # Kick panel: separate recessed plate with punched louvres.
    add("KickPanel", L.box_bm(W - 0.012, 0.012, 0.15, (0, FRONT - 0.002, 0.085)), m["steel"], col, root,
        bev=(0.003, 2), uv="box")
    add("KickShadowGap", L.box_bm(W - 0.006, 0.004, 0.006, (0, FRONT - 0.0105, 0.164)), m["gap"], col, root)
    if lod == 0:
        for i in range(9):
            x = -0.24 + i * 0.06
            add(f"Louvre_{i}", L.rounded_plate_bm(0.042, 0.012, 0.005, 0.004, (x, FRONT - 0.006, 0.1), 4), m["gap"],
                col, root)
            lip = L.box_bm(0.044, 0.006, 0.0025, (x, FRONT - 0.0105, 0.1065))
            add(f"LouvreLip_{i}", lip, m["steel"], col, root, uv="box")
        for i, x in enumerate((-0.345, 0.345)):
            screw(f"KickScrew_{i}", x, FRONT - 0.0085, 0.085, col, root, m)
        add("ServiceLock", L.cylinder_bm(0.011, 0.008, 24, (0.29, FRONT - 0.012, 0.05), axis="Y"), m["polished"],
            col, root, bev=(0.002, 2, 30))
        add("ServiceKeyway", L.box_bm(0.0025, 0.002, 0.009, (0.29, FRONT - 0.0165, 0.05)), m["gap"], col, root)
        for i, (x, z) in enumerate(((-0.345, 0.2), (0.345, 0.2), (-0.345, 0.965), (0.345, 0.965))):
            screw(f"PanelScrew_{i}", x, FRONT - 0.0155, z, col, root, m)
        # Folded panel returns: thin vertical lips where neighbouring machines meet.
        for i, x in enumerate((-W / 2 + 0.003, W / 2 - 0.003)):
            add(f"PanelReturn_{i}", L.box_bm(0.006, 0.02, Z_PANEL - 0.18, (x, FRONT - 0.006, (Z_PANEL + 0.18) / 2)),
                m["polished"], col, root, bev=(0.002, 2))
        # Door latch receptacle on the cabinet, right of the opening.
        add("LatchHousing", L.rounded_plate_bm(0.03, 0.07, 0.006, 0.012, (COLLAR_R + 0.03, y0 - 0.001, DOOR_Z), 4),
            m["panel"], col, root, bev=(0.002, 2))
        add("LatchSlot", L.box_bm(0.008, 0.004, 0.03, (COLLAR_R + 0.03, y0 - 0.0135, DOOR_Z)), m["gap"], col, root)

    # Control housing: stainless box whose front leans back.
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
    add("LEDWindow", L.box_bm(0.15, 0.002, 0.06, (-0.21, -0.0055, 0.03)), m["led_off"], col, frame)
    L.text_mesh("LEDDigits", "28", 0.045, m["led"], col, frame, bold=True, location=(-0.21, -0.009, 0.03))
    L.text_mesh("LEDLabel", "MINUTES REMAINING", 0.0075, m["print"], col, frame, location=(-0.21, -0.0065, -0.012))
    labels = ["HOT", "WARM", "COLD", "START"]
    for i, lab in enumerate(labels):
        x = -0.06 + i * 0.05
        add(f"Button_{lab}", L.rounded_plate_bm(0.034, 0.022, 0.006, 0.006, (x, -0.004, 0.035), 4), m["button"],
            col, frame, bev=(0.0015, 2))
        L.text_mesh(f"ButtonLabel_{lab}", lab, 0.0075, m["print"], col, frame, location=(x, -0.0065, 0.008))
    # Card reader on the right.
    add("Reader", L.rounded_plate_bm(0.09, 0.11, 0.01, 0.018, (0.27, -0.004, 0.0), 6), m["handle"], col, frame,
        bev=(0.002, 2))
    add("ReaderSlot", L.box_bm(0.065, 0.004, 0.006, (0.27, -0.023, 0.03)), m["gap"], col, frame)
    add("ReaderScreen", L.box_bm(0.05, 0.002, 0.025, (0.27, -0.023, -0.012)), m["led_off"], col, frame)
    L.text_mesh("PanelBrand", "aqualux  COMMERCIAL", 0.011, m["print"], col, frame, bold=True,
                location=(-0.02, -0.0065, -0.05))


def build_door(m, col, root, lod=0):
    """Door assembly as manufactured: chrome trim rim, satin face ring with screws,
    inner chrome step, black glass retainer, frosted-edge outer glass, thick inner
    glass bowl, handle with end caps and fixings, two-knuckle hinge."""
    y0 = FRONT - 0.014
    seg = 96 if lod == 0 else 40
    door = L.root_empty("Door", col)
    door.parent = root
    hx = -TRIM_R - 0.012              # hinge axis just outside the trim on the left
    door.location = (hx, y0 - 0.02, DOOR_Z)
    door.empty_display_size = 0.05

    def local(bm):
        bmesh.ops.translate(bm, vec=Vector((-hx, -(y0 - 0.02), -DOOR_Z)), verts=bm.verts)
        return bm

    def ring(name, prof, mat, smooth=30, n=seg):
        return add(name, local(L.revolve_bm([(r, y0 + y) for r, y in prof], n, True, (0, 0, DOOR_Z))), mat, col,
                   door, smooth=smooth)

    ring("DoorTrim", [(TRIM_R - 0.012, -0.004), (TRIM_R - 0.011, -0.022), (TRIM_R - 0.006, -0.031), (TRIM_R, -0.029),
                      (TRIM_R + 0.0015, -0.016), (TRIM_R, -0.005)], m["polished"])
    face = [(TRIM_R - 0.012, -0.008), (TRIM_R - 0.012, -0.03), (0.236, -0.0325), (0.222, -0.0345), (0.214, -0.035),
            (0.214, -0.008)]
    o = ring("DoorFace", face, m["steel"], smooth=25)
    L.box_uv(o)
    ring("DoorStep", [(0.2145, -0.0348), (0.212, -0.0372), (0.205, -0.0365), (0.2, -0.03), (0.198, -0.02),
                      (0.199, -0.008), (0.2145, -0.008)], m["polished"])
    ring("GlassRetainer", [(0.1995, -0.012), (0.1995, -0.023), (0.196, -0.029), (0.187, -0.0305), (0.181, -0.027),
                           (0.181, -0.012)], m["panel"])
    # Outer glass with a frosted print band at its edge, then the thick inner bowl.
    add("GlassOuter", local(L.revolve_bm([(r, y0 + y) for r, y in
                                          [(0.0, -0.029)] + [(0.17 * t, -0.029 + 0.003 * t * t) for t in (0.5, 0.85, 1.0)]],
                                         seg, False, (0, 0, DOOR_Z))), m["glass"], col, door, smooth=85)
    add("GlassFrost", local(L.revolve_bm([(0.17, y0 - 0.026), (0.1825, y0 - 0.0255)], seg, False, (0, 0, DOOR_Z))),
        m["frost"], col, door, smooth=85)
    if lod == 0:
        bowl = [(0.0, 0.1)] + [(0.15 * t, 0.1 - 0.105 * t * t) for t in (0.35, 0.6, 0.8, 0.93, 1.0)] + [(0.176, -0.01)]
        add("GlassBowl", local(L.revolve_bm([(r, y0 + y) for r, y in bowl], 64, False, (0, 0, DOOR_Z))),
            m["glass_inner"], col, door, smooth=85)
        bowl2 = [(r * 0.97, y + 0.007) for r, y in bowl]
        add("GlassBowlBack", local(L.revolve_bm([(r, y0 + y) for r, y in bowl2], 64, False, (0, 0, DOOR_Z))),
            m["glass_inner"], col, door, smooth=85)
        # Eight screws hold the face ring to the inner frame.
        for k in range(8):
            a = 2 * math.pi * (k + 0.5) / 8
            r = 0.231
            yz = -0.0335 - 0.0005
            hb = L.revolve_bm([(0.0, -0.0018), (0.0026, -0.0016), (0.0038, -0.0006), (0.0038, 0.0), (0.0, 0.0)], 12,
                              True, (0, 0, 0))
            bmesh.ops.translate(hb, vec=Vector((math.cos(a) * r, y0 + yz, DOOR_Z + math.sin(a) * r)), verts=hb.verts)
            add(f"FaceScrew_{k}", local(hb), m["polished"], col, door, smooth=60)

    # Handle: black bar with ribbed grip, chrome end caps and escutcheons on two posts.
    hz = DOOR_Z
    bar = L.rounded_plate_bm(0.27, 0.034, 0.016, 0.03, (0.165, y0 - 0.068, hz), 8)
    add("HandleBar", local(bar), m["handle"], col, door, bev=(0.005, 3))
    for i, x in enumerate((0.07, 0.255)):
        add(f"HandlePost_{i}", local(L.cylinder_bm(0.011, 0.04, 20, (x, y0 - 0.05, hz), axis="Y")), m["handle"],
            col, door)
        add(f"HandleRose_{i}", local(L.cylinder_bm(0.018, 0.004, 32, (x, y0 - 0.0355, hz), axis="Y")), m["polished"],
            col, door, bev=(0.0015, 2, 30))
    if lod == 0:
        for i, x in enumerate((0.03, 0.3)):
            add(f"HandleCap_{i}", local(L.box_bm(0.012, 0.032, 0.03, (x, y0 - 0.068, hz))), m["polished"], col, door,
                bev=(0.006, 3))
        for k in range(7):
            add(f"GripRib_{k}", local(L.box_bm(0.004, 0.0015, 0.03, (0.12 + k * 0.016, y0 - 0.0855, hz))), m["panel"],
                col, door)
    # Hinge: cabinet block, two knuckles on the door, vertical pin, cover plate.
    for i, dz in enumerate((-0.14, 0.14)):
        z = DOOR_Z + dz
        add(f"HingeBlock_{i}", L.box_bm(0.03, 0.022, 0.07, (hx - 0.004, y0 - 0.011, z)), m["polished"], col, root,
            bev=(0.005, 2))
        add(f"HingeKnuckle_{i}", local(L.cylinder_bm(0.011, 0.05, 24, (hx, y0 - 0.02, z))), m["polished"], col, door,
            bev=(0.002, 2, 30))
        add(f"HingeArm_{i}", local(L.box_bm(0.04, 0.012, 0.03, (hx + 0.022, y0 - 0.022, z))), m["polished"], col, door,
            bev=(0.004, 2))
        if lod == 0:
            add(f"HingePinCap_{i}", local(L.cylinder_bm(0.0075, 0.004, 16, (hx, y0 - 0.02, z + 0.027))), m["polished"],
                col, door)
            for j, sz in enumerate((-0.022, 0.022)):
                screw(f"HingeScrew_{i}{j}", hx - 0.004, y0 - 0.0225, z + sz, col, root, m, r=0.0035)


def build_drum(m, col, root):
    y1, y2 = FRONT + 0.085, FRONT + 0.6
    # Folded rubber bellows between the collar and the drum mouth.
    bellows = [(COLLAR_R - 0.044, FRONT + 0.016), (0.236, FRONT + 0.022), (0.246, FRONT + 0.032), (0.232, FRONT + 0.042),
               (0.242, FRONT + 0.052), (0.228, FRONT + 0.062), (0.236, FRONT + 0.072), (DRUM_R - 0.01, FRONT + 0.08)]
    add("Bellows", L.revolve_bm(bellows, 64, False, (0, 0, DOOR_Z)), m["rubber"], col, root, smooth=55)
    add("DrumMouth", L.revolve_bm([(0.2, FRONT + 0.08), (DRUM_R, FRONT + 0.085)], 64, False, (0, 0, DOOR_Z)),
        m["steel"], col, root, smooth=60, uv="box")
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


STEEL_GRIME = dict(seed=17, floor=0.0, floor_band=0.45, floor_dark=0.5, stain=0.32, stain_scale=0.2, drip=0.25)


def sticker(name, w, h, x, z, mat, col, root, lines=(), size=0.007, ink=None, y_off=0.0, rot=0.0, header=None):
    """A flat vinyl sticker on the front panel with a few lines of text."""
    y = FRONT - 0.0145 - 0.0015 - y_off      # >= 1.5 mm off the panel (no z-fighting)
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
    return o


def build_details(m, col, root):
    """Everything that says real people use and service this machine."""
    # How-to-use instructions on the right of the door.
    # Kept clear of the door latch (z 0.52-0.6) on the right of the opening.
    sticker("HowTo", 0.075, 0.2, 0.33, 0.8, m["sticker"], col, root, header="HOW TO USE",
            lines=["1 LOAD CLOTHES", "  DO NOT OVERLOAD", "2 SOAP IN TOP", "  DISPENSER", "3 CLOSE DOOR",
                   "4 SELECT TEMP", "5 TAP KEY/CARD", "6 PRESS START", "", "REMOVE CLOTHES", "PROMPTLY"],
            size=0.0048, ink=m["ink"])
    # Caution label, lower left.
    y = FRONT - 0.0145 - 0.0015
    tri = bmesh.new()
    v = [tri.verts.new((-0.335, y, 0.28)), tri.verts.new((-0.285, y, 0.28)), tri.verts.new((-0.31, y, 0.323))]
    tri.faces.new(v)
    add("CautionTri", tri, m["sticker_yellow"], col, root)
    L.text_mesh("CautionMark", "!", 0.026, m["ink"], col, root, bold=True, location=(-0.31, y - 0.0012, 0.293))
    sticker("Caution", 0.08, 0.05, -0.31, 0.24, m["sticker_yellow"], col, root, header="CAUTION",
            lines=["DO NOT OPEN", "DOOR WHILE", "RUNNING"], size=0.0045, ink=m["ink"])
    # Price sticker, top left of the front.
    sticker("Price", 0.11, 0.045, -0.24, 0.94, m["sticker_red"], col, root, header="WASH  $4.50",
            lines=["HOT / WARM / COLD"], size=0.0065, ink=m["ink_white"], rot=1.5)
    sticker("NoDyes", 0.07, 0.03, 0.31, 0.38, m["sticker"], col, root, header="NO DYES",
            lines=["NO TINTS"], size=0.0055, ink=m["sticker_red"])
    # Room-key card sticker on the reader side of the panel.
    sticker("TapKey", 0.07, 0.035, 0.31, 0.948, m["sticker_blue"], col, root, header="TAP KEY",
            lines=["▲ READER"], size=0.006, ink=m["ink_white"])
    # Rating plate, key lock on the service panel, leftover tape from an old note.
    add("SerialPlate", L.box_bm(0.07, 0.0012, 0.035, (0.29, y - 0.0006, 0.1)), m["plate"], col, root)
    for i, t in enumerate(["MODEL WX450", "SN 2610-0447", "208-240V 60Hz"]):
        L.text_mesh(f"Serial_{i}", t, 0.0042, m["ink"], col, root, location=(0.29, y - 0.0025, 0.11 - i * 0.008))
    add("KeyLock", L.cylinder_bm(0.012, 0.01, 24, (-0.3, y - 0.004, 0.09), axis="Y"), m["polished"], col, root,
        bev=(0.002, 2, 30))
    add("KeyHole", L.box_bm(0.0025, 0.002, 0.009, (-0.3, y - 0.0095, 0.09)), m["gap"], col, root)
    for i, (x, z, r) in enumerate(((-0.05, 0.965, 3.0), (0.12, 0.97, -2.0))):
        bm = L.box_bm(0.06, 0.0006, 0.014, (x, y + 0.0004, z))
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
                location=(-0.21, 0.04, zt + 0.0105), rotation=(0, 0, 0))
    for i, (x, w, ln) in enumerate(((-0.27, 0.03, 0.05), (-0.2, 0.018, 0.035), (-0.14, 0.04, 0.025))):
        add(f"Residue_{i}", L.rounded_plate_bm(w, ln, w * 0.4, 0.0008, (x, -0.02 - ln / 2, zt + 0.0015), 4),
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


def build_lod2(m, col, root):
    """Far stand-in: cabinet, control face with LED, door disc and handle (~300 tris)."""
    add("Cabinet", L.box_bm(W, D, H, (0, 0, H / 2)), m["steel"], col, root, uv="box")
    add("Face", L.box_bm(W - 0.03, 0.004, 0.2, (0, FRONT + LEAN / 2 - 0.004, (H + Z_PANEL) / 2)), m["panel"], col,
        root)
    add("Door", L.cylinder_bm(TRIM_R, 0.03, 20, (0, FRONT - 0.03, DOOR_Z), axis="Y"), m["polished"], col, root)
    add("Glass", L.cylinder_bm(0.19, 0.004, 20, (0, FRONT - 0.047, DOOR_Z), axis="Y"), m["gap"], col, root)
    add("Handle", L.box_bm(0.27, 0.03, 0.034, (0.16, FRONT - 0.065, DOOR_Z)), m["panel"], col, root)


def build(lod=0):
    """lod=0: full detail. lod=1: distant version (same silhouette, door and
    screen; no screws, print, stickers, drum internals) for Unity's LODGroup."""
    name = NAME if lod == 0 else f"{NAME}_LOD{lod}"
    L.clear_collection(name)
    col = L.collection(name)
    col.hide_viewport = False
    col.hide_render = False
    root = L.root_empty(name, col)
    m = materials()
    if lod == 2:
        build_lod2(m, col, root)
        return _tris(col)
    build_cabinet(m, col, root, lod)
    if lod == 0:
        build_controls(m, col, root)
    else:
        lodface(m, col, root)
    build_door(m, col, root, lod)
    if lod == 0:
        build_drum(m, col, root)
        build_details(m, col, root)
    else:
        bm = L.cylinder_bm(DRUM_R, 0.3, 24, (0, FRONT + 0.25, DOOR_Z), axis="Y", caps=True)
        add("DrumDark", bm, m["gap"], col, root)
    for obj in col.all_objects:
        if obj.name.split(".")[0] in ("Cabinet", "FrontPanel", "ControlHousing", "KickPanel", "DoorCollar"):
            L.grime(obj, **STEEL_GRIME)
    return _tris(col)


def lodface(m, col, root):
    tilt = math.atan2(LEAN, H - Z_PANEL)
    frame = L.root_empty("ControlFace", col)
    frame.parent = root
    frame.location = (0, FRONT + LEAN / 2 - 0.001, (H + Z_PANEL) / 2)
    frame.rotation_euler = (-tilt, 0, 0)
    add("Face", L.box_bm(W - 0.03, 0.004, H - Z_PANEL - 0.03, (0, -0.002, 0)), m["panel"], col, frame)
    add("LEDWindow", L.box_bm(0.15, 0.002, 0.06, (-0.21, -0.0055, 0.03)), m["led"], col, frame)


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
