"""Tileable architecture surfaces: walls, floor, ceiling.

A 6m wall cannot have its own atlas - at the bundle density that is a 1100px
face. Architecture tiles instead, which is what every shipped game does. The
texel density is identical to the furniture tier (184 px/m), so a 512 tile
covers 2.78m and a wall next to a locker has the same pixel size. That is the
whole point: the moment the wall is coarser than the props in front of it, the
props start to look pasted on.

Every drawn feature is wrapped to the tile edges. Value noise happens to tile
for free - nearest-neighbour upscaled blocks have no continuity to break - but
a crack drawn near an edge would stop dead at the seam.
"""
import numpy as np
from PIL import Image, ImageDraw
import palette, texgen as T
import kit

DENSITY = kit.TIERS["furniture"]
TILE = kit.ARCH_TILE            # 2.78 m at 184 px/m
GRAIN_M = (0.045, 0.022, 0.010)


def _oct():
    return tuple(max(2, int(round(g * DENSITY))) for g in GRAIN_M)


def wrapped(size, fn):
    """Run a draw callback nine times, offset by the tile, so anything that
    crosses an edge reappears on the far side. Cheap, and it is the only way a
    hand-drawn crack survives tiling."""
    def go(d):
        for dx in (-size, 0, size):
            for dy in (-size, 0, size):
                fn(d, dx, dy)
    return go


def crack(d, x, y, length, seed, colour, dx=0, dy=0, width=1):
    """A wandering hairline. Cracks branch; a straight line reads as a scratch."""
    rng = np.random.default_rng(seed)
    px, py = x + dx, y + dy
    ang = rng.uniform(0, 6.28)
    for _ in range(length):
        ang += rng.uniform(-0.55, 0.55)
        nx, ny = px + np.cos(ang) * 3, py + np.sin(ang) * 3
        d.line([(px, py), (nx, ny)], fill=colour, width=width)
        px, py = nx, ny
        if rng.random() < 0.06:
            b = ang + rng.uniform(-1.2, 1.2)
            d.line([(px, py), (px + np.cos(b) * 9, py + np.sin(b) * 9)],
                   fill=colour, width=1)


def _m(metres):
    """Metres -> texels at the architecture density."""
    return max(1, int(round(metres * DENSITY)))


def shade(rgb, mask, amount):
    """Darken by a 0..1 mask. Wear multiplies the surface; it does not cover it."""
    return rgb * (1.0 - amount * mask[..., None])


def lighten(rgb, mask, amount):
    return rgb + (255.0 - rgb) * (amount * mask[..., None])


def concrete_base(size, seed, lo, hi, grime):
    o = _oct()
    n = T.fbm(size, size, seed=seed, octaves=o)
    rgb = T.from_ramp(lo + (hi - lo) * n, "concrete")
    return T.grime(rgb, T.fbm(size, size, seed=seed + 401, octaves=o), grime)


