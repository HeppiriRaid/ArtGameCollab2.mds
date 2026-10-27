"""Repeating laundry bay: the room shell of the infinite hotel laundry.

One bay is 24 m long (Y), 10 m wide (X), 3.2 m to the drop ceiling.
Bays chain along +Y: each bay owns the partition + double doors at y=+12, the
previous bay's partition closes y=-12. Washers stand on the -X wall facing +X,
dryers on the +X wall facing -X. Unity places machines and lights at the
exported empties (WasherSlot_##, DryerSlot_##, TrofferSlot_##, SignSlot_*).
See docs/design/laundry-room.md.
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

NAME = "LaundryBay"
LEN, WID, HGT = 24.0, 10.0, 3.2
HL, HW = LEN / 2, WID / 2
WAINSCOT = 1.2
PIL_Y = (-9.0, -3.0, 3.0, 9.0)          # pilasters
PIL_W, PIL_D = 0.5, 0.3
DOOR_W, DOOR_H = 2.0, 2.4                # end double door opening
PART_T = 0.2                             # partition thickness
SIDE_DOOR_Y = 10.55                      # service door on the +X wall
SIDE_DOOR_W, SIDE_DOOR_H = 1.0, 2.15


def materials():
    return {
        "floor": L.material("Floor_Concrete", tex="ph_concrete_floor_worn_001", normal_strength=0.8,
                            vertex_color=True, tint=(0.8, 0.8, 0.76)),
        "tile": L.material("Wall_Tile", tex="ph_long_white_tiles", normal_strength=1.0,
                           vertex_color=True, tint=(0.92, 0.9, 0.8)),
        "plaster": L.material("Wall_Plaster", tex="ph_painted_plaster_wall", normal_strength=0.8,
                              vertex_color=True, tint=(0.93, 0.85, 0.52)),
        "ceiling": L.material("Ceiling_Tile", tex="ceiling_tile", normal_strength=0.8, vertex_color=True),
        "plenum": L.material("Plenum_Dark", base=(0.012, 0.011, 0.01), roughness=0.9),
        "cap": L.material("Tile_Cap", base=(0.78, 0.76, 0.68), roughness=0.25, vertex_color=True),
        "cove": L.material("Rubber_Cove", base=(0.05, 0.045, 0.04), tex="rubber", normal_strength=0.4),
        "line": L.material("Floor_Paint_Yellow", base=(0.75, 0.55, 0.05), roughness=0.55, vertex_color=True),
        "grate": L.material("Drain_Grate", base=(0.08, 0.075, 0.07), metallic=0.85, roughness=0.6),
        "frame": L.material("Door_Frame", base=(0.32, 0.33, 0.33), metallic=0.3, tex="paint_powder",
                            normal_strength=0.3, vertex_color=True),
        "door": L.material("Door_Paint", base=(0.62, 0.6, 0.52), metallic=0.1, tex="paint_powder",
                           normal_strength=0.3, vertex_color=True),
        "steel": L.material("Steel_Brushed", metallic=1.0, tex="steel_brushed", normal_strength=0.22),
        "glass": L.material("Glass_Wired", base=(0.15, 0.17, 0.16), roughness=0.08, alpha=0.3),
        "black": L.material("Print_Black", base=(0.01, 0.01, 0.01), roughness=0.5),
        "white": L.material("Print_White", base=(0.88, 0.89, 0.9), roughness=0.35),
        "exit": L.material("Exit_Sign_Red", base=(0.9, 0.05, 0.03), emission=(1.0, 0.06, 0.03),
                           emission_strength=4.0),
        "exit_body": L.material("Exit_Sign_Body", base=(0.75, 0.74, 0.7), roughness=0.4),
        "pipe_green": L.material("Pipe_Green", base=(0.17, 0.24, 0.18), metallic=0.2, tex="paint_powder",
                                 normal_strength=0.3, vertex_color=True),
        "pipe_red": L.material("Pipe_Red", base=(0.45, 0.06, 0.04), metallic=0.2, tex="paint_powder",
                               normal_strength=0.3, vertex_color=True),
        "lagging": L.material("Pipe_Lagging", base=(0.72, 0.7, 0.62), tex="plastic_matte", normal_strength=0.6,
                              vertex_color=True),
        "galv": L.material("Galvanized", base=(0.55, 0.56, 0.56), metallic=0.9, roughness=0.45),
        "brass": L.material("Brass", base=(0.75, 0.55, 0.25), metallic=1.0, roughness=0.3),
        "valve_blue": L.material("Valve_Blue", base=(0.05, 0.2, 0.6), roughness=0.4),
        "hose": L.material("Hose_Braided", base=(0.6, 0.6, 0.6), metallic=0.8, roughness=0.45, tex="steel_brushed",
                           normal_strength=1.0),
        "clock_face": L.material("Clock_Face", base=(0.86, 0.85, 0.8), roughness=0.3),
        "sign": L.material("Sign_Plate", base=(0.82, 0.82, 0.8), roughness=0.4),
        "extinguisher": L.material("Extinguisher_Red", base=(0.6, 0.03, 0.02), roughness=0.25, coat=0.8),
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


def slot(name, col, parent, loc, rot_z_deg=0.0):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = 0.3
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(rot_z_deg))
    return L.link(e, col, parent)


# ------------------------------------------------------------------- surfaces

def build_floor(m, col, root):
    floor = add("Floor", L.grid_bm(WID, LEN, 0.5, (-HW, -HL, 0), (1, 0, 0), (0, 1, 0)), m["floor"], col, root,
                uv="box", texel=2.5, dirt=dict(seed=1, floor=-10, stain=0.45, stain_scale=2.2))
    for i, x in enumerate((-3.75, 3.75)):
        add(f"AisleLine_{i}", L.box_bm(0.08, LEN, 0.003, (x, 0, 0.0025)), m["line"], col, root,
            dirt=dict(seed=5 + i, floor=-10, stain=0.6, stain_scale=0.5))
    for i, y in enumerate((-6.0, 0.0, 6.0)):
        add(f"DrainPit_{i}", L.box_bm(0.3, 0.3, 0.06, (0, y, -0.03), skip=("+z",)), m["plenum"], col, root)
        add(f"DrainFrame_{i}", L.box_bm(0.34, 0.34, 0.006, (0, y, 0.0)), m["grate"], col, root)
        for k in range(9):
            add(f"DrainBar_{i}_{k}", L.box_bm(0.012, 0.3, 0.008, (-0.12 + k * 0.03, y, 0.003)), m["grate"],
                col, root)
    return floor


def wall_run(m, col, root, name, x, y0, y1, facing, seed, z0=0.0, z1=HGT, ext_end=0.0):
    """One wall strip at x between y0..y1: cove, tile wainscot, cap, plaster."""
    sx = 1 if facing == "+x" else -1          # normal direction
    au, av = Vector((0, 1, 0)), Vector((0, 0, 1))
    if sx < 0:
        au = Vector((0, -1, 0))
        y0, y1 = y1, y0
    length = abs(y1 - y0)
    wd = dict(seed=seed, floor=0.0, floor_band=0.5, floor_dark=0.55, stain=0.35, stain_scale=1.4, drip=0.35,
              ceiling=HGT, ceiling_band=0.7)
    add(f"{name}_Tile", L.grid_bm(length, WAINSCOT - z0, 0.25, (x, y0, z0), au, av), m["tile"], col, root,
        uv="box", texel=1.0, dirt=wd)
    add(f"{name}_Plaster", L.grid_bm(length, z1 - WAINSCOT, 0.4, (x, y0, WAINSCOT), au, av), m["plaster"], col,
        root, uv="box", texel=2.0, dirt=wd)
    # Trim runs ext_end past the far end so its end face hides inside the partition
    # instead of sitting flush on the partition's face (z-fighting).
    t0, t1 = min(y0, y1), max(y0, y1) + ext_end
    yc, tlen = (t0 + t1) / 2, t1 - t0
    add(f"{name}_Cap", L.box_bm(0.025, tlen, 0.03, (x + sx * 0.012, yc, WAINSCOT)), m["cap"], col, root,
        bev=(0.008, 3), dirt=wd)
    if z0 == 0.0:
        add(f"{name}_Cove", L.box_bm(0.012, tlen, 0.1, (x + sx * 0.006, yc, 0.05)), m["cove"], col, root,
            uv="box", bev=(0.003, 2))


def build_walls(m, col, root):
    # -X wall (washers), continuous.
    wall_run(m, col, root, "WallW", -HW, -HL, HL - PART_T / 2, "+x", seed=11, ext_end=0.04)
    # +X wall (dryers) with the service door opening.
    d0, d1 = SIDE_DOOR_Y - SIDE_DOOR_W / 2, SIDE_DOOR_Y + SIDE_DOOR_W / 2
    wall_run(m, col, root, "WallE_a", HW, -HL, d0, "-x", seed=12)
    wall_run(m, col, root, "WallE_b", HW, d1, HL - PART_T / 2, "-x", seed=13, ext_end=0.04)
    wall_run(m, col, root, "WallE_over", HW, d0, d1, "-x", seed=14, z0=SIDE_DOOR_H)
    # Pilasters.
    for i, y in enumerate(PIL_Y):
        for side, x in (("W", -HW + PIL_D / 2), ("E", HW - PIL_D / 2)):
            wd = dict(seed=30 + i, floor=0.0, floor_band=0.5, floor_dark=0.55, stain=0.3, drip=0.3,
                      ceiling=HGT)
            add(f"Pilaster_{side}{i}_Tile", L.box_bm(PIL_D, PIL_W, WAINSCOT, (x, y, WAINSCOT / 2), skip=("-z", "+z")),
                m["tile"], col, root, uv="box", texel=1.0, dirt=wd)
            add(f"Pilaster_{side}{i}_Plaster", L.box_bm(PIL_D, PIL_W, HGT - WAINSCOT, (x, y, (HGT + WAINSCOT) / 2),
                                                        skip=("-z", "+z")),
                m["plaster"], col, root, uv="box", texel=2.0, dirt=wd)
            add(f"Pilaster_{side}{i}_Cap", L.box_bm(PIL_D + 0.03, PIL_W + 0.03, 0.036, (x, y, WAINSCOT)), m["cap"],
                col, root, bev=(0.008, 3), dirt=wd)


def build_partition(m, col, root):
    """Partition wall at y=+HL with a double swing door; tiled/plastered both sides."""
    y = HL
    for face, yy, facing in (("S", y - PART_T / 2, -1), ("N", y + PART_T / 2, 1)):
        # Faces: the south face looks back into this bay (-Y), the north one into the next bay.
        au = Vector((1, 0, 0)) if facing < 0 else Vector((-1, 0, 0))
        side_w = (WID - DOOR_W) / 2
        for part, (xa, xb) in (("L", (-HW, -DOOR_W / 2)), ("R", (DOOR_W / 2, HW))):
            x0 = xa if facing < 0 else xb
            seg = dict(seed=50 + (1 if part == "R" else 0) + (2 if face == "N" else 0), floor=0.0, floor_band=0.5,
                       floor_dark=0.55, stain=0.35, drip=0.35, ceiling=HGT)
            add(f"Part{face}_{part}_Tile", L.grid_bm(side_w, WAINSCOT, 0.25, (x0, yy, 0), au, (0, 0, 1)),
                m["tile"], col, root, uv="box", texel=1.0, dirt=seg)
            add(f"Part{face}_{part}_Plaster", L.grid_bm(side_w, HGT - WAINSCOT, 0.4, (x0, yy, WAINSCOT), au, (0, 0, 1)),
                m["plaster"], col, root, uv="box", texel=2.0, dirt=seg)
            # Outer ends run 4 cm past the side walls (hidden outside the room).
            xa2, xb2 = (xa - 0.04, xb) if part == "L" else (xa, xb + 0.04)
            xc, trim_w = (xa2 + xb2) / 2, xb2 - xa2
            add(f"Part{face}_{part}_Cap", L.box_bm(trim_w, 0.025, 0.03, (xc, yy + facing * 0.012, WAINSCOT)),
                m["cap"], col, root, bev=(0.008, 3))
            add(f"Part{face}_{part}_Cove", L.box_bm(trim_w, 0.012, 0.1, (xc, yy + facing * 0.006, 0.05)),
                m["cove"], col, root, uv="box")
        x0 = -DOOR_W / 2 if facing < 0 else DOOR_W / 2
        add(f"Part{face}_Over", L.grid_bm(DOOR_W, HGT - DOOR_H, 0.4, (x0, yy, DOOR_H), au, (0, 0, 1)),
            m["plaster"], col, root, uv="box", texel=2.0,
            dirt=dict(seed=60, floor=0.0, stain=0.35, drip=0.3, ceiling=HGT))
    # Opening reveals (jambs + head).
    for i, x in enumerate((-DOOR_W / 2, DOOR_W / 2)):
        add(f"Jamb_{i}", L.box_bm(0.06, PART_T + 0.04, DOOR_H, (x + (0.03 if i == 0 else -0.03), y, DOOR_H / 2)),
            m["frame"], col, root, bev=(0.006, 2), uv="box",
            dirt=dict(seed=70 + i, floor=0.0, floor_band=0.6, floor_dark=0.5, stain=0.3))
    add("DoorHead", L.box_bm(DOOR_W, PART_T + 0.04, 0.06, (0, y, DOOR_H - 0.03)), m["frame"], col, root,
        bev=(0.006, 2), uv="box", dirt=dict(seed=72, floor=0.0, stain=0.3))

    # Two door leaves, hinged at the jambs, propped open into the next bay.
    leaf_w = DOOR_W / 2 - 0.07
    for i, (name, hx, sgn, angle) in enumerate((("DoorLeafL", -DOOR_W / 2 + 0.06, 1, 72),
                                                 ("DoorLeafR", DOOR_W / 2 - 0.06, -1, 64))):
        pivot = L.root_empty(name, col)
        pivot.parent = root
        pivot.location = (hx, y + PART_T / 2, 0)
        pivot.rotation_euler = (0, 0, math.radians(sgn * angle))
        pivot.empty_display_size = 0.2
        cx = sgn * leaf_w / 2
        leaf = L.box_bm(leaf_w, 0.045, DOOR_H - 0.04, (cx, 0.0225, (DOOR_H - 0.04) / 2 + 0.01))
        add(f"{name}_Panel", leaf, m["door"], col, pivot, bev=(0.004, 2), uv="box",
            dirt=dict(seed=80 + i, floor=0.0, floor_band=0.6, floor_dark=0.45, stain=0.35, drip=0.2))
        for fy, fs in ((-0.001, "a"), (0.046, "b")):
            add(f"{name}_Kick{fs}", L.box_bm(leaf_w - 0.04, 0.0015, 0.3, (cx, fy, 0.17)), m["steel"], col, pivot,
                uv="box")
            add(f"{name}_Push{fs}", L.box_bm(0.1, 0.0015, 0.3, (cx + sgn * (leaf_w / 2 - 0.12), fy, 1.15)),
                m["steel"], col, pivot, uv="box")
        # Porthole window: steel ring + wired glass, through the leaf.
        ring = [(0.15, -0.006), (0.165, -0.006), (0.168, 0.0), (0.168, 0.045), (0.165, 0.051), (0.15, 0.051),
                (0.15, 0.045), (0.155, 0.04), (0.155, 0.005), (0.15, 0.0)]
        rb = L.revolve_bm([(r, yy) for r, yy in ring], 48, True, (cx, 0, 1.55))
        add(f"{name}_PortRing", rb, m["steel"], col, pivot, smooth=50)
        add(f"{name}_PortGlass", L.cylinder_bm(0.152, 0.006, 48, (cx, 0.0225, 1.55), axis="Y"), m["glass"], col,
            pivot)

    # EXIT sign over the door (both sides) and a blank bay-number plate (text added in Unity).
    for face, yy, s in (("S", y - PART_T / 2, -1), ("N", y + PART_T / 2, 1)):
        add(f"Exit{face}_Body", L.box_bm(0.36, 0.08, 0.18, (0, yy + s * 0.04, DOOR_H + 0.2)), m["exit_body"], col,
            root, bev=(0.01, 2))
        L.text_mesh(f"Exit{face}_Text", "EXIT", 0.11, m["exit"], col, root, bold=True,
                    location=(0, yy + s * 0.083, DOOR_H + 0.2),
                    rotation=(math.radians(90), 0, 0 if s < 0 else math.pi))
        add(f"BayPlate{face}", L.box_bm(0.9, 0.01, 0.22, (-1.6, yy + s * 0.005, 2.55)), m["sign"], col, root,
            bev=(0.004, 2))
        sl = slot(f"SignSlot_{face}", col, root, (-1.6, yy + s * 0.0125, 2.55), 0 if s < 0 else 180)


def build_side_door(m, col, root):
    """Service door on the +X wall leading to a short dead-end vestibule (teleport trigger in Unity)."""
    x, y = HW, SIDE_DOOR_Y
    for i, yy in enumerate((y - SIDE_DOOR_W / 2, y + SIDE_DOOR_W / 2)):
        add(f"SideJamb_{i}", L.box_bm(0.2, 0.05, SIDE_DOOR_H, (x + 0.08, yy + (0.025 if i == 0 else -0.025),
                                                               SIDE_DOOR_H / 2)),
            m["frame"], col, root, bev=(0.005, 2), uv="box", dirt=dict(seed=90 + i, floor=0.0, stain=0.3))
    add("SideHead", L.box_bm(0.2, SIDE_DOOR_W, 0.05, (x + 0.08, y, SIDE_DOOR_H - 0.025)), m["frame"], col, root,
        bev=(0.005, 2), uv="box")
    pivot = L.root_empty("SideDoorLeaf", col)
    pivot.parent = root
    pivot.location = (x + 0.02, y - SIDE_DOOR_W / 2 + 0.05, 0)
    pivot.rotation_euler = (0, 0, math.radians(-18))      # left ajar
    pivot.empty_display_size = 0.2
    lw = SIDE_DOOR_W - 0.1
    add("SideDoor_Panel", L.box_bm(0.045, lw, SIDE_DOOR_H - 0.06, (0.0225, lw / 2, (SIDE_DOOR_H - 0.06) / 2 + 0.01)),
        m["door"], col, pivot, bev=(0.004, 2), uv="box",
        dirt=dict(seed=95, floor=0.0, floor_band=0.6, floor_dark=0.45, stain=0.4, drip=0.3))
    add("SideDoor_Lever", L.box_bm(0.07, 0.12, 0.02, (-0.04, lw - 0.1, 1.0)), m["steel"], col, pivot,
        bev=(0.008, 3), uv="box")
    add("SideDoor_Kick", L.box_bm(0.0015, lw - 0.04, 0.25, (-0.001, lw / 2, 0.14)), m["steel"], col, pivot,
        uv="box")
    add("SideDoor_Sign", L.box_bm(0.004, 0.36, 0.12, (-0.003, lw / 2, 1.6)), m["sign"], col, pivot)
    L.text_mesh("SideDoor_SignText", "SERVICE", 0.045, m["black"], col, pivot, bold=True,
                location=(-0.0055, lw / 2, 1.615), rotation=(math.radians(90), 0, -math.pi / 2))
    L.text_mesh("SideDoor_SignText2", "STAFF ONLY", 0.026, m["black"], col, pivot,
                location=(-0.0055, lw / 2, 1.565), rotation=(math.radians(90), 0, -math.pi / 2))
    # Vestibule: 2.6 m deep dark corridor that turns out of sight.
    vx0, vx1 = HW, HW + 2.6
    vy0, vy1 = y - SIDE_DOOR_W / 2, y + SIDE_DOOR_W / 2 + 1.2
    vd = dict(seed=97, floor=0.0, floor_band=0.6, floor_dark=0.5, stain=0.5, drip=0.5, ceiling=SIDE_DOOR_H + 0.25)
    add("Vest_Floor", L.grid_bm(vx1 - vx0, vy1 - vy0, 0.5, (vx0, vy0, 0), (1, 0, 0), (0, 1, 0)), m["floor"], col, root,
        uv="box", texel=2.5, dirt=dict(seed=98, floor=-10, stain=0.6))
    add("Vest_Ceil", L.grid_bm(vx1 - vx0, vy1 - vy0, 0.6, (vx0, vy1, SIDE_DOOR_H + 0.25), (1, 0, 0), (0, -1, 0)),
        m["plaster"], col, root, uv="box", texel=2.0, dirt=vd)
    add("Vest_WallS", L.grid_bm(vx1 - vx0, SIDE_DOOR_H + 0.25, 0.4, (vx1, vy0, 0), (-1, 0, 0), (0, 0, 1)),
        m["plaster"], col, root, uv="box", texel=2.0, dirt=vd)
    add("Vest_WallE", L.grid_bm(vy1 - vy0, SIDE_DOOR_H + 0.25, 0.4, (vx1, vy1, 0), (0, -1, 0), (0, 0, 1)),
        m["plaster"], col, root, uv="box", texel=2.0, dirt=vd)
    add("Vest_WallN", L.grid_bm(vx1 - vx0 - 1.2, SIDE_DOOR_H + 0.25, 0.4, (vx0, vy1, 0), (1, 0, 0), (0, 0, 1)),
        m["plaster"], col, root, uv="box", texel=2.0, dirt=vd)
    # Sits 12 cm behind the room's tiled wall (never in the same plane: z-fighting).
    add("Vest_WallBack", L.grid_bm(1.2, SIDE_DOOR_H + 0.25, 0.4, (vx0 + 0.12, vy1, 0), (0, -1, 0), (0, 0, 1)),
        m["plaster"], col, root, uv="box", texel=2.0, dirt=vd)
    slot("SideDoorTrigger", col, root, (HW + 1.9, y + 0.6, 1.0), 0)


def build_ceiling(m, col, root):
    """Drop ceiling: grid aligned to 0.6 m tiles, two missing tiles and one hanging."""
    step = 0.6
    nx, ny = 18, 40
    x0, y0 = -5.4, -HL
    missing = {(4, 13), (13, 29)}
    # Troffer openings: 0.6 x 1.2 m, aligned to the grid (x = +-2.1, every 2.4 m).
    troffer_cells = set()
    for i in (5, 12):
        for k in range(10):
            j = 1 + 4 * k
            troffer_cells |= {(i, j), (i, j + 1)}
    bm = bmesh.new()
    verts = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            verts[i, j] = bm.verts.new((x0 + i * step, y0 + j * step, HGT))
    for j in range(ny):
        for i in range(nx):
            if (i, j) in missing or (i, j) in troffer_cells:
                continue
            bm.faces.new((verts[i, j], verts[i, j + 1], verts[i + 1, j + 1], verts[i + 1, j]))   # faces down
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    add("Ceiling", bm, m["ceiling"], col, root, uv="box", texel=1.2,
        dirt=dict(seed=7, floor=-10, stain=0.55, stain_scale=1.1, ceiling=None))
    for k, (i, j) in enumerate(missing):
        cx, cy = x0 + (i + 0.5) * step, y0 + (j + 0.5) * step
        add(f"Plenum_{k}", L.box_bm(step, step, 0.5, (cx, cy, HGT + 0.25), skip=("-z",)), m["plenum"], col, root)
        add(f"PlenumPipe_{k}", L.cylinder_bm(0.04, step, 16, (cx, cy, HGT + 0.3), axis="X"), m["galv"], col, root)
        if k == 1:
            # The missing tile hangs from one corner of the grid.
            t = L.box_bm(0.585, 0.585, 0.015, (0.29, -0.29, -0.0075))
            tile = add("HangingTile", t, m["ceiling"], col, root, uv="box", texel=1.2,
                       dirt=dict(seed=9, floor=-10, stain=0.7, stain_scale=0.4))
            tile.location = (cx - 0.3, cy + 0.3, HGT)
            tile.rotation_euler = (math.radians(-55), math.radians(12), 0)
    # Troffer slots: two rows, every 2.4 m; one sprinkler head per 3 m.
    n = 0
    for x in (-2.1, 2.1):
        for k in range(10):
            slot(f"TrofferSlot_{n:02d}", col, root, (x, -12 + 1.2 + k * 2.4, HGT), 0)
            n += 1
    for i, y in enumerate([-10.5 + 3 * k for k in range(8)]):
        for j, x in enumerate((-3.6, 0.0, 3.6)):
            bm = L.revolve_bm([(0.0, -0.0), (0.03, 0.0), (0.03, 0.006), (0.009, 0.01), (0.009, 0.045),
                               (0.02, 0.05), (0.0, 0.052)], 12, True, (0, 0, 0))
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, "X"))
            bmesh.ops.translate(bm, vec=Vector((x, y, HGT)), verts=bm.verts)
            add(f"Sprinkler_{i}_{j}", bm, m["brass"], col, root)


def build_pipes(m, col, root):
    """Exposed pipe runs along both walls under the ceiling, with hangers and flanges."""
    runs = [("Lag", 0.085, 2.92, "lagging"), ("Green", 0.055, 2.72, "pipe_green"), ("Red", 0.04, 2.58, "pipe_red")]
    for side, sx in (("W", -1), ("E", 1)):
        xw = sx * (HW - PIL_D - 0.12)
        for k, (nm, r, z, mat) in enumerate(runs):
            x = xw - sx * k * 0.03
            add(f"Pipe{side}_{nm}", L.cylinder_bm(r, LEN, 24, (x, 0, z), axis="Y", caps=False), m[mat], col, root,
                dirt=dict(seed=100 + k, floor=-10, stain=0.45, stain_scale=0.8, drip=0.0), uv=None)
            for i in range(16):
                yy = -HL + 0.75 + i * 1.5
                add(f"Clamp{side}_{nm}_{i:02d}", L.cylinder_bm(r + 0.008, 0.03, 24, (x, yy, z), axis="Y"),
                    m["galv"], col, root)
                add(f"Hanger{side}_{nm}_{i:02d}", L.cylinder_bm(0.006, HGT - z - r, 8,
                                                                (x, yy, (HGT + z + r) / 2)), m["galv"], col, root)
            for i in range(4):
                yy = -HL + 3 + i * 6
                add(f"Flange{side}_{nm}_{i}", L.cylinder_bm(r * 1.45, 0.04, 24, (x, yy, z), axis="Y"),
                    m[mat], col, root, bev=(0.004, 2, 30))
            L.cylinder_uv(bpy.data.objects[f"Pipe{side}_{nm}"], "Y", texel=0.6)


def build_wall_details(m, col, root):
    # Wall clock above the washers, stopped at 3:33.
    cx, cy, cz = -HW + 0.03, 0.0, 2.35
    face = L.cylinder_bm(0.17, 0.02, 48, (cx, cy, cz), axis="X")
    add("Clock_Body", L.cylinder_bm(0.185, 0.045, 48, (cx + 0.0, cy, cz), axis="X"), m["black"], col, root,
        bev=(0.01, 3, 30))
    add("Clock_Face", face, m["clock_face"], col, root)
    for i in range(12):
        a = math.radians(90 - i * 30)
        add(f"Clock_Tick_{i:02d}", L.box_bm(0.003, 0.008 if i % 3 else 0.012, 0.025 if i % 3 else 0.035,
                                            (0, 0, 0)), m["black"], col, root)
        t = bpy.data.objects[f"Clock_Tick_{i:02d}"]
        t.location = (cx + 0.012, cy + math.cos(a) * 0.14, cz + math.sin(a) * 0.14)
        t.rotation_euler = (a - math.pi / 2, 0, 0)
    for nm, ln, ang in (("Hour", 0.085, 90 - 3.55 * 30), ("Minute", 0.13, 90 - 33 * 6)):
        h = add(f"Clock_{nm}Hand", L.box_bm(0.003, 0.008, ln, (0, 0, ln / 2 - 0.015)), m["black"], col, root)
        h.location = (cx + 0.015, cy, cz)
        h.rotation_euler = (math.radians(-(90 - ang)), 0, 0)
    # Fire extinguisher on the first east pilaster.
    ex, ey = HW - PIL_D - 0.1, PIL_Y[1] - 0.0
    add("Extinguisher", L.cylinder_bm(0.08, 0.5, 32, (ex, ey, 0.75)), m["extinguisher"], col, root,
        bev=(0.03, 4, 30))
    add("ExtinguisherHead", L.box_bm(0.05, 0.12, 0.08, (ex, ey, 1.04)), m["black"], col, root, bev=(0.01, 2))
    add("ExtinguisherBracket", L.box_bm(0.03, 0.12, 0.2, (ex + 0.08, ey, 0.85)), m["frame"], col, root,
        dirt=dict(seed=120, floor=0.0, stain=0.2))
    # Electrical conduit with junction boxes along the west wall above the tile cap.
    add("Conduit", L.cylinder_bm(0.012, LEN - 0.3, 12, (-HW + 0.03, -0.1, 1.9), axis="Y"), m["galv"], col, root)
    for i, y in enumerate((-10.5, -4.5, 1.5, 7.5)):
        add(f"JBox_{i}", L.box_bm(0.05, 0.11, 0.11, (-HW + 0.03, y, 1.9)), m["galv"], col, root, bev=(0.004, 2))
        add(f"Outlet_{i}", L.box_bm(0.01, 0.07, 0.11, (-HW + 0.058, y, 1.9)), m["white"], col, root,
            bev=(0.003, 2))


CURB_H = 0.2                 # raised tiled plinth under the washer bank
WASHER_W, WASHER_D = 0.76, 0.724
DRYER_W, DRYER_D = 0.792, 0.96


def machine_slots(col, root, m=None):
    """Washers on a raised curb along the west wall, stack dryers along the east
    wall, both as continuous banks with no gaps (like a real laundromat), grouped
    between the pilasters."""
    m = m or materials()
    segments = [(-HL + PART_T / 2, PIL_Y[0] - PIL_W / 2), (PIL_Y[0] + PIL_W / 2, PIL_Y[1] - PIL_W / 2),
                (PIL_Y[1] + PIL_W / 2, PIL_Y[2] - PIL_W / 2), (PIL_Y[2] + PIL_W / 2, PIL_Y[3] - PIL_W / 2),
                (PIL_Y[3] + PIL_W / 2, HL - PART_T / 2)]
    wx = -HW + 0.06 + WASHER_D / 2
    curb_front = wx + WASHER_D / 2 + 0.06
    w = d = 0
    for si, (a, b) in enumerate(segments):
        # Curb: back runs 5 cm into the wall, ends 3 cm into the pilasters/partition,
        # so none of its faces lies flush on another surface.
        ca, cb = a - 0.03, b + 0.03
        curb = L.box_bm(curb_front + HW + 0.05, cb - ca, CURB_H, ((curb_front - HW - 0.05) / 2, (ca + cb) / 2, CURB_H / 2))
        add(f"Curb_{si}", curb, m["tile"], col, root, uv="box", texel=1.0, bev=(0.008, 3),
            dirt=dict(seed=140 + si, floor=0.0, floor_band=0.25, floor_dark=0.55, stain=0.4, stain_scale=0.5))
        n = int((b - a - 0.04) // WASHER_W)
        start = (a + b) / 2 - (n - 1) * WASHER_W / 2
        for k in range(n):
            y = start + k * WASHER_W
            slot(f"WasherSlot_{w:02d}", col, root, (wx, y, CURB_H), 90)
            # Hot / cold supply valves on the wall, braided hoses down behind the machine.
            for j, (dy, mat) in enumerate(((-0.12, "pipe_red"), (0.12, "valve_blue"))):
                vy = y + dy
                add(f"Valve_{w:02d}_{j}", L.cylinder_bm(0.018, 0.08, 16, (-HW + 0.04, vy, 1.72), axis="X"), m["galv"],
                    col, root)
                add(f"ValveHandle_{w:02d}_{j}", L.box_bm(0.012, 0.07, 0.016, (-HW + 0.09, vy, 1.72)), m[mat], col, root,
                    bev=(0.004, 2))
                add(f"Hose_{w:02d}_{j}", L.cylinder_bm(0.011, 1.72 - CURB_H - 1.15, 10,
                                                       (-HW + 0.06, vy, (1.72 + CURB_H + 1.15) / 2)),
                    m["hose"], col, root)
            w += 1
        if si == 4:
            continue          # service door segment on the east wall
        n = int((b - a - 0.04) // DRYER_W)
        start = (a + b) / 2 - (n - 1) * DRYER_W / 2
        for k in range(n):
            slot(f"DryerSlot_{d:02d}", col, root, (HW - 0.04 - DRYER_D / 2, start + k * DRYER_W, 0), -90)
            d += 1
    # Loose props along the aisle: carts / tables.
    for i, y in enumerate((-7.5, -1.0, 5.5)):
        slot(f"PropSlot_{i}", col, root, (-2.2 if i % 2 else 2.2, y, 0), 0)
    return w, d


def lookdev_interior():
    """Preview lighting for renders inside the bay (emissive panels + dim world)."""
    col = L.collection("_LookDev")
    L.clear_collection("_LookDev")
    scene = bpy.context.scene
    world = bpy.data.worlds.get("Interior") or bpy.data.worlds.new("Interior")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.004, 0.004, 0.003, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    lens = L.material("LookDev_Troffer", base=(1, 1, 1), emission=(1.0, 0.97, 0.88), emission_strength=6.0)
    bpy.context.view_layer.update()          # slot matrix_world is stale until the depsgraph runs
    for k in range(20):
        s = bpy.data.objects.get(f"TrofferSlot_{k:02d}")
        if s is None:
            continue
        p = s.matrix_world.translation
        o = L.link(L.mesh_object(f"LD_Troffer_{k}", L.box_bm(0.58, 1.18, 0.01, (p.x, p.y, p.z - 0.01)), lens), col)
        if k in (3, 14):
            o.hide_render = True                 # dead tubes
        ld = bpy.data.lights.new(f"LD_Area_{k}", "AREA")
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = 0.55, 1.15
        ld.energy = 0 if k in (3, 14) else 90
        ld.color = (1.0, 0.95, 0.82)
        lo = L.link(bpy.data.objects.new(f"LD_Area_{k}", ld), col)
        lo.location = (p.x, p.y, p.z - 0.03)
    cam_data = bpy.data.cameras.get("LookDevCam") or bpy.data.cameras.new("LookDevCam")
    cam_data.lens = 24
    cam = L.link(bpy.data.objects.new("LookDevCam", cam_data), col)
    cam.location = (-1.0, -11.2, 1.65)
    cam.rotation_euler = (Vector((0.4, 6, 1.4)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_raytracing = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0


def build():
    # Keep the washer around (other collection); hide it from renders of the bay.
    wc = bpy.data.collections.get("WasherExtractor")
    if wc:
        wc.hide_render = True
        wc.hide_viewport = True
    L.clear_collection(NAME)
    col = L.collection(NAME)
    root = L.root_empty(NAME, col)
    m = materials()
    build_floor(m, col, root)
    build_walls(m, col, root)
    build_partition(m, col, root)
    build_side_door(m, col, root)
    build_ceiling(m, col, root)
    build_pipes(m, col, root)
    build_wall_details(m, col, root)
    w, d = machine_slots(col, root, m)
    lookdev_interior()
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for obj in col.all_objects:
        if obj.type == "MESH":
            ev = obj.evaluated_get(dg).data
            ev.calc_loop_triangles()
            tris += len(ev.loop_triangles)
    return {"objects": len(col.all_objects), "triangles": tris, "washers": w, "dryers": d}
