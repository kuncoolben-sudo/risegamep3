"""Phuket: a turquoise bay with limestone karst islands, a sandy beach with palms and an umbrella, a wooden pier and
longtail boats. Unit 7 (beach activities, hobbies)."""
import math

from .common import B, karst, longtail, palm, parasol, plate, rz

PALETTE = {
    'Sea': '#2fc2d6', 'Shallow': '#6fe3da', 'Sand': '#f4e0ac', 'SandDark': '#e2c685', 'Rock': '#8d8779', 'RockLight': '#b5ae9a',
    'Moss': '#4b9c50', 'Moss2': '#2f7d43', 'Wood': '#ab7640', 'DarkWood': '#7a4a24', 'Trunk': '#8a6a3c', 'Palm': '#3fa84f',
    'Red': '#e0453a', 'Yellow': '#ffd23f', 'Blue': '#3b82d6', 'White': '#ffffff', 'HullBlue': '#2f6fd0', 'Foam': '#e6fbff',
    'Lamp': ('#ffe9a8', dict(emit='#ffd060', es=1.5)),
}
RADIUS = 5.0
LABEL_Y = 5.2


def lighthouse(p, c):
    """A white lighthouse with red bands on a rocky point (Promthep Cape)."""
    x, y = c
    p.blob(B, 'Rock', (x, y, 0.25), 0.75, (1.1, 0.9, 0.55), 0.12, 41, 8, 5)
    p.blob(B, 'RockLight', (x - 0.25, y - 0.3, 0.3), 0.4, (1, 0.8, 0.6), 0.12, 42, 7, 4)
    p.blob(B, 'Foam', (x, y, 0.1), 1.0, (0.85, 0.72, 0.05), 0.03, 43, 10, 3)
    z, h = 0.55, 1.5
    p.cone(B, 'White', (x, y, z), (x, y, z + h), 0.27, 0.19, seg=10)
    for f in (0.25, 0.62):
        p.cone(B, 'Red', (x, y, z + h * f), (x, y, z + h * f + 0.2), 0.282 - 0.08 * f, 0.282 - 0.08 * (f + 0.2 / h), seg=10)
    p.cone(B, 'Red', (x, y, z + h), (x, y, z + h + 0.06), 0.3, 0.3, seg=10)
    p.cone(B, 'Lamp', (x, y, z + h + 0.06), (x, y, z + h + 0.3), 0.15, 0.15, seg=8)
    p.cone(B, 'Red', (x, y, z + h + 0.3), (x, y, z + h + 0.52), 0.2, 0.0, seg=8)


def sandcastle(p, c):
    x, y, z = c
    p.box(B, 'SandDark', (x, y, z + 0.1), (0.5, 0.4, 0.2))
    for sx in (-1, 1):
        p.cone(B, 'SandDark', (x + sx * 0.25, y - 0.2, z), (x + sx * 0.25, y - 0.2, z + 0.38), 0.11, 0.09, seg=6)
        p.cone(B, 'SandDark', (x + sx * 0.25, y - 0.2, z + 0.38), (x + sx * 0.25, y - 0.2, z + 0.5), 0.1, 0.0, seg=6)
    p.cone(B, 'DarkWood', (x, y, z + 0.2), (x, y, z + 0.6), 0.012, 0.012, seg=4)
    p.blade(B, 'Red', (x, y, z + 0.58), (x + 0.2, y, z + 0.54), 0.12, 0.01, face=(0, 1, 0), peak=0.5)


def beach_ball(p, c, r=0.15):
    x, y, z = c
    p.sphere(B, 'Yellow', (x, y, z + r), r, seg=10, rings=7)
    p.torus(B, 'Red', (x, y, z + r), r * 1.0, r * 0.18, seg=14, minor=4)
    p.torus(B, 'Blue', (x, y, z + r), r * 1.0, r * 0.18, rot=(90, 0, 30), seg=14, minor=4)


