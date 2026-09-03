"""The three prop textures.

Atlas rectangles are NOT hand-placed here - they come from geometry.py, which
derives them from the mesh geometry at a single fixed texel density. That is
what keeps texels square on a curved surface; laying the atlas out by eye is
exactly how you end up with 13:1 slivers on a bottle neck.
"""
import numpy as np
from PIL import ImageDraw
import palette, texgen as T, geometry as P


def can():
    """Body label occupies rows 0..CAN_BODY_ROWS and wraps 360 degrees.
    Lid and base discs sit below it at their true texel radius. All label
    furniture is proportional to the band so it survives a density change."""
    w, h = P.CAN_TEX
    body = P.CAN_BODY_ROWS
    y = lambda f: int(body * f)
    tin = T.from_ramp(0.35 + 0.5 * T.fbm(h, w, seed=10, octaves=(48, 24, 12)), "tin")
    rgb = T.grime(tin, T.fbm(h, w, seed=11), 0.30)

    paper = T.from_ramp(0.55 + 0.4 * T.fbm(h, w, seed=12, octaves=(48, 24, 12)), "paper")
    paper = T.grime(paper, T.fbm(h, w, seed=13), 0.5)
    mask = np.zeros((h, w), dtype=bool)
    mask[0:body] = True
    rgb = np.where(mask[..., None], paper, rgb)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, y(0.09)], fill=T.px("olive", 1))
    T.wordmark(d, (5, y(0.13), w - 5, y(0.35)), seed=21, colour=T.px("void", 0))
    d.rectangle([0, y(0.40), w - 1, y(0.46)], fill=T.px("red", 1))
    T.smallprint(d, (8, y(0.53), w - 9, y(0.93)), T.px("paper", 0), seed=22, gap=4)
    d.rectangle([0, body - 3, w - 1, body - 1], fill=T.px("olive", 0))

    r, cy = P.CAN_DISC_R, P.CAN_DISC_Y
    for cx, shade in ((r + 2, 3), (3 * r + 6, 1)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=T.px("tin", shade))
        for rr in range(r - 3, 1, -4):
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                      outline=T.px("tin", max(0, shade - 1)))

    T.scratches(img, 70, T.px("tin", 4), seed=23, length=6)
    T.scratches(img, 24, T.px("rust", 1), seed=24, length=4)
    return np.asarray(img, dtype=np.float32)


