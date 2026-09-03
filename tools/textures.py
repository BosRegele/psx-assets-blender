"""The three prop textures. Each function documents its UV atlas layout -
build.py unwraps against these rectangles, so the two must move together.
"""
import numpy as np
from PIL import Image, ImageDraw
import palette, texgen as T


def can(size=64):
    """Canned food, 64x64.

    Atlas:  y   0..40  body label, U wraps 360 deg around the cylinder
            y  40..64  x  0..24  lid  (concentric ring stamping)
                       x 24..48  base (same stamping, darker)
                       x 48..64  bare tin, spare
    """
    s = size
    # base: bare galvanised tin everywhere
    tin = T.from_ramp(0.35 + 0.5 * T.fbm(s, s, seed=10, octaves=(32, 16, 8)), "tin")
    rgb = T.grime(tin, T.fbm(s, s, seed=11), 0.30)

    # --- body label band ---------------------------------------------------
    band = np.zeros((s, s), dtype=bool)
    band[0:40] = True
    paper = T.from_ramp(0.55 + 0.4 * T.fbm(s, s, seed=12, octaves=(32, 16, 8)), "paper")
    paper = T.grime(paper, T.fbm(s, s, seed=13), 0.5)
    rgb = np.where(band[..., None], paper, rgb)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)

    # olive header + red stripe: the state-issue label sandwich
    d.rectangle([0, 0, s - 1, 5], fill=T.px("olive", 1))
    d.rectangle([0, 20, s - 1, 23], fill=T.px("red", 1))
    d.rectangle([0, 38, s - 1, 39], fill=T.px("olive", 0))

    T.wordmark(d, (4, 8, s - 4, 18), seed=21, rows=1, colour=T.px("void", 0))
    T.smallprint(d, (6, 26, s - 8, 36), T.px("paper", 0), seed=22, gap=3)

    # --- lid / base stamping ----------------------------------------------
    for cx, cy, r_out, shade in ((12, 52, 11, 3), (36, 52, 11, 1)):
        d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                  fill=T.px("tin", shade))
        for r in range(r_out - 2, 1, -3):
            d.ellipse([cx - r, cy - r, cx + r, cy + r],
                      outline=T.px("tin", max(0, shade - 1)))

    T.scratches(img, 40, T.px("tin", 4), seed=23, length=5)
    T.scratches(img, 14, T.px("rust", 1), seed=24, length=3)
    return np.asarray(img, dtype=np.float32)


def bottle(size=128):
    """Vodka bottle, 128x128.

    Atlas runs top-to-bottom exactly as the bottle does, so the revolved
    profile can map V linearly against image rows:
            y   0..24   foil cap
            y  24..44   neck glass
            y  44..92   paper label
            y  92..128  lower body glass
    U wraps 360 degrees throughout.
    """
    s = size
    glass = T.from_ramp(0.25 + 0.45 * T.fbm(s, s, seed=30), "glass")
    rgb = T.grime(glass, T.fbm(s, s, seed=31), 0.25)

    label = T.from_ramp(0.5 + 0.45 * T.fbm(s, s, seed=32), "paper")
    label = T.grime(label, T.fbm(s, s, seed=33), 0.45)
    mask = np.zeros((s, s), dtype=bool)
    mask[44:92] = True
    rgb = np.where(mask[..., None], label, rgb)

    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)

    # foil cap with knurling
    d.rectangle([0, 0, s - 1, 23], fill=T.px("red", 2))
    for x in range(0, s, 4):
        d.line([(x, 2), (x, 21)], fill=T.px("red", 1))
    d.rectangle([0, 20, s - 1, 23], fill=T.px("red", 0))

    # vertical specular column on the glass - the one cue that reads
    # "glass" with no specular shading at all
    for band in ((24, 43), (92, s - 1)):
        for x in range(14, 21):
            d.line([(x, band[0]), (x, band[1])], fill=T.px("glass", 3))
        d.line([(17, band[0]), (17, band[1])], fill=T.px("concrete", 1))

    # label furniture
    d.rectangle([0, 44, s - 1, 47], fill=T.px("red", 1))
    d.rectangle([0, 88, s - 1, 91], fill=T.px("red", 1))
    d.rectangle([0, 54, s - 1, 56], fill=T.px("olive", 1))
    T.wordmark(d, (8, 60, s - 8, 74), seed=34, rows=1, colour=T.px("red", 0))
    T.smallprint(d, (12, 78, s - 12, 86), T.px("paper", 0), seed=35, gap=3)

    T.scratches(img, 50, T.px("glass", 3), seed=36, length=6)
    return np.asarray(img, dtype=np.float32)


def pack(size=64):
    """Cigarette pack, 64x64.

    Atlas:  x  0..32 y  0..40  front       x 32..64 y  0..40  back
            x  0..32 y 40..52  left side   x 32..64 y 40..52  right side
            x  0..32 y 52..64  top         x 32..64 y 52..64  bottom
    """
    s = size
    card = T.from_ramp(0.45 + 0.45 * T.fbm(s, s, seed=40), "paper")
    rgb = T.grime(card, T.fbm(s, s, seed=41), 0.40)
    img = T.to_pil(rgb)
    d = ImageDraw.Draw(img)

    # front face: olive field, red band, wordmark
    d.rectangle([0, 0, 31, 39], fill=T.px("olive", 1))
    d.rectangle([0, 14, 31, 18], fill=T.px("red", 2))
    T.wordmark(d, (3, 4, 29, 12), seed=42, rows=1, colour=T.px("paper", 4))
    T.smallprint(d, (4, 22, 28, 30), T.px("olive", 3), seed=43, gap=3)
    d.rectangle([0, 33, 31, 39], fill=T.px("void", 1))
    T.smallprint(d, (3, 34, 28, 38), T.px("paper", 2), seed=44, gap=2)

    # back face: same family, plainer
    d.rectangle([32, 0, 63, 39], fill=T.px("olive", 0))
    T.smallprint(d, (35, 6, 60, 30), T.px("olive", 3), seed=45, gap=3)
    d.rectangle([32, 33, 63, 39], fill=T.px("void", 1))

    # sides
    d.rectangle([0, 40, 31, 51], fill=T.px("olive", 1))
    d.rectangle([32, 40, 63, 51], fill=T.px("olive", 1))
    T.smallprint(d, (2, 44, 29, 48), T.px("olive", 3), seed=46, gap=2)

    # top: exposed filters. bottom: plain card
    d.rectangle([0, 52, 31, 63], fill=T.px("paper", 3))
    for i in range(6):
        for j in range(2):
            x, y = 2 + i * 5, 54 + j * 5
            d.ellipse([x, y, x + 3, y + 3], fill=T.px("paper", 4),
                      outline=T.px("rust", 1))
    d.rectangle([32, 52, 63, 63], fill=T.px("paper", 1))

    T.scratches(img, 25, T.px("paper", 4), seed=47, length=4)
    return np.asarray(img, dtype=np.float32)


BUILDERS = {"can": can, "bottle": bottle, "pack": pack}

if __name__ == "__main__":
    import os
    os.makedirs("../assets/textures", exist_ok=True)
    for name, fn in BUILDERS.items():
        p = f"../assets/textures/{name}_d.png"
        palette.save(fn(), p, strength=20.0)
        print("wrote", p)
