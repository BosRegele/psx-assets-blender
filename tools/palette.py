"""Master CLUT and PS1-accurate quantisation for the psx-assets-blender style.

Two rules define the look:
  1. Every colour is 15-bit safe (each channel a multiple of 8) - the PS1
     framebuffer stored 5 bits per channel, so anything else is a lie.
  2. Gradients are never smooth. They are Bayer-dithered into the CLUT, which
     is what makes a 64x64 texture read as "PS1" instead of "small".
"""
import numpy as np
from PIL import Image

# --- master palette: 32 colours, post-soviet grime -------------------------
# Grouped by material so texgen can pull a coherent ramp per surface.
PALETTE = {
    "void":     [(0x00, 0x00, 0x00), (0x18, 0x18, 0x20)],
    # galvanised tin: cold, slightly blue
    "tin":      [(0x30, 0x38, 0x40), (0x50, 0x58, 0x60), (0x78, 0x80, 0x88),
                 (0xA0, 0xA8, 0xB0), (0xC8, 0xD0, 0xD8)],
    # oxidation crawling over everything
    "rust":     [(0x38, 0x20, 0x18), (0x60, 0x30, 0x18), (0x88, 0x48, 0x20),
                 (0xB0, 0x68, 0x30)],
    # army surplus olive - the signature colour of the era
    "olive":    [(0x20, 0x28, 0x18), (0x38, 0x40, 0x20), (0x50, 0x58, 0x30),
                 (0x70, 0x78, 0x48)],
    # stained paper labels
    "paper":    [(0x58, 0x50, 0x40), (0x80, 0x78, 0x60), (0xA8, 0xA0, 0x88),
                 (0xC8, 0xC0, 0xA8), (0xE0, 0xD8, 0xC0)],
    # faded state-issue red
    "red":      [(0x48, 0x10, 0x10), (0x78, 0x20, 0x18), (0xA8, 0x30, 0x20),
                 (0xC8, 0x50, 0x38)],
    # clear bottle glass. Vodka ships in flint glass, not the green used for
    # beer and wine. Thickness reads as a faint cool tint, so the ramp runs
    # from a shadowed teal-grey up to an almost-white highlight.
    "glass":    [(0x50, 0x60, 0x60), (0x88, 0x98, 0x98), (0xB8, 0xC8, 0xC8),
                 (0xE0, 0xE8, 0xE8)],
    # concrete / neutral filler
    "concrete": [(0x40, 0x40, 0x40), (0x68, 0x68, 0x68), (0x90, 0x90, 0x90),
                 (0xB8, 0xB8, 0xB8)],
    # --- added for the bunker set -----------------------------------------
    # Furniture needs ramps the three consumables never did. 32 entries could
    # not carry timber, upholstery, rubber and brass without one of them
    # borrowing another's ramp and reading as the wrong material.
    "wood":     [(0x30, 0x20, 0x10), (0x58, 0x38, 0x20), (0x80, 0x58, 0x30),
                 (0xA8, 0x80, 0x50)],
    "fabric":   [(0x30, 0x28, 0x28), (0x50, 0x40, 0x38), (0x70, 0x58, 0x50),
                 (0x90, 0x78, 0x68)],
    "rubber":   [(0x10, 0x10, 0x10), (0x20, 0x20, 0x20), (0x38, 0x38, 0x38),
                 (0x50, 0x50, 0x58)],
    "brass":    [(0x48, 0x38, 0x10), (0x78, 0x60, 0x20), (0xA8, 0x88, 0x38),
                 (0xD0, 0xB0, 0x58)],
    # --- colour, so the set is not eight shades of grime --------------------
    # Institutional paint and hazard marking did exist, and a room where every
    # object is olive or rust reads as a texture pass rather than as a place.
    "blue":     [(0x18, 0x28, 0x40), (0x28, 0x48, 0x68), (0x40, 0x70, 0x98),
                 (0x70, 0xA0, 0xC0)],
    "yellow":   [(0x50, 0x40, 0x10), (0x88, 0x70, 0x18), (0xC0, 0xA0, 0x28),
                 (0xE8, 0xD0, 0x60)],
    "skin":     [(0x40, 0x30, 0x28), (0x70, 0x58, 0x48), (0xA0, 0x80, 0x68),
                 (0xC8, 0xA8, 0x90)],
}

CLUT = np.array([c for group in PALETTE.values() for c in group], dtype=np.float32)
assert len(CLUT) == 60, f"CLUT must be 60 entries, got {len(CLUT)}"
assert (CLUT.astype(int) % 8 == 0).all(), "every channel must be 15-bit safe"

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6],
                   [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32)


def ramp(name):
    """Return a material's colour ramp as a float array, dark -> light."""
    return np.array(PALETTE[name], dtype=np.float32)


def bayer(shape, strength=24.0):
    """Tiled ordered-dither offset field, centred on zero."""
    h, w = shape
    tile = (BAYER4 / 16.0) - 0.46875  # centre the 0..15 range
    return np.tile(tile, (h // 4 + 1, w // 4 + 1))[:h, :w, None] * strength


def quantise(rgb, strength=24.0):
    """Dither a float RGB array (H,W,3) in 0..255 and snap it to the CLUT."""
    dithered = np.clip(rgb + bayer(rgb.shape[:2], strength), 0, 255)
    flat = dithered.reshape(-1, 1, 3)
    idx = np.argmin(((flat - CLUT[None, :, :]) ** 2).sum(-1), axis=1)
    return CLUT[idx].reshape(rgb.shape).astype(np.uint8)


def save(rgb, path, strength=24.0):
    """Quantise and write a texture. Returns the path."""
    Image.fromarray(quantise(np.asarray(rgb, dtype=np.float32), strength)).save(path)
    return path


def swatch(path, cell=32):
    """Render the CLUT as a documentation image, 8 columns."""
    rows = (len(CLUT) + 7) // 8
    img = np.zeros((rows * cell, 8 * cell, 3), dtype=np.uint8)
    for i, c in enumerate(CLUT.astype(np.uint8)):
        r, col = divmod(i, 8)
        img[r * cell:(r + 1) * cell, col * cell:(col + 1) * cell] = c
    Image.fromarray(img).save(path)
    return path
