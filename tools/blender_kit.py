"""Build every registered prop inside Blender. Runs via the execute_code bridge.

Geometry, UVs and atlas placement all come from kit.py, the same module the
texture baker used, so the mesh and the texture cannot disagree.
"""
import bpy, os, sys, math, importlib

sys.path.insert(0, "D:/PSX-Props/tools")
import kit, props
for m in (kit, props):
    importlib.reload(m)

TEX = "D:/PSX-Props/assets/textures"
OUT = "D:/PSX-Props/exports"


def clear():
    # Unhide first: select_all cannot touch a hidden object, so any prop left
    # hidden by the screenshot pass survived the wipe and the next build added
    # a .001 duplicate beside it.
    for o in bpy.data.objects:
        o.hide_viewport = False
        o.hide_set(False)
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
    for poly in face_uvs:
        for u, v in poly:
            uv.data[i].uv = (u, v)
            i += 1
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
    tex.interpolation = "Closest"
    tex.extension = "EXTEND"      # atlases must not wrap; a clamp hides seams
    tex.location = (-400, 200)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    ob.data.materials.append(mat)


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


def main(arrange=True, do_export=True):
    clear()
    os.makedirs(OUT, exist_ok=True)
    names = list(props.REGISTRY)
    cols = 6
    spacing = 1.6
    report, total = [], 0
    for idx, name in enumerate(names):
        tier, parts = props.REGISTRY[name]()
        r = kit.build(parts, tier)
        ob = make(name, r["verts"], r["faces"], r["uvs"])
        material(ob, f"{TEX}/{name}_d.png", f"MI_{name}")
        tris = sum(len(f) - 2 for f in r["faces"])
        total += tris
        # export at the origin, then move it for the contact sheet - otherwise
        # every FBX ships with the grid offset baked into its transform
        if do_export:
            export(ob, name)
        if arrange:
            ob.location = ((idx % cols) * spacing - (cols - 1) * spacing / 2,
                           (idx // cols) * spacing * 1.6, 0)
        report.append(f"{name}: {tris} tris")
    return f"{len(names)} props, {total} tris total"


print(main())
