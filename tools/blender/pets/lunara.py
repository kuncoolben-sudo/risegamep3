"""Lunara, the moon fairy: a fluffy cub (form 1), a winged young fairy (2) and the four-winged moon fairy (3)."""
import math

from .kit import Frame, R, wings

PALETTE = {
    'White': '#fbf8ff', 'Lav': '#c4b2f4', 'Blue': '#86b8ff', 'PinkIn': '#ffc2dc', 'Pink': '#ffb0d0',
    'Gold': ('#f2c44c', dict(rough=0.4, emit='#d9a21f', es=0.25)), 'Moon': ('#ffd75e', dict(emit='#ffcb3a', es=2.0)),
    'Iris': '#3f7dff', 'Pupil': '#14204a', 'Sclera': '#ffffff', 'Shine': ('#ffffff', dict(emit='#ffffff', es=1.0)),
    'Wing': ('#cdbdff', dict(alpha=0.62, emit='#a58bff', es=0.5)), 'WingTip': ('#9cc4ff', dict(alpha=0.75, emit='#6fa4ff', es=0.6)),
    'Gem': ('#82dcff', dict(emit='#4fb8ff', es=3.0)),
}
SCALE = {1: 1.0, 2: 1.0, 3: 1.25}


def build(p, form):
    (cub if form == 1 else fairy)(p, form)


def crescent(p, piv, c, r, a0=40, a1=320, thick=0.035):
    pts = []
    n = 9
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / (n - 1))
        pts.append((c[0] + math.cos(a) * r, c[1], c[2] + math.sin(a) * r))
    taper = [0.008, 0.02, 0.032, thick, thick, thick, 0.032, 0.02, 0.008]
    p.tube(piv, 'Moon', pts, taper, seg=6)


def ear(p, piv, sx, base, tip, w=0.16):
    p.blade(piv, 'White', base, tip, w, 0.03, face=(0, 1, 0), peak=0.4)
    inner_b = (base[0] + 0.0, base[1] - 0.015, base[2] + 0.02)
    inner_t = (tip[0] - sx * 0.01, tip[1] - 0.015, tip[2] - 0.08)
    p.blade(piv, 'PinkIn', inner_b, inner_t, w * 0.55, 0.02, face=(0, 1, 0), peak=0.4)
    p.blade(piv, 'Blue', (base[0] * 0.3 + tip[0] * 0.7, base[1] * 0.3 + tip[1] * 0.7, base[2] * 0.3 + tip[2] * 0.7), tip, w * 0.4, 0.032, face=(0, 1, 0), peak=0.3)


def cub(p, form):
    p.pivot('Head', (0, -0.22, 0.58))
    p.pivot('EarL', (-0.16, -0.3, 1.0), parent='Head')
    p.pivot('EarR', (0.16, -0.3, 1.0), parent='Head')
    p.pivot('Tail', (0, 0.4, 0.4))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.15, -0.08, 0.26))
        p.pivot('LegB' + s, (sx * 0.18, 0.3, 0.26))
    p.sphere('Body', 'White', (0, 0.1, 0.36), 0.33, (1, 1.15, 0.9))
    p.sphere('Body', 'White', (0, -0.14, 0.42), 0.2, (1, 0.8, 1))
    hc = (0, -0.32, 0.78)
    p.sphere('Head', 'White', hc, 0.31, (1.06, 1.0, 0.95))
    p.sphere('Head', 'White', (0, -0.55, 0.7), 0.12, (1, 1.1, 0.85))
    p.sphere('Head', 'Pink', (0, -0.66, 0.72), 0.03, seg=6, rings=4)
    crescent(p, 'Head', (0, -0.58, 1.0), 0.09, 20, 300, 0.028)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.31, sx, yaw=34, pitch=4, size=0.115, iris='Iris')
        p.sphere('Head', 'PinkIn', (sx * 0.24, -0.5, 0.68), 0.06, (1, 0.3, 0.7), seg=6, rings=4)
        ear(p, 'EarL' if sx < 0 else 'EarR', sx, (sx * 0.16, -0.3, 1.02), (sx * 0.3, -0.24, 1.42))
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'White', (sx * 0.15, -0.08, 0.3), (sx * 0.15, -0.1, 0.1), 0.075, 0.065)
        p.sphere('LegF' + s, 'Blue', (sx * 0.15, -0.12, 0.05), 0.075, (1, 1.3, 0.7))
        p.cone('LegB' + s, 'White', (sx * 0.18, 0.3, 0.3), (sx * 0.18, 0.32, 0.1), 0.09, 0.07)
        p.sphere('LegB' + s, 'Blue', (sx * 0.18, 0.28, 0.05), 0.08, (1, 1.3, 0.7))
    p.torus('Body', 'Gold', (0, -0.3, 0.54), 0.16, 0.022, rot=(65, 0, 0), seg=14)
    p.sphere('Body', 'Gem', (0, -0.42, 0.5), 0.045, seg=6, rings=4)
    path = [(0, 0.45, 0.38), (0, 0.62, 0.5), (0, 0.7, 0.68), (0, 0.62, 0.88)]
    p.fluff_tail('Tail', 'White', 'Blue', path, [0.15, 0.18, 0.2, 0.17], seg=9, rings=7)


