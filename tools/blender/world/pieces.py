"""Hand-placed things on the island: the waterfall with its river and lake and a cave beside it, a fishing village on
stilts with a pier, boats and a market stall, two pavilions, a bridge to an islet, a lighthouse, a golden chedi on a
hill, karsts and sailboats offshore and the volcano's lava and smoke. All in one kit model; heights come from the
ground (layout.height) so everything stands on it."""
import math

from places.common import B, chedi, gable, karst, longtail, plate, prism, rz, slab, strip, thai_roof

from . import layout as L

PALETTE = {
    'Water': ('#3fc0e0', dict(rough=0.2)), 'Falls': ('#e8f8ff', dict(emit='#bfe8ff', es=0.4)), 'Foam': '#ffffff',
    'Wood': '#a9743f', 'WoodDark': '#7a4a24', 'Teak': '#8a5a32', 'Thatch': '#c9a45c', 'RoofRed': '#c0532e', 'RoofTeal': '#3d8f86',
    'White': '#ffffff', 'Cream': '#f4ead2', 'Red': '#e0453a', 'Green': '#2f9e6b', 'Yellow': '#ffd23f', 'Blue': '#3b82d6',
    'Gold': ('#f2bb32', dict(rough=0.35, emit='#c98a10', es=0.3)), 'GoldDark': ('#d9992a', dict(rough=0.4, emit='#a8700c', es=0.2)),
    'Lamp': ('#ffe9a8', dict(emit='#ffd060', es=1.5)), 'Glass': '#27496f', 'HullBlue': '#2f6fd0', 'Sail': '#fffaf0',
    'Rock': '#948d7c', 'RockLight': '#c3bba5', 'Moss': '#4d9e50', 'Moss2': '#2e7d42', 'Cave': '#2b2522', 'Stone': '#ddd6c6',
    'Lava': ('#ff6a2a', dict(emit='#ff4a12', es=3.0)), 'Smoke': '#a19c96', 'Orange': '#ff8a2a', 'Fish': '#9ab3c4',
}

VILLAGE = [(44.6, -7.4, 'Cream', 'Thatch'), (46.1, -3.0, 'Teak', 'RoofRed'), (45.2, 4.0, 'Cream', 'RoofTeal')]
PIER = (40.6, 53.5, 0.8)  # x from, x to, y
STALL = (40.4, 6.3)
CAVE = (6.3, 1.9, 1.9)    # x, width, height of the cave mouth in the rock shelf, east of the waterfall
KARSTS = [(-52.0, -12.0, 2.3, 8.0, 1, 20), (-57.0, 7.0, 1.9, 6.5, 3, -15), (-46.0, -30.0, 2.0, 7.0, 5, 40), (-36.0, -44.0, 1.7, 5.0, 9, 0)]
SAILBOATS = [(22.0, -64.0, 75), (-18.0, -67.0, -80), (63.0, 12.0, 10)]
BRIDGE = (0.0, -40.4, -49.8)  # x, y on the beach, y on the islet


def gz(x, y):
    return L.height(x, y)


def keep_out():
    """Circles (Blender x, y, r) the trees and rocks of layout.decor must keep clear of."""
    out = [(x, y, 2.4) for x, y, _, _ in VILLAGE] + [((PIER[0] + PIER[1]) / 2, PIER[2], 6.8), (L.SALA[0], L.SALA[1], 2.3),
                                                      (STALL[0], STALL[1], 1.8), (BRIDGE[0], (BRIDGE[1] + BRIDGE[2]) / 2, 5.2),
                                                      (0.0, -54.0, 2.4), (25.0, -51.0, 2.0), (L.HILL[0], L.HILL[1], 1.9)]
    out += [(x, y, r * 1.4 + 1.0) for x, y, r, _, _, _ in KARSTS]
    return out


def ribbon(p, m, pts, w0, w1=None):
    """A strip draped along 3D points, w0 wide at the start narrowing to w1 (lava runs)."""
    n = len(pts)
    w1 = w0 if w1 is None else w1
    left, right = [], []
    for i, (x, y, z) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((x - dy / ln * w, y + dx / ln * w, z))
        right.append((x + dy / ln * w, y - dx / ln * w, z))
    p.poly(B, m, left + right, [(i, n + i, n + i + 1, i + 1) for i in range(n - 1)])


