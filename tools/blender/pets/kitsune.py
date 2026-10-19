"""Kitsune, the wisdom fox: a one-tailed kit (form 1), a five-tailed fox (2) and the nine-tailed fox (3)."""
import math

from mathutils import Vector as V

from .kit import R, wings

PALETTE = {
    'White': '#fff8fb', 'PinkTip': '#ffc0d8', 'Pink': '#ff9ec2', 'Deep': '#f2639a', 'Paw': '#ff8fb5',
    'Gold': ('#f2c14b', dict(rough=0.4, emit='#d9a21f', es=0.25)), 'Iris': '#8a4bd6', 'Pupil': '#201040', 'Sclera': '#ffffff',
    'Shine': ('#ffffff', dict(emit='#ffffff', es=1.0)), 'Flower': '#f2457a', 'FlowerC': '#ffd24a', 'Leaf': '#4fbf6a',
    'Gem': ('#ff9ee8', dict(emit='#ff6fd8', es=3.0)),
}
SCALE = {1: 1.0, 2: 1.05, 3: 1.3}
YAWS = {1: [0], 2: [-55, -28, 0, 28, 55], 3: [-80, -60, -40, -20, 0, 20, 40, 60, 80]}


def build(p, form):
    (kit if form == 1 else fox)(p, form)


def fox_tail(p, piv, base, yaw, pitch, length, thick, n=6):
    """A fluffy tail curling upwards from base; yaw 0 points straight back, positive turns to the right."""
    ya = math.radians(yaw)
    pos = V(base)
    pts, radii = [], []
    for i in range(n):
        t = i / (n - 1)
        pit = math.radians(pitch + 50 * t)
        d = V((math.sin(ya) * math.cos(pit), math.cos(ya) * math.cos(pit), math.sin(pit)))
        if i:
            pos = pos + d * (length / (n - 1))
        pts.append(tuple(pos))
        radii.append(thick * (0.55 + 0.9 * math.sin(math.pi * min(1.0, 0.15 + t * 0.9))))
    p.fluff_tail(piv, 'White', 'PinkTip', pts, radii, seg=8, rings=6)


def flower(p, piv, c, r=0.05):
    for i in range(5):
        a = 2 * math.pi * i / 5
        p.sphere(piv, 'Flower', (c[0] + math.cos(a) * r * 1.3, c[1] - 0.01, c[2] + math.sin(a) * r * 1.3), r, (1, 0.5, 1), seg=7, rings=5)
    p.sphere(piv, 'FlowerC', (c[0], c[1] - 0.03, c[2]), r * 0.6, seg=6, rings=4)
    p.blade(piv, 'Leaf', (c[0], c[1], c[2] - r), (c[0] + r * 2.4, c[1] + 0.02, c[2] - r * 2.2), r * 1.2, face=(0, 1, 0))


def ear(p, piv, sx, base, tip, w):
    p.blade(piv, 'White', base, tip, w, 0.03, face=(0, 1, 0), peak=0.4)
    p.blade(piv, 'Pink', (base[0], base[1] - 0.015, base[2] + 0.02), (tip[0] - sx * 0.01, tip[1] - 0.015, tip[2] - 0.1), w * 0.55, 0.02, face=(0, 1, 0), peak=0.4)


