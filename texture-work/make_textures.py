#!/usr/bin/env python3
"""
bertie_s1 texture generator — original procedural 16x16 pixel art.
Shared silhouette families per CUSTOM_CONTENT_PLAN §5: proofs share a tablet
family with boss-specific centers; portal keys share a threshold notch; table
keys share a grid motif. No third-party art is copied.

Run:  python texture-work/make_textures.py
"""
import os
import random
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEX_ITEM = os.path.join(ROOT, "src", "main", "resources", "assets", "bertie_s1", "textures", "item")
TEX_BLOCK = os.path.join(ROOT, "src", "main", "resources", "assets", "bertie_s1", "textures", "block")
os.makedirs(TEX_ITEM, exist_ok=True)
os.makedirs(TEX_BLOCK, exist_ok=True)

T = (0, 0, 0, 0)

def shade(c, f):
    return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))),
            max(0, min(255, int(c[2] * f))), 255)

class Px:
    def __init__(self):
        self.img = Image.new("RGBA", (16, 16), T)
        self.p = self.img.load()

    def set(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            self.p[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def frame(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.set(x, y0, c); self.set(x, y1, c)
        for y in range(y0, y1 + 1):
            self.set(x0, y, c); self.set(x1, y, c)

    def noise(self, x0, y0, x1, y1, base, seed, strength=0.12):
        rng = random.Random(seed)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.p[x, y][3] > 0:
                    f = 1.0 + (rng.random() - 0.5) * 2 * strength
                    self.set(x, y, shade(self.p[x, y], f))

    def save(self, folder, name):
        self.img.save(os.path.join(folder, name + ".png"))

# palettes
WOOD = (140, 102, 60, 255)
WOOD_D = shade(WOOD, 0.7)
STONE = (128, 128, 130, 255)
STONE_D = shade(STONE, 0.72)
DARKSTONE = (52, 48, 56, 255)
DARKSTONE_L = (84, 78, 92, 255)
BRASS = (196, 158, 74, 255)
ANDESITE = (136, 136, 140, 255)
IRON = (200, 200, 205, 255)
COPPER = (186, 112, 76, 255)
GOLD = (240, 200, 70, 255)
TEAL = (36, 160, 156, 255)
MOON = (168, 212, 220, 255)
VIOLET = (120, 70, 160, 255)
SCULK = (14, 74, 88, 255)
SCULK_L = (0, 190, 190, 255)
FIRE = (232, 120, 40, 255)
FIRE_D = (160, 52, 24, 255)
IVORY = (232, 224, 200, 255)
ENDER = (16, 180, 128, 255)
OBS = (28, 20, 44, 255)
WAX = (170, 46, 60, 255)
SOUL_GOLD = (222, 178, 62, 255)
BLACKISH = (24, 24, 28, 255)

def tablet(center, rim, seed, notch=False):
    """Shared proof-tablet family: rounded rim + boss-specific center motif."""
    px = Px()
    px.rect(3, 2, 12, 13, rim)
    px.rect(4, 1, 11, 1, rim)
    px.rect(4, 14, 11, 14, rim)
    px.rect(5, 4, 10, 11, shade(rim, 0.55))
    px.rect(6, 5, 9, 10, center)
    px.set(7, 7, shade(center, 1.5)); px.set(8, 8, shade(center, 1.35))
    if notch:
        px.rect(7, 12, 8, 13, shade(rim, 1.3))
    px.noise(3, 1, 12, 14, rim, seed)
    return px

def ingot(base, seed, sheen=None):
    px = Px()
    for i, (y0) in enumerate([9, 8, 7]):
        px.rect(2 + i, y0, 11 + i, y0 + 3, shade(base, 0.8 + 0.15 * i))
    px.rect(4, 6, 13, 9, base)
    px.rect(4, 6, 13, 6, shade(base, 1.3))
    if sheen:
        px.set(5, 7, sheen); px.set(6, 7, sheen)
    px.noise(2, 6, 14, 12, base, seed)
    return px

def seal(base, glyph, seed, grid=3):
    """Wax/arcane seal with an NxN grid glyph (table-key family)."""
    px = Px()
    for y in range(16):
        for x in range(16):
            if (x - 7.5) ** 2 + (y - 7.5) ** 2 <= 42:
                px.set(x, y, base)
    px.frame(4, 4, 11, 11, shade(base, 0.6))
    step = 7 // max(1, grid)
    for gy in range(grid):
        for gx in range(grid):
            px.set(5 + gx * (6 // max(1, grid - 1) if grid > 1 else 0),
                   5 + gy * (6 // max(1, grid - 1) if grid > 1 else 0), glyph)
    px.noise(1, 1, 14, 14, base, seed)
    return px

def plate(base, holes, seed):
    px = Px()
    px.rect(2, 3, 13, 12, base)
    px.rect(2, 3, 13, 3, shade(base, 1.25))
    px.rect(2, 12, 13, 12, shade(base, 0.7))
    if holes:
        for hy in (5, 8, 11):
            for hx in (4, 7, 10):
                px.set(hx, hy - 1, shade(base, 0.45))
    px.noise(2, 3, 13, 12, base, seed)
    return px

def compass(needle, seed):
    px = Px()
    for y in range(16):
        for x in range(16):
            d = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d <= 46:
                px.set(x, y, BLACKISH if d > 30 else (40, 44, 52, 255))
    for i in range(4):
        px.set(7, 4 + i, needle)
        px.set(8, 7 + i, shade(needle, 0.6))
    px.set(7, 7, (255, 255, 255, 255))
    px.noise(1, 1, 14, 14, BLACKISH, seed, 0.08)
    return px

def eye(quadrants, seed):
    px = Px()
    for y in range(16):
        for x in range(16):
            d = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d <= 40:
                q = (0 if x < 8 else 1) + (0 if y < 8 else 2)
                px.set(x, y, quadrants[q])
    px.rect(6, 6, 9, 9, BLACKISH)
    px.set(7, 7, (255, 255, 255, 255)); px.set(8, 8, (200, 255, 240, 255))
    px.noise(1, 1, 14, 14, quadrants[0], seed, 0.10)
    return px

def mallet(seed):
    px = Px()
    px.rect(9, 2, 13, 6, WOOD)          # head
    px.rect(9, 2, 13, 2, shade(WOOD, 1.25))
    px.set(11, 4, BRASS)                 # brass pin
    for i in range(8):                   # diagonal handle
        px.set(8 - i, 6 + i, WOOD_D)
        px.set(9 - i, 6 + i, shade(WOOD_D, 1.2))
    px.noise(1, 1, 14, 14, WOOD, seed)
    return px

def vane(seed):
    px = Px()
    for i in range(10):
        x = 2 + i
        y = 12 - i
        px.rect(x, y, x + 1, min(y + 3, 14), WOOD if i % 2 else shade(WOOD, 1.15))
    px.rect(11, 2, 13, 4, shade(WOOD, 0.6))   # shaft notch
    px.noise(1, 1, 14, 14, WOOD, seed)
    return px

def cage(seed):
    px = Px()
    for x in (3, 7, 11):
        px.rect(x, 3, x + 1, 12, IRON)
    px.rect(3, 3, 12, 4, shade(IRON, 0.8))
    px.rect(3, 11, 12, 12, shade(IRON, 0.8))
    px.set(5, 8, FIRE); px.set(9, 7, FIRE); px.set(6, 6, shade(FIRE, 1.2))
    px.noise(3, 3, 12, 12, IRON, seed)
    return px

def lattice(base, cell, seed):
    px = Px()
    for i in range(4):
        px.rect(2, 2 + i * 4, 13, 2 + i * 4, base)
        px.rect(2 + i * 4 if i < 3 else 13, 2, 2 + i * 4 if i < 3 else 13, 14, base)
    px.rect(13, 2, 13, 14, base)
    px.rect(2, 14, 13, 14, base)
    for gy in range(3):
        for gx in range(3):
            px.set(4 + gx * 4, 4 + gy * 4, cell)
            px.set(5 + gx * 4, 4 + gy * 4, shade(cell, 0.7))
    px.noise(2, 2, 13, 14, base, seed)
    return px

def shard(base, seed):
    px = Px()
    pts = [(7, 1), (10, 5), (12, 10), (8, 14), (5, 10), (4, 5)]
    for y in range(1, 15):
        for x in range(3, 13):
            inside = (abs(x - 7.5) * 1.4 + abs(y - 7.5)) < 7.5
            if inside:
                px.set(x, y, base)
    px.set(6, 4, shade(base, 1.5)); px.set(7, 6, shade(base, 1.3))
    px.noise(3, 1, 12, 14, base, seed)
    return px

def blank(base, groove, seed):
    px = Px()
    px.rect(2, 4, 13, 12, base)
    px.rect(2, 4, 13, 4, shade(base, 1.2))
    px.rect(5, 7, 10, 9, groove)
    px.noise(2, 4, 13, 12, base, seed)
    return px

def anchor(seed):
    px = Px()
    px.rect(6, 1, 9, 3, MOON)            # loop
    px.rect(7, 3, 8, 9, OBS)             # shaft
    px.rect(4, 9, 11, 11, OBS)           # arms
    px.rect(6, 11, 9, 13, shade(OBS, 1.6))
    px.set(7, 12, MOON); px.set(8, 12, MOON)
    px.noise(4, 1, 11, 13, OBS, seed, 0.2)
    return px

def core(seed):
    px = Px()
    px.rect(3, 3, 12, 12, (46, 108, 110, 255))
    px.frame(3, 3, 12, 12, shade(TEAL, 0.6))
    px.rect(6, 6, 9, 9, TEAL)
    px.set(7, 7, (240, 255, 250, 255)); px.set(8, 8, shade(TEAL, 1.4))
    for x, y in [(5, 5), (10, 5), (5, 10), (10, 10)]:
        px.set(x, y, SOUL_GOLD)
    px.noise(3, 3, 12, 12, TEAL, seed)
    return px

def quad_matrix(seed):
    px = Px()
    cols = [FIRE, IVORY, VIOLET, TEAL]
    for qy in range(2):
        for qx in range(2):
            px.rect(2 + qx * 6, 2 + qy * 6, 7 + qx * 6, 7 + qy * 6, cols[qy * 2 + qx])
    px.frame(2, 2, 13, 13, DARKSTONE)
    px.rect(7, 2, 8, 13, DARKSTONE); px.rect(2, 7, 13, 8, DARKSTONE)
    px.set(7, 7, (255, 255, 255, 255)); px.set(8, 8, (255, 255, 255, 255))
    px.noise(2, 2, 13, 13, DARKSTONE, seed, 0.08)
    return px

ITEM_PAINTERS = {
    "opening_mallet": lambda: mallet(1),
    "stone_crucible_blank": lambda: blank(STONE, STONE_D, 3),
    "stone_pour_channel": lambda: blank(STONE_D, shade(STONE_D, 0.6), 4),
    "kinetic_vane": lambda: vane(7),
    "kinetic_pattern_plate": lambda: plate(ANDESITE, True, 10),
    "crafting_language_slate": lambda: plate(STONE_D, True, 11),
    "crafting_language_seal": lambda: seal(WAX, GOLD, 12, 3),
    "twilight_concord": lambda: shard((92, 160, 96, 255), 15),
    "spirit_focused_echo": lambda: shard(TEAL, 23),
    "spirit_altar_witness": lambda: seal(shade(WOOD, 1.1), TEAL, 24, 2),
    "runewood_resonance": lambda: seal(WOOD_D, SOUL_GOLD, 25, 2),
    "warden_echo_pattern": lambda: tablet(SCULK, SCULK_L, 27),
    "echoing_city_compass": lambda: compass(SCULK_L, 28),
    "weeping_compass": lambda: compass(VIOLET, 29),
    "well_attunement": lambda: shard((60, 30, 90, 255), 30),
    "descent_anchor": lambda: anchor(31),
    "complex_spectrum_seal": lambda: seal((80, 60, 110, 255), MOON, 33, 3),
    "soulbound_authority": lambda: tablet(SOUL_GOLD, BLACKISH, 34),
    "ignitium_lattice": lambda: lattice(FIRE_D, FIRE, 35),
    "ignitium_strut": lambda: ingot(FIRE_D, 36, FIRE),
    "dragonbone_frame": lambda: lattice(shade(IVORY, 0.85), MOON, 37),
    "dragonbone_brace": lambda: ingot(IVORY, 38),
    "concordant_moonsteel_ingot": lambda: ingot((44, 110, 118, 255), 39, MOON),
    "hephaestian_sovereign_seal": lambda: seal(DARKSTONE, GOLD, 40, 3),
    "convergence_matrix": lambda: quad_matrix(41),
    "mekanism_access_core": lambda: core(42),
    "boss_rematch_seal": lambda: seal((110, 40, 40, 255), IVORY, 43, 2),
}

def block_tex(base, accent, seed):
    px = Px()
    px.rect(0, 0, 15, 15, base)
    px.frame(0, 0, 15, 15, shade(base, 0.7))
    px.frame(3, 3, 12, 12, accent)
    px.noise(0, 0, 15, 15, base, seed)
    return px

BLOCK_PAINTERS = {
    "licensed_crafting_plinth": lambda: block_tex(DARKSTONE, SOUL_GOLD, 100),
    "echo_lock": lambda: block_tex(SCULK, SCULK_L, 103),
}

for name, painter in ITEM_PAINTERS.items():
    painter().save(TEX_ITEM, name)
for name, painter in BLOCK_PAINTERS.items():
    painter().save(TEX_BLOCK, name)

print(f"items: {len(ITEM_PAINTERS)}  blocks: {len(BLOCK_PAINTERS)}")
