"""Amphawa floating market: a canal between old wooden shophouses, boats laden with fruit, grilled seafood and noodles,
vendors in straw hats, an arched footbridge, an eating spot under an umbrella and a coconut ice-cream cart.
Unit 5 (food, buying and selling, daily life)."""
import math

from .common import B, gable, lantern, palm, parasol, plate, prism, rz

PALETTE = {
    'Water': '#4fae9c', 'Bank': '#c9a06a', 'Plank': '#a9774a', 'PlankDark': '#7a5232', 'Hull': '#6e4426',
    'WallTeal': '#5e9e8f', 'WallCream': '#efe1bf', 'WallBrown': '#a06a40', 'WallSalmon': '#e39b78', 'Roof': '#b8532e',
    'RoofDark': '#8c3d22', 'RoofGrey': '#857a72', 'Tin': '#a29c94', 'Interior': '#3a2a1e', 'Shutter': '#3f7a6a', 'Red': '#e0453a', 'White': '#fffaf0', 'Yellow': '#ffd23f',
    'Orange': '#ff8a2a', 'Green': '#5cb84a', 'Purple': '#8d4bb8', 'Hat': '#e8c872', 'Skin': '#f0b98a', 'ShirtBlue': '#3b82d6',
    'ShirtPink': '#f06a9a', 'ShirtGreen': '#3fae6a', 'Basket': '#c8964f', 'Ember': ('#ff6a2a', dict(emit='#ff4a10', es=2.0)),
    'Grill': '#2e2e2e', 'Steam': '#eef4f7', 'Palm': '#3fa84f', 'Trunk': '#8a6a3c', 'Cord': '#4a3520',
    'LanternRed': ('#ff5a3c', dict(emit='#ff3a1c', es=2.2)), 'LanternYellow': ('#ffd36a', dict(emit='#ffb020', es=2.2)),
    'Sign': '#2f6b3a', 'SignText': '#f2c94c',
}
RADIUS = 5.0
LABEL_Y = 5.0
CANAL = 1.1  # half-width of the canal, which runs along x through the middle
BANK = 0.26  # height of the walkways on both banks


def bank(p, side):
    """The walkway on one side of the canal (the part of the round base beyond |y| = CANAL) with a timber edge."""
    t0 = math.asin(CANAL / 5.0)
    angs = [t0 + (math.pi - 2 * t0) * i / 15 for i in range(16)]
    ring = [(5.0 * math.cos(a), side * 5.0 * math.sin(a)) for a in angs]
    prism(p, 'Bank', [(x, y, 0.0) for x, y in ring], [(x, y, BANK) for x, y in ring])
    p.box(B, 'PlankDark', (0, side * (CANAL + 0.05), BANK - 0.08), (2 * math.sqrt(25 - (CANAL + 0.12) ** 2), 0.12, 0.2))


def vendor(p, at, shirt_m, standing=False):
    """A vendor in a wide conical straw hat (ngob), sitting (or standing) at `at`."""
    x, y, z = at
    if standing:
        p.cone(B, 'Interior', (x, y, z), (x, y, z + 0.45), 0.12, 0.1, seg=6)
        z += 0.4
    p.sphere(B, shirt_m, (x, y, z + 0.2), 0.16, (1, 0.85, 1.25), seg=7, rings=5)
    p.sphere(B, 'Skin', (x, y, z + 0.47), 0.1, seg=7, rings=5)
    p.cone(B, 'Hat', (x, y, z + 0.5), (x, y, z + 0.68), 0.3, 0.0, seg=10, smooth=False)


def basket(p, c, fruit, r=0.2):
    """A round basket heaped with fruit."""
    x, y, z = c
    p.cone(B, 'Basket', (x, y, z), (x, y, z + 0.12), r * 0.75, r, seg=8)
    p.sphere(B, fruit, (x, y, z + 0.17), r * 0.4, seg=6, rings=4)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        p.sphere(B, fruit, (x + math.cos(a) * r * 0.48, y + math.sin(a) * r * 0.48, z + 0.13), r * 0.36, seg=6, rings=4)


