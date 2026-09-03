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
    """Blocky value noise, upscaled with nearest so it stays pixel-honest.

    `cells` is the block size IN PIXELS, not a count of subdivisions. Passing a
    large value at full amplitude produces huge flat patches rather than grain -
    the coarsest octave should stay well under a tenth of the texture width.
    """
    rng = RNG if seed is None else np.random.default_rng(seed)
    small = rng.random((max(1, h // cells), max(1, w // cells)))
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.NEAREST)
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(h, w, seed=None, octaves=(16, 8, 4, 2)):
    """Sum of noise octaves, normalised to 0..1. Used for grime and wear.

    Octaves are block sizes in pixels, coarsest first, each at half the previous
    amplitude. Scale them with the texture, but keep the coarsest modest: it
    carries the most weight and reads as blotching if it gets too large.
    """
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


def scratches(img, count, colour, seed=1, length=8, ybox=None):
    """Short scuffs, drawn on the PIL image so they stay 1px crisp.

    `ybox` restricts them to one atlas band. Without it, glass-coloured scuffs
    land on the paper label as green flecks - a material bleeding across an
    atlas boundary, which is the sort of thing that reads as sloppy up close.
    """
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img)
    w, h = img.size
    y0, y1 = ybox if ybox else (0, h)
    for _ in range(count):
        x, y = rng.integers(0, w), rng.integers(y0, max(y0 + 1, y1))
        dx, dy = rng.integers(-length, length), rng.integers(-2, 3)
        d.line([(int(x), int(y)), (int(x + dx), int(y + dy))], fill=colour)
    return img


def wordmark(d, box, seed=2, rows=1, colour=(0, 0, 0)):
    """Blocky pseudo-letterforms grouped into words.

    At this resolution a real typeface turns to mush, so the era's artists
    suggested text with rectangles instead. Three things stop it reading as a
    barcode: varied glyph width, a third of glyphs sitting at x-height rather
    than cap-height, and genuine word gaps.

    Glyph metrics derive from the row height, so the same call produces
    correctly-proportioned lettering on a 64px and a 256px atlas alike. Fixing
    them in absolute pixels is what turns letters into thin bars when the
    texture size changes.
    """
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    rh = max(3, (y1 - y0) // rows)
    lo, hi = max(2, round(rh * 0.34)), max(3, round(rh * 0.72))
    kern, space = max(1, rh // 7), max(2, rh // 3)
    for r in range(rows):
        top = y0 + r * rh
        x = x0
        while x < x1 - lo:
            for _ in range(int(rng.integers(2, 6))):      # 2-5 glyphs per word
                w = int(rng.integers(lo, hi + 1))
                if x + w > x1:
                    break
                short = rng.random() < 0.34
                gt = top + (rh // 3 if short else 0)
                d.rectangle([x, gt, x + w - 1, top + rh - 2], fill=colour)
                x += w + kern
            x += space
    return d


def smallprint(d, box, colour, seed=3, gap=2):
    """Horizontal dashes standing in for ingredient text.

    Ragged right edges are what make it read as prose rather than as rules.
    """
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    gap = max(2, gap)
    for y in range(y0, y1, gap):
        w = int(rng.integers((x1 - x0) // 3, x1 - x0))
        d.line([(x0, y), (x0 + w, y)], fill=colour)
    return d


def to_pil(rgb):
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def px(name, i):
    return tuple(int(v) for v in palette.ramp(name)[i])


def streaks(h, w, count=14, seed=5, width=(1, 4)):
    """Vertical bands, 0..1. Glass carries mould lines and dried runs; without
    them a flat tint dithers into a visible regular cross-hatch instead of
    reading as a surface."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), dtype=np.float32)
    for _ in range(count):
        x = int(rng.integers(0, w))
        bw = int(rng.integers(*width))
        out[:, x:x + bw] += float(rng.random()) * 0.6 + 0.2
    return np.clip(out, 0, 1)


# --- real lettering --------------------------------------------------------
FONTS = {"display": "C:/Windows/Fonts/framd.ttf",   # Franklin Gothic Medium
         "heavy":   "C:/Windows/Fonts/ariblk.ttf",
         "cond":    "C:/Windows/Fonts/impact.ttf"}
_font_cache = {}


def font(role, size):
    key = (role, size)
    if key not in _font_cache:
        from PIL import ImageFont
        _font_cache[key] = ImageFont.truetype(FONTS[role], size)
    return _font_cache[key]


def fit(role, s, max_w, max_h, start=64):
    """Largest size at which `s` fits the box. Labels are laid out by the box,
    not by a magic number, so a density change rescales the type with it."""
    for size in range(start, 5, -1):
        f = font(role, size)
        x0, y0, x1, y1 = f.getbbox(s)
        if x1 - x0 <= max_w and y1 - y0 <= max_h:
            return f
    return font(role, 6)


def text(d, xy, s, f, colour, centre=False, track=0):
    """Aliased text. `d.fontmode = "1"` is the whole trick: PIL antialiases TTF
    by default, and those grey edge pixels quantise into mud against a 32-colour
    CLUT. One-bit rendering keeps every glyph edge on a texel boundary.

    `track` adds letter spacing, which condensed industrial labels of the era
    used heavily and which also stops small caps from merging at low res.
    """
    prev, d.fontmode = d.fontmode, "1"
    x, y = xy
    if track:
        w = sum(f.getbbox(c)[2] - f.getbbox(c)[0] + track for c in s) - track
        if centre:
            x -= w // 2
        for c in s:
            d.text((x, y), c, font=f, fill=colour)
            x += f.getbbox(c)[2] - f.getbbox(c)[0] + track
    else:
        bb = f.getbbox(s)
        if centre:
            x -= (bb[2] - bb[0]) // 2
        d.text((x - bb[0], y - bb[1]), s, font=f, fill=colour)
    d.fontmode = prev
    return d
