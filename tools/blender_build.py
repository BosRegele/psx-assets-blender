"""Runs INSIDE Blender via the addon's execute_code bridge.

Meshes are built from explicit vertex/face/UV lists rather than modelled with
operators. At this triangle budget that is less code, not more, and it is the
only way to hit the texture atlas exactly - smart-unwrap would scatter the
islands and break the shared-atlas contract in textures.py.
"""
import bpy, bmesh, math, os

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
def build_can(N=12, r=0.037, h=0.102):
    """Atlas: body v 0.375..1.0 ; lid disc at (.1875,.1875) ; base at (.5625,.1875)"""
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
        u0, u1 = i / N, (i + 1) / N
        uvs.append([(u0, 0.375), (u1, 0.375), (u1, 1.0), (u0, 1.0)])

    for cx, cy, centre, ring, flip in ((0.1875, 0.1875, ct, N, False),
                                       (0.5625, 0.1875, cb, 0, True)):
        rad = 11 / 64
        for i in range(N):
            j = (i + 1) % N
            a_i, a_j = TAU * i / N, TAU * j / N
            p = (cx + rad * math.cos(a_i), cy + rad * math.sin(a_i))
            q = (cx + rad * math.cos(a_j), cy + rad * math.sin(a_j))
            if flip:
                faces.append((centre, ring + j, ring + i))
                uvs.append([(cx, cy), q, p])
            else:
                faces.append((centre, ring + i, ring + j))
                uvs.append([(cx, cy), p, q])
    return make("SM_Can_Food_01", verts, faces, uvs)


# --- vodka bottle ----------------------------------------------------------
# (radius, z, atlas row) - rows come straight from textures.bottle()
PROFILE = [
    (0.000, 0.300, 2), (0.016, 0.300, 5), (0.016, 0.282, 20),
    (0.013, 0.278, 24), (0.013, 0.212, 32), (0.026, 0.196, 36),
    (0.042, 0.180, 42), (0.042, 0.150, 48), (0.042, 0.055, 88),
    (0.042, 0.008, 118), (0.038, 0.000, 125), (0.000, 0.000, 127),
]


def build_bottle(N=10):
    verts, faces, uvs = [], [], []
    rings = PROFILE[1:-1]
    for r, z, _ in rings:
        for i in range(N):
            a = TAU * i / N
            verts.append((r * math.cos(a), r * math.sin(a), z))
    top = len(verts); verts.append((0, 0, PROFILE[0][1]))
    bot = len(verts); verts.append((0, 0, PROFILE[-1][1]))

    def v_of(row):
        return 1.0 - row / 128.0

    for k in range(len(rings) - 1):
        v0, v1 = v_of(rings[k][2]), v_of(rings[k + 1][2])
        for i in range(N):
            j = (i + 1) % N
            a, b = k * N + i, k * N + j
            c, d = (k + 1) * N + j, (k + 1) * N + i
            faces.append((a, b, c, d))
            u0, u1 = i / N, (i + 1) / N
            uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    for i in range(N):
        j = (i + 1) % N
        faces.append((top, i, j))
        uvs.append([(0.5, v_of(PROFILE[0][2])), (i / N, v_of(rings[0][2])),
                    ((i + 1) / N, v_of(rings[0][2]))])
    base = (len(rings) - 1) * N
    for i in range(N):
        j = (i + 1) % N
        faces.append((bot, base + j, base + i))
        uvs.append([(0.5, v_of(PROFILE[-1][2])),
                    ((i + 1) / N, v_of(rings[-1][2])), (i / N, v_of(rings[-1][2]))])
    return make("SM_Bottle_Vodka_01", verts, faces, uvs)


# --- cigarette pack --------------------------------------------------------
def build_pack(w=0.055, d=0.023, h=0.088):
    x, y = w / 2, d / 2
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0),
             (-x, -y, h), (x, -y, h), (x, y, h), (-x, y, h)]
    R = lambda x0, y0, x1, y1: (x0 / 64, 1 - y1 / 64, x1 / 64, 1 - y0 / 64)
    spec = [((0, 1, 5, 4), R(0, 0, 32, 40)),    # front
            ((2, 3, 7, 6), R(32, 0, 64, 40)),   # back
            ((3, 0, 4, 7), R(0, 40, 32, 52)),   # left
            ((1, 2, 6, 5), R(32, 40, 64, 52)),  # right
            ((4, 5, 6, 7), R(0, 52, 32, 64)),   # top
            ((3, 2, 1, 0), R(32, 52, 64, 64))]  # bottom
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
