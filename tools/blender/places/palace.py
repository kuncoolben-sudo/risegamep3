"""The Grand Palace, Bangkok: crenellated white walls round a courtyard, a tiered-roof throne hall, a golden chedi and a
tall prang. Unit 1 (countries, time)."""
import math

from .common import B, chedi, plate, slab, spire, thai_roof, tiered_roof, wall

PALETTE = {
    'Stone': '#d8d2c4', 'White': '#f7f2e8', 'Cream': '#f1e3c0', 'Gold': ('#f2bb32', dict(rough=0.35, emit='#c98a10', es=0.3)),
    'GoldDark': ('#d9992a', dict(rough=0.4, emit='#a8700c', es=0.2)), 'Orange': '#e8742a', 'Green': '#2f9e6b', 'Red': '#c63d2f',
    'Pink': '#f2a7b8', 'Blue': '#3d6fd0', 'Dark': '#2b2b33', 'Glass': '#9fd3ee', 'Flag': '#f7c948', 'Wood': '#8a5a2b', 'Lawn': '#7ec850',
}
RADIUS = 5.4
LABEL_Y = 6.8


def throne_hall(p, c):
    cx, cy = c
    slab(p, 'Stone', (cx, cy, 0.1), 4.3, 2.9, 0.18)
    slab(p, 'White', (cx, cy, 0.28), 3.9, 2.5, 0.16)
    p.box(B, 'Cream', (cx, cy, 0.44 + 0.65), (3.4, 2.0, 1.3))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cone(B, 'Gold', (cx + sx * 1.7, cy + sy * 1.0, 0.44), (cx + sx * 1.7, cy + sy * 1.0, 1.9), 0.11, 0.09, seg=8)
    for i in range(3):  # doors and windows on the front
        x = cx + (i - 1) * 0.95
        p.box(B, 'Red' if i == 1 else 'Blue', (x, cy - 1.03, 1.05), (0.5, 0.06, 0.9 if i == 1 else 0.6))
        p.box(B, 'Gold', (x, cy - 1.05, 1.58), (0.62, 0.05, 0.08))
    top = tiered_roof(p, 'Cream', ('Orange', 'Green'), ('Green', 'Orange'), 'Gold', (cx, cy, 1.74),
                      [(3.4, 2.0, 0.85), (2.4, 1.4, 0.78), (1.5, 1.0, 0.66)], 0, 0.38, panel_m='Gold')
    spire(p, 'Gold', (cx, cy, top), 0.3, 1.5, tiers=4, seg=8, tip_m='Gold')


def golden_chedi(p, c):
    cx, cy = c
    slab(p, 'White', (cx, cy, 0), 2.1, 2.1, 0.22)
    slab(p, 'Cream', (cx, cy, 0.22), 1.7, 1.7, 0.2)
    chedi(p, 'Gold', 'GoldDark', (cx, cy, 0.42), 0.72, 4.0, seg=14, tip_m='Gold')
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cone(B, 'Gold', (cx + sx * 0.95, cy + sy * 0.95, 0.42), (cx + sx * 0.95, cy + sy * 0.95, 1.25), 0.12, 0.0, seg=6)


def prang(p, c):
    cx, cy = c
    slab(p, 'White', (cx, cy, 0), 2.2, 2.2, 0.22)
    prof = [(0.95, 0.22), (0.95, 0.85), (0.8, 0.85), (0.8, 1.45), (0.66, 1.45), (0.66, 1.95), (0.52, 1.95), (0.52, 2.4), (0.4, 2.4),
            (0.4, 2.75), (0.28, 2.75), (0.28, 3.05), (0.12, 3.6), (0.0, 4.1)]
    p.lathe(B, 'White', prof, (cx, cy, 0), seg=8, rot=22.5)
    for z, r in ((0.85, 0.82), (1.45, 0.68), (1.95, 0.54)):
        p.cone(B, 'Pink', (cx, cy, z), (cx, cy, z + 0.08), r, r, seg=8)
    for z in (1.05, 1.65, 2.15):
        p.sphere(B, 'Gold', (cx, cy - (0.78 - (z - 1.05) * 0.18), z), 0.07, seg=6, rings=4)
    p.cone(B, 'Gold', (cx, cy, 3.9), (cx, cy, 4.9), 0.07, 0.0, seg=6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.lathe(B, 'Pink', [(0.26, 0.22), (0.26, 0.8), (0.2, 1.0), (0.09, 1.5), (0, 1.9)], (cx + sx * 0.95, cy + sy * 0.95, 0), seg=6)


def guardian(p, c, body_m):
    x, y = c
    p.cone(B, body_m, (x, y, 0.1), (x, y, 0.95), 0.26, 0.2, seg=8)
    p.sphere(B, body_m, (x, y, 1.12), 0.2, seg=8, rings=6)
    p.cone(B, 'Gold', (x, y, 1.28), (x, y, 1.8), 0.17, 0.0, seg=6)
    p.cone(B, 'Gold', (x - 0.3, y - 0.05, 0.4), (x - 0.34, y - 0.05, 1.5), 0.05, 0.08, seg=6)
    for sx in (-1, 1):
        p.sphere(B, 'Dark', (x + sx * 0.08, y - 0.17, 1.14), 0.03, seg=5, rings=4)


def build(p):
    plate(p, 'Stone', (0, 0, 0), 5.4, 0.1)
    plate(p, 'Lawn', (0, 0.4, 0.1), 2.6, 0.03)
    # walls: back and sides, the front opens at the gate
    for a, b in (((-3.8, 3.8), (3.8, 3.8)), ((-3.8, -3.8), (-3.8, 3.8)), ((3.8, -3.8), (3.8, 3.8)),
                 ((-3.8, -3.8), (-1.2, -3.8)), ((1.2, -3.8), (3.8, -3.8))):
        wall(p, 'White', a, b, 0.85, 0.3, 0.1, merlon=(0.3, 0.26), step=0.55)
        wall(p, 'Green', a, b, 0.1, 0.34, 0.45)
    for sx in (-1, 1):  # gate posts and a little tiered roof
        p.box(B, 'White', (sx * 1.2, -3.8, 0.1 + 0.85), (0.5, 0.5, 1.7))
        p.box(B, 'Gold', (sx * 1.2, -3.8, 1.95), (0.58, 0.58, 0.1))
    thai_roof(p, 'Orange', 'Green', 'Gold', (0, -3.8, 1.95), 2.4, 0.7, 0.55, 0.25, 0, panel_m='Gold')
    throne_hall(p, (0, -0.6))
    golden_chedi(p, (-2.4, 2.2))
    prang(p, (2.4, 2.2))
    guardian(p, (-1.9, -3.1), 'Green')
    guardian(p, (1.9, -3.1), 'Blue')
    for sx in (-1, 1):  # flags
        p.cone(B, 'Wood', (sx * 3.2, -3.2, 0.1), (sx * 3.2, -3.2, 2.6), 0.04, 0.03, seg=5)
        p.blade(B, 'Flag', (sx * 3.2, -3.2, 2.45), (sx * 3.2 - sx * 0.7, -3.2, 2.25), 0.4, 0.02, face=(0, 1, 0), peak=0.5)
        p.blob(B, 'Lawn', (sx * 2.8, -2.5, 0.4), 0.38, (1, 1, 1.1), 0.1, 4 + sx, 7, 5)