def lake_and_falls(p):
    lx, ly, lr = L.LAKE
    plate(p, 'Water', (lx, ly, L.LAKE_Z - 0.03), lr + 0.9, 0.03, seg=32)
    sx, sy, half, sh = L.SHELF
    face_y = shelf_face_y

    def sheet(m, x0, x1, cols, off, z_top):
        xs = [x0 + (x1 - x0) * j / cols for j in range(cols + 1)]
        zs = [L.LAKE_Z + (z_top - L.LAKE_Z) * i / 9 for i in range(10)]
        c = cols + 1
        p.poly(B, m, [(x, face_y(x, z) + off, z) for z in zs for x in xs],
               [(i * c + j, i * c + j + 1, (i + 1) * c + j + 1, (i + 1) * c + j) for i in range(9) for j in range(cols)])

    sheet('Falls', sx - 1.4, sx + 1.4, 4, -0.3, sh + 0.03)
    for x in (sx - 0.8, sx + 0.1, sx + 0.9):  # white streaks in the falling water
        sheet('Foam', x - 0.07, x + 0.07, 1, -0.34, sh - 0.1)
    for i, x in enumerate((sx - 1.1, sx - 0.3, sx + 0.5, sx + 1.2)):  # splash where it lands
        p.blob(B, 'Foam', (x, face_y(x, 0.2) - 0.6, 0.05), 0.42, (1, 0.8, 0.55), 0.15, 20 + i, 7, 5)
    p.blob(B, 'Foam', (sx, face_y(sx, sh) - 0.32, sh), 0.3, (5.0, 0.8, 0.5), 0.06, 30, 9, 5)  # the lip
    strip(p, 'Water', [(sx, sy + 0.9), (sx + 0.5, sy + 3.0), (sx - 0.3, sy + 6.5), (sx + 0.5, sy + 10.5), (sx, sy + 13.5)], 1.7, sh + 0.06)
    for i in range(8):  # stones round the near shore of the pool
        a = math.radians(200 + i * 20)
        x, y = lx + math.cos(a) * (lr + 0.5), ly + math.sin(a) * (lr + 0.5)
        p.blob(B, 'Rock' if i % 3 else 'RockLight', (x, y, gz(x, y) + 0.05), 0.32, (1.2, 1, 0.75), 0.18, 40 + i, 6, 4)


def stilt_house(p, x, y, wall, roof, w=1.9, d=1.6):
    zf = 1.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = x + sx * (w / 2 - 0.05), y + sy * (d / 2 + 0.15)
            p.cone(B, 'WoodDark', (px, py, gz(px, py) - 0.1), (px, py, zf), 0.06, 0.06, seg=5)
    p.box(B, 'Wood', (x, y - 0.25, zf + 0.04), (w + 0.4, d + 0.9, 0.08))  # floor with a porch in front
    fy = y + 0.1 - (d - 0.2) / 2
    p.box(B, wall, (x, y + 0.1, zf + 0.6), (w, d - 0.2, 1.1))
    p.box(B, 'WoodDark', (x, fy - 0.02, zf + 0.5), (0.4, 0.04, 0.8))
    for sx in (-1, 1):
        p.box(B, 'Glass', (x + sx * 0.55, fy - 0.02, zf + 0.72), (0.3, 0.04, 0.3))
    gable(p, roof, (x, y + 0.1, zf + 1.15), w, d - 0.2, 0.8, 0.28, 0, 0.1, panel_m=wall, inset=0.15)
    shore = 41.4  # a plank walk to the beach
    p.box(B, 'Wood', ((shore + x - w / 2) / 2, y - 0.6, zf - 0.08), (x - w / 2 - shore + 0.3, 0.6, 0.06))
    for px in (shore + 0.6, (shore + x - w / 2) / 2):
        p.cone(B, 'WoodDark', (px, y - 0.6, gz(px, y - 0.6) - 0.1), (px, y - 0.6, zf - 0.1), 0.04, 0.04, seg=4)


