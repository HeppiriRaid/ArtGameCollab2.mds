"""Shared helpers for modelling the hotel laundry props in Blender 5.x.

Conventions
- Metres, Z up, the prop's front faces -Y, origin at floor level.
- Every prop is parented to one empty named after the prop, inside a
  collection of the same name; that collection is what gets exported.
- Textures are image based (no procedural nodes) so the glTF export carries
  them into Unity. Tiling is baked into UVs (TEXEL metres per texture tile).
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

TEX_DIR = os.path.expanduser("~/Documents/Blender/HotelLaundry/textures")
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


# ---------------------------------------------------------------- scene setup

def collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def clear_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        return
    for obj in list(col.all_objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)


def root_empty(name, col):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.3
    col.objects.link(empty)
    return empty


def link(obj, col, parent=None):
    col.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


# ------------------------------------------------------------------ materials

def _tex_path(stem):
    for ext in (".png", ".jpg"):
        path = os.path.join(TEX_DIR, stem + ext)
        if os.path.exists(path):
            return path
    return None


def _image(stem, non_color):
    path = _tex_path(stem)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    return img


def material(name, base=(0.8, 0.8, 0.8), metallic=0.0, roughness=0.5,
             tex=None, normal_strength=1.0, emission=None, emission_strength=0.0,
             alpha=1.0, ior=1.5, coat=0.0, vertex_color=False, tint=None):
    """Principled material, optionally driven by `<tex>_basecolor/_roughness/_normal` images.

    vertex_color multiplies the "Col" attribute into the base colour (exported as
    glTF COLOR_0, which Unity's glTF shader multiplies too): used for grime.
    tint multiplies a constant colour into a textured base colour.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Coat Weight"].default_value = coat
    base_socket = bsdf.inputs["Base Color"]
    if vertex_color:
        attr = nt.nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "Col"
        attr.location = (-600, 600)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs["A"].default_value = (*base, 1.0)
        mix.location = (-250, 450)
        nt.links.new(attr.outputs["Color"], mix.inputs["B"])
        nt.links.new(mix.outputs["Result"], base_socket)
        base_socket = mix.inputs["A"]
    if tex:
        y = 300
        for suffix, non_color in (("basecolor", False), ("roughness", True), ("normal", True)):
            if _tex_path(f"{tex}_{suffix}") is None:
                continue
            node = nt.nodes.new("ShaderNodeTexImage")
            node.image = _image(f"{tex}_{suffix}", non_color)
            node.location = (-600, y)
            y -= 300
            if suffix == "basecolor":
                if tint is not None:
                    tmix = nt.nodes.new("ShaderNodeMix")
                    tmix.data_type = "RGBA"
                    tmix.blend_type = "MULTIPLY"
                    tmix.inputs["Factor"].default_value = 1.0
                    tmix.inputs["B"].default_value = (*tint, 1.0)
                    nt.links.new(node.outputs["Color"], tmix.inputs["A"])
                    nt.links.new(tmix.outputs["Result"], base_socket)
                else:
                    nt.links.new(node.outputs["Color"], base_socket)
            elif suffix == "roughness":
                nt.links.new(node.outputs["Color"], bsdf.inputs["Roughness"])
            else:
                nmap = nt.nodes.new("ShaderNodeNormalMap")
                nmap.location = (-250, y + 300)
                nmap.inputs["Strength"].default_value = normal_strength
                nt.links.new(node.outputs["Color"], nmap.inputs["Color"])
                nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = "BLENDED"
        mat.use_backface_culling = False
    return mat


# ---------------------------------------------------------------- mesh basics

def mesh_object(name, bm, mat=None, smooth_angle=35.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat is not None:
        me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return bpy.data.objects.new(name, me)


def box_bm(sx, sy, sz, center=(0, 0, 0), skip=()):
    """Axis aligned box. `skip` holds face directions to leave open: '-y', '+z', ..."""
    bm = bmesh.new()
    cx, cy, cz = center
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [bm.verts.new((cx + x * hx, cy + y * hy, cz + z * hz))
         for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    # Vertex index = 4*x + 2*y + z (each 0 for -1, 1 for +1); windings face outward.
    faces = {
        "-x": (0, 1, 3, 2), "+x": (4, 6, 7, 5),
        "-y": (0, 4, 5, 1), "+y": (2, 3, 7, 6),
        "-z": (0, 2, 6, 4), "+z": (1, 5, 7, 3),
    }
    for key, idx in faces.items():
        if key not in skip:
            bm.faces.new([v[i] for i in idx])
    bm.normal_update()
    return bm


def grid_bm(size_u, size_v, step, origin, axis_u, axis_v):
    """Flat grid of quads (`step` metres) spanning size_u x size_v.

    origin is the grid corner; axis_u / axis_v are unit Vectors along its edges.
    Normals follow axis_u x axis_v.
    """
    bm = bmesh.new()
    nu, nv = max(1, round(size_u / step)), max(1, round(size_v / step))
    o, au, av = Vector(origin), Vector(axis_u), Vector(axis_v)
    rows = [[bm.verts.new(o + au * (size_u * i / nu) + av * (size_v * j / nv)) for i in range(nu + 1)]
            for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    bm.normal_update()
    return bm


def grime(obj, seed=0, floor=0.0, floor_band=0.35, floor_dark=0.62, stain=0.35, stain_scale=1.6,
          ceiling=None, ceiling_band=0.6, drip=0.0):
    """Paint a "Col" vertex colour layer: dark band near the floor, blotchy stains,
    optional darkening toward the ceiling and vertical drip streaks.
    Works in world space so neighbouring pieces match."""
    from mathutils import noise
    me = obj.data
    col = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    mw = obj.matrix_world
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            v = 1.0
            h = p.z - floor
            if h < floor_band:
                v *= floor_dark + (1 - floor_dark) * max(0.0, h / floor_band) ** 0.7
            n = noise.fractal(p / stain_scale + off, 0.6, 2.2, 4)
            v *= 1.0 - stain * max(0.0, n) ** 1.3
            if drip > 0:
                d = noise.noise(Vector((p.x * 9 + off.x, p.y * 9 + off.y, p.z * 0.35)))
                v *= 1.0 - drip * max(0.0, d) ** 2
            if ceiling is not None and ceiling - p.z < ceiling_band:
                v *= 0.85 + 0.15 * (ceiling - p.z) / ceiling_band
            v = max(0.0, min(1.0, v))
            tint = (v, v * 0.985, v * 0.95, 1.0)     # grime is warm, not grey
            col.data[li].color = tint
    me.color_attributes.active_color = col
    return col


def cylinder_bm(radius, depth, segments=32, center=(0, 0, 0), axis="Z", caps=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    rot = {"Z": Matrix(), "Y": Matrix.Rotation(math.radians(90), 4, "X"),
           "X": Matrix.Rotation(math.radians(90), 4, "Y")}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot, verts=bm.verts)
    return bm


def rounded_plate_bm(w, h, radius, thickness, center=(0, 0, 0), segments=8, facing="-y"):
    """Plate with rounded corners: w along X, h along Z, extruded toward `facing`.

    facing '-y' / '+y' for front/back faces, '-x' / '+x' for side faces.
    """
    bm = bmesh.new()
    hw, hh = w / 2, h / 2
    verts = [bm.verts.new(co) for co in ((-hw, 0, -hh), (hw, 0, -hh), (hw, 0, hh), (-hw, 0, hh))]
    bm.faces.new(verts)
    bmesh.ops.bevel(bm, geom=verts, offset=radius, segments=segments, affect="VERTICES",
                    profile=0.5, profile_type="SUPERELLIPSE")   # 0.5 = round corner
    ext = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
    moved = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, -thickness, 0)), verts=moved)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rot = {"-y": Matrix(), "+y": Matrix.Rotation(math.pi, 4, "Z"),
           "-x": Matrix.Rotation(-math.pi / 2, 4, "Z"), "+x": Matrix.Rotation(math.pi / 2, 4, "Z")}[facing]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot, verts=bm.verts)
    return bm


