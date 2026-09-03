"""The bunker set. Each prop is a declaration in metres, nothing more.

Dimensions are real: a locker is 1.85m because that is what a locker is, and
`kit` derives the atlas from them. Getting scale right is not pedantry - it is
what lets a buyer drop the whole set into a scene and have it sit together.

Box `pos` is the minimum corner, `size` is (w, d, h) along (x, y, z).
Cylinder `pos` is the base centre. Every prop's origin is at floor level,
centred in plan, so it drops onto a floor without fixup.
"""
import math

from kit import Box, Cylinder

# --- storage ---------------------------------------------------------------


def locker_steel():
    """Two-door steel locker, the backbone of any bunker dressing kit."""
    W, D, H = 0.80, 0.50, 1.85
    p = [Box("body", (-W / 2, -D / 2, 0.08), (W, D, H - 0.08),
             {"front": "steel_worn", "back": "steel", "left": "steel_panel",
              "right": "steel_panel", "top": "steel", "bottom": "unseen"}),
         Box("plinth", (-W / 2, -D / 2, 0), (W, D, 0.08), "steel_worn")]
    # Doors stand 45mm proud with a 20mm reveal between them. Flush panels on a
    # flat face are invisible without shadowing; the gap is what reads.
    for i, x in enumerate((-W / 2 + 0.02, 0.01)):
        p.append(Box(f"door{i}", (x, -D / 2 - 0.045, 0.14),
                     (W / 2 - 0.03, 0.045, H - 0.22),
                     {"front": "steel_door", "back": "dark",
                      "left": "steel", "right": "steel",
                      "top": "steel", "bottom": "steel"}))
    return "furniture", p


def cabinet_wall():
    """Wall-hung cabinet with a single door."""
    W, D, H = 0.90, 0.34, 0.70
    return "furniture", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H),
            {"front": "steel_worn", "back": "steel", "left": "steel_panel",
             "right": "steel_panel", "top": "steel", "bottom": "steel"}),
        Box("door", (-W / 2 + 0.02, -D / 2 - 0.035, 0.04), (W - 0.04, 0.035, H - 0.08),
            {"front": "steel_door", "back": "steel", "left": "steel",
             "right": "steel", "top": "steel", "bottom": "steel"}),
    ]


def filing_cabinet():
    """Three-drawer filing cabinet."""
    W, D, H = 0.46, 0.60, 1.10
    p = [Box("body", (-W / 2, -D / 2, 0), (W, D, H), "steel_worn")]
    for i in range(3):
        p.append(Box(f"drawer{i}", (-W / 2 + 0.02, -D / 2 - 0.03, 0.05 + i * 0.34),
                     (W - 0.04, 0.03, 0.30),
                     {"front": "steel_drawer", "back": "steel", "left": "steel",
                      "right": "steel", "top": "steel", "bottom": "steel"}))
    return "furniture", p


def shelf_unit():
    """Open steel shelving, four decks."""
    W, D, H = 1.00, 0.40, 1.90
    p = []
    for i, (x, y) in enumerate(((-W / 2, -D / 2), (W / 2 - 0.04, -D / 2),
                                (-W / 2, D / 2 - 0.04), (W / 2 - 0.04, D / 2 - 0.04))):
        p.append(Box(f"post{i}", (x, y, 0), (0.04, 0.04, H), "steel_panel"))
    for i in range(4):
        p.append(Box(f"deck{i}", (-W / 2, -D / 2, 0.12 + i * 0.56),
                     (W, D, 0.03), "steel_worn"))
    return "furniture", p


def crate_ammo():
    """Stencilled ammunition crate."""
    W, D, H = 0.62, 0.32, 0.26
    return "furniture", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H - 0.04),
            {"front": "olive_stencil", "back": "olive_stencil",
             "left": "olive_metal", "right": "olive_metal",
             "top": "olive_metal", "bottom": "olive_metal"}),
        Box("lid", (-W / 2 - 0.01, -D / 2 - 0.01, H - 0.04),
            (W + 0.02, D + 0.02, 0.04), "olive_metal"),
    ]


def crate_wood():
    """Timber supply crate."""
    S, H = 0.55, 0.45
    return "furniture", [
        Box("body", (-S / 2, -S / 2, 0), (S, S, H), "wood_planks"),
        Box("rail_b", (-S / 2 - 0.01, -S / 2 - 0.01, 0.04),
            (S + 0.02, S + 0.02, 0.04), "wood"),
        Box("rail_t", (-S / 2 - 0.01, -S / 2 - 0.01, H - 0.08),
            (S + 0.02, S + 0.02, 0.04), "wood"),
    ]


def barrel_steel():
    """Rolled-hoop steel drum."""
    R, H = 0.28, 0.86
    p = [Cylinder("body", (0, 0, 0), R, H, "steel_worn", n=12)]
    for i, z in enumerate((0.24, 0.56)):
        p.append(Cylinder(f"hoop{i}", (0, 0, z), R + 0.012, 0.05, "steel", n=12))
    return "furniture", p


# --- surfaces to work on ---------------------------------------------------


def table_steel():
    """Field table: steel top, tube legs, lower shelf."""
    W, D, H = 1.20, 0.62, 0.75
    p = [Box("top", (-W / 2, -D / 2, H - 0.04), (W, D, 0.04), "steel_worn"),
         Box("shelf", (-W / 2 + 0.06, -D / 2 + 0.06, 0.18),
             (W - 0.12, D - 0.12, 0.02), "steel")]
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        p.append(Box(f"leg{i}",
                     (sx * (W / 2 - 0.07) - 0.025, sy * (D / 2 - 0.07) - 0.025, 0),
                     (0.05, 0.05, H - 0.04), "steel_panel"))
    return "furniture", p


def desk_wood():
    """Officer's desk with a drawer bank."""
    W, D, H = 1.30, 0.68, 0.76
    p = [Box("top", (-W / 2, -D / 2, H - 0.05), (W, D, 0.05), "wood"),
         Box("bank", (W / 2 - 0.46, -D / 2 + 0.04, 0.04), (0.44, D - 0.08, H - 0.09),
             {"front": "steel_drawer", "back": "wood", "left": "wood",
              "right": "wood", "top": "wood", "bottom": "wood"}),
         Box("panel", (-W / 2 + 0.04, D / 2 - 0.06, 0.20),
             (0.78, 0.04, H - 0.26), "wood_planks")]
    for i, sy in enumerate((-1, 1)):
        p.append(Box(f"leg{i}", (-W / 2 + 0.05, sy * (D / 2 - 0.09) - 0.03, 0),
                     (0.06, 0.06, H - 0.05), "wood"))
    return "furniture", p


def chair_wood():
    """Plain timber chair."""
    W, D, SH, H = 0.44, 0.44, 0.45, 0.90
    p = [Box("seat", (-W / 2, -D / 2, SH), (W, D, 0.04), "wood_planks"),
         Box("back", (-W / 2 + 0.02, D / 2 - 0.06, SH + 0.04),
             (W - 0.04, 0.04, H - SH - 0.04), "wood_planks")]
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        p.append(Box(f"leg{i}", (sx * (W / 2 - 0.06) - 0.02,
                                 sy * (D / 2 - 0.06) - 0.02, 0),
                     (0.04, 0.04, SH), "wood"))
    return "furniture", p


def stool_metal():
    """Welded steel stool."""
    R, H = 0.17, 0.46
    p = [Cylinder("seat", (0, 0, H - 0.03), R, 0.03, "steel_worn", n=10)]
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        p.append(Box(f"leg{i}", (sx * 0.11 - 0.015, sy * 0.11 - 0.015, 0),
                     (0.03, 0.03, H - 0.03), "steel_panel"))
    p.append(Box("ring", (-0.13, -0.13, 0.16), (0.26, 0.26, 0.02), "steel"))
    return "furniture", p