def steam(p, x, y, z, seed):
    for k in range(3):
        p.blob(B, 'Steam', (x + 0.04 * (k % 2), y, z + 0.22 * k), 0.08 + 0.035 * k, (1, 1, 0.8), 0.15, seed + k, 6, 4)


def boat(p, c, yaw, s=1.0):
    """A wooden canal boat with upturned ends. Returns T(x, y, z), which places things on it: local y runs along the
    boat and its deck is at z = 0.25."""
    def T(x, y, z):
        return rz((x * s, y * s, z * s), yaw, c)
    side = [(0.34 * max(0.12, 1 - t * t) ** 0.55, t * 1.25) for t in (-1 + i / 4 for i in range(9))]
    outline = side + [(-hx, y) for hx, y in reversed(side)]
    prism(p, 'Hull', [T(hx * 0.6, y * 0.92, 0.0) for hx, y in outline], [T(hx, y, 0.24) for hx, y in outline])
    prism(p, 'Plank', [T(hx * 0.85, y * 0.88, 0.23) for hx, y in outline], [T(hx * 0.85, y * 0.88, 0.25) for hx, y in outline])
    for sy in (-1, 1):
        p.tube(B, 'Hull', [T(0, sy * 1.15, 0.2), T(0, sy * 1.33, 0.32), T(0, sy * 1.4, 0.46)], [0.05 * s, 0.04 * s, 0.025 * s], seg=5)
    return T


def shophouse(p, x, w, wall_m, trim_m, roof_m, goods):
    """A two-storey wooden shophouse on the far bank facing the canal: an open shop front with goods on a table,
    shuttered windows upstairs, a gable roof, a tin awning over the walkway with lanterns under it and a sign on it."""
    d, h, z0 = 1.5, 1.5, BANK
    y = CANAL + 0.75 + d / 2
    fy = y - d / 2
    p.box(B, wall_m, (x, y, z0 + h / 2), (w, d, h))
    p.box(B, 'Interior', (x, fy - 0.005, z0 + 0.4), (w - 0.45, 0.02, 0.66))
    for sx in (-1, 1):
        p.box(B, trim_m, (x + sx * (w / 2 - 0.12), fy - 0.03, z0 + 0.4), (0.2, 0.05, 0.7))
        p.box(B, 'Interior', (x + sx * 0.33, fy - 0.005, z0 + 1.2), (0.3, 0.02, 0.32))
        p.box(B, trim_m, (x + sx * 0.55, fy - 0.03, z0 + 1.2), (0.1, 0.04, 0.34))
    gable(p, roof_m, (x, y, z0 + h), w, d, 0.6, 0.18, 0, 0.0, panel_m=wall_m, inset=0.14)
    za, zb = z0 + 0.95, z0 + 0.78
    hw = w / 2 + 0.05
    p.poly(B, 'Tin', [(x - hw, fy, za), (x + hw, fy, za), (x + hw, fy - 0.62, zb), (x - hw, fy - 0.62, zb)], [(0, 3, 2, 1)])
    for sx in (-1, 1):
        p.cone(B, 'PlankDark', (x + sx * (w / 2 - 0.02), fy - 0.58, z0), (x + sx * (w / 2 - 0.02), fy - 0.58, zb), 0.03, 0.03, seg=4)
        lantern(p, 'LanternRed' if sx < 0 else 'LanternYellow', (x + sx * w * 0.25, fy - 0.45, zb - 0.12), 0.1, 'Cord', 0.19)
    p.box(B, 'Plank', (x, fy - 0.28, z0 + 0.3), (w - 0.5, 0.32, 0.05))
    for sx in (-1, 1):
        p.box(B, 'PlankDark', (x + sx * (w / 2 - 0.32), fy - 0.28, z0 + 0.14), (0.05, 0.28, 0.28))
    for i in range(5):
        gx = x - (w - 0.7) / 2 + (w - 0.7) * i / 4
        m = goods[i % len(goods)]
        if i % 2:
            p.sphere(B, m, (gx, fy - 0.28, z0 + 0.4), 0.08, seg=6, rings=4)
        else:
            p.box(B, m, (gx, fy - 0.28, z0 + 0.39), (0.14, 0.14, 0.13))
    p.box(B, 'Sign', (x, fy - 0.64, zb + 0.18), (w * 0.55, 0.04, 0.22))
    p.box(B, 'SignText', (x, fy - 0.665, zb + 0.18), (w * 0.4, 0.02, 0.07))


