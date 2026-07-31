#!/usr/bin/env python3
"""
bertie_progression texture generator — storm_core (16x16), hand-placed pixel art.

A dark grey storm cloud striking downwards. The bolt starts inside the cloud
and drops out of its underside — nothing sits above the skyline, and nothing
is painted across the cloud's face either. It is one continuous path, but it
is only drawn where it is in open air; the stretch still inside the cloud is
occluded and marked by a glow alone. Paint that stretch on top and it stops
being a bolt in a cloud and becomes a bolt lying in front of one.

    cloud   a union of seven circles, rows 0..7: three crowns, two shoulders
            rounding the sides in, and two low ones hanging the base into
            lumps. Only the outer perimeter of that union survives as an
            outline; every arc inside another circle is gone. Spurs where two
            arcs almost meet get pruned, and the skyline takes a lighter
            outline than the sides and base — near-black all the way round
            draws a cut-out, not a cloud. Shaded by each column's depth below
            its own top edge, so the mass stays lumpy.
    bolt    a 2px stroke leaning down-left the whole way, never vertical on
            any stretch long enough to notice. It gathers inside the cloud
            (rows 3..6, hidden), drops through the gap between the two base
            lumps at row 7, and runs to a single-pixel point at row 14 —
            down-left, one row that juts right, down-left again, then the tip.
            The kink has to be below the cloud: it is the only part of the
            outline that says lightning, and buried in the grey there is
            nothing left to read. The point is closed off by two outline
            pixels on row 15, one under the tip and one down-left of it, so it
            tapers along the lean of the stroke instead of ending flat.
    glow    yellow mixed into the grey along the hidden run, plus an aura
            scattering out of it ring by ring — a cloud diffuses what is lit
            inside it rather than holding the light in a line. The falloff has
            to be long and shallow: one strong ring lands as a smudge with a
            hard edge, several faint ones land as light in fog. Brighter and
            tighter where the bolt actually breaks out of the underside, since
            there the light is escaping rather than diffusing.

    pulse   a white charge running the length of the bolt, from its top end
            inside the cloud down and off the tail. Behind the grey it is a
            bloom rather than a stroke, scattering the same way the resting
            glow does but brighter and reaching further. It swells on the last
            row still behind the cloud, then clears the base at its own width
            and full strength and rides the glyph down. Every pulse frame
            holds one tick, the engine minimum and the same for all of them —
            holding the swell longer reads as the pulse slowing to grow, and
            holding the run through the cloud longer than the run below it
            reads as the tail end sprinting.

The lean matters more than it looks. The hidden run is what carries the eye
down to the glyph, and if it drops straight the bolt reads as a pole hung off
the cloud however diagonal the part below it is.

This writes a vertical strip of 16x16 frames plus storm_core.png.mcmeta, which
is how Minecraft animates a sprite. Frame 0 carries no pulse — it is the
fallback for a client with animation off, so it has to stand on its own.

storm_core used to be the fourth of the glass-sphere cores in make_cores.py.
It is generated here instead, and make_cores.py now covers the other three.

Every pixel is placed here — nothing is copied from another mod, so there is
no NOTICE carve-out.

Run:  python texture-work/make_storm_core.py [--ascii]
"""
import json
import os
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEX_ITEM = os.path.join(ROOT, "src", "main", "resources", "assets", "bertie_progression", "textures", "item")

SIZE = 16

OUTLINE = "#0A0C11"
# The skyline takes a lighter outline than the sides and base. Near-black all
# the way round draws the cloud as a hard cut-out; up top, where the light is
# coming from, a softer edge lets the crowns turn instead of stopping. Still
# dark enough to hold a silhouette against a white inventory slot.
OUTLINE_TOP = "#252C38"
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
# Ring-by-ring falloff of that light out through the grey: the aura around the
# hidden run, and the tighter, brighter spot where it breaks out of the base.
GLOW_AURA = (0.13, 0.075, 0.04)
GLOW_BREAK = (0.28, 0.12, 0.05)

# The cloud, as a union of circles — the way you would draw one by hand. Every
# arc that falls inside another circle disappears; only the outer perimeter of
# the union survives, and that perimeter becomes the outline with the interior
# shaded as cloud.
#
# Spacing is the whole game. Circles closer together than roughly twice their
# radius merge with no dip between them and the union comes out a slab — that
# is what went wrong with every earlier attempt at this, hand-drawn or not.
# These sit far enough apart that each crown keeps its own arc.
CLOUD_CIRCLES = (
    (4.0, 3.9, 2.5),     # left crown
    (8.0, 3.1, 2.8),     # centre crown, the tallest
    (12.0, 3.9, 2.5),    # right crown
    (2.6, 5.0, 1.7),     # shoulders, rounding the sides in rather than
    (13.4, 5.0, 1.7),    #   letting them drop straight
    (5.9, 6.1, 1.9),     # base lumps; the bolt drops through the gap
    (10.1, 6.1, 1.9),    #   left between them
)

