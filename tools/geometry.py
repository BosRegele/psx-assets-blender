"""Shared geometry contract. Pure stdlib so Blender's interpreter can import it.

This module exists because texel density is the whole ballgame. If the texture
atlas is laid out by hand and the mesh is unwrapped separately, the two drift
and you get the classic stretched-neck artifact. Here the geometry computes the
atlas rows, and both textures.py and blender_build.py read them from one place.

Density is fixed by the widest ring: the body wraps the full texture width
exactly once. Every other ring then uses a U span proportional to its radius,
and V advances with arc length along the profile. The result is square texels
everywhere instead of 13:1 slivers on the neck.
"""
import math

TAU = math.pi * 2


def density(tex_w, radius):
    """Pixels per metre implied by wrapping `radius` once across `tex_w`."""
    return tex_w / (TAU * radius)


def arc_rows(profile, dens):
    """Cumulative arc length along a (radius, z) profile, in texture rows."""
    rows, s = [0.0], 0.0
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        s += math.hypot(r1 - r0, z1 - z0)
        rows.append(s * dens)
    return rows


# Every prop wraps its widest ring across exactly one full texture width, so
# each prop has square texels internally. The resulting densities are then kept
# within ~15% of each other across the bundle, which is what stops one prop
# looking chunkier than the next on a shelf.

# --- vodka bottle ----------------------------------------------------------
BOTTLE_TEX = (256, 512)          # portrait: the bottle is taller than round
BOTTLE_R = 0.042
BOTTLE_PROFILE = [               # (radius, z), cap first, base last
    (0.000, 0.300), (0.016, 0.300), (0.016, 0.282), (0.013, 0.278),
    (0.013, 0.212), (0.026, 0.196), (0.034, 0.188), (0.042, 0.180),
    (0.042, 0.150), (0.042, 0.055), (0.042, 0.008), (0.038, 0.000),
    (0.000, 0.000),
]
BOTTLE_DENSITY = density(BOTTLE_TEX[0], BOTTLE_R)
BOTTLE_ROWS = arc_rows(BOTTLE_PROFILE, BOTTLE_DENSITY)
# profile-index boundaries the texture paints against
BOTTLE_BANDS = {"cap": (0, 3), "neck": (3, 5), "shoulder": (5, 8),
                "label": (8, 9), "lower": (9, 12)}

# The profile only reaches row ~356 of 512, so the poles get real discs in the
# space below it. Mapping a fan to a single row leaves the cap top a flat
# untextured disc, which is what made it read as plastic.
_cap_r = int(round(BOTTLE_PROFILE[1][0] * BOTTLE_DENSITY))
_base_r = int(round(BOTTLE_PROFILE[-2][0] * BOTTLE_DENSITY))
BOTTLE_CAP_DISC = (_cap_r + 6, int(round(BOTTLE_ROWS[-1])) + _cap_r + 12, _cap_r)
BOTTLE_BASE_DISC = (2 * _cap_r + _base_r + 18,
                    int(round(BOTTLE_ROWS[-1])) + _base_r + 14, _base_r)


def taper_spans(profile=None, rows=None, tol=1e-6):
    """Row ranges where the radius changes, i.e. where U scale differs between
    the two rings of a quad. Those quads are trapezoids in UV space, so any
    texture detail there gets sheared into a swirl. Painted content must be
    constant around the circumference across these spans.
    """
    profile = profile or BOTTLE_PROFILE
    rows = rows or BOTTLE_ROWS
    out = []
    for i in range(len(profile) - 1):
        r0, r1 = profile[i][0], profile[i + 1][0]
        if r0 > tol and r1 > tol and abs(r1 - r0) > tol:
            out.append((int(rows[i]), int(round(rows[i + 1]))))
    return out


def straight_spans(profile=None, rows=None, tol=1e-6):
    """Row ranges of constant radius - the cylindrical sections, where
    directional detail such as a specular column is safe to paint."""
    profile = profile or BOTTLE_PROFILE
    rows = rows or BOTTLE_ROWS
    return [(int(rows[i]), int(round(rows[i + 1])))
            for i in range(len(profile) - 1)
            if profile[i][0] > tol and abs(profile[i + 1][0] - profile[i][0]) <= tol]


def band(name, rows=None):
    """Atlas row span (top, bottom) for a named bottle band."""
    rows = rows or BOTTLE_ROWS
    a, b = BOTTLE_BANDS[name]
    return int(round(rows[a])), int(round(rows[b]))


# --- canned food -----------------------------------------------------------
CAN_TEX = (256, 256)
CAN_R, CAN_H = 0.037, 0.102
CAN_DENSITY = density(CAN_TEX[0], CAN_R)
CAN_BODY_ROWS = int(round(CAN_H * CAN_DENSITY))     # label band height
CAN_DISC_R = int(round(CAN_R * CAN_DENSITY))        # lid radius in texels
CAN_DISC_Y = CAN_BODY_ROWS + CAN_DISC_R + 2

# --- cigarette pack --------------------------------------------------------
# Matched to the can's density so the two read as the same material scale.
PACK_TEX = (256, 256)
PACK_W, PACK_D, PACK_H = 0.055, 0.023, 0.088
PACK_DENSITY = CAN_DENSITY
_pw = int(round(PACK_W * PACK_DENSITY))
_pd = int(round(PACK_D * PACK_DENSITY))
_ph = int(round(PACK_H * PACK_DENSITY))
# Six faces, each at its true aspect ratio. The earlier layout gave the side
# faces a square rect for a 23x88mm surface - a 3.8:1 texel stretch that the
# density audit caught.
PACK_ATLAS = {
    "front":  (0, 0, _pw, _ph),
    "back":   (_pw, 0, 2 * _pw, _ph),
    "left":   (2 * _pw, 0, 2 * _pw + _pd, _ph),
    "right":  (2 * _pw + _pd, 0, 2 * _pw + 2 * _pd, _ph),
    "top":    (0, _ph, _pw, _ph + _pd),
    "bottom": (_pw, _ph, 2 * _pw, _ph + _pd),
}

if __name__ == "__main__":
    print(f"bottle density {BOTTLE_DENSITY:.0f} px/m, tex {BOTTLE_TEX}")
    for i, (r, z) in enumerate(BOTTLE_PROFILE):
        print(f"  [{i:2}] r={r:.3f} z={z:.3f} -> row {BOTTLE_ROWS[i]:6.1f}"
              f"  u_scale {r / BOTTLE_R:.2f}")
    print("  bands:", {k: band(k) for k in BOTTLE_BANDS})
    print(f"can density {CAN_DENSITY:.0f} px/m, body rows {CAN_BODY_ROWS}, disc r {CAN_DISC_R}")
    print(f"pack density {PACK_DENSITY:.0f} px/m, atlas {PACK_ATLAS}")
    ds = [BOTTLE_DENSITY, CAN_DENSITY, PACK_DENSITY]
    print(f"bundle density spread: {max(ds) / min(ds):.3f}")
