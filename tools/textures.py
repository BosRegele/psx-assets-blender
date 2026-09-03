"""The three prop textures.

Atlas rectangles are NOT hand-placed here - they come from geometry.py, which
derives them from the mesh geometry at a single fixed texel density. That is
what keeps texels square on a curved surface; laying the atlas out by eye is
exactly how you end up with 13:1 slivers on a bottle neck.
"""
import numpy as np
from PIL import ImageDraw
import palette, texgen as T, geometry as P

# Fictional brands. Numeric suffixes and generic product nouns keep every label
# clear of real trademarks, which is a hard requirement for marketplace listing.
BRANDS = {
    "vodka": ("ЗАРЯ-59", "ВОДКА",
              ("ОСОБАЯ ОЧИСТКА",
               "0.5 Л   40% ОБ.")),
    "can":   ("ТУШЁНКА", "ГОВЯДИНА",
              ("ТУ 9216-14", "МАССА НЕТТО 525 Г")),
    "pack":  ("ДОЗОР", "СИГАРЕТЫ",
              ("20 ШТ", "1 КЛАСС")),
}
FRONT = 0.75   # u of the camera-facing side, so brands read in the default view


def can():
    """Body label wraps 360 degrees over rows 0..CAN_BODY_ROWS; lid and base
    discs sit below at their true texel radius."""
    w, h = P.CAN_TEX
    body = P.CAN_BODY_ROWS
    y = lambda f: int(body * f)
    cx = int(w * FRONT)
    brand, sub, lines = BRANDS["can"]

    tin = T.from_ramp(0.35 + 0.5 * T.fbm(h, w, seed=10, octaves=(28, 14, 7, 3)), "tin")
    rgb = T.grime(tin, T.fbm(h, w, seed=11, octaves=(32, 16, 8, 4)), 0.30)
    paper = T.from_ramp(0.66 + 0.24 * T.fbm(h, w, seed=12, octaves=(9, 5, 3)), "paper")
    paper = T.grime(paper, T.fbm(h, w, seed=13, octaves=(14, 7, 3)), 0.24)
    mask = np.zeros((h, w), dtype=bool)
    mask[0:body] = True
    rgb = np.where(mask[..., None], paper, rgb)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, y(0.10)], fill=T.px("olive", 1))
    T.text(d, (cx, y(0.15)), brand,
           T.fit("heavy", brand, int(w * 0.27), y(0.19)), T.px("void", 0),
           centre=True, track=1)
    d.rectangle([0, y(0.43), w - 1, y(0.52)], fill=T.px("red", 1))
    T.text(d, (cx, y(0.455)), sub,
           T.fit("display", sub, int(w * 0.21), y(0.06)), T.px("paper", 4),
           centre=True, track=1)
    ly = y(0.60)
    for line in lines:
        f = T.fit("display", line, int(w * 0.24), y(0.08))
        T.text(d, (cx, ly), line, f, T.px("void", 1), centre=True, track=1)
        ly += f.size + 3
    T.smallprint(d, (int(w * 0.10), y(0.80), int(w * 0.34), y(0.94)),
                 T.px("paper", 1), seed=22, gap=4)
    d.rectangle([0, body - 4, w - 1, body - 1], fill=T.px("olive", 0))

    r, cy = P.CAN_DISC_R, P.CAN_DISC_Y
    for dx, shade in ((r + 2, 3), (3 * r + 6, 1)):
        d.ellipse([dx - r, cy - r, dx + r, cy + r], fill=T.px("tin", shade))
        for rr in range(r - 4, 2, -5):
            d.ellipse([dx - rr, cy - rr, dx + rr, cy + rr],
                      outline=T.px("tin", max(0, shade - 1)))

    T.scratches(img, 70, T.px("paper", 4), seed=23, length=7, ybox=(0, body))
    T.scratches(img, 90, T.px("tin", 4), seed=25, length=9, ybox=(body, h))
    T.scratches(img, 40, T.px("rust", 1), seed=24, length=6, ybox=(body, h))
    return np.asarray(img, dtype=np.float32)


