"""Khao Yai National Park: a mossy cliff with a waterfall into a pool, forest, a wooden park sign, a sambar deer and a
great hornbill on a dead snag. Unit 8 (animals)."""
import math

from .common import B, plate, round_tree, rz, strip

PALETTE = {
    'Grass': '#79c24f', 'Cliff': '#7d7262', 'CliffLight': '#a59c88', 'Moss': '#4f9a4a', 'Falls': ('#dff5ff', dict(emit='#a6e0ff', es=0.5)),
    'Foam': '#ffffff', 'Pool': '#2fb7b2', 'PoolDeep': '#1f8f98', 'Trunk': '#6a4a2a', 'Leaf': '#3f9f45', 'Leaf2': '#2b7d3a', 'Leaf3': '#82c852',
    'Wood': '#8a5a2b', 'SignGreen': '#2f6b3a', 'SignYellow': '#f2c94c', 'Deer': '#a9683a', 'DeerLight': '#ecd3ab', 'Antler': '#dccba2',
    'Dark': '#2a2a2a', 'Beak': '#f5a623', 'BirdBlack': '#1e1e24', 'White': '#ffffff', 'Flower': '#ff7aa8', 'Stone': '#9a9484',
}
RADIUS = 5.0
LABEL_Y = 6.2


def front_y(z, x=0.2, cx=0.2, cy=3.4, rx=2.2, ry=1.5, cz=2.3, rz_=2.4):
    """y of the cliff's front face at height z and across-position x (for the ellipsoid used below)."""
    t = max(0.0, 1 - ((x - cx) / rx) ** 2 - ((z - cz) / rz_) ** 2)
    return cy - ry * math.sqrt(t)


def ribbon(p, m, x, w, z0, z1, n=8, cols=3, off=-0.25):
    """A sheet of falling water centred on x that hugs the cliff face from height z0 down to z1 (clear of its bumps)."""
    xs = [x - w / 2 + w * j / cols for j in range(cols + 1)]
    zs = [z1 + (z0 - z1) * i / n for i in range(n + 1)]
    c = cols + 1
    p.poly(B, m, [(xx, front_y(zz, xx) + off, zz) for zz in zs for xx in xs],
           [(i * c + j, i * c + j + 1, (i + 1) * c + j + 1, (i + 1) * c + j) for i in range(n) for j in range(cols)])


def deer(p, c, yaw=0):
    """A sambar deer standing; faces local -y rotated by yaw."""
    cx, cy = c

    def T(x, y, z):
        return rz((x, y, z), yaw, (cx, cy, 0.1))
    p.sphere(B, 'Deer', T(0, 0, 0.78), 0.34, (0.7, 1.35, 0.7), rot=(0, 0, yaw), seg=9, rings=6)
    p.sphere(B, 'DeerLight', T(0, -0.05, 0.62), 0.28, (0.55, 1.2, 0.4), rot=(0, 0, yaw), seg=8, rings=5)
    for lx in (-0.14, 0.14):
        for ly in (-0.38, 0.38):
            a, b = T(lx, ly, 0.7), T(lx, ly, 0.0)
            p.cone(B, 'Deer', a, b, 0.07, 0.04, seg=5)
            p.sphere(B, 'Dark', T(lx, ly, 0.0), 0.05, seg=5, rings=4)
    p.cone(B, 'Deer', T(0, -0.42, 0.95), T(0, -0.66, 1.4), 0.12, 0.08, seg=6)
    p.sphere(B, 'Deer', T(0, -0.72, 1.45), 0.13, (0.9, 1.3, 0.9), rot=(0, 0, yaw), seg=7, rings=5)
    p.sphere(B, 'Dark', T(0, -0.88, 1.42), 0.04, seg=5, rings=4)
    for sx in (-1, 1):
        p.sphere(B, 'Dark', T(sx * 0.07, -0.78, 1.5), 0.025, seg=4, rings=3)
        p.blade(B, 'Deer', T(sx * 0.1, -0.68, 1.52), T(sx * 0.26, -0.66, 1.62), 0.1, 0.02, face=(0, 0, 1))
        p.tube(B, 'Antler', [T(sx * 0.07, -0.68, 1.55), T(sx * 0.12, -0.7, 1.82), T(sx * 0.2, -0.72, 2.05)], [0.022, 0.018, 0.008], seg=4)
        p.tube(B, 'Antler', [T(sx * 0.1, -0.7, 1.72), T(sx * 0.22, -0.78, 1.86)], [0.016, 0.006], seg=4)
    p.sphere(B, 'DeerLight', T(0, 0.46, 0.86), 0.09, seg=5, rings=4)


