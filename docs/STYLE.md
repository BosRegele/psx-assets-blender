# Style Bible

Everything in this kit obeys the numbers below. The premium feel of a PSX-era
bundle does not come from detail - there is no room for detail at 64x64. It
comes from every prop looking like it was made for the *same game*.

## Hard constraints

| Rule | Value | Why |
|---|---|---|
| Triangle budget | 120-500 tris per prop | PS1 pushed ~180k tris/sec total |
| Texture size | 256x256, or 256x512 for tall props | ~1mm per texel at prop scale |
| Palette | fixed 32-colour CLUT | see `palette.png` |
| Colour depth | 15-bit, every channel a multiple of 8 | PS1 framebuffer was 5 bits/channel |
| Dither | ordered Bayer 4x4, strength 20 | the single strongest era cue |
| Filtering | `Closest` / point sampling, no mipmaps | bilinear instantly kills the look |
| Shading | flat faces, roughness 1.0, specular 0, metallic 0 | no PBR anywhere |
| Texel density | ~970-1101 px/m, square texels on every prop | non-square texels are the #1 tell of an amateur asset |
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
3. Labels use **real type**, set with a real typeface and rendered one-bit.
   `d.fontmode = "1"` is the whole trick: PIL antialiases TTF by default, and
   those grey edge pixels quantise into mud against a 32-colour CLUT. One-bit
   rendering puts every glyph edge on a texel boundary.

   Two constraints keep it legible on a curved surface:

   - **Cap type at ~28% of the texture width.** A cylinder presents only about
     100 degrees of arc legibly; wider type wraps out of sight and reads as a
     truncated word however crisp the glyphs are.
   - **Size from the box, never a fixed point size** (`texgen.fit`), so a
     density change rescales the type with it.

   Brand names are invented, with numeric suffixes and generic product nouns.
   Real trademarks mean a rejected listing.

4. Noise octaves are **block sizes in pixels**, not a subdivision count. Scale
   them with the texture and keep the coarsest well under a tenth of the width -
   it carries the most amplitude and turns into damp-looking blotches otherwise.

5. Scuffs stay inside their own atlas band (`scratches(..., ybox=...)`). Glass
   flecks bleeding onto a paper label is exactly the sort of detail that reads
   as sloppy at close range.
4. One vertical specular column is what makes unlit glass read as glass.

## Texel density: the rule that matters most

A texel must be square on the model. If it is not, the texture reads as smeared
no matter how good the artwork is - and on a revolved shape like a bottle it is
very easy to get badly wrong. The first version of this kit put 13:1 slivers on
the bottle neck, because the neck wrapped the full 128px width across its 8cm
circumference while getting only 8 texture rows for 6.6cm of height.

The fix is a single contract in `tools/geometry.py`:

- **V advances with arc length** along the profile, so a centimetre of surface
  always gets the same number of rows, whether it is neck or belly.
- **U spans `r / r_max`** of the texture width, so a narrow ring does not smear
  the full width across a small circumference.
- The atlas rectangles are then **computed from the geometry**, not placed by
  hand. `textures.py` paints into whatever rows `geometry.py` derives.

The price is slight shear across the two shoulder rings, where the surface is
genuinely converging. An extra ring there softens it.

Run the audit before shipping anything:

```bash
cd tools && python check_density.py
```

It fails if any face deviates more than 1.15 from square texels, or if the
per-prop densities drift more than 1.15 apart across the bundle. It is what
caught the cigarette pack's side faces being mapped to a square rectangle for
a 23x88mm surface.

## UV atlases

Each texture function in `tools/textures.py` documents its atlas rectangles in
its docstring, and reads the actual numbers from `tools/geometry.py`. Those
rectangles are a **contract** with `tools/blender_build.py`, which writes UVs
explicitly rather than calling smart-unwrap - automatic unwrapping scatters
islands and breaks the shared atlas.

Note: the module is named `geometry.py`, not `profile.py`. Python ships a
stdlib module called `profile`, and Blender had already imported it, so the
shadowing import silently resolved to the wrong module.

## Deliberate non-goals

- **No normal/roughness/metallic maps.** Diffuse only. PBR maps on a 64px
  texture are wasted bytes and break the aesthetic.
- **No LODs.** A 48-triangle can does not need one.
- **No affine texture warping baked in.** The signature PS1 texture wobble is a
  *renderer* effect. Bake it into the asset and it is wrong from every other
  angle. Ship clean UVs and let the buyer's PSX shader do it.
