"""Box-composite props: density tiers, geometry, and automatic atlas packing.

The three hand-built props each needed their atlas laid out by hand. That does
not scale to a bundle. Here a prop is declared in metres and the UV atlas is
PACKED automatically at a fixed texel density, so square texels are structural
rather than something to remember.

Both the texture painter and the Blender mesh builder import this module and
read the same packing, exactly as they share geometry.py for the revolved props.
Packing is deterministic - sorted by height then name - so the two never drift.
"""
import math

# Two tiers, a factor of two apart. One density for the whole bundle would put
# a 1.8m locker on a 1024px atlas, which no PS1 ever did; four tiers would make
# the pixel size visibly inconsistent from prop to prop. Two is the compromise.
TIERS = {"prop": 551.0,        # handheld, under ~0.35m
         "furniture": 184.0}   # everything larger
# 3:1. Not arbitrary: a 1.85m locker seen across a room covers roughly 340
# screen pixels, so 184 px/m lands near 1:1 on screen. At the handheld density
# it would carry 500 texels nobody ever resolves. Shipped games varied density
# by object scale for exactly this reason - the rule is square texels within a
# prop and a constant density within a tier, not one number for the bundle.

# Architecture tiles rather than packing an atlas, but it must land on the
# same texel density as the furniture around it. The constants live here, not
# in arch.py, because Blender's interpreter has no PIL and cannot import that
# module - and a wall whose density drifts from the props is the whole failure
# this pipeline exists to prevent.
ARCH_TILE = 512                       # px; 2.78 m at the furniture density


def arch_tile_metres():
    return ARCH_TILE / TIERS["furniture"]


FACES = ("front", "back", "left", "right", "top", "bottom")

# A face marked "hidden" still exists in the mesh - leaving a hole would break
# shadow casting and any physics collider generated from the mesh - but it
# shares one 4px rect with every other hidden face instead of claiming atlas
# space it will never show. On the couch this is the difference between a
# 1024 and a 512 sheet.
# Two ways a face can go untextured, and they are not the same claim:
#   "hidden" - another part of this prop covers it. check_hidden() verifies it.
#   "unseen" - the world covers it: a poster's back against a wall, a plinth
#              underside on the floor. Nothing in the prop can prove that, so
#              it is exempt from the check and has to be argued in the code.
# Marking a visible face hidden renders a flat grey slab, which is what put a
# grey stripe along the top of the couch.
HIDDEN = "hidden"
UNSEEN = "unseen"
FILLERS = (HIDDEN, UNSEEN)
HIDDEN_KEY = "__hidden__"
HIDDEN_PX = 4

# face -> (which box dimensions it spans, vertex order, outward axis)
_FACE_DIMS = {"front": ("w", "h"), "back": ("w", "h"),
              "left": ("d", "h"), "right": ("d", "h"),
              "top": ("w", "d"), "bottom": ("w", "d")}


def _rotate(verts, pivot, rot):
    """Rotate a part's vertices about its own centroid, XYZ order.

    Parts rotate here rather than at the object level because a prop is one
    mesh: a cartridge lying on its side and the box it sits in have to be the
    same object, or every piece of clutter becomes another draw call.
    """
    if not rot or not any(rot):
        return verts
    rx, ry, rz = (math.radians(a) for a in rot)
    cx, cy, cz = pivot
    out = []
    for x, y, z in verts:
        x, y, z = x - cx, y - cy, z - cz
        y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
        x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
        x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
        out.append((x + cx, y + cy, z + cz))
    return out


