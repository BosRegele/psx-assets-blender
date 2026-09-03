# Style Bible

Everything in this kit obeys the numbers below. The premium feel of a PSX-era
bundle does not come from detail - there is no room for detail at 64x64. It
comes from every prop looking like it was made for the *same game*.

## Hard constraints

| Rule | Value | Why |
|---|---|---|
| Triangle budget | 120-500 tris per prop | PS1 pushed ~180k tris/sec total |
| Texture size | 64x64 small props, 128x128 hero props | matches 1MB VRAM budgets |
| Palette | fixed 32-colour CLUT | see `palette.png` |
| Colour depth | 15-bit, every channel a multiple of 8 | PS1 framebuffer was 5 bits/channel |
| Dither | ordered Bayer 4x4, strength 20 | the single strongest era cue |
| Filtering | `Closest` / point sampling, no mipmaps | bilinear instantly kills the look |
| Shading | flat faces, roughness 1.0, specular 0, metallic 0 | no PBR anywhere |
| Texel density | 64 px/m, uniform across the bundle | mismatched density is the #1 tell of an asset flip |
| Scale | real-world metres | can 102mm, bottle 300mm, pack 88mm |
| Pivot | base centre, +Z up | drops onto a floor without fixup |

## Naming

```
SM_<Category>_<Name>_<##>      mesh      SM_Bottle_Vodka_01
MI_SM_<Category>_<Name>_<##>   material  MI_SM_Bottle_Vodka_01
<name>_d.png                   diffuse   bottle_d.png
```

## Palette

32 colours in eight material ramps: `void`, `tin`, `rust`, `olive`, `paper`,
`red`, `glass`, `concrete`. Ramps run dark to light and are indexed by
`palette.ramp(name)`. Nothing in a texture may use a colour outside the CLUT -
`palette.quantise()` enforces this, and the module asserts 15-bit safety at
import time.

![palette](palette.png)

## Texture authoring rules

1. Author at full colour depth, quantise **last**. Hand-picking CLUT indices
   produces flat, lifeless texels.
2. Grime is not optional. Every surface gets an fbm multiply pass. Clean
   surfaces read as "untextured", not as "new".
3. Text is drawn as blocky glyph rectangles, never a real typeface. At 64px a
   font turns to mush; varied glyph widths with genuine word gaps read as
   language at play distance. It also keeps every label trademark-free.
4. One vertical specular column is what makes unlit glass read as glass.

## UV atlases

Each texture function in `tools/textures.py` documents its atlas rectangles in
its docstring. Those rectangles are a **contract** with `tools/blender_build.py`,
which writes UVs explicitly rather than calling smart-unwrap. Change one, change
both - automatic unwrapping scatters islands and breaks the shared atlas.

## Deliberate non-goals

- **No normal/roughness/metallic maps.** Diffuse only. PBR maps on a 64px
  texture are wasted bytes and break the aesthetic.
- **No LODs.** A 48-triangle can does not need one.
- **No affine texture warping baked in.** The signature PS1 texture wobble is a
  *renderer* effect. Bake it into the asset and it is wrong from every other
  angle. Ship clean UVs and let the buyer's PSX shader do it.
