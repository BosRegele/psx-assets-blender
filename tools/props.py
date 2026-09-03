"""The bunker set. Each prop is a declaration in metres, nothing more.

Dimensions are real: a locker is 1.85m because that is what a locker is, and
`kit` derives the atlas from them. Getting scale right is not pedantry - it is
what lets a buyer drop the whole set into a scene and have it sit together.

Box `pos` is the minimum corner, `size` is (w, d, h) along (x, y, z).
Cylinder `pos` is the base centre. Every prop's origin is at floor level,
centred in plan, so it drops onto a floor without fixup.
"""
from kit import Box, Cylinder

# --- storage ---------------------------------------------------------------


def locker_steel():
    """Two-door steel locker, the backbone of any bunker dressing kit."""
    W, D, H = 0.80, 0.50, 1.85
    p = [Box("body", (-W / 2, -D / 2, 0.08), (W, D, H - 0.08),
             {"front": "steel_worn", "back": "steel", "left": "steel_panel",
              "right": "steel_panel", "top": "steel", "bottom": "hidden"}),
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
    p = [Box("base", (-W / 2, -D / 2, 0.10), (W, D, 0.28),
             {"front": "fabric", "back": "hidden", "left": "fabric",
              "right": "fabric", "top": "hidden", "bottom": "hidden"}),
         Box("plinth", (-W / 2 + 0.05, -D / 2 + 0.05, 0),
             (W - 0.10, D - 0.10, 0.10), "wood"),
         Box("back", (-W / 2, D / 2 - 0.20, 0.38), (W, 0.20, H - 0.30),
             {"front": "fabric_seam", "back": "fabric", "left": "fabric",
              "right": "fabric", "top": "fabric", "bottom": "hidden"})]
    # Cushions stand 60mm proud of the base with a gap between them; flush
    # cushions read as one slab.
    seat_w = (W - 0.40) / 3
    for i in range(3):
        p.append(Box(f"cushion{i}", (-W / 2 + 0.20 + i * seat_w + 0.012,
                                     -D / 2 + 0.08, 0.38),
                     (seat_w - 0.024, D - 0.30, 0.13),
                     {"front": "fabric_seam", "back": "hidden",
                      "left": "fabric", "right": "fabric",
                      "top": "fabric_seam", "bottom": "hidden"}))
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
        p.append(Box(f"frame{i}", (-W / 2, -D / 2, z), (W, D, 0.06), {"front": "steel_worn", "back": "steel_worn", "left": "steel_worn", "right": "steel_worn", "top": "hidden", "bottom": "steel"}))
        p.append(Box(f"mattress{i}", (-W / 2 + 0.03, -D / 2 + 0.04, z + 0.06),
                     (W - 0.06, D - 0.08, 0.10),
                     {"front": "canvas", "back": "canvas", "left": "canvas",
                      "right": "canvas", "top": "canvas", "bottom": "hidden"}))
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
        Cylinder("filter", (0, -D / 2 - 0.055, 0.03), 0.045, 0.09, "olive_metal", n=10),
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
        Box("sight", (0.31, -0.014, 0.090), (0.036, 0.028, 0.036), "steel"),
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
             "right": "olive_metal", "top": "olive_metal", "bottom": "hidden"}),
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
            {"front": "label_red", "back": "hidden", "left": "hidden",
             "right": "hidden", "top": "hidden", "bottom": "hidden"}),
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