def hornbill(p, c, yaw=0, k=1.4):
    """A great hornbill, body centre at c, beak towards local -y rotated by yaw, scaled by k (its feet hang 0.63 below c)."""
    cx, cy, cz = c

    def T(x, y, z):
        return rz((x * k, y * k, z * k), yaw, (cx, cy, cz))
    p.sphere(B, 'BirdBlack', T(0, 0.05, 0), 0.2 * k, (0.85, 1.3, 0.9), rot=(0, 0, yaw), seg=8, rings=6)
    p.sphere(B, 'White', T(0, 0.3, -0.04), 0.14 * k, (0.8, 1.6, 0.6), rot=(0, 0, yaw), seg=7, rings=5)
    p.sphere(B, 'White', T(0, -0.16, 0.12), 0.13 * k, seg=7, rings=5)
    p.sphere(B, 'BirdBlack', T(0, -0.26, 0.24), 0.11 * k, seg=7, rings=5)
    p.cone(B, 'Beak', T(0, -0.32, 0.22), T(0, -0.66, 0.16), 0.07 * k, 0.02 * k, seg=6)
    p.sphere(B, 'Beak', T(0, -0.4, 0.31), 0.07 * k, (0.7, 1.5, 0.8), rot=(0, 0, yaw), seg=6, rings=4)
    p.sphere(B, 'White', T(0.0, -0.31, 0.27), 0.02 * k, seg=4, rings=3)
    p.cone(B, 'Trunk', T(0, 0, -0.18), T(0, 0, -0.45), 0.03 * k, 0.03 * k, seg=4)


