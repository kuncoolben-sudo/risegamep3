"""Where everything on the island is, and how high and what colour the ground is at any point.

Blender coordinates: x east, y north (away from the game camera; three.js z is -y), z up, 1 unit = 1 game unit.
The places and roads of the map all lie within y in [-17, 17] and the player walks inside WALK_R, so the features that
stand inside that circle (a lake under a waterfall, mountains and two forest hills) are kept to the north, where the
camera sees them past the places. The rest rings the island: beaches, west cliffs with a cave, a fishing village and
pier in the east, a bridge to an islet in the south, islets, karsts, a lighthouse, a snowy range behind the mountains
and a volcano out to sea. Everything here is deterministic, so the game data written from it never drifts."""
import math
import random

from mathutils import Vector, noise

SEA = -0.12      # water level: the game draws its sea at this height
GRASS_R = 36.5   # flat grass inside this radius, sand from here to the waterline
WALK_R = 40.0    # the player stays inside this radius (WORLD_RADIUS in src/world3d/config.ts)
COAST_R = 42.5   # mean radius of the beaches' waterline
CLIFFS = (155.0, 205.0)  # angle range of the west cliffs (degrees, 0 = east, 90 = north)

LAKE = (2.0, 25.5, 3.6)        # lake under the waterfall: centre x, y and radius
LAKE_Z = -0.05                 # its water level
SHELF = (2.0, 29.4, 5.0, 5.5)  # rock shelf the waterfall drops from: x and y of its lip, half width, height
SALA = (38.8, -9.5)            # pavilion on the east beach, just inside the walkable circle

# x, y, base radius, height. The first INSIDE stand inside the walkable circle and block the player.
MOUNTAINS = [
    (-9.0, 35.5, 10.0, 9.0), (9.5, 36.5, 10.5, 10.5), (21.5, 31.0, 7.5, 6.0), (-21.5, 31.5, 7.5, 5.5),
    (30.5, 20.5, 6.5, 3.2), (-31.5, 22.5, 6.0, 2.8),
    (-4.0, 52.0, 16.0, 19.0), (16.0, 50.0, 13.0, 15.0), (-24.0, 47.0, 12.0, 12.0), (33.0, 41.0, 10.0, 8.0),
    (-37.0, 37.0, 9.0, 7.0), (4.0, 70.0, 18.0, 24.0), (-22.0, 66.0, 13.0, 16.0), (26.0, 64.0, 12.0, 14.0),
]
INSIDE = 6
HILL = MOUNTAINS[4]  # the hill with the golden chedi

# islets: x, y, radius, height, kind
ISLETS = [(0.0, -54.0, 7.5, 1.6, 'palm'), (25.0, -51.0, 5.0, 1.3, 'rock'), (-30.0, -50.0, 6.0, 1.4, 'palm'),
          (55.0, -17.0, 4.5, 1.8, 'rock'), (51.0, 29.0, 6.5, 2.6, 'green'), (-64.0, -38.0, 8.0, 2.2, 'dry'),
          (-98.0, 28.0, 17.0, 15.0, 'volcano')]
VOLCANO = ISLETS[-1]
SNOW = 7.6

noise.seed_set(7)


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def window(phi, a, b, soft):
    """1 inside the angle range [a, b] (degrees), fading to 0 over `soft` degrees outside it."""
    mid, half = (a + b) / 2, (b - a) / 2
    return 1 - smooth(half, half + soft, abs((phi - mid + 180) % 360 - 180))


def bump(t):
    return (1 - t * t) ** 2 if t < 1 else 0.0


def fbm(x, y, s, octaves=4):
    return noise.fractal(Vector((x * s + 13.1, y * s - 7.7, 0.5)), 0.65, 2.0, octaves, noise_basis='PERLIN_ORIGINAL')


def coast(phi):
    a = math.radians(phi)
    return COAST_R + 1.5 * math.sin(3 * a + 0.7) + 0.8 * math.sin(7 * a + 2.1)


