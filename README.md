# psx-assets-blender

Game-ready PS1-era props for Blender, and the tooling that keeps them looking
like one coherent set.

![hero](docs/hero.png)

Post-soviet grime: canned rations, cheap vodka, state-issue cigarettes. Built
for survival horror and boomer-shooter projects that want the real thing rather
than a low-poly model with a blurry texture stretched over it.

| Prop | Tris | Texture |
|---|---|---|
| `SM_Can_Food_01` | 48 | 64x64 |
| `SM_Bottle_Vodka_01` | 200 | 128x128 |
| `SM_Pack_Cigarettes_01` | 12 | 64x64 |

Exported as `.fbx` (embedded textures) and `.glb`, real-world scale, pivots at
base centre, +Z up.

## What makes it look right

A 64x64 texture is not automatically "PSX". Four things do the work, and all of
them are enforced in code rather than left to taste:

- **A fixed 32-colour CLUT** shared by every prop in the bundle
- **15-bit colour** - every channel a multiple of 8, like the PS1 framebuffer
- **Ordered Bayer dithering** instead of smooth gradients
- **Point sampling** (`Closest`) with no mipmaps

Full rules in [docs/STYLE.md](docs/STYLE.md).

## Regenerating

Textures are procedural; models are built from explicit vertex, face and UV
lists so they hit the texture atlas exactly.

```bash
cd tools
python textures.py          # writes assets/textures/*.png
```

Then, with Blender running and the socket bridge listening on port 9876:

```bash
python -c "import bridge; print(bridge.run(open('blender_build.py').read()))"
```

`bridge.py` talks to a Blender addon exposing `execute_code` on
`127.0.0.1:9876`. Without it, paste `blender_build.py` into Blender's text
editor and run it there - it has no dependency on the bridge.

## Layout

```
tools/palette.py        32-colour CLUT, 15-bit quantise, Bayer dither
tools/texgen.py         noise, grime, scuffs, pseudo-glyph wordmarks
tools/textures.py       the three prop textures + their UV atlas contracts
tools/blender_build.py  meshes, UVs, materials, FBX/GLB export
tools/bridge.py         socket client for the Blender addon
```

## Licence

Code in `tools/` is MIT - take the pipeline and build your own kit.

The models and textures in `assets/` and `exports/` are samples, published for
evaluation and portfolio purposes; all rights reserved. Larger commercial
bundles built with this pipeline are sold separately.