def village(p):
    for x, y, wall, roof in VILLAGE:
        stilt_house(p, x, y, wall, roof)
    x0, x1, y = PIER
    p.box(B, 'Wood', ((x0 + x1) / 2, y, 0.5), (x1 - x0, 1.2, 0.1))
    x = x0 + 0.7
    while x < x1:
        for sy in (-1, 1):
            p.cone(B, 'WoodDark', (x, y + sy * 0.55, gz(x, y) - 0.1), (x, y + sy * 0.55, 0.48), 0.06, 0.06, seg=5)
        x += 1.5
    p.cone(B, 'WoodDark', (x1 - 0.3, y + 0.5, 0.5), (x1 - 0.3, y + 0.5, 1.9), 0.04, 0.04, seg=5)  # lamp post
    p.sphere(B, 'Lamp', (x1 - 0.3, y + 0.5, 2.0), 0.13, seg=8, rings=6)
    longtail(p, 'HullBlue', 'Red', 'Wood', ('Red', 'Yellow', 'Blue'), (49.8, y + 1.5, L.SEA - 0.06), 90, 1.0)
    longtail(p, 'Red', 'Yellow', 'Wood', ('Blue', 'White', 'Yellow'), (51.2, y - 1.6, L.SEA - 0.06), 98, 0.95)
    # a market stall on the beach
    sx, sy = STALL
    z = gz(sx, sy)
    for dx in (-0.7, 0.7):
        for dy in (-0.45, 0.45):
            p.cone(B, 'WoodDark', (sx + dx, sy + dy, z), (sx + dx, sy + dy, z + 1.4), 0.04, 0.04, seg=4)
    p.box(B, 'Wood', (sx, sy, z + 0.7), (1.6, 1.0, 0.08))
    for i in range(5):
        p.box(B, 'Red' if i % 2 else 'White', (sx - 0.72 + i * 0.36, sy, z + 1.45), (0.36, 1.2, 0.06), rot=(-8, 0, 0))
    for i, (dx, m) in enumerate(((-0.45, 'Fish'), (0.0, 'Orange'), (0.45, 'Yellow'))):
        p.cone(B, 'Wood', (sx + dx, sy - 0.15, z + 0.74), (sx + dx, sy - 0.15, z + 0.84), 0.13, 0.17, seg=8)
        for j in range(3):
            p.sphere(B, m, (sx + dx + (j - 1) * 0.08, sy - 0.15, z + 0.9), 0.07, seg=6, rings=4)


def sala(p, x, y, roof='RoofRed', trim='Green', size=1.6):
    z0 = gz(x, y)
    slab(p, 'Stone', (x, y, z0 - 0.05), size + 0.6, size + 0.6, 0.25)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cone(B, 'White', (x + sx * size / 2, y + sy * size / 2, z0 + 0.2), (x + sx * size / 2, y + sy * size / 2, z0 + 1.55), 0.07, 0.06, seg=6)
    thai_roof(p, roof, trim, 'Gold', (x, y, z0 + 1.55), size + 0.1, size + 0.1, 0.75, 0.3, 0, panel_m='Gold')


