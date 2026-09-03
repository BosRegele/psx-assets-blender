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
    ("SM_Locker_Open_01", -2.95, D2 - 0.28, 0, 0),
    ("SM_Locker_Blue_01", -2.10, D2 - 0.28, 0, 0),
    ("SM_Shelf_Steel_01", -0.75, D2 - 0.24, 0, 0),
    ("SM_Cabinet_Filing_01", 0.55, D2 - 0.34, 0, 0),
    ("SM_Map_Wall_01", 2.05, D2 - 0.03, 1.05, 0),
    ("SM_Radio_Valve_01", 0.55, D2 - 0.34, 1.10, 0),
    ("SM_ToolBoard_01", W2 - 0.03, -1.30, 1.28, -90),
    ("SM_Gauge_Wall_01", W2 - 0.06, -2.02, 1.52, -90),
    ("SM_Phone_Field_01", -0.10, -2.05, 0.450, 20),
    ("SM_Board_Notice_01", 3.05, D2 - 0.03, 1.15, 0),

    # west wall
    ("SM_Bunk_Steel_01", -W2 + 0.50, 0.55, 0, 90),
    ("SM_Poster_01", -W2 + 0.03, -1.15, 1.25, 90),
    ("SM_Clock_Wall_01", -W2 + 0.06, -1.95, 1.85, 90),
    ("SM_Barrel_Steel_01", -W2 + 0.42, -2.10, 0, 0),
    ("SM_Scrap_Pile_01", 2.05, 2.20, 0, 25),

    # east wall: the desk corner
    ("SM_Desk_Wood_01", W2 - 0.42, 1.30, 0, -90),
    ("SM_Chair_Wood_01", W2 - 1.25, 1.30, 0, 90),
    ("SM_Cabinet_Wall_01", W2 - 0.20, -0.10, 1.35, -90),
    ("SM_Pipe_Valve_01", W2 - 0.22, -2.25, 0, 0),

    # south side
    ("SM_Couch_Worn_01", -1.35, -D2 + 0.48, 0, 180),
    ("SM_Table_Steel_01", 1.35, -1.10, 0, 0),
    ("SM_Stool_Metal_01", 1.35, -1.95, 0, 0),
    ("SM_Chair_Wood_01", 2.35, -0.95, 0, -110),

    # floor clutter and refuse
    ("SM_Crate_Ammo_01", 3.05, 2.28, 0, 20),
    ("SM_Crate_Ammo_01", 3.07, 2.29, 0.22, -14),
    ("SM_Crate_Wood_01", -0.10, -2.05, 0, -8),
    ("SM_JerryCan_01", 3.18, 0.10, 0, 35),
    ("SM_Bucket_01", -2.60, -1.55, 0, 0),
    ("SM_Toolbox_01", 0.55, -2.30, 0, 12),
    ("SM_Rags_01", -2.30, -0.80, 0, 0),
    ("SM_AmmoTin_01", 2.55, -0.45, 0, -25),
    ("SM_Trash_Pile_01", 0.05, 1.55, 0, 30),
    ("SM_Trash_Pile_01", -1.95, -1.05, 0, 140),
    ("SM_Debris_01", 2.05, -1.95, 0, 60),
    ("SM_Debris_01", -0.85, 0.35, 0, 200),
    ("SM_Debris_01", 2.60, 0.20, 0, 15),
    ("SM_Cartridges_Pile_01", 0.95, 1.05, 0, 0),
    ("SM_Cartridges_Pile_01", -1.55, 1.85, 0, 70),
    ("SM_Crate_Hazard_01", 2.95, -1.70, 0, 15),
    ("SM_Wrench_01", -2.70, 1.30, 0.004, 110),
    ("SM_Hammer_01", -3.00, 1.52, 0.015, (0, 90, 40)),

    # He is standing in the far corner, mostly out of the light. Nothing else
    # in the room is a person, so the silhouette does the work.
    ("SM_Figure_Stalker_01", -2.68, -2.30, 0, 28),

    # table top, z 0.750. Kept inside x 0.83..1.87, y -1.33..-0.87 - several
    # of these used to hang over the edge.
    ("SM_Bottle_Vodka_01", 0.95, -1.28, 0.750, 0),
    ("SM_Bottle_Beer_01", 1.72, -1.20, 0.750, 0),
    ("SM_Mug_Enamel_01", 1.30, -1.30, 0.750, 25),
    ("SM_Ashtray_01", 1.55, -1.05, 0.750, 0),
    ("SM_Can_Food_01", 1.10, -0.95, 0.750, 0),
    ("SM_Bread_01", 1.75, -0.93, 0.750, -12),
    ("SM_Pack_Cigarettes_01", 1.42, -1.10, 0.750, 40),
    ("SM_Matchbox_01", 1.50, -1.22, 0.750, -20),
    ("SM_Plate_Tin_01", 1.05, -1.15, 0.750, 0),
    ("SM_Pliers_01", 1.24, -1.02, 0.752, 60),
    ("SM_Sausage_01", 1.05, -1.15, 0.768, (0, 90, 20)),

    # desk top, z 0.760
    ("SM_Radio_Field_01", W2 - 0.38, 1.72, 0.760, -90),
    ("SM_Lamp_Oil_01", W2 - 0.34, 0.92, 0.760, 0),
    ("SM_Papers_01", W2 - 0.54, 1.30, 0.760, 8),
    ("SM_Books_01", W2 - 0.68, 0.80, 0.760, -6),
    ("SM_Revolver_01", W2 - 0.50, 1.05, 0.760, (0, 0, 40)),
    ("SM_Grenade_01", W2 - 0.64, 1.86, 0.760, 0),
    ("SM_Headphones_01", W2 - 0.56, 1.55, 0.760, 20),
    ("SM_Screwdriver_01", W2 - 0.40, 1.18, 0.760, (0, 90, 25)),

    # Shelf decks are at 0.150 / 0.710 / 1.270 / 1.830. These were placed at
    # round numbers 30mm above the steel and floated.
    ("SM_MessTin_01", -1.05, D2 - 0.26, 0.150, 0),
    ("SM_Canteen_01", -0.62, D2 - 0.26, 0.150, 0),
    ("SM_Jar_Glass_01", -1.08, D2 - 0.28, 0.710, 0),
    ("SM_Jar_Glass_01", -0.90, D2 - 0.26, 0.710, 0),
    ("SM_Can_Food_01", -0.62, D2 - 0.28, 0.710, 0),
    ("SM_BugSpray_01", -0.42, D2 - 0.26, 0.710, 0),
    ("SM_FirstAid_01", -0.95, D2 - 0.26, 1.270, 0),
    ("SM_Kettle_01", -0.52, D2 - 0.26, 1.270, 0),
    ("SM_Helmet_Steel_01", -0.80, D2 - 0.26, 1.830, 0),

    # weapons and gear. The bunk's lower mattress tops out at 0.580.
    ("SM_GasMask_01", -W2 + 0.55, 1.20, 0.580, -60),
    ("SM_Vest_Armor_01", -W2 + 0.62, -0.35, 0, 70),
    ("SM_Rifle_02", -2.72, D2 - 0.42, 0.62, (0, 74, 8)),
    ("SM_SMG_01", 3.03, 2.25, 0.480, (0, 0, 25)),
    ("SM_AmmoBelt_01", 3.09, 2.35, 0.480, (0, 0, -34)),
    ("SM_Cartridge_01", 1.62, -1.02, 0.750, (0, 90, 15)),
]