class Box:
    """An axis-aligned box. `pos` is the minimum corner, `size` is (w, d, h)
    along (x, y, z). `surfaces` maps face names to painter keys; a bare string
    applies to every face."""

    __slots__ = ("name", "pos", "size", "surfaces", "rot", "pivot")

    def __init__(self, name, pos, size, surfaces, rot=None, pivot=None):
        """`pivot` is the point the part rotates about, in the prop's own
        space. It defaults to the part's centroid, which is right for a slab
        lying at an angle and wrong for anything hinged: a hammer claw or a
        plier arm has to swing about where it joins, or both ends move and the
        part floats free of what it is attached to.
        """
        self.name = name
        self.pos = tuple(float(v) for v in pos)
        self.size = tuple(float(v) for v in size)
        self.rot = tuple(rot) if rot else None
        self.pivot = tuple(float(v) for v in pivot) if pivot else None
        self.surfaces = ({f: surfaces for f in FACES}
                         if isinstance(surfaces, str) else dict(surfaces))

    def dims(self):
        w, d, h = self.size
        return {"w": w, "d": d, "h": h}

    def face_px(self, face, density):
        a, b = _FACE_DIMS[face]
        dm = self.dims()
        return max(1, int(round(dm[a] * density))), max(1, int(round(dm[b] * density)))

    def verts(self):
        x, y, z = self.pos
        w, d, h = self.size
        v = [(x, y, z), (x + w, y, z), (x + w, y + d, z), (x, y + d, z),
             (x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h),
             (x, y + d, z + h)]
        return _rotate(v, self.pivot or (x + w / 2, y + d / 2, z + h / 2),
                       self.rot)

    # local vertex indices per face, wound outward
    QUADS = {"front": (0, 1, 5, 4), "back": (2, 3, 7, 6),
             "left": (3, 0, 4, 7), "right": (1, 2, 6, 5),
             "top": (4, 5, 6, 7), "bottom": (3, 2, 1, 0)}


class Cylinder:
    """An N-gon prism. `pos` is the base centre. Packs as one wrap band plus
    two cap squares, all at the same density as the boxes around it."""

    __slots__ = ("name", "pos", "r", "r2", "h", "n", "surfaces", "rot", "pivot")

    PARTS = ("side", "top", "bottom")

    def __init__(self, name, pos, radius, height, surfaces, n=10,
                 r2=None, rot=None, centre=False, pivot=None):
        """`r2` gives the top radius: a frustum, which is what turns a blocky
        cylinder into a bullet, a funnel or a tapered mug.

        `centre=True` makes `pos` the middle of the cylinder rather than the
        base. Rotation happens about the centroid, so an un-centred rotated
        cylinder ends up half its length above where it was placed - which is
        how a rifle barrel detached itself from the receiver.
        """
        self.name = name
        pos = tuple(float(v) for v in pos)
        if centre:
            pos = (pos[0], pos[1], pos[2] - float(height) / 2.0)
        self.pos = pos
        self.r, self.h, self.n = float(radius), float(height), int(n)
        self.r2 = float(r2) if r2 is not None else float(radius)
        self.rot = tuple(rot) if rot else None
        self.pivot = tuple(float(v) for v in pivot) if pivot else None
        self.surfaces = ({p: surfaces for p in self.PARTS}
                         if isinstance(surfaces, str) else dict(surfaces))

    def face_px(self, part, density):
        rmax = max(self.r, self.r2)
        if part == "side":
            slant = math.hypot(self.h, self.r2 - self.r)
            return (max(4, int(round(TAU * rmax * density))),
                    max(2, int(round(slant * density))))
        rr = self.r if part == "bottom" else self.r2
        s = max(4, int(round(2 * max(rr, 0.002) * density)))
        return s, s


class Sphere:
    """A UV sphere, mapped equirectangularly to one atlas rect.

    Boxes cannot make a grenade, a bulb or a doorknob read as round at any
    triangle budget. The rect is sized 2*pi*r by pi*r so texels stay square
    across the equator, which is where they are actually seen.
    """

    __slots__ = ("name", "pos", "r", "seg", "ring", "surfaces", "rot",
                 "squash", "pivot")
    PARTS = ("skin",)

    def __init__(self, name, pos, radius, surfaces, seg=10, ring=6,
                 rot=None, squash=1.0, pivot=None):
        self.name = name
        self.pos = tuple(float(v) for v in pos)
        self.r, self.seg, self.ring = float(radius), int(seg), int(ring)
        self.squash = float(squash)      # <1 flattens it into a pebble
        self.rot = tuple(rot) if rot else None
        self.pivot = tuple(float(v) for v in pivot) if pivot else None
        self.surfaces = ({"skin": surfaces} if isinstance(surfaces, str)
                         else dict(surfaces))

    def face_px(self, part, density):
        return (max(6, int(round(TAU * self.r * density))),
                max(4, int(round(math.pi * self.r * density))))