def butterfly_wing(p, piv, fr, s, big):
    def ellipse(cu, cv, a, b, rot, n=18):
        pts = []
        c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        for i in range(n + 1):
            t = 2 * math.pi * i / n
            x, y = a * math.cos(t), b * math.sin(t)
            pts.append(fr.p((cu + x * c - y * sn) * s, (cv + x * sn + y * c) * s, 0))
        return pts

    shapes = [(0.5, 0.36, 0.5, 0.36, 25), (0.34, -0.24, 0.32, 0.24, -20)]
    if big:
        shapes = [(0.58, 0.42, 0.6, 0.42, 25), (0.4, -0.3, 0.4, 0.3, -20)]
    for cu, cv, a, b, rot in shapes:
        ring = ellipse(cu, cv, a, b, rot)
        hub = fr.p(cu * s, cv * s, 0)
        p.fan(piv, 'Wing', hub, ring)
        p.fan(piv, 'WingTip', hub, ring[2:7])  # tinted outer panel
        p.tube(piv, 'Gold', ring, 0.014, seg=4, caps=False)
        for k in (3, 6, 9, 12):
            p.tube(piv, 'WingTip', [fr.p(0, 0, 0), ring[k]], 0.008, seg=4)
    p.tube(piv, 'Gold', [fr.p(0, 0, 0), fr.p(0.25 * s, 0.2 * s, 0)], [0.03, 0.02], seg=5)


def fairy(p, form):
    big = form == 3
    p.pivot('Head', (0, -0.3, 0.92))
    p.pivot('EarL', (-0.16, -0.5, 1.4), parent='Head')
    p.pivot('EarR', (0.16, -0.5, 1.4), parent='Head')
    p.pivot('WingL', (-0.16, 0.12, 1.0))
    p.pivot('WingR', (0.16, 0.12, 1.0))
    p.pivot('Tail', (0, 0.75, 0.72))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.16, -0.14, 0.62))
        p.pivot('LegB' + s, (sx * 0.17, 0.5, 0.62))
    p.sphere('Body', 'White', (0, 0.2, 0.74), 0.33, (0.8, 1.5, 0.8))
    p.sphere('Body', 'White', (0, -0.18, 0.84), 0.22, (0.9, 0.9, 1.0))
    p.tube('Head', 'White', [(0, -0.2, 0.82), (0, -0.34, 1.02), (0, -0.42, 1.16)], [0.15, 0.13, 0.12])
    hc = (0, -0.48, 1.24)
    p.sphere('Head', 'White', hc, 0.3, (1.05, 1.0, 0.95))
    p.sphere('Head', 'White', (0, -0.7, 1.15), 0.11, (1, 1.15, 0.85))
    p.sphere('Head', 'Pink', (0, -0.81, 1.16), 0.028, seg=6, rings=4)
    # gold circlet + crescent
    p.tube('Head', 'Gold', [(math.sin(a) * 0.27, -0.5 - math.cos(a) * 0.26, 1.46 + 0.0) for a in [math.radians(x) for x in range(-70, 71, 20)]], 0.016, seg=5)
    crescent(p, 'Head', (0, -0.77, 1.5), 0.1 if not big else 0.13, 20, 300, 0.03)
    p.sphere('Head', 'Gem', (0, -0.78, 1.44), 0.035, seg=6, rings=4)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.3, sx, yaw=36, pitch=4, size=0.115, iris='Iris')
        p.sphere('Head', 'PinkIn', (sx * 0.2, -0.66, 1.18), 0.05, (1, 0.3, 0.7), seg=6, rings=4)
        ear(p, 'EarL' if sx < 0 else 'EarR', sx, (sx * 0.16, -0.5, 1.46), (sx * 0.34, -0.42, 1.92 if big else 1.84), 0.18)
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'White', (sx * 0.16, -0.14, 0.66), (sx * 0.16, -0.17, 0.2), 0.075, 0.05)
        p.cone('LegF' + s, 'Blue', (sx * 0.16, -0.17, 0.22), (sx * 0.16, -0.18, 0.06), 0.05, 0.055)
        p.sphere('LegF' + s, 'Gold', (sx * 0.16, -0.2, 0.04), 0.06, (1, 1.3, 0.6))
        p.cone('LegB' + s, 'White', (sx * 0.17, 0.5, 0.66), (sx * 0.17, 0.52, 0.2), 0.1, 0.055)
        p.cone('LegB' + s, 'Blue', (sx * 0.17, 0.52, 0.22), (sx * 0.17, 0.5, 0.06), 0.055, 0.06)
        p.sphere('LegB' + s, 'Gold', (sx * 0.17, 0.46, 0.04), 0.065, (1, 1.3, 0.6))
        if big:
            p.torus('LegF' + s, 'Gold', (sx * 0.16, -0.17, 0.2), 0.055, 0.014, seg=10)
            p.torus('LegB' + s, 'Gold', (sx * 0.17, 0.52, 0.2), 0.06, 0.014, seg=10)
        fr = Frame((sx * 0.16, 0.12, 1.0), sx, lift=28, sweep=8, pitch=78)
        butterfly_wing(p, 'WingL' if sx < 0 else 'WingR', fr, 1.0 if not big else 1.15, big)
    p.torus('Body', 'Gold', (0, -0.32, 1.0), 0.17, 0.024, rot=(62, 0, 0), seg=14)
    p.sphere('Body', 'Gem', (0, -0.46, 0.93), 0.05 if not big else 0.07, seg=7, rings=5)
    path = [(0, 0.78, 0.7), (0, 1.0, 0.62), (0, 1.2, 0.72), (0, 1.34, 0.94), (0, 1.3, 1.16)]
    p.fluff_tail('Tail', 'White', 'Blue', path, [0.14, 0.18, 0.2, 0.2, 0.17], seg=9, rings=7)
    if big:
        p.blade('Tail', 'Pink', (0, 1.3, 1.0), (0, 1.0, 1.5), 0.14, face=(1, 0, 0))
        p.blade('Tail', 'Lav', (0, 1.32, 1.0), (0, 1.5, 1.4), 0.12, face=(1, 0, 0))


