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
    # Flat prismatic acrylic lens just above the flange (the classic backrooms panel),
    # with a thin inner trim; the lamp tubes read as two brighter bands through it.
    add("Lens", L.box_bm(w - 0.05, l - 0.05, 0.004, (0, 0, 0.012)), lens, col, root)
    for i, (sx, sy, cx, cy) in enumerate([(w - 0.04, 0.012, 0, -l / 2 + 0.026), (w - 0.04, 0.012, 0, l / 2 - 0.026),
                                          (0.012, l - 0.04, -w / 2 + 0.026, 0), (0.012, l - 0.04, w / 2 - 0.026, 0)]):
        add(f"Trim_{i}", L.box_bm(sx, sy, 0.016, (cx, cy, 0.006)), louvre, col, root, bev=(0.002, 2))
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


# ------------------------------------------------- traces of people (small props)

def _lump(bm, scale, amount, seed=0.0):
    from mathutils import noise
    for v in bm.verts:
        v.co += v.normal * amount * noise.fractal(v.co * scale + Vector((seed, seed * 0.7, 0)), 0.6, 2.0, 4)
    return bm


def laundry_basket():
    """Oval plastic laundry basket with slotted sides and clothes spilling over the rim."""
    col, root = start("LaundryBasket")
    plastic = L.material("Basket_Blue", base=(0.12, 0.3, 0.6), roughness=0.4, tex="plastic_matte", normal_strength=0.5,
                         vertex_color=True)
    cloth = L.material("Cloth_Mixed", base=(0.62, 0.55, 0.5), tex="towel", normal_strength=1.0, vertex_color=True)
    W, D, H = 0.58, 0.42, 0.27
    # Tapered oval tub: lathe-like ring of quads, open top, with slot holes as dark inset plates.
    bm = bmesh.new()
    rings = []
    for k, (z, s_) in enumerate(((0.0, 0.86), (0.02, 0.9), (H - 0.03, 1.0), (H, 1.04))):
        ring = []
        for i in range(40):
            a_ = 2 * math.pi * i / 40
            ring.append(bm.verts.new((math.cos(a_) * W / 2 * s_, math.sin(a_) * D / 2 * s_, z)))
        rings.append(ring)
    for k in range(3):
        for i in range(40):
            j = (i + 1) % 40
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    tub = add("Tub", bm, plastic, col, root, uv="box", texel=0.3, smooth=50)
    mod = tub.modifiers.new("Solid", "SOLIDIFY")
    mod.thickness = 0.006
    tub.modifiers.move(len(tub.modifiers) - 1, 0)
    rim = L.revolve_bm([(0.0, 0.0), (0.012, 0.0), (0.012, 0.012), (0.0, 0.012)], 8, True, (0, 0, 0))
    add("Rim", L.box_bm(W * 1.06, 0.02, 0.02, (0, -D / 2 * 1.04, H)), plastic, col, root, bev=(0.008, 2))
    add("Rim2", L.box_bm(W * 1.06, 0.02, 0.02, (0, D / 2 * 1.04, H)), plastic, col, root, bev=(0.008, 2))
    for i, x in enumerate((-W / 2 * 1.04, W / 2 * 1.04)):
        add(f"Handle_{i}", L.box_bm(0.03, 0.14, 0.035, (x, 0, H - 0.01)), plastic, col, root, bev=(0.01, 3))
    slots = L.material("Basket_SlotShadow", base=(0.01, 0.015, 0.03), roughness=0.8)
    for i in range(14):
        a_ = 2 * math.pi * (i + 0.5) / 14
        x, y = math.cos(a_) * W / 2 * 0.955, math.sin(a_) * D / 2 * 0.955
        o = add(f"Slot_{i:02d}", L.box_bm(0.012, 0.05, 0.12, (0, 0, 0)), slots, col, root)
        o.location = (x * 1.012, y * 1.012, 0.13)
        o.rotation_euler = (0, 0, a_)
    pile = _lump(L.box_bm(W * 0.85, D * 0.8, 0.22, (0, 0, H - 0.02)), 7, 0.05, 2)
    bmesh.ops.subdivide_edges(pile, edges=pile.edges[:], cuts=7, use_grid_fill=True)
    _lump(pile, 9, 0.04, 3)
    add("Clothes", pile, cloth, col, root, uv="box", texel=0.25, smooth=80,
        dirt=dict(seed=9, floor=-10, stain=0.4, stain_scale=0.06))
    # A shirt sleeve hanging over the rim.
    sleeve = _lump(L.cylinder_bm(0.035, 0.22, 12, (W / 2 + 0.02, 0.05, H - 0.06)), 12, 0.012, 4)
    add("Sleeve", sleeve, cloth, col, root, uv="box", texel=0.25, smooth=80)
    return col.name