TAU = math.pi * 2


def skyline_pack(items, size, pad=1):
    """Bottom-left skyline packing. Returns {key: (x, y, w, h)} or None.

    Shelf packing wasted about a third of the sheet: one tall item such as a
    barrel's wrap band set a shelf height that everything after it had to clear.
    Skyline fills the gap beside tall items, which is what lets a barrel fit a
    512 atlas instead of spilling to 1024.

    Deterministic: sorted tallest-first, ties broken by name, so the texture
    painter and the mesh builder always agree on placement.
    """
    tw, th = size
    ordered = sorted(items, key=lambda it: (-it[2], -it[1], it[0]))
    sky = [(0, 0, tw)]          # (x, y, width) segments, left to right
    out = {}

    def fits(idx, w):
        """Lowest y at which width w can rest starting at segment idx."""
        x = sky[idx][0]
        if x + w > tw:
            return None
        y, remaining, i = 0, w, idx
        while remaining > 0 and i < len(sky):
            y = max(y, sky[i][1])
            remaining -= sky[i][2]
            i += 1
        return None if remaining > 0 else y

    for key, w, h in ordered:
        w, h = w + pad, h + pad
        best = None
        for i in range(len(sky)):
            y = fits(i, w)
            if y is not None and y + h <= th and (best is None or y < best[0]
                                                  or (y == best[0] and sky[i][0] < best[1])):
                best = (y, sky[i][0], i)
        if best is None:
            return None
        y, x, _ = best
        out[key] = (x, y, w - pad, h - pad)
        # splice the new roof into the skyline
        new, consumed = [], w
        for sx, sy, sw in sky:
            if consumed <= 0 or sx + sw <= x:
                new.append((sx, sy, sw))
                continue
            if sx >= x + w:
                new.append((sx, sy, sw))
                continue
            left = x - sx
            if left > 0:
                new.append((sx, sy, left))
            right = (sx + sw) - (x + w)
            if right > 0:
                new.append((x + w, sy, right))
            consumed -= sw
        new.append((x, y + h, w))
        sky = sorted(new, key=lambda s: s[0])
    return out


ATLAS_SIZES = ((128, 128), (256, 256), (256, 512), (512, 512),
               (512, 1024), (1024, 1024))


def atlas(boxes, tier, sizes=ATLAS_SIZES):
    """Smallest atlas the prop's faces fit into, plus placements.

    Rectangular sizes are allowed: a tall prop's faces are tall, and forcing
    them square wastes half the sheet.
    """
    density = TIERS[tier]
    items, any_hidden = [], False
    for b in boxes:
        parts = (FACES if isinstance(b, Box) else
                 Sphere.PARTS if isinstance(b, Sphere) else Cylinder.PARTS)
        for p in parts:
            if b.surfaces[p] in FILLERS:
                any_hidden = True
                continue
            items.append((f"{b.name}.{p}", *b.face_px(p, density)))
    if any_hidden:
        items.append((HIDDEN_KEY, HIDDEN_PX, HIDDEN_PX))
    for size in sizes:
        placed = skyline_pack(items, size)
        if placed is not None:
            return size, placed, density
    raise ValueError(f"faces do not fit {sizes[-1]}px at {density} px/m")


def uv_rect(place, size):
    """Texel rect -> UV rect (u0, v0, u1, v1), y measured from the image top."""
    x, y, w, h = place
    tw, th = size
    return x / tw, 1.0 - (y + h) / th, (x + w) / tw, 1.0 - y / th