CAST = {
    # 1. Healing Moonlight: sit up on the hind legs, gaze at the moon, ears and tail lifted
    1: [
        (0, {}),
        (14, {'Rig': R(-24, loc=(0, 0, 0.1)), 'Head': R(-26), 'LegFL': R(-35), 'LegFR': R(-35), 'EarL': R(0, 0, 14), 'EarR': R(0, 0, -14), 'Tail': R(-20)}),
        (26, {'Rig': R(-28, loc=(0, 0, 0.11)), 'Head': R(-30), 'LegFL': R(-45, 0, 8), 'LegFR': R(-45, 0, -8), 'EarL': R(0, 0, 18), 'EarR': R(0, 0, -18), 'Tail': R(-26)}),
        (52, {'Rig': R(-26, loc=(0, 0, 0.1)), 'Head': R(-28), 'LegFL': R(-40), 'LegFR': R(-40), 'EarL': R(0, 0, 14), 'EarR': R(0, 0, -14), 'Tail': R(-22)}),
        (64, {'Rig': R(0), 'Head': R(2)}),
        (72, {}),
    ],
    # 2. Moon Ring: a pirouette with fluttering wings
    2: [
        (0, {}),
        (10, {'Rig': R(loc=(0, 0, -0.05)), **wings(-15), 'Head': R(8)}),
        (22, {'Rig': R(0, 0, 130, loc=(0, 0, 0.25)), **wings(40), 'Head': R(-10), 'Tail': R(0, 0, 25)}),
        (36, {'Rig': R(0, 0, 250, loc=(0, 0, 0.32)), **wings(-5), 'Head': R(-10), 'Tail': R(0, 0, -25)}),
        (50, {'Rig': R(0, 0, 350, loc=(0, 0, 0.25)), **wings(35), 'Head': R(-6)}),
        (62, {'Rig': R(0, 0, 360, loc=(0, 0, 0)), **wings(10)}),
        (72, {'Rig': R(0, 0, 360)}),
    ],
    # 3. Moonlight Wings: lift off, wings wide, slow beats, head to the moon
    3: [
        (0, {}),
        (12, {'Rig': R(loc=(0, 0, -0.06)), **wings(-20), 'Head': R(8)}),
        (24, {'Rig': R(loc=(0, 0, 0.55)), **wings(62), 'Head': R(-18), 'Tail': R(-18), 'LegFL': R(-20), 'LegFR': R(-20), 'LegBL': R(20), 'LegBR': R(20)}),
        (36, {'Rig': R(loc=(0, 0, 0.6)), **wings(-8), 'Head': R(-14), 'LegFL': R(-20), 'LegFR': R(-20), 'LegBL': R(20), 'LegBR': R(20)}),
        (48, {'Rig': R(loc=(0, 0, 0.55)), **wings(58), 'Head': R(-18), 'LegFL': R(-20), 'LegFR': R(-20), 'LegBL': R(20), 'LegBR': R(20)}),
        (60, {'Rig': R(loc=(0, 0, 0.12)), **wings(15), 'Head': R(-4)}),
        (72, {}),
    ],
}