def detergent_jug():
    """5 l HDPE detergent jug with an integrated handle, measuring cap and wraparound label."""
    col, root = start("DetergentJug")
    jug = L.material("Jug_Orange", base=(0.9, 0.42, 0.05), roughness=0.3, coat=0.3, tex="plastic_matte",
                     normal_strength=0.3, vertex_color=True)
    cap = L.material("Cap_White", base=(0.88, 0.88, 0.86), roughness=0.35)
    label = L.material("Label_Paper", base=(0.9, 0.9, 0.85), roughness=0.6)
    ink = L.material("Ink_Blue", base=(0.05, 0.15, 0.55), roughness=0.5)
    drip = L.material("Soap_Residue", base=(0.62, 0.72, 0.85), roughness=0.8, alpha=0.55)
    W, D, H = 0.22, 0.13, 0.3
    body = L.box_bm(W, D, H, (0, 0, H / 2))
    add("Body", body, jug, col, root, bev=(0.03, 5), uv="box", texel=0.3,
        dirt=dict(seed=31, floor=0.0, floor_band=0.05, floor_dark=0.7, stain=0.2, stain_scale=0.05))
    add("Shoulder", L.box_bm(W * 0.8, D * 0.85, 0.05, (0.0, 0, H + 0.02)), jug, col, root, bev=(0.02, 4), uv="box")
    add("Handle", L.box_bm(0.04, 0.05, 0.12, (W / 2 - 0.04, 0, H + 0.02)), jug, col, root, bev=(0.015, 3))
    add("HandleTop", L.box_bm(0.11, 0.05, 0.03, (W / 2 - 0.09, 0, H + 0.075)), jug, col, root, bev=(0.012, 3))
    add("Spout", L.cylinder_bm(0.03, 0.03, 24, (-W / 2 + 0.06, 0, H + 0.055)), jug, col, root)
    add("Cap", L.cylinder_bm(0.035, 0.05, 32, (-W / 2 + 0.06, 0, H + 0.09)), cap, col, root, bev=(0.006, 2, 30))
    add("Label", L.box_bm(W - 0.02, 0.002, 0.15, (0, -D / 2 - 0.0035, 0.13)), label, col, root)
    L.text_mesh("Brand", "BRITE", 0.04, ink, col, root, bold=True, location=(0, -D / 2 - 0.0065, 0.16))
    L.text_mesh("Sub", "HE LAUNDRY DETERGENT  5 L", 0.009, ink, col, root, location=(0, -D / 2 - 0.0065, 0.1))
    add("Drip", L.rounded_plate_bm(0.012, 0.08, 0.006, 0.0015, (-W / 2 + 0.03, -D / 2 - 0.004, 0.24), 4), drip, col,
        root)
    return col.name


def sock():
    """A single lost sock, crumpled."""
    col, root = start("LostSock")
    mat = L.material("Sock_Grey", base=(0.32, 0.32, 0.34), tex="towel", normal_strength=1.2, vertex_color=True)
    bm = L.cylinder_bm(0.035, 0.24, 16, (0, 0, 0.0), axis="Y")
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 0.01], cuts=6)
    for v in bm.verts:
        v.co.z = v.co.z * 0.35 + 0.012
        v.co.x += 0.04 * math.sin(v.co.y * 9)
    _lump(bm, 25, 0.008, 1)
    add("Sock", bm, mat, col, root, uv="box", texel=0.15, smooth=80,
        dirt=dict(seed=3, floor=-10, stain=0.4, stain_scale=0.05))
    return col.name


def dryer_sheet():
    col, root = start("DryerSheet")
    mat = L.material("DryerSheet", base=(0.9, 0.9, 0.92), roughness=0.8, tex="plastic_matte", normal_strength=0.8)
    bm = L.grid_bm(0.22, 0.17, 0.02, (-0.11, -0.085, 0.004), (1, 0, 0), (0, 1, 0))
    _lump(bm, 20, 0.01, 7)
    for v in bm.verts:
        v.co.z = max(v.co.z, 0.002)
    o = add("Sheet", bm, mat, col, root, uv="box", texel=0.2, smooth=80)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return col.name


