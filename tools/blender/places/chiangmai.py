"""Chiang Mai: a golden Lanna chedi on a stepped base, a teak temple hall with crossed gable ornaments, a string of
lanterns and Yi Peng sky lanterns floating over pink blossom trees. Unit 3 (family and friends, community)."""
import math

from .common import B, chedi, gable, plate, round_tree, slab

PALETTE = {
    'Plaza': '#d9bc8f', 'Stone': '#e9e0cc', 'White': '#f7f1e5', 'Gold': ('#f2bb32', dict(rough=0.35, emit='#c98a10', es=0.3)),
    'GoldDark': ('#d9992a', dict(rough=0.4, emit='#a8700c', es=0.2)), 'Teak': '#80502d', 'TeakDark': '#55331a', 'Terracotta': '#b9532f',
    'RoofDark': '#8f3d22', 'Red': '#d6402f', 'Cord': '#4a3520', 'Pink': '#f6a8c8', 'PinkDark': '#e27fab', 'Leaf': '#58b04e', 'Trunk': '#6b4a2b',
    'Lawn': '#86cf62', 'LanternRed': ('#ff5a3c', dict(emit='#ff3a1c', es=2.5)), 'LanternYellow': ('#ffd36a', dict(emit='#ffb020', es=2.5)),
    'Window': ('#ffd98a', dict(emit='#ffb830', es=1.2)), 'Flame': ('#fff1b0', dict(emit='#ffd060', es=3.0)),
}
RADIUS = 4.8
LABEL_Y = 7.4


def lanna_hall(p, c, w, d, wall_h, yaw=0):
    """A Lanna hall: dark teak walls on a white plinth, two low sweeping tiers of terracotta roof, crossed gable ornaments
    at the ridge ends and a veranda of columns. The gable end faces front (-y)."""
    cx, cy = c
    slab(p, 'White', (cx, cy, 0.1), w + 0.5, d + 0.5, 0.2)
    p.box(B, 'Teak', (cx, cy, 0.3 + wall_h / 2), (w, d, wall_h))
    for i in range(3):
        p.box(B, 'Window', (cx + (i - 1) * w * 0.28, cy - d / 2 - 0.02, 0.3 + wall_h * 0.58), (0.3, 0.05, 0.4))
    p.box(B, 'TeakDark', (cx, cy - d / 2 - 0.03, 0.3 + wall_h * 0.4), (0.42, 0.06, wall_h * 0.8))
    gable(p, 'Terracotta', (cx, cy, 0.3 + wall_h), w, d, 1.0, 0.45, 0, 0.12, panel_m='Teak')
    gable(p, 'RoofDark', (cx, cy, 0.3 + wall_h + 0.7), w * 0.62, d * 0.8, 0.8, 0.3, 0, 0.12, panel_m='Teak')
    for sy in (-1, 1):  # crossed gable ornaments (kalae)
        z = 0.3 + wall_h + 0.7 + 0.8 + 0.12
        for sgn in (-1, 1):
            p.box(B, 'TeakDark', (cx, cy + sy * (d * 0.4 + 0.3), z + 0.18), (0.05, 0.05, 0.62), rot=(sy * 12, sgn * 40, 0))
    for sx in (-1, 1):  # veranda columns
        for sy in (-1, 1):
            p.cone(B, 'TeakDark', (cx + sx * (w / 2 - 0.1), cy + sy * (d / 2 + 0.2), 0.2), (cx + sx * (w / 2 - 0.1), cy + sy * (d / 2 + 0.2), 0.3 + wall_h), 0.07, 0.07, seg=6)


def build(p):
    plate(p, 'Plaza', (0, 0, 0), 4.8, 0.1)
    # golden Lanna chedi on a stepped base
    slab(p, 'White', (0, 2.0, 0.1), 3.0, 3.0, 0.22)
    slab(p, 'White', (0, 2.0, 0.32), 2.5, 2.5, 0.22)
    slab(p, 'Gold', (0, 2.0, 0.54), 2.0, 2.0, 0.28)
    chedi(p, 'Gold', 'GoldDark', (0, 2.0, 0.82), 0.72, 4.4, seg=14, tip_m='Gold')
    for sx in (-1, 1):
        for sy in (-1, 1):
            chedi(p, 'Gold', 'GoldDark', (sx * 0.78, 2.0 + sy * 0.78, 0.82), 0.2, 1.1, seg=8)
    for i in range(4):  # steps up to the base
        slab(p, 'Stone', (0, 0.35 - i * 0.28, 0.1), 1.6 + i * 0.16, 0.3, 0.1 + (3 - i) * 0.05)
    lanna_hall(p, (-2.55, -0.5), 1.8, 2.3, 0.95)
    lanna_hall(p, (2.65, -0.7), 1.5, 1.9, 0.9)
    # a string of lanterns across the front
    pts = [(-3.7, -3.1, 3.0), (3.7, -3.1, 3.0)]
    for x in pts:
        p.cone(B, 'Trunk', (x[0], x[1], 0.1), (x[0], x[1], x[2]), 0.07, 0.05, seg=5)
    cord = [(-3.7 + 7.4 * t, -3.1, 3.0 - 0.55 * math.sin(math.pi * t)) for t in [i / 8 for i in range(9)]]
    p.tube(B, 'Cord', cord, 0.015, seg=4)
    for i in range(1, 8):
        c = cord[i]
        p.cone(B, 'Cord', (c[0], c[1], c[2]), (c[0], c[1], c[2] - 0.22), 0.01, 0.01, seg=4)
        p.sphere(B, 'LanternRed' if i % 2 else 'LanternYellow', (c[0], c[1], c[2] - 0.38), 0.17, (1, 1, 1.3), seg=8, rings=6)
    # Yi Peng sky lanterns drifting up round the chedi (none in front of it)
    for x, y, z in ((-3.0, 0.6, 5.0), (-2.1, 2.9, 6.3), (-3.3, 3.0, 4.4), (2.4, 3.1, 5.7), (3.2, 1.0, 6.5), (1.5, 3.6, 7.0), (-1.3, 3.9, 7.2)):
        p.cone(B, 'LanternYellow', (x, y, z), (x, y, z + 0.4), 0.17, 0.24, seg=8)
        p.sphere(B, 'Flame', (x, y, z - 0.02), 0.09, seg=6, rings=4)
    # blossom trees
    round_tree(p, 'Trunk', 'Pink', (3.2, -3.0, 0.1), 1.8, 0.8, 5, 'PinkDark')
    round_tree(p, 'Trunk', 'Pink', (-3.4, 1.9, 0.1), 2.0, 0.9, 9, 'PinkDark')
    round_tree(p, 'Trunk', 'Leaf', (3.6, 1.2, 0.1), 1.6, 0.7, 12)