def triangulate(obj):
    """Last modifier: avoids n-gon tangent errors in the glTF export."""
    mod = obj.modifiers.new("Triangulate", "TRIANGULATE")
    if hasattr(mod, "keep_custom_normals"):   # removed in newer Blender, always kept there
        mod.keep_custom_normals = True
    mod.quad_method = "BEAUTY"
    mod.min_vertices = 5                      # only n-gons; quads tangent fine
    return mod


def revolve_bm(profile, segments=64, closed=True, center=(0, 0, 0)):
    """Lathe a (radius, y) profile around the Y axis, then move to `center`.

    Points are walked in order; `closed` joins the last back to the first.
    """
    bm = bmesh.new()
    rings = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((center[0] + r * ca, center[1] + y, center[2] + r * sa))
                      for r, y in profile])
    n = len(profile)
    last = n if closed else n - 1
    for i in range(segments):
        a, b = rings[i], rings[(i + 1) % segments]
        for j in range(last):
            k = (j + 1) % n
            verts = [a[j], a[k], b[k], b[j]]
            if len(set(verts)) == 4:
                bm.faces.new(verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ------------------------------------------------------------------------- UV

def box_uv(obj, texel=0.5):
    """World-scale box projection; `texel` metres per texture tile.

    Front/back faces map X->U, Z->V; sides Y->U, Z->V; top/bottom X->U, Y->V,
    so brushed-metal streaks run horizontally on every visible face.
    """
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y, co.z
            elif ax == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            uv.data[li].uv = (u / texel, v / texel)


def cylinder_uv(obj, axis="Y", texel=0.5, radius=None):
    """Wrap U around `axis`, V along it."""
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    ai = "XYZ".index(axis)
    oth = [i for i in range(3) if i != ai]
    for poly in me.polygons:
        loops = list(poly.loop_indices)
        angs = []
        for li in loops:
            co = me.vertices[me.loops[li].vertex_index].co
            angs.append(math.atan2(co[oth[1]], co[oth[0]]))
        # keep each face continuous across the -pi/pi seam
        ref = angs[0]
        for li, a in zip(loops, angs):
            while a - ref > math.pi:
                a -= 2 * math.pi
            while a - ref < -math.pi:
                a += 2 * math.pi
            co = me.vertices[me.loops[li].vertex_index].co
            r = radius if radius else math.hypot(co[oth[0]], co[oth[1]])
            uv.data[li].uv = (a * r / texel, co[ai] / texel)


# ------------------------------------------------------------------ modifiers

def bevel(obj, width=0.004, segments=3, angle=40.0, harden=True):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle)
    mod.harden_normals = harden
    mod.miter_outer = "MITER_ARC"
    return mod