# Support surfaces, so a prop cannot silently float or overhang again. Values
# are measured from the prop definitions, not typed by eye.
SUPPORTS = {
    "table": dict(z=0.750, x=(0.83, 1.87), y=(-1.33, -0.87)),
    "desk": dict(z=0.760, x=(W2 - 0.70, W2 - 0.14), y=(0.70, 1.90)),
    "shelf": dict(z=(0.150, 0.710, 1.270, 1.830),
                  x=(-1.22, -0.28), y=(D2 - 0.42, D2 - 0.06)),
}


# Props that legitimately sit on something else, with the offset they ride at.
STACKED = {"SM_Sausage_01": 0.018}     # on the plate rim


def check_overlaps(margin=0.03, min_overlap=0.06):
    """Floor-standing props whose plan footprints intersect.

    The stalker was placed 270mm from a barrel of 280mm radius and rendered
    inside it, which is invisible in a layout table and obvious in a render.
    Only ground-level props are checked - things deliberately stacked on a
    surface are meant to share a footprint.
    """
    import kit as _kit
    boxes = []
    for entry in LAYOUT:
        name, x, y, z, rot = entry
        if z > 0.05 or name not in props.REGISTRY:
            continue
        fx0, fy0, fx1, fy1 = _kit.footprint(props.REGISTRY[name]()[1])
        # Rotate the four corners and take their AABB. A circumscribed square
        # was conservative enough to report a right-angled desk as colliding
        # with half the room.
        rz = math.radians(rot[2] if isinstance(rot, (tuple, list)) else rot)
        c, s_ = math.cos(rz), math.sin(rz)
        pts = [(px * c - py * s_, px * s_ + py * c)
               for px in (fx0, fx1) for py in (fy0, fy1)]
        boxes.append((name,
                      x + min(p[0] for p in pts), y + min(p[1] for p in pts),
                      x + max(p[0] for p in pts), y + max(p[1] for p in pts)))
    hits = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            ox = min(a[3], b[3]) - max(a[1], b[1])
            oy = min(a[4], b[4]) - max(a[2], b[2])
            if ox > min_overlap and oy > min_overlap:
                hits.append(f"{a[0]} overlaps {b[0]} by "
                            f"{ox * 1000:.0f}x{oy * 1000:.0f}mm")
    return hits


