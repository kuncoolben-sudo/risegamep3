"""Doi Inthanon, the roof of Thailand: a mountain wrapped in cloud with the twin royal pagodas on its summit, flower
gardens, pines, a stone stairway and a red songthaew waiting at its foot. Unit 2 (weather, seasons, travel)."""
import math

from .common import B, pine, plate, rz, slab, spire

PALETTE = {
    'GrassLow': '#6bb85a', 'Grass': '#7cc65e', 'GrassHigh': '#8fd06b', 'Rock': '#8c8678', 'Stone': '#e4ddcc', 'Step': '#cfc6b0',
    'PagodaA': '#a9bfae', 'PagodaB': '#c9a9a8', 'Trim': '#f4efe2', 'Gold': ('#f2bb32', dict(rough=0.35, emit='#c98a10', es=0.3)),
    'GoldDark': ('#d9992a', dict(rough=0.4, emit='#a8700c', es=0.2)), 'Pine': '#2f7d4a', 'Pine2': '#3f9a58', 'Trunk': '#6b4a2b',
    'Cloud': '#ffffff', 'CloudShade': '#dde8f4', 'Pink': '#ff7aa8', 'Purple': '#a56be0', 'Yellow': '#ffd23f', 'Red': '#e0453a',
    'White': '#ffffff', 'Glass': '#27496f', 'Dark': '#2a2a2a', 'Wood': '#8a5a2b', 'SignGreen': '#2f6b3a',
}
RADIUS = 5.0
LABEL_Y = 7.8
HILL = [(4.3, 0.1), (3.8, 0.55), (3.2, 1.35), (2.65, 2.15), (2.3, 2.75), (2.15, 3.0), (0.0, 3.06)]  # (radius, height), foot to summit
TOP = 3.08  # the summit terrace
FLOWERS = ('Pink', 'Purple', 'Yellow', 'Red')


def hill_z(x, y):
    """Height of the mountain's surface at (x, y)."""
    r = math.hypot(x, y)
    if r >= HILL[0][0]:
        return 0.1
    for (r0, z0), (r1, z1) in zip(HILL, HILL[1:]):
        if r1 <= r <= r0:
            return z0 + (z1 - z0) * (r0 - r) / (r0 - r1)
    return HILL[-1][1]


def pagoda(p, c, body_m, r=0.56, h=1.8):
    """A royal pagoda: octagonal terraces, a tall bell-shaped body with gilded bands and doorways and a golden spire."""
    x, y, z = c
    p.lathe(B, 'Trim', [(r * 1.4, 0), (r * 1.4, 0.16), (r * 1.22, 0.16), (r * 1.22, 0.3), (r * 1.08, 0.3), (r * 1.08, 0.42), (0, 0.42)], (x, y, z), seg=8, rot=22.5)
    zb = z + 0.42
    prof = [(r, 0), (r, h * 0.12), (r * 1.06, h * 0.2), (r, h * 0.38), (r * 0.82, h * 0.55), (r * 0.55, h * 0.7), (r * 0.3, h * 0.8), (r * 0.18, h * 0.84)]
    p.lathe(B, body_m, prof, (x, y, zb), seg=12, smooth=True, caps=False)
    for f, k in ((0.12, 1.03), (0.3, 1.05)):
        p.cone(B, 'Gold', (x, y, zb + h * f), (x, y, zb + h * f + 0.05), r * k, r * k, seg=12)
    spire(p, 'Gold', (x, y, zb + h * 0.82), r * 0.3, h * 0.55, tiers=4, seg=8, tip_m='Gold')
    for k in range(4):
        a = math.radians(k * 90 - 90)
        size = (0.24, 0.05, 0.34) if k % 2 == 0 else (0.05, 0.24, 0.34)
        p.box(B, 'GoldDark', (x + math.cos(a) * r * 1.01, y + math.sin(a) * r * 1.01, zb + 0.2), size)


def cloud(p, c, s, seed):
    x, y, z = c
    for i, (dx, dy, dz, r) in enumerate(((0, 0, 0, 0.55), (0.55, 0.1, -0.08, 0.42), (-0.55, -0.05, -0.1, 0.4), (0.2, -0.32, -0.14, 0.36), (-0.2, 0.3, 0.06, 0.38))):
        p.blob(B, 'CloudShade' if dz < -0.09 else 'Cloud', (x + dx * s, y + dy * s, z + dz * s), r * s, (1.25, 1.0, 0.72), 0.08, seed + i, 8, 5)