def weighted_normals(obj):
    mod = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    return mod


def boolean_cut(obj, cutter_bm):
    """Subtract a temporary cutter mesh from `obj` and apply immediately."""
    cutter = mesh_object(obj.name + "_cutter", cutter_bm)
    bpy.context.scene.collection.objects.link(cutter)
    cutter.matrix_world = Matrix()
    mod = obj.modifiers.new("Cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    apply_modifiers(obj, only=("Cut",))
    me = cutter.data
    bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.data.meshes.remove(me)


def apply_modifiers(obj, only=None):
    """Bake (some) modifiers into the mesh without needing operator context."""
    keep = [m for m in obj.modifiers if only is not None and m.name not in only]
    states = [(m, m.show_viewport) for m in keep]
    for m in keep:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True,
                                          depsgraph=dg)
    for m, s in states:
        m.show_viewport = s
    old = obj.data
    obj.data = new
    new.name = old.name
    for m in list(obj.modifiers):
        if only is None or m.name in only:
            obj.modifiers.remove(m)
    if old.users == 0:
        bpy.data.meshes.remove(old)


# ----------------------------------------------------------------------- text

def _font(path):
    if os.path.exists(path):
        return bpy.data.fonts.load(path, check_existing=True)
    return None


def text_mesh(name, body, size, mat, col, parent=None, bold=False, extrude=0.0,
              align="CENTER", location=(0, 0, 0), rotation=(math.radians(90), 0, 0)):
    """Flat text converted to a mesh (glTF can't export font curves). Faces -Y by default.

    Flat and low curve resolution: printed labels don't need depth, and extruded
    small text costs thousands of triangles per word.
    """
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.resolution_u = 2 if size < 0.015 else 4
    cu.align_x = align
    cu.align_y = "CENTER"
    font = _font(FONT_BOLD if bold else FONT_REGULAR)
    if font:
        cu.font = font
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)
    me.name = name
    me.materials.clear()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    obj.rotation_euler = rotation
    return link(obj, col, parent)


