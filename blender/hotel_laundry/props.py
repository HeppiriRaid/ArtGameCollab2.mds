"""Smaller props for the hotel laundry: troffer light, linen cart, folding table,
wire shelving with linens, detergent drums. Each builds its own collection;
origin at the floor (or ceiling for the troffer), front faces -Y.
"""
import importlib
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.expanduser("~/Documents/GitHub/ArtGameCollab2.mds/blender/hotel_laundry"))
import laundry_lib as L  # noqa: E402
importlib.reload(L)


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


def start(name):
    L.clear_collection(name)
    col = L.collection(name)
    return col, L.root_empty(name, col)


# --------------------------------------------------------------------- troffer

def troffer():
    """2x4 ft recessed fluorescent troffer with a parabolic louvre grid.
    Origin at the ceiling plane; the fixture hangs 0-12 cm above it (+Z).
    The lens is its own material ("Troffer_Lens") so Unity can flicker it."""
    col, root = start("Troffer")
    white = L.material("Troffer_Paint", base=(0.85, 0.84, 0.8), roughness=0.4, tex="paint_powder",
                       normal_strength=0.2)
    louvre = L.material("Troffer_Louvre", base=(0.9, 0.9, 0.9), metallic=1.0, roughness=0.18)
    lens = L.material("Troffer_Lens", base=(1.0, 0.98, 0.92), roughness=0.3,
                      emission=(1.0, 0.96, 0.86), emission_strength=5.0)
    w, l, d = 0.6, 1.2, 0.12
    # Flange frame flush with the ceiling, housing above.
    add("Housing", L.box_bm(w - 0.02, l - 0.02, d, (0, 0, d / 2), skip=("-z",)), white, col, root)
    for i, (sx, sy, cx, cy) in enumerate([(w, 0.025, 0, -l / 2 + 0.0125), (w, 0.025, 0, l / 2 - 0.0125),
                                          (0.025, l, -w / 2 + 0.0125, 0), (0.025, l, w / 2 - 0.0125, 0)]):
        add(f"Flange_{i}", L.box_bm(sx, sy, 0.012, (cx, cy, -0.006)), white, col, root, bev=(0.003, 2))
    add("Lens", L.box_bm(w - 0.06, l - 0.06, 0.004, (0, 0, d - 0.02)), lens, col, root)
    # Parabolic louvres: 3 long blades, 9 cross blades, curved profile approximated by a taper.
    for i in range(4):
        x = -w / 2 + 0.03 + i * (w - 0.06) / 3
        bm = L.box_bm(0.006, l - 0.06, 0.07, (x, 0, 0.035))
        add(f"LouvreLong_{i}", bm, louvre, col, root, bev=(0.0025, 2))
    for k in range(10):
        y = -l / 2 + 0.03 + k * (l - 0.06) / 9
        add(f"LouvreCross_{k}", L.box_bm(w - 0.06, 0.005, 0.07, (0, y, 0.035)), louvre, col, root,
            bev=(0.002, 2))
    return col.name


# ------------------------------------------------------------------ linen cart