def couch_worn():
    """Sagging three-seat couch."""
    W, D, H = 1.90, 0.86, 0.78
    # The base top shows between the cushions and in front of the backrest,
    # and the rear shows whenever the couch is not flat against a wall.
    p = [Box("base", (-W / 2, -D / 2, 0.10), (W, D, 0.28),
             {"front": "fabric", "back": "fabric", "left": "fabric",
              "right": "fabric", "top": "fabric", "bottom": "unseen"}),
         Box("plinth", (-W / 2 + 0.05, -D / 2 + 0.05, 0),
             (W - 0.10, D - 0.10, 0.10), "wood"),
         Box("back", (-W / 2, D / 2 - 0.20, 0.38), (W, 0.20, H - 0.30),
             {"front": "fabric_seam", "back": "fabric", "left": "fabric",
              "right": "fabric", "top": "fabric", "bottom": "unseen"})]
    # Cushions stand 60mm proud of the base with a gap between them; flush
    # cushions read as one slab.
    seat_w = (W - 0.40) / 3
    for i in range(3):
        p.append(Box(f"cushion{i}", (-W / 2 + 0.20 + i * seat_w + 0.012,
                                     -D / 2 + 0.08, 0.38),
                     (seat_w - 0.024, D - 0.30, 0.13),
                     {"front": "fabric_seam", "back": "fabric",
                      "left": "fabric", "right": "fabric",
                      "top": "fabric_seam", "bottom": "unseen"}))
    for i, sx in enumerate((-1, 1)):
        p.append(Box(f"arm{i}", (sx * (W / 2 - 0.20) - 0.10, -D / 2, 0.38),
                     (0.20, D, 0.30), "fabric_seam"))
    return "furniture", p


def bunk_bed():
    """Two-tier steel bunk."""
    W, D, H = 0.90, 1.95, 1.70
    p = []
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        p.append(Box(f"post{i}", (sx * (W / 2 - 0.04) - 0.03,
                                  sy * (D / 2 - 0.04) - 0.03, 0),
                     (0.06, 0.06, H), "steel_panel"))
    for i, z in enumerate((0.42, 1.14)):
        p.append(Box(f"frame{i}", (-W / 2, -D / 2, z), (W, D, 0.06), {"front": "steel_worn", "back": "steel_worn", "left": "steel_worn", "right": "steel_worn", "top": "steel_worn", "bottom": "steel"}))
        p.append(Box(f"mattress{i}", (-W / 2 + 0.03, -D / 2 + 0.04, z + 0.06),
                     (W - 0.06, D - 0.08, 0.10),
                     {"front": "canvas", "back": "canvas", "left": "canvas",
                      "right": "canvas", "top": "canvas", "bottom": "unseen"}))
    return "furniture", p


# --- wall dressing ---------------------------------------------------------


def map_wall():
    """Situation map on a board. Thin box; hang it on a wall."""
    W, H, T = 1.30, 0.95, 0.03
    return "furniture", [
        Box("board", (-W / 2, 0, 0), (W, T, H),
            {"front": "map", "back": "wood", "left": "wood", "right": "wood",
             "top": "wood", "bottom": "wood"}),
        Box("rail_t", (-W / 2 - 0.02, -0.01, H - 0.04), (W + 0.04, T + 0.02, 0.04), "wood"),
        Box("rail_b", (-W / 2 - 0.02, -0.01, 0), (W + 0.04, T + 0.02, 0.04), "wood"),
    ]


def notice_board():
    """Cork board with pinned paper."""
    W, H, T = 0.70, 0.50, 0.03
    p = [Box("board", (-W / 2, 0, 0), (W, T, H),
             {"front": "wood", "back": "wood", "left": "wood", "right": "wood",
              "top": "wood", "bottom": "wood"})]
    for i, (x, z, w, h) in enumerate(((-0.28, 0.26, 0.22, 0.16),
                                      (0.02, 0.30, 0.18, 0.14),
                                      (-0.10, 0.06, 0.26, 0.15))):
        p.append(Box(f"sheet{i}", (x, -0.005, z), (w, 0.006, h), "paper"))
    return "furniture", p


# --- equipment -------------------------------------------------------------


def jerrycan():
    """Twenty-litre fuel can."""
    W, D, H = 0.34, 0.17, 0.46
    return "furniture", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H),
            {"front": "olive_stencil", "back": "olive_stencil",
             "left": "olive_metal", "right": "olive_metal",
             "top": "olive_metal", "bottom": "olive_metal"}),
        Box("handle", (-0.10, -0.03, H), (0.20, 0.06, 0.05), "olive_metal"),
        Cylinder("spout", (0.11, 0, H), 0.035, 0.05, "olive_metal", n=8),
    ]


def gasmask():
    """Filter respirator. Boxes and a canister - which is what a PS1 one was."""
    W, D, H = 0.19, 0.16, 0.25
    return "prop", [
        Box("face", (-W / 2, -D / 2, 0), (W, D, H), "rubber"),
        Box("lensL", (-W / 2 + 0.015, -D / 2 - 0.008, H - 0.10),
            (0.065, 0.012, 0.055), "glass_lens"),
        Box("lensR", (0.015, -D / 2 - 0.008, H - 0.10),
            (0.065, 0.012, 0.055), "glass_lens"),
        Cylinder("filter", (0, -D / 2 - 0.040, 0.03), 0.045, 0.09, "olive_metal", n=10),
        Box("strapL", (-W / 2 - 0.02, -0.02, H - 0.06), (0.02, 0.10, 0.03), "canvas"),
        Box("strapR", (W / 2, -0.02, H - 0.06), (0.02, 0.10, 0.03), "canvas"),
    ]


def helmet_steel():
    """Stamped steel helmet, faceted the way the hardware forced."""
    return "furniture", [
        Cylinder("crown", (0, 0, 0.035), 0.115, 0.125, "steel_worn", n=10),
        Cylinder("skirt", (0, 0, 0.0), 0.138, 0.045, "steel_worn", n=10),
        Cylinder("liner", (0, 0, 0.020), 0.100, 0.012, "canvas", n=10),
        Box("strap", (-0.10, -0.012, 0.0), (0.20, 0.024, 0.016), "canvas"),
    ]


def vest_armor():
    """Plate carrier: chest and back plates with shoulder straps."""
    W, D, H = 0.36, 0.22, 0.48
    p = [Box("front", (-W / 2, -D / 2, 0), (W, 0.05, H), "canvas"),
         Box("back", (-W / 2, D / 2 - 0.05, 0), (W, 0.05, H), "canvas"),
         Box("plate", (-W / 2 + 0.04, -D / 2 - 0.015, 0.10),
             (W - 0.08, 0.02, H - 0.20), "steel_panel")]
    for i, sx in enumerate((-1, 1)):
        p.append(Box(f"strap{i}", (sx * (W / 2 - 0.09) - 0.035, -D / 2, H - 0.03),
                     (0.07, D, 0.03), "canvas"))
        p.append(Box(f"pouch{i}", (sx * 0.10 - 0.055, -D / 2 - 0.03, 0.06),
                     (0.11, 0.05, 0.13), "canvas"))
    return "prop", p


def rifle():
    """Service rifle. Receiver, barrel, furniture, magazine."""
    return "prop", [
        Box("receiver", (-0.16, -0.030, 0.0), (0.34, 0.060, 0.090), "steel_worn"),
        Box("stock", (-0.44, -0.028, -0.020), (0.28, 0.056, 0.090), "wood"),
        Box("comb", (-0.30, -0.026, 0.070), (0.14, 0.052, 0.030), "wood"),
        Box("grip", (-0.11, -0.026, -0.110), (0.055, 0.052, 0.115), "wood"),
        Box("handguard", (0.18, -0.032, 0.004), (0.24, 0.064, 0.075), "wood_planks"),
        Box("barrel", (0.42, -0.016, 0.028), (0.22, 0.032, 0.032), "steel"),
        Box("mag", (-0.01, -0.024, -0.170), (0.080, 0.048, 0.175), "steel_worn"),
        Box("sight", (0.30, -0.014, 0.070), (0.036, 0.028, 0.036), "steel"),
    ]