def wall(size=TILE, seed=900):
    """Bunker wall: board-formed concrete, damp running from the tie holes,
    spalled patches where the render has come away."""
    rgb = concrete_base(size, seed, 0.16, 0.58, 0.38)

    # damp: noise stretched hard on the vertical axis so it runs, not mottles
    damp = T.blotch(size, size, _m(0.10), _m(1.30), 0.52, seed + 11, octaves=4)
    rgb = shade(rgb, damp, 0.50)
    # a second, tighter pass gives the dark cores inside the wet areas
    rgb = shade(rgb, damp * T.blotch(size, size, _m(0.05), _m(0.6), 0.62,
                                     seed + 12), 0.35)

    # spalling: broad irregular patches lightened to bare aggregate
    spall = T.blotch(size, size, _m(0.35), _m(0.30), 0.66, seed + 13, octaves=4)
    rgb = lighten(rgb, spall, 0.22)
    rgb = shade(rgb, T.blotch(size, size, _m(0.06), _m(0.06), 0.55, seed + 14)
                * spall, 0.30)

    # efflorescence: pale salt bloom, sparse
    rgb = lighten(rgb, T.blotch(size, size, _m(0.5), _m(0.5), 0.78, seed + 15), 0.28)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)

    # shuttering board lines every 600mm - a real geometric feature, so drawn
    pitch = _m(0.60)
    for y in range(0, size, pitch):
        d.line([(0, y), (size, y)], fill=T.px("concrete", 0))
        d.line([(0, y + 1), (size, y + 1)], fill=T.px("concrete", 2))

    # form-tie holes on the board lines, each with a rust weep
    for y in range(pitch // 2, size, pitch):
        for x in range(_m(0.9) // 2, size, _m(0.9)):
            r = max(1, _m(0.011))
            d.ellipse([x - r, y - r, x + r, y + r], fill=T.px("void", 1))
            d.ellipse([x - r, y - r, x, y], fill=T.px("rust", 1))

    for i in range(8):
        x, y = int(rng.integers(0, size)), int(rng.integers(0, size))
        wrapped(size, lambda dd, dx, dy, x=x, y=y, i=i:
                crack(dd, x, y, 30, seed + 60 + i, T.px("void", 1), dx, dy))(d)

    T.scratches(img, 200, T.px("concrete", 3), seed=seed + 7, length=9)
    return np.asarray(img, dtype=np.float32)


def floor(size=TILE, seed=910):
    """Worn screed: polished traffic lanes, ground-in dirt, drum rust rings."""
    rgb = concrete_base(size, seed, 0.12, 0.50, 0.42)

    # traffic polish - broad, slightly directional
    polish = T.blotch(size, size, _m(1.10), _m(0.55), 0.50, seed + 21, octaves=4)
    rgb = lighten(rgb, polish, 0.20)
    # ground-in dirt collects where the polish is not
    rgb = shade(rgb, T.blotch(size, size, _m(0.45), _m(0.45), 0.48, seed + 22,
                              octaves=4) * (1.0 - polish * 0.7), 0.46)
    # oil: small, very dark, tight
    rgb = shade(rgb, T.blotch(size, size, _m(0.20), _m(0.20), 0.74, seed + 23), 0.55)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed + 3)

    pitch = _m(1.40)
    for k in range(0, size, pitch):
        d.line([(k, 0), (k, size)], fill=T.px("void", 1))
        d.line([(0, k), (size, k)], fill=T.px("void", 1))
        d.line([(k + 1, 0), (k + 1, size)], fill=T.px("concrete", 2))

    def rings(dd, dx, dy):
        for _ in range(4):
            x = int(rng.integers(0, size)) + dx
            y = int(rng.integers(0, size)) + dy
            r = int(rng.integers(_m(0.18), _m(0.30)))
            dd.arc([x - r, y - r, x + r, y + r],
                   int(rng.integers(0, 180)), int(rng.integers(200, 360)),
                   fill=T.px("rust", 0), width=max(1, _m(0.010)))
    wrapped(size, rings)(d)

    for i in range(5):
        x, y = int(rng.integers(0, size)), int(rng.integers(0, size))
        wrapped(size, lambda dd, dx, dy, x=x, y=y, i=i:
                crack(dd, x, y, 36, seed + 40 + i, T.px("void", 1), dx, dy))(d)

    T.scratches(img, 380, T.px("concrete", 3), seed=seed + 9, length=13)
    return np.asarray(img, dtype=np.float32)


def ceiling(size=TILE, seed=920):
    """Soffit: darker, sooty, with condensation blooms and rust weeps."""
    rgb = concrete_base(size, seed, 0.08, 0.38, 0.42)
    rgb = shade(rgb, T.blotch(size, size, _m(0.60), _m(0.60), 0.52, seed + 31,
                              octaves=4), 0.45)
    rgb = shade(rgb, T.blotch(size, size, _m(0.15), _m(0.15), 0.70, seed + 32), 0.40)
    bloom = T.blotch(size, size, _m(0.30), _m(0.30), 0.72, seed + 33)
    rgb = rgb * (1 - 0.5 * bloom[..., None]) +         np.array(T.px("rust", 0), dtype=np.float32) * 0.5 * bloom[..., None]

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)
    pitch = _m(0.90)
    for x in range(0, size, pitch):
        d.line([(x, 0), (x, size)], fill=T.px("void", 1))
        d.line([(x + 1, 0), (x + 1, size)], fill=T.px("concrete", 1))
    return np.asarray(img, dtype=np.float32)


SURFACES = {"wall": wall, "floor": floor, "ceiling": ceiling}


def bake(out_dir):
    import os
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for name, fn in SURFACES.items():
        p = os.path.join(out_dir, f"ARCH_{name}_d.png")
        palette.save(fn(), p, strength=18.0)
        paths[name] = p
        print(f"ARCH_{name}: {TILE}x{TILE} = {TILE / DENSITY:.2f}m tile "
              f"at {DENSITY:.0f} px/m")
    return paths


if __name__ == "__main__":
    import os
    bake(os.path.join(os.path.dirname(__file__), "..", "assets", "textures"))
