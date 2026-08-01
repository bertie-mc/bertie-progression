#!/usr/bin/env python3
"""
bertie_progression texture generator — storm_core (16x16), hand-placed pixel art.

A dark grey storm cloud striking downwards. The bolt starts inside the cloud
and drops out of its underside — nothing sits above the skyline, and nothing
is painted across the cloud's face either. It is one continuous path, but it
is only drawn where it is in open air; the stretch still inside the cloud is
occluded and marked by a glow alone. Paint that stretch on top and it stops
being a bolt in a cloud and becomes a bolt lying in front of one.

    cloud   rows 0..7, two crowns over a body on a flat base, after berlord's
            reference. Not shaded as a gradient: a flat mid-grey fill, compact
            lighter blocks scattered through the upper body, and a darker band
            along the underside. A per-column ramp reads as a shaded ball, and
            single-row highlights read as stripes; it takes two-row blocks,
            one under each crown and each shoulder, before the mass breaks up
            into puffs. The edge is one colour all the way round and only a
            couple of steps darker than the fill — a near-black ring turns the
            whole thing into a cut-out.
    bolt    a 2px stroke leaning down-left the whole way, never vertical on
            any stretch long enough to notice. It gathers inside the cloud
            (rows 3..7, hidden), drops clear of the flat base at row 8 just
            left of centre, and runs to a single-pixel point at row 14 —
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
    rain    streaks blown down-left on the bolt's own lean, blue-grey so they
            do not read as cloud breaking off, with a brighter pixel at the
            leading end. Each is a staircase rather than a true 45 line: a
            diagonal that only touches at the corners reads as a row of
            separate dots at this size. They share a slope and vary in length
            instead — three or four pixels is not enough line for an angle to
            survive being different from its neighbours, so the gusting has to
            come from somewhere that reads, and length does.

            Seeds are tiled along the wind so the field stays full as streaks
            blow off the bottom left, which means each one lands two or three
            times over. Three seeds is the ceiling before the copies start
            running into each other and clumping.

            The rain is also why nothing can be held any more: a long rest
            frame freezes it mid-air, so the gap between strikes is ten
            one-tick frames of rain instead. The frame count has to stay a
            whole number of rain cycles or the loop jumps at the wrap — there
            is an assert on that.

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

# Cloud greys. Not a smooth ramp: a flat mid fill, irregular lighter clusters
# scattered through the upper body, and a darker band along the underside. A
# per-column gradient reads as a shaded ball; the clusters are what make it
# read as cloud.
CLOUD_FILL = "#4E555F"
CLOUD_LIGHT = "#79828E"
CLOUD_DARK = "#383D45"    # the underside, in its own shadow
CLOUD_EDGE = "#22262D"    # darker than the fill, well short of black

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
GLOW_AURA = (0.09, 0.05, 0.025)
GLOW_BREAK = (0.22, 0.10, 0.04)

# The cloud, as inclusive x spans per row: a stepped dome on a flat base,
# after berlord's reference. Circle unions were tried and abandoned — at this
# size circles either merge into a slab or leave spurs and holes, and neither
# gives the clean stepped skyline the reference has.
CLOUD = {
    0: [(4, 6), (9, 11)],
    1: [(3, 7), (9, 12)],
    2: [(2, 13)],
    3: [(1, 14)],
    4: [(0, 14)],
    5: [(0, 14)],
    6: [(1, 14)],
    7: [(2, 13)],
}

# Rows from here down take the dark underside colour.
CLOUD_UNDERSIDE = 6

# The lighter clusters, as (row, first column, run). Deliberately irregular in
# size and placement — evenly spaced ones read as a pattern, not as cloud.
# Compact blocks, two rows each, not single-row runs — a run reads as a stripe
# across the cloud, a block reads as a puff turning towards the light.
CLOUD_LIGHTS = (
    (1, 4, 3), (2, 4, 2),      # left crown
    (1, 10, 2), (2, 10, 2),    # right crown
    (3, 2, 2), (4, 2, 2),      # left shoulder
    (3, 7, 2), (4, 7, 2),      # centre
    (3, 11, 2), (4, 12, 2),    # right shoulder
    (5, 4, 2),                 # one last catch, low on the body
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

# --- rain ---------------------------------------------------------------------
#
# Streaks blown down-left out of the cloud's base, on the same lean as the
# bolt. Blue-grey rather than any of the cloud's own greys, so they do not read
# as bits of cloud breaking off.
RAIN = "#7E97B2"
RAIN_TAIL = "#5B6E85"    # trailing pixels, so a streak reads as having a head
RAIN_TOP = 8             # first row below the cloud
RAIN_PERIOD = 4          # the wind carries a streak this far before repeating
RAIN_TICKS_PER_ROW = 2   # frames a streak spends on each step

# Streak shapes, listed tail first so the last offset is the leading end. Each
# is a staircase down-left, alternating a step down and a step left, because a
# true 45 line only touches at the corners and at this size reads as a row of
# separate dots rather than as a streak.
#
# They all share that slope. Mixing slopes was tried first and the streaks
# stopped reading as lines at all — three or four pixels is not enough line for
# an angle to survive being different from its neighbours. The gusting comes
# from length instead, which does read at this size.
RAIN_SHAPES = {
    "gust":  ((2, -2), (1, -2), (1, -1), (0, -1), (0, 0)),
    "long":  ((1, -2), (1, -1), (0, -1), (0, 0)),
    "short": ((1, -1), (0, -1), (0, 0)),
}

# Leading ends, tiled along the wind by (-RAIN_PERIOD, +RAIN_PERIOD) so the
# field stays full as streaks blow off the bottom left. Scattered by hand — an
# even lattice reads as hatching rather than as weather.
# Three is enough. Each one tiles into two or three copies, so five seeds put
# roughly thirty pixels of rain into the frame and the copies started running
# into each other and clumping.
RAIN_STREAKS = (
    (11, 12, "gust"),
    (2, 12, "long"),
    (14, 15, "short"),
)

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
REST_FRAMES = 10
PULSE_FRAMES = [
    ("veiled",  3), ("veiled",  4), ("veiled",  5), ("veiled",  6),
    ("burst",   7),
    ("open",    8), ("open",    9), ("open",   10), ("open",   11),
    ("open",   12), ("open",   13), ("open",   14), ("open",   15),
    ("open",   16),
]
FRAMES = [None] * REST_FRAMES + PULSE_FRAMES

# Every frame runs one tick. Nothing can be held any more: the rain falls the
# whole time, and a held frame freezes it mid-air. So the gap between strikes
# is ten frames of rain with no pulse in them rather than one long frame.
#
# The frame count has to be a whole number of rain cycles or the loop jumps
# where it wraps.
assert len(FRAMES) % (RAIN_PERIOD * RAIN_TICKS_PER_ROW) == 0, (
    "frame count %d is not a whole number of %d-frame rain cycles"
    % (len(FRAMES), RAIN_PERIOD * RAIN_TICKS_PER_ROW))


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


def rain_pixels(frame):
    """Rain for one frame, as {pixel: is_head}. The wind carries each streak
    one step down-left every RAIN_TICKS_PER_ROW frames; because the seeds are
    tiled by exactly the distance travelled in RAIN_PERIOD steps, the field is
    identical again after that and the loop closes."""
    blown = (frame // RAIN_TICKS_PER_ROW) % RAIN_PERIOD
    out = {}
    for sx, sy, shape in RAIN_STREAKS:
        for k in range(-3, 4):
            hx = sx - blown - k * RAIN_PERIOD
            hy = sy + blown + k * RAIN_PERIOD
            shape_px = RAIN_SHAPES[shape]
            for i, (dx, dy) in enumerate(shape_px):
                p = (hx + dx, hy + dy)
                if 0 <= p[0] < SIZE and RAIN_TOP <= p[1] < SIZE:
                    out[p] = i == len(shape_px) - 1
    return out


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


def paint(pulse=None, frame=0):
    cloud = spans(CLOUD)
    bolt = spans(BOLT_PATH)
    visible = bolt - cloud   # in open air: drawn
    hidden = bolt & cloud    # behind the cloud: glow only

    grid = {p: hexcol(CLOUD_FILL) for p in cloud}

    for row, x0, run in CLOUD_LIGHTS:
        for x in range(x0, x0 + run):
            if (x, row) in cloud and row < CLOUD_UNDERSIDE:
                grid[(x, row)] = hexcol(CLOUD_LIGHT)

    for (x, y) in cloud:
        if y >= CLOUD_UNDERSIDE:
            grid[(x, y)] = hexcol(CLOUD_DARK)

    # Inset edge: any cloud pixel with an orthogonal neighbour outside it. One
    # colour all the way round, and only a step or two darker than the fill —
    # a near-black ring turns the whole thing into a cut-out.
    for (x, y) in cloud:
        if any((x + dx, y + dy) not in cloud for dx, dy in ORTHO):
            grid[(x, y)] = hexcol(CLOUD_EDGE)

    # Light coming through the cloud. Applied after the outline, so the edge
    # warms too where the bolt crosses it.
    for p in hidden:
        grid[p] = mix(grid[p], hexcol(GLOW), 0.16)
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

    # Rain goes down before the bolt does, so the bolt and its outline win
    # anywhere the two would land on the same pixel — a streak crossing behind
    # the stroke is fine, one drawn over it is not.
    for p, head in rain_pixels(frame).items():
        if p not in cloud:
            grid[p] = hexcol(RAIN if head else RAIN_TAIL)

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
    frames = [paint(spec, i) for i, spec in enumerate(FRAMES)]
    strip = Image.new("RGBA", (SIZE, SIZE * len(frames)), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        strip.paste(frame, (0, i * SIZE))
    return strip, frames


def build_mcmeta():
    # Every frame is one tick, so the frame list can be left implicit.
    return {"animation": {"frametime": 1}}


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