def songthaew(p, c, yaw):
    """A red songthaew (a pick-up with a roofed bench seat in the back); its cab faces local +x."""
    def T(x, y, z):
        return rz((x, y, z), yaw, c)
    rot = (0, 0, yaw)
    p.box(B, 'Red', T(0, 0, 0.36), (1.3, 0.56, 0.26), rot=rot)
    p.box(B, 'Red', T(0.42, 0, 0.66), (0.42, 0.54, 0.36), rot=rot)
    p.box(B, 'Glass', T(0.635, 0, 0.7), (0.02, 0.46, 0.2), rot=rot)
    for sy in (-1, 1):
        p.box(B, 'Glass', T(0.45, sy * 0.275, 0.72), (0.26, 0.02, 0.16), rot=rot)
    p.box(B, 'White', T(-0.22, 0, 0.98), (0.86, 0.62, 0.05), rot=rot)
    for px in (-0.6, 0.15):
        for sy in (-1, 1):
            q = T(px, sy * 0.27, 0)
            p.cone(B, 'White', (q[0], q[1], c[2] + 0.49), (q[0], q[1], c[2] + 0.96), 0.02, 0.02, seg=4)
    for px in (-0.38, 0.4):
        for sy in (-1, 1):
            p.cone(B, 'Dark', T(px, sy * 0.25, 0.2), T(px, sy * 0.33, 0.2), 0.16, 0.16, seg=10)
    p.box(B, 'Yellow', T(0.67, 0, 0.42), (0.02, 0.4, 0.08), rot=rot)


def sign(p, c):
    x, y, z = c
    for sx in (-1, 1):
        p.cone(B, 'Wood', (x + sx * 0.45, y, z), (x + sx * 0.45, y, z + 1.0), 0.04, 0.04, seg=5)
    p.box(B, 'SignGreen', (x, y - 0.02, z + 0.78), (1.1, 0.06, 0.42))
    p.box(B, 'Yellow', (x, y - 0.06, z + 0.85), (0.8, 0.02, 0.08))
    p.box(B, 'White', (x, y - 0.06, z + 0.7), (0.55, 0.02, 0.06))


def build(p):
    plate(p, 'GrassLow', (0, 0, 0), 5.0, 0.1)
    p.lathe(B, 'Grass', [(HILL[0][0], 0.0)] + HILL, (0, 0, 0), seg=18, rot=10)
    p.blob(B, 'GrassHigh', (2.5, 1.9, 1.0), 1.0, (1.5, 1.2, 1.3), 0.1, 3, 9, 6)  # shoulders of the mountain
    p.blob(B, 'Grass', (-2.6, 1.5, 1.1), 1.0, (1.3, 1.4, 1.3), 0.1, 7, 9, 6)
    # the summit: a paved terrace with the twin pagodas, a sign and clipped bushes
    plate(p, 'Stone', (0, 0, TOP - 0.08), 2.12, 0.08)
    pagoda(p, (-0.95, 0.3, TOP), 'PagodaA')
    pagoda(p, (0.95, 0.3, TOP), 'PagodaB')
    sign(p, (1.45, -1.3, TOP))
    for x, y in ((0.0, 1.35), (-1.85, -0.5), (1.85, 0.9)):
        p.blob(B, 'Pine2', (x, y, TOP + 0.12), 0.2, (1, 1, 0.9), 0.1, int(x * 5 + 9), 7, 5)
    for i in range(24):  # flowers round the terrace, leaving the top of the stairs clear
        if i == 18:
            continue
        a = math.radians(i * 15)
        x, y = math.cos(a) * 2.32, math.sin(a) * 2.32
        p.sphere(B, FLOWERS[i % 4], (x, y, hill_z(x, y) + 0.06), 0.12, seg=5, rings=3, smooth=False)
    # a stone stairway up the front, lined with flowers
    for i in range(15):
        y = -4.55 + i * 0.18
        slab(p, 'Step', (0, y, hill_z(0, y) - 0.38), 0.86, 0.2, 0.45)
    for i in range(1, 14, 2):
        y = -4.55 + i * 0.18
        for sx in (-1, 1):
            x = sx * 0.62
            p.sphere(B, FLOWERS[(i // 2 + (sx > 0)) % 4], (x, y, hill_z(x, y) + 0.05), 0.12, seg=5, rings=3, smooth=False)
    # pines and rocks on the slopes
    for i, (x, y, h) in enumerate(((-3.4, -0.6, 1.7), (-1.7, -3.0, 1.4), (1.8, -3.3, 1.6), (3.0, -1.9, 1.8), (3.5, 0.3, 1.5),
                                   (0.6, 3.6, 1.7), (-1.3, 3.5, 1.5), (-2.7, -2.2, 1.3), (2.4, -2.7, 1.2))):
        pine(p, 'Trunk', 'Pine' if i % 2 else 'Pine2', (x, y, hill_z(x, y) - 0.08), h, 0.48 + h * 0.05, 3)
    for x, y, r, seed in ((-2.0, -1.7, 0.4, 1), (2.4, -1.4, 0.35, 2), (-3.4, 0.9, 0.45, 3)):
        p.blob(B, 'Rock', (x, y, hill_z(x, y)), r, (1.2, 1.0, 0.8), 0.15, seed, 7, 5)
    # clouds hugging the mountain
    cloud(p, (-3.3, -1.6, 1.8), 1.0, 1)
    cloud(p, (3.35, -1.1, 2.1), 0.9, 11)
    cloud(p, (-2.2, 3.0, 3.2), 1.0, 21)
    cloud(p, (2.4, 2.9, 2.9), 0.9, 31)
    # the tour truck waiting on the road at the foot
    songthaew(p, (-3.05, -3.45, 0.1), -41.5)
