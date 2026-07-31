#!/usr/bin/env python3
"""
bertie_s1 texture generator — the four elemental cores (16x16), hand-placed.

The cores are the four 7x7 mechanical-crafter walls that feed the Hephaestus
Forge tier 2 ritual, one per Cataclysm boss domain. They are meant to read as a
set at inventory size, so every one is built from the same three-part shell and
differs only in metal, lens colour and the one motif inside the lens:

    shell   a 14px sphere: 1px silhouette outline, 1px lit shell ring shaded
            from the upper left, and four cardinal studs in the accent metal
    lens    a recessed 10px window — dark at the top where the rim shadows it,
            bright at the bottom where light bounces back up
    motif   the domain, drawn inside the lens:
              abyssal  a black pearl sunk in trench water, light from above
              desert   a molten heart with a four-armed sunburst in the sand
              cursed   a slit jade iris with cursed flesh at the corners
              storm    a white-hot bolt zigzagging through an indigo cloud

Cataclysm's abyss/desert/cursed/storm eyes were looked at for silhouette and
colour family only — an ornate shell around a glowing lens — and Cataclysm,
Deepwaters, Malum and Slag ingredient items for each domain's palette. No
third-party art is copied, so nothing here needs a NOTICE carve-out.

Run:  python texture-work/make_cores.py
"""
import math
import os

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEX_ITEM = os.path.join(ROOT, "src", "main", "resources", "assets", "bertie_s1", "textures", "item")

SIZE = 16
C = 8.0          # sphere centre, in pixel-corner coordinates
R_OUT = 7.0      # silhouette radius        -> 14px sphere
R_LENS = 5.2     # lens radius              -> 10px window
R_IN = 4.2       # lens interior            -> 8px motif field

# Light from the upper left, as a unit vector in screen space.
LIGHT = (-0.6, -0.8)