# --------------------------------------------------------------------- export

def _group_of(obj, keep_separate):
    """The keep_separate pivot this object hangs under (matched without Blender's
    .001 suffixes, since every prop has its own "Door"), or None."""
    p = obj
    while p is not None:
        if p.name.split(".")[0] in keep_separate:
            return p
        p = p.parent
    return None


def merged_copy(col_name, keep_separate=(), tmp_name="_Export"):
    """Copy a prop into `tmp_name` as few objects as possible.

    All meshes are modifier-applied and joined into one object (one glTF mesh,
    one primitive per material). Each hierarchy under an empty named in
    keep_separate (e.g. "Door") becomes its own object, origin at that empty, so
    it can still move in Unity. Returns the temp collection name.
    """
    src = bpy.data.collections[col_name]
    # Objects in a viewport-hidden collection are not evaluated, so their
    # matrix_world is stale; make it visible and refresh before reading it.
    src.hide_viewport = False
    bpy.context.view_layer.update()
    clear_collection(tmp_name)
    tmp = collection(tmp_name)
    root_src = next(o for o in src.objects if o.parent is None)
    root = root_empty(root_src.name, tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    groups = {}
    for obj in src.all_objects:
        if obj.type != "MESH":
            continue
        me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.transform(obj.matrix_world)
        if "Col" not in me.color_attributes:
            # Joining fills a missing layer with black, and glTF multiplies COLOR_0
            # into every primitive, so ungrimed parts must be explicitly white.
            c = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
            c.data.foreach_set("color", [1.0] * (4 * len(c.data)))
        copy = bpy.data.objects.new(obj.name + "_m", me)
        tmp.objects.link(copy)
        groups.setdefault(_group_of(obj, keep_separate), []).append(copy)
    # Marker empties (WasherSlot_03, SideDoorTrigger, ...) survive as plain nodes.
    for obj in src.all_objects:
        if obj.type == "EMPTY" and ("Slot" in obj.name or "Trigger" in obj.name):
            e = bpy.data.objects.new(obj.name, None)
            tmp.objects.link(e)
            e.parent = root
            e.matrix_world = obj.matrix_world.copy()
    out = []
    for key, objs in groups.items():
        active = objs[0]
        if len(objs) > 1:
            with bpy.context.temp_override(active_object=active, object=active,
                                           selected_objects=objs, selected_editable_objects=objs):
                bpy.ops.object.join()
        if key is None:
            active.name = root_src.name + "_Body"
            active.data.name = active.name
        else:
            pivot = key.matrix_world.copy()
            active.data.transform(pivot.inverted())
            active.matrix_world = pivot
            active.name = key.name.split(".")[0]
            active.data.name = active.name
        world = active.matrix_world.copy()
        active.parent = root
        active.matrix_world = world
        out.append(active.name)
    return tmp_name, out


def export_glb(col_name, path, keep_separate=None):
    """Export one collection as .glb with modifiers applied and textures embedded.

    With keep_separate (a tuple, may be empty) the prop is first merged by
    merged_copy(); the temp copy is removed afterwards.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = None
    if keep_separate is not None:
        tmp, _ = merged_copy(col_name, keep_separate)
        col_name = tmp
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_active_collection=False,
        collection=col_name,
        export_vertex_color="MATERIAL",
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials="EXPORT",
        export_image_format="JPEG",      # ~4x smaller than PNG; no alpha textures are used
        export_jpeg_quality=88,
        export_yup=True,
        export_extras=False,
        export_lights=False,
        export_cameras=False,
    )
    if tmp is not None:
        clear_collection(tmp)
        bpy.data.collections.remove(bpy.data.collections[tmp])
    return os.path.getsize(path)