def bottle():
    """Bands come from geometry.band(); V is arc length, U is radius-scaled."""
    w, h = P.BOTTLE_TEX
    cap, neck, shoulder = P.band("cap"), P.band("neck"), P.band("shoulder")
    label, lower = P.band("label"), P.band("lower")
    cx = int(w * FRONT)
    brand, sub, lines = BRANDS["vodka"]

    # Clear glass is mostly bright; thickness darkens it rather than tinting it.
    base = 0.56 + 0.32 * T.fbm(h, w, seed=30, octaves=(7, 4, 2))
    # Mould lines run down the straight sections only. Across the shoulder the
    # U scale is changing ring to ring, so any vertical feature there gets
    # sheared into a diagonal swirl - that was the smearing on the shoulder.
    runs = T.streaks(h, w, 18, seed=37, width=(1, 4))
    for y0, y1 in P.taper_spans():
        runs[y0:y1] = 0.0
    base = np.clip(base - 0.22 * runs, 0, 1)
    # Wherever the radius changes, the quad is a trapezoid in UV and any
    # horizontal variation gets sheared into a swirl. Flatten those spans to
    # their row mean: a rotationally symmetric band has nothing to shear, and
    # it reads as smooth blown glass, which is what a shoulder actually is.
    # The spans come from the profile, not from a hand-named band - the first
    # attempt at this missed the 0.31 -> 0.62 jump because it sat inside "neck".
    for y0, y1 in P.taper_spans():
        base[y0:y1] = base[y0:y1].mean(axis=1, keepdims=True)
    rgb = T.grime(T.from_ramp(base, "glass"),
                  T.fbm(h, w, seed=31, octaves=(10, 5, 3)), 0.20)
    lab = T.from_ramp(0.66 + 0.24 * T.fbm(h, w, seed=32, octaves=(9, 5, 3)), "paper")
    lab = T.grime(lab, T.fbm(h, w, seed=33, octaves=(14, 7, 3)), 0.22)
    mask = np.zeros((h, w), dtype=bool)
    mask[label[0]:label[1]] = True
    rgb = np.where(mask[..., None], lab, rgb)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)

    d.rectangle([0, cap[0], w - 1, cap[1] - 1], fill=T.px("red", 2))
    for x in range(0, w, 5):
        d.line([(x, cap[0] + 1), (x, cap[1] - 5)], fill=T.px("red", 1))
    d.rectangle([0, cap[1] - 5, w - 1, cap[1] - 1], fill=T.px("red", 0))

    # A vertical column only survives on a cylindrical section. Painting one
    # across a taper is what smears it round the shoulder.
    for y0, y1 in P.straight_spans():
        if y1 - y0 < 12 or y0 >= label[0] and y1 <= label[1]:
            continue
        for x in range(28, 38):
            d.line([(x, y0), (x, y1 - 1)], fill=T.px("glass", 3))
        d.line([(33, y0), (33, y1 - 1)], fill=T.px("void", 1))

    lh = label[1] - label[0]
    L = lambda f: label[0] + int(lh * f)
    d.rectangle([0, label[0], w - 1, L(0.04)], fill=T.px("red", 1))
    d.rectangle([0, L(0.96), w - 1, label[1] - 1], fill=T.px("red", 1))
    # Type is capped at 28% of the texture width. A cylinder only presents
    # about 100 degrees of arc legibly; anything wider wraps out of sight and
    # reads as a truncated word no matter how crisp the glyphs are.
    T.text(d, (cx, L(0.09)), brand,
           T.fit("heavy", brand, int(w * 0.28), int(lh * 0.25)), T.px("red", 0),
           centre=True, track=2)
    d.rectangle([int(w * 0.66), L(0.40), int(w * 0.84), L(0.425)], fill=T.px("olive", 1))
    T.text(d, (cx, L(0.48)), sub,
           T.fit("display", sub, int(w * 0.20), int(lh * 0.15)), T.px("void", 1),
           centre=True, track=3)
    ly = L(0.70)
    for line in lines:
        f = T.fit("display", line, int(w * 0.24), int(lh * 0.10))
        T.text(d, (cx, ly), line, f, T.px("void", 1), centre=True, track=1)
        ly += f.size + 3

    for i, (y0, y1) in enumerate(P.straight_spans()):
        if y1 - y0 < 12 or (y0 >= label[0] and y1 <= label[1]):
            continue
        T.scratches(img, 22, T.px("glass", 3), seed=36 + i, length=5, ybox=(y0, y1))
    T.scratches(img, 30, T.px("paper", 4), seed=39, length=6, ybox=label)

    # --- pole discs -------------------------------------------------------
    ccx, ccy, cr = P.BOTTLE_CAP_DISC
    d.ellipse([ccx - cr, ccy - cr, ccx + cr, ccy + cr], fill=T.px("red", 2))
    for rr in range(cr - 2, 1, -3):
        d.ellipse([ccx - rr, ccy - rr, ccx + rr, ccy + rr], outline=T.px("red", 1))
    d.ellipse([ccx - cr // 3, ccy - cr // 3, ccx + cr // 3, ccy + cr // 3],
              fill=T.px("red", 3))

    bcx, bcy, br = P.BOTTLE_BASE_DISC
    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=T.px("glass", 1))
    for rr in range(br - 3, 2, -6):          # punt rings
        d.ellipse([bcx - rr, bcy - rr, bcx + rr, bcy + rr], outline=T.px("glass", 0))
    d.ellipse([bcx - br // 3, bcy - br // 3, bcx + br // 3, bcy + br // 3],
              fill=T.px("glass", 0))
    return np.asarray(img, dtype=np.float32)


def pack():
    """Six faces, each rect at its true aspect ratio; see geometry.PACK_ATLAS."""
    w, h = P.PACK_TEX
    A = P.PACK_ATLAS
    card = T.from_ramp(0.52 + 0.30 * T.fbm(h, w, seed=40, octaves=(9, 5, 3)), "paper")
    rgb = T.grime(card, T.fbm(h, w, seed=41), 0.40)
    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)

    fx0, fy0, fx1, fy1 = A["front"]
    fh = fy1 - fy0
    f = lambda t: fy0 + int(fh * t)
    brand, sub, lines = BRANDS["pack"]
    fw, cx = fx1 - fx0, fx0 + (fx1 - fx0) // 2
    d.rectangle([fx0, fy0, fx1 - 1, fy1 - 1], fill=T.px("olive", 1))
    T.text(d, (cx, f(0.10)), brand,
           T.fit("heavy", brand, int(fw * 0.82), int(fh * 0.16)),
           T.px("paper", 4), centre=True, track=1)
    T.text(d, (cx, f(0.29)), sub,
           T.fit("display", sub, int(fw * 0.76), int(fh * 0.09)),
           T.px("paper", 3), centre=True, track=1)
    d.rectangle([fx0, f(0.42), fx1 - 1, f(0.50)], fill=T.px("red", 2))
    ly = f(0.56)
    for line in lines:
        ft = T.fit("display", line, int(fw * 0.55), int(fh * 0.08))
        T.text(d, (cx, ly), line, ft, T.px("olive", 3), centre=True, track=1)
        ly += ft.size + 2
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
