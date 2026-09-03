"""Procedural pixel textures for the psx-assets-blender kit.

Every texture is authored at full colour depth, then pushed through
palette.quantise() as the very last step. Nothing here paints CLUT indices
by hand - the dither pass is what unifies the whole bundle.

UV atlas layouts are documented per-function and are the contract the
Blender build scripts unwrap against. Changing a layout here means changing
the matching unwrap in build.py.
"""
import numpy as np
from PIL import Image, ImageDraw
import palette

RNG = np.random.default_rng(0xC0FFEE)


# --- surface helpers -------------------------------------------------------

def value_noise(h, w, cells, seed=None):
    """Blocky value noise, upscaled with nearest so it stays pixel-honest."""
    rng = RNG if seed is None else np.random.default_rng(seed)
    small = rng.random((max(1, h // cells), max(1, w // cells)))
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.NEAREST)
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(h, w, seed=None, octaves=(16, 8, 4, 2)):
    """Sum of noise octaves, normalised to 0..1. Used for grime and wear."""
    out = np.zeros((h, w), dtype=np.float32)
    amp = 1.0
    for i, cells in enumerate(octaves):
        out += value_noise(h, w, cells, None if seed is None else seed + i) * amp
        amp *= 0.5
    out -= out.min()
    return out / max(out.max(), 1e-6)


def from_ramp(mask, name):
    """Map a 0..1 mask onto a named palette ramp, dark -> light."""
    r = palette.ramp(name)
    idx = np.clip((mask * (len(r) - 1)), 0, len(r) - 1)
    lo, hi = np.floor(idx).astype(int), np.ceil(idx).astype(int)
    t = (idx - lo)[..., None]
    return r[lo] * (1 - t) + r[hi] * t


def grime(rgb, mask, amount=0.45):
    """Darken with a noise mask. Grime is what sells the era."""
    return rgb * (1.0 - amount * mask[..., None])


def scratches(img, count, colour, seed=1, length=8):
    """Short bright scuffs. Drawn on the PIL image so they stay 1px crisp."""
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(count):
        x, y = rng.integers(0, w), rng.integers(0, h)
        dx, dy = rng.integers(-length, length), rng.integers(-2, 3)
        d.line([(int(x), int(y)), (int(x + dx), int(y + dy))], fill=colour)
    return img


def wordmark(d, box, seed=2, rows=1, density=0.72, colour=(0, 0, 0)):
    """Blocky pseudo-letterforms grouped into words.

    At 64px a real typeface turns to mush, so the era's artists suggested
    text with rectangles instead. The trick is that uniform bars read as a
    barcode - what sells it as language is varied glyph width, a few short
    x-height glyphs among the tall ones, and real word gaps. Also sidesteps
    every trademark problem.
    """
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    rh = max(3, (y1 - y0) // rows)
    for r in range(rows):
        top = y0 + r * rh
        x = x0
        # 1-3 words per row, each 2-5 glyphs
        while x < x1 - 2:
            glyphs = int(rng.integers(2, 6))
            for _ in range(glyphs):
                w = int(rng.integers(2, 5))
                if x + w > x1:
                    break
                # a third of glyphs sit at x-height instead of cap-height
                short = rng.random() < 0.34
                gt = top + (rh // 3 if short else 0)
                d.rectangle([x, gt, x + w - 1, top + rh - 2], fill=colour)
                x += w + 1
            x += 3  # word gap
    return d


def smallprint(d, box, colour, seed=3, gap=2):
    """Horizontal dashes standing in for ingredient text."""
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    for y in range(y0, y1, gap):
        w = int(rng.integers((x1 - x0) // 3, x1 - x0))
        d.line([(x0, y), (x0 + w, y)], fill=colour)
    return d


def to_pil(rgb):
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def px(name, i):
    return tuple(int(v) for v in palette.ramp(name)[i])