def plastic_chair():
    """Moulded stacking chair: polypropylene shell on a chrome four-leg frame."""
    col, root = start("PlasticChair")
    shell = L.material("Chair_Shell", base=(0.42, 0.44, 0.45), roughness=0.45, tex="plastic_matte",
                       normal_strength=0.4, vertex_color=True)
    chrome = L.material("Chrome", base=(0.92, 0.92, 0.93), metallic=1.0, roughness=0.12)
    rubber = L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5)
    seat = L.box_bm(0.46, 0.44, 0.02, (0, 0.0, 0.45))
    bmesh.ops.subdivide_edges(seat, edges=seat.edges[:], cuts=4, use_grid_fill=True)
    for v in seat.verts:
        v.co.z -= 0.025 * (1 - (2 * v.co.x / 0.46) ** 2) * (1 - (2 * v.co.y / 0.44) ** 2)
    add("Seat", seat, shell, col, root, bev=(0.008, 3), uv="box",
        dirt=dict(seed=61, floor=0.0, floor_band=0.5, floor_dark=0.8, stain=0.3, stain_scale=0.1))
    back = L.box_bm(0.44, 0.02, 0.38, (0, 0.21, 0.69))
    for v in back.verts:
        v.co.y += (v.co.z - 0.5) * 0.18
    add("Back", back, shell, col, root, bev=(0.008, 3), uv="box",
        dirt=dict(seed=62, floor=0.0, stain=0.3, stain_scale=0.1))
    for i, (x, y) in enumerate(((-0.2, -0.18), (0.2, -0.18), (-0.2, 0.2), (0.2, 0.2))):
        leg = L.cylinder_bm(0.011, 0.45, 12, (x, y, 0.225))
        add(f"Leg_{i}", leg, chrome, col, root)
        add(f"Glide_{i}", L.cylinder_bm(0.014, 0.012, 12, (x, y, 0.006)), rubber, col, root)
    for i, x in enumerate((-0.2, 0.2)):
        add(f"BackPost_{i}", L.cylinder_bm(0.01, 0.3, 12, (x, 0.23, 0.6)), chrome, col, root)
    return col.name