def bridge(p):
    x, y0, y1 = BRIDGE
    n = 8
    pts = [(y0 + (y1 - y0) * i / n, 0.5 + 0.45 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    for (ya, za), (yb, zb) in zip(pts, pts[1:]):
        p.box(B, 'Wood', (x, (ya + yb) / 2, (za + zb) / 2), (1.3, math.hypot(yb - ya, zb - za) + 0.03, 0.08),
              rot=(math.degrees(math.atan2(zb - za, yb - ya)), 0, 0))
    for sx in (-1, 1):
        rail = [(x + sx * 0.6, y, z + 0.5) for y, z in pts]
        p.tube(B, 'WoodDark', rail, 0.035, seg=4)
        for rx, ry, rzz in rail:
            p.cone(B, 'WoodDark', (rx, ry, gz(rx, ry) - 0.1), (rx, ry, rzz + 0.03), 0.045, 0.045, seg=4)


def lighthouse(p, x, y, k=1.6):
    z = gz(x, y) - 0.05
    h = 1.5 * k
    p.cone(B, 'White', (x, y, z), (x, y, z + h), 0.27 * k, 0.19 * k, seg=10)
    for f in (0.25, 0.62):
        p.cone(B, 'Red', (x, y, z + h * f), (x, y, z + h * f + 0.2 * k), 0.282 * k - 0.08 * k * f, 0.282 * k - 0.08 * k * (f + 0.13), seg=10)
    p.cone(B, 'Red', (x, y, z + h), (x, y, z + h + 0.06 * k), 0.3 * k, 0.3 * k, seg=10)
    p.cone(B, 'Lamp', (x, y, z + h + 0.06 * k), (x, y, z + h + 0.3 * k), 0.15 * k, 0.15 * k, seg=8)
    p.cone(B, 'Red', (x, y, z + h + 0.3 * k), (x, y, z + h + 0.52 * k), 0.2 * k, 0.0, seg=8)


def shelf_face_y(x, z):
    """y where the rock shelf behind the lake reaches height z (its face looks south, at the camera)."""
    sy = L.SHELF[1]
    lo, hi = sy - 3.5, sy + 2.0
    for _ in range(28):
        mid = (lo + hi) / 2
        if L.height(x, mid) < z:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def cave(p):
    """A dark cave mouth in the rock shelf beside the waterfall, with rocks round its rim."""
    cx, w, hgt = CAVE
    n = 12
    rim = [(cx - w / 2 * math.cos(math.pi * i / n), hgt * math.sin(math.pi * i / n) + 0.02) for i in range(n + 1)]
    verts = [(cx, shelf_face_y(cx, 0.3) - 0.06, 0.3)] + [(x, shelf_face_y(x, z) - 0.06, z) for x, z in rim]
    p.poly(B, 'Cave', verts, [(0, i + 2, i + 1) for i in range(n)])
    for i in range(7):
        x, z = rim[min(n, 1 + i * 2)]
        p.blob(B, 'Rock' if i % 2 else 'RockLight', (x, shelf_face_y(x, z) - 0.15, z), 0.35, (1.1, 0.8, 1.0), 0.2, 60 + i, 6, 4)


def sailboat(p, c, yaw):
    def T(x, y, z):
        return rz((x, y, z), yaw, c)
    outline = [(-0.32, 0.9), (0.32, 0.9), (0.36, -0.4), (0.0, -1.05), (-0.36, -0.4)]
    prism(p, 'White', [T(x * 0.7, y, -0.15) for x, y in outline], [T(x, y, 0.25) for x, y in outline])
    p.box(B, 'Wood', T(0, 0.1, 0.27), (0.5, 1.4, 0.04), rot=(0, 0, yaw))
    p.cone(B, 'WoodDark', T(0, -0.1, 0.25), T(0, -0.1, 2.4), 0.03, 0.02, seg=5)
    p.poly(B, 'Sail', [T(0, -0.04, 0.5), T(0, -0.04, 2.3), T(0, 0.85, 0.55)], [(0, 1, 2)])
    p.poly(B, 'Sail', [T(0, -0.16, 0.5), T(0, -0.95, 0.45), T(0, -0.16, 2.1)], [(0, 1, 2)])
    p.blade(B, 'Red', T(0, -0.1, 2.35), T(0, 0.25, 2.3), 0.12, 0.01, face=rz((1, 0, 0), yaw), peak=0.5)


def volcano(p):
    vx, vy, R, H, _ = L.VOLCANO
    floor = L.height(vx, vy)
    plate(p, 'Lava', (vx, vy, floor + 0.4), 0.17 * R * 0.8, 0.06, seg=18)
    for k, a in enumerate((200, 255, 320)):  # lava running down the slopes
        pts = []
        for i in range(9):
            t = 0.16 + 0.065 * i
            ang = math.radians(a + 7 * math.sin(i * 1.3 + k))
            x, y = vx + math.cos(ang) * t * R, vy + math.sin(ang) * t * R
            pts.append((x, y, L.height(x, y) + 0.3))
        ribbon(p, 'Lava', pts, 1.4, 0.5)
    for i in range(6):  # smoke drifting off the crater
        p.blob(B, 'Smoke', (vx + i * 0.9, vy + i * 0.5, floor + 4.0 + i * 2.2), 1.3 + i * 0.35, (1.2, 1, 0.8), 0.15, 70 + i, 8, 5)


def build(p):
    lake_and_falls(p)
    village(p)
    sala(p, *L.SALA)
    sala(p, 0.0, -54.0, 'RoofTeal', 'Red', 1.4)
    bridge(p)
    lighthouse(p, 25.0, -51.0)
    cave(p)
    hx, hy = L.HILL[0], L.HILL[1]
    top = gz(hx, hy)
    slab(p, 'White', (hx, hy, top - 0.15), 1.7, 1.7, 0.35)
    slab(p, 'Stone', (hx, hy, top + 0.2), 1.3, 1.3, 0.22)
    chedi(p, 'Gold', 'GoldDark', (hx, hy, top + 0.42), 0.55, 2.6, seg=12, tip_m='Gold')
    for x, y, r, h, seed, yaw in KARSTS:
        karst(p, (x, y), r, h, seed, yaw=yaw, stretch=1.2, z0=L.SEA)
    for x, y, yaw in SAILBOATS:
        sailboat(p, (x, y, L.SEA), yaw)
    volcano(p)