def linen_cart():
    """Hotel linen cart: galvanised frame, vinyl-coated canvas bag, four casters,
    half full of crumpled towels."""
    col, root = start("LinenCart")
    frame = L.material("Cart_Frame", base=(0.62, 0.63, 0.63), metallic=0.85, roughness=0.4, vertex_color=True)
    canvas = L.material("Cart_Canvas", base=(0.36, 0.38, 0.4), tex="plastic_matte", normal_strength=0.8,
                        vertex_color=True)
    rubber = L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5)
    towel = L.material("Towel_White", base=(0.86, 0.85, 0.82), tex="towel", normal_strength=1.0, vertex_color=True)
    W, D, H, B = 0.72, 1.05, 0.95, 0.22       # width, depth, rim height, bag bottom
    for i, (x, y) in enumerate([(-W / 2, -D / 2), (W / 2, -D / 2), (-W / 2, D / 2), (W / 2, D / 2)]):
        add(f"Post_{i}", L.cylinder_bm(0.012, H - 0.12, 12, (x, y, 0.12 + (H - 0.12) / 2)), frame, col, root)
        # caster: swivel plate, fork, wheel
        add(f"CasterPlate_{i}", L.box_bm(0.07, 0.07, 0.008, (x, y, 0.115)), frame, col, root)
        add(f"CasterFork_{i}", L.box_bm(0.035, 0.05, 0.06, (x, y, 0.08)), frame, col, root, bev=(0.006, 2))
        add(f"Wheel_{i}", L.cylinder_bm(0.05, 0.03, 24, (x, y + 0.012, 0.05), axis="X"), rubber, col, root,
            bev=(0.008, 3, 30))
    for k, z in enumerate((B, H)):
        for j, (a, b) in enumerate([((-W / 2, -D / 2), (W / 2, -D / 2)), ((W / 2, -D / 2), (W / 2, D / 2)),
                                    ((W / 2, D / 2), (-W / 2, D / 2)), ((-W / 2, D / 2), (-W / 2, -D / 2))]):
            ax = "X" if a[1] == b[1] else "Y"
            ln = abs(b[0] - a[0]) if ax == "X" else abs(b[1] - a[1])
            add(f"Rail_{k}_{j}", L.cylinder_bm(0.013, ln, 12, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z), axis=ax),
                frame, col, root)
    # Bag: open-top box slightly inset, with a sagging bottom.
    bm = L.box_bm(W - 0.03, D - 0.03, H - B - 0.02, (0, 0, (H + B) / 2 - 0.01), skip=("+z",))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:
        if v.co.z < B + 0.05:
            v.co.z -= 0.035 * (1 - (2 * v.co.x / W) ** 2) * (1 - (2 * v.co.y / D) ** 2)
        else:
            # canvas bulges a little between the posts
            v.co.x *= 1 + 0.03 * (1 - (2 * v.co.y / D) ** 2)
    bag = add("Bag", bm, canvas, col, root, uv="box", texel=0.4,
              dirt=dict(seed=3, floor=0.0, floor_band=0.4, floor_dark=0.6, stain=0.5, stain_scale=0.3))
    # Crumpled towels filling about half the bag.
    random.seed(4)
    tw = add("Towels", _crumpled_pile(W - 0.08, D - 0.08, 0.42, H - 0.12), towel, col, root, uv="box",
             texel=0.25, smooth=80, dirt=dict(seed=6, floor=-10, stain=0.25, stain_scale=0.15))
    tw.location.z = 0
    return col.name


def _crumpled_pile(w, d, h, zc):
    """A lumpy heap: subdivided box displaced by noise, reads as crumpled linen."""
    from mathutils import noise
    bm = L.box_bm(w, d, h, (0, 0, zc))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=10, use_grid_fill=True)
    for v in bm.verts:
        n = noise.fractal(v.co * 7.0, 0.6, 2.0, 4)
        top = (v.co.z - (zc - h / 2)) / h
        v.co += v.normal * (0.045 * n) * (0.4 + top)
        v.co.z += 0.06 * noise.noise(v.co * 3.0) * top
    return bm


# --------------------------------------------------------------- folding table