def kit(p, form):
    p.pivot('Head', (0, -0.22, 0.56))
    p.pivot('EarL', (-0.17, -0.3, 0.98), parent='Head')
    p.pivot('EarR', (0.17, -0.3, 0.98), parent='Head')
    p.pivot('Tail1', (0, 0.36, 0.38))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.14, -0.08, 0.24))
        p.pivot('LegB' + s, (sx * 0.17, 0.28, 0.24))
    p.sphere('Body', 'White', (0, 0.1, 0.34), 0.31, (1, 1.15, 0.9))
    p.sphere('Body', 'White', (0, -0.14, 0.4), 0.18, (1, 0.8, 1))
    hc = (0, -0.3, 0.76)
    p.sphere('Head', 'White', hc, 0.3, (1.06, 1.0, 0.95))
    p.sphere('Head', 'White', (0, -0.53, 0.68), 0.12, (1, 1.2, 0.8))
    p.sphere('Head', 'Deep', (0, -0.65, 0.7), 0.028, seg=6, rings=4)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.3, sx, yaw=34, pitch=4, size=0.115, iris='Iris')
        p.sphere('Head', 'Pink', (sx * 0.24, -0.48, 0.66), 0.055, (1, 0.3, 0.7), seg=6, rings=4)
        ear(p, 'EarL' if sx < 0 else 'EarR', sx, (sx * 0.17, -0.3, 1.0), (sx * 0.34, -0.22, 1.42), 0.17)
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'White', (sx * 0.14, -0.08, 0.28), (sx * 0.14, -0.1, 0.1), 0.07, 0.06)
        p.sphere('LegF' + s, 'Paw', (sx * 0.14, -0.12, 0.05), 0.075, (1, 1.3, 0.7))
        p.cone('LegB' + s, 'White', (sx * 0.17, 0.28, 0.3), (sx * 0.17, 0.3, 0.1), 0.09, 0.065)
        p.sphere('LegB' + s, 'Paw', (sx * 0.17, 0.25, 0.05), 0.08, (1, 1.3, 0.7))
    flower(p, 'EarR', (0.2, -0.34, 1.02))
    p.torus('Body', 'Gold', (0, -0.3, 0.52), 0.15, 0.02, rot=(65, 0, 0), seg=14)
    p.sphere('Body', 'Gem', (0, -0.4, 0.47), 0.042, seg=6, rings=4)
    fox_tail(p, 'Tail1', (0, 0.36, 0.36), 0, 18, 0.7, 0.2, 6)


def fox(p, form):
    big = form == 3
    yaws = YAWS[form]
    p.pivot('Head', (0, -0.3, 0.9))
    p.pivot('EarL', (-0.17, -0.5, 1.42), parent='Head')
    p.pivot('EarR', (0.17, -0.5, 1.42), parent='Head')
    for i in range(len(yaws)):
        p.pivot(f'Tail{i + 1}', (0, 0.66, 0.72))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.17, -0.14, 0.6))
        p.pivot('LegB' + s, (sx * 0.19, 0.46, 0.6))
    p.sphere('Body', 'White', (0, 0.2, 0.72), 0.31, (0.82, 1.45, 0.82))
    p.sphere('Body', 'White', (0, -0.16, 0.82), 0.2, (0.9, 0.85, 1.0))
    p.tube('Head', 'White', [(0, -0.18, 0.8), (0, -0.32, 1.0), (0, -0.4, 1.14)], [0.14, 0.12, 0.11])
    hc = (0, -0.48, 1.24)
    p.sphere('Head', 'White', hc, 0.29, (1.05, 1.0, 0.95))
    p.sphere('Head', 'White', (0, -0.7, 1.15), 0.11, (1, 1.2, 0.8))
    p.sphere('Head', 'Deep', (0, -0.82, 1.17), 0.03, seg=6, rings=4)
    p.sphere('Head', 'Gem', (0, -0.76, 1.46), 0.04 if not big else 0.055, seg=6, rings=4)
    if big:
        p.tube('Head', 'Gold', [(math.sin(a) * 0.29, -0.48 - math.cos(a) * 0.28, 1.43) for a in [math.radians(x) for x in range(-70, 71, 20)]], 0.016, seg=5)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.29, sx, yaw=36, pitch=4, size=0.11, iris='Iris')
        p.sphere('Head', 'Pink', (sx * 0.22, -0.66, 1.14), 0.05, (1, 0.3, 0.7), seg=6, rings=4)
        ear(p, 'EarL' if sx < 0 else 'EarR', sx, (sx * 0.17, -0.5, 1.44), (sx * 0.36, -0.4, 1.9 if big else 1.84), 0.19)
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'White', (sx * 0.17, -0.14, 0.64), (sx * 0.17, -0.17, 0.2), 0.07, 0.05)
        p.cone('LegF' + s, 'Paw', (sx * 0.17, -0.17, 0.22), (sx * 0.17, -0.18, 0.05), 0.05, 0.055)
        p.sphere('LegF' + s, 'Paw', (sx * 0.17, -0.2, 0.04), 0.06, (1, 1.3, 0.6))
        p.cone('LegB' + s, 'White', (sx * 0.19, 0.46, 0.64), (sx * 0.19, 0.48, 0.2), 0.095, 0.055)
        p.cone('LegB' + s, 'Paw', (sx * 0.19, 0.48, 0.22), (sx * 0.19, 0.46, 0.05), 0.055, 0.06)
        p.sphere('LegB' + s, 'Paw', (sx * 0.19, 0.42, 0.04), 0.065, (1, 1.3, 0.6))
    flower(p, 'EarR', (0.2, -0.5, 1.46), 0.06 if not big else 0.075)
    p.torus('Body', 'Gold', (0, -0.3, 0.98), 0.16, 0.022, rot=(62, 0, 0), seg=14)
    p.sphere('Body', 'Gem', (0, -0.44, 0.92), 0.05 if not big else 0.07, seg=7, rings=5)
    if big:
        for dx in (-0.09, 0.09):
            p.sphere('Body', 'Gold', (dx, -0.4, 0.84), 0.025, seg=5, rings=4)
    m = max(abs(y) for y in yaws)
    for i, y in enumerate(yaws):
        length = (1.1 if big else 0.95) - abs(y) / m * 0.25
        fox_tail(p, f'Tail{i + 1}', (0, 0.66, 0.72), y, 56 - abs(y) * 0.5, length, 0.115 if big else 0.13, 6)