def pistol():
    """Sidearm."""
    return "prop", [
        Box("slide", (-0.075, -0.019, 0.0), (0.155, 0.038, 0.040), "steel_worn"),
        Box("frame", (-0.070, -0.018, -0.026), (0.140, 0.036, 0.028), "steel"),
        Box("grip", (-0.062, -0.020, -0.125), (0.048, 0.040, 0.100), "wood"),
        Box("guard", (-0.010, -0.015, -0.048), (0.055, 0.030, 0.022), "steel"),
    ]


def ammo_tin():
    """Small belt-ammunition tin."""
    W, D, H = 0.30, 0.15, 0.19
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H - 0.03),
            {"front": "olive_stencil", "back": "olive_stencil",
             "left": "olive_metal", "right": "olive_metal",
             "top": "olive_metal", "bottom": "olive_metal"}),
        Box("lid", (-W / 2 - 0.006, -D / 2 - 0.006, H - 0.03),
            (W + 0.012, D + 0.012, 0.03), "olive_metal"),
        Box("handle", (-0.05, -0.02, H), (0.10, 0.04, 0.02), "steel"),
    ]


def field_radio():
    """Backpack radio set."""
    W, D, H = 0.30, 0.18, 0.34
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H), "olive_metal"),
        Box("panel", (-W / 2 + 0.02, -D / 2 - 0.012, 0.06),
            (W - 0.04, 0.014, 0.18), "steel_panel"),
        Cylinder("dialA", (-0.06, -D / 2 - 0.02, 0.13), 0.028, 0.012, "steel", n=8),
        Cylinder("dialB", (0.05, -D / 2 - 0.02, 0.13), 0.020, 0.012, "steel", n=8),
        Box("antenna", (0.10, -0.008, H), (0.016, 0.016, 0.26), "steel"),
        Box("handle", (-0.07, -0.03, H), (0.14, 0.06, 0.025), "canvas"),
    ]


def bucket():
    """Galvanised bucket."""
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.14, 0.26, "steel_worn", n=10),
        Cylinder("rim", (0, 0, 0.24), 0.145, 0.02, "steel", n=10),
        Box("handle", (-0.145, -0.008, 0.24), (0.29, 0.016, 0.02), "steel"),
    ]


def lamp_cage():
    """Caged bulkhead lamp."""
    p = [Cylinder("base", (0, 0, 0), 0.075, 0.045, "steel_worn", n=8),
         Cylinder("glass", (0, 0, 0.045), 0.055, 0.105, "glass_lens", n=8),
         Cylinder("cap", (0, 0, 0.150), 0.070, 0.025, "steel", n=8)]
    for i, (dx, dy) in enumerate(((0.062, 0), (-0.062, 0), (0, 0.062), (0, -0.062))):
        p.append(Box(f"bar{i}", (dx - 0.011, dy - 0.011, 0.040),
                     (0.022, 0.022, 0.115), "steel"))
    return "prop", p


def pipe_valve():
    """Pipe run with a hand wheel - the cheapest way to say 'bunker'."""
    return "furniture", [
        Cylinder("pipe", (0, 0, 0), 0.07, 1.20, "steel_worn", n=10),
        Cylinder("flange", (0, 0, 0.52), 0.10, 0.04, "steel", n=10),
        Cylinder("wheel", (0, 0.14, 0.56), 0.13, 0.02, "steel_panel", n=12),
        Box("stem", (-0.02, 0.0, 0.55), (0.04, 0.15, 0.04), "steel"),
    ]


REGISTRY = {
    "SM_Locker_Steel_01": locker_steel,
    "SM_Cabinet_Wall_01": cabinet_wall,
    "SM_Cabinet_Filing_01": filing_cabinet,
    "SM_Shelf_Steel_01": shelf_unit,
    "SM_Crate_Ammo_01": crate_ammo,
    "SM_Crate_Wood_01": crate_wood,
    "SM_Barrel_Steel_01": barrel_steel,
    "SM_Table_Steel_01": table_steel,
    "SM_Desk_Wood_01": desk_wood,
    "SM_Chair_Wood_01": chair_wood,
    "SM_Stool_Metal_01": stool_metal,
    "SM_Couch_Worn_01": couch_worn,
    "SM_Bunk_Steel_01": bunk_bed,
    "SM_Map_Wall_01": map_wall,
    "SM_Board_Notice_01": notice_board,
    "SM_JerryCan_01": jerrycan,
    "SM_GasMask_01": gasmask,
    "SM_Helmet_Steel_01": helmet_steel,
    "SM_Vest_Armor_01": vest_armor,
    "SM_Rifle_01": rifle,
    "SM_Pistol_01": pistol,
    "SM_AmmoTin_01": ammo_tin,
    "SM_Radio_Field_01": field_radio,
    "SM_Bucket_01": bucket,
    "SM_Lamp_Cage_01": lamp_cage,
    "SM_Pipe_Valve_01": pipe_valve,
}


# --- clutter: the layer that makes a room look lived in --------------------
# These are what sell a bunker. Furniture says "a room exists"; a half-used
# tin of roach powder next to an overflowing ashtray says someone lives here.


def ashtray():
    """Glass ashtray with a bed of ash and butts."""
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.070, 0.028, "glass_lens", n=10),
        Cylinder("bowl", (0, 0, 0.020), 0.055, 0.010, "ash", n=10),
    ]


def bug_spray():
    """Aerosol tin of roach powder."""
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.032, 0.150,
                 {"side": "label_red", "top": "chrome", "bottom": "chrome"}, n=10),
        Cylinder("neck", (0, 0, 0.150), 0.016, 0.014, "chrome", n=8),
        Cylinder("cap", (0, 0, 0.164), 0.022, 0.026, "rubber", n=8),
    ]


def glass_jar():
    """Preserve jar with a screw lid."""
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.045, 0.115, "glass_lens", n=10),
        Cylinder("lid", (0, 0, 0.115), 0.047, 0.014, "olive_metal", n=10),
    ]


def beer_bottle():
    """Stubby brown bottle."""
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.033, 0.145, "wood", n=10),
        Cylinder("label", (0, 0, 0.045), 0.034, 0.055, "label_red", n=10),
        Cylinder("neck", (0, 0, 0.145), 0.014, 0.070, "wood", n=8),
        Cylinder("cap", (0, 0, 0.215), 0.016, 0.010, "chrome", n=8),
    ]


def enamel_mug():
    """Chipped enamel mug."""
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.042, 0.090, "enamel", n=10),
        Box("handle", (0.042, -0.008, 0.030), (0.028, 0.016, 0.040), "enamel"),
    ]


def tin_plate():
    return "prop", [
        Cylinder("base", (0, 0, 0), 0.105, 0.010, "enamel", n=12),
        Cylinder("rim", (0, 0, 0.010), 0.115, 0.008, "enamel", n=12),
    ]


def mess_tin():
    """Aluminium mess tin with a folded handle."""
    W, D, H = 0.16, 0.10, 0.07
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H), "chrome"),
        Box("lid", (-W / 2 - 0.004, -D / 2 - 0.004, H), (W + 0.008, D + 0.008, 0.012), "chrome"),
        Box("handle", (-W / 2 - 0.02, -0.012, 0.02), (0.02, 0.024, 0.03), "chrome"),
    ]