def lint_bin():
    """Round grey waste bin overflowing with lint and used dryer sheets."""
    col, root = start("LintBin")
    bin_m = L.material("Bin_Grey", base=(0.28, 0.29, 0.3), roughness=0.5, tex="plastic_matte", normal_strength=0.5,
                       vertex_color=True)
    lint = L.material("Lint_Grey", base=(0.55, 0.53, 0.52), tex="towel", normal_strength=1.5)
    sheet = L.material("DryerSheet", base=(0.9, 0.9, 0.92), roughness=0.8, tex="plastic_matte", normal_strength=0.8)
    prof = [(0.17, 0.0), (0.2, 0.62), (0.215, 0.64), (0.215, 0.66), (0.2, 0.66), (0.185, 0.64), (0.155, 0.02),
            (0.0, 0.02)]
    bm = bmesh.new()
    rings = []
    for i in range(48):
        a_ = 2 * math.pi * i / 48
        rings.append([bm.verts.new((r * math.cos(a_), r * math.sin(a_), z)) for r, z in prof])
    for i in range(48):
        a1, b1 = rings[i], rings[(i + 1) % 48]
        for j in range(len(prof) - 1):
            bm.faces.new((a1[j], a1[j + 1], b1[j + 1], b1[j]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    add("Bin", bm, bin_m, col, root, uv="box", texel=0.3, smooth=50,
        dirt=dict(seed=71, floor=0.0, floor_band=0.2, floor_dark=0.6, stain=0.4, stain_scale=0.08))
    heap = _lump(L.cylinder_bm(0.19, 0.12, 24, (0, 0, 0.66)), 14, 0.03, 5)
    bmesh.ops.subdivide_edges(heap, edges=heap.edges[:], cuts=2)
    _lump(heap, 22, 0.015, 6)
    add("Lint", heap, lint, col, root, uv="box", texel=0.1, smooth=80)
    for i, (x, y, r) in enumerate(((0.06, 0.02, 20), (-0.08, -0.05, -35), (0.0, 0.1, 60))):
        g = L.grid_bm(0.16, 0.12, 0.02, (-0.08, -0.06, 0), (1, 0, 0), (0, 1, 0))
        _lump(g, 18, 0.015, i)
        o = add(f"Sheet_{i}", g, sheet, col, root, smooth=80)
        o.location = (x, y, 0.73 + i * 0.01)
        o.rotation_euler = (math.radians(r * 0.5), math.radians(r * 0.3), math.radians(r))
    return col.name


def wet_floor_sign():
    """Yellow A-frame 'CAUTION WET FLOOR' sign, opened on the floor."""
    col, root = start("WetFloorSign")
    yellow = L.material("Sign_Yellow", base=(0.95, 0.7, 0.04), roughness=0.4, tex="plastic_matte", normal_strength=0.3,
                        vertex_color=True)
    ink = L.material("Ink_Black", base=(0.02, 0.02, 0.02), roughness=0.6)
    for side, sgn in (("F", -1), ("B", 1)):
        panel = L.box_bm(0.3, 0.012, 0.62, (0, 0, 0.31))
        bmesh.ops.rotate(panel, verts=panel.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(sgn * 11), 3, "X"))
        bmesh.ops.translate(panel, vec=Vector((0, sgn * 0.06, 0)), verts=panel.verts)
        add(f"Panel{side}", panel, yellow, col, root, bev=(0.01, 3), uv="box",
            dirt=dict(seed=81, floor=0.0, floor_band=0.2, floor_dark=0.6, stain=0.3, stain_scale=0.1))
    for i, (t, sz, z) in enumerate((("CAUTION", 0.045, 0.52), ("WET FLOOR", 0.035, 0.2), ("PISO MOJADO", 0.022, 0.14))):
        o = L.text_mesh(f"Text_{i}", t, sz, ink, col, root, bold=(i < 2),
                        location=(0, -0.06 - 0.008 - (0.62 - z) * math.sin(math.radians(11)) * 0 - 0.0065 - (z - 0.31) * -math.tan(math.radians(11)), z),
                        rotation=(math.radians(90 - 11), 0, 0))
    add("Figure", L.box_bm(0.07, 0.003, 0.12, (0, -0.06 - 0.0075 + (0.36 - 0.31) * math.tan(math.radians(11)), 0.36)),
        ink, col, root)
    bpy.data.objects["Figure"].rotation_euler = (math.radians(-11), 0, 0)
    add("TopHandle", L.box_bm(0.12, 0.05, 0.03, (0, 0, 0.635)), yellow, col, root, bev=(0.01, 3))
    return col.name


def mop_bucket():
    """Yellow commercial mop bucket with a wringer and a mop leaning in it."""
    col, root = start("MopBucket")
    yellow = L.material("Bucket_Yellow", base=(0.9, 0.65, 0.05), roughness=0.4, tex="plastic_matte",
                        normal_strength=0.4, vertex_color=True)
    grey = L.material("Wringer_Grey", base=(0.35, 0.36, 0.37), roughness=0.4)
    water = L.material("Water_Dirty", base=(0.18, 0.17, 0.12), roughness=0.05, alpha=0.85)
    mop = L.material("Mop_Strands", base=(0.75, 0.72, 0.62), tex="towel", normal_strength=1.5, vertex_color=True)
    pole = L.material("Pole_Blue", base=(0.1, 0.25, 0.6), metallic=0.5, roughness=0.3)
    rubber = L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5)
    add("Bucket", L.box_bm(0.4, 0.3, 0.3, (0, 0, 0.19), skip=("+z",)), yellow, col, root, bev=(0.04, 4), uv="box",
        dirt=dict(seed=91, floor=0.0, floor_band=0.15, floor_dark=0.6, stain=0.5, stain_scale=0.08))
    add("Water", L.box_bm(0.37, 0.27, 0.005, (0, 0, 0.26)), water, col, root)
    for i, (x, y) in enumerate(((-0.17, -0.12), (0.17, -0.12), (-0.17, 0.12), (0.17, 0.12))):
        add(f"Caster_{i}", L.cylinder_bm(0.025, 0.02, 16, (x, y, 0.025), axis="X"), rubber, col, root)
    add("Wringer", L.box_bm(0.2, 0.16, 0.16, (0, 0.06, 0.42)), grey, col, root, bev=(0.02, 3))
    add("WringerLever", L.cylinder_bm(0.012, 0.55, 12, (0.12, 0.08, 0.68)), grey, col, root)
    add("MopPole", L.cylinder_bm(0.013, 1.35, 12, (-0.05, -0.02, 0.9)), pole, col, root)
    bpy.data.objects["MopPole"].rotation_euler = (math.radians(-12), math.radians(8), 0)
    strands = _lump(L.cylinder_bm(0.09, 0.16, 16, (-0.05, -0.02, 0.24)), 30, 0.02, 8)
    add("MopHead", strands, mop, col, root, uv="box", texel=0.15, smooth=80,
        dirt=dict(seed=92, floor=-10, stain=0.6, stain_scale=0.05))
    return col.name


