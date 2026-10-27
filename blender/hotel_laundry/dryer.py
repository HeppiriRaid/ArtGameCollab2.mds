"""Commercial tumble dryer, following the Primus DX16 spec sheet
(docs/references/dryer.md): 1625 H x 800 W x ~960 D mm body, 762 mm drum,
black round door hinged on the right, lint drawer bar, touchscreen pod, and a
rear exhaust duct that rises to the ceiling. Front faces -Y, origin at floor.
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

NAME = "TumbleDryer"
W, D, H = 0.8, 0.96, 1.625
FRONT = -D / 2
DOOR_Z = 0.98
DOOR_R = 0.34          # outer radius of the black door
GLASS_R = 0.26
DRUM_R = 0.381
LINT_Z = 0.57
CEILING = 3.2


def materials():
    return {
        "steel": L.material("Steel_Brushed", metallic=1.0, tex="steel_brushed", normal_strength=0.22),
        "door": L.material("Paint_Black", base=(0.015, 0.015, 0.017), metallic=0.3, tex="paint_powder",
                           normal_strength=0.3, coat=0.4),
        "galv": L.material("Drum_Galvanized", base=(0.6, 0.61, 0.6), metallic=1.0, tex="drum_perforated",
                           normal_strength=1.0),
        "glass": L.material("Glass_Door", base=(0.12, 0.15, 0.15), roughness=0.02, alpha=0.12, ior=1.52),
        "graphite": L.material("Plastic_Graphite", base=(0.03, 0.032, 0.035), tex="plastic_matte",
                               normal_strength=0.4, coat=0.4),
        "bezel": L.material("Screen_Bezel", base=(0.008, 0.008, 0.01), roughness=0.08, coat=1.0),
        "ui_bg": L.material("UI_DryerBg", base=(0.08, 0.09, 0.12), emission=(0.08, 0.09, 0.12),
                            emission_strength=0.5),
        "ui_text": L.material("UI_DryerText", base=(0.9, 0.55, 0.15), emission=(1.0, 0.55, 0.12),
                              emission_strength=1.5),
        "badge": L.material("Badge_Blue", base=(0.03, 0.12, 0.32), metallic=0.4, roughness=0.25, coat=1.0),
        "white": L.material("Print_White", base=(0.88, 0.89, 0.9), roughness=0.35),
        "rubber": L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5),
        "duct": L.material("Duct_Galvanized", base=(0.5, 0.51, 0.5), metallic=0.9, roughness=0.5,
                           vertex_color=True),
        "lint": L.material("Lint_Grey", base=(0.45, 0.43, 0.42), tex="towel", normal_strength=1.5),
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


def build(col, root, m):
    # Cabinet open at the front; stainless front panel with the drum opening.
    add("Cabinet", L.box_bm(W, D, H - 0.03, (0, 0, (H + 0.03) / 2), skip=("-y",)), m["steel"], col, root,
        bev=(0.008, 3), uv="box")
    panel = L.link(L.mesh_object("FrontPanel", L.box_bm(W - 0.004, 0.012, H - 0.035, (0, FRONT - 0.006,
                                                                                     (H + 0.035) / 2)),
                                 m["steel"]), col, root)
    L.boolean_cut(panel, L.cylinder_bm(GLASS_R + 0.02, 0.1, 96, (0, FRONT, DOOR_Z), axis="Y"))
    L.box_uv(panel)
    L.bevel(panel, 0.004, 2)
    L.weighted_normals(panel)
    L.triangulate(panel)
    # Panel seams: control band and lint drawer split lines.
    for i, z in enumerate((H - 0.17, LINT_Z + 0.06, 0.12)):
        add(f"Seam_{i}", L.box_bm(W - 0.01, 0.003, 0.004, (0, FRONT - 0.0125, z)), m["graphite"], col, root)
    add("Plinth", L.box_bm(W - 0.04, D - 0.04, 0.03, (0, 0, 0.015)), m["rubber"], col, root)

    # Control pod: angled black housing with a touchscreen.
    pod = L.rounded_plate_bm(0.24, 0.13, 0.015, 0.05, (0.06, FRONT - 0.012, H - 0.085), 6)
    for v in pod.verts:
        if v.co.y < FRONT - 0.03:
            v.co.y += (v.co.z - (H - 0.15)) * 0.25        # leans back toward the top
    add("ControlPod", pod, m["bezel"], col, root, bev=(0.004, 2))
    add("Screen", L.box_bm(0.17, 0.002, 0.09, (0.06, FRONT - 0.058, H - 0.083)), m["ui_bg"], col, root)
    ui = L.text_mesh("ScreenTime", "DRYING  38", 0.016, m["ui_text"], col, root, bold=True,
                     location=(0.06, FRONT - 0.0595, H - 0.075))
    L.text_mesh("ScreenTemp", "HIGH  75°C", 0.009, m["ui_text"], col, root,
                location=(0.06, FRONT - 0.0595, H - 0.1))
    for o in (bpy.data.objects["ControlPod"], bpy.data.objects["Screen"], ui,
              bpy.data.objects["ScreenTemp"]):
        o.rotation_euler.x += 0.0 if o.name == "ControlPod" else 0.0
    add("Badge", L.rounded_plate_bm(0.09, 0.024, 0.012, 0.003, (-0.25, FRONT - 0.012, H - 0.085), 8),
        m["badge"], col, root)
    L.text_mesh("BadgeText", "aqualux", 0.014, m["white"], col, root, bold=True,
                location=(-0.25, FRONT - 0.0155, H - 0.085))

    # Lint drawer bar handle across the full width.
    add("LintBar", L.rounded_plate_bm(W - 0.06, 0.04, 0.018, 0.03, (0, FRONT - 0.012, LINT_Z), 8),
        m["graphite"], col, root, bev=(0.004, 2))

    # Drum seen through the door: galvanised perforated cylinder with three lifters.
    y1, y2 = FRONT + 0.02, FRONT + 0.75
    bm = L.cylinder_bm(DRUM_R, y2 - y1, 96, (0, (y1 + y2) / 2, DOOR_Z), axis="Y", caps=False)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    drum = add("Drum", bm, m["galv"], col, root, smooth=60)
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
    back = add("DrumBack", L.cylinder_bm(DRUM_R, 0.004, 96, (0, y2, DOOR_Z), axis="Y"), m["galv"], col, root)
    L.box_uv(back, texel=tile)
    add("DrumLip", L.revolve_bm([(GLASS_R + 0.02, FRONT + 0.001), (DRUM_R, FRONT + 0.02)], 96, False,
                                (0, 0, DOOR_Z)), m["steel"], col, root, uv="box")
    for i in range(3):
        a = math.radians(30 + 120 * i)
        bm = L.box_bm(0.07, y2 - y1 - 0.04, 0.06, (0, (y1 + y2) / 2, 0))
        bmesh.ops.transform(bm, matrix=Matrix.Translation((math.cos(a) * (DRUM_R - 0.025), 0,
                                                            DOOR_Z + math.sin(a) * (DRUM_R - 0.025)))
                            @ Matrix.Rotation(-a + math.radians(90), 4, "Y"), verts=bm.verts)
        add(f"Lifter_{i}", bm, m["galv"], col, root, bev=(0.02, 3), uv="box")

    # Door: black ring, glass, gasket, handle; pivot on the right hinge.
    door = L.root_empty("Door", col)
    door.parent = root
    hx = DOOR_R - 0.005
    door.location = (hx, FRONT - 0.03, DOOR_Z)
    door.empty_display_size = 0.05

    def local(bm):
        bmesh.ops.translate(bm, vec=Vector((-hx, -(FRONT - 0.03), -DOOR_Z)), verts=bm.verts)
        return bm

    y0 = FRONT - 0.012
    ring = [(GLASS_R - 0.01, -0.004), (GLASS_R - 0.005, -0.03), (GLASS_R + 0.02, -0.045),
            (DOOR_R - 0.03, -0.05), (DOOR_R - 0.005, -0.04), (DOOR_R, -0.02), (DOOR_R - 0.004, -0.004),
            (GLASS_R, -0.004)]
    add("DoorRing", local(L.revolve_bm([(r, y0 + y) for r, y in ring], 96, True, (0, 0, DOOR_Z))), m["door"],
        col, door, smooth=55)
    glass = [(0.0, -0.03)] + [(GLASS_R * t, -0.03 + 0.02 * t ** 2) for t in (0.3, 0.6, 0.85, 1.0)]
    add("DoorGlass", local(L.revolve_bm([(r, y0 + y) for r, y in glass], 64, False, (0, 0, DOOR_Z))),
        m["glass"], col, door, smooth=85)
    gasket = [(GLASS_R - 0.012, -0.006), (GLASS_R - 0.004, 0.0), (GLASS_R + 0.01, 0.0), (GLASS_R + 0.012, -0.006)]
    add("DoorGasket", local(L.revolve_bm([(r, y0 + y) for r, y in gasket], 64, True, (0, 0, DOOR_Z))),
        m["rubber"], col, door, smooth=60)
    add("DoorHandle", local(L.rounded_plate_bm(0.035, 0.16, 0.015, 0.03,
                                                (-DOOR_R + 0.04, y0 - 0.045, DOOR_Z), 6)),
        m["graphite"], col, door, bev=(0.004, 2))
    for z in (DOOR_Z - 0.2, DOOR_Z + 0.2):
        add(f"Hinge_{z:.2f}", L.box_bm(0.03, 0.04, 0.07, (hx + 0.012, FRONT - 0.02, z)), m["door"], col, root,
            bev=(0.006, 2))

    # Exhaust: collar on the rear top, galvanised duct rising to the ceiling, with a band clamp.
    yd, zc = D / 2 - 0.15, H + 0.06
    add("ExhaustCollar", L.cylinder_bm(0.1, 0.12, 32, (0.2, yd, H + 0.06)), m["duct"], col, root,
        dirt=dict(seed=301, floor=-10, stain=0.4, stain_scale=0.3))
    add("ExhaustDuct", L.cylinder_bm(0.095, CEILING - H - 0.12, 32, (0.2, yd, (CEILING + H + 0.12) / 2), caps=False),
        m["duct"], col, root, dirt=dict(seed=302, floor=-10, stain=0.5, stain_scale=0.3, drip=0.4))
    add("DuctClamp", L.cylinder_bm(0.1, 0.03, 32, (0.2, yd, H + 0.5)), m["duct"], col, root,
        dirt=dict(seed=303, floor=-10, stain=0.3))
    # A tuft of lint escaping the drawer seam: the one bit of disorder.
    lint = L.box_bm(0.12, 0.01, 0.015, (-0.2, FRONT - 0.014, LINT_Z + 0.062))
    add("LintTuft", lint, m["lint"], col, root, bev=(0.005, 2), uv="box", texel=0.1)


def run():
    L.clear_collection(NAME)
    col = L.collection(NAME)
    root = L.root_empty(NAME, col)
    build(col, root, materials())
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for obj in col.all_objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(dg).data
            ev.calc_loop_triangles()
            tris += len(ev.loop_triangles)
    return {"objects": len(col.all_objects), "triangles": tris}