def build(p):
    plate(p, 'Grass', (0, 0, 0), 5.0, 0.1)
    # cliff + moss + waterfall
    p.blob(B, 'Cliff', (0.2, 3.4, 2.3), 1.0, (2.2, 1.5, 2.4), 0.07, 2, 11, 8)
    p.blob(B, 'Cliff', (-2.5, 2.9, 1.4), 1.0, (1.1, 1.1, 1.5), 0.1, 6, 9, 6)
    p.blob(B, 'CliffLight', (2.7, 2.9, 1.2), 1.0, (1.1, 1.0, 1.3), 0.1, 9, 9, 6)
    p.blob(B, 'Moss', (0.4, 3.3, 4.55), 1.0, (1.7, 1.2, 0.45), 0.12, 4, 9, 5)
    p.blob(B, 'Moss', (-2.5, 2.8, 2.5), 1.0, (0.9, 0.8, 0.4), 0.12, 8, 8, 5)
    p.blob(B, 'Moss', (2.7, 2.9, 2.1), 1.0, (0.9, 0.8, 0.4), 0.12, 13, 8, 5)
    ribbon(p, 'Falls', 0.1, 1.9, 4.3, 0.45)
    for x, w in ((-0.45, 0.14), (0.3, 0.1), (0.7, 0.14)):  # white streaks on the falling water
        ribbon(p, 'Foam', x, w, 4.2, 0.55, cols=1, off=-0.29)
    p.blob(B, 'Foam', (0.1, front_y(4.3, 0.1) - 0.3, 4.3), 0.3, (3.2, 0.8, 0.6), 0.08, 40, 9, 5)
    for i, x in enumerate((-0.75, -0.2, 0.35, 0.9)):  # splash where it lands
        p.blob(B, 'Foam', (x, front_y(0.45, x) - 0.35, 0.35), 0.32, (1, 0.8, 0.7), 0.15, 20 + i, 7, 5)
    # pool + stream
    p.cone(B, 'PoolDeep', (0.15, 1.2, 0.1), (0.15, 1.2, 0.16), 1.7, 1.7, seg=22, smooth=False)
    p.cone(B, 'Pool', (0.15, 1.2, 0.16), (0.15, 1.2, 0.2), 1.35, 1.35, seg=22, smooth=False)
    for i in range(9):
        a = i * 2 * math.pi / 9 + 0.3
        p.blob(B, 'Stone', (0.15 + math.cos(a) * 1.75, 1.2 + math.sin(a) * 1.5, 0.22), 0.28, (1, 1, 0.8), 0.18, 30 + i, 6, 4)
    strip(p, 'Pool', [(0.4, -0.4), (0.95, -1.1), (0.95, -1.9), (1.6, -2.8), (2.1, -4.3)], 0.76, 0.13)
    # forest
    for i, (x, y, h, r, m, m2) in enumerate([(-3.4, 0.6, 2.4, 1.0, 'Leaf2', 'Leaf'), (-3.7, -1.0, 1.9, 0.8, 'Leaf', 'Leaf3'), (3.5, 0.5, 2.6, 1.0, 'Leaf', 'Leaf2'),
                                             (3.6, -1.2, 1.8, 0.8, 'Leaf3', 'Leaf'), (-3.4, -2.5, 1.5, 0.65, 'Leaf', None), (3.0, -3.0, 2.0, 0.85, 'Leaf2', 'Leaf3'),
                                             (-1.6, 1.8, 1.7, 0.7, 'Leaf3', None), (1.9, 1.9, 1.8, 0.75, 'Leaf', 'Leaf2')]):
        round_tree(p, 'Trunk', m, (x, y, 0.1), h, r, i + 1, m2)
    for x, y in ((-0.9, 0.5), (1.4, 0.4), (-1.2, 2.2), (1.9, 1.0)):  # ferns
        for k in range(5):
            a = k * 2 * math.pi / 5
            p.blade(B, 'Leaf3', (x, y, 0.14), (x + math.cos(a) * 0.45, y + math.sin(a) * 0.45, 0.5), 0.16, 0.015, face=(0, 0, 1))
    for x, y in ((-1.4, -1.3), (-1.2, -1.6), (-0.9, -1.2), (2.9, -1.6), (3.1, -1.3)):
        p.sphere(B, 'Flower', (x, y, 0.18), 0.07, seg=5, rings=4)
    # park sign
    sx0, sy0 = -1.5, -2.7
    for sx in (-1, 1):
        p.cone(B, 'Wood', (sx0 + sx * 0.95, sy0, 0.1), (sx0 + sx * 0.95, sy0, 1.7), 0.07, 0.07, seg=5)
    p.box(B, 'Wood', (sx0, sy0, 1.3), (2.2, 0.12, 0.95))
    p.box(B, 'SignGreen', (sx0, sy0 - 0.07, 1.3), (1.9, 0.05, 0.7))
    p.box(B, 'SignYellow', (sx0, sy0 - 0.11, 1.45), (1.5, 0.03, 0.14))
    p.box(B, 'SignYellow', (sx0, sy0 - 0.11, 1.18), (1.1, 0.03, 0.1))
    p.box(B, 'Wood', (sx0, sy0, 1.86), (2.4, 0.3, 0.07))
    deer(p, (-1.3, -0.3), 25)
    # a dead snag with a great hornbill perched on it
    p.tube(B, 'Trunk', [(2.4, -0.8, 0.1), (2.35, -0.8, 1.0), (2.5, -0.75, 1.9)], [0.1, 0.08, 0.05], seg=5)
    p.tube(B, 'Trunk', [(2.38, -0.8, 1.2), (2.0, -0.85, 1.6)], [0.045, 0.025], seg=4)
    hornbill(p, (2.5, -0.75, 2.5), -50)