def height(x, y):
    """Height of the ground at (x, y)."""
    r = math.hypot(x, y)
    phi = math.degrees(math.atan2(y, x)) % 360
    rc = coast(phi)
    if r < GRASS_R:
        h = 0.0
    elif r < rc:
        h = -0.08 * ((r - GRASS_R) / (rc - GRASS_R)) ** 2
    else:
        h = -0.08 - 2.4 * smooth(rc, rc + 9, r) - 1.6 * smooth(rc + 9, rc + 45, r) + 0.35 * fbm(x, y, 0.05) * smooth(rc + 6, rc + 20, r)
    w = window(phi, CLIFFS[0], CLIFFS[1], 10)
    if w > 0 and r > 40.2:
        c = (4.4 + 1.6 * fbm(x, y, 0.15)) * w * smooth(40.3, 41.5, r) * (1 - smooth(44.8, 46.8, r))
        if c > 0.02:  # the cliffs drop straight into the sea
            h = max(h, c)
    floor = min(h, 0.0)  # mountains rise from the sea floor where they stand in the sea
    for mx, my, R, H in MOUNTAINS:
        t = math.hypot(x - mx, y - my) / R
        if t < 1:
            b = bump(t)
            h = max(h, floor + H * b * (0.85 + 0.25 * fbm(x, y, 0.16)) + 0.5 * fbm(x, y, 0.45) * b)
    sx, sy, half, sh = SHELF
    lat = 1 - smooth(half, half + 1.6, abs(x - sx))
    if lat > 0:
        s = sh * lat * smooth(sy - 0.5, sy + 0.7, y) * (1 - smooth(sy + 12, sy + 16, y))
        if s > 0.02:
            h = max(h, s)
    for ix, iy, R, H, kind in ISLETS:
        t = math.hypot(x - ix, y - iy) / R
        if t < 1:
            if kind == 'volcano':
                v = -3.0 + (H + 3.0) * bump(max(t, 0.17)) ** 0.75 + 0.5 * fbm(x, y, 0.35) * (1 - t)
                if t < 0.17:
                    v -= 3.2 * (1 - (t / 0.17) ** 2)  # the crater
            else:
                v = -2.6 + (H + 2.6) * bump(t) ** 0.5 + 0.2 * fbm(x, y, 0.5) * bump(t)
            h = max(h, v)
    lx, ly, lr = LAKE
    d = math.hypot(x - lx, y - ly)
    if d < lr + 1.4:
        k = 1 - smooth(lr - 0.6, lr + 1.4, d)
        h = h * (1 - k) - 0.55 * k
    return h


def normal_z(x, y, e=0.35):
    """Up-component of the ground's normal at (x, y) (1 = flat)."""
    dx = (height(x + e, y) - height(x - e, y)) / (2 * e)
    dy = (height(x, y + e) - height(x, y - e)) / (2 * e)
    return 1 / math.sqrt(1 + dx * dx + dy * dy)


def islet_at(x, y, grow=1.0):
    for ix, iy, R, H, kind in ISLETS:
        if math.hypot(x - ix, y - iy) < R * grow:
            return kind
    return None


# ------------------------------------------------------------------ colours