def build(p):
    plate(p, 'Sea', (0, 0, 0), 5.0, 0.1)
    plate(p, 'Shallow', (-1.6, -1.6, 0.1), 3.1, 0.02)
    # beach
    p.blob(B, 'Sand', (-2.1, -2.1, 0.1), 2.1, (1.35, 1.0, 0.2), 0.05, 3, 11, 5, flat_bottom=True)
    p.blob(B, 'SandDark', (-2.6, -1.4, 0.16), 1.0, (1.2, 0.8, 0.15), 0.06, 8, 8, 4)
    # karst islands
    karst(p, (2.3, 2.4), 1.25, 3.6, 1)
    karst(p, (3.5, 0.3), 0.85, 2.4, 11)
    karst(p, (-0.9, 3.5), 0.8, 2.0, 21)
    # palms and parasol
    palm(p, 'Trunk', 'Palm', (-3.0, -2.5, 0.2), 2.8, (0.55, 0.2), 7, 1.1, 0.3)
    palm(p, 'Trunk', 'Palm', (-1.9, -3.2, 0.2), 2.3, (-0.4, 0.3), 7, 1.0, 1.1)
    palm(p, 'Trunk', 'Palm', (-3.4, -1.2, 0.2), 2.0, (0.3, -0.35), 6, 0.95, 2.0)
    parasol(p, 'DarkWood', 'Red', 'White', (-1.4, -1.8, 0.2), 1.3, 0.85)
    p.box(B, 'Blue', (-1.0, -2.3, 0.3), (0.5, 0.8, 0.08), rot=(25, 0, 20))
    p.box(B, 'Yellow', (-0.5, -2.2, 0.3), (0.5, 0.8, 0.08), rot=(25, 0, 20))
    # pier from the beach out over the bay
    a, b = (-0.6, -1.2), (2.0, -0.5)
    yaw = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    p.box(B, 'Wood', (mid[0], mid[1], 0.55), (length, 0.75, 0.08), rot=(0, 0, yaw))
    n = int(length / 0.65)
    for i in range(n + 1):
        u = i / n
        x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        for sy in (-1, 1):
            q = rz((0, sy * 0.33, 0), yaw, (x, y, 0))
            p.cone(B, 'DarkWood', (q[0], q[1], 0.08), (q[0], q[1], 0.52), 0.06, 0.06, seg=5)
            p.cone(B, 'DarkWood', (q[0], q[1], 0.58), (q[0], q[1], 1.08), 0.035, 0.035, seg=4)
    for sy in (-1, 1):
        s0, s1 = rz((-length / 2, sy * 0.33, 1.02), yaw, (mid[0], mid[1], 0)), rz((length / 2, sy * 0.33, 1.02), yaw, (mid[0], mid[1], 0))
        p.tube(B, 'Wood', [s0, s1], 0.03, seg=4)
    end = rz((length / 2 + 0.05, 0, 0), yaw, (mid[0], mid[1], 0))
    p.cone(B, 'DarkWood', (end[0], end[1], 0.58), (end[0], end[1], 1.9), 0.04, 0.04, seg=5)
    p.cone(B, 'Yellow', (end[0], end[1], 1.75), (end[0], end[1], 2.15), 0.7, 0.05, seg=8, smooth=False)
    # boats and buoys
    longtail(p, 'HullBlue', 'Red', 'Wood', ('Red', 'Yellow', 'Blue'), (1.5, -2.9, 0.1), 75, 1.0)
    longtail(p, 'Red', 'Yellow', 'Wood', ('Blue', 'White', 'Yellow'), (0.0, 0.9, 0.1), 105, 0.9)
    for c, m in (((0.3, 2.6), 'Red'), ((2.5, -1.5), 'White'), ((0.6, -3.6), 'Red')):
        p.sphere(B, m, (c[0], c[1], 0.18), 0.14, seg=7, rings=5)
    # holiday things on the beach and the lighthouse on the cape
    sandcastle(p, (-2.4, -1.3, 0.44))
    beach_ball(p, (-1.0, -2.7, 0.42))
    lighthouse(p, (3.5, -1.7))
