#!/usr/bin/env python3
"""
bertie_s1 texture generator — netherly_meal (16x16), hand-placed pixel art.

The Hephaestus ritual folds a fire dragon heart, a koboleton bone, living flesh,
dragon blood, fire scales and a bucket of lava into a plain bowl, so the item
shows all of that: the vanilla bowl silhouette pixel-for-pixel but plated in
black dragon scale, a koboleton bone jutting out to the right, a chunk of fire
dragon heart half sunk in the middle of the meal - the brew runs across its
base - and the molten brew drooling over the front lip.

The bowl reuses minecraft:item/bowl's exact outline and its shading structure,
with the vanilla brown ramp remapped onto a black-scale ramp; the belly band is
broken by two darker seams so the plating reads at 16px.

Every pixel is placed here. The Ice and Fire / Cataclysm items were looked at for
silhouette and colour family only — no third-party art is copied, so nothing here
needs a NOTICE carve-out.

Run:  python texture-work/make_netherly_meal.py
"""
import os
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEX_ITEM = os.path.join(ROOT, "src", "main", "resources", "assets", "bertie_s1", "textures", "item")

PALETTE = {
    ".": None,
    # bowl — black dragon scale ramp, darkest to lightest
    "0": "#000000",
    "1": "#14101A",
    "2": "#1B1622",
    "3": "#2A2331",
    "4": "#342C3E",
    "5": "#3E3844",
    "6": "#5A565E",
    "7": "#969495",   # rim specular
    # brew — lava / blood
    "l": "#B32A06",
    "o": "#F0600C",
    "a": "#FFA61C",
    "y": "#FFE24E",
    # fire dragon heart
    "p": "#1A0518",
    "h": "#5E1638",
    "e": "#9E2246",
    "f": "#D9436B",
    "g": "#FF9A2E",
    # koboleton bone
    "n": "#1E0F08",
    "b": "#5F473F",
    "c": "#9A887C",
    "w": "#DBCCA7",
}

# (row, first column, run). Painted in order, so later layers sit in front.
# A '.' inside a run leaves whatever is already underneath — that is how the
# bowl's interior is left open for the brew.
LAYERS = [
    # --- bowl: vanilla bowl outline 1:1, recoloured to black scale ---
    (5,  5, "333333"),
    (6,  3, "33......33"),
    (7,  2, "3..........0"),
    (8,  2, "344......440"),
    (9,  2, "375444445210"),
    (10, 3, "1636636520"),
    (11, 4, "00556500"),
    (12, 6, "0000"),
    # --- brew ---
    (6, 5, "lloool"),
    (7, 3, "loayaoooll"),
    (8, 5, "oaaool"),
    # --- drool over the front lip, plus a dribble on the right ---
    (9,  6, "ao"),
    (10, 6, "o"),
    (11, 6, "l"),
    (9, 10, "o"),
    # --- koboleton bone, out to the right ---
    (1, 14, "nn"),
    (2, 13, "nww"),
    (3, 12, "nwcn"),
    (4, 11, "nwcn"),
    (5, 10, "nwcn"),
    (6,  9, "ncbn"),
    # --- fire dragon heart, out to the left ---
    (3, 6, "php"),
    (4, 5, "pehhp"),
    (5, 4, "pfeeep"),
    (6, 4, "pegep"),
]


def build():
    grid = [["." for _ in range(16)] for _ in range(16)]
    for y, x0, run in LAYERS:
        for i, ch in enumerate(run):
            if ch != ".":
                grid[y][x0 + i] = ch
    return grid


def render(grid):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y in range(16):
        for x in range(16):
            col = PALETTE[grid[y][x]]
            if col:
                px[x, y] = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    return img


if __name__ == "__main__":
    os.makedirs(TEX_ITEM, exist_ok=True)
    render(build()).save(os.path.join(TEX_ITEM, "netherly_meal.png"))
    print("wrote netherly_meal.png")
