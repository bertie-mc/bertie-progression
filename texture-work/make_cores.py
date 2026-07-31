#!/usr/bin/env python3
"""
bertie_s1 texture generator — the four elemental cores (16x16), hand-placed.

The cores are the four 7x7 mechanical-crafter walls that feed the Hephaestus
Forge tier 2 ritual, one per Cataclysm boss domain. Each one is a glass sphere
holding a single primary essence, and they are meant to read as a set at
inventory size, so the glass is identical on all four and only what is trapped
inside changes:

    glass   a 14px sphere: a dark tinted silhouette ring, a shell ring that
            catches the light at the upper left and rim-lights at the lower
            right, and a three-pixel specular glint painted last, over the
            contents, because it sits on the front of the sphere
    essence the domain, filling the sphere on the same four depth bands:
              abyssal  seawater, a current running through it, bubbles, coral,
                       and the pearl that settled out of it
              desert   sand, wind ripples across the grain, gold and pebbles
              cursed   a skull with lit sockets, adrift in green miasma
              storm    a branching bolt, sparks scattered around the arc

Each essence carries a few off-palette flecks — coral in the water, gold in the
sand, crimson in the miasma, warm sparks in the storm — so a 10px interior
still looks alive instead of like a flat tinted fill.

No third-party art is copied; Cataclysm, Deepwaters, Malum and Slag ingredient
items were looked at for each domain's palette only. Nothing here needs a
NOTICE carve-out.

Run:  python texture-work/make_cores.py
"""
import os

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEX_ITEM = os.path.join(ROOT, "src", "main", "resources", "assets", "bertie_s1", "textures", "item")

SIZE = 16
C = 8.0          # sphere centre, in pixel-corner coordinates
R_OUT = 7.0      # silhouette          -> 14px sphere
R_GLASS = 6.0    # inside the outline  -> 1px silhouette ring
R_IN = 5.0       # the essence         -> 1px shell ring, 10px interior

# Light from the upper left, as a unit vector in screen space.
LIGHT = (-0.6, -0.8)

# The glint on the front of the sphere. Painted after the essence.
SPECULAR = [(4, 4), (5, 4), (4, 5)]


