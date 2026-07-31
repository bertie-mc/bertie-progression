#!/usr/bin/env python3
"""
bertie_progression texture generator — storm_core (16x16), hand-placed pixel art.

A dark grey storm cloud with a yellow bolt passing through it. The bolt is one
continuous path from the top of the sprite to the bottom, but it is only drawn
where it is in open air — the cloud occludes the middle of it. That is the
whole trick: paint the stroke across the cloud's face and it reads as a bolt
lying in front of a cloud, so instead the cloud swallows it and only a warm
glow marks where it is running behind:

    cloud   rows 1..8: two crowns, each two rows tall, over a body that rounds
            in at the sides and the base. Shaded by each column's depth below
            its own top edge, so every crown keeps a lit cap and the mass stays
            lumpy rather than settling into one grey slab.
    bolt    a 2px stroke. The tip clears the skyline through the valley between
            the crowns (rows 0..2), running down-left a column per row — a tip
            dropped straight down is a pole standing on the cloud, not a bolt,
            and the valley is cut wide enough to let the diagonal through. The
            middle is hidden behind the cloud (rows 3..8), and the whole glyph
            — down-left, one row that juts right, down-left again to a point —
            hangs clear of the base in rows 9..15 where nothing covers it. The
            kink has to be below the cloud: it is the only part of the outline
            that says lightning, and buried in the grey there is nothing left
            to read.
    glow    yellow mixed into the grey the hidden run passes through, plus one
            faint ring. Strongest where the bolt enters and leaves the cloud
            and falling away with depth, so it reads as light at the two holes
            it went through rather than as an even channel from skyline to
            base — that channel is a seam, and it splits the cloud in two
            however faint it is.

Tip and glyph share the same columns on purpose. Entering at a corner instead
frees up the whole skyline for the cloud, but then the two yellow pieces sit
too far apart to read as one bolt and it just looks like a cloud next to a
lightning bolt.

storm_core used to be the fourth of the glass-sphere cores in make_cores.py.
It is generated here instead, and make_cores.py now covers the other three.

Every pixel is placed here — nothing is copied from another mod, so there is
no NOTICE carve-out.

Run:  python texture-work/make_storm_core.py [--ascii]
"""
import os
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEX_ITEM = os.path.join(ROOT, "src", "main", "resources", "assets", "bertie_progression", "textures", "item")

SIZE = 16

OUTLINE = "#0A0C11"
# Cloud greys, by depth below the column's own top edge. Dark, faintly blue so
# they stay cold against the yellow.
CLOUD_RAMP = [
    "#7C8794",   # lit cap
    "#606A77",
    "#4B5360",
    "#3C424D",
    "#2F343E",
    "#262B33",
    "#1E222A",   # the base, in its own shadow
]

BOLT_HI = "#FFE870"   # leading edge of the stroke
BOLT = "#FFB800"      # the stroke
AIR_EDGE = "#2E1D04"  # its outline, which only exists in open air
# What the cloud mixes towards where the bolt runs behind it. Deliberately a
# mid amber and not a pale one: a bright glow sits at a much higher luminance
# than the surrounding grey, and the band of it splits the cloud into two dark
# lobes with a light waist. This warms the grey without lifting it.
GLOW = "#C89020"

# The cloud, as inclusive x spans per row. Two crowns, each two rows tall so
# they read as lobes rather than one-pixel bumps, with a valley between them
# that the tip of the bolt clears the skyline through. The valley is five
# columns at row 1 and three at row 2 — it has to be wider than the stroke,
# because the tip crosses it on a diagonal and a narrower gap would clip it.
# The sides taper in above and below the widest rows so the body is not a
# full-width bar.
CLOUD = {
    1: [(2, 5), (11, 13)],
    2: [(1, 6), (10, 14)],
    3: [(1, 14)],
    4: [(1, 14)],
    5: [(1, 14)],
    6: [(1, 13)],
    7: [(2, 12)],
    8: [(4, 11)],
}