def folding_table():
    """Stainless folding table with an undershelf, stacks of folded towels on top."""
    col, root = start("FoldingTable")
    steel = L.material("Steel_Brushed", metallic=1.0, tex="steel_brushed", normal_strength=0.22)
    towel = L.material("Towel_White", base=(0.86, 0.85, 0.82), tex="towel", normal_strength=1.0, vertex_color=True)
    rubber = L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5)
    W, D, H = 1.8, 0.76, 0.91
    add("Top", L.box_bm(W, D, 0.04, (0, 0, H - 0.02)), steel, col, root, bev=(0.006, 3), uv="box")
    add("BackSplash", L.box_bm(W, 0.03, 0.12, (0, D / 2 - 0.015, H + 0.06)), steel, col, root, bev=(0.004, 2),
        uv="box")
    add("Shelf", L.box_bm(W - 0.1, D - 0.1, 0.025, (0, 0, 0.25)), steel, col, root, bev=(0.004, 2), uv="box")
    for i, (x, y) in enumerate([(-W / 2 + 0.05, -D / 2 + 0.05), (W / 2 - 0.05, -D / 2 + 0.05),
                                (-W / 2 + 0.05, D / 2 - 0.05), (W / 2 - 0.05, D / 2 - 0.05)]):
        add(f"Leg_{i}", L.cylinder_bm(0.02, H - 0.04, 20, (x, y, (H - 0.04) / 2)), steel, col, root, uv="box")
        add(f"Foot_{i}", L.cylinder_bm(0.024, 0.02, 20, (x, y, 0.01)), rubber, col, root)
    random.seed(11)
    n = 0
    for sx in (-0.55, -0.05, 0.45):
        count = random.randint(4, 9)
        for k in range(count):
            z = H + 0.035 * k + 0.0175
            dx, dy = random.uniform(-0.015, 0.015), random.uniform(-0.015, 0.015)
            add(f"FoldedTowel_{n:02d}", _folded_towel(0.42, 0.3, 0.035, (sx + dx, -0.05 + dy, z),
                                                     random.uniform(-4, 4)),
                towel, col, root, uv="box", texel=0.25, smooth=180, bev=(0.01, 3, 20),
                dirt=dict(seed=n, floor=-10, stain=0.12, stain_scale=0.2))
            n += 1
    return col.name


def _folded_towel(w, d, t, center, rot_deg):
    bm = L.box_bm(w, d, t, (0, 0, 0))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=4, use_grid_fill=True)
    for v in bm.verts:
        u, q = 2 * v.co.x / w, 2 * v.co.y / d
        # pillowy: thicker in the middle, edges pinched and rounded like folded terry
        puff = (1 - u * u) * (1 - q * q)
        v.co.z *= 0.75 + 0.6 * puff
        edge = max(abs(u), abs(q))
        if edge > 0.7:
            k = (edge - 0.7) / 0.3
            v.co.x *= 1 - 0.04 * k
            v.co.y *= 1 - 0.04 * k
        if q < -0.95:
            v.co.y -= 0.008       # the folded front edge bulges out
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ Matrix.Rotation(math.radians(rot_deg), 4, "Z"),
                        verts=bm.verts)
    return bm


# --------------------------------------------------------------- wire shelving

def wire_shelving():
    """Chrome wire shelving unit (4 shelves) stocked with folded sheets and towels."""
    col, root = start("WireShelving")
    chrome = L.material("Chrome_Wire", base=(0.85, 0.86, 0.87), metallic=1.0, roughness=0.15)
    towel = L.material("Towel_White", base=(0.86, 0.85, 0.82), tex="towel", normal_strength=1.0, vertex_color=True)
    sheet = L.material("Sheet_White", base=(0.9, 0.9, 0.88), tex="plastic_matte", normal_strength=0.6,
                       vertex_color=True)
    W, D, H = 1.52, 0.46, 1.88
    for i, (x, y) in enumerate([(-W / 2, -D / 2), (W / 2, -D / 2), (-W / 2, D / 2), (W / 2, D / 2)]):
        add(f"Post_{i}", L.cylinder_bm(0.0125, H, 16, (x, y, H / 2)), chrome, col, root)
    levels = (0.15, 0.7, 1.25, 1.8)
    for k, z in enumerate(levels):
        for j, (sx, sy, cx, cy) in enumerate([(W, 0.012, 0, -D / 2), (W, 0.012, 0, D / 2),
                                              (0.012, D, -W / 2, 0), (0.012, D, W / 2, 0)]):
            add(f"Frame_{k}_{j}", L.box_bm(sx, sy, 0.025, (cx, cy, z)), chrome, col, root)
        for w in range(14):
            x = -W / 2 + 0.05 + w * (W - 0.1) / 13
            add(f"Wire_{k}_{w:02d}", L.cylinder_bm(0.003, D, 6, (x, 0, z + 0.01), axis="Y"), chrome, col, root)
        add(f"Collar_{k}", L.box_bm(W + 0.02, 0.02, 0.006, (0, -D / 2, z - 0.012)), chrome, col, root)
    random.seed(23)
    n = 0
    for k, z in enumerate(levels[:3]):
        x = -W / 2 + 0.12
        while x < W / 2 - 0.2:
            is_sheet = random.random() < 0.4
            w, d, t = (0.36, 0.3, 0.03) if is_sheet else (0.32, 0.26, 0.04)
            count = random.randint(3, 8) if k < 2 else random.randint(2, 7)
            for c in range(count):
                add(f"Linen_{n:03d}", _folded_towel(w, d, t, (x + w / 2 + random.uniform(-0.01, 0.01),
                                                              random.uniform(-0.03, 0.03),
                                                              z + 0.02 + t * (c + 0.5)),
                                                    random.uniform(-3, 3)),
                    sheet if is_sheet else towel, col, root, uv="box", texel=0.25, smooth=180, bev=(0.008, 3, 20),
                    dirt=dict(seed=n, floor=-10, stain=0.15, stain_scale=0.2))
                n += 1
            x += w + random.uniform(0.02, 0.08)
    return col.name


