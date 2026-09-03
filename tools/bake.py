"""Bake every registered prop's texture atlas.

One pass per prop: pack, paint each face into its rect, quantise once at the
end. Painting per-face and quantising globally is deliberate - a single
quantise keeps the whole atlas on one CLUT, which is what makes separately
painted faces read as one object.
"""
import os
import numpy as np
from PIL import Image
import palette, kit, props, surfaces

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "textures")


def bake(name, fn, verbose=True):
    tier, parts = fn()
    r = kit.build(parts, tier)
    img = Image.new("RGB", r["size"], tuple(int(v) for v in palette.CLUT[1]))
    seed = abs(hash(name)) % 10_000
    for i, (rect, surf) in enumerate(zip(r["rects"], r["surfaces"])):
        surfaces.paint(img, surf, rect, seed + i * 13, r["density"])
    path = os.path.join(OUT, f"{name}_d.png")
    palette.save(np.asarray(img, dtype=np.float32), path, strength=18.0)
    tris = sum(len(f) - 2 for f in r["faces"])
    if verbose:
        print(f"{name:<24} {r['size'][0]}x{r['size'][1]:<5} {tris:>4} tris  "
              f"{len(r['verts']):>4} verts")
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for name, fn in props.REGISTRY.items():
        total += sum(len(f) - 2 for f in bake(name, fn)["faces"])
    print(f"\n{len(props.REGISTRY)} props, {total} triangles total")


if __name__ == "__main__":
    main()
