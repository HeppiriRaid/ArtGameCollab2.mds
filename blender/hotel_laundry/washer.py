"""Commercial washer-extractor (hotel laundry hero prop).

~0.74 W x 0.80 D x 1.27 H m, front faces -Y, origin at floor centre.
Brand name is fictional ("AQUALUX").
"""
import importlib
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals()
                else os.path.expanduser("~/Documents/GitHub/ArtGameCollab2.mds/blender/hotel_laundry"))
import laundry_lib as L  # noqa: E402
importlib.reload(L)

NAME = "WasherExtractor"

# Main dimensions
W, D = 0.74, 0.80
Z_PLINTH, Z_BODY, Z_TOP = 0.04, 0.12, 1.00   # plinth bottom, body bottom, body top
Z_HOUSING = 1.27                               # control housing top
FRONT = -D / 2                                 # body front plane (y)
PLATE_T = 0.012
Y_PLATE = FRONT - PLATE_T                      # front face of the steel front plate
DOOR_Z = 0.56
HOLE_R = 0.195
TILT = math.atan2(0.06, Z_HOUSING - Z_TOP)     # control fascia leans back 0.06 m


def materials():
    return {
        "steel": L.material("Steel_Brushed", metallic=1.0, tex="steel_brushed", normal_strength=0.6),
        "chrome": L.material("Chrome", base=(0.92, 0.92, 0.93), metallic=1.0, roughness=0.07),
        "drum": L.material("Drum_Perforated", metallic=1.0, tex="drum_perforated", normal_strength=1.0),
        "tub": L.material("Tub_Dark", base=(0.05, 0.05, 0.055), metallic=0.9, roughness=0.45),
        "graphite": L.material("Plastic_Graphite", base=(0.035, 0.037, 0.04), tex="plastic_matte",
                               normal_strength=0.4),
        "grey": L.material("Plastic_LightGrey", base=(0.55, 0.56, 0.57), tex="plastic_matte",
                           normal_strength=0.4),
        "rubber": L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5),
        "glass": L.material("Glass_Door", base=(0.12, 0.15, 0.15), roughness=0.02, alpha=0.12, ior=1.52),
        "screen": L.material("Display_Glass", base=(0.005, 0.006, 0.008), roughness=0.05, coat=1.0),
        "lcd": L.material("Display_Text", base=(0.2, 0.9, 1.0), emission=(0.25, 0.85, 1.0),
                          emission_strength=6.0),
        "white": L.material("Print_White", base=(0.85, 0.86, 0.87), roughness=0.4),
        "black": L.material("Print_Black", base=(0.01, 0.01, 0.01), roughness=0.5),
        "btn": L.material("Button_White", base=(0.82, 0.83, 0.84), roughness=0.35),
        "start": L.material("Button_Green", base=(0.05, 0.55, 0.15), roughness=0.3,
                            emission=(0.1, 1.0, 0.25), emission_strength=1.5),
        "red": L.material("Button_Red", base=(0.7, 0.03, 0.02), roughness=0.25, coat=0.6),
        "yellow": L.material("Label_Yellow", base=(0.95, 0.72, 0.02), roughness=0.4),
        "label": L.material("Label_Silver", base=(0.75, 0.76, 0.77), metallic=0.8, roughness=0.3),
        "hot": L.material("Ring_Red", base=(0.75, 0.05, 0.03), roughness=0.4),
        "cold": L.material("Ring_Blue", base=(0.03, 0.2, 0.75), roughness=0.4),
    }


def add(name, bm, mat, col, parent, bev=None, uv=None, smooth=35.0):
    obj = L.link(L.mesh_object(name, bm, mat, smooth), col, parent)
    if uv == "box":
        L.box_uv(obj)
    if bev:
        L.bevel(obj, *bev)
        L.weighted_normals(obj)
    return obj


