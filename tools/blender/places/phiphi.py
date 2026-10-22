"""Phi Phi Islands (Maya Bay): a turquoise lagoon walled in by limestone cliffs, a white-sand beach with palms, a striped
umbrella and a lifeguard tower, a ferry, a longtail boat, kayaks and a swimmer in a ring. Unit 4 (around town: getting about by boat)."""
import math

from .common import B, karst, longtail, palm, parasol, plate, prism, rz

PALETTE = {
    'Sea': '#1fb6d4', 'Shallow': '#7ce8dc', 'Sand': '#fbeec2', 'Rock': '#948d7c', 'RockLight': '#c3bba5', 'Moss': '#4d9e50',
    'Moss2': '#2e7d42', 'Palm': '#3fa84f', 'Trunk': '#8a6a3c', 'Foam': '#eafcff', 'White': '#ffffff', 'HullBlue': '#1f5fc0',
    'Deck': '#caa676', 'Glass': '#27496f', 'Red': '#e0453a', 'Yellow': '#ffd23f', 'Orange': '#ff8a2a', 'Blue': '#3b82d6',
    'Wood': '#ab7640', 'Pink': '#ff7aa8', 'Skin': '#f0b98a', 'Dark': '#2a2a2a',
}
RADIUS = 5.0
LABEL_Y = 6.0
BEACH = (0.0, 2.6, 0.1, 3.3, 1.76, 0.3)  # the sand mound: centre x, y, z, semi-axes x, y and its height


def sand_z(x, y):
    """Height of the beach at (x, y)."""
    cx, cy, cz, ax, ay, hz = BEACH
    t = 1 - ((x - cx) / ax) ** 2 - ((y - cy) / ay) ** 2
    return cz + hz * math.sqrt(t) if t > 0 else cz


def ferry(p, c, yaw):
    """A two-deck passenger ferry, white over a blue hull; bow towards local -y."""
    def T(x, y, z):
        return rz((x, y, z), yaw, c)
    outline = [(-0.45, 1.2), (0.45, 1.2), (0.47, -0.6), (0.0, -1.45), (-0.47, -0.6)]

    def ring(z, k=1.0):
        return [T(x * k, y, z) for x, y in outline]
    prism(p, 'HullBlue', ring(0.0, 0.7), ring(0.2))
    prism(p, 'White', ring(0.2), ring(0.5, 1.05))
    prism(p, 'Deck', ring(0.5, 0.97), ring(0.54, 0.97))
    p.box(B, 'White', T(0, 0.3, 0.82), (0.74, 1.15, 0.56), rot=(0, 0, yaw))
    p.box(B, 'Glass', T(0, 0.3, 0.88), (0.77, 1.0, 0.18), rot=(0, 0, yaw))
    p.box(B, 'Glass', T(0, -0.27, 0.88), (0.6, 0.04, 0.18), rot=(0, 0, yaw))
    p.box(B, 'White', T(0, 0.1, 1.24), (0.6, 0.72, 0.3), rot=(0, 0, yaw))
    p.box(B, 'Glass', T(0, 0.1, 1.26), (0.63, 0.6, 0.13), rot=(0, 0, yaw))
    p.box(B, 'HullBlue', T(0, 0.1, 1.42), (0.7, 0.85, 0.05), rot=(0, 0, yaw))
    p.cone(B, 'Red', T(0, 0.82, 1.1), T(0, 0.82, 1.5), 0.12, 0.1, seg=6)
    p.cone(B, 'Dark', T(0, 0.82, 1.5), T(0, 0.82, 1.54), 0.1, 0.1, seg=6)
    p.cone(B, 'White', T(0, -0.1, 1.45), T(0, -0.1, 1.95), 0.02, 0.015, seg=4)
    p.blade(B, 'Red', T(0, -0.1, 1.92), T(0.32, -0.1, 1.86), 0.18, 0.015, face=rz((0, 1, 0), yaw), peak=0.5)


def kayak(p, c, yaw, hull_m, shirt_m, hat_m):
    """A sea kayak with a paddler in a straw hat and a double-bladed paddle."""
    def T(x, y, z):
        return rz((x, y, z), yaw, c)
    p.sphere(B, hull_m, T(0, 0, 0.1), 1.0, (0.17, 0.95, 0.1), seg=9, rings=5, rot=(0, 0, yaw))
    p.box(B, 'Dark', T(0, 0.05, 0.19), (0.2, 0.42, 0.03), rot=(0, 0, yaw))
    p.sphere(B, shirt_m, T(0, 0.05, 0.38), 0.15, (1, 0.8, 1.3), seg=7, rings=5, rot=(0, 0, yaw))
    p.sphere(B, 'Skin', T(0, 0.05, 0.62), 0.09, seg=6, rings=4)
    p.cone(B, hat_m, T(0, 0.05, 0.66), T(0, 0.05, 0.78), 0.15, 0.0, seg=8)
    p.tube(B, 'Wood', [T(-0.62, 0.02, 0.5), T(0.62, 0.12, 0.28)], 0.016, seg=4)
    p.blade(B, 'Red', T(-0.6, 0.02, 0.5), T(-0.85, 0.0, 0.58), 0.12, 0.02, face=(0, 0, 1))
    p.blade(B, 'Red', T(0.6, 0.12, 0.28), T(0.85, 0.14, 0.2), 0.12, 0.02, face=(0, 0, 1))


