"""Render one framed screenshot per prop, then assemble a labelled contact sheet.

Runs on the host and drives Blender through the bridge, one prop at a time.
The sheet doubles as the repo's marketing image and as the thing to actually
look at when judging whether a prop reads.
"""
import os, sys
from PIL import Image, ImageDraw
import bridge, props

SHOTS = os.path.join(os.path.dirname(__file__), "..", "renders", "props")
DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")

FRAME = '''
import bpy
ob = bpy.data.objects["{name}"]
ob.location = (0, 0, 0)
for o in bpy.data.objects:
    o.hide_viewport = (o is not ob)
bpy.ops.object.select_all(action="DESELECT")
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
for a in bpy.context.window.screen.areas:
    if a.type == "VIEW_3D":
        r = [r for r in a.regions if r.type == "WINDOW"][0]
        with bpy.context.temp_override(area=a, region=r):
            bpy.ops.view3d.view_axis(type="FRONT")
            bpy.ops.view3d.view_orbit(angle=0.36, type="ORBITUP")
            bpy.ops.view3d.view_orbit(angle=0.42, type="ORBITLEFT")
            bpy.ops.view3d.view_selected()
        break
'''


def capture(names=None, size=520):
    os.makedirs(SHOTS, exist_ok=True)
    names = names or list(props.REGISTRY)
    for n in names:
        bridge.run(FRAME.format(name=n))
        bridge.send("get_viewport_screenshot",
                    {"max_size": size,
                     "filepath": os.path.abspath(os.path.join(SHOTS, f"{n}.png"))
                        .replace("\\", "/")})
    return names


def sheet(names, cols=6, cell=300, path=None):
    """Grid the shots, cropped to their content so small props are not lost in
    a sea of background."""
    pad, label = 8, 22
    rows = (len(names) + cols - 1) // cols
    W = cols * (cell + pad) + pad
    H = rows * (cell + label + pad) + pad
    out = Image.new("RGB", (W, H), (26, 26, 30))
    d = ImageDraw.Draw(out)
    for i, n in enumerate(names):
        p = os.path.join(SHOTS, f"{n}.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        bg = im.getpixel((2, 2))
        # trim the flat viewport background so every prop fills its cell
        mask = im.point(lambda v: 255)
        diff = Image.new("L", im.size, 0)
        px, dp = im.load(), diff.load()
        for y in range(0, im.height, 2):
            for x in range(0, im.width, 2):
                c = px[x, y]
                if abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2]) > 18:
                    dp[x, y] = 255
        box = diff.getbbox()
        if box:
            box = (max(0, box[0] - 6), max(0, box[1] - 6),
                   min(im.width, box[2] + 8), min(im.height, box[3] + 8))
            im = im.crop(box)
        im.thumbnail((cell, cell), Image.LANCZOS)
        cx = pad + (i % cols) * (cell + pad)
        cy = pad + (i // cols) * (cell + label + pad)
        d.rectangle([cx, cy, cx + cell, cy + cell], fill=(20, 20, 24))
        out.paste(im, (cx + (cell - im.width) // 2, cy + (cell - im.height) // 2))
        d.text((cx + 4, cy + cell + 5), n.replace("SM_", "").replace("_01", ""),
               fill=(150, 150, 160))
    path = path or os.path.join(DOCS, "bunker-set.png")
    out.save(path)
    return path, out.size


if __name__ == "__main__":
    names = capture()
    print(sheet(names))
