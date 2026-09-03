"""Surface painters. Each fills one packed atlas rectangle.

A painter is registered by name and referenced from a prop declaration, so
adding a prop never means writing new drawing code - only picking surfaces.

Every face gets `edge_shade` last. PS1-era art baked ambient occlusion into the
texture because there was no runtime shadowing, and it is the single thing that
stops a box composite reading as a pile of untextured blocks.
"""
import numpy as np
from PIL import ImageDraw
import texgen as T

PAINTERS = {}


def painter(name):
    def deco(fn):
        PAINTERS[name] = fn
        return fn
    return deco


# Grain is specified in METRES, not pixels. Sizing noise off the face meant a
# 1.85m locker got 37px blocks and a 0.15m tin got 3px ones, so the same
# painter produced two different materials. At world scale, steel looks like
# steel whatever it is wrapped around.
GRAIN_M = (0.045, 0.022, 0.010)


def _oct(density):
    return tuple(max(2, int(round(g * density))) for g in GRAIN_M)


def base(img, rect, ramp, lo, hi, seed, grime=0.25, density=184.0):
    x, y, w, h = rect
    o = _oct(density)
    n = T.fbm(h, w, seed=seed, octaves=o)
    rgb = T.from_ramp(lo + (hi - lo) * n, ramp)
    rgb = T.grime(rgb, T.fbm(h, w, seed=seed + 977, octaves=o), grime)
    img.paste(T.to_pil(rgb), (x, y))
    return ImageDraw.Draw(img)


