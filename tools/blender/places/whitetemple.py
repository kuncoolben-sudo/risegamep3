"""Wat Rong Khun (the White Temple), Chiang Rai: a dazzling white temple with stacked silver-trimmed roofs and spires, the
bridge over a pond of reaching hands and the little golden building beside it. Unit 6 (my day: a trip to see art)."""
import random

from .common import B, plate, round_tree, slab, spire, tiered_roof

PALETTE = {
    'Lawn': '#7cc45a', 'Plaza': '#c9ced6', 'Stone': '#e4e7ec', 'White': '#fdfdff', 'RoofW': '#e2eaf5', 'Silver': ('#a9bdd8', dict(rough=0.25, emit='#8fa8c4', es=0.25)),
    'Mirror': ('#d8efff', dict(rough=0.12, emit='#8fc8ff', es=0.7)), 'Gold': ('#f2bb32', dict(rough=0.35, emit='#c98a10', es=0.3)),
    'GoldDark': ('#d9992a', dict(rough=0.4, emit='#a8700c', es=0.2)), 'Water': '#7fd3e6', 'Leaf': '#4ea84a', 'Leaf2': '#2f8a3e',
    'Trunk': '#7a5632', 'Dark': '#2b2b33',
}
RADIUS = 5.0
LABEL_Y = 7.2


def hand(p, x, y, h, lean):
    """A hand reaching up out of the pond (the 'bridge of the cycle of rebirth'): arm, open palm and spread fingers."""
    lx, ly = lean
    top = (x + lx, y + ly, 0.14 + h)
    p.tube(B, 'White', [(x, y, 0.1), (x + lx * 0.25, y + ly * 0.25, 0.14 + h * 0.5), top], [0.11, 0.085, 0.07], seg=6)
    p.sphere(B, 'White', (top[0], top[1], top[2] + 0.06), 0.12, (0.9, 0.5, 1.0), seg=7, rings=5, smooth=False)
    for k in range(4):
        s = k - 1.5
        base = (top[0] + s * 0.05, top[1], top[2] + 0.13)
        tip = (base[0] + s * 0.08 + lx * 0.15, base[1] + ly * 0.15, base[2] + 0.24 - abs(s) * 0.04)
        p.cone(B, 'White', base, tip, 0.035, 0.018, seg=5)
    p.cone(B, 'White', (top[0] - 0.1, top[1], top[2] + 0.05), (top[0] - 0.24, top[1], top[2] + 0.2), 0.035, 0.018, seg=5)


def temple(p, c):
    cx, cy = c
    slab(p, 'Stone', (cx, cy, 0.14), 4.6, 3.2, 0.26)
    slab(p, 'White', (cx, cy, 0.4), 4.1, 2.8, 0.2)
    slab(p, 'Stone', (cx, cy, 0.6), 3.6, 2.4, 0.16)
    z0 = 0.76
    p.box(B, 'White', (cx, cy, z0 + 0.75), (2.8, 1.9, 1.5))
    p.box(B, 'Gold', (cx, cy - 0.96, z0 + 0.55), (0.78, 0.05, 1.08))
    p.box(B, 'Dark', (cx, cy - 0.98, z0 + 0.5), (0.58, 0.04, 0.9))
    for sx in (-1, 1):
        p.box(B, 'Mirror', (cx + sx * 0.98, cy - 0.96, z0 + 0.85), (0.4, 0.05, 0.6))
    rnd = random.Random(3)
    for _ in range(18):  # the mirror mosaic
        p.box(B, 'Mirror', (cx + rnd.uniform(-1.3, 1.3), cy - 0.97, z0 + rnd.uniform(0.2, 1.4)), (0.09, 0.04, 0.09))
    top = tiered_roof(p, 'White', 'RoofW', 'Silver', 'Silver', (cx, cy, z0 + 1.5), [(2.8, 1.9, 0.85), (1.9, 1.4, 0.75), (1.2, 1.0, 0.62)], 0, 0.35,
                      panel_m='Silver')
    spire(p, 'Silver', (cx, cy, top), 0.28, 1.5, tiers=4, seg=8, tip_m='Gold')
    for sx in (-1, 1):
        for sy in (-1, 1):
            spire(p, 'White', (cx + sx * 1.65, cy + sy * 1.0, z0), 0.2, 1.7, tiers=4, seg=8, tip_m='Silver')