def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexc(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def mix(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]


C = {k: hexc(v) for k, v in {
    'grass': '#86cf62', 'grass_light': '#98d96d', 'grass_dark': '#74bd55', 'meadow': '#a6dc73',
    'sand': '#f3e2a8', 'sand_wet': '#e4cb8f', 'floor_sand': '#eadaa2', 'floor_shallow': '#9ad8c6', 'floor_mid': '#3f9fc6',
    'floor_deep': '#2a6aa3', 'forest': '#5aa64a', 'forest_dark': '#478f3f', 'rock': '#9a917f', 'rock_dark': '#7d7567',
    'rock_light': '#b9af9b', 'snow': '#f4f8ff', 'lake_floor': '#5fb8b6', 'dry': '#dca461', 'dry_dark': '#bd8443',
    'volcano': '#5d4e48', 'volcano_dark': '#463a35', 'ash': '#7b6c62',
}.items()}


def face_color(x, y, z, nz, jitter):
    """sRGB colour of a ground face whose centre is at (x, y, z) and whose normal has up-component nz."""
    r = math.hypot(x, y)
    kind = islet_at(x, y, 1.05)
    if z < SEA - 0.02:
        d = SEA - z
        lx, ly, lr = LAKE
        if math.hypot(x - lx, y - ly) < lr + 0.8:
            c = C['lake_floor']
        else:
            c = mix(C['floor_sand'], C['floor_shallow'], smooth(0.05, 0.9, d))
            c = mix(c, C['floor_mid'], smooth(0.9, 2.2, d))
            c = mix(c, C['floor_deep'], smooth(2.2, 4.0, d))
    elif kind == 'volcano':
        t = math.hypot(x - VOLCANO[0], y - VOLCANO[1]) / VOLCANO[2]
        c = C['ash'] if t < 0.32 else C['volcano_dark'] if nz < 0.8 else C['volcano']
        if z < 0.3:
            c = C['volcano_dark']
    elif kind == 'dry':
        c = C['rock'] if nz < 0.75 else C['dry_dark'] if fbm(x, y, 0.4) > 0.1 else C['dry']
    elif z > SNOW + 0.8 * fbm(x, y, 0.3):
        c = C['snow']
    elif z < 0.32 and (r > GRASS_R + 0.7 * fbm(x, y, 0.25) or kind):
        c = C['sand_wet'] if z < SEA + 0.07 else C['sand']
    elif nz < 0.74:
        c = C['rock_dark'] if fbm(x, y, 0.5) > 0.15 else C['rock']
    elif z > 6.6:
        c = C['rock_light']
    elif z > 2.0:
        c = C['forest_dark'] if fbm(x, y, 0.35) > 0.1 else C['forest']
    else:
        n = fbm(x, y, 0.06)
        c = C['grass_light'] if n > 0.22 else C['grass_dark'] if n < -0.25 else C['meadow'] if fbm(x, y, 0.13) > 0.55 else C['grass']
    k = 1 + jitter
    return [_lin(min(1.0, v * k)) for v in c] + [1.0]


# ------------------------------------------------------------------ what the game needs

def obstacles():
    """Circles (three.js x, z, radius) the player cannot enter: the mountains and hills inside the walkable circle, the
    lake, the waterfall's rock shelf and the beach pavilion."""
    out = []
    for mx, my, R, H in MOUNTAINS[:INSIDE]:
        t = math.sqrt(max(0.0, 1 - math.sqrt(0.25 / (H * 0.6))))  # where even the lowest slope is under 0.25 high
        out.append((mx, -my, round(t * R + 0.4, 2)))
    lx, ly, lr = LAKE
    out.append((lx, -ly, lr + 0.4))
    sx, sy, half, sh = SHELF
    out.append((sx, -(sy + 2.5), half + 0.8))
    out.append((SALA[0], -SALA[1], 1.7))
    return out


def decor(keep_out):
    """Trees, palms and rocks on the land outside the walkable circle and on the obstacles inside it, as
    [kind, x, y, z, scale, turn] in three.js coordinates. keep_out = [(x, y, r)] in Blender coordinates (the set pieces)."""
    rnd = random.Random(11)
    inside = [(ox, -oz, r) for ox, oz, r in obstacles()]
    out = []
    step = 2.2
    gx = -80.0
    while gx < 80:
        gy = -70.0
        while gy < 86:
            x, y = gx + rnd.uniform(-0.8, 0.8), gy + rnd.uniform(-0.8, 0.8)
            gy += step
            r = math.hypot(x, y)
            if r < WALK_R - 0.5 and not any(math.hypot(x - ox, y - oy) < orad for ox, oy, orad in inside):
                continue  # the game scatters the walkable ground itself
            if r > 75 and not islet_at(x, y):
                continue
            if any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep_out):
                continue
            z = height(x, y)
            if z < SEA + 0.06 or z > SNOW - 0.6:
                continue
            kind = islet_at(x, y)
            if kind in ('volcano', 'rock'):
                continue
            lx, ly, lr = LAKE
            if math.hypot(x - lx, y - ly) < lr + 1.2 or (abs(x - SHELF[0]) < SHELF[2] + 1 and SHELF[1] - 1 < y < SHELF[1] + 12):
                continue  # the lake, the waterfall and the river on the shelf
            nz = normal_z(x, y)
            roll = rnd.random()
            pick = None
            if kind == 'dry':
                pick = 'rock' if roll < 0.12 else None
            elif z < 0.45:
                pick = 'palm' if roll < 0.3 else None
            elif nz > 0.8:
                if roll < 0.55:
                    pick = 'pine' if z > 3.6 + rnd.uniform(-1.2, 1.2) else rnd.choice(('tree', 'tree', 'bigtree', 'autumn', 'bloom', 'bush', 'pine'))
            elif z > 1.0 and roll < 0.07:
                pick = 'boulder'
            if pick:
                out.append([pick, round(x, 2), round(z - 0.08, 2), round(-y, 2), round(rnd.uniform(0.8, 1.25), 2), round(rnd.uniform(0, 6.28), 2)])
        gx += step
    return out
