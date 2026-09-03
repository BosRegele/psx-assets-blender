"""Runs INSIDE Blender via the addon's execute_code bridge.

Meshes are built from explicit vertex/face/UV lists rather than modelled with
operators. At this triangle budget that is less code, not more, and it is the
only way to hit the texture atlas exactly - smart-unwrap would scatter the
islands and break the shared-atlas contract in textures.py.
"""
import bpy, bmesh, math, os, sys

sys.path.insert(0, "D:/PSX-Props/tools")
import importlib
import geometry as P
importlib.reload(P)   # Blender keeps modules alive between runs; always re-read

TEX = "D:/PSX-Props/assets/textures"
OUT = "D:/PSX-Props/exports"
TAU = math.pi * 2


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def make(name, verts, faces, face_uvs):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    i = 0
    for poly_uvs in face_uvs:
        for u, v in poly_uvs:
            uv.data[i].uv = (u, v)
            i += 1
    # PSX shading is flat and unlit-looking; no smooth normals anywhere
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def material(ob, png, name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(png, check_existing=True)
    tex.interpolation = "Closest"      # the single most important setting here
    tex.extension = "REPEAT"
    tex.location = (-400, 200)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    ob.data.materials.append(mat)
    return mat


# --- canned food -----------------------------------------------------------
def build_can(N=12):
    """Body wraps U 0..1 over the true circumference; lid and base discs use
    their real texel radius. Density is P.CAN_DENSITY everywhere."""
    r, h = P.CAN_R, P.CAN_H
    w, th = P.CAN_TEX
    v_body = 1.0 - P.CAN_BODY_ROWS / th
    verts, faces, uvs = [], [], []
    for z in (0.0, h):
        for i in range(N):
            a = TAU * i / N
            verts.append((r * math.cos(a), r * math.sin(a), z))
    verts += [(0, 0, 0.0), (0, 0, h)]
    cb, ct = 2 * N, 2 * N + 1

    for i in range(N):
        j = (i + 1) % N
        faces.append((i, j, N + j, N + i))
        uvs.append([(i / N, v_body), ((i + 1) / N, v_body),
                    ((i + 1) / N, 1.0), (i / N, 1.0)])

    dr = P.CAN_DISC_R
    rad = dr / w
    cy = 1.0 - P.CAN_DISC_Y / th
    for cx, centre, ring, flip in (((dr + 2) / w, ct, N, False),
                                   ((3 * dr + 6) / w, cb, 0, True)):
        for i in range(N):
            j = (i + 1) % N
            ai, aj = TAU * i / N, TAU * j / N
            p = (cx + rad * math.cos(ai), cy + rad * math.sin(ai))
            q = (cx + rad * math.cos(aj), cy + rad * math.sin(aj))
            if flip:
                faces.append((centre, ring + j, ring + i)); uvs.append([(cx, cy), q, p])
            else:
                faces.append((centre, ring + i, ring + j)); uvs.append([(cx, cy), p, q])
    return make("SM_Can_Food_01", verts, faces, uvs)


# --- vodka bottle ----------------------------------------------------------
def build_bottle(N=12):
    """The fix for stretched texels.

    V advances with arc length along the profile, so a centimetre of glass gets
    the same number of texture rows wherever it sits. U spans only r/R_body of
    the texture width, so the narrow neck does not smear the full 128px across
    its 8cm circumference. Together these give square texels from cap to base;
    the price is a little shear across the two shoulder rings, which is why the
    shoulder has an extra ring to soften it.
    """
    prof, rows, th = P.BOTTLE_PROFILE, P.BOTTLE_ROWS, P.BOTTLE_TEX[1]
    rings = prof[1:-1]
    ring_rows = rows[1:-1]
    verts, faces, uvs = [], [], []
    for r, z in rings:
        for i in range(N):
            a = TAU * i / N
            verts.append((r * math.cos(a), r * math.sin(a), z))
    top = len(verts); verts.append((0, 0, prof[0][1]))
    bot = len(verts); verts.append((0, 0, prof[-1][1]))

    v = lambda row: 1.0 - row / th
    us = lambda r: r / P.BOTTLE_R

    for k in range(len(rings) - 1):
        v0, v1 = v(ring_rows[k]), v(ring_rows[k + 1])
        s0, s1 = us(rings[k][0]), us(rings[k + 1][0])
        for i in range(N):
            j = (i + 1) % N
            a, b = k * N + i, k * N + j
            c, dd = (k + 1) * N + j, (k + 1) * N + i
            faces.append((a, b, c, dd))
            uvs.append([(i / N * s0, v0), ((i + 1) / N * s0, v0),
                        ((i + 1) / N * s1, v1), (i / N * s1, v1)])

    s_top, s_bot = us(rings[0][0]), us(rings[-1][0])
    for i in range(N):
        j = (i + 1) % N
        faces.append((top, i, j))
        uvs.append([(s_top / 2, v(rows[0])), (i / N * s_top, v(ring_rows[0])),
                    ((i + 1) / N * s_top, v(ring_rows[0]))])
    base = (len(rings) - 1) * N
    for i in range(N):
        j = (i + 1) % N
        faces.append((bot, base + j, base + i))
        uvs.append([(s_bot / 2, v(rows[-1])),
                    ((i + 1) / N * s_bot, v(ring_rows[-1])),
                    (i / N * s_bot, v(ring_rows[-1]))])
    return make("SM_Bottle_Vodka_01", verts, faces, uvs)


# --- cigarette pack --------------------------------------------------------
def build_pack():
    x, y, h = P.PACK_W / 2, P.PACK_D / 2, P.PACK_H
    w, th = P.PACK_TEX
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0),
             (-x, -y, h), (x, -y, h), (x, y, h), (-x, y, h)]
    def R(key):
        x0, y0, x1, y1 = P.PACK_ATLAS[key]
        return x0 / w, 1 - y1 / th, x1 / w, 1 - y0 / th
    spec = [((0, 1, 5, 4), R("front")), ((2, 3, 7, 6), R("back")),
            ((3, 0, 4, 7), R("left")),  ((1, 2, 6, 5), R("right")),
            ((4, 5, 6, 7), R("top")),   ((3, 2, 1, 0), R("bottom"))]
    faces, uvs = [], []
    for f, (u0, v0, u1, v1) in spec:
        faces.append(f)
        uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    return make("SM_Pack_Cigarettes_01", verts, faces, uvs)


def export(ob, stem):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=f"{OUT}/{stem}.fbx", use_selection=True,
                             apply_scale_options="FBX_SCALE_ALL",
                             mesh_smooth_type="FACE", path_mode="COPY",
                             embed_textures=True)
    bpy.ops.export_scene.gltf(filepath=f"{OUT}/{stem}.glb", use_selection=True,
                              export_format="GLB")


def main():
    clear()
    os.makedirs(OUT, exist_ok=True)
    jobs = [(build_can, "can", "SM_Can_Food_01", -0.14),
            (build_bottle, "bottle", "SM_Bottle_Vodka_01", 0.0),
            (build_pack, "pack", "SM_Pack_Cigarettes_01", 0.14)]
    report = []
    for fn, tex, stem, xoff in jobs:
        ob = fn()
        material(ob, f"{TEX}/{tex}_d.png", f"MI_{stem}")
        ob.location.x = xoff
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        export(ob, stem)
        report.append(f"{stem}: {tris} tris, {len(ob.data.vertices)} verts")
    return "\n".join(report)


print(main())