def build(boxes, tier):
    """Verts, quads and per-loop UVs for a box-composite prop."""
    size, placed, density = atlas(boxes, tier)
    verts, faces, uvs, surfaces, rects = [], [], [], [], []
    for b in boxes:
        base = len(verts)
        if isinstance(b, Box):
            verts.extend(b.verts())
            for f in FACES:
                key = (HIDDEN_KEY if b.surfaces[f] in FILLERS else f"{b.name}.{f}")
                u0, v0, u1, v1 = uv_rect(placed[key], size)
                faces.append(tuple(base + i for i in Box.QUADS[f]))
                uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
                surfaces.append(b.surfaces[f])
                rects.append(placed[key])
        elif isinstance(b, Sphere):
            cx, cy, cz = b.pos
            seg, ring, r = b.seg, b.ring, b.r
            u0, v0, u1, v1 = uv_rect(placed[HIDDEN_KEY if b.surfaces["skin"] in FILLERS
                                            else f"{b.name}.skin"], size)
            local = []
            for j in range(ring + 1):
                phi = math.pi * j / ring
                for i in range(seg + 1):
                    th = TAU * i / seg
                    local.append((cx + r * math.sin(phi) * math.cos(th),
                                  cy + r * math.sin(phi) * math.sin(th),
                                  cz + r * math.cos(phi) * b.squash))
            local = _rotate(local, b.pivot or b.pos, b.rot)
            verts.extend(local)
            idx = lambda j, i: base + j * (seg + 1) + i
            for j in range(ring):
                for i in range(seg):
                    a, bb = idx(j, i), idx(j, i + 1)
                    c, dd = idx(j + 1, i + 1), idx(j + 1, i)
                    ua, ub = u0 + (u1 - u0) * i / seg, u0 + (u1 - u0) * (i + 1) / seg
                    va = v1 - (v1 - v0) * j / ring
                    vb = v1 - (v1 - v0) * (j + 1) / ring
                    if j == 0:                       # top cap: triangles
                        faces.append((a, c, dd))
                        uvs.append([(ua, va), (ub, vb), (ua, vb)])
                    elif j == ring - 1:              # bottom cap
                        faces.append((a, bb, c))
                        uvs.append([(ua, va), (ub, va), (ub, vb)])
                    else:
                        faces.append((a, bb, c, dd))
                        uvs.append([(ua, va), (ub, va), (ub, vb), (ua, vb)])
                    surfaces.append(b.surfaces["skin"])
                    rects.append(placed[HIDDEN_KEY if b.surfaces["skin"] in FILLERS
                                        else f"{b.name}.skin"])
        else:
            cx, cy, cz = b.pos
            n, r, r2, hh = b.n, b.r, b.r2, b.h
            local = []
            for z, rr in ((cz, r), (cz + hh, r2)):
                for i in range(n):
                    a = TAU * i / n
                    local.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z))
            local += [(cx, cy, cz), (cx, cy, cz + hh)]
            local = _rotate(local, b.pivot or (cx, cy, cz + hh / 2), b.rot)
            verts.extend(local)
            bot_c, top_c = base + 2 * n, base + 2 * n + 1
            skey = (HIDDEN_KEY if b.surfaces["side"] in FILLERS
                    else f"{b.name}.side")
            su0, sv0, su1, sv1 = uv_rect(placed[skey], size)
            for i in range(n):
                j = (i + 1) % n
                faces.append((base + i, base + j, base + n + j, base + n + i))
                a0, a1 = su0 + (su1 - su0) * i / n, su0 + (su1 - su0) * (i + 1) / n
                uvs.append([(a0, sv0), (a1, sv0), (a1, sv1), (a0, sv1)])
                surfaces.append(b.surfaces["side"])
                rects.append(placed[skey])
            for part, centre, ring, flip in (("top", top_c, n, False),
                                             ("bottom", bot_c, 0, True)):
                pkey = (HIDDEN_KEY if b.surfaces[part] in FILLERS
                        else f"{b.name}.{part}")
                u0, v0, u1, v1 = uv_rect(placed[pkey], size)
                mu, mv = (u0 + u1) / 2, (v0 + v1) / 2
                ru, rv = (u1 - u0) / 2, (v1 - v0) / 2
                for i in range(n):
                    j = (i + 1) % n
                    ai, aj = TAU * i / n, TAU * j / n
                    pi = (mu + ru * math.cos(ai), mv + rv * math.sin(ai))
                    pj = (mu + ru * math.cos(aj), mv + rv * math.sin(aj))
                    if flip:
                        faces.append((centre, base + ring + j, base + ring + i))
                        uvs.append([(mu, mv), pj, pi])
                    else:
                        faces.append((centre, base + ring + i, base + ring + j))
                        uvs.append([(mu, mv), pi, pj])
                    surfaces.append(b.surfaces[part])
                    rects.append(placed[pkey])
    return dict(verts=verts, faces=faces, uvs=uvs, surfaces=surfaces,
                rects=rects, size=size, placed=placed, density=density)


