#!/usr/bin/env python3
"""Turn a Nano Banana "pixel art" render into true 64x64 pixel art for a Pixoo 64.

    python3 pixoo64.py render.png [--colors 16] [--despeckle]

Writes render_64.png (exactly what the LEDs will show) and render_1024.png
(the same pixels scaled x16 with hard edges -- upload this one).
"""
import argparse
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

GRID, CELL = 64, 16
LIMIT = 5_000_000  # contest limit: 5 MB


def despeckle(img):
    """Replace pixels whose colour none of their 8 neighbours share (stray bits of thin lines)."""
    src, out = img.load(), img.copy()
    dst, n = out.load(), 0
    for y in range(GRID):
        for x in range(GRID):
            around = [src[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if (dx or dy) and 0 <= x + dx < GRID and 0 <= y + dy < GRID]
            if src[x, y] not in around:
                dst[x, y] = Counter(around).most_common(1)[0][0]
                n += 1
    return out, n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--colors", type=int, default=16, help="palette size (default 16)")
    ap.add_argument("--despeckle", action="store_true",
                    help="remove isolated single pixels; skip it if the art has intentional 1-pixel stars or glints")
    args = ap.parse_args()

    src = Path(args.image)
    img = Image.open(src).convert("RGBA")
    img = Image.alpha_composite(Image.new("RGBA", img.size, "black"), img).convert("RGB")
    img = ImageOps.fit(img, (GRID * CELL,) * 2, Image.Resampling.LANCZOS)  # centre-crop to 1:1

    # Octree keeps small accent colours (eyes, nose) that median-cut merges away.
    pal = img.quantize(args.colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)

    # Each LED takes the most common colour of its 16x16 block: this removes the
    # anti-aliasing, noise and uneven "fake pixels" that image models draw.
    small = Image.new("P", (GRID, GRID))
    for y in range(GRID):
        for x in range(GRID):
            block = pal.crop((x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL))
            small.putpixel((x, y), max(block.getcolors())[1])

    # Near-black would leave LEDs faintly glowing; make it truly off.
    palette = pal.getpalette()
    for i in range(0, len(palette), 3):
        if max(palette[i:i + 3]) < 40:
            palette[i:i + 3] = [0, 0, 0]
    small.putpalette(palette)
    small = small.convert("RGB")
    if args.despeckle:
        small, n = despeckle(small)
        print(f"despeckle: replaced {n} isolated pixels")

    big = small.resize((GRID * CELL,) * 2, Image.Resampling.NEAREST)
    for path, im in ((src.with_name(f"{src.stem}_64.png"), small),
                     (src.with_name(f"{src.stem}_1024.png"), big)):
        im.save(path, optimize=True)
        size = path.stat().st_size
        print(f"{path}: {im.width}x{im.height}, {size / 1024:.0f} KB{'' if size < LIMIT else '  !! over 5 MB'}")
    print(f"{len(small.getcolors())} colours used")


if __name__ == "__main__":
    main()