def bread_loaf():
    """Dark rye brick."""
    W, D, H = 0.22, 0.11, 0.09
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H - 0.02), "bread"),
        Box("crown", (-W / 2 + 0.012, -D / 2 + 0.008, H - 0.02),
            (W - 0.024, D - 0.016, 0.02), "bread"),
    ]


def sausage():
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.026, 0.180, "meat", n=8),
        Cylinder("tie", (0, 0, 0.180), 0.010, 0.014, "paper", n=6),
    ]


def matchbox():
    W, D, H = 0.055, 0.036, 0.016
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H),
            {"front": "label_red", "back": "cardboard", "left": "cardboard",
             "right": "cardboard", "top": "label_red", "bottom": "cardboard"}),
    ]


def canteen():
    """Felt-covered water bottle."""
    W, D, H = 0.10, 0.055, 0.20
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H - 0.03), "canvas"),
        Cylinder("neck", (0, 0, H - 0.03), 0.016, 0.022, "olive_metal", n=8),
        Cylinder("cap", (0, 0, H - 0.008), 0.019, 0.014, "rubber", n=8),
    ]


def first_aid():
    """Field medical box."""
    W, D, H = 0.24, 0.14, 0.13
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H - 0.02),
            {"front": "label_red", "back": "olive_metal", "left": "olive_metal",
             "right": "olive_metal", "top": "olive_metal", "bottom": "unseen"}),
        Box("lid", (-W / 2 - 0.005, -D / 2 - 0.005, H - 0.02),
            (W + 0.01, D + 0.01, 0.02), "olive_metal"),
        Box("clasp", (-0.02, -D / 2 - 0.008, H - 0.06), (0.04, 0.01, 0.04), "chrome"),
    ]


def book_stack():
    """Three tired hardbacks."""
    p, z = [], 0.0
    for i, (w, d, h) in enumerate(((0.17, 0.12, 0.030),
                                   (0.15, 0.11, 0.026),
                                   (0.16, 0.115, 0.022))):
        p.append(Box(f"book{i}", (-w / 2 + i * 0.008, -d / 2, z), (w, d, h),
                     {"front": "paper", "back": "label_red", "left": "label_red",
                      "right": "paper", "top": "label_red", "bottom": "paper"}))
        z += h
    return "prop", p


def paper_stack():
    p, z = [], 0.0
    for i in range(4):
        p.append(Box(f"sheet{i}", (-0.105 + i * 0.004, -0.075, z),
                     (0.21, 0.15, 0.004), "paper"))
        z += 0.004
    return "prop", p


def kettle():
    """Sooty stovetop kettle."""
    return "prop", [
        Cylinder("body", (0, 0, 0), 0.075, 0.115, "steel_worn", n=10),
        Cylinder("lid", (0, 0, 0.115), 0.048, 0.016, "steel", n=8),
        Box("spout", (0.070, -0.012, 0.060), (0.055, 0.024, 0.028), "steel_worn"),
        Box("handle", (-0.020, -0.010, 0.131), (0.040, 0.020, 0.040), "rubber"),
    ]


def oil_lamp():
    """Kerosene hurricane lamp."""
    return "prop", [
        Cylinder("reservoir", (0, 0, 0), 0.048, 0.055, "chrome", n=10),
        Cylinder("glass", (0, 0, 0.055), 0.036, 0.090, "glass_lens", n=10),
        Cylinder("cowl", (0, 0, 0.145), 0.042, 0.020, "steel_worn", n=10),
        Box("bail", (-0.040, -0.005, 0.165), (0.080, 0.010, 0.030), "steel"),
    ]


def toolbox():
    W, D, H = 0.36, 0.16, 0.14
    return "prop", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H), "steel_worn"),
        Box("handle", (-0.06, -0.012, H), (0.12, 0.024, 0.022), "steel"),
        Box("latch", (-0.03, -D / 2 - 0.006, H - 0.05), (0.06, 0.008, 0.03), "chrome"),
    ]


def poster_wall():
    """Propaganda sheet, pinned flat."""
    W, H, T = 0.42, 0.60, 0.004
    return "prop", [
        Box("sheet", (-W / 2, 0, 0), (W, T, H),
            # a poster is pinned flat; only its face is ever on screen
            {"front": "label_red", "back": "unseen", "left": "unseen",
             "right": "unseen", "top": "unseen", "bottom": "unseen"}),
    ]


def wall_clock():
    return "prop", [
        Cylinder("case", (0, 0, 0), 0.11, 0.045, "rubber", n=12),
        Cylinder("face", (0, 0, 0.045), 0.095, 0.006, "enamel", n=12),
    ]


def rag_pile():
    """Heap of oily rags."""
    p = []
    for i, (x, y, w, d, h) in enumerate(((-0.06, -0.04, 0.16, 0.12, 0.035),
                                         (-0.02, -0.07, 0.13, 0.14, 0.030),
                                         (-0.05, -0.02, 0.11, 0.09, 0.028))):
        p.append(Box(f"rag{i}", (x, y, i * 0.022), (w, d, h), "fabric"))
    return "prop", p


REGISTRY.update({
    "SM_Ashtray_01": ashtray,
    "SM_BugSpray_01": bug_spray,
    "SM_Jar_Glass_01": glass_jar,
    "SM_Bottle_Beer_01": beer_bottle,
    "SM_Mug_Enamel_01": enamel_mug,
    "SM_Plate_Tin_01": tin_plate,
    "SM_MessTin_01": mess_tin,
    "SM_Bread_01": bread_loaf,
    "SM_Sausage_01": sausage,
    "SM_Matchbox_01": matchbox,
    "SM_Canteen_01": canteen,
    "SM_FirstAid_01": first_aid,
    "SM_Books_01": book_stack,
    "SM_Papers_01": paper_stack,
    "SM_Kettle_01": kettle,
    "SM_Lamp_Oil_01": oil_lamp,
    "SM_Toolbox_01": toolbox,
    "SM_Poster_01": poster_wall,
    "SM_Clock_Wall_01": wall_clock,
    "SM_Rags_01": rag_pile,
})


# --- round things ----------------------------------------------------------
# Everything above this line is boxes and straight cylinders, which is why the
# weapons and the gas mask read as blocky. Frustums, spheres and per-part
# rotation are what let a cartridge taper and a grenade be round at a budget
# a PS1 would have accepted.

from kit import Sphere


def ceiling_light():
    """Surface-mounted panel fixture. The `emitter` face gets its own emissive
    material slot in the scene, so the light visibly comes from the diffuser
    rather than from an unexplained point in the air."""
    W, D, H = 0.62, 0.22, 0.09
    return "furniture", [
        Box("housing", (-W / 2, -D / 2, 0), (W, D, H),
            {"front": "steel_worn", "back": "steel_worn", "left": "steel",
             "right": "steel", "top": "unseen", "bottom": "steel_worn"}),
        Box("diffuser", (-W / 2 + 0.03, -D / 2 + 0.025, -0.018),
            (W - 0.06, D - 0.05, 0.020), "emitter"),
        Box("bracketL", (-W / 2 + 0.06, -0.018, H), (0.03, 0.036, 0.05), "steel"),
        Box("bracketR", (W / 2 - 0.09, -0.018, H), (0.03, 0.036, 0.05), "steel"),
    ]


def cartridge():
    """A single rifle round: tapered brass case, copper tip."""
    return "prop", [
        Cylinder("rim", (0, 0, 0), 0.0060, 0.002, "brass", n=8),
        Cylinder("case", (0, 0, 0.002), 0.0058, 0.036, "brass", n=8, r2=0.0042),
        Cylinder("neck", (0, 0, 0.038), 0.0042, 0.006, "brass", n=8, r2=0.0040),
        Cylinder("bullet", (0, 0, 0.044), 0.0040, 0.016, "copper", n=8, r2=0.0012),
    ]


