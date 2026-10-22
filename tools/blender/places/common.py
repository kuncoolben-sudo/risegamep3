"""Building blocks shared by the eight location models (see ../build_places.py): Thai roofs, spires, walls,
palms, boats and so on, all made from the primitives of pets/kit.py. Coordinates are metres in the model's own
frame (x right, y back, z up, front of the building towards -y); every part goes to the single 'Body' pivot."""
import math
import random

from pets.kit import V

B = 'Body'


def rz(pt, yaw_deg, c=(0, 0, 0)):
    """Rotate pt about the vertical axis through the origin by yaw (degrees) and move it to c."""
    a = math.radians(yaw_deg)
    x, y, z = pt
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a), c[2] + z)


def plate(p, m, c, r, h=0.08, seg=28):
    """A flat round slab: ground, water, plaza."""
    p.cone(B, m, c, (c[0], c[1], c[2] + h), r, r, seg=seg, smooth=False)


def slab(p, m, c, w, d, h=0.1, yaw=0):
    p.box(B, m, (c[0], c[1], c[2] + h / 2), (w, d, h), rot=(0, 0, yaw))


def wall(p, m, a, b, h=0.9, t=0.25, z0=0.0, merlon=None, merlon_m=None, step=0.5):
    """A straight wall from a to b (x, y); merlon=(w, h) adds crenellations along the top."""
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    yaw = math.degrees(math.atan2(by - ay, bx - ax))
    mid = ((ax + bx) / 2, (ay + by) / 2)
    p.box(B, m, (mid[0], mid[1], z0 + h / 2), (length, t, h), rot=(0, 0, yaw))
    if merlon:
        n = max(1, int(length / step))
        for i in range(n):
            u = (i + 0.5) / n - 0.5
            x, y = mid[0] + math.cos(math.radians(yaw)) * u * length, mid[1] + math.sin(math.radians(yaw)) * u * length
            p.box(B, merlon_m or m, (x, y, z0 + h + merlon[1] / 2), (merlon[0], t * 1.05, merlon[1]), rot=(0, 0, yaw))


def gable(p, m, c, w, d, h, over=0.3, yaw=0, lift=0.0, panel_m=None, inset=0.2):
    """A gable roof: ridge along local y, eaves at z=0, ridge at z=h; the ridge ends rise by `lift` (Thai upswept look).
    w and d are the wall plan size; over is the overhang. panel_m fills both gable ends with an inset triangle."""
    hw, hd = w / 2 + over, d / 2 + over
    pts = [(-hw, -hd, 0), (hw, -hd, 0), (0, -hd, h + lift), (-hw, hd, 0), (hw, hd, 0), (0, hd, h + lift)]
    pts = [rz(q, yaw, c) for q in pts]
    p.poly(B, m, pts, [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], solid=True)
    if panel_m:
        k, zc = 1 - inset, (h + lift) / 3
        for sy in (-1, 1):
            y = sy * (hd + 0.012)
            tri = [(-hw * k, y, zc * (1 - k)), (hw * k, y, zc * (1 - k)), (0, y, zc + (h + lift - zc) * k)]
            p.poly(B, panel_m, [rz(q, yaw, c) for q in (tri if sy < 0 else tri[::-1])], [(0, 1, 2)])


def chofa(p, m, base, direction, h=0.45, r=0.05):
    """A curved gable finial rising from base, bending towards direction (unit x, y)."""
    bx, by, bz = base
    dx, dy = direction
    p.tube(B, m, [base, (bx + dx * 0.08, by + dy * 0.08, bz + h * 0.5), (bx + dx * 0.22, by + dy * 0.22, bz + h * 0.9),
                  (bx + dx * 0.4, by + dy * 0.4, bz + h)], [r, r * 0.8, r * 0.55, r * 0.2], seg=5)


