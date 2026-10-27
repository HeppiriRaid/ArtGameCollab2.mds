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

def _image(name, non_color):
    path = os.path.join(TEX_DIR, name + ".png")
    img = bpy.data.images.get(name + ".png")
    if img is None or img.filepath != path:
        img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    return img


def material(name, base=(0.8, 0.8, 0.8), metallic=0.0, roughness=0.5,
             tex=None, normal_strength=1.0, emission=None, emission_strength=0.0,
             alpha=1.0, ior=1.5, coat=0.0):
    """Principled material, optionally driven by `<tex>_basecolor/_roughness/_normal` PNGs."""
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
    if tex:
        y = 300
        for suffix, non_color in (("basecolor", False), ("roughness", True), ("normal", True)):
            path = os.path.join(TEX_DIR, f"{tex}_{suffix}.png")
            if not os.path.exists(path):
                continue
            node = nt.nodes.new("ShaderNodeTexImage")
            node.image = _image(f"{tex}_{suffix}", non_color)
            node.location = (-600, y)
            y -= 300
            if suffix == "basecolor":
                nt.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
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
    faces = {
        "-x": (0, 1, 3, 2), "+x": (4, 6, 7, 5),
        "-y": (0, 2, 6, 4), "+y": (1, 5, 7, 3),
        "-z": (0, 4, 5, 1), "+z": (2, 3, 7, 6),
    }
    for key, idx in faces.items():
        if key not in skip:
            bm.faces.new([v[i] for i in idx])
    bm.normal_update()
    return bm


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

def export_glb(col_name, path):
    """Export one collection as .glb with modifiers applied and textures embedded."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_active_collection=False,
        collection=col_name,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_yup=True,
        export_extras=False,
        export_lights=False,
        export_cameras=False,
    )
    return os.path.getsize(path)