def cartridge_pile():
    """Loose rounds lying where they were dropped."""
    p = []
    spread = ((0.00, 0.00, 90, 12), (0.03, 0.015, 90, -34), (-0.025, 0.02, 90, 58),
              (0.012, -0.028, 90, 140), (-0.04, -0.01, 90, 96), (0.05, -0.02, 90, 20))
    for i, (dx, dy, ry, rz) in enumerate(spread):
        p.append(Cylinder(f"case{i}", (dx, dy, 0.006), 0.0058, 0.036, "brass",
                          n=8, r2=0.0042, rot=(0, ry, rz), centre=True))
        p.append(Cylinder(f"tip{i}", (dx + 0.026, dy, 0.006), 0.0040, 0.016, "copper",
                          n=8, r2=0.0012, rot=(0, ry, rz), centre=True))
    return "prop", p


def ammo_belt():
    """Linked belt. Rounds nearly touching, with a visible link between each -
    spaced out they read as beads on a string rather than as ammunition."""
    p = []
    for i in range(11):
        x = -0.16 + i * 0.032
        tilt = 5 * math.sin(i * 0.9)
        p.append(Cylinder(f"rnd{i}", (x, 0.004, 0.028), 0.0062, 0.052, "brass",
                          n=8, r2=0.0044, rot=(90 + tilt, 0, 0), centre=True))
        p.append(Cylinder(f"tip{i}", (x, -0.030, 0.028), 0.0044, 0.018, "copper",
                          n=8, r2=0.0014, rot=(90 + tilt, 0, 0), centre=True))
        p.append(Box(f"link{i}", (x - 0.019, 0.010, 0.014), (0.038, 0.026, 0.012),
                     "gunmetal", rot=(tilt, 0, 0)))
    return "prop", p


def grenade():
    """Fragmentation grenade: a squashed sphere with a fuse."""
    return "prop", [
        Sphere("body", (0, 0, 0.038), 0.030, "olive_metal", seg=12, ring=8,
               squash=1.25),
        Cylinder("collar", (0, 0, 0.066), 0.011, 0.010, "gunmetal", n=8),
        Cylinder("fuse", (0, 0, 0.076), 0.009, 0.020, "gunmetal", n=8, r2=0.007),
        Box("lever", (-0.006, -0.030, 0.062), (0.012, 0.038, 0.006), "gunmetal"),
    ]


def rifle_v2():
    """Rounded service rifle: cylindrical barrel and gas tube, tapered muzzle,
    curved magazine. The box-composite version read as a plank."""
    return "prop", [
        Box("receiver", (-0.17, -0.026, 0.0), (0.33, 0.052, 0.080), "gunmetal"),
        Box("stock", (-0.45, -0.024, -0.018), (0.29, 0.048, 0.086), "wood",
            rot=(0, -4, 0)),
        Box("comb", (-0.33, -0.022, 0.066), (0.15, 0.044, 0.026), "wood"),
        Box("grip", (-0.10, -0.023, -0.112), (0.050, 0.046, 0.118), "wood",
            rot=(0, -14, 0)),
        Cylinder("handguard", (0.255, 0, 0.038), 0.028, 0.19, "wood", n=10,
                 rot=(0, 90, 0), centre=True),
        Cylinder("barrel", (0.435, 0, 0.038), 0.011, 0.18, "gunmetal", n=8,
                 r2=0.009, rot=(0, 90, 0), centre=True),
        Cylinder("gastube", (0.30, 0, 0.068), 0.008, 0.18, "gunmetal", n=6,
                 rot=(0, 90, 0), centre=True),
        Cylinder("muzzle", (0.535, 0, 0.038), 0.013, 0.032, "gunmetal", n=8,
                 r2=0.011, rot=(0, 90, 0), centre=True),
        Box("mag", (-0.02, -0.022, -0.175), (0.072, 0.044, 0.170), "gunmetal",
            rot=(0, 12, 0)),
        Cylinder("rearsight", (-0.10, 0, 0.072), 0.010, 0.024, "gunmetal", n=6),
        Cylinder("frontsight", (0.50, 0, 0.042), 0.008, 0.026, "gunmetal", n=6),
    ]


def smg():
    """Compact submachine gun with a wire stock."""
    return "prop", [
        Box("receiver", (-0.10, -0.024, 0), (0.26, 0.048, 0.070), "gunmetal"),
        Cylinder("barrel", (0.22, 0, 0.034), 0.010, 0.13, "gunmetal", n=8,
                 rot=(0, 90, 0), centre=True),
        Cylinder("shroud", (0.20, 0, 0.034), 0.020, 0.10, "gunmetal", n=10,
                 rot=(0, 90, 0), centre=True),
        Box("grip", (-0.04, -0.020, -0.100), (0.044, 0.040, 0.104), "rubber",
            rot=(0, -12, 0)),
        Box("mag", (0.06, -0.018, -0.150), (0.052, 0.036, 0.155), "gunmetal"),
        Box("stockA", (-0.28, -0.020, 0.020), (0.19, 0.010, 0.010), "gunmetal"),
        Box("stockB", (-0.28, 0.012, 0.020), (0.19, 0.010, 0.010), "gunmetal"),
        Box("butt", (-0.30, -0.024, 0.006), (0.026, 0.048, 0.040), "gunmetal"),
    ]


def revolver():
    """Service revolver, 235mm overall. The first pass had a grip as long as
    the frame; a sidearm's proportions are unforgiving because everyone knows
    what one looks like."""
    return "prop", [
        Box("frame", (-0.040, -0.013, 0), (0.085, 0.026, 0.032), "gunmetal"),
        Cylinder("cyl", (0.000, 0, 0.016), 0.019, 0.036, "gunmetal", n=10,
                 rot=(0, 90, 0), centre=True),
        Cylinder("barrel", (0.082, 0, 0.016), 0.0085, 0.075, "gunmetal", n=8,
                 rot=(0, 90, 0), centre=True),
        Box("rib", (0.046, -0.005, 0.026), (0.072, 0.010, 0.010), "gunmetal"),
        Box("grip", (-0.044, -0.014, -0.072), (0.034, 0.028, 0.076), "rubber",
            rot=(0, -20, 0)),
        Box("hammer", (-0.044, -0.006, 0.030), (0.016, 0.012, 0.014), "gunmetal"),
        Box("guard", (-0.014, -0.010, -0.030), (0.040, 0.020, 0.014), "gunmetal"),
        Box("trigger", (-0.004, -0.004, -0.026), (0.008, 0.008, 0.016),
            "gunmetal", rot=(0, 12, 0)),
    ]


# --- refuse ----------------------------------------------------------------

def trash_pile():
    """A heap of indeterminate refuse. Squashed spheres and tilted boxes read
    as a pile; a stack of neat boxes never does."""
    p = []
    lumps = ((0.00, 0.00, 0.075, 0.55, (12, 8, 20)),
             (0.09, 0.04, 0.055, 0.60, (-10, 14, 70)),
             (-0.08, 0.05, 0.048, 0.50, (16, -8, 130)),
             (0.03, -0.09, 0.060, 0.58, (-14, 10, 200)),
             (-0.10, -0.06, 0.042, 0.52, (8, 12, 300)))
    for i, (x, y, r, sq, rot) in enumerate(lumps):
        p.append(Sphere(f"lump{i}", (x, y, r * sq), r, "trash",
                        seg=8, ring=5, squash=sq, rot=rot))
    for i, (x, y, w, d, h, rot) in enumerate(
            ((0.06, -0.02, 0.10, 0.07, 0.035, (0, 18, 26)),
             (-0.05, 0.09, 0.08, 0.06, 0.030, (12, 0, 118)),
             (0.11, 0.09, 0.07, 0.05, 0.025, (-14, 6, 200)))):
        p.append(Box(f"card{i}", (x, y, 0.01), (w, d, h), "trash", rot=rot))
    for i, (x, y, rot) in enumerate(((-0.13, -0.02, (0, 90, 30)),
                                     (0.14, -0.06, (0, 90, 110)))):
        p.append(Cylinder(f"can{i}", (x, y, 0.033), 0.033, 0.095, "steel_worn",
                          n=8, rot=rot, centre=True))
    return "furniture", p