def thai_roof(p, m, trim_m, horn_m, c, w, d, h, over=0.35, yaw=0, lift=0.18, panel_m=None):
    """One tier of a Thai roof: gable roof + a trim bar along the front and back eaves + gold horns at the four ends."""
    gable(p, m, c, w, d, h, over, yaw, lift, panel_m)
    hw, hd = w / 2 + over, d / 2 + over
    for sy in (-1, 1):
        p.box(B, trim_m, rz((0, sy * hd, 0.03), yaw, c), (hw * 2, 0.07, 0.08), rot=(0, 0, yaw))
    # horns: at both ends of the ridge, leaning outwards
    for sy in (-1, 1):
        chofa(p, horn_m, rz((0, sy * hd * 0.97, h + lift - 0.02), yaw, c), (math.cos(math.radians(yaw + 90)) * sy, math.sin(math.radians(yaw + 90)) * sy),
              h=min(0.55, 0.35 + h * 0.2))


def spire(p, m, c, r, h, tiers=5, seg=10, tip_m=None):
    """A stacked cone spire (prang tip / chedi finial)."""
    prof = []
    for i in range(tiers):
        t = i / tiers
        rr = r * (1 - t * 0.9)
        prof += [(rr, h * t), (rr * 0.72, h * (t + 0.55 / tiers))]
    prof.append((0, h))
    p.lathe(B, m, prof, c, seg=seg)
    if tip_m:
        p.sphere(B, tip_m, (c[0], c[1], c[2] + h + r * 0.06), r * 0.12, seg=6, rings=4)


def chedi(p, m, ring_m, c, r, h, seg=14, tip_m=None):
    """A bell-shaped chedi: base ring, bell, collar rings, long spire."""
    z = 0.0
    prof = [(r * 1.0, z), (r * 1.0, z + h * 0.06), (r * 0.86, z + h * 0.06), (r * 0.86, z + h * 0.10),
            (r * 0.78, z + h * 0.12), (r * 0.9, z + h * 0.2), (r * 0.82, z + h * 0.36), (r * 0.62, z + h * 0.5),
            (r * 0.36, z + h * 0.6), (r * 0.26, z + h * 0.62), (r * 0.18, z + h * 0.7)]
    p.lathe(B, m, prof, c, seg=seg, smooth=True, caps=False)
    for i, f in enumerate((0.64, 0.7, 0.76, 0.82, 0.88)):  # umbrella rings on the spire
        p.cone(B, ring_m, (c[0], c[1], c[2] + h * f), (c[0], c[1], c[2] + h * f + 0.05), r * (0.34 - i * 0.05), r * (0.3 - i * 0.05), seg=10)
    p.lathe(B, m, [(r * 0.12, h * 0.7), (r * 0.05, h * 0.96), (0, h)], c, seg=8)
    if tip_m:
        p.sphere(B, tip_m, (c[0], c[1], c[2] + h + 0.02), r * 0.1, seg=6, rings=4)


