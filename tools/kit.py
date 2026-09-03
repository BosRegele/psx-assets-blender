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

FACES = ("front", "back", "left", "right", "top", "bottom")

# A face marked "hidden" still exists in the mesh - leaving a hole would break
# shadow casting and any physics collider generated from the mesh - but it
# shares one 4px rect with every other hidden face instead of claiming atlas
# space it will never show. On the couch this is the difference between a
# 1024 and a 512 sheet.
HIDDEN = "hidden"
HIDDEN_KEY = "__hidden__"
HIDDEN_PX = 4

# face -> (which box dimensions it spans, vertex order, outward axis)
_FACE_DIMS = {"front": ("w", "h"), "back": ("w", "h"),
              "left": ("d", "h"), "right": ("d", "h"),
              "top": ("w", "d"), "bottom": ("w", "d")}


class Box:
    """An axis-aligned box. `pos` is the minimum corner, `size` is (w, d, h)
    along (x, y, z). `surfaces` maps face names to painter keys; a bare string
    applies to every face."""

    __slots__ = ("name", "pos", "size", "surfaces")

    def __init__(self, name, pos, size, surfaces):
        self.name = name
        self.pos = tuple(float(v) for v in pos)
        self.size = tuple(float(v) for v in size)
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
        return [(x, y, z), (x + w, y, z), (x + w, y + d, z), (x, y + d, z),
                (x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h),
                (x, y + d, z + h)]

    # local vertex indices per face, wound outward
    QUADS = {"front": (0, 1, 5, 4), "back": (2, 3, 7, 6),
             "left": (3, 0, 4, 7), "right": (1, 2, 6, 5),
             "top": (4, 5, 6, 7), "bottom": (3, 2, 1, 0)}


class Cylinder:
    """An N-gon prism. `pos` is the base centre. Packs as one wrap band plus
    two cap squares, all at the same density as the boxes around it."""

    __slots__ = ("name", "pos", "r", "h", "n", "surfaces")
    PARTS = ("side", "top", "bottom")

    def __init__(self, name, pos, radius, height, surfaces, n=10):
        self.name = name
        self.pos = tuple(float(v) for v in pos)
        self.r, self.h, self.n = float(radius), float(height), int(n)
        self.surfaces = ({p: surfaces for p in self.PARTS}
                         if isinstance(surfaces, str) else dict(surfaces))

    def face_px(self, part, density):
        if part == "side":
            return (max(4, int(round(TAU * self.r * density))),
                    max(2, int(round(self.h * density))))
        s = max(4, int(round(2 * self.r * density)))
        return s, s


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
        parts = FACES if isinstance(b, Box) else Cylinder.PARTS
        for p in parts:
            if b.surfaces[p] == HIDDEN:
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
                key = (HIDDEN_KEY if b.surfaces[f] == HIDDEN else f"{b.name}.{f}")
                u0, v0, u1, v1 = uv_rect(placed[key], size)
                faces.append(tuple(base + i for i in Box.QUADS[f]))
                uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
                surfaces.append(b.surfaces[f])
                rects.append(placed[key])
        else:
            cx, cy, cz = b.pos
            n, r, hh = b.n, b.r, b.h
            for z in (cz, cz + hh):
                for i in range(n):
                    a = TAU * i / n
                    verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
            bot_c, top_c = base + 2 * n, base + 2 * n + 1
            verts += [(cx, cy, cz), (cx, cy, cz + hh)]
            skey = (HIDDEN_KEY if b.surfaces["side"] == HIDDEN
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
                pkey = (HIDDEN_KEY if b.surfaces[part] == HIDDEN
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


def density_report(boxes, tier):
    """Texel aspect for every face. check_density.py consumes this."""
    density = TIERS[tier]
    worst, rows = 1.0, []
    for b in boxes:
        if not isinstance(b, Box):
            pw, ph = b.face_px("side", density)
            du, dv = pw / (TAU * b.r), ph / b.h
            ratio = max(du / dv, dv / du)
            worst = max(worst, ratio)
            if ratio > 1.05:
                rows.append(f"  {b.name}.side: {du:.0f} x {dv:.0f} px/m  ratio {ratio:.3f}")
            continue
        dm = b.dims()
        for f in FACES:
            if b.surfaces[f] == HIDDEN:
                continue
            a, c = _FACE_DIMS[f]
            pw, ph = b.face_px(f, density)
            du, dv = pw / dm[a], ph / dm[c]
            ratio = max(du / dv, dv / du)
            worst = max(worst, ratio)
            if ratio > 1.05:
                rows.append(f"  {b.name}.{f}: {du:.0f} x {dv:.0f} px/m  ratio {ratio:.3f}")
    return worst, rows