def hexcol(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def disc(radius):
    """Pixels whose centre falls inside a circle of `radius` about C."""
    return {(x, y) for y in range(SIZE) for x in range(SIZE)
            if (x + 0.5 - C) ** 2 + (y + 0.5 - C) ** 2 <= radius * radius}


OUT = disc(R_OUT)
GLASS = disc(R_GLASS)
IN = disc(R_IN)
RING_EDGE = OUT - GLASS
RING_SHELL = GLASS - IN


def facing(x, y):
    """How squarely a pixel faces the light: +1 upper left, -1 lower right."""
    return ((x + 0.5 - C) * LIGHT[0] + (y + 0.5 - C) * LIGHT[1]) / R_OUT


# Per-core palettes. `edge`/`mid`/`hi`/`rim` are the glass itself; 0..3 is the
# essence ramp, darkest to brightest; the rest are that essence's own details.
CORES = {
    "abyssal_core": {
        "edge": "#08222F", "mid": "#1B5570", "hi": "#B4EEF8", "rim": "#3E9CB8",
        "0": "#063049", "1": "#0A5578", "2": "#147EA6", "3": "#2FA8CC",
        "F": "#DFF8FF",   # caustic flare where the light enters
        "b": "#EAFDFF",   # bubbles
        "P": "#12202E",   # black pearl settled at the bottom
        "c": "#E8705A",   # coral grit
    },
    "desert_core": {
        "edge": "#3E2810", "mid": "#8A6428", "hi": "#FFEEC4", "rim": "#D9A040",
        "0": "#5C3410", "1": "#8A5418", "2": "#B47620", "3": "#E0A030",
        "4": "#F5CF74",   # grains catching the light
        "g": "#FFF8D8",   # gold glinting in the sand
    },
    "cursed_core": {
        "edge": "#071B14", "mid": "#14513A", "hi": "#A8F7C6", "rim": "#2E9A64",
        "0": "#062218", "1": "#0C4128", "2": "#146B3E", "3": "#2FA55E",
        "B": "#E6DEC0", "H": "#FFFAE4", "D": "#A89B78",   # bone, lit and shaded
        "E": "#05130C",   # eye socket
        "G": "#5CFF9E",   # what is looking out of it
        "N": "#06170E",   # nose and mouth
        "m": "#A6FFB8",   # motes drifting in the miasma
        "v": "#C1264A",   # cursed flesh
    },
    "storm_core": {
        "edge": "#120E36", "mid": "#332C8A", "hi": "#D2D6FF", "rim": "#5A5ED8",
        "0": "#14103C", "1": "#241D68", "2": "#3C36A8", "3": "#8E92F0",
        "W": "#FFFFFF",   # the arc
        "s": "#FFFAC8",   # sparks thrown off it
    },
}

# The essence, as (row, first column, run) over the 10px interior. Painted in
# order, so the flecks at the end of each list land on top of the fill.
ESSENCE = {
    # Seawater filling most of the sphere, foam line near the top.
    "abyssal_core": [
        # Water fills the whole sphere. An air gap and a foam line read as a
        # half-empty bottle at this size, and the foam collides with the
        # specular; depth plus a current does the same job without the blob.
        (3,  6, "3333"),
        (4,  4, "33333333"),
        (5,  4, "33333333"),
        (6,  3, "2222222222"),
        (7,  3, "2222222222"),
        (8,  3, "2222222222"),
        (9,  3, "1111111111"),
        (10, 4, "11111111"),
        (11, 4, "00000000"),
        (12, 6, "0000"),
        # a current running down through the depth bands
        (7,  4, "33"),
        (8,  6, "33"),
        (9,  8, "33"),
        # light entering the top of the sphere
        (3,  7, "FF"),
        (4, 10, "F"),
        # bubbles on their way up
        (5,  6, "b"),
        (7,  9, "b"),
        (9,  5, "b"),
        (10, 10, "b"),
        # coral grit, and the pearl that settled out of it
        (11, 5, "c"),
        (9, 11, "c"),
        (10, 8, "P"),
    ],
    # A dune drifted up the inside of the glass, grains still in the air.
    "desert_core": [
        # Sand fills the whole sphere, same depth bands as the water. A dune
        # surface with sunlit air above it turns into one flat pale mass at
        # this size; wind ripples and loose grain carry the domain instead.
        (3,  6, "3333"),
        (4,  4, "33333333"),
        (5,  4, "33333333"),
        (6,  3, "2222222222"),
        (7,  3, "2222222222"),
        (8,  3, "2222222222"),
        (9,  3, "1111111111"),
        (10, 4, "11111111"),
        (11, 4, "00000000"),
        (12, 6, "0000"),
        # wind ripples drifting across the grain
        (6,  3, "33"),
        (6,  9, "3"),
        (7,  6, "333"),
        (8,  4, "33"),
        (8, 10, "33"),
        (9,  5, "222"),
        (10, 8, "22"),
        (11, 5, "11"),
        # loose grain catching the light, gold in it, dark pebbles in the bed
        (4,  6, "4"),
        (5,  9, "4"),
        (7,  4, "4"),
        (9,  8, "4"),
        (10, 6, "4"),
        (8,  7, "g"),
        (11, 9, "g"),
        (9,  4, "0"),
        (6, 11, "0"),
        (10, 10, "0"),
    ],
    # A skull adrift in miasma, something still lit behind the sockets.
    "cursed_core": [
        (3,  6, "0000"),
        (4,  4, "01111110"),
        (5,  4, "11222211"),
        (6,  3, "1122222211"),
        (7,  3, "1122222211"),
        (8,  3, "1122222211"),
        (9,  3, "1122222211"),
        (10, 4, "11222211"),
        (11, 4, "01111110"),
        (12, 6, "0000"),
        # the skull
        (4,  6, "HHBB"),
        (5,  5, "HBBBBD"),
        (6,  4, "HBBBBBBD"),
        (7,  4, "BEEBBEEB"),
        (8,  4, "BEGBBGEB"),
        (9,  4, "BBBNNBBD"),
        (10, 5, "DBBBBD"),
        (11, 6, "BNNB"),
        # miasma wisps, motes, and flesh that did not burn off
        (6,  3, "3"),
        (9, 12, "3"),
        (3,  7, "m"),
        (11, 4, "m"),
        (5, 11, "m"),
        (7,  3, "v"),
        (8, 12, "v"),
    ],
    # A bolt branching across the sphere, sparks thrown off the arc.
    "storm_core": [
        (3,  6, "0000"),
        (4,  4, "00011000"),
        (5,  4, "00111100"),
        (6,  3, "0011111100"),
        (7,  3, "0011221100"),
        (8,  3, "0011221100"),
        (9,  3, "0011111100"),
        (10, 4, "00111100"),
        (11, 4, "00011000"),
        (12, 6, "0000"),
        # the arc, with a spur left at row 6 and right at row 9
        (3,  9, "W"),
        (4,  8, "W"),
        (5,  8, "W"),
        (6,  5, "WWW"),
        (7,  7, "WW"),
        (8,  6, "WW"),
        (9,  7, "WWW"),
        (10, 6, "W"),
        (11, 7, "W"),
        (12, 7, "W"),
    ],
}

# Sparks are placed after the bolt glow so the glow does not swallow them.
STORM_SPARKS = [(5, 4), (11, 5), (4, 10), (10, 11)]


def paint(name):
    pal = CORES[name]
    grid = {}

    for (x, y) in RING_EDGE:
        grid[(x, y)] = pal["rim"] if facing(x, y) < -0.72 else pal["edge"]

    # The shell stays a flat tint apart from the lower-right rim light. Giving
    # it a lit arc at the upper left too merges it with the specular and the
    # whole top of the sphere goes to one bright mass.
    for (x, y) in RING_SHELL:
        grid[(x, y)] = pal["rim"] if facing(x, y) < -0.45 else pal["mid"]

    for row, x0, run in ESSENCE[name]:
        for i, ch in enumerate(run):
            p = (x0 + i, row)
            if p in IN:
                grid[p] = pal[ch]

    # Bleed the bolt's light into the cloud around it. The field is dark enough
    # that a full four-neighbour glow reads as brightness, not as a fatter bolt.
    if name == "storm_core":
        bolt = {(x0 + i, row) for row, x0, run in ESSENCE[name]
                for i, ch in enumerate(run) if ch == "W"}
        for (x, y) in IN - bolt:
            if any((x + dx, y + dy) in bolt for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                grid[(x, y)] = pal["2"]
        for p in STORM_SPARKS:
            grid[p] = pal["s"]

    for p in SPECULAR:
        grid[p] = pal["hi"]

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for (x, y), col in grid.items():
        px[x, y] = hexcol(col)
    return img


if __name__ == "__main__":
    os.makedirs(TEX_ITEM, exist_ok=True)
    for name in CORES:
        paint(name).save(os.path.join(TEX_ITEM, name + ".png"))
        print("wrote " + name + ".png")