# The bolt, as inclusive x spans per row. One continuous path top to bottom;
# rows 4..8 land inside the cloud and are never drawn, only glowed. Rows 9..15
# carry the whole glyph clear of the cloud: down-left to row 11, one row that
# juts right at row 12, then down-left again to a point.
#
# That jut is only two columns wider than the stroke on purpose. An earlier
# pass kicked five columns and the two strokes stopped reading as one bolt —
# with that much offset the shape curves and lands as a dollar sign.
BOLT_PATH = {
    0:  (10, 11),
    1:  (9, 10),
    2:  (8, 9),
    3:  (8, 9),
    4:  (8, 9),
    5:  (8, 9),
    6:  (8, 9),
    7:  (8, 9),
    8:  (8, 9),
    9:  (8, 9),
    10: (7, 8),
    11: (6, 7),
    12: (6, 9),
    13: (7, 8),
    14: (6, 7),
    15: (6, 6),
}

ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))


def hexcol(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def mix(a, b, t):
    """Blend colour `a` a fraction `t` of the way towards `b`."""
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


def grow(pixels):
    """The orthogonal neighbourhood of a set of pixels, inside the sprite."""
    out = set()
    for (x, y) in pixels:
        for dx, dy in ORTHO:
            p = (x + dx, y + dy)
            if 0 <= p[0] < SIZE and 0 <= p[1] < SIZE:
                out.add(p)
    return out - set(pixels)


def spans(table):
    out = set()
    for y, rows in table.items():
        for x0, x1 in (rows if isinstance(rows, list) else [rows]):
            out.update((x, y) for x in range(x0, x1 + 1))
    return out


def paint():
    cloud = spans(CLOUD)
    bolt = spans(BOLT_PATH)
    visible = bolt - cloud   # in open air: drawn
    hidden = bolt & cloud    # behind the cloud: glow only

    # Depth below each column's own top edge, so every crown keeps a lit cap.
    tops = {}
    for (x, y) in cloud:
        tops[x] = min(y, tops.get(x, SIZE))

    grid = {}
    for (x, y) in cloud:
        grid[(x, y)] = hexcol(CLOUD_RAMP[min(y - tops[x], len(CLOUD_RAMP) - 1)])

    # Inset outline: any cloud pixel with an orthogonal neighbour outside it.
    for (x, y) in cloud:
        if any((x + dx, y + dy) not in cloud for dx, dy in ORTHO):
            grid[(x, y)] = hexcol(OUTLINE)

    # Light coming through the cloud. Applied after the outline, so the edge
    # warms too where the bolt crosses it.
    # Strongest where the bolt enters and leaves the cloud, falling away with
    # depth. A flat strength down the whole hidden run lifts an even channel of
    # grey from the skyline to the base, and that seam cuts the cloud into two
    # lobes however faint it is — the falloff is what keeps it one mass.
    lit_rows = sorted({y for (x, y) in visible})
    ring1 = (grow(bolt) & cloud) - bolt
    for p in ring1:
        grid[p] = mix(grid[p], hexcol(GLOW), 0.06)
    for (x, y) in hidden:
        depth = max(1, min(abs(y - ly) for ly in lit_rows))
        grid[(x, y)] = mix(grid[(x, y)], hexcol(GLOW), (0.34, 0.20, 0.09)[min(depth - 1, 2)])

    # The stroke, only where it is in open air, with its own outline. The
    # outline stops at the cloud: run it over the grey and the bolt would
    # look cut out of the cloud instead of passing behind it.
    for p in grow(visible) - cloud - bolt:
        grid[p] = hexcol(AIR_EDGE)
    for y, (x0, x1) in BOLT_PATH.items():
        for x in range(x0, x1 + 1):
            if (x, y) in visible:
                grid[(x, y)] = hexcol(BOLT_HI if x == x0 else BOLT)

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for (x, y), col in grid.items():
        px[x, y] = col
    return img


def dump(img):
    """Rough ASCII of the sprite, for checking the silhouette by eye."""
    px = img.load()
    for y in range(SIZE):
        row = ""
        for x in range(SIZE):
            r, g, b, a = px[x, y]
            lum = (r + g + b) / 3
            row += "." if a == 0 else " #+=-o*"[min(int(lum / 255 * 6) + 1, 6)]
        print(row)


if __name__ == "__main__":
    os.makedirs(TEX_ITEM, exist_ok=True)
    image = paint()
    image.save(os.path.join(TEX_ITEM, "storm_core.png"))
    print("wrote storm_core.png")
    if "--ascii" in sys.argv:
        dump(image)