def scrap_pile():
    """Cut offcuts and bent plate - the industrial cousin of the trash heap."""
    p = []
    for i, (x, y, z, w, d, h, rot) in enumerate(
            ((0.00, 0.00, 0.00, 0.28, 0.20, 0.020, (4, 3, 12)),
             (-0.04, 0.03, 0.02, 0.22, 0.16, 0.018, (-8, 6, 62)),
             (0.06, -0.03, 0.04, 0.24, 0.12, 0.016, (10, -5, 118)),
             (0.02, 0.05, 0.055, 0.16, 0.14, 0.014, (-6, 9, 170)))):
        p.append(Box(f"plate{i}", (x - w / 2, y - d / 2, z), (w, d, h),
                     "steel_worn", rot=rot))
    for i, (x, y, rot) in enumerate(((0.12, 0.06, (0, 78, 40)),
                                     (-0.11, -0.07, (0, 84, 130)),
                                     (0.03, -0.10, (0, 70, 200)))):
        p.append(Cylinder(f"bar{i}", (x, y, 0.030), 0.014, 0.30, "steel_worn",
                          n=6, rot=rot, centre=True))
    return "furniture", p


def debris_small():
    """Loose floor litter to scatter between the big pieces."""
    p = []
    for i, (x, y, r, sq, rot) in enumerate(
            ((0.00, 0.00, 0.028, 0.45, (0, 0, 20)),
             (0.07, 0.05, 0.020, 0.40, (0, 0, 80)),
             (-0.06, 0.03, 0.024, 0.38, (0, 0, 150)))):
        p.append(Sphere(f"bit{i}", (x, y, r * sq), r, "trash",
                        seg=6, ring=4, squash=sq, rot=rot))
    for i, (x, y, rot) in enumerate(((0.05, -0.05, (2, 0, 24)),
                                     (-0.04, -0.06, (0, 3, 96)))):
        p.append(Box(f"paper{i}", (x, y, 0.001), (0.09, 0.065, 0.003),
                     "paper", rot=rot))
    return "prop", p


def locker_open():
    """Locker with one door swung open: hanging rail, hanger and a coat.

    Built from panels, not a solid box with a dark face painted on the front.
    A closed box has no interior, so the coat inside the first version was
    sealed in and invisible - the whole point of an open door is that you can
    see what is in there.
    """
    W, D, H = 0.80, 0.50, 1.85
    t = 0.025                      # sheet thickness
    hw = W / 2 - t
    p = [
        Box("plinth", (-W / 2, -D / 2, 0), (W, D, 0.08), "steel_worn"),
        Box("back", (-W / 2, D / 2 - t, 0.08), (W, t, H - 0.08),
            {"front": "steel_worn", "back": "steel", "left": "steel",
             "right": "steel", "top": "steel", "bottom": "unseen"}),
        Box("sideL", (-W / 2, -D / 2, 0.08), (t, D, H - 0.08), "steel_panel"),
        Box("sideR", (W / 2 - t, -D / 2, 0.08), (t, D, H - 0.08), "steel_panel"),
        Box("divider", (-t / 2, -D / 2 + t, 0.08), (t, D - t, H - 0.08), "steel"),
        Box("top", (-W / 2, -D / 2, H - t), (W, D, t), "steel"),
        Box("shelf", (-W / 2 + t, -D / 2 + t, H - 0.30), (hw, D - 2 * t, t),
            "steel_worn"),
        # right bay stays shut
        Box("door_shut", (t / 2, -D / 2 - 0.04, 0.10), (hw, 0.04, H - 0.14),
            {"front": "steel_door", "back": "steel", "left": "steel",
             "right": "steel", "top": "steel", "bottom": "steel"}),
        # left bay's door, hinged on the outer jamb and swung open
        Box("hinge_t", (-W / 2 - 0.012, -D / 2 - 0.012, H - 0.34),
            (0.030, 0.044, 0.070), "chrome"),
        Box("hinge_b", (-W / 2 - 0.012, -D / 2 - 0.012, 0.22),
            (0.030, 0.030, 0.070), "chrome"),
        # A door hinges at its edge. Rotating it about its own centre swung
        # the hinge line away from the jamb and left the whole leaf floating.
        Box("door_open", (-W / 2 - 0.012, -D / 2 - 0.38, 0.10),
            (0.040, 0.40, H - 0.14),
            {"front": "steel_panel", "back": "steel_door", "left": "steel_door",
             "right": "steel_panel", "top": "steel", "bottom": "steel"},
            rot=(0, 0, -16), pivot=(-W / 2 + 0.008, -D / 2 + 0.02, 0.9)),
        # contents of the open bay
        Cylinder("rail", (-W / 4, 0, H - 0.36), 0.010, hw - 0.02, "chrome",
                 n=6, rot=(0, 90, 0), centre=True, pivot=(-W / 4, 0, H - 0.36)),
        Box("hanger_bar", (-W / 4 - 0.12, -0.010, H - 0.455),
            (0.24, 0.014, 0.012), "chrome"),
        Cylinder("hanger_hook", (-W / 4, 0, H - 0.45), 0.006, 0.096, "chrome",
                 n=6),
        Box("coat_shoulder", (-W / 4 - 0.15, -0.075, H - 0.565),
            (0.30, 0.15, 0.13), "coat"),
        Box("coat", (-W / 4 - 0.13, -0.068, H - 1.09), (0.26, 0.14, 0.53),
            "coat"),
        Box("coat_hem", (-W / 4 - 0.14, -0.070, H - 1.14),
            (0.28, 0.145, 0.08), "coat", rot=(0, 0, 5)),
        Box("boots", (-W / 4 - 0.11, -0.06, 0.08), (0.22, 0.13, 0.13), "rubber"),
    ]
    return "furniture", p


REGISTRY.update({
    "SM_CeilingLight_01": ceiling_light,
    "SM_Cartridge_01": cartridge,
    "SM_Cartridges_Pile_01": cartridge_pile,
    "SM_AmmoBelt_01": ammo_belt,
    "SM_Grenade_01": grenade,
    "SM_Rifle_02": rifle_v2,
    "SM_SMG_01": smg,
    "SM_Revolver_01": revolver,
    "SM_Trash_Pile_01": trash_pile,
    "SM_Scrap_Pile_01": scrap_pile,
    "SM_Debris_01": debris_small,
    "SM_Locker_Open_01": locker_open,
})


# --- things that look like things ------------------------------------------
# A prop earns its place by being recognisable in silhouette before the texture
# loads. Each of these is built around the one shape that identifies it: a
# hammer is a heavy head on a thin handle, a valve radio is a wooden case with
# a lit scale, headphones are two cups on an arc.


def hammer():
    """Claw hammer.

    The claw is a CHAIN: each segment starts where the last one ended and
    hinges about that joint. Rotating several segments about one shared pivot
    at different angles fans them out instead of curling them, which is what
    left two blades hanging beside the head.
    """
    L, HZ = 0.300, 0.286
    JX, JZ = -0.026, HZ + 0.020          # where the claw leaves the head
    p = [
        Cylinder("handle", (0, 0, 0), 0.011, L, "wood", n=8, r2=0.015),
        Box("head", (-0.026, -0.019, HZ), (0.052, 0.038, 0.040), "gunmetal"),
        Box("peen", (0.026, -0.013, HZ + 0.006), (0.042, 0.026, 0.028),
            "gunmetal"),
    ]
    x, z = JX, JZ
    for i, (ang, ln, th) in enumerate(((-16, 0.024, 0.026),
                                       (-46, 0.022, 0.022),
                                       (-88, 0.018, 0.018))):
        p.append(Box(f"claw{i}", (x - ln, -th / 2, z - th / 2), (ln, th, th),
                     "gunmetal", rot=(0, ang, 0), pivot=(x, 0, z)))
        a = math.radians(ang)
        x, z = x - ln * math.cos(a), z + ln * math.sin(a)
    return "prop", p