def build_cabinet(m, col, root):
    # Main body: open at the front (the front plate closes it) so the drum is visible.
    add("Body", L.box_bm(W, D, Z_TOP - Z_BODY, (0, 0, (Z_TOP + Z_BODY) / 2), skip=("-y",)),
        m["steel"], col, root, bev=(0.012, 4), uv="box")

    # Control housing with a fascia leaning back.
    bm = L.box_bm(W, D, Z_HOUSING - Z_TOP, (0, 0, (Z_HOUSING + Z_TOP) / 2))
    for v in bm.verts:
        if v.co.z > Z_TOP + 0.01 and v.co.y < 0:
            v.co.y += 0.06
    add("ControlHousing", bm, m["steel"], col, root, bev=(0.012, 4), uv="box")

    # Front plate with the porthole opening.
    z0, z1 = Z_BODY + 0.03, Z_TOP - 0.03
    plate = add("FrontPlate", L.box_bm(W - 0.03, PLATE_T, z1 - z0, (0, FRONT - PLATE_T / 2, (z0 + z1) / 2)),
                m["steel"], col, root)
    L.boolean_cut(plate, L.cylinder_bm(HOLE_R, 0.1, 96, (0, FRONT, DOOR_Z), axis="Y"))
    L.box_uv(plate)
    L.bevel(plate, 0.004, 3)
    L.weighted_normals(plate)

    # Recessed plinth with vent slots and a toe kick shadow line.
    add("Plinth", L.box_bm(W - 0.04, D - 0.06, Z_BODY - Z_PLINTH, (0, 0.01, (Z_BODY + Z_PLINTH) / 2)),
        m["graphite"], col, root, bev=(0.004, 2), uv="box")
    for i in range(14):
        x = -0.26 + i * 0.04
        add(f"Vent_{i:02d}", L.box_bm(0.022, 0.006, 0.035, (x, FRONT + 0.028, 0.08)),
            m["black"], col, root, bev=(0.002, 2))

    # Front plate screws.
    for i, (x, z) in enumerate([(-0.33, z0 + 0.025), (0.33, z0 + 0.025), (-0.33, z1 - 0.025), (0.33, z1 - 0.025)]):
        head = add(f"Screw_{i}", L.cylinder_bm(0.0065, 0.004, 24, (x, Y_PLATE - 0.002, z), axis="Y"),
                   m["chrome"], col, root, bev=(0.0015, 2, 30))
        add(f"ScrewSlot_{i}a", L.box_bm(0.008, 0.0012, 0.0012, (x, Y_PLATE - 0.0041, z)), m["black"], col, head.parent)
        add(f"ScrewSlot_{i}b", L.box_bm(0.0012, 0.0012, 0.008, (x, Y_PLATE - 0.0041, z)), m["black"], col, head.parent)

    # Leveling feet: rubber pad, threaded stem, hex nut.
    for i, (x, y) in enumerate([(-0.3, -0.33), (0.3, -0.33), (-0.3, 0.33), (0.3, 0.33)]):
        add(f"FootPad_{i}", L.cylinder_bm(0.032, 0.012, 32, (x, y, 0.006)), m["rubber"], col, root,
            bev=(0.003, 2, 30))
        add(f"FootStem_{i}", L.cylinder_bm(0.009, 0.03, 16, (x, y, 0.027)), m["chrome"], col, root)
        add(f"FootNut_{i}", L.cylinder_bm(0.017, 0.008, 6, (x, y, 0.036)), m["chrome"], col, root,
            bev=(0.0015, 2, 30))

    # Detergent dispenser lid on the top, front-left, with hinge and label.
    zt = Z_HOUSING
    add("DispenserLid", L.box_bm(0.26, 0.14, 0.012, (-0.18, -0.2, zt + 0.004)), m["grey"], col, root,
        bev=(0.004, 3), uv="box")
    add("DispenserHinge", L.cylinder_bm(0.006, 0.24, 24, (-0.18, -0.127, zt + 0.006), axis="X"),
        m["chrome"], col, root)
    L.text_mesh("DispenserText", "DETERGENT  I   II   III   IV", 0.012, m["black"], col, root,
                location=(-0.18, -0.2, zt + 0.0105), rotation=(0, 0, 0))

    # Rear service connections: hot/cold inlets, drain, chemical dosing ports.
    yb = D / 2
    for i, (x, ring) in enumerate([(-0.22, "hot"), (-0.14, "cold")]):
        add(f"Inlet_{i}", L.cylinder_bm(0.016, 0.06, 32, (x, yb + 0.03, 1.15), axis="Y"),
            m["chrome"], col, root, bev=(0.002, 2, 30))
        add(f"InletRing_{i}", L.cylinder_bm(0.019, 0.01, 32, (x, yb + 0.01, 1.15), axis="Y"),
            m[ring], col, root)
    add("Drain", L.cylinder_bm(0.038, 0.08, 32, (0.2, yb + 0.04, 0.2), axis="Y"),
        m["graphite"], col, root, bev=(0.003, 2, 30))
    for i in range(5):
        add(f"DosingPort_{i}", L.cylinder_bm(0.006, 0.03, 16, (0.05 + i * 0.03, yb + 0.015, 1.18), axis="Y"),
            m["grey"], col, root)

    # Data plate on the right side.
    add("DataPlate", L.box_bm(0.0015, 0.14, 0.08, (W / 2 + 0.001, 0.2, 0.9)), m["label"], col, root,
        bev=(0.002, 2))
    lines = ["AQUALUX PRO 18", "WASHER-EXTRACTOR", "MODEL WX18-H  SN 26A0417", "400V 3N~ 50Hz  9.5kW", "IPX4   18 kg DRY LINEN"]
    for i, t in enumerate(lines):
        L.text_mesh(f"DataPlateText_{i}", t, 0.0075 if i else 0.011, m["black"], col, root, bold=(i == 0),
                    location=(W / 2 + 0.0019, 0.2, 0.925 - i * 0.013), rotation=(math.radians(90), 0, math.radians(90)))