# Below this many texels on its short side, a face's aspect is dominated by
# rounding to whole pixels rather than by the mapping. A cartridge rim is 2mm:
# 1.1 texels at the handheld density, which rounds to 2 and reports a 1.8
# ratio. That is a part under the tier's resolution, not a density fault, and
# conflating the two makes the audit cry wolf on every small detail.
MIN_MEANINGFUL_PX = 4


# face -> (axis index, which end of the box, the two in-plane axes)
_FACE_AXIS = {"front": (1, 0, (0, 2)), "back": (1, 1, (0, 2)),
              "left": (0, 0, (1, 2)), "right": (0, 1, (1, 2)),
              "bottom": (2, 0, (0, 1)), "top": (2, 1, (0, 1))}


def part_bounds(b):
    """World-space AABB of one part, computed from its actual vertices so
    rotation and pivots are accounted for."""
    if isinstance(b, Box):
        v = b.verts()
    elif isinstance(b, Sphere):
        r = b.r
        cx, cy, cz = b.pos
        return (cx - r, cy - r, cz - r * b.squash,
                cx + r, cy + r, cz + r * b.squash)
    else:
        cx, cy, cz = b.pos
        r = max(b.r, b.r2)
        v = _rotate([(cx + dx * r, cy + dy * r, cz + dz * b.h)
                     for dx in (-1, 1) for dy in (-1, 1) for dz in (0, 1)],
                    b.pivot or (cx, cy, cz + b.h / 2), b.rot)
    xs = [q[0] for q in v]; ys = [q[1] for q in v]; zs = [q[2] for q in v]
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def check_connected(parts, gap=0.004):
    """Parts that touch nothing else in the prop.

    A detached piece is the single most common way a box composite goes wrong,
    and it is invisible in a parts list. AABB adjacency is coarse - two parts
    can share a bounding box without touching - so this under-reports rather
    than crying wolf, and anything it does flag is genuinely floating.
    """
    if len(parts) < 2:
        return []
    bounds = [part_bounds(b) for b in parts]

    def touches(a, b):
        return all(min(a[i + 3], b[i + 3]) - max(a[i], b[i]) > -gap
                   for i in range(3))

    parent = list(range(len(parts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if touches(bounds[i], bounds[j]):
                parent[find(i)] = find(j)
    groups = {}
    for i in range(len(parts)):
        groups.setdefault(find(i), []).append(parts[i].name)
    if len(groups) == 1:
        return []
    biggest = max(groups.values(), key=len)
    return [n for g in groups.values() if g is not biggest for n in g]


def footprint(boxes):
    """Plan-view bounding box of a prop, in its own space: (x0, y0, x1, y1)."""
    xs, ys = [], []
    for b in boxes:
        if isinstance(b, Box):
            xs += [b.pos[0], b.pos[0] + b.size[0]]
            ys += [b.pos[1], b.pos[1] + b.size[1]]
        elif isinstance(b, Sphere):
            xs += [b.pos[0] - b.r, b.pos[0] + b.r]
            ys += [b.pos[1] - b.r, b.pos[1] + b.r]
        else:
            r = max(b.r, b.r2)
            xs += [b.pos[0] - r, b.pos[0] + r]
            ys += [b.pos[1] - r, b.pos[1] + r]
    return min(xs), min(ys), max(xs), max(ys)


def check_hidden(boxes, eps=0.004):
    """Report faces marked `hidden` that nothing actually covers.

    A hidden face shares one 4px filler rect, so if it turns out to be visible
    it renders as a flat grey slab. That is exactly what happened to the couch:
    the base top was marked hidden, but the cushions only cover the middle of
    it and the strip in front of the backrest was on screen the whole time.

    Axis-aligned parts only - a rotated part is not assumed to cover anything,
    which errs toward reporting rather than silently passing.
    """
    solid = [b for b in boxes if isinstance(b, Box) and not b.rot]
    problems = []
    for b in boxes:
        if not isinstance(b, Box):
            continue
        for f in FACES:
            if b.surfaces[f] != HIDDEN:
                continue
            axis, end, plane = _FACE_AXIS[f]
            at = b.pos[axis] + (b.size[axis] if end else 0.0)
            lo = [b.pos[i] for i in plane]
            hi = [b.pos[i] + b.size[i] for i in plane]
            covered = False
            for o in solid:
                if o is b:
                    continue
                o_lo, o_hi = o.pos[axis], o.pos[axis] + o.size[axis]
                # the other part must reach this plane from the outside
                if end and not (o_lo <= at + eps <= o_hi + eps):
                    continue
                if not end and not (o_lo - eps <= at - eps <= o_hi):
                    continue
                if all(o.pos[a] <= lo[i] + eps and
                       o.pos[a] + o.size[a] >= hi[i] - eps
                       for i, a in enumerate(plane)):
                    covered = True
                    break
            if not covered:
                problems.append(f"{b.name}.{f}")
    return problems


def density_report(boxes, tier):
    """Texel aspect for every face. check_density.py consumes this.

    Returns (worst ratio, detail rows, count of sub-resolution faces).
    """
    density = TIERS[tier]
    worst, rows, tiny = 1.0, [], 0
    for b in boxes:
        if isinstance(b, Sphere):
            pw, ph = b.face_px("skin", density)
            if min(pw, ph) < MIN_MEANINGFUL_PX:
                tiny += 1
                continue
            du, dv = pw / (TAU * b.r), ph / (math.pi * b.r)
            ratio = max(du / dv, dv / du)
            worst = max(worst, ratio)
            if ratio > 1.05:
                rows.append(f"  {b.name}.skin: {du:.0f} x {dv:.0f} px/m  ratio {ratio:.3f}")
            continue
        if not isinstance(b, Box):
            pw, ph = b.face_px("side", density)
            if min(pw, ph) < MIN_MEANINGFUL_PX:
                tiny += 1
                continue
            slant = math.hypot(b.h, b.r2 - b.r)
            du, dv = pw / (TAU * max(b.r, b.r2)), ph / max(slant, 1e-6)
            ratio = max(du / dv, dv / du)
            worst = max(worst, ratio)
            if ratio > 1.05:
                rows.append(f"  {b.name}.side: {du:.0f} x {dv:.0f} px/m  ratio {ratio:.3f}")
            continue
        dm = b.dims()
        for f in FACES:
            if b.surfaces[f] in FILLERS:
                continue
            a, c = _FACE_DIMS[f]
            pw, ph = b.face_px(f, density)
            if min(pw, ph) < MIN_MEANINGFUL_PX:
                tiny += 1
                continue
            du, dv = pw / dm[a], ph / dm[c]
            ratio = max(du / dv, dv / du)
            worst = max(worst, ratio)
            if ratio > 1.05:
                rows.append(f"  {b.name}.{f}: {du:.0f} x {dv:.0f} px/m  ratio {ratio:.3f}")
    return worst, rows, tiny