def footbridge(p, x):
    """An arched wooden footbridge over the canal at x."""
    ys = [-CANAL - 0.45, -0.8, -0.3, 0.3, 0.8, CANAL + 0.45]
    zs = [BANK, 0.7, 0.92, 0.92, 0.7, BANK]
    for (y0, z0), (y1, z1) in zip(zip(ys, zs), zip(ys[1:], zs[1:])):
        L = math.hypot(y1 - y0, z1 - z0)
        ang = math.degrees(math.atan2(z1 - z0, y1 - y0))
        p.box(B, 'Plank', (x, (y0 + y1) / 2, (z0 + z1) / 2), (0.85, L + 0.02, 0.07), rot=(ang, 0, 0))
    for sx in (-1, 1):
        rail = [(x + sx * 0.4, y, z + 0.42) for y, z in zip(ys, zs)]
        p.tube(B, 'PlankDark', rail, 0.025, seg=4)
        for rx, ry, rzz in rail:
            p.cone(B, 'PlankDark', (rx, ry, rzz - 0.42), (rx, ry, rzz + 0.03), 0.03, 0.03, seg=4)
    for y in (-0.55, 0.55):  # piles in the water
        for sx in (-1, 1):
            p.cone(B, 'PlankDark', (x + sx * 0.35, y, 0.0), (x + sx * 0.35, y, 0.82), 0.045, 0.045, seg=5)


def cart(p, c):
    """A coconut ice-cream cart with a striped canopy."""
    x, y = c
    z = BANK
    p.box(B, 'WallCream', (x, y, z + 0.5), (1.0, 0.5, 0.45))
    p.box(B, 'Red', (x, y - 0.255, z + 0.5), (1.0, 0.02, 0.1))
    for sx in (-1, 1):
        p.cone(B, 'Grill', (x + sx * 0.32, y - 0.27, z + 0.18), (x + sx * 0.32, y - 0.2, z + 0.18), 0.16, 0.16, seg=10)
        p.cone(B, 'PlankDark', (x + sx * 0.46, y, z + 0.72), (x + sx * 0.46, y, z + 1.35), 0.025, 0.025, seg=4)
    p.box(B, 'Red', (x, y, z + 1.38), (1.15, 0.65, 0.05))
    p.box(B, 'White', (x, y - 0.33, z + 1.31), (1.15, 0.02, 0.1))
    for gx in (-0.28, 0.0, 0.28):
        p.sphere(B, 'Green', (x + gx, y + 0.05, z + 0.83), 0.12, (1, 1, 0.9), seg=7, rings=5)