def build_door(m, col, root):
    y0 = Y_PLATE
    center = (0, 0, DOOR_Z)
    door = L.root_empty("Door", col)
    door.parent = root
    # Door hinges on the left; the empty sits on the hinge axis so it can swing in Unity.
    door.location = (-0.30, y0 - 0.03, DOOR_Z)
    door.empty_display_size = 0.05

    def local(bm):
        bmesh.ops.translate(bm, vec=Vector((0.30, -(y0 - 0.03), -DOOR_Z)), verts=bm.verts)
        return bm

    ring = [(0.183, -0.004), (0.188, -0.03), (0.2, -0.05), (0.225, -0.062), (0.258, -0.058),
            (0.276, -0.042), (0.283, -0.02), (0.281, -0.006), (0.272, 0.0), (0.19, 0.0)]
    add("DoorRing", local(L.revolve_bm([(r, y0 + y) for r, y in ring], 96, True, center)),
        m["chrome"], col, door, smooth=50)
    inner = [(0.192, -0.006), (0.192, -0.05), (0.198, -0.052), (0.198, -0.004)]
    add("DoorRingInner", local(L.revolve_bm([(r, y0 + y) for r, y in inner], 96, True, center)),
        m["graphite"], col, door, smooth=50)
    glass = [(0.0, 0.07)] + [(0.192 * t, 0.07 - 0.112 * t ** 2) for t in (0.2, 0.4, 0.6, 0.75, 0.88, 1.0)]
    add("DoorGlass", local(L.revolve_bm([(r, y0 + y) for r, y in glass], 96, False, center)),
        m["glass"], col, door, smooth=80)

    # Hinge block and lever handle.
    add("HingeBlock", L.box_bm(0.07, 0.05, 0.16, (-0.30, y0 - 0.025, DOOR_Z)), m["steel"], col, root,
        bev=(0.008, 4), uv="box")
    for z in (DOOR_Z - 0.05, DOOR_Z + 0.05):
        add(f"HingePin_{z:.2f}", local(L.cylinder_bm(0.012, 0.035, 32, (-0.30, y0 - 0.03, z))),
            m["chrome"], col, door, bev=(0.002, 2, 30))
    bm = L.box_bm(0.03, 0.035, 0.13, (0.285, y0 - 0.05, DOOR_Z))
    add("Handle", local(bm), m["chrome"], col, door, bev=(0.012, 5))
    add("HandleGrip", local(L.box_bm(0.022, 0.012, 0.09, (0.29, y0 - 0.071, DOOR_Z))), m["graphite"], col,
        door, bev=(0.005, 3))