def validate(tol=0.004):
    """Check every placed prop that claims to sit on a surface actually does.

    Three separate rounds of renders had things hovering or hanging over an
    edge; eyeballing coordinates does not catch a 30mm float.
    """
    problems = []
    for entry in LAYOUT:
        name, x, y, z, _ = entry
        for label, s in SUPPORTS.items():
            zs = s["z"] if isinstance(s["z"], tuple) else (s["z"],)
            near = [zz for zz in zs if abs(z - zz) < 0.12]
            if not near or z < 0.05:
                continue
            if not (s["x"][0] <= x <= s["x"][1] and s["y"][0] <= y <= s["y"][1]):
                continue
            lift = STACKED.get(name, 0.0)
            if min(abs(z - lift - zz) for zz in near) > tol:
                problems.append(f"{name} on {label}: z={z:.3f}, "
                                f"surface at {min(near, key=lambda q: abs(z - q)):.3f}")
    return problems


# Ceiling panels sit flush under the soffit; the fixture is 90mm deep.
LAMPS = [(-2.15, 1.30), (1.55, -0.85), (2.85, 1.95), (-1.45, -1.85)]


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
            if name not in props.REGISTRY:
                raise KeyError(f"{name} is in LAYOUT but nothing can build it")
            tier, parts = props.REGISTRY[name]()
            cache[name] = mesh_from(name, kit.build(parts, tier))
        ob = bpy.data.objects.new(name, cache[name])
        bpy.context.collection.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = _euler(rz)
        placed.append(ob)
    return placed


def mesh_from(name, r):
    """Build a mesh, splitting the emissive faces into their own material slot.

    A fixture needs two materials - the housing reads from the atlas like every
    other prop, while the diffuser has to actually emit. Doing it per-polygon
    keeps it one object and one draw call.
    """
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
    me.materials.append(pixel_material(f"MI_{name}", f"{TEX}/{name}_d.png",
                                       repeat=False))
    if "emitter" in r["surfaces"]:
        glow = bpy.data.materials.new(f"MI_{name}_Emit")
        glow.use_nodes = True
        nt = glow.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (1.0, 0.93, 0.80, 1.0)
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.86, 0.62, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 14.0
        me.materials.append(glow)
        for p, surf in zip(me.polygons, r["surfaces"]):
            p.material_index = 1 if surf == "emitter" else 0
    return me


def build_lamps():
    """Ceiling panels: an emissive diffuser plus a matching area light.

    An earlier version hung bulkhead cans with a point light inside them and a
    cold area light floating against a wall - which read, correctly, as an
    unexplained glow. Light now comes from a fixture you can see.
    """
    obs = []
    tier, parts = props.REGISTRY["SM_CeilingLight_01"]()
    r = kit.build(parts, tier)
    me = mesh_from("SM_CeilingLight_01", r)
    z = ROOM["h"] - 0.09
    for i, (x, y) in enumerate(LAMPS):
        ob = bpy.data.objects.new(f"CeilingLight_{i}", me)
        bpy.context.collection.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, math.radians(90 if i % 2 else 0))
        ob.visible_shadow = False       # the housing must not block its own panel
        obs.append(ob)

        panel = bpy.data.lights.new(f"Panel_{i}", type="AREA")
        panel.energy = 78.0
        panel.color = (1.0, 0.82, 0.58)
        panel.shape = "RECTANGLE"
        panel.size, panel.size_y = 0.56, 0.17
        lo = bpy.data.objects.new(f"Panel_{i}", panel)
        bpy.context.collection.objects.link(lo)
        lo.location = (x, y, z - 0.03)
        lo.rotation_euler = (math.pi, 0, math.radians(90 if i % 2 else 0))
        obs.append(lo)

    # Very dim cool fill so the darks keep material information instead of
    # crushing to black. A bunker should be dark, not empty.
    fill = bpy.data.lights.new("Fill", type="AREA")
    fill.energy = 5.0
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
             ((2.05, -0.35, 1.20), (1.30, -1.15, 0.78)),    # the table, close
             ((2.20, 1.70, 1.62), (-2.55, -2.05, 1.05)),    # couch and the corner
             ((-0.60, 0.90, 1.35), (-3.10, -2.10, 1.15))]   # straight at him
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


def save_blend(path="D:/PSX-Props/scene/Bunker_Scene.blend"):
    """Ship the assembled scene as a file. Rebuilding it costs a minute, but a
    buyer wants to open it, and it keeps this work off whatever the user
    happens to have loaded."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return path


def render_all(out_dir="D:/PSX-Props/renders", shots=(0, 1, 2, 3, 4, 5),
               samples=180, res=(1920, 1080)):
    """Build once, then render every camera. Rebuilding per shot would be
    minutes of wasted work for four frames of the same room."""
    main()
    save_blend()
    done = []
    for i in shots:
        done.append(render(f"{out_dir}/bunker_{i}.png", shot=i,
                           samples=samples, res=res))
    return done


def main():
    problems = validate() + check_overlaps()
    if problems:
        raise ValueError("bad placements: " + "; ".join(problems))
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