def edge_shade(d, rect, ramp):
    """Darken the border. Depth scales with the face so small parts do not go
    solid black and large ones still read as having thickness."""
    x, y, w, h = rect
    depth = max(1, min(w, h) // 22)
    for i in range(depth):
        d.rectangle([x + i, y + i, x + w - 1 - i, y + h - 1 - i],
                    outline=T.px(ramp, 0))


def _in(rect, m):
    x, y, w, h = rect
    return [x + m, y + m, x + w - 1 - m, y + h - 1 - m]


# --- metals ----------------------------------------------------------------
@painter("steel")
def steel(img, rect, seed, density=184.0):
    d = base(img, rect, "tin", 0.36, 0.64, seed, 0.22, density=density)
    T.scratches(img, max(3, rect[2] * rect[3] // 900), T.px("tin", 4),
                seed=seed + 5, length=max(3, rect[2] // 10),
                ybox=(rect[1], rect[1] + rect[3]))
    edge_shade(d, rect, "tin")
    return d


@painter("steel_worn")
def steel_worn(img, rect, seed, density=184.0):
    d = base(img, rect, "tin", 0.34, 0.58, seed, 0.26, density=density)
    x, y, w, h = rect
    rng = np.random.default_rng(seed + 11)
    # Rust is a stain, not a rash. Few blooms, each built from several small
    # overlapping lobes so the silhouette is ragged, and the bright tone used
    # only as a small core - a solid bright disc reads as a painted dot.
    for _ in range(max(1, w * h // 14000)):
        cx, cy = int(rng.integers(x, x + w)), int(rng.integers(y, y + h))
        r = int(rng.integers(2, max(3, min(w, h) // 11)))
        for _ in range(4):
            ox, oy = int(rng.integers(-r, r + 1)), int(rng.integers(-r, r + 1))
            rr = max(1, int(r * rng.uniform(0.4, 0.9)))
            d.ellipse([cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr],
                      fill=T.px("rust", 0))
        d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3],
                  fill=T.px("rust", 1))
    T.scratches(img, max(4, w * h // 700), T.px("tin", 4), seed=seed + 5,
                length=max(3, w // 8), ybox=(y, y + h))
    edge_shade(d, rect, "tin")
    return d


@painter("steel_panel")
def steel_panel(img, rect, seed, density=184.0):
    """Riveted plate: an inset panel line plus corner rivets."""
    d = steel(img, rect, seed, density)
    x, y, w, h = rect
    m = max(2, min(w, h) // 9)
    if w > 12 and h > 12:
        d.rectangle(_in(rect, m), outline=T.px("tin", 1))
        for px_, py in ((x + m, y + m), (x + w - 1 - m, y + m),
                        (x + m, y + h - 1 - m), (x + w - 1 - m, y + h - 1 - m)):
            d.point((px_, py), fill=T.px("tin", 4))
    return d


@painter("steel_door")
def steel_door(img, rect, seed, density=184.0):
    """Locker door: inset panel, vent slits, handle, hinges."""
    d = steel_worn(img, rect, seed, density)
    x, y, w, h = rect
    m = max(2, min(w, h) // 10)
    d.rectangle(_in(rect, m), outline=T.px("tin", 1))
    for i in range(4):
        sy = y + h // 8 + i * max(2, h // 40)
        d.line([(x + w // 3, sy), (x + 2 * w // 3, sy)], fill=T.px("void", 1))
    hx = x + w - max(3, w // 6)
    d.rectangle([hx - max(1, w // 40), y + h // 2 - max(2, h // 14),
                 hx + max(1, w // 40), y + h // 2 + max(2, h // 14)],
                fill=T.px("tin", 4), outline=T.px("void", 1))
    for hy in (y + h // 6, y + 5 * h // 6):
        d.rectangle([x + 1, hy - max(1, h // 40), x + max(3, w // 12),
                     hy + max(1, h // 40)], fill=T.px("tin", 1))
    edge_shade(d, rect, "tin")
    return d


@painter("steel_drawer")
def steel_drawer(img, rect, seed, density=184.0):
    d = steel(img, rect, seed, density)
    x, y, w, h = rect
    d.rectangle(_in(rect, max(2, min(w, h) // 8)), outline=T.px("tin", 1))
    d.rectangle([x + w // 3, y + h // 2 - max(1, h // 12),
                 x + 2 * w // 3, y + h // 2 + max(1, h // 12)],
                fill=T.px("tin", 4), outline=T.px("void", 1))
    if w > 24 and h > 16:
        d.rectangle([x + w // 8, y + h // 5, x + w // 3, y + h // 3],
                    fill=T.px("paper", 3), outline=T.px("void", 1))
    edge_shade(d, rect, "tin")
    return d


@painter("olive_metal")
def olive_metal(img, rect, seed, density=184.0):
    d = base(img, rect, "olive", 0.25, 0.72, seed, 0.35, density=density)
    T.scratches(img, max(3, rect[2] * rect[3] // 1100), T.px("olive", 3),
                seed=seed + 5, length=max(3, rect[2] // 9),
                ybox=(rect[1], rect[1] + rect[3]))
    edge_shade(d, rect, "olive")
    return d


@painter("olive_stencil")
def olive_stencil(img, rect, seed, density=184.0):
    """Ammo crate face: olive with a stencilled lot number."""
    d = olive_metal(img, rect, seed, density)
    x, y, w, h = rect
    if w > 26 and h > 14:
        s = "ЯЩ-7.62"
        f = T.fit("display", s, int(w * 0.62), max(4, int(h * 0.24)))
        T.text(d, (x + w // 2, y + int(h * 0.30)), s, f, T.px("paper", 2),
               centre=True, track=1)
        T.smallprint(d, (x + w // 4, y + int(h * 0.62), x + 3 * w // 4,
                         y + int(h * 0.80)), T.px("olive", 3), seed=seed + 3, gap=3)
    edge_shade(d, rect, "olive")
    return d


# --- timber ----------------------------------------------------------------
@painter("wood")
def wood(img, rect, seed, density=184.0):
    d = base(img, rect, "wood", 0.30, 0.78, seed, 0.30, density=density)
    x, y, w, h = rect
    rng = np.random.default_rng(seed + 21)
    for _ in range(max(3, w // 5)):
        gy = int(rng.integers(y, y + h))
        d.line([(x, gy), (x + w, gy + int(rng.integers(-1, 2)))],
               fill=T.px("wood", int(rng.integers(0, 2))))
    edge_shade(d, rect, "wood")
    return d


@painter("wood_planks")
def wood_planks(img, rect, seed, density=184.0):
    d = wood(img, rect, seed, density)
    x, y, w, h = rect
    n = max(2, min(5, h // 8))
    for i in range(1, n):
        py = y + i * h // n
        d.line([(x, py), (x + w - 1, py)], fill=T.px("wood", 0))
        if py + 1 < y + h:
            d.line([(x, py + 1), (x + w - 1, py + 1)], fill=T.px("wood", 2))
    edge_shade(d, rect, "wood")
    return d


# --- soft goods ------------------------------------------------------------
@painter("fabric")
def fabric(img, rect, seed, density=184.0):
    d = base(img, rect, "fabric", 0.25, 0.75, seed, 0.32, density=density)
    x, y, w, h = rect
    rng = np.random.default_rng(seed + 31)
    for _ in range(max(1, w * h // 2600)):
        cx, cy = rng.integers(x, x + w), rng.integers(y, y + h)
        r = int(rng.integers(2, max(3, min(w, h) // 5)))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=T.px("fabric", 0))
    edge_shade(d, rect, "fabric")
    return d


@painter("fabric_seam")
def fabric_seam(img, rect, seed, density=184.0):
    """Cushion face: piped seam just inside the edge."""
    d = fabric(img, rect, seed, density)
    x, y, w, h = rect
    m = max(2, min(w, h) // 8)
    if w > 12 and h > 12:
        d.rectangle(_in(rect, m), outline=T.px("fabric", 3))
        for sx in range(x + m, x + w - m, 3):
            d.point((sx, y + m), fill=T.px("fabric", 0))
    edge_shade(d, rect, "fabric")
    return d


@painter("canvas")
def canvas(img, rect, seed, density=184.0):
    d = base(img, rect, "olive", 0.32, 0.70, seed, 0.30, density=density)
    x, y, w, h = rect
    for wy in range(y, y + h, 3):
        d.line([(x, wy), (x + w - 1, wy)], fill=T.px("olive", 1))
    edge_shade(d, rect, "olive")
    return d


@painter("rubber")
def rubber(img, rect, seed, density=184.0):
    d = base(img, rect, "rubber", 0.30, 0.85, seed, 0.20, density=density)
    edge_shade(d, rect, "rubber")
    return d


# --- misc ------------------------------------------------------------------
@painter("concrete")
def concrete(img, rect, seed, density=184.0):
    d = base(img, rect, "concrete", 0.20, 0.70, seed, 0.35, density=density)
    edge_shade(d, rect, "concrete")
    return d


@painter("paper")
def paper(img, rect, seed, density=184.0):
    d = base(img, rect, "paper", 0.55, 0.92, seed, 0.20, density=density)
    edge_shade(d, rect, "paper")
    return d


@painter("map")
def wall_map(img, rect, seed, density=184.0):
    """A situation map: contour blobs, a grid, roads, and grease-pencil marks."""
    d = base(img, rect, "paper", 0.62, 0.95, seed, 0.16, density=density)
    x, y, w, h = rect
    rng = np.random.default_rng(seed + 41)
    for _ in range(max(3, w * h // 1400)):
        cx, cy = rng.integers(x, x + w), rng.integers(y, y + h)
        r = int(rng.integers(3, max(4, min(w, h) // 3)))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=T.px("olive", 2))
        d.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2],
                  outline=T.px("olive", 2))
    step = max(6, min(w, h) // 6)
    for gx in range(x + step, x + w, step):
        d.line([(gx, y), (gx, y + h - 1)], fill=T.px("concrete", 1))
    for gy in range(y + step, y + h, step):
        d.line([(x, gy), (x + w - 1, gy)], fill=T.px("concrete", 1))
    for _ in range(max(2, w * h // 3000)):
        pts = [(int(rng.integers(x, x + w)), int(rng.integers(y, y + h)))
               for _ in range(3)]
        d.line(pts, fill=T.px("rust", 1))
    for _ in range(max(1, w * h // 4500)):
        cx, cy = rng.integers(x, x + w), rng.integers(y, y + h)
        r = int(rng.integers(3, max(4, min(w, h) // 5)))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=T.px("red", 2))
    edge_shade(d, rect, "paper")
    return d


@painter("glass_lens")
def glass_lens(img, rect, seed, density=184.0):
    d = base(img, rect, "glass", 0.45, 0.95, seed, 0.10, density=density)
    x, y, w, h = rect
    d.ellipse(_in(rect, max(1, min(w, h) // 8)), outline=T.px("rubber", 2))
    d.line([(x + w // 4, y + h // 4), (x + w // 2, y + h // 2)],
           fill=T.px("glass", 3))
    edge_shade(d, rect, "rubber")
    return d


@painter("dark")
def dark(img, rect, seed, density=184.0):
    return base(img, rect, "void", 0.0, 0.9, seed, 0.10, density=density)


@painter("enamel")
def enamel(img, rect, seed, density=184.0):
    """Chipped enamelware: pale blue-white with dark chips at the edges."""
    d = base(img, rect, "concrete", 0.62, 0.98, seed, 0.16, density=density)
    x, y, w, h = rect
    rng = np.random.default_rng(seed + 51)
    for _ in range(max(1, w * h // 5200)):
        cx, cy = int(rng.integers(x, x + w)), int(rng.integers(y, y + h))
        r = max(1, int(rng.integers(1, max(2, min(w, h) // 22))))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=T.px("void", 1))
    edge_shade(d, rect, "concrete")
    return d


@painter("cardboard")
def cardboard(img, rect, seed, density=184.0):
    d = base(img, rect, "paper", 0.34, 0.66, seed, 0.30, density=density)
    edge_shade(d, rect, "paper")
    return d


@painter("label_red")
def label_red(img, rect, seed, density=184.0):
    """Printed consumer label: a red field with a stencilled word."""
    d = base(img, rect, "paper", 0.62, 0.94, seed, 0.18, density=density)
    x, y, w, h = rect
    d.rectangle([x, y + h // 5, x + w - 1, y + h // 2], fill=T.px("red", 2))
    if w > 22 and h > 16:
        f = T.fit("heavy", "ДИХЛО", int(w * 0.72), max(4, h // 5))
        T.text(d, (x + w // 2, y + h // 5 + 1), "ДИХЛО", f, T.px("paper", 4),
               centre=True, track=1)
        T.smallprint(d, (x + w // 6, y + int(h * 0.60), x + 5 * w // 6,
                         y + int(h * 0.85)), T.px("void", 1), seed=seed, gap=3)
    edge_shade(d, rect, "paper")
    return d


@painter("bread")
def bread(img, rect, seed, density=184.0):
    d = base(img, rect, "wood", 0.45, 0.92, seed, 0.22, density=density)
    x, y, w, h = rect
    rng = np.random.default_rng(seed + 61)
    for _ in range(max(2, w * h // 700)):      # crumb pitting
        cx, cy = int(rng.integers(x, x + w)), int(rng.integers(y, y + h))
        d.point((cx, cy), fill=T.px("wood", 1))
    edge_shade(d, rect, "wood")
    return d


@painter("meat")
def meat(img, rect, seed, density=184.0):
    d = base(img, rect, "rust", 0.30, 0.85, seed, 0.25, density=density)
    edge_shade(d, rect, "rust")
    return d


@painter("ash")
def ash(img, rect, seed, density=184.0):
    """Ashtray interior: grey ash with butt ends."""
    d = base(img, rect, "concrete", 0.20, 0.55, seed, 0.30, density=density)
    x, y, w, h = rect
    rng = np.random.default_rng(seed + 71)
    for _ in range(max(3, w * h // 500)):
        cx, cy = int(rng.integers(x, x + w)), int(rng.integers(y, y + h))
        ln = max(2, int(rng.integers(2, max(3, w // 6))))
        d.line([(cx, cy), (cx + ln, cy + int(rng.integers(-1, 2)))],
               fill=T.px("paper", 3))
        d.point((cx, cy), fill=T.px("rust", 1))
    edge_shade(d, rect, "concrete")
    return d


@painter("chrome")
def chrome(img, rect, seed, density=184.0):
    d = base(img, rect, "tin", 0.55, 0.95, seed, 0.12, density=density)
    edge_shade(d, rect, "tin")
    return d


@painter("brass")
def brass_(img, rect, seed, density=184.0):
    d = base(img, rect, "brass", 0.42, 0.95, seed, 0.14, density=density)
    edge_shade(d, rect, "brass")
    return d


@painter("copper")
def copper(img, rect, seed, density=184.0):
    d = base(img, rect, "rust", 0.55, 0.95, seed, 0.12, density=density)
    edge_shade(d, rect, "rust")
    return d


@painter("gunmetal")
def gunmetal(img, rect, seed, density=184.0):
    """Blued steel: darker and tighter than the galvanised `steel` used on
    furniture, so a weapon does not read as a filing cabinet."""
    d = base(img, rect, "rubber", 0.40, 0.85, seed, 0.16, density=density)
    x, y, w, h = rect
    T.scratches(img, max(2, w * h // 1600), T.px("tin", 2), seed=seed + 5,
                length=max(3, w // 8), ybox=(y, y + h))
    edge_shade(d, rect, "rubber")
    return d


@painter("emitter")
def emitter(img, rect, seed, density=184.0):
    """The lit face of a fixture. The scene gives this its own emissive
    material slot; the texture is only what it looks like switched off."""
    x, y, w, h = rect
    ImageDraw.Draw(img).rectangle([x, y, x + w - 1, y + h - 1],
                                  fill=T.px("paper", 4))
    return ImageDraw.Draw(img)


@painter("coat")
def coat(img, rect, seed, density=184.0):
    d = base(img, rect, "olive", 0.18, 0.52, seed, 0.34, density=density)
    x, y, w, h = rect
    for cy in range(y + h // 4, y + h, max(3, h // 5)):   # fold shadows
        d.line([(x, cy), (x + w - 1, cy)], fill=T.px("olive", 0))
    edge_shade(d, rect, "olive")
    return d


@painter("trash")
def trash(img, rect, seed, density=184.0):
    """Indeterminate refuse: torn paper, wet card, rust, and grease. Reads as
    a heap precisely because no single material dominates."""
    o = _oct(density)
    x, y, w, h = rect
    n = T.fbm(h, w, seed=seed, octaves=o)
    ramps = ("paper", "rust", "concrete", "olive")
    rgb = T.from_ramp(0.25 + 0.6 * n, ramps[seed % len(ramps)])
    sel = T.blotch(h, w, max(2, o[0]), max(2, o[0]), 0.45, seed + 5)
    rgb = rgb * (1 - sel[..., None]) +         T.from_ramp(0.2 + 0.6 * n, ramps[(seed + 1) % len(ramps)]) * sel[..., None]
    rgb = T.grime(rgb, T.fbm(h, w, seed=seed + 91, octaves=o), 0.45)
    img.paste(T.to_pil(rgb), (x, y))
    d = ImageDraw.Draw(img)
    edge_shade(d, rect, "void")
    return d


@painter("hidden")
def hidden(img, rect, seed, density=184.0):
    """The shared filler rect. Flat mid-tone: it is never seen, but a
    conspicuous colour would bleed through at grazing angles."""
    x, y, w, h = rect
    ImageDraw.Draw(img).rectangle([x, y, x + w - 1, y + h - 1],
                                  fill=T.px("concrete", 1))


def paint(img, name, rect, seed, density=184.0):
    return PAINTERS[name](img, rect, seed, density)
