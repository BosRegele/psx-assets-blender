"""Assemble the bunker scene and render it in Cycles on the GPU.

Runs inside Blender through the bridge. The room is built here rather than
declared in props.py because architecture tiles instead of packing an atlas -
a 7m wall at the bundle density would be an 1100px face.

Lighting is doing most of the work in these renders. The textures are unlit
diffuse by design, so without practical lights in shot the room reads flat;
with them, the same 3300 triangles read as a place.
"""
import bpy, math, os, sys, importlib

sys.path.insert(0, "D:/PSX-Props/tools")
import kit, props, blender_build
for m in (kit, props, blender_build):
    importlib.reload(m)   # arch.py needs PIL, which Blender lacks; its two
                          # constants live in kit for exactly that reason

TEX = "D:/PSX-Props/assets/textures"
ROOM = dict(w=7.4, d=5.4, h=2.75)
TAU = math.pi * 2


# --- shared helpers --------------------------------------------------------

def clear():
    for o in bpy.data.objects:
        o.hide_viewport = False
        o.hide_set(False)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                  bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def pixel_material(name, png, repeat=True, emission=0.0):
    """Point-sampled diffuse. `Closest` is what keeps the aesthetic under a
    physically based renderer - bilinear filtering would dissolve every texel
    the whole pipeline exists to place."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(png, check_existing=True)
    tex.interpolation = "Closest"
    tex.extension = "REPEAT" if repeat else "EXTEND"
    tex.location = (-500, 200)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.02
    if emission:
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.86, 0.62, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def quad(name, verts, uvs, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for i, (u, v) in enumerate(uvs):
        uv.data[i].uv = (u, v)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


# --- room ------------------------------------------------------------------

def build_room():
    """Six quads with UVs scaled so every surface lands on arch.DENSITY.

    The UV scale is computed from the tile's world size, not typed in. Type it
    in and the wall silently drifts off the props' pixel size the first time
    the room changes dimensions.
    """
    W, D, H = ROOM["w"], ROOM["d"], ROOM["h"]
    tile_m = kit.arch_tile_metres()            # metres covered by one tile
    mats = {k: pixel_material(f"MI_ARCH_{k}", f"{TEX}/ARCH_{k}_d.png")
            for k in ("wall", "floor", "ceiling")}

    def uvs(a, b):
        s, t = a / tile_m, b / tile_m
        return [(0, 0), (s, 0), (s, t), (0, t)]

    x0, x1, y0, y1 = -W / 2, W / 2, -D / 2, D / 2
    parts = [
        ("Floor", [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)],
         uvs(W, D), "floor"),
        ("Ceiling", [(x0, y1, H), (x1, y1, H), (x1, y0, H), (x0, y0, H)],
         uvs(W, D), "ceiling"),
        ("Wall_N", [(x0, y1, 0), (x1, y1, 0), (x1, y1, H), (x0, y1, H)],
         uvs(W, H), "wall"),
        ("Wall_S", [(x1, y0, 0), (x0, y0, 0), (x0, y0, H), (x1, y0, H)],
         uvs(W, H), "wall"),
        ("Wall_W", [(x0, y0, 0), (x0, y1, 0), (x0, y1, H), (x0, y0, H)],
         uvs(D, H), "wall"),
        ("Wall_E", [(x1, y1, 0), (x1, y0, 0), (x1, y0, H), (x1, y1, H)],
         uvs(D, H), "wall"),
    ]
    return [quad(n, v, u, mats[m]) for n, v, u, m in parts]


# --- dressing --------------------------------------------------------------
# (prop, x, y, z, rotation about Z in degrees). A prop's front face is -Y, so
# something standing against the west wall needs +90.

W2, D2 = ROOM["w"] / 2, ROOM["d"] / 2


def _euler(rot):
    """A layout entry gives either a Z angle or a full (X, Y, Z) triple.
    Upright is the wrong default for a sausage on a plate or a rifle leaning
    against a wall, and those are the props a dressed room needs most."""
    if isinstance(rot, (tuple, list)):
        return tuple(math.radians(a) for a in rot)
    return (0.0, 0.0, math.radians(rot))

LAYOUT = [
    # North wall sits at +Y and a prop's front face is -Y, so these take no
    # rotation. The first pass gave them 180 and turned every one to the wall.
    ("SM_Locker_Steel_01", -2.95, D2 - 0.28, 0, 0),
    ("SM_Locker_Steel_01", -2.10, D2 - 0.28, 0, 0),
    ("SM_Shelf_Steel_01", -0.75, D2 - 0.24, 0, 0),
    ("SM_Cabinet_Filing_01", 0.55, D2 - 0.34, 0, 0),
    ("SM_Map_Wall_01", 2.05, D2 - 0.03, 1.05, 0),
    ("SM_Board_Notice_01", 3.05, D2 - 0.03, 1.15, 0),

    # west wall: bunks and a poster
    (-1, 0, 0, 0, 0),  # spacer, ignored
    ("SM_Bunk_Steel_01", -W2 + 0.50, 0.55, 0, 90),
    ("SM_Poster_01", -W2 + 0.03, -1.15, 1.25, 90),
    ("SM_Clock_Wall_01", -W2 + 0.06, -1.95, 1.85, 90),
    ("SM_Barrel_Steel_01", -W2 + 0.42, -2.10, 0, 0),

    # east wall: the desk corner
    ("SM_Desk_Wood_01", W2 - 0.42, 1.30, 0, -90),
    ("SM_Chair_Wood_01", W2 - 1.25, 1.30, 0, 90),
    ("SM_Cabinet_Wall_01", W2 - 0.20, -0.10, 1.35, -90),
    ("SM_Pipe_Valve_01", W2 - 0.22, -2.25, 0, 0),

    # south side: the couch and a table
    ("SM_Couch_Worn_01", -1.35, -D2 + 0.48, 0, 180),
    ("SM_Table_Steel_01", 1.35, -1.10, 0, 0),
    ("SM_Stool_Metal_01", 1.35, -1.95, 0, 0),
    ("SM_Chair_Wood_01", 2.35, -0.95, 0, -110),

    # floor clutter
    ("SM_Crate_Ammo_01", 2.90, 1.85, 0, 20),
    ("SM_Crate_Ammo_01", 2.92, 1.86, 0.22, -14),
    ("SM_Crate_Wood_01", -0.10, -2.05, 0, -8),
    ("SM_JerryCan_01", 3.05, 0.55, 0, 35),
    ("SM_Bucket_01", -2.60, -1.55, 0, 0),
    ("SM_Toolbox_01", 0.55, -2.20, 0, 12),
    ("SM_Rags_01", -3.05, -0.35, 0, 0),
    ("SM_AmmoTin_01", 3.02, 1.20, 0, -25),

    # table top: the layer that says someone lives here
    ("SM_Bottle_Vodka_01", 1.02, -1.02, 0.75, 0),
    ("SM_Bottle_Beer_01", 1.62, -0.92, 0.75, 0),
    ("SM_Mug_Enamel_01", 1.36, -1.24, 0.75, 25),
    ("SM_Ashtray_01", 1.74, -1.26, 0.75, 0),
    ("SM_Can_Food_01", 0.90, -1.30, 0.75, 0),
    ("SM_Bread_01", 1.24, -0.84, 0.75, -12),
    ("SM_Pack_Cigarettes_01", 1.56, -1.34, 0.75, 40),
    ("SM_Matchbox_01", 1.66, -1.42, 0.75, -20),
    ("SM_Plate_Tin_01", 1.02, -1.44, 0.75, 0),
    ("SM_Sausage_01", 1.10, -1.47, 0.80, (0, 90, 20)),

    # desk top
    ("SM_Radio_Field_01", W2 - 0.40, 1.70, 0.76, -90),
    ("SM_Lamp_Oil_01", W2 - 0.30, 0.92, 0.76, 0),
    ("SM_Papers_01", W2 - 0.55, 1.28, 0.76, 8),
    ("SM_Books_01", W2 - 0.72, 0.78, 0.76, -6),

    # shelves: 0.15 / 0.71 / 1.27 / 1.83 decks
    ("SM_Jar_Glass_01", -1.05, D2 - 0.24, 0.74, 0),
    ("SM_Jar_Glass_01", -0.88, D2 - 0.26, 0.74, 0),
    ("SM_Can_Food_01", -0.60, D2 - 0.24, 0.74, 0),
    ("SM_BugSpray_01", -0.42, D2 - 0.26, 0.74, 0),
    ("SM_FirstAid_01", -0.95, D2 - 0.25, 1.30, 0),
    ("SM_Kettle_01", -0.52, D2 - 0.25, 1.30, 0),
    ("SM_MessTin_01", -1.02, D2 - 0.24, 0.18, 0),
    ("SM_Canteen_01", -0.62, D2 - 0.25, 0.18, 0),
    ("SM_Helmet_Steel_01", -0.80, D2 - 0.25, 1.86, 0),

    # gear on the bunk and around it
    ("SM_GasMask_01", -W2 + 0.55, 1.20, 0.48, -60),
    ("SM_Vest_Armor_01", -W2 + 0.62, -0.35, 0, 70),
    ("SM_Rifle_01", -2.72, D2 - 0.42, 0.62, (0, 74, 8)),
    ("SM_Pistol_01", W2 - 0.62, 1.52, 0.79, 30),
]

LAMPS = [(-2.0, 1.30, ROOM["h"] - 0.30),
         (1.60, -0.70, ROOM["h"] - 0.30),
         (2.90, 2.00, ROOM["h"] - 0.30)]


# The three consumables predate kit.py: they are revolved profiles built from
# geometry.py, so they are absent from props.REGISTRY. The scene skipped them
# silently and the table rendered without its vodka, tin or cigarettes.
LEGACY = {"SM_Can_Food_01": "build_can",
          "SM_Bottle_Vodka_01": "build_bottle",
          "SM_Pack_Cigarettes_01": "build_pack"}


def build_props():
    """One mesh per placement. Meshes are shared between repeats of a prop, so
    two lockers cost one mesh and two objects."""
    cache, placed = {}, []
    for entry in LAYOUT:
        if not isinstance(entry[0], str):
            continue
        name, x, y, z, rz = entry
        if name in LEGACY:
            if name not in cache:
                proto = getattr(blender_build, LEGACY[name])()
                proto.data.materials.clear()
                proto.data.materials.append(pixel_material(
                    f"MI_{name}", f"{TEX}/{name}_d.png", repeat=False))
                cache[name] = proto.data
                bpy.data.objects.remove(proto)
            ob = bpy.data.objects.new(name, cache[name])
            bpy.context.collection.objects.link(ob)
            ob.location = (x, y, z)
            ob.rotation_euler = _euler(rz)
            placed.append(ob)
            continue
        if name not in cache:
            tier, parts = props.REGISTRY[name]() if name in props.REGISTRY else (None, None)
            if parts is None:
                raise KeyError(f"{name} is in LAYOUT but nothing can build it")
            r = kit.build(parts, tier)
            me = bpy.data.meshes.new(name)
            me.from_pydata(r["verts"], [], r["faces"])
            me.update()
            uv = me.uv_layers.new(name="UVMap")
            i = 0
            for poly in r["uvs"]:
                for u, v in poly:
                    uv.data[i].uv = (u, v)
                    i += 1
            for p in me.polygons:
                p.use_smooth = False
            me.materials.append(
                pixel_material(f"MI_{name}", f"{TEX}/{name}_d.png", repeat=False))
            cache[name] = me
        ob = bpy.data.objects.new(name, cache[name])
        bpy.context.collection.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = _euler(rz)
        placed.append(ob)
    return placed


def build_lamps():
    """Caged lamps with a real emitter inside, plus a matching point light.

    The emissive geometry is what makes the fixture read as the source; the
    point light is what actually carries the room. One without the other looks
    either flat or unexplained.
    """
    obs = []
    lamp_mesh = None
    tier, parts = props.REGISTRY["SM_Lamp_Cage_01"]()
    r = kit.build(parts, tier)
    for i, (x, y, z) in enumerate(LAMPS):
        if lamp_mesh is None:
            me = bpy.data.meshes.new("SM_Lamp_Cage_01")
            me.from_pydata(r["verts"], [], r["faces"])
            me.update()
            uv = me.uv_layers.new(name="UVMap")
            k = 0
            for poly in r["uvs"]:
                for u, v in poly:
                    uv.data[k].uv = (u, v)
                    k += 1
            for p in me.polygons:
                p.use_smooth = False
            me.materials.append(pixel_material(
                "MI_SM_Lamp_Cage_01", f"{TEX}/SM_Lamp_Cage_01_d.png",
                repeat=False, emission=3.0))
            lamp_mesh = me
        ob = bpy.data.objects.new(f"Lamp_Fixture_{i}", lamp_mesh)
        bpy.context.collection.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (math.pi, 0, 0)      # hangs downward
        # The fixture's glass is an opaque diffuse texture like everything else
        # here, so a bulb inside it is a bulb inside a sealed tin - the first
        # lit render came out black for exactly this reason. Let light through
        # the housing rather than faking a transmissive shader the rest of the
        # kit does not use.
        ob.visible_shadow = False
        obs.append(ob)

        bulb = bpy.data.lights.new(f"Bulb_{i}", type="POINT")
        bulb.energy = 150.0
        bulb.color = (1.0, 0.78, 0.52)
        bulb.shadow_soft_size = 0.08
        lo = bpy.data.objects.new(f"Bulb_{i}", bulb)
        bpy.context.collection.objects.link(lo)
        lo.location = (x, y, z - 0.20)
        obs.append(lo)

    # a cold sliver from the doorway, so the warm practicals have something
    # to sit against
    key = bpy.data.lights.new("Doorway", type="AREA")
    key.energy = 55.0
    key.color = (0.58, 0.70, 1.0)
    key.size, key.size_y = 0.55, 1.7
    key.shape = "RECTANGLE"
    ko = bpy.data.objects.new("Doorway", key)
    bpy.context.collection.objects.link(ko)
    ko.location = (ROOM["w"] / 2 - 0.06, -2.15, 1.10)
    ko.rotation_euler = (0, math.radians(-90), 0)
    ko.visible_camera = False        # it is a light, not a glowing panel on the wall
    obs.append(ko)

    # very dim cool fill so the darks keep some material information instead of
    # crushing to black. A bunker should be dark, not empty.
    fill = bpy.data.lights.new("Fill", type="AREA")
    fill.energy = 4.0
    fill.color = (0.66, 0.74, 0.95)
    fill.size, fill.size_y = ROOM["w"] * 0.7, ROOM["d"] * 0.7
    fill.shape = "RECTANGLE"
    fo = bpy.data.objects.new("Fill", fill)
    bpy.context.collection.objects.link(fo)
    fo.location = (0, 0, ROOM["h"] - 0.05)
    fo.rotation_euler = (math.pi, 0, 0)
    fo.visible_camera = False
    obs.append(fo)
    return obs


def build_camera(shot=0):
    """Aim by target point, not by typed Euler angles.

    Hand-written rotations are guesswork inside a closed room - the first pass
    of this scene rendered a black frame because the camera was facing a wall.
    A look-at vector cannot be wrong.
    """
    from mathutils import Vector
    cam = bpy.data.cameras.new("Cam")
    cam.lens = 22.0
    ob = bpy.data.objects.new("Cam", cam)
    bpy.context.collection.objects.link(ob)
    shots = [((-2.60, -2.05, 1.68), (1.30, 1.35, 0.85)),    # across to the desk
             ((2.55, -2.10, 1.55), (-2.30, 1.90, 1.00)),    # across to the lockers
             ((0.10, -2.30, 1.32), (0.60, 2.20, 0.95)),     # down the room
             ((2.05, -0.35, 1.20), (1.30, -1.15, 0.78))]    # the table, close
    loc, tgt = shots[shot % len(shots)]
    ob.location = loc
    ob.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return ob


def setup_cycles(samples=200, res=(1920, 1080)):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "HIP"
    prefs.get_devices()
    enabled = []
    for d in prefs.devices:
        d.use = (d.type == "HIP")
        if d.use:
            enabled.append(d.name)
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3   # bounce light was flattening the room
    sc.cycles.transmission_bounces = 2
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.02, 0.025, 0.035, 1.0)
    bg.inputs[1].default_value = 0.012
    return enabled


def render(path, shot=0, samples=200, res=(1920, 1080)):
    build_camera(shot)
    setup_cycles(samples, res)
    bpy.context.scene.render.filepath = path
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return path


def render_all(out_dir="D:/PSX-Props/renders", shots=(0, 1, 2, 3),
               samples=180, res=(1920, 1080)):
    """Build once, then render every camera. Rebuilding per shot would be
    minutes of wasted work for four frames of the same room."""
    main()
    done = []
    for i in shots:
        done.append(render(f"{out_dir}/bunker_{i}.png", shot=i,
                           samples=samples, res=res))
    return done


def main():
    clear()
    room = build_room()
    dressing = build_props()
    lamps = build_lamps()
    devs = setup_cycles()
    tris = sum(len(p.vertices) - 2
               for o in room + dressing + lamps if o.type == "MESH"
               for p in o.data.polygons)
    return (f"room + {len(dressing)} placed props, {tris} tris in scene | "
            f"GPU: {', '.join(devs) or 'NONE'}")


print(main())