def clothes_rack():
    """Chrome rolling garment rack with a few wire hangers, one shirt left behind."""
    col, root = start("ClothesRack")
    chrome = L.material("Chrome", base=(0.92, 0.92, 0.93), metallic=1.0, roughness=0.12)
    wire = L.material("Hanger_Wire", base=(0.7, 0.7, 0.7), metallic=1.0, roughness=0.3)
    shirt = L.material("Shirt_White", base=(0.86, 0.86, 0.88), tex="plastic_matte", normal_strength=0.8,
                       vertex_color=True)
    rubber = L.material("Rubber_Black", base=(0.018, 0.018, 0.018), tex="rubber", normal_strength=0.5)
    W, H = 1.2, 1.6
    for i, x in enumerate((-W / 2, W / 2)):
        add(f"Upright_{i}", L.cylinder_bm(0.014, H, 12, (x, 0, H / 2 + 0.05)), chrome, col, root)
        add(f"Foot_{i}", L.cylinder_bm(0.012, 0.5, 12, (x, 0, 0.06), axis="Y"), chrome, col, root)
        for j, y in enumerate((-0.25, 0.25)):
            add(f"Wheel_{i}{j}", L.cylinder_bm(0.03, 0.02, 16, (x, y, 0.03), axis="X"), rubber, col, root)
    add("Rail", L.cylinder_bm(0.014, W + 0.03, 12, (0, 0, H + 0.05), axis="X"), chrome, col, root)
    for k in range(7):
        x = -0.45 + k * 0.13
        hook = L.revolve_bm([(0.018, -0.002), (0.02, -0.002), (0.02, 0.002), (0.018, 0.002)], 12, True, (0, 0, 0))
        o = add(f"HangerHook_{k}", hook, wire, col, root)
        o.location = (x, 0, H + 0.05)
        o.rotation_euler = (0, math.radians(90), 0)
        tri = bmesh.new()
        vs = [tri.verts.new(p) for p in ((x, -0.2, H - 0.12), (x, 0.2, H - 0.12), (x, 0, H + 0.02))]
        for a_, b_ in ((0, 1), (1, 2), (2, 0)):
            e = L.cylinder_bm(0.0018, (vs[a_].co - vs[b_].co).length, 6, (0, 0, 0))
            mid = (vs[a_].co + vs[b_].co) / 2
            q = (vs[b_].co - vs[a_].co).to_track_quat("Z", "Y")
            bmesh.ops.transform(e, matrix=Matrix.Translation(mid) @ q.to_matrix().to_4x4(), verts=e.verts)
            add(f"Hanger_{k}_{a_}", e, wire, col, root)
        tri.free()
    body = _lump(L.box_bm(0.03, 0.42, 0.62, (-0.32, 0, H - 0.45)), 8, 0.012, 2)
    bmesh.ops.subdivide_edges(body, edges=body.edges[:], cuts=5, use_grid_fill=True)
    _lump(body, 10, 0.01, 3)
    add("Shirt", body, shirt, col, root, uv="box", texel=0.3, smooth=80,
        dirt=dict(seed=95, floor=-10, stain=0.2, stain_scale=0.08))
    return col.name


BUILDERS = {
    "Troffer": troffer,
    "LinenCart": linen_cart,
    "FoldingTable": folding_table,
    "WireShelving": wire_shelving,
    "DosingStation": detergent_station,
    "LaundryBasket": laundry_basket,
    "DetergentJug": detergent_jug,
    "LostSock": sock,
    "DryerSheet": dryer_sheet,
    "PlasticChair": plastic_chair,
    "LintBin": lint_bin,
    "WetFloorSign": wet_floor_sign,
    "MopBucket": mop_bucket,
    "ClothesRack": clothes_rack,
}