def fan_out(form, deg):
    """Tails spread wider by deg (positive) at the outer ones, none at the centre."""
    yaws = YAWS[form]
    m = max(abs(y) for y in yaws) or 1
    return {f'Tail{i + 1}': R(0, 0, -deg * y / m) for i, y in enumerate(yaws)}


def raise_tails(form, deg):
    return {f'Tail{i + 1}': R(-deg) for i in range(len(YAWS[form]))}


def both(deg_x):
    return {'LegFL': R(deg_x), 'LegFR': R(deg_x)}


CAST = {
    # 1. Wisdom Fire: sit up, one paw reaching out to throw the foxfire
    1: [
        (0, {}),
        (14, {'Rig': R(-18, loc=(0, 0, 0.06)), 'Head': R(-16), 'LegFR': R(-40), 'Tail1': R(-14)}),
        (26, {'Rig': R(-18, loc=(0, 0, 0.06)), 'Head': R(-6), 'LegFR': R(-100), 'EarL': R(0, 0, 10), 'EarR': R(0, 0, -10), 'Tail1': R(-22)}),
        (36, {'Rig': R(-10, loc=(0, 0, 0.04)), 'Head': R(4), 'LegFR': R(-70), 'Tail1': R(-10)}),
        (54, {'Rig': R(-6), 'Head': R(2), 'LegFR': R(-30)}),
        (72, {}),
    ],
    # 2. Illusion Mist: stand tall, the five tails sweep out wide
    2: [
        (0, {}),
        (12, {'Rig': R(-6, loc=(0, 0, 0.05)), 'Head': R(-14), **raise_tails(2, 12), **fan_out(2, 8)}),
        (24, {'Rig': R(-8, loc=(0, 0, 0.08)), 'Head': R(-20), **raise_tails(2, 22), **fan_out(2, 30), 'EarL': R(0, 0, 14), 'EarR': R(0, 0, -14)}),
        (40, {'Rig': R(-8, loc=(0, 0, 0.08)), 'Head': R(-18), **raise_tails(2, 16), **fan_out(2, 18)}),
        (56, {'Rig': R(-2), 'Head': R(-4), **fan_out(2, 6)}),
        (72, {}),
    ],
    # 3. Gate of Knowledge: tails fully fanned and raised, front paws pushing the gate open
    3: [
        (0, {}),
        (14, {'Rig': R(-10, loc=(0, 0, 0.1)), 'Head': R(-12), **raise_tails(3, 10), **fan_out(3, 10), **both(-35)}),
        (26, {'Rig': R(-14, loc=(0, 0, 0.18)), 'Head': R(-18), **raise_tails(3, 24), **fan_out(3, 28), **both(-85), 'EarL': R(0, 0, 14), 'EarR': R(0, 0, -14)}),
        (46, {'Rig': R(-14, loc=(0, 0, 0.2)), 'Head': R(-16), **raise_tails(3, 20), **fan_out(3, 22), **both(-80)}),
        (60, {'Rig': R(-4, loc=(0, 0, 0.04)), 'Head': R(-4), **fan_out(3, 6), **both(-20)}),
        (72, {}),
    ],
}