def hexcol(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def disc(radius):
    """Pixels whose centre falls inside a circle of `radius` about C."""
    out = set()
    for y in range(SIZE):
        for x in range(SIZE):
            if (x + 0.5 - C) ** 2 + (y + 0.5 - C) ** 2 <= radius * radius:
                out.add((x, y))
    return out


def edge_of(mask):
    """Pixels of `mask` that touch something outside it — the 1px outline."""
    return {(x, y) for (x, y) in mask
            if not all((x + dx, y + dy) in mask
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


OUT = disc(R_OUT)
LENS = disc(R_LENS)
IN = disc(R_IN)
SHELL = OUT - LENS
RIM = LENS - IN
OUTLINE = edge_of(OUT)

# Four cardinal studs, one pixel in from the silhouette so the outline stays crisp.
STUDS = {(7, 2), (8, 2), (7, 13), (8, 13), (2, 7), (2, 8), (13, 7), (13, 8)}

# Per-core palettes. Shell ramp runs k (outline) -> d -> s -> h (lit); `stud`
# and `stud_lo` are the accent metal; `lens_hi`/`lens_lo` light the lens rim;
# 0..4 is the domain ramp, darkest to brightest.
CORES = {
    "abyssal_core": {
        "k": "#040C12", "d": "#0D2029", "s": "#1B3C4A", "h": "#357080",
        "stud": "#8CE4F0", "stud_lo": "#2E8296",
        "lens_hi": "#04101A", "lens_lo": "#26789A",
        "0": "#032230", "1": "#064A70", "2": "#0B85B4", "3": "#31C6E8", "4": "#9AF0FF",
        # black pearl
        "P": "#0A0812", "p": "#2C2140", "W": "#EAF7FF",
    },
    "desert_core": {
        "k": "#241304", "d": "#513211", "s": "#8A6120", "h": "#D5A24C",
        "stud": "#F6E7BA", "stud_lo": "#9C8659",
        "lens_hi": "#2A1405", "lens_lo": "#C98A2C",
        "0": "#5E2A0A", "1": "#A24E10", "2": "#E8871C", "3": "#FFC64A", "4": "#FFF0B4",
        # molten heart + dragonbone grit
        "C": "#FFFDE8", "b": "#EDE0BC",
    },
    "cursed_core": {
        "k": "#04070A", "d": "#0E141B", "s": "#1D2731", "h": "#3A4C5E",
        "stud": "#43E084", "stud_lo": "#146B3C",
        "lens_hi": "#03090A", "lens_lo": "#158A46",
        "0": "#04211A", "1": "#0A5A32", "2": "#189B4E", "3": "#3FDD76", "4": "#A6FFB8",
        # slit iris + catchlight + cursed flesh
        "I": "#03080B", "L": "#DFFFF4", "v": "#C1264A",
    },
    "storm_core": {
        "k": "#0D131B", "d": "#26364A", "s": "#4C6480", "h": "#9CB6CE",
        "stud": "#FFD24A", "stud_lo": "#9A6E14",
        "lens_hi": "#0E0F38", "lens_lo": "#4A4ED4",
        "0": "#191A52", "1": "#3438AE", "2": "#6A72E8", "3": "#B6C4FF", "4": "#F0F5FF",
        # bolt
        "W": "#FFFFFF",
    },
}

# Motifs, painted over the lens interior as (row, first column, run). A '.'
# keeps whatever the domain ramp already put there.
MOTIFS = {
    # trench water lit from the surface, black pearl sunk in the middle
    "abyssal_core": [
        (4,  6, "3443"),
        (5,  5, "233332"),
        (6,  4, "123PP321"),
        (7,  4, "12PPPP21"),
        (8,  4, "01PPPP10"),
        (9,  4, "011PP110"),
        (10, 5, "001100"),
        (11, 6, "0000"),
        # specular off the pearl, then its iridescent bounce
        (7,  6, "W"),
        (8,  9, "p"),
        # caustics coming down through the water
        (5,  5, "4"),
        (6, 10, "3"),
    ],
    # molten heart with a four-armed sunburst thrown across the sand
    "desert_core": [
        (4,  6, "1331"),
        (5,  5, "113311"),
        (6,  4, "01244210"),
        (7,  4, "334CC433"),
        (8,  4, "334CC433"),
        (9,  4, "01244210"),
        (10, 5, "113311"),
        (11, 6, "1331"),
        # dragonbone grit caught in the corners
        (5,  5, "b"),
        (10, 10, "b"),
    ],
    # slit jade iris, cursed flesh at the corners of the window
    "cursed_core": [
        (4,  6, "2332"),
        (5,  5, "23II32"),
        (6,  4, "124II421"),
        (7,  4, "23IIII32"),
        (8,  4, "23IIII32"),
        (9,  4, "124II421"),
        (10, 5, "23II32"),
        (11, 6, "2332"),
        # catchlight, so the iris reads as an eye and not a hole
        (7,  6, "L"),
        (5,  5, "v"),
        (5, 10, "v"),
        (10, 5, "v"),
        (10, 10, "v"),
    ],
    # white-hot bolt zigzagging through an indigo cloud
    "storm_core": [
        (4,  6, "0110"),
        (5,  5, "011110"),
        (6,  4, "01122110"),
        (7,  4, "01122110"),
        (8,  4, "01122110"),
        (9,  4, "01122110"),
        (10, 5, "011110"),
        (11, 6, "0110"),
        (4,  8, "W"),
        (5,  8, "W"),
        (6,  7, "WW"),
        (7,  7, "W"),
        (8,  8, "W"),
        (9,  7, "WW"),
        (10, 7, "W"),
        (11, 7, "W"),
    ],
}

# Domain ramp used where a motif leaves a lens pixel unpainted.
FALLBACK = "1"


def shell_shade(x, y, pal):
    """Ramp the shell ring by how much it faces the light."""
    nx = (x + 0.5 - C) / R_OUT
    ny = (y + 0.5 - C) / R_OUT
    t = nx * LIGHT[0] + ny * LIGHT[1]
    if t > 0.55:
        return pal["h"]
    if t > 0.05:
        return pal["s"]
    if t > -0.55:
        return pal["d"]
    return pal["k"]


def paint(name):
    pal = CORES[name]
    grid = {}

    # shell: outline, lit ring, studs
    for (x, y) in SHELL:
        grid[(x, y)] = pal["k"] if (x, y) in OUTLINE else shell_shade(x, y, pal)
    for (x, y) in STUDS:
        nx, ny = (x + 0.5 - C) / R_OUT, (y + 0.5 - C) / R_OUT
        lit = nx * LIGHT[0] + ny * LIGHT[1] > -0.1
        grid[(x, y)] = pal["stud"] if lit else pal["stud_lo"]

    # lens rim: shadowed under the top of the shell, bounce-lit at the bottom
    for (x, y) in RIM:
        grid[(x, y)] = pal["lens_lo"] if y > C else pal["lens_hi"]

    # lens interior: domain ramp, then the motif on top
    for (x, y) in IN:
        grid[(x, y)] = pal[FALLBACK]
    for row, x0, run in MOTIFS[name]:
        for i, ch in enumerate(run):
            if ch == ".":
                continue
            p = (x0 + i, row)
            if p in IN:
                grid[p] = pal[ch]

    # Glow the storm bolt sideways only. A full halo closes around the zigzag
    # and the whole lens goes bright; left/right keeps it a 3px-wide streak.
    if name == "storm_core":
        bolt = {(x0 + i, row) for row, x0, run in MOTIFS[name]
                for i, ch in enumerate(run) if ch == "W"}
        for (x, y) in IN - bolt:
            if (x - 1, y) in bolt or (x + 1, y) in bolt:
                grid[(x, y)] = pal["3"]

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
