#!/usr/bin/env python3
"""
bertie_progression texture generator — storm_core (16x16), hand-placed pixel art.

A dark grey storm cloud striking downwards. The bolt starts inside the cloud
and drops out of its underside — nothing sits above the skyline, and nothing
is painted across the cloud's face either. It is one continuous path, but it
is only drawn where it is in open air; the stretch still inside the cloud is
occluded and marked by a glow alone. Paint that stretch on top and it stops
being a bolt in a cloud and becomes a bolt lying in front of one.

    cloud   rows 1..8: a body that swells to the full width, broken into three
            small bumps along the skyline and three deep lobes along the base,
            so neither edge rules a flat line across the sprite. Shaded by
            each column's depth below its own top edge, so the mass stays
            lumpy rather than settling into one grey slab — which does mean
            the base lobes sit at the dark end of the ramp and read as feet
            rather than as billows, the price of keeping the light overhead.
    bolt    a 2px stroke leaning down-left the whole way, never vertical on
            any stretch long enough to notice. It gathers inside the cloud
            (rows 5..8, hidden), drops clear of the middle base lobe at row 9,
            and runs to row 15 — down-left, one row that juts right, down-left
            again to a point. The kink has to be below the cloud: it is the
            only part of the outline that says lightning, and buried in the
            grey there is nothing left to read.
    glow    yellow mixed into the grey along the hidden run, with a halo where
            the bolt breaks out of the underside and nothing else. The run
            gets no falloff rings of its own — give it any and the diagonal
            stops reading as a line and turns into a smudge across the cloud.

The lean matters more than it looks. The hidden run is what carries the eye
down to the glyph, and if it drops straight the bolt reads as a pole hung off
the cloud however diagonal the part below it is.

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

# The cloud, as inclusive x spans per row. This is the three-crown silhouette
# turned through 180 degrees, so the deep lobes now carry the base and the
# small lumps break the skyline. Two lobes over a narrower body reads as a
# bean — it takes the third, and a body wide enough to carry all three,
# before the silhouette is unmistakably a cloud.
#
# Both edges step across two rows rather than ruling one flat line. The bolt
# drops clear from under the middle base lobe.
CLOUD = {
    1: [(2, 4), (8, 9), (11, 13)],
    2: [(2, 14)],
    3: [(1, 15)],
    4: [(0, 15)],
    5: [(0, 15)],
    6: [(0, 15)],
    7: [(0, 3), (5, 15)],
    8: [(1, 3), (6, 9), (12, 14)],
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
    5:  (10, 11),
    6:  (9, 10),
    7:  (8, 9),
    8:  (7, 8),
    9:  (6, 7),
    10: (5, 6),
    11: (4, 5),
    12: (4, 7),
    13: (5, 6),
    14: (4, 5),
    15: (4, 4),
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
    near = grow(visible) & cloud
    far = (grow(visible | near) & cloud) - near
    for p in far:
        grid[p] = mix(grid[p], hexcol(GLOW), 0.10)
    for p in near:
        grid[p] = mix(grid[p], hexcol(GLOW), 0.28)
    # The hidden run itself, and nothing around it. Give this a ring or two of
    # falloff and the diagonal stops reading as a line and becomes a smudge;
    # push the strength much past this and it does the same on its own, since
    # amber into blue-grey lands on brown long before it lands on light.
    for p in hidden:
        grid[p] = mix(grid[p], hexcol(GLOW), 0.22)

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