def golden_hall(p, c):
    cx, cy = c
    slab(p, 'Stone', (cx, cy, 0.14), 1.8, 1.6, 0.14)
    p.box(B, 'Gold', (cx, cy, 0.28 + 0.45), (1.25, 1.05, 0.9))
    p.box(B, 'GoldDark', (cx, cy - 0.54, 0.62), (0.34, 0.04, 0.6))
    for sx in (-1, 1):
        p.box(B, 'Mirror', (cx + sx * 0.4, cy - 0.54, 0.78), (0.24, 0.04, 0.36))
    top = tiered_roof(p, 'Gold', 'Gold', 'GoldDark', 'GoldDark', (cx, cy, 1.18), [(1.25, 1.05, 0.5), (0.85, 0.7, 0.42)], 0, 0.25, panel_m='GoldDark')
    spire(p, 'Gold', (cx, cy, top), 0.16, 0.8, tiers=3, seg=6, tip_m='Gold')


def pavilion(p, c):
    cx, cy = c
    slab(p, 'Stone', (cx, cy, 0.14), 1.7, 1.7, 0.14)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cone(B, 'White', (cx + sx * 0.65, cy + sy * 0.65, 0.28), (cx + sx * 0.65, cy + sy * 0.65, 1.2), 0.07, 0.06, seg=6)
    top = tiered_roof(p, 'White', 'RoofW', 'Silver', 'Silver', (cx, cy, 1.2), [(1.5, 1.5, 0.55), (0.9, 0.9, 0.45)], 0, 0.28, panel_m='Silver')
    spire(p, 'Silver', (cx, cy, top), 0.14, 0.7, tiers=3, seg=6, tip_m='Gold')


def build(p):
    plate(p, 'Lawn', (0, 0, 0), 5.0, 0.1)
    plate(p, 'Plaza', (0, 0.2, 0.1), 4.4, 0.04)
    # the pond, its rim and the bridge across it
    plate(p, 'Water', (0, -1.7, 0.14), 1.9, 0.03)
    p.torus(B, 'White', (0, -1.7, 0.15), 1.95, 0.1, seg=26, minor=5)
    slab(p, 'White', (0, -1.6, 0.32), 0.8, 4.3, 0.08)
    for sx in (-1, 1):
        x = sx * 0.38
        for i in range(9):
            y = -3.6 + i * 0.5
            p.cone(B, 'White', (x, y, 0.4), (x, y, 0.82), 0.045, 0.04, seg=5)
            p.sphere(B, 'Silver', (x, y, 0.88), 0.055, seg=5, rings=3)
        p.tube(B, 'White', [(x, -3.65, 0.78), (x, 0.45, 0.78)], 0.03, seg=4)
    for x, y, h, lean in ((-1.0, -3.2, 0.8, (0.15, 0.1)), (1.05, -3.0, 1.0, (-0.15, 0.1)), (-1.3, -2.6, 1.1, (0.2, 0.0)), (1.2, -2.4, 0.9, (-0.2, 0.05)),
                          (-0.9, -1.9, 1.2, (0.15, 0.05)), (1.0, -1.7, 1.15, (-0.15, 0.0)), (-1.4, -1.2, 0.9, (0.2, 0.1)), (1.3, -1.0, 1.05, (-0.2, 0.1)),
                          (-0.9, -0.6, 0.8, (0.15, 0.1)), (0.95, -0.4, 0.9, (-0.15, 0.1))):
        hand(p, x, y, h, lean)
    temple(p, (0, 2.1))
    golden_hall(p, (-3.3, -0.2))
    pavilion(p, (3.3, -0.2))
    round_tree(p, 'Trunk', 'Leaf', (-3.6, 2.9, 0.14), 1.9, 0.85, 4, 'Leaf2')
    round_tree(p, 'Trunk', 'Leaf2', (3.7, 2.6, 0.14), 1.7, 0.8, 8, 'Leaf')
    for x, y in ((-3.2, -2.9), (3.1, -3.0), (0.0, -4.1)):
        p.blob(B, 'Leaf', (x, y, 0.3), 0.4, (1, 1, 0.8), 0.12, int(x * 3 + 20), 7, 5)