# The bolt, as inclusive x spans per row. One continuous path top to bottom;
# rows 4..8 land inside the cloud and are never drawn, only glowed. Rows 9..15
# carry the whole glyph clear of the cloud: down-left to row 11, one row that
# juts right at row 12, then down-left again to a point.
#
# That jut is only two columns wider than the stroke on purpose. An earlier
# pass kicked five columns and the two strokes stopped reading as one bolt —
# with that much offset the shape curves and lands as a dollar sign.
BOLT_PATH = {
    3:  (11, 12),
    4:  (10, 11),
    5:  (9, 10),
    6:  (8, 9),
    7:  (7, 8),
    8:  (6, 7),
    9:  (5, 6),
    10: (4, 5),
    11: (4, 7),
    12: (6, 7),
    13: (5, 6),
    14: (5, 5),
}

ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))

# --- animation ---------------------------------------------------------------
#
# A pulse runs the length of the bolt, from its top end inside the cloud down
# and out of the tail. Emitted as a vertical strip of 16x16 frames with a
# storm_core.png.mcmeta beside it, which is how Minecraft animates a sprite.
#
# Frame 0 is the resting sprite with no pulse in it, and it is what a client
# with animation off falls back to, so it has to stand on its own.

PULSE_CORE = "#FFFFFF"    # the head, in open air
PULSE_EDGE = "#FFF6C8"    # its halo, and the first row of tail behind it
PULSE_VEIL = "#FFF0C0"    # what the cloud mixes towards while the pulse is behind it

# Head first, then the two rows of tail trailing it. Each is the colour used
# where that row is in open air, and the mix strength where it is behind the
# cloud. The veiled strengths stay well under the open ones — behind the grey
# the pulse is meant to be a bloom in the cloud, not the stroke showing through.
PULSE_FALLOFF = (
    (PULSE_CORE, 0.62),
    (PULSE_EDGE, 0.40),
    (BOLT_HI,    0.20),
)

# How the pulse's light scatters out through the grey, ring by ring. Brighter
# and reaching further than the resting aura, and further again on the swell.
PULSE_AURA = (0.30, 0.17, 0.09)
PULSE_AURA_BURST = (0.50, 0.30, 0.16, 0.08)

# (pulse, hold in ticks). `pulse` is (phase, head row) or None for the rest
# frame. Phases: "veiled" while the head is still behind the cloud, "burst" for
# the swell, "open" for the run below the cloud.
#
# The burst sits on row 8, the last row still behind the cloud, so the swell
# lands the frame *before* the pulse clears the base rather than the frame
# after. Every pulse frame holds one tick — the minimum, and the same for all
# of them. Holding the swell longer than its neighbours reads as the pulse
# slowing down to grow, and holding the run through the cloud longer than the
# run below it reads as the tail end sprinting.
#
# The heads at rows 16 and 17 are past the end of the bolt on purpose — no head
# is drawn, only the tail behind it, so the pulse runs off the tail rather than
# vanishing on the last row.
FRAMES = [
    (None,             12),
    (("veiled",  3),    1),
    (("veiled",  4),    1),
    (("veiled",  5),    1),
    (("burst",   6),    1),
    (("open",    7),    1),
    (("open",    8),    1),
    (("open",    9),    1),
    (("open",   10),    1),
    (("open",   11),    1),
    (("open",   12),    1),
    (("open",   13),    1),
    (("open",   14),    1),
    (("open",   15),    1),
    (("open",   16),    1),
]


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


def disperse(grid, source, cloud, colour, strengths):
    """Bleed `colour` outward from `source` through the cloud, a ring per entry
    in `strengths`. The source itself is left alone — whatever set it, set it
    for a reason."""
    seen = set(source)
    front = set(source)
    for t in strengths:
        front = (grow(front) & cloud) - seen
        if not front:
            return
        seen |= front
        for p in front:
            grid[p] = mix(grid[p], hexcol(colour), t)