# ----------------------------------------------------------- detergent drums

def detergent_station():
    """Chemical dosing station: wall panel with pumps and tubes over three 20 l drums."""
    col, root = start("DosingStation")
    panel = L.material("Plastic_LightGrey", base=(0.55, 0.56, 0.57), tex="plastic_matte", normal_strength=0.4)
    blue = L.material("Drum_Blue", base=(0.05, 0.2, 0.55), tex="plastic_matte", normal_strength=0.5,
                      vertex_color=True)
    white = L.material("Drum_White", base=(0.82, 0.82, 0.78), tex="plastic_matte", normal_strength=0.5,
                       vertex_color=True)
    red = L.material("Drum_Red", base=(0.6, 0.06, 0.04), tex="plastic_matte", normal_strength=0.5, vertex_color=True)
    tube = L.material("Tube_Clear", base=(0.85, 0.8, 0.6), roughness=0.2, alpha=0.6)
    black = L.material("Print_Black", base=(0.01, 0.01, 0.01), roughness=0.5)
    label = L.material("Label_Paper", base=(0.9, 0.9, 0.85), roughness=0.6)
    add("Panel", L.box_bm(0.95, 0.03, 0.45, (0, 0.2, 1.3)), panel, col, root, bev=(0.006, 2), uv="box")
    for i in range(3):
        x = -0.32 + i * 0.32
        add(f"Pump_{i}", L.box_bm(0.12, 0.09, 0.16, (x, 0.14, 1.3)), panel, col, root, bev=(0.01, 3), uv="box")
        add(f"PumpHead_{i}", L.cylinder_bm(0.035, 0.03, 24, (x, 0.09, 1.3), axis="Y"), black, col, root,
            bev=(0.004, 2, 30))
        mat = (blue, white, red)[i]
        dx = x
        bm = L.box_bm(0.28, 0.24, 0.38, (dx, 0.0, 0.19))
        add(f"Drum_{i}", bm, mat, col, root, bev=(0.03, 4), uv="box",
            dirt=dict(seed=200 + i, floor=0.0, floor_band=0.15, floor_dark=0.7, stain=0.35, stain_scale=0.2))
        add(f"DrumCap_{i}", L.cylinder_bm(0.03, 0.03, 20, (dx + 0.06, -0.04, 0.395)), black, col, root)
        add(f"DrumHandle_{i}", L.box_bm(0.03, 0.12, 0.05, (dx - 0.07, 0.03, 0.405)), mat, col, root,
            bev=(0.012, 3))
        add(f"DrumLabel_{i}", L.box_bm(0.16, 0.002, 0.12, (dx, -0.121, 0.2)), label, col, root)
        # suction tube from drum cap up to the pump
        bm = L.cylinder_bm(0.005, 0.88, 8, (dx + 0.06, 0.02, 0.84))
        add(f"Tube_{i}", bm, tube, col, root)
    return col.name


BUILDERS = {
    "Troffer": troffer,
    "LinenCart": linen_cart,
    "FoldingTable": folding_table,
    "WireShelving": wire_shelving,
    "DosingStation": detergent_station,
}