def palm(p, trunk_m, leaf_m, base, h=2.6, lean=(0.6, 0.0), n=7, leaf_len=1.15, seed=0):
    """A coconut palm with a leaning trunk and a crown of drooping leaves."""
    bx, by, bz = base
    pts = [(bx + lean[0] * (t ** 1.6), by + lean[1] * (t ** 1.6), bz + h * t) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    p.tube(B, trunk_m, pts, [0.11, 0.095, 0.085, 0.075, 0.07], seg=6)
    top = pts[-1]
    for i in range(n):
        a = 2 * math.pi * i / n + seed
        dx, dy = math.cos(a), math.sin(a)
        p.blade(B, leaf_m, (top[0], top[1], top[2] - 0.02), (top[0] + dx * leaf_len, top[1] + dy * leaf_len, top[2] - 0.45), 0.32, 0.02, face=(0, 0, 1), peak=0.45)
    p.sphere(B, trunk_m, (top[0], top[1], top[2] - 0.08), 0.12, seg=6, rings=4)


def round_tree(p, trunk_m, leaf_m, base, h=1.6, r=0.8, seed=1, leaf2_m=None):
    bx, by, bz = base
    p.cone(B, trunk_m, (bx, by, bz), (bx, by, bz + h * 0.62), 0.13, 0.09, seg=6)
    p.blob(B, leaf_m, (bx, by, bz + h * 0.8), r, (1, 1, 0.85), 0.12, seed, 8, 6)
    if leaf2_m:
        p.blob(B, leaf2_m, (bx + r * 0.35, by - r * 0.2, bz + h * 1.0), r * 0.6, (1, 1, 0.8), 0.12, seed + 3, 7, 5)


def pine(p, trunk_m, leaf_m, base, h=2.0, r=0.6, tiers=3):
    bx, by, bz = base
    p.cone(B, trunk_m, (bx, by, bz), (bx, by, bz + h * 0.3), 0.09, 0.07, seg=5)
    for i in range(tiers):
        t = i / tiers
        p.cone(B, leaf_m, (bx, by, bz + h * (0.22 + t * 0.55)), (bx, by, bz + h * (0.22 + t * 0.55) + h * 0.5), r * (1 - t * 0.35), 0.0, seg=7, smooth=False)


def lantern(p, m, c, r=0.14, cord_m=None, drop=0.0):
    """A paper lantern (glowing) with an optional cord up."""
    p.sphere(B, m, c, r, (1, 1, 1.25), seg=8, rings=6)
    if drop and cord_m:
        p.cone(B, cord_m, (c[0], c[1], c[2] + r * 1.2), (c[0], c[1], c[2] + drop), 0.012, 0.012, seg=4)


def longtail(p, hull_m, trim_m, wood_m, sash_m, c, yaw=0, s=1.0):
    """A Thai longtail boat: long narrow hull, raised bow with coloured sashes, tail pole with a propeller."""
    def T(x, y, z):
        return rz((x * s, y * s, z * s), yaw, c)
    p.sphere(B, hull_m, T(0, 0, 0.18), 1.0 * s, (0.22 / 1.0, 1.55 / 1.0, 0.2 / 1.0), seg=10, rings=6, rot=(0, 0, yaw))
    p.box(B, wood_m, T(0, 0, 0.3), (0.38 * s, 1.9 * s, 0.05 * s), rot=(0, 0, yaw))  # deck
    p.tube(B, trim_m, [T(0, -1.45, 0.25), T(0, -1.62, 0.5), T(0, -1.55, 0.78)], [0.07 * s, 0.05 * s, 0.03 * s], seg=5)  # raised bow
    for i, off in enumerate((-0.04, 0.0, 0.04)):
        p.blade(B, sash_m[i % len(sash_m)], T(off * 6, -1.58, 0.72), T(off * 6, -1.5, 0.45), 0.09 * s, 0.01, face=rz((1, 0, 0), yaw), peak=0.5)
    p.cone(B, wood_m, T(0, 1.2, 0.35), T(0, 2.2, 0.75), 0.04 * s, 0.03 * s, seg=5)  # tail pole
    p.box(B, trim_m, T(0, 2.25, 0.78), (0.2 * s, 0.03 * s, 0.03 * s), rot=(0, 0, yaw))  # propeller


def tiered_roof(p, wall_m, roof_m, trim_m, horn_m, c, tiers, yaw=0, over=0.35, lift=0.18, band=0.5, panel_m=None):
    """Stacked Thai roof tiers, widest first: tiers=[(span, ridge length, height), ...] and c the eaves point of the lowest
    tier. Every upper tier stands on a short band of wall that rises out of the roof below. roof_m and trim_m may be a
    sequence of materials, used in turn; panel_m decorates the gable ends. Returns the height of the top ridge."""
    cx, cy, e = c
    for i, (w, d, h) in enumerate(tiers):
        if i:
            p.box(B, wall_m, (cx, cy, e - band / 2 + 0.04), (w, d, band), rot=(0, 0, yaw))
        roof = roof_m if isinstance(roof_m, str) else roof_m[i % len(roof_m)]
        trim = trim_m if isinstance(trim_m, str) else trim_m[i % len(trim_m)]
        thai_roof(p, roof, trim, horn_m, (cx, cy, e), w, d, h, over, yaw, lift, panel_m)
        e += h + lift - 0.06
    return e + 0.06


def prism(p, m, lo, hi):
    """A closed shape between two rings of points with the same count (hull sections, plinths, banks)."""
    n = len(lo)
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    faces += [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    p.poly(B, m, list(lo) + list(hi), faces, solid=True)


def strip(p, m, pts, width, z):
    """A flat ribbon (stream, path) through the points (x, y) at height z, with mitred joins."""
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L * width / 2, dx / L * width / 2
        left.append((x + nx, y + ny, z))
        right.append((x - nx, y - ny, z))
    p.poly(B, m, left + right, [(i, n + i, n + i + 1, i + 1) for i in range(n - 1)])


def parasol(p, pole_m, m1, m2, c, h=1.5, r=0.8, seg=8):
    """A beach/market umbrella with a striped canopy, standing at c."""
    x, y, z = c
    p.cone(B, pole_m, (x, y, z), (x, y, z + h + 0.12), 0.03, 0.03, seg=5)
    top = (x, y, z + h + 0.3)
    rim = [(x + math.cos(2 * math.pi * i / seg) * r, y + math.sin(2 * math.pi * i / seg) * r, z + h) for i in range(seg)]
    for i in range(seg):
        p.poly(B, m1 if i % 2 == 0 else m2, [top, rim[i], rim[(i + 1) % seg]], [(0, 1, 2)])
    p.sphere(B, pole_m, top, 0.045, seg=6, rings=4)


def _support(ax, ay, yaw, ux, uy):
    """The point of an ellipse (semi-axes ax, ay, turned by yaw degrees) furthest along the unit direction (ux, uy)."""
    a = math.radians(yaw)
    lx, ly = ux * math.cos(a) + uy * math.sin(a), -ux * math.sin(a) + uy * math.cos(a)
    k = math.hypot(ax * lx, ay * ly) or 1.0
    px, py = ax * ax * lx / k, ay * ay * ly / k
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)


def karst(p, c, r, h, seed, yaw=0.0, stretch=1.0, z0=0.1):
    """A limestone karst rising sheer out of the water: jungle over its top, a sunlit face and hanging vines towards the
    camera (-y) and a fringe of foam at its foot. stretch > 1 draws it out into a wall along yaw (degrees).
    Uses the palette keys Rock, RockLight, Moss, Moss2 and Foam."""
    x, y = c
    sx, sy = stretch, 1.0 / math.sqrt(stretch)
    rot = (0, 0, yaw)
    zc, hz = z0 + h * 0.3, h * 0.62  # the rock's centre and vertical semi-axis: widest just above the water

    def f(z):  # the rock's horizontal scale at height z
        return math.sqrt(max(0.0, 1 - ((z - zc) / hz) ** 2))

    def face(z, ang=0.0, inset=1.0):  # the rock's outline at height z, seen from the camera turned by ang degrees
        u = (math.sin(math.radians(ang)), -math.cos(math.radians(ang)))
        dx, dy = _support(r * sx * f(z), r * sy * f(z), yaw, *u)
        return x + dx * inset, y + dy * inset
    p.blob(B, 'Rock', (x, y, zc), r, (sx, sy, hz / r), 0.06, seed, 9, 6, rot=rot)
    side = 1 if seed % 2 else -1  # the sunlit patch and the vine sit off-centre, on opposite sides
    zl = z0 + h * 0.25
    q = face(zl, 24 * side, 0.8)
    p.blob(B, 'RockLight', (q[0], q[1], zl), r * 0.5, (1.1, 0.6, h * 0.32 / r), 0.08, seed + 4, 7, 4)
    zt = z0 + h * 0.78
    rm = r * (f(zt) + 0.08)
    p.blob(B, 'Moss', (x, y, zt), rm, (sx, sy, (0.16 * h + 0.12) / rm), 0.1, seed + 2, 8, 5, rot=rot)
    rnd = random.Random(seed)
    for i in range(3):  # bushes on top
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.0, 0.5) * rm
        q = rz((math.cos(a) * d * sx, math.sin(a) * d * sy, 0), yaw, (x, y, 0))
        p.blob(B, 'Moss2', (q[0], q[1], zt + 0.12 * h + 0.05), r * rnd.uniform(0.2, 0.3), (1, 1, 0.8), 0.15, seed + 10 + i, 6, 4)
    zv = zt - 0.2 - 0.56 * r  # one vine hanging from the jungle cap
    q = face(zv, -30 * side, 0.97)
    p.blob(B, 'Moss2', (q[0], q[1], zv), r * 0.14, (1, 0.7, 4.0), 0.1, seed + 20, 5, 3)
    p.blob(B, 'Foam', (x, y, z0), 1.0, (r * sx * f(z0) + 0.12 * r, r * sy * f(z0) + 0.12 * r, 0.05), 0.03, seed + 30, 10, 3, rot=rot)
