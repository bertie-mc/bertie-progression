#!/usr/bin/env python3
"""
bertie_progression texture generator — storm_core (16x16), hand-placed pixel art.

A dark grey storm cloud with a bolt driven straight through it. The bolt comes
in over the cloud's right shoulder, kinks once inside the mass, and runs out of
the base to the lower left, so the two shapes read as one object rather than as
a bolt parked in front of a cloud:

    cloud   rows 2..8, scalloped along the top into two crowns with a valley
            between them, sides and base rounded in by a pixel. Shading is by
            each column's depth below its own top edge, so every crown keeps
            its own lit cap and the mass stays lumpy instead of collapsing
            into one grey slab.
    bolt    a 2px stroke, steep above and below, with a flat jog to the right
            at row 6 — the kink is what makes it read as lightning at 16px
            rather than as a bent streak. Where it crosses open air it takes a
            near-black outline, so the item still has a clean silhouette in an
            inventory slot; where it crosses the cloud that same ring becomes
            cold light spilling into the grey, with a fainter second ring
            beyond it. That spill is what sells the bolt as being *inside* the
            cloud rather than painted on top of it.

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
# Cloud greys, by depth below the column's own top edge. Dark, faintly blue.
CLOUD_RAMP = [
    "#7C8794",   # lit cap
    "#606A77",
    "#4B5360",
    "#3C424D",
    "#2F343E",
    "#262B33",
    "#1E222A",   # the base, in its own shadow
]
SEAM = "#22262E"      # billow undersides

CORE = "#FFFFFF"      # the stroke
CORE_EDGE = "#DCE6FF"
SPILL = "#BFD0F5"     # cold light thrown into the cloud
AIR_EDGE = "#0A0C12"  # the stroke's outline, where it crosses open air

# The cloud, as inclusive x spans per row. Two crowns at row 3 with a valley
# between them at x=5..6, then a shoulder sloping away to the lower right. The
# bolt comes down over that shoulder rather than through the valley: put it in
# the valley and it fills the one concave dip in the skyline, and the whole
# thing stops reading as a cloud and starts reading as a hammer head.
CLOUD = {
    2: [(1, 3), (6, 9), (12, 14)],
    3: [(0, 10), (12, 15)],
    4: [(0, 15)],
    5: [(0, 15)],
    6: [(0, 15)],
    7: [(1, 14)],
    8: [(1, 14)],
    9: [(2, 13)],
}

# Billow undersides, as (row, first column, run length). Left empty: the depth
# ramp already darkens each column away from its own cap, and any run long
# enough to see turns into a belt across the cloud and splits it in two.
SEAMS = []

# The bolt path, as inclusive x spans per row: down-left over the shoulder to
# row 6, a flat jog right at row 7, then down-left again and out of the frame.
# The jog is what makes it read as lightning at 16px rather than as a bent
# streak, and it has to kick *against* the drift to register as a kink.
BOLT = {
    0:  (12, 12),
    1:  (11, 12),
    2:  (10, 11),
    3:  (9, 10),
    4:  (9, 10),
    5:  (8, 9),
    6:  (8, 9),
    7:  (8, 11),
    8:  (10, 11),
    9:  (9, 10),
    10: (8, 9),
    11: (7, 8),
    12: (6, 7),
    13: (5, 6),
    14: (4, 5),
    15: (3, 3),
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
    bolt = spans(BOLT)

    # Depth below each column's own top edge, so every crown keeps a lit cap.
    tops = {}
    for (x, y) in cloud:
        tops[x] = min(y, tops.get(x, SIZE))

    grid = {}
    for (x, y) in cloud:
        grid[(x, y)] = hexcol(CLOUD_RAMP[min(y - tops[x], len(CLOUD_RAMP) - 1)])

    for row, x0, run in SEAMS:
        for x in range(x0, x0 + run):
            if (x, row) in cloud:
                grid[(x, row)] = hexcol(SEAM)

    # Inset outline: any cloud pixel with an orthogonal neighbour outside it.
    for (x, y) in cloud:
        if any((x + dx, y + dy) not in cloud for dx, dy in ORTHO):
            grid[(x, y)] = hexcol(OUTLINE)

    ring1 = grow(bolt)
    ring2 = grow(bolt | ring1)

    # Second ring: a faint lift on the grey already there. Inside the cloud
    # only — in open air a second ring would just bloat the bolt.
    for p in ring2 & cloud:
        grid[p] = mix(grid[p], hexcol(SPILL), 0.10)

    # First ring: light spilling into the cloud, a dark edge in open air. Kept
    # well under half — push it further and the spill bleaches a band right
    # through the middle of the cloud and the billows stop reading.
    for p in ring1:
        grid[p] = mix(grid[p], hexcol(SPILL), 0.35) if p in cloud else hexcol(AIR_EDGE)

    # The stroke: white down its leading edge, a hair cooler behind it.
    for y, (x0, x1) in BOLT.items():
        for x in range(x0, x1 + 1):
            grid[(x, y)] = hexcol(CORE if x == x0 else CORE_EDGE)

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