def build_drum(m, col, root):
    y0 = FRONT
    gasket = [(HOLE_R + 0.004, -0.004), (HOLE_R - 0.012, -0.012), (HOLE_R - 0.022, 0.0),
              (HOLE_R - 0.018, 0.03), (HOLE_R - 0.006, 0.05), (HOLE_R + 0.004, 0.06)]
    add("Gasket", L.revolve_bm([(r, y0 + y) for r, y in gasket], 96, False, (0, 0, DOOR_Z)),
        m["rubber"], col, root, smooth=60)

    r, y1, y2 = HOLE_R + 0.01, y0 + 0.06, y0 + 0.5
    bm = L.cylinder_bm(r, y2 - y1, 96, (0, (y1 + y2) / 2, DOOR_Z), axis="Y", caps=False)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)      # visible from inside
    drum = add("Drum", bm, m["drum"], col, root, smooth=60)
    L.cylinder_uv(drum, "Y", texel=0.12, radius=r)
    # cylinder_uv works in object space; the drum axis is at x=0, z=DOOR_Z.
    me = drum.data
    uv = me.uv_layers["UVMap"]
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a = math.atan2(co.z - DOOR_Z, co.x)
            uv.data[li].uv = (a * r / 0.12, co.y / 0.12)
    # fix the seam: faces crossing +-pi
    for poly in me.polygons:
        us = [uv.data[li].uv[0] for li in poly.loop_indices]
        if max(us) - min(us) > math.pi * r / 0.12:
            for li in poly.loop_indices:
                if uv.data[li].uv[0] < 0:
                    uv.data[li].uv[0] += 2 * math.pi * r / 0.12

    back = add("DrumBack", L.cylinder_bm(r, 0.004, 96, (0, y2, DOOR_Z), axis="Y"), m["drum"], col, root)
    L.box_uv(back, texel=0.12)
    add("DrumHub", L.cylinder_bm(0.05, 0.02, 48, (0, y2 - 0.01, DOOR_Z), axis="Y"), m["steel"], col, root,
        bev=(0.004, 3, 30), uv="box")
    for i in range(3):
        a = math.radians(90 + 120 * i)
        bm = L.box_bm(0.045, y2 - y1 - 0.02, 0.04, (0, (y1 + y2) / 2, 0))
        bmesh.ops.transform(bm, matrix=Matrix.Translation((math.cos(a) * (r - 0.018), 0,
                                                            DOOR_Z + math.sin(a) * (r - 0.018)))
                            @ Matrix.Rotation(-a + math.radians(90), 4, "Y"), verts=bm.verts)
        add(f"Lifter_{i}", bm, m["steel"], col, root, bev=(0.012, 4), uv="box")
    add("Tub", L.cylinder_bm(r + 0.02, 0.56, 96, (0, y0 + 0.33, DOOR_Z), axis="Y", caps=False),
        m["tub"], col, root)


def build_panel(m, col, root):
    """Control fascia elements, laid out in the fascia's own tilted frame."""
    frame = L.root_empty("ControlPanel", col)
    frame.parent = root
    zc = (Z_TOP + Z_HOUSING) / 2
    frame.location = (0, FRONT + 0.03 - 0.0005, zc)
    frame.rotation_euler = (-TILT, 0, 0)
    frame.empty_display_size = 0.05

    def at(x, z, y=0.0):
        return (x, y, z)

    add("Fascia", L.box_bm(W - 0.05, 0.006, 0.2, at(0, 0, -0.003)), m["graphite"], col, frame,
        bev=(0.004, 3), uv="box")
    L.text_mesh("Brand", "AQUALUX", 0.03, m["white"], col, frame, bold=True,
                location=at(-0.25, 0.045, -0.0065), align="CENTER")
    L.text_mesh("BrandSub", "PRO 18  WASHER-EXTRACTOR", 0.0095, m["white"], col, frame,
                location=at(-0.25, 0.017, -0.0065))

    # Display window with live-looking readout.
    add("DisplayBezel", L.box_bm(0.19, 0.006, 0.085, at(-0.02, 0.03, -0.007)), m["black"], col, frame,
        bev=(0.004, 3))
    add("DisplayGlass", L.box_bm(0.17, 0.002, 0.066, at(-0.02, 0.03, -0.0105)), m["screen"], col, frame,
        bev=(0.002, 2))
    L.text_mesh("DisplayProgram", "TOWELS  60°C", 0.015, m["lcd"], col, frame, bold=True,
                location=at(-0.02, 0.043, -0.0117))
    L.text_mesh("DisplayTime", "0:42", 0.026, m["lcd"], col, frame, bold=True,
                location=at(-0.035, 0.015, -0.0117))
    L.text_mesh("DisplaySpin", "1000 rpm", 0.008, m["lcd"], col, frame,
                location=at(0.035, 0.012, -0.0117))

    # Function buttons and start.
    labels = ["PRE", "EXTRA", "TEMP"]
    for i, lab in enumerate(labels):
        x = -0.09 + i * 0.045
        add(f"Button_{lab}", L.cylinder_bm(0.012, 0.008, 40, at(x, -0.05, -0.008), axis="Y"),
            m["btn"], col, frame, bev=(0.003, 3, 30))
        L.text_mesh(f"ButtonLabel_{lab}", lab, 0.0065, m["white"], col, frame,
                    location=at(x, -0.074, -0.0065))
    add("Button_START", L.cylinder_bm(0.016, 0.01, 48, at(0.055, -0.05, -0.009), axis="Y"),
        m["start"], col, frame, bev=(0.004, 3, 30))
    L.text_mesh("ButtonLabel_START", "START", 0.0075, m["white"], col, frame, bold=True,
                location=at(0.055, -0.078, -0.0065))

    # Program selector knob with knurled grip and pointer.
    kx, kz = 0.16, 0.0
    add("KnobSkirt", L.cylinder_bm(0.048, 0.006, 64, at(kx, kz, -0.008), axis="Y"), m["chrome"], col, frame,
        bev=(0.002, 2, 30))
    knob = add("Knob", L.cylinder_bm(0.034, 0.028, 48, at(kx, kz, -0.025), axis="Y"), m["graphite"], col,
               frame, bev=(0.004, 3, 30))
    for i in range(24):
        a = 2 * math.pi * i / 24
        bm = L.box_bm(0.004, 0.022, 0.004, (kx + math.cos(a) * 0.0345, -0.025, kz + math.sin(a) * 0.0345))
        add(f"KnobRib_{i:02d}", bm, m["graphite"], col, frame)
    add("KnobPointer", L.box_bm(0.004, 0.002, 0.022, at(kx, kz + 0.018, -0.0395)), m["white"], col, frame)
    progs = ["COTTON", "TOWELS", "LINEN", "MIXED", "DELICATE", "WOOL", "RINSE", "SPIN"]
    for i, p in enumerate(progs):
        a = math.radians(160 - i * (140 / (len(progs) - 1)))
        L.text_mesh(f"Program_{p}", p, 0.0062, m["white"], col, frame,
                    location=at(kx + math.cos(a) * 0.066, kz + math.sin(a) * 0.066, -0.0065))

    # Emergency stop: yellow collar and red mushroom head.
    ex = 0.29
    add("EStopCollar", L.cylinder_bm(0.034, 0.004, 64, at(ex, 0.0, -0.008), axis="Y"), m["yellow"], col,
        frame, bev=(0.0015, 2, 30))
    add("EStopBody", L.cylinder_bm(0.016, 0.018, 48, at(ex, 0.0, -0.018), axis="Y"), m["black"], col, frame)
    head = [(0.0, -0.046), (0.012, -0.0455), (0.02, -0.043), (0.024, -0.037), (0.025, -0.03), (0.0, -0.03)]
    add("EStopHead", L.revolve_bm(head, 64, True, at(ex, 0.0)), m["red"], col, frame, smooth=60)
    L.text_mesh("EStopText", "EMERGENCY STOP", 0.0048, m["black"], col, frame, bold=True,
                location=at(ex, -0.028, -0.0103))