def bottle():
    """Bands come from profile.band(); V is arc length, U is radius-scaled."""
    w, h = P.BOTTLE_TEX
    cap, neck, shoulder = P.band("cap"), P.band("neck"), P.band("shoulder")
    label, lower = P.band("label"), P.band("lower")

    # wide tonal range plus vertical runs, so the dither breaks up instead
    # of settling into one regular pattern across the whole neck
    base = 0.15 + 0.85 * T.fbm(h, w, seed=30, octaves=(64, 32, 12, 5))
    base = np.clip(base + 0.28 * T.streaks(h, w, 16, seed=37), 0, 1)
    glass = T.from_ramp(base, "glass")
    rgb = T.grime(glass, T.fbm(h, w, seed=31), 0.35)
    lab = T.from_ramp(0.5 + 0.45 * T.fbm(h, w, seed=32, octaves=(48, 24, 12)), "paper")
    lab = T.grime(lab, T.fbm(h, w, seed=33), 0.45)
    mask = np.zeros((h, w), dtype=bool)
    mask[label[0]:label[1]] = True
    rgb = np.where(mask[..., None], lab, rgb)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)

    # foil cap, knurled. U scale on the cap is 0.38, so the ribs are drawn at
    # 0.38 of the width and still land at the right world-space pitch.
    d.rectangle([0, cap[0], w - 1, cap[1] - 1], fill=T.px("red", 2))
    for x in range(0, w, 3):
        d.line([(x, cap[0] + 1), (x, cap[1] - 3)], fill=T.px("red", 1))
    d.rectangle([0, cap[1] - 3, w - 1, cap[1] - 1], fill=T.px("red", 0))

    # one vertical specular column per glass band - the only cue that reads
    # as glass with no specular shading at all
    for y0, y1 in (neck, shoulder, lower):
        for x in range(13, 20):
            d.line([(x, y0), (x, y1 - 1)], fill=T.px("glass", 3))
        d.line([(16, y0), (16, y1 - 1)], fill=T.px("concrete", 1))

    # label furniture, sized off the band so it scales with the geometry
    lh = label[1] - label[0]
    d.rectangle([0, label[0], w - 1, label[0] + 2], fill=T.px("red", 1))
    d.rectangle([0, label[1] - 3, w - 1, label[1] - 1], fill=T.px("red", 1))
    d.rectangle([0, label[0] + 8, w - 1, label[0] + 10], fill=T.px("olive", 1))
    T.wordmark(d, (8, label[0] + 14, w - 8, label[0] + lh // 2 + 4),
               seed=34, rows=1, colour=T.px("red", 0))
    T.smallprint(d, (12, label[0] + lh // 2 + 8, w - 12, label[1] - 6),
                 T.px("paper", 0), seed=35, gap=3)

    T.scratches(img, 70, T.px("glass", 3), seed=36, length=6)
    return np.asarray(img, dtype=np.float32)


def pack():
    """Six faces, each rect at its true aspect ratio; see geometry.PACK_ATLAS."""
    w, h = P.PACK_TEX
    A = P.PACK_ATLAS
    card = T.from_ramp(0.45 + 0.45 * T.fbm(h, w, seed=40, octaves=(48, 24, 12)), "paper")
    rgb = T.grime(card, T.fbm(h, w, seed=41), 0.40)
    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)

    fx0, fy0, fx1, fy1 = A["front"]
    fh = fy1 - fy0
    f = lambda t: fy0 + int(fh * t)
    d.rectangle([fx0, fy0, fx1 - 1, fy1 - 1], fill=T.px("olive", 1))
    T.wordmark(d, (fx0 + 3, f(0.08), fx1 - 3, f(0.30)), seed=42,
               colour=T.px("paper", 4))
    d.rectangle([fx0, f(0.36), fx1 - 1, f(0.45)], fill=T.px("red", 2))
    T.smallprint(d, (fx0 + 4, f(0.52), fx1 - 4, f(0.74)), T.px("olive", 3),
                 seed=43, gap=3)
    d.rectangle([fx0, f(0.84), fx1 - 1, fy1 - 1], fill=T.px("void", 1))
    T.smallprint(d, (fx0 + 3, f(0.87), fx1 - 4, fy1 - 3), T.px("paper", 2),
                 seed=44, gap=2)

    bx0, by0, bx1, by1 = A["back"]
    d.rectangle([bx0, by0, bx1 - 1, by1 - 1], fill=T.px("olive", 0))
    T.smallprint(d, (bx0 + 4, by0 + 6, bx1 - 4, by1 - 12), T.px("olive", 3),
                 seed=45, gap=4)
    d.rectangle([bx0, by1 - int(fh * 0.16), bx1 - 1, by1 - 1], fill=T.px("void", 1))

    for key, seed in (("left", 46), ("right", 48)):
        x0, y0, x1, y1 = A[key]
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=T.px("olive", 1))
        T.smallprint(d, (x0 + 1, y0 + 4, x1 - 2, y1 - 4), T.px("olive", 3),
                     seed=seed, gap=4)

    tx0, ty0, tx1, ty1 = A["top"]
    d.rectangle([tx0, ty0, tx1 - 1, ty1 - 1], fill=T.px("paper", 3))
    step = max(4, (tx1 - tx0) // 7)
    for i in range((tx1 - tx0 - 2) // step):
        for j in range(max(1, (ty1 - ty0 - 2) // step)):
            x, y = tx0 + 2 + i * step, ty0 + 2 + j * step
            d.ellipse([x, y, x + step - 2, y + step - 2], fill=T.px("paper", 4),
                      outline=T.px("rust", 1))
    ox0, oy0, ox1, oy1 = A["bottom"]
    d.rectangle([ox0, oy0, ox1 - 1, oy1 - 1], fill=T.px("paper", 1))

    T.scratches(img, 45, T.px("paper", 4), seed=47, length=5)
    return np.asarray(img, dtype=np.float32)


BUILDERS = {"can": can, "bottle": bottle, "pack": pack}

if __name__ == "__main__":
    import os
    os.makedirs("../assets/textures", exist_ok=True)
    for name, fn in BUILDERS.items():
        p = f"../assets/textures/{name}_d.png"
        palette.save(fn(), p, strength=20.0)
        print("wrote", p)