def wrench():
    """Open-ended spanner. Both heads hinge about the end of the shaft they
    are welded to, so the joint stays closed at any angle."""
    Z = 0.005
    return "prop", [
        Box("shaft", (-0.100, -0.011, 0), (0.200, 0.022, 0.010), "chrome"),
        Box("head_a", (-0.142, -0.021, 0), (0.044, 0.042, 0.010), "chrome",
            rot=(0, 0, 15), pivot=(-0.098, 0, Z)),
        Box("slot_a", (-0.142, -0.007, 0.0008), (0.026, 0.014, 0.011), "dark",
            rot=(0, 0, 15), pivot=(-0.098, 0, Z)),
        Box("head_b", (0.098, -0.019, 0), (0.040, 0.038, 0.010), "chrome",
            rot=(0, 0, -15), pivot=(0.098, 0, Z)),
        Box("slot_b", (0.114, -0.006, 0.0008), (0.024, 0.012, 0.011), "dark",
            rot=(0, 0, -15), pivot=(0.098, 0, Z)),
    ]


def pliers():
    """Combination pliers. Both arms pivot about the pin, which is the only
    way the jaws meet and the handles splay from the same point."""
    PX, PZ = 0.030, 0.010
    P = (PX, 0, PZ)
    return "prop", [
        Box("jawL", (PX, -0.010, 0.004), (0.072, 0.009, 0.012), "chrome",
            rot=(0, 0, 7), pivot=P),
        Box("jawR", (PX, 0.001, 0.004), (0.072, 0.009, 0.012), "chrome",
            rot=(0, 0, -7), pivot=P),
        Box("noseL", (PX + 0.060, -0.008, 0.005), (0.030, 0.006, 0.010),
            "chrome", rot=(0, 0, 11), pivot=P),
        Box("noseR", (PX + 0.060, 0.002, 0.005), (0.030, 0.006, 0.010),
            "chrome", rot=(0, 0, -11), pivot=P),
        Cylinder("pin", (PX, 0, PZ), 0.010, 0.026, "chrome", n=8,
                 rot=(90, 0, 0), centre=True),
        Box("gripL", (PX - 0.135, -0.015, 0.004), (0.135, 0.012, 0.012),
            "red_grip", rot=(0, 0, -11), pivot=P),
        Box("gripR", (PX - 0.135, 0.003, 0.004), (0.135, 0.012, 0.012),
            "red_grip", rot=(0, 0, 11), pivot=P),
        Box("armL", (PX - 0.045, -0.014, 0.004), (0.048, 0.010, 0.012),
            "chrome", rot=(0, 0, -11), pivot=P),
        Box("armR", (PX - 0.045, 0.004, 0.004), (0.048, 0.010, 0.012),
            "chrome", rot=(0, 0, 11), pivot=P),
    ]


def screwdriver():
    return "prop", [
        Cylinder("handle", (0, 0, 0.045), 0.016, 0.090, "yellow_paint", n=8,
                 r2=0.013),
        Cylinder("collar", (0, 0, 0.090), 0.008, 0.008, "chrome", n=8),
        Cylinder("shaft", (0, 0, 0.098), 0.0045, 0.110, "chrome", n=6),
        Box("tip", (-0.006, -0.0015, 0.205), (0.012, 0.003, 0.014), "chrome"),
    ]


def tool_board():
    """Perforated wall board with tools hung on it, plus painted outlines -
    the thing that says workshop faster than any amount of clutter."""
    W, H, T = 0.90, 0.62, 0.020
    p = [Box("board", (-W / 2, 0, 0), (W, T, H),
             {"front": "pegboard", "back": "unseen", "left": "wood",
              "right": "wood", "top": "wood", "bottom": "wood"})]
    for i, (x, z, w, h) in enumerate(((-0.34, 0.40, 0.030, 0.20),
                                      (-0.22, 0.38, 0.026, 0.22),
                                      (-0.08, 0.42, 0.034, 0.16))):
        p.append(Box(f"tool{i}", (x, -0.018, z), (w, 0.018, h), "chrome"))
    p.append(Cylinder("coil", (0.24, -0.004, 0.34), 0.085, 0.024, "rubber",
                      n=12, rot=(90, 0, 0), centre=True))
    p.append(Box("saw", (0.02, -0.016, 0.10), (0.34, 0.014, 0.090), "chrome",
                 rot=(0, 0, 0)))
    p.append(Box("saw_grip", (0.34, -0.020, 0.08), (0.070, 0.020, 0.070),
                 "wood"))
    return "furniture", p


def radio_valve():
    """Wooden-cased valve set: lit tuning scale, speaker grille, two knobs."""
    W, D, H = 0.44, 0.24, 0.30
    return "furniture", [
        Box("case", (-W / 2, -D / 2, 0), (W, D, H),
            {"front": "wood", "back": "wood", "left": "wood", "right": "wood",
             "top": "wood", "bottom": "unseen"}),
        Box("grille", (-W / 2 + 0.03, -D / 2 - 0.008, 0.04),
            (0.22, 0.010, 0.17), "speaker"),
        Box("scale", (0.00, -D / 2 - 0.010, 0.15), (0.18, 0.012, 0.075),
            "dial"),
        Box("bezel", (-0.006, -D / 2 - 0.014, 0.144),
            (0.192, 0.008, 0.087), "brass"),
        Cylinder("knobA", (0.05, -D / 2 - 0.012, 0.075), 0.022, 0.022,
                 "bakelite", n=10, rot=(90, 0, 0), centre=True),
        Cylinder("knobB", (0.15, -D / 2 - 0.012, 0.075), 0.022, 0.022,
                 "bakelite", n=10, rot=(90, 0, 0), centre=True),
        Box("feet", (-W / 2 + 0.02, -D / 2 + 0.02, -0.014),
            (W - 0.04, D - 0.04, 0.014), "bakelite"),
    ]


def headphones():
    """Bakelite cups on a sprung steel arc.

    Three things had to be right. Each segment sits ON the arc rather than
    being rotated in place, or every one pivots about the same point and the
    band becomes a star. The tangent at angle `a` is reached by rotating -a,
    not +a. And the arc has to run far enough round to actually reach the
    cups - stopping at 64 degrees left a visible gap on both sides.
    """
    R, CZ = 0.092, 0.020          # arc radius, and the centre it swings about
    SPAN, N = 78.0, 11
    CUP_Y, CUP_Z = 0.089, 0.036
    p = []
    for i in range(N):
        a = math.radians(-SPAN + i * (2 * SPAN / (N - 1)))
        cy, cz = R * math.sin(a), CZ + R * math.cos(a)
        p.append(Box(f"band{i}", (-0.006, cy - 0.015, cz - 0.005),
                     (0.012, 0.030, 0.010), "chrome",
                     rot=(-math.degrees(a), 0, 0)))
    for i, sy in enumerate((-1, 1)):
        p.append(Cylinder(f"cup{i}", (0, sy * CUP_Y, CUP_Z), 0.033, 0.028,
                          "bakelite", n=10, rot=(90, 0, 0), centre=True))
        p.append(Cylinder(f"pad{i}", (0, sy * (CUP_Y - 0.019), CUP_Z), 0.029,
                          0.014, "rubber", n=10, rot=(90, 0, 0), centre=True))
    p.append(Cylinder("cord", (0.02, -0.105, 0.006), 0.005, 0.13, "rubber",
                      n=6, rot=(0, 80, 28), centre=True))
    return "prop", p