def swimmer(p, c):
    """A snorkeller floating in a pink ring."""
    x, y = c
    p.torus(B, 'Pink', (x, y, 0.15), 0.3, 0.1, seg=12, minor=6)
    p.sphere(B, 'Skin', (x, y, 0.22), 0.1, seg=6, rings=4)
    p.box(B, 'Dark', (x, y - 0.09, 0.24), (0.14, 0.04, 0.07))
    p.tube(B, 'Yellow', [(x + 0.06, y - 0.04, 0.26), (x + 0.1, y - 0.02, 0.5)], 0.015, seg=4)
    for sx in (-1, 1):
        p.tube(B, 'Skin', [(x + sx * 0.1, y, 0.16), (x + sx * 0.38, y - 0.12, 0.2)], 0.03, seg=4)


def tower(p, c):
    """A lifeguard tower on stilts with a red roof and a flag, standing on the sand."""
    x, y = c
    z = sand_z(x, y) - 0.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cone(B, 'Wood', (x + sx * 0.32, y + sy * 0.32, z), (x + sx * 0.32, y + sy * 0.32, z + 0.85), 0.045, 0.045, seg=5)
            p.cone(B, 'Wood', (x + sx * 0.3, y + sy * 0.3, z + 0.85), (x + sx * 0.3, y + sy * 0.3, z + 1.65), 0.03, 0.03, seg=4)
    p.box(B, 'Wood', (x, y, z + 0.85), (0.85, 0.85, 0.07))
    p.box(B, 'White', (x, y - 0.3, z + 1.08), (0.7, 0.05, 0.36))
    p.cone(B, 'Red', (x, y, z + 1.62), (x, y, z + 2.0), 0.72, 0.05, seg=4, smooth=False)
    p.cone(B, 'Wood', (x, y, z + 2.0), (x, y, z + 2.55), 0.02, 0.02, seg=4)
    p.blade(B, 'Red', (x, y, z + 2.5), (x + 0.4, y, z + 2.42), 0.22, 0.02, face=(0, 1, 0), peak=0.5)


def build(p):
    plate(p, 'Sea', (0, 0, 0), 5.0, 0.1)
    plate(p, 'Shallow', (0, 0.9, 0.1), 3.2, 0.02)
    cx, cy, cz, ax, ay, hz = BEACH
    p.blob(B, 'Sand', (cx, cy, cz), 1.0, (ax, ay, hz), 0.012, 5, 14, 6, flat_bottom=True)
    # a wall of cliffs round the back and sides of the lagoon; the front is open water for the boats
    for i, (a, h) in enumerate(((172, 3.3), (147, 4.1), (122, 4.7), (97, 4.3), (72, 4.8), (47, 4.0), (22, 3.4))):
        t = math.radians(a)
        karst(p, (math.cos(t) * 3.55, 0.3 + math.sin(t) * 3.55), 0.95, h, 10 + i * 7, yaw=a + 90, stretch=1.45)
    karst(p, (-3.6, -2.0), 0.75, 2.5, 90)
    karst(p, (3.45, -2.25), 0.7, 2.0, 97)
    # beach life
    for (x, y), h, lean, seed in (((-1.7, 1.75), 2.5, (0.4, -0.25), 0.4), ((-0.45, 2.3), 2.8, (-0.3, 0.2), 1.3), ((0.95, 2.0), 2.3, (0.35, -0.2), 2.2)):
        palm(p, 'Trunk', 'Palm', (x, y, sand_z(x, y) - 0.05), h, lean, 7, 1.0, seed)
    parasol(p, 'Wood', 'Yellow', 'White', (-1.0, 1.35, sand_z(-1.0, 1.35) - 0.05), 1.3, 0.75)
    p.box(B, 'Blue', (-0.3, 1.55, sand_z(-0.3, 1.55)), (0.45, 0.8, 0.03), rot=(0, 0, 25))
    tower(p, (1.7, 1.6))
    # boats and swimmers
    ferry(p, (1.3, -1.4, 0.1), -70)
    longtail(p, 'HullBlue', 'Red', 'Wood', ('Red', 'Yellow', 'Blue'), (-1.0, -3.0, 0.1), 100, 0.9)
    kayak(p, (-0.7, 0.2, 0.1), 25, 'Orange', 'Red', 'Yellow')
    kayak(p, (0.5, -0.4, 0.1), -35, 'Yellow', 'Blue', 'White')
    swimmer(p, (-1.8, -1.0))
    for c, m in (((2.3, 0.1), 'Red'), ((-0.4, -3.7), 'Yellow'), ((-2.2, -0.3), 'Red')):
        p.sphere(B, m, (c[0], c[1], 0.18), 0.14, seg=7, rings=5)