def circle_union(circles):
    return {(x, y) for y in range(SIZE) for x in range(SIZE)
            if any((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r
                   for cx, cy, r in circles)}


def declutter(pixels):
    """Drop anything hanging off the union by a single orthogonal neighbour.
    Where two arcs almost meet they leave one-pixel spurs, and at 16px those
    read as grit on the outline rather than as cloud."""
    px = set(pixels)
    while True:
        spurs = {p for p in px
                 if sum((p[0] + dx, p[1] + dy) in px for dx, dy in ORTHO) <= 1}
        if not spurs:
            return px
        px -= spurs


def tip_edge():
    """The outline pixel down-left of the bolt's point. The ring pass only
    reaches orthogonally, so without this the point closes off flat underneath
    and the taper stops reading as a taper."""
    row = max(BOLT_PATH)
    return {(BOLT_PATH[row][0] - 1, row + 1)}


def spans(table):
    out = set()
    for y, rows in table.items():
        for x0, x1 in (rows if isinstance(rows, list) else [rows]):
            out.update((x, y) for x in range(x0, x1 + 1))
    return out


def bolt_row(row):
    """The stroke pixels on one row, empty past either end of the path."""
    if row not in BOLT_PATH:
        return set()
    x0, x1 = BOLT_PATH[row]
    return {(x, row) for x in range(x0, x1 + 1)}


def paint(pulse=None):
    cloud = declutter(circle_union(CLOUD_CIRCLES))
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

    # Inset outline: any cloud pixel with an orthogonal neighbour outside it,
    # lighter along the skyline than round the sides and base.
    for (x, y) in cloud:
        open_sides = [(dx, dy) for dx, dy in ORTHO if (x + dx, y + dy) not in cloud]
        if open_sides:
            skyline = open_sides == [(0, -1)]
            grid[(x, y)] = hexcol(OUTLINE_TOP if skyline else OUTLINE)

    # Light coming through the cloud. Applied after the outline, so the edge
    # warms too where the bolt crosses it.
    for p in hidden:
        grid[p] = mix(grid[p], hexcol(GLOW), 0.22)
    # A cloud does not hold light in a line — it scatters it — so the hidden
    # run carries an aura out into the grey around it. This wants a long
    # shallow falloff and nothing steeper: one strong ring lands as a smudge
    # with a hard edge, several faint ones land as light in fog. Amber into
    # blue-grey reaches brown well before it reaches light, so the outer rings
    # have to stay very low or the whole cloud goes dirty.
    disperse(grid, hidden, cloud, GLOW, GLOW_AURA)
    # Where the bolt actually leaves the cloud the light is escaping rather
    # than diffusing, so that spot runs brighter and tighter than the aura.
    disperse(grid, visible, cloud, GLOW, GLOW_BREAK)

    # The stroke, only where it is in open air, with its own outline. The
    # outline stops at the cloud: run it over the grey and the bolt would
    # look cut out of the cloud instead of passing behind it.
    for p in (grow(visible) | tip_edge()) - cloud - bolt:
        if 0 <= p[0] < SIZE and 0 <= p[1] < SIZE:
            grid[p] = hexcol(AIR_EDGE)
    for y, (x0, x1) in BOLT_PATH.items():
        for x in range(x0, x1 + 1):
            if (x, y) in visible:
                grid[(x, y)] = hexcol(BOLT_HI if x == x0 else BOLT)

    if pulse is not None:
        phase, head = pulse

        # Head and the two rows of tail behind it. Behind the cloud this only
        # lifts the grey; in open air it replaces the stroke outright.
        veiled = set()
        for i, (air, veil) in enumerate(PULSE_FALLOFF):
            row = bolt_row(head - i)
            for p in row & visible:
                grid[p] = hexcol(air)
            for p in row & cloud:
                grid[p] = mix(grid[p], hexcol(PULSE_VEIL), veil)
            veiled |= row & cloud

        crown = bolt_row(head)
        lit = crown & visible

        # The swell happens on the last row still behind the cloud, so on that
        # frame it has to read as a bloom widening in the grey — there is no
        # open air up there to put a halo in.
        if phase == "burst" and not lit:
            for p in crown & cloud:
                grid[p] = mix(grid[p], hexcol(PULSE_VEIL), 0.62)

        # The pulse's own light scattering out through the cloud, same idea as
        # the resting aura but brighter and reaching further, and further again
        # on the swell. Without this the pulse is two lit pixels behind an
        # opaque cloud, which is not how a cloud lit from inside looks.
        disperse(grid, veiled, cloud, PULSE_VEIL,
                 PULSE_AURA_BURST if phase == "burst" else PULSE_AURA)

        if lit:
            ring = grow(lit) - bolt - cloud
            if phase == "burst":
                for p in grow(lit | ring) - bolt - cloud - ring:
                    grid[p] = hexcol(PULSE_EDGE)
                for p in ring:
                    grid[p] = hexcol(PULSE_CORE)
            else:
                for p in ring:
                    grid[p] = hexcol(PULSE_EDGE)

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


def build_strip():
    """The frames stacked top to bottom, which is the layout Minecraft wants."""
    frames = [paint(spec) for spec, _ in FRAMES]
    strip = Image.new("RGBA", (SIZE, SIZE * len(frames)), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        strip.paste(frame, (0, i * SIZE))
    return strip, frames


def build_mcmeta():
    return {
        "animation": {
            "frametime": 1,
            "frames": [{"index": i, "time": hold}
                       for i, (_, hold) in enumerate(FRAMES)],
        }
    }


if __name__ == "__main__":
    os.makedirs(TEX_ITEM, exist_ok=True)
    strip, frames = build_strip()
    strip.save(os.path.join(TEX_ITEM, "storm_core.png"))
    with open(os.path.join(TEX_ITEM, "storm_core.png.mcmeta"), "w", newline="\n") as fh:
        json.dump(build_mcmeta(), fh, indent=2)
        fh.write("\n")
    print("wrote storm_core.png (%d frames) and storm_core.png.mcmeta" % len(frames))
    if "--ascii" in sys.argv:
        dump(frames[0])