def field_phone():
    """Crank telephone in a wooden box."""
    W, D, H = 0.24, 0.16, 0.20
    return "prop", [
        Box("case", (-W / 2, -D / 2, 0), (W, D, H),
            {"front": "bakelite", "back": "wood", "left": "wood",
             "right": "wood", "top": "wood", "bottom": "unseen"}),
        Box("handset", (-0.085, -D / 2 - 0.030, H),
            (0.170, 0.040, 0.030), "bakelite"),
        Cylinder("ear", (-0.070, -D / 2 - 0.010, H + 0.015), 0.026, 0.026,
                 "bakelite", n=8, centre=True),
        Cylinder("mouth", (0.070, -D / 2 - 0.010, H + 0.015), 0.026, 0.026,
                 "bakelite", n=8, centre=True),
        Cylinder("crank", (W / 2 + 0.010, 0, 0.12), 0.010, 0.030, "chrome",
                 n=6, rot=(0, 90, 0), centre=True),
        Box("crank_arm", (W / 2 + 0.020, -0.006, 0.12), (0.012, 0.012, 0.055),
            "chrome"),
        Box("plate", (-0.05, -D / 2 - 0.006, 0.05), (0.10, 0.008, 0.05),
            "brass"),
    ]


def gauge_wall():
    """Pressure gauge on a stub of pipe."""
    return "prop", [
        Cylinder("pipe", (0, 0.03, 0), 0.016, 0.09, "steel_worn", n=8,
                 rot=(90, 0, 0), centre=True),
        Cylinder("body", (0, -0.030, 0), 0.058, 0.036, "brass", n=12,
                 rot=(90, 0, 0), centre=True),
        Cylinder("face", (0, -0.050, 0), 0.050, 0.006, "dial", n=12,
                 rot=(90, 0, 0), centre=True),
    ]


def locker_blue():
    """Same locker, painted institutional blue. A set needs repeats that are
    not identical, and paint is the cheapest way to get one."""
    W, D, H = 0.80, 0.50, 1.85
    p = [Box("body", (-W / 2, -D / 2, 0.08), (W, D, H - 0.08),
             {"front": "blue_paint", "back": "steel", "left": "blue_paint",
              "right": "blue_paint", "top": "blue_paint", "bottom": "unseen"}),
         Box("plinth", (-W / 2, -D / 2, 0), (W, D, 0.08), "steel_worn")]
    for i, x in enumerate((-W / 2 + 0.02, 0.01)):
        p.append(Box(f"door{i}", (x, -D / 2 - 0.045, 0.14),
                     (W / 2 - 0.03, 0.045, H - 0.22),
                     {"front": "blue_door", "back": "dark", "left": "blue_paint",
                      "right": "blue_paint", "top": "blue_paint",
                      "bottom": "blue_paint"}))
    return "furniture", p


def crate_hazard():
    """Yellow-and-black striped shipping crate."""
    W, D, H = 0.62, 0.40, 0.36
    return "furniture", [
        Box("body", (-W / 2, -D / 2, 0), (W, D, H - 0.05),
            {"front": "hazard", "back": "hazard", "left": "yellow_paint",
             "right": "yellow_paint", "top": "yellow_paint", "bottom": "unseen"}),
        Box("lid", (-W / 2 - 0.012, -D / 2 - 0.012, H - 0.05),
            (W + 0.024, D + 0.024, 0.05), "yellow_paint"),
        Box("clasp", (-0.03, -D / 2 - 0.010, H - 0.12), (0.06, 0.012, 0.07),
            "gunmetal"),
    ]


def figure_stalker():
    """A gaunt figure in a long coat and a respirator.

    Deliberately wrong: too tall, narrow across the shoulders, arms too long,
    head slightly too small, standing a fraction off vertical. Narrow is the
    unsettling part; flat is just a mistake, and the first version was 150mm
    front to back, so from the side it read as a cardboard cutout. PS1 human meshes were crude enough
    that a viewer fills in the rest, and the uncanny reading comes from the
    proportions rather than from any detail the budget could not afford.
    """
    p = [
        # boots and legs
        Box("bootL", (-0.105, -0.055, 0), (0.085, 0.135, 0.085), "rubber",
            rot=(0, 0, -8)),
        Box("bootR", (0.022, -0.050, 0), (0.085, 0.135, 0.085), "rubber",
            rot=(0, 0, 11)),
        Box("legL", (-0.092, -0.048, 0.085), (0.068, 0.096, 0.420), "coat",
            rot=(0, 2, 0)),
        Box("legR", (0.028, -0.046, 0.085), (0.068, 0.096, 0.420), "coat",
            rot=(0, -3, 0)),
        # the coat: a long tapered slab, wider at the hem
        Box("coat_skirt", (-0.140, -0.105, 0.380), (0.280, 0.215, 0.470),
            "coat", rot=(0, 1, 0)),
        Box("coat_body", (-0.128, -0.100, 0.840), (0.256, 0.205, 0.330),
            "coat"),
        Box("shoulders", (-0.168, -0.098, 1.090), (0.336, 0.200, 0.085),
            "coat", rot=(0, 0, 2)),
        Box("lapel", (-0.078, -0.112, 1.020), (0.156, 0.022, 0.150), "coat",
            rot=(0, 0, 3)),
        # arms hang too long, barely bent
        Box("armL", (-0.196, -0.062, 0.690), (0.074, 0.124, 0.480), "coat",
            rot=(0, 6, 0)),
        Box("armR", (0.122, -0.062, 0.680), (0.074, 0.124, 0.490), "coat",
            rot=(0, -8, 0)),
        Box("handL", (-0.186, -0.042, 0.628), (0.056, 0.078, 0.078), "skin",
            rot=(0, 5, 0)),
        Box("handR", (0.128, -0.042, 0.608), (0.056, 0.078, 0.078), "skin",
            rot=(0, -7, 0)),
        # neck and head, tilted a few degrees off true
        Cylinder("neck", (0, -0.004, 1.185), 0.036, 0.055, "skin", n=8),
        Sphere("head", (0, -0.010, 1.278), 0.088, "skin", seg=10, ring=7,
               squash=1.18, rot=(6, 0, -9)),
        # respirator: two lenses and a filter where a face should be
        Box("mask", (-0.078, -0.106, 1.222), (0.156, 0.060, 0.110), "rubber",
            rot=(6, 0, -9)),
        Box("lensL", (-0.062, -0.118, 1.288), (0.052, 0.016, 0.040),
            "glass_lens", rot=(6, 0, -9)),
        Box("lensR", (0.012, -0.118, 1.288), (0.052, 0.016, 0.040),
            "glass_lens", rot=(6, 0, -9)),
        Cylinder("filter", (0, -0.150, 1.190), 0.040, 0.075, "olive_metal",
                 n=10, rot=(64, 0, 0), centre=True),
        Box("hood", (-0.098, -0.098, 1.330), (0.196, 0.170, 0.062), "coat",
            rot=(6, 0, -9)),
    ]
    return "furniture", p


REGISTRY.update({
    "SM_Hammer_01": hammer,
    "SM_Wrench_01": wrench,
    "SM_Pliers_01": pliers,
    "SM_Screwdriver_01": screwdriver,
    "SM_ToolBoard_01": tool_board,
    "SM_Radio_Valve_01": radio_valve,
    "SM_Headphones_01": headphones,
    "SM_Phone_Field_01": field_phone,
    "SM_Gauge_Wall_01": gauge_wall,
    "SM_Locker_Blue_01": locker_blue,
    "SM_Crate_Hazard_01": crate_hazard,
    "SM_Figure_Stalker_01": figure_stalker,
})
