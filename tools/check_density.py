"""Texel density audit. Fails loudly if any surface drifts from square texels.

Run this before shipping a prop. Non-square texels are the single most obvious
tell of an amateur asset - they are what makes a bottle neck look smeared.
"""
import math, sys
import geometry as P
import kit, props

TOLERANCE = 1.15


def bottle_report():
    prof, rows = P.BOTTLE_PROFILE, P.BOTTLE_ROWS
    W = P.BOTTLE_TEX[0]
    worst, lines = 1.0, []
    for k in range(len(prof) - 1):
        r0, z0 = prof[k]
        r1, z1 = prof[k + 1]
        if r0 == 0 or r1 == 0:
            continue
        rm = (r0 + r1) / 2
        du = (W * (rm / P.BOTTLE_R)) / (P.TAU * rm)
        arc = math.hypot(r1 - r0, z1 - z0)
        dv = (rows[k + 1] - rows[k]) / arc
        ratio = du / dv
        worst = max(worst, ratio, 1 / ratio)
        lines.append(f"  r={rm * 1000:>5.1f}mm  {du:>6.0f} x {dv:>6.0f} px/m  ratio {ratio:.3f}")
    return worst, lines


def box_report(name, w, h, atlas_key):
    """w and h are the real-world dimensions of that face, in metres."""
    x0, y0, x1, y1 = P.PACK_ATLAS[atlas_key]
    du, dv = (x1 - x0) / w, (y1 - y0) / h
    ratio = max(du / dv, dv / du)
    return ratio, [f"  {name}: {du:>6.0f} x {dv:>6.0f} px/m  ratio {ratio:.3f}"]


def kit_report():
    """Every box-composite prop. This is the gate for the bunker set."""
    worst, lines, tiny_total, offenders = 1.0, [], 0, 0
    for name, fn in props.REGISTRY.items():
        tier, parts = fn()
        w, rows, tiny = kit.density_report(parts, tier)
        tiny_total += tiny
        worst = max(worst, w)
        if w > TOLERANCE:
            offenders += 1
            lines.append(f"  {name} (worst {w:.3f})")
            lines += ["  " + r for r in rows[:3]]
    lines.insert(0, f"  {len(props.REGISTRY)} props, {offenders} over tolerance, "
                    f"{tiny_total} faces below texel resolution "
                    f"(< {kit.MIN_MEANINGFUL_PX}px, aspect not meaningful)")
    return worst, lines


def main():
    worst = 1.0
    for title, (w, ls) in (("bottle", bottle_report()),
                           ("pack front", box_report("front", P.PACK_W, P.PACK_H, "front")),
                           ("pack side", box_report("side", P.PACK_D, P.PACK_H, "left")),
                           ("pack top", box_report("top", P.PACK_W, P.PACK_D, "top")),
                           ("bunker set", kit_report())):
        print(title); print("\n".join(ls)); worst = max(worst, w)
    can_u = P.CAN_TEX[0] / (P.TAU * P.CAN_R)
    can_v = P.CAN_BODY_ROWS / P.CAN_H
    print(f"can\n  body: {can_u:>6.0f} x {can_v:>6.0f} px/m  ratio {can_u / can_v:.3f}")
    worst = max(worst, can_u / can_v, can_v / can_u)
    print(f"\nworst deviation from square texels: {worst:.3f} (tolerance {TOLERANCE})")
    return 0 if worst <= TOLERANCE else 1


if __name__ == "__main__":
    sys.exit(main())