def build(p):
    plate(p, 'Water', (0, 0, 0), 4.98, 0.1)
    bank(p, 1)
    bank(p, -1)
    # the far bank: a row of shophouses facing the canal
    for x, wall, trim, roof, goods in ((-2.5, 'WallTeal', 'PlankDark', 'Roof', ('Orange', 'Yellow', 'Red')),
                                       (-0.85, 'WallCream', 'Shutter', 'RoofGrey', ('Green', 'Purple', 'Yellow')),
                                       (0.8, 'WallBrown', 'Shutter', 'RoofDark', ('Red', 'Orange', 'White')),
                                       (2.45, 'WallSalmon', 'PlankDark', 'RoofGrey', ('Yellow', 'Green', 'Orange'))):
        shophouse(p, x, 1.55, wall, trim, roof, goods)
    footbridge(p, -4.0)
    # a fruit boat
    T = boat(p, (-1.75, 0.3, 0.02), 90)
    vendor(p, T(0, 0.85, 0.25), 'ShirtBlue')
    for y, fruit in ((-0.75, 'Orange'), (-0.28, 'Red'), (0.2, 'Yellow')):
        basket(p, T(0, y, 0.25), fruit)
    # a boat grilling seafood under an umbrella
    T = boat(p, (0.9, -0.35, 0.02), 84)
    vendor(p, T(0, 0.85, 0.25), 'ShirtPink')
    g = T(0, -0.25, 0.25)
    p.box(B, 'Grill', (g[0], g[1], g[2] + 0.1), (0.36, 0.46, 0.2), rot=(0, 0, 84))
    p.box(B, 'Ember', (g[0], g[1], g[2] + 0.205), (0.3, 0.4, 0.02), rot=(0, 0, 84))
    for k in (-0.12, 0.0, 0.12):
        p.tube(B, 'Plank', [T(-0.22, -0.25 + k, 0.47), T(0.22, -0.25 + k, 0.47)], 0.008, seg=3)
        for j in (-0.1, 0.0, 0.1):
            p.sphere(B, 'Orange', T(j, -0.25 + k, 0.47), 0.035, seg=5, rings=3)
    steam(p, g[0], g[1], g[2] + 0.6, 5)
    parasol(p, 'PlankDark', 'Red', 'White', T(0.2, 0.55, 0.25), 0.95, 0.55)
    # a noodle boat
    T = boat(p, (3.35, 0.45, 0.02), 98, 0.88)
    vendor(p, T(0, 0.85, 0.25), 'ShirtGreen')
    c = T(0, -0.3, 0.25)
    p.cone(B, 'Grill', c, (c[0], c[1], c[2] + 0.22), 0.15, 0.15, seg=10)
    p.cone(B, 'Orange', (c[0], c[1], c[2] + 0.22), (c[0], c[1], c[2] + 0.225), 0.13, 0.13, seg=10)
    steam(p, c[0], c[1], c[2] + 0.45, 9)
    for j in (0.15, 0.4):
        b = T(0, j, 0.25)
        p.cone(B, 'White', b, (b[0], b[1], b[2] + 0.07), 0.05, 0.09, seg=8)
    # the near bank: an eating spot, an ice-cream cart, crates of fruit and palms
    parasol(p, 'PlankDark', 'Red', 'White', (-1.6, -2.45, BANK), 1.45, 0.85)
    p.cone(B, 'Plank', (-1.6, -2.45, BANK + 0.5), (-1.6, -2.45, BANK + 0.55), 0.42, 0.42, seg=10)
    for k in range(3):
        a = math.radians(90 + k * 120)
        sx, sy = -1.6 + math.cos(a) * 0.62, -2.45 + math.sin(a) * 0.62
        p.cone(B, 'Red', (sx, sy, BANK), (sx, sy, BANK + 0.32), 0.13, 0.13, seg=8)
    vendor(p, (-1.6 + math.cos(math.radians(210)) * 0.62, -2.45 + math.sin(math.radians(210)) * 0.62, BANK + 0.27), 'ShirtBlue')
    for dx in (-0.15, 0.15):
        p.cone(B, 'White', (-1.6 + dx, -2.5, BANK + 0.55), (-1.6 + dx, -2.5, BANK + 0.61), 0.05, 0.09, seg=8)
    cart(p, (1.4, -2.5))
    vendor(p, (1.4, -2.05, BANK), 'ShirtPink', standing=True)
    for x, y, fruit in ((-0.25, -1.6, 'Orange'), (2.9, -1.55, 'Green'), (-2.9, -1.6, 'Yellow')):
        p.box(B, 'Plank', (x, y, BANK + 0.11), (0.42, 0.32, 0.22))
        basket(p, (x, y, BANK + 0.22), fruit, 0.17)
    palm(p, 'Trunk', 'Palm', (-3.5, -2.6, BANK), 2.3, (0.3, 0.2), 6, 0.95, 0.5)
    palm(p, 'Trunk', 'Palm', (3.6, -2.3, BANK), 2.1, (-0.3, 0.2), 6, 0.9, 1.7)