def build_labels(m, col, root):
    # Hot-glass warning sticker, top right of the front plate.
    x, z, y = 0.25, 0.9, Y_PLATE - 0.0004
    bm = bmesh.new()
    s = 0.03
    verts = [bm.verts.new((x - s, y, z - s * 0.85)), bm.verts.new((x + s, y, z - s * 0.85)),
             bm.verts.new((x, y, z + s * 0.9))]
    bm.faces.new(verts)
    bm.normal_update()
    add("WarnTriangle", bm, m["yellow"], col, root)
    L.text_mesh("WarnMark", "!", 0.032, m["black"], col, root, bold=True, location=(x, y - 0.0004, z - 0.006))
    L.text_mesh("WarnText", "CAUTION  HOT GLASS", 0.0085, m["black"], col, root, bold=True,
                location=(x, y - 0.0004, z - 0.045))


def lookdev():
    """Studio floor, HDRI and camera for preview renders (not exported)."""
    col = L.collection("_LookDev")
    L.clear_collection("_LookDev")
    floor = L.link(L.mesh_object("Floor", L.box_bm(6, 6, 0.01, (0, 0, -0.005)),
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
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene = bpy.context.scene
    scene.world = world

    cam_data = bpy.data.cameras.get("LookDevCam") or bpy.data.cameras.new("LookDevCam")
    cam_data.lens = 50
    cam = L.link(bpy.data.objects.new("LookDevCam", cam_data), col)
    cam.location = (1.9, -2.6, 1.35)
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
    return floor


def build():
    L.clear_collection(NAME)
    col = L.collection(NAME)
    root = L.root_empty(NAME, col)
    m = materials()
    build_cabinet(m, col, root)
    build_door(m, col, root)
    build_drum(m, col, root)
    build_panel(m, col, root)
    build_labels(m, col, root)
    lookdev()
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for obj in col.all_objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(dg).data
            ev.calc_loop_triangles()
            tris += len(ev.loop_triangles)
    return {"objects": len(col.all_objects), "triangles": tris}


if __name__ == "__main__":
    build()
