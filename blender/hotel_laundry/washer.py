"""Commercial softmount washer-extractor (hotel laundry hero prop).

Proportions follow the Primus FX105 spec sheet (see docs/references/washer.md):
1245 H x 795 W x 795 D mm, door centre 648 mm, 180 mm control strip.
Front faces -Y, origin at floor centre. Brand is fictional ("AQUALUX").
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

NAME = "WasherExtractor"

W, D, H = 0.795, 0.795, 1.245
Z_FOOT = 0.048            # floor clearance under the cabinet
Z_STRIP = H - 0.18        # bottom of the stainless control strip
FRONT = -D / 2
PANEL_T = 0.015
Y_PANEL = FRONT - PANEL_T # outer face of the front panel
DOOR_Z = 0.648
SURROUND_R = 0.306        # dark recessed door surround (reaches down to ~342 mm)
OPEN_R = 0.205            # loading opening
DRUM_R = 0.31             # 620 mm drum
STRIP_LEAN = 0.03         # control strip leans back by this much at the top
TILT = math.atan2(STRIP_LEAN, H - Z_STRIP)


def materials():
    return {
        "paint": L.material("Paint_Anthracite", base=(0.052, 0.056, 0.062), metallic=0.35,
                            tex="paint_powder", normal_strength=0.35),
        "steel": L.material("Steel_Brushed", metallic=1.0, tex="steel_brushed", normal_strength=0.22),
        "chrome": L.material("Chrome", base=(0.92, 0.92, 0.93), metallic=1.0, roughness=0.07),
        "drum": L.material("Drum_Perforated", metallic=1.0, tex="drum_perforated", normal_strength=1.0),
        "tub": L.material("Tub_Dark", base=(0.06, 0.06, 0.065), metallic=0.9, roughness=0.4),
        "surround": L.material("Plastic_DoorSurround", base=(0.022, 0.024, 0.027), roughness=0.3,
                               tex="plastic_matte", normal_strength=0.3, coat=0.3),
        "ring": L.material("Plastic_DoorRing", base=(0.4, 0.42, 0.44), tex="plastic_matte",
                           normal_strength=0.3, coat=0.2),
        "graphite": L.material("Plastic_Graphite", base=(0.03, 0.032, 0.035), tex="plastic_matte",
                               normal_strength=0.4, coat=0.4),
        "base": L.material("Plastic_Base", base=(0.012, 0.012, 0.013), tex="plastic_matte", normal_strength=0.4),
        "rubber": L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5),
        "blue_gasket": L.material("Rubber_Blue", base=(0.02, 0.16, 0.5), tex="rubber", normal_strength=0.4),
        "glass": L.material("Glass_Door", base=(0.12, 0.15, 0.15), roughness=0.02, alpha=0.12, ior=1.52),
        "bezel": L.material("Screen_Bezel", base=(0.008, 0.008, 0.01), roughness=0.08, coat=1.0),
        "ui_bg": L.material("UI_Background", base=(0.86, 0.88, 0.91), roughness=0.1,
                            emission=(0.86, 0.88, 0.91), emission_strength=0.45),
        "ui_blue": L.material("UI_Blue", base=(0.04, 0.33, 0.78), roughness=0.1,
                              emission=(0.02, 0.2, 0.62), emission_strength=0.5),
        "ui_grey": L.material("UI_Grey", base=(0.72, 0.74, 0.77), roughness=0.1,
                              emission=(0.72, 0.74, 0.77), emission_strength=0.35),
        "ui_green": L.material("UI_Green", base=(0.1, 0.62, 0.3), roughness=0.1,
                               emission=(0.05, 0.45, 0.18), emission_strength=0.5),
        "ui_text": L.material("UI_TextDark", base=(0.06, 0.08, 0.12), roughness=0.2),
        "white": L.material("Print_White", base=(0.88, 0.89, 0.9), roughness=0.35),
        "black": L.material("Print_Black", base=(0.01, 0.01, 0.01), roughness=0.5),
        "badge": L.material("Badge_Blue", base=(0.03, 0.12, 0.32), metallic=0.4, roughness=0.25, coat=1.0),
        "red": L.material("Button_Red", base=(0.72, 0.03, 0.02), roughness=0.22, coat=0.8),
        "yellow": L.material("Label_Yellow", base=(0.95, 0.72, 0.02), roughness=0.35),
        "label": L.material("Label_Silver", base=(0.75, 0.76, 0.77), metallic=0.8, roughness=0.3),
        "hot": L.material("Ring_Red", base=(0.75, 0.05, 0.03), roughness=0.4),
        "cold": L.material("Ring_Blue", base=(0.03, 0.2, 0.75), roughness=0.4),
    }


def add(name, bm, mat, col, parent, bev=None, uv=None, smooth=35.0, tri=True):
    obj = L.link(L.mesh_object(name, bm, mat, smooth), col, parent)
    if uv == "box":
        L.box_uv(obj)
    if bev:
        L.bevel(obj, *bev)
        L.weighted_normals(obj)
    if tri:
        L.triangulate(obj)
    return obj


def lathe(profile, y0, center, segments=96):
    """Revolve a (radius, y-offset) profile around the door axis, offsets relative to y0."""
    return L.revolve_bm([(r, y0 + y) for r, y in profile], segments, True, center)


# ------------------------------------------------------------------ cabinet

def build_cabinet(m, col, root):
    # Painted cabinet shell, open at the front.
    add("Cabinet", L.box_bm(W, D, Z_STRIP - Z_FOOT, (0, 0, (Z_STRIP + Z_FOOT) / 2), skip=("-y",)),
        m["paint"], col, root, bev=(0.01, 4), uv="box")

    # Front panel with the big opening for the recessed door surround.
    panel = add("FrontPanel", L.box_bm(W - 0.004, PANEL_T, Z_STRIP - Z_FOOT - 0.006,
                                       (0, FRONT - PANEL_T / 2, (Z_STRIP + Z_FOOT) / 2)),
                m["paint"], col, root, tri=False)
    L.boolean_cut(panel, L.cylinder_bm(SURROUND_R, 0.1, 128, (0, FRONT, DOOR_Z), axis="Y"))
    L.box_uv(panel)
    L.bevel(panel, 0.005, 3)
    L.weighted_normals(panel)
    L.triangulate(panel)

    # Embossed rounded panels on both sides.
    for side, sx in (("L", -1), ("R", 1)):
        add(f"SideEmboss_{side}", L.rounded_plate_bm(0.5, 0.78, 0.05, 0.004,
                                                     (sx * W / 2, -0.03, 0.56), 10,
                                                     "-x" if sx < 0 else "+x"),
            m["paint"], col, root, bev=(0.002, 2), uv="box")

    # Recessed black base hiding the feet.
    add("Base", L.box_bm(W - 0.06, D - 0.06, Z_FOOT, (0, 0, Z_FOOT / 2)), m["base"], col, root,
        bev=(0.003, 2), uv="box")
    for i, (x, y) in enumerate([(-0.33, -0.33), (0.33, -0.33), (-0.33, 0.33), (0.33, 0.33)]):
        add(f"Foot_{i}", L.cylinder_bm(0.03, 0.012, 32, (x, y, 0.006)), m["rubber"], col, root,
            bev=(0.003, 2, 30))

    # Front panel fasteners along the bottom.
    for i, x in enumerate((-0.36, 0.36)):
        add(f"Screw_{i}", L.cylinder_bm(0.0055, 0.003, 24, (x, Y_PANEL - 0.0015, Z_FOOT + 0.025), axis="Y"),
            m["chrome"], col, root, bev=(0.0012, 2, 30))

    # Data plate on the right side, near the back.
    add("DataPlate", L.box_bm(0.0015, 0.13, 0.075, (W / 2 + 0.003, 0.32, 0.92)), m["label"], col, root,
        bev=(0.002, 2))
    lines = ["AQUALUX PRO 12", "WASHER-EXTRACTOR  WX105", "SN 26A0417   400V 3N~ 50Hz",
             "HEATING 7 kW   IPX4", "CAPACITY 12 kg  (1:9)"]
    for i, t in enumerate(lines):
        L.text_mesh(f"DataPlateText_{i}", t, 0.0068 if i else 0.0095, m["black"], col, root, bold=(i == 0),
                    location=(W / 2 + 0.0039, 0.32, 0.945 - i * 0.012),
                    rotation=(math.radians(90), 0, math.radians(90)))


def build_strip(m, col, root):
    """Stainless control strip with a lean-back front, plus its controls."""
    bm = L.box_bm(W, D, H - Z_STRIP, (0, 0, (H + Z_STRIP) / 2))
    for v in bm.verts:
        if v.co.z > Z_STRIP + 0.01 and v.co.y < 0:
            v.co.y += STRIP_LEAN
    add("ControlStrip", bm, m["steel"], col, root, bev=(0.008, 4), uv="box")

    frame = L.root_empty("ControlPanel", col)
    frame.parent = root
    frame.location = (0, FRONT + STRIP_LEAN / 2, (H + Z_STRIP) / 2)
    frame.rotation_euler = (-TILT, 0, 0)
    frame.empty_display_size = 0.05

    # Central stop: yellow collar, black body, red mushroom head.
    ex = -0.32
    add("StopCollar", L.cylinder_bm(0.032, 0.003, 64, (ex, -0.0015, 0.0), axis="Y"), m["yellow"], col, frame,
        bev=(0.001, 2, 30))
    add("StopBody", L.cylinder_bm(0.017, 0.016, 48, (ex, -0.01, 0.0), axis="Y"), m["black"], col, frame,
        bev=(0.002, 2, 30))
    head = [(0.0, -0.04), (0.012, -0.0395), (0.02, -0.037), (0.024, -0.031), (0.025, -0.024), (0.0, -0.024)]
    add("StopHead", L.revolve_bm(head, 64, True, (ex, 0.0, 0.0)), m["red"], col, frame, smooth=60)
    L.text_mesh("StopText", "STOP", 0.0065, m["black"], col, frame, bold=True, location=(ex, -0.0032, -0.024))

    # 7" touchscreen with a live-looking wash cycle UI.
    sx = -0.13
    add("ScreenBezel", L.rounded_plate_bm(0.185, 0.118, 0.008, 0.006, (sx, 0.0, 0.0), 6), m["bezel"],
        col, frame)
    sw, sh, y = 0.155, 0.087, -0.0064
    add("Screen", L.box_bm(sw, 0.0005, sh, (sx, y, 0.0)), m["ui_bg"], col, frame)
    y -= 0.0004
    add("UI_Header", L.box_bm(sw, 0.0004, 0.013, (sx, y, sh / 2 - 0.0065)), m["ui_blue"], col, frame)
    yt = y - 0.0003
    L.text_mesh("UI_HeaderText", "Washer 1  •  Running", 0.0058, m["white"], col, frame,
                location=(sx - 0.045, yt, sh / 2 - 0.0065))
    L.text_mesh("UI_Clock", "14:32", 0.0058, m["white"], col, frame, location=(sx + 0.064, yt, sh / 2 - 0.0065))
    L.text_mesh("UI_Program", "Hotel Towels  60°C", 0.0075, m["ui_text"], col, frame, bold=True,
                location=(sx - 0.03, y, 0.016))
    L.text_mesh("UI_Time", "42 min", 0.016, m["ui_text"], col, frame, bold=True,
                location=(sx - 0.035, y, -0.004))
    L.text_mesh("UI_Phase", "Main wash  •  12.0 kg", 0.0055, m["ui_text"], col, frame,
                location=(sx - 0.03, y, -0.02))
    add("UI_BarBack", L.box_bm(0.1, 0.0003, 0.005, (sx - 0.022, y, -0.031)), m["ui_grey"], col, frame)
    add("UI_BarFill", L.box_bm(0.058, 0.0003, 0.005, (sx - 0.043, y - 0.0002, -0.031)), m["ui_blue"], col, frame)
    add("UI_Button", L.cylinder_bm(0.017, 0.0004, 48, (sx + 0.05, y, -0.006), axis="Y"), m["ui_green"], col,
        frame)
    L.text_mesh("UI_ButtonText", "PAUSE", 0.0052, m["white"], col, frame, bold=True,
                location=(sx + 0.05, y - 0.0003, -0.006))

    # Brand badge on the right.
    add("Badge", L.rounded_plate_bm(0.1, 0.026, 0.013, 0.003, (0.28, 0.0, 0.03), 8), m["badge"], col, frame)
    L.text_mesh("BadgeText", "aqualux", 0.016, m["white"], col, frame, bold=True,
                location=(0.28, -0.0034, 0.03))
    L.text_mesh("ModelText", "PRO 12  •  WX105", 0.0075, m["white"], col, frame,
                location=(0.28, -0.0003, 0.005))

    # Soap hopper on the top, towards the back.
    zt = H
    add("SoapHopperLid", L.rounded_plate_bm(0.3, 0.2, 0.02, 0.008, (-0.17, 0.0, 0.0), 6), m["steel"], col,
        root, bev=(0.002, 2))
    lid = bpy.data.objects["SoapHopperLid"]
    lid.rotation_euler = (math.radians(-90), 0, 0)
    lid.location = (0, 0.18, zt)
    add("SoapHopperGrip", L.box_bm(0.08, 0.018, 0.01, (-0.17, 0.075, zt + 0.011)), m["graphite"], col, root,
        bev=(0.004, 3))
    add("SoapHopperHinge", L.cylinder_bm(0.006, 0.28, 24, (-0.17, 0.285, zt + 0.006), axis="X"), m["steel"],
        col, root, uv="box")


def build_door(m, col, root):
    y0 = Y_PANEL
    center = (0, 0, DOOR_Z)

    # Dark recessed surround pressed into the panel opening, sloping into the drum.
    surround = [(SURROUND_R + 0.002, -0.0005), (SURROUND_R - 0.004, 0.008), (SURROUND_R - 0.02, 0.016),
                (OPEN_R + 0.03, 0.02), (OPEN_R + 0.008, 0.026), (OPEN_R, 0.04), (OPEN_R, 0.075),
                (OPEN_R + 0.01, 0.075), (SURROUND_R + 0.002, 0.03)]
    add("DoorSurround", lathe(surround, y0, center, 128), m["surround"], col, root, smooth=60, uv=None)

    door = L.root_empty("Door", col)
    door.parent = root
    hinge_x = 0.27
    door.location = (hinge_x, y0 - 0.04, DOOR_Z)   # hinge axis on the right, so the door swings in Unity
    door.empty_display_size = 0.05

    def local(bm):
        bmesh.ops.translate(bm, vec=Vector((-hinge_x, -(y0 - 0.04), -DOOR_Z)), verts=bm.verts)
        return bm

    ring = [(0.176, -0.012), (0.18, -0.05), (0.192, -0.066), (0.214, -0.075), (0.236, -0.072),
            (0.25, -0.06), (0.255, -0.04), (0.253, -0.018), (0.244, -0.006), (0.18, -0.006)]
    add("DoorRing", local(lathe(ring, y0, center)), m["ring"], col, door, smooth=55)
    trim = [(0.168, -0.008), (0.168, -0.058), (0.178, -0.062), (0.179, -0.012)]
    add("DoorTrim", local(lathe(trim, y0, center)), m["chrome"], col, door, smooth=55)
    glass = [(0.0, 0.1)] + [(0.17 * t, 0.1 - 0.155 * t ** 2) for t in (0.2, 0.4, 0.6, 0.75, 0.88, 1.0)]
    add("DoorGlass", local(L.revolve_bm([(r, y0 + y) for r, y in glass], 96, False, center)),
        m["glass"], col, door, smooth=85)

    # Round knob handle on the left of the ring.
    knob = [(0.0, -0.112), (0.012, -0.111), (0.021, -0.106), (0.026, -0.098), (0.027, -0.09),
            (0.023, -0.082), (0.014, -0.078), (0.011, -0.07), (0.011, -0.06), (0.0, -0.06)]
    kx = -0.262
    bm = L.revolve_bm([(r, y0 + y) for r, y in knob], 48, True, (kx, 0, DOOR_Z))
    add("DoorKnob", local(bm), m["graphite"], col, door, smooth=60)
    add("DoorKnobArm", local(L.box_bm(0.03, 0.02, 0.034, (kx + 0.018, y0 - 0.065, DOOR_Z))), m["ring"], col,
        door, bev=(0.008, 4))

    # Hinge housing on the right, mostly hidden behind the ring.
    add("HingeHousing", L.rounded_plate_bm(0.05, 0.15, 0.015, 0.045, (hinge_x, y0, DOOR_Z), 6),
        m["graphite"], col, root, bev=(0.004, 3))


def build_drum(m, col, root):
    y0 = FRONT
    # Blue gasket lip at the opening (seen through the glass).
    lip = [(OPEN_R - 0.002, 0.04), (OPEN_R - 0.014, 0.046), (OPEN_R - 0.016, 0.06),
           (OPEN_R - 0.006, 0.072), (OPEN_R + 0.004, 0.075)]
    add("GasketLip", L.revolve_bm([(r, y0 + y) for r, y in lip], 96, False, (0, 0, DOOR_Z)),
        m["blue_gasket"], col, root, smooth=60)

    y1, y2 = y0 + 0.08, y0 + 0.66
    front = [(OPEN_R - 0.01, 0.075), (DRUM_R, 0.08)]
    add("DrumFront", L.revolve_bm([(r, y0 + y) for r, y in front], 96, False, (0, 0, DOOR_Z)),
        m["steel"], col, root, uv="box")
    bm = L.cylinder_bm(DRUM_R, y2 - y1, 128, (0, (y1 + y2) / 2, DOOR_Z), axis="Y", caps=False)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    drum = add("Drum", bm, m["drum"], col, root, smooth=60)
    me = drum.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    tile = 0.12
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
    back = add("DrumBack", L.cylinder_bm(DRUM_R, 0.004, 128, (0, y2, DOOR_Z), axis="Y"), m["drum"], col, root)
    L.box_uv(back, texel=tile)
    add("DrumHub", L.cylinder_bm(0.06, 0.02, 48, (0, y2 - 0.01, DOOR_Z), axis="Y"), m["steel"], col, root,
        bev=(0.004, 3, 30), uv="box")
    for i in range(3):
        a = math.radians(90 + 120 * i)
        bm = L.box_bm(0.06, y2 - y1 - 0.02, 0.05, (0, (y1 + y2) / 2, 0))
        bmesh.ops.transform(bm, matrix=Matrix.Translation((math.cos(a) * (DRUM_R - 0.022), 0,
                                                            DOOR_Z + math.sin(a) * (DRUM_R - 0.022)))
                            @ Matrix.Rotation(-a + math.radians(90), 4, "Y"), verts=bm.verts)
        add(f"Lifter_{i}", bm, m["steel"], col, root, bev=(0.016, 4), uv="box")


def build_rear(m, col, root):
    yb = D / 2
    for i, (x, ring) in enumerate([(-0.25, "hot"), (-0.17, "cold"), (-0.09, "cold")]):
        add(f"Inlet_{i}", L.cylinder_bm(0.016, 0.06, 32, (x, yb + 0.03, 1.12), axis="Y"),
            m["steel"], col, root, bev=(0.002, 2, 30), uv="box")
        add(f"InletRing_{i}", L.cylinder_bm(0.019, 0.01, 32, (x, yb + 0.01, 1.12), axis="Y"),
            m[ring], col, root)
    add("DrainValve", L.cylinder_bm(0.038, 0.09, 48, (0.22, yb + 0.045, 0.16), axis="Y"),
        m["graphite"], col, root, bev=(0.003, 2, 30))
    for i in range(5):
        add(f"SoapPort_{i}", L.cylinder_bm(0.006, 0.03, 16, (0.05 + i * 0.03, yb + 0.015, 0.98), axis="Y"),
            m["white"], col, root)
    add("MainSwitch", L.box_bm(0.06, 0.03, 0.06, (0.25, yb + 0.015, 1.12)), m["graphite"], col, root,
        bev=(0.004, 3))
    add("MainSwitchHandle", L.box_bm(0.012, 0.02, 0.04, (0.25, yb + 0.04, 1.12)), m["red"], col, root,
        bev=(0.003, 2))


def lookdev():
    """Studio floor, HDRI, key light and camera for preview renders (not exported)."""
    col = L.collection("_LookDev")
    L.clear_collection("_LookDev")
    L.link(L.mesh_object("Floor", L.box_bm(6, 6, 0.01, (0, 0, -0.005)),
                         L.material("LookDev_Floor", base=(0.18, 0.18, 0.19), roughness=0.35)), col)
    world = bpy.data.worlds.get("LookDev") or bpy.data.worlds.new("LookDev")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    hdri = os.path.expanduser("~/Documents/Blender/HotelLaundry/textures/hdri_lookdev.hdr")
    if os.path.exists(hdri):
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hdri, check_existing=True)
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene = bpy.context.scene
    scene.world = world

    cam_data = bpy.data.cameras.get("LookDevCam") or bpy.data.cameras.new("LookDevCam")
    cam_data.lens = 50
    cam = L.link(bpy.data.objects.new("LookDevCam", cam_data), col)
    cam.location = (1.95, -2.75, 1.45)
    target = Vector((0, 0, 0.66))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    key_data = bpy.data.lights.get("LookDevKey") or bpy.data.lights.new("LookDevKey", "AREA")
    key_data.energy = 250
    key_data.size = 1.5
    key = L.link(bpy.data.objects.new("LookDevKey", key_data), col)
    key.location = (-1.6, -1.8, 2.4)
    key.rotation_euler = (Vector((0, 0, 0.6)) - key.location).to_track_quat("-Z", "Y").to_euler()

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_raytracing = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def build():
    L.clear_collection(NAME)
    col = L.collection(NAME)
    root = L.root_empty(NAME, col)
    m = materials()
    build_cabinet(m, col, root)
    build_strip(m, col, root)
    build_door(m, col, root)
    build_drum(m, col, root)
    build_rear(m, col, root)
    lookdev()
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for obj in col.all_objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(dg).data
            ev.calc_loop_triangles()
            tris += len(ev.loop_triangles)
    return {"objects": len(col.all_objects), "triangles": tris}


def render_views(out_dir):
    """Hero 3/4 view plus a control-strip close-up, for comparing with references."""
    scene = bpy.context.scene
    cam = scene.camera
    shots = {
        "hero": ((1.95, -2.75, 1.45), (0, 0, 0.66), 50),
        "front": ((0.0, -3.2, 0.7), (0, 0, 0.64), 50),
        "panel": ((-0.25, -0.75, 1.28), (-0.12, 0, 1.15), 50),
    }
    paths = []
    for name, (loc, target, lens) in shots.items():
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        scene.render.filepath = os.path.join(out_dir, f"washer_{name}.png")
        bpy.ops.render.render(write_still=True)
        paths.append(scene.render.filepath)
    return paths
