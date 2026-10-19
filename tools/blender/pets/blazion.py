"""Blazion, the fire dragon: a hatchling (form 1), a winged young dragon (2) and the armoured dragon (3)."""
import math

from .kit import Frame, R, wings

PALETTE = {
    'Red': '#d9482b', 'DarkRed': '#9d2e1c', 'Cream': '#f6dfb2', 'Horn': '#f4e3a6', 'Dark': '#37282d',
    'Membrane': '#f27a2e', 'Fire': ('#ffb43c', dict(emit='#ff8a1f', es=3.0)), 'Iris': '#ffc83a', 'Pupil': '#2a1410',
    'Sclera': '#fff6df', 'Shine': ('#ffffff', dict(emit='#ffffff', es=1.0)), 'Gold': '#e7b83e',
}
SCALE = {1: 1.0, 2: 1.15, 3: 1.4}


def build(p, form):
    (baby if form == 1 else adult)(p, form)


def claws(p, piv, x, y, z, n=3, length=0.12):
    for i in range(n):
        dx = (i - (n - 1) / 2) * 0.05
        p.cone(piv, 'Horn', (x + dx, y, z + 0.02), (x + dx * 1.4, y - length, z - 0.01), 0.022, 0.004, seg=5)


def flame(p, piv, base, h=0.3, r=0.08):
    x, y, z = base
    p.cone(piv, 'Fire', (x, y, z), (x, y + h * 0.25, z + h), r, 0.0, seg=6)
    p.sphere(piv, 'Fire', (x, y, z + 0.02), r * 0.9, seg=7, rings=5)


def baby(p, form):
    p.pivot('Head', (0, -0.22, 0.62))
    p.pivot('Jaw', (0, -0.5, 0.66), parent='Head')
    p.pivot('Tail', (0, 0.42, 0.34))
    p.pivot('WingL', (-0.27, 0.1, 0.62))
    p.pivot('WingR', (0.27, 0.1, 0.62))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.2, -0.08, 0.36))
        p.pivot('LegB' + s, (sx * 0.22, 0.34, 0.36))
    p.sphere('Body', 'Red', (0, 0.12, 0.4), 0.36, (1, 1.25, 0.95))
    p.sphere('Body', 'Cream', (0, -0.1, 0.3), 0.3, (0.8, 0.85, 0.8))
    for i in range(5):
        y = -0.02 + i * 0.15
        top = 0.4 + 0.342 * math.sqrt(max(0.0, 1 - ((y - 0.12) / 0.45) ** 2))
        p.cone('Body', 'Dark', (0, y, top - 0.03), (0, y + 0.05, top + 0.12 - i * 0.015), 0.05, 0.0, seg=5)
    hc = (0, -0.4, 0.8)
    p.sphere('Head', 'Red', hc, 0.3, (1.05, 1.0, 0.95))
    p.sphere('Head', 'Red', (0, -0.62, 0.74), 0.17, (1.0, 1.1, 0.8))
    p.sphere('Jaw', 'Cream', (0, -0.55, 0.64), 0.13, (1.0, 1.4, 0.55))
    for sx in (-1, 1):
        p.sphere('Head', 'Dark', (sx * 0.06, -0.77, 0.79), 0.025, seg=5, rings=4)
        p.eye('Head', hc, 0.3, sx, yaw=36, pitch=10, size=0.1, iris='Iris')
        p.tube('Head', 'Horn', [(sx * 0.14, -0.36, 1.04), (sx * 0.2, -0.3, 1.2), (sx * 0.23, -0.16, 1.32)], [0.06, 0.045, 0.012], seg=6)
        p.blade('Head', 'DarkRed', (sx * 0.27, -0.3, 0.86), (sx * 0.46, -0.18, 0.96), 0.12, face=(0, 0, 1))
        p.blade('WingL' if sx < 0 else 'WingR', 'DarkRed', (sx * 0.28, 0.1, 0.64), (sx * 0.46, 0.22, 0.82), 0.13, face=(0, 0, 1))
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'Red', (sx * 0.2, -0.08, 0.4), (sx * 0.2, -0.12, 0.1), 0.1, 0.085)
        p.sphere('LegF' + s, 'DarkRed', (sx * 0.2, -0.16, 0.06), 0.1, (1, 1.35, 0.6))
        claws(p, 'LegF' + s, sx * 0.2, -0.24, 0.05, 3, 0.1)
        p.cone('LegB' + s, 'Red', (sx * 0.22, 0.34, 0.42), (sx * 0.22, 0.36, 0.1), 0.13, 0.09)
        p.sphere('LegB' + s, 'DarkRed', (sx * 0.22, 0.3, 0.06), 0.11, (1, 1.35, 0.6))
        claws(p, 'LegB' + s, sx * 0.22, 0.22, 0.05, 3, 0.1)
    path = [(0, 0.4, 0.3), (0, 0.62, 0.2), (0, 0.84, 0.2), (0, 1.02, 0.3), (0, 1.12, 0.46)]
    p.tube('Tail', 'Red', path, [0.17, 0.13, 0.1, 0.07, 0.04])
    for pt in path[1:4]:
        p.cone('Tail', 'Dark', (pt[0], pt[1], pt[2] + 0.06), (pt[0], pt[1] + 0.04, pt[2] + 0.2), 0.04, 0.0, seg=5)
    flame(p, 'Tail', (0, 1.12, 0.5), 0.3, 0.08)


def dragon_wing(p, piv, fr, s, fingers):
    """Bat-like wing in the frame fr: bones + a scalloped membrane."""
    tips = [(1.35, 0.1), (1.32, 0.52), (1.12, 0.92), (0.8, 1.18), (0.45, 1.3)][:fingers] if fingers > 4 else [(1.35, 0.1), (1.28, 0.62), (1.0, 1.05), (0.6, 1.25)]
    S = fr.p(0, 0, 0)
    E = fr.p(0.38 * s, -0.12 * s, 0.05 * s)
    W = fr.p(0.78 * s, -0.04 * s, 0)
    tp = [fr.p(u * s, v * s, 0) for u, v in tips]
    hub = fr.p(0.55 * s, 0.5 * s, 0)
    ring = [W]
    for i, t in enumerate(tp):
        ring.append(t)
        if i + 1 < len(tp):
            mid = (t + tp[i + 1]) / 2
            ring.append(S + (mid - S) * 0.84)
    ring.append(fr.p(0.08 * s, 0.92 * s, 0))
    p.fan(piv, 'Membrane', hub, ring)
    p.tube(piv, 'DarkRed', [S, E, W], [0.075, 0.055, 0.04], seg=6)
    for t in tp:
        p.tube(piv, 'DarkRed', [W, (W + t) / 2, t], [0.035, 0.025, 0.01], seg=5)
    p.cone(piv, 'Horn', W, W + fr.w * 0.14 - fr.v * 0.08, 0.035, 0.0, seg=5)


def adult(p, form):
    big = form == 3
    p.pivot('Head', (0, -0.32, 0.8))
    p.pivot('Jaw', (0, -0.64, 1.14), parent='Head')
    p.pivot('Tail', (0, 0.72, 0.55))
    p.pivot('WingL', (-0.32, 0.1, 0.98))
    p.pivot('WingR', (0.32, 0.1, 0.98))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.28, -0.1, 0.64))
        p.pivot('LegB' + s, (sx * 0.3, 0.5, 0.62))
    p.sphere('Body', 'Red', (0, 0.2, 0.62), 0.4, (0.9, 1.45, 0.85))
    p.sphere('Body', 'Cream', (0, -0.02, 0.5), 0.34, (0.72, 1.25, 0.7))
    for i in range(6):
        y = -0.22 + i * 0.15
        top = 0.62 + 0.34 * math.sqrt(max(0.0, 1 - ((y - 0.2) / 0.58) ** 2))
        p.cone('Body', 'Dark', (0, y, top - 0.03), (0, y + 0.06, top + (0.2 if big else 0.14) - i * 0.015), 0.06, 0.0, seg=5)
    for sx in (-1, 1):
        p.sphere('Body', 'Red', (sx * 0.28, 0.5, 0.55), 0.27)
    # neck + head
    p.tube('Head', 'Red', [(0, -0.3, 0.72), (0, -0.42, 0.92), (0, -0.5, 1.1)], [0.22, 0.19, 0.17])
    p.sphere('Head', 'Cream', (0, -0.5, 0.9), 0.15, (0.8, 0.8, 1.4))
    hc = (0, -0.58, 1.22)
    p.sphere('Head', 'Red', hc, 0.27, (1.0, 1.05, 0.92))
    p.sphere('Head', 'Red', (0, -0.82, 1.14), 0.17, (1.0, 1.2, 0.8))
    p.sphere('Jaw', 'Cream', (0, -0.8, 1.07), 0.13, (1.0, 1.5, 0.5))
    for sx in (-1, 1):
        p.sphere('Head', 'Dark', (sx * 0.06, -0.99, 1.19), 0.025, seg=5, rings=4)
        p.eye('Head', hc, 0.27, sx, yaw=40, pitch=9, size=0.085, iris='Iris')
        p.box('Head', 'Dark', (sx * 0.16, -0.76, 1.37), (0.16, 0.06, 0.045), rot=(0, 0, sx * 26))
        p.tube('Head', 'Horn', [(sx * 0.14, -0.5, 1.42), (sx * 0.24, -0.36, 1.62), (sx * 0.3, -0.12, 1.72)], [0.07, 0.05, 0.012], seg=6)
        p.tube('Head', 'Horn', [(sx * 0.22, -0.46, 1.28), (sx * 0.36, -0.38, 1.36), (sx * 0.44, -0.26, 1.34)], [0.045, 0.03, 0.01], seg=5)
        p.blade('Head', 'DarkRed', (sx * 0.28, -0.56, 1.16), (sx * 0.5, -0.46, 1.1), 0.14, face=(0, 0, 1))
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'Red', (sx * 0.28, -0.1, 0.66), (sx * 0.28, -0.14, 0.14), 0.12, 0.08)
        p.sphere('LegF' + s, 'DarkRed', (sx * 0.28, -0.19, 0.07), 0.11, (1, 1.4, 0.6))
        claws(p, 'LegF' + s, sx * 0.28, -0.28, 0.06, 3, 0.12)
        p.cone('LegB' + s, 'Red', (sx * 0.3, 0.5, 0.64), (sx * 0.3, 0.52, 0.14), 0.15, 0.09)
        p.sphere('LegB' + s, 'DarkRed', (sx * 0.3, 0.46, 0.07), 0.12, (1, 1.4, 0.6))
        claws(p, 'LegB' + s, sx * 0.3, 0.36, 0.06, 3, 0.12)
        fr = Frame((sx * 0.32, 0.1, 0.98), sx, lift=40, sweep=22, pitch=52)
        dragon_wing(p, 'WingL' if sx < 0 else 'WingR', fr, 1.15 if big else 1.0, 5 if big else 4)
        if big:
            p.sphere('Body', 'Dark', (sx * 0.4, 0.0, 0.96), 0.18, (1, 1.2, 0.8))
            p.cone('Body', 'Dark', (sx * 0.4, 0.0, 1.02), (sx * 0.52, -0.02, 1.3), 0.08, 0.0, seg=5)
            p.tube('Head', 'Horn', [(sx * 0.06, -0.48, 1.46), (sx * 0.08, -0.4, 1.66), (sx * 0.06, -0.3, 1.8)], [0.05, 0.035, 0.01], seg=5)
    path = [(0, 0.7, 0.55), (0, 1.0, 0.4), (0, 1.35, 0.35), (0, 1.65, 0.45), (0, 1.85, 0.65)]
    p.tube('Tail', 'Red', path, [0.2, 0.16, 0.12, 0.08, 0.04])
    for pt in path[1:4]:
        p.cone('Tail', 'Dark', (pt[0], pt[1], pt[2] + 0.1), (pt[0], pt[1] + 0.05, pt[2] + 0.3), 0.05, 0.0, seg=5)
    flame(p, 'Tail', (0, 1.86, 0.7), 0.42 if big else 0.34, 0.1)
    if big:
        p.sphere('Body', 'Fire', (0, -0.38, 0.74), 0.075, seg=8, rings=5)
        p.torus('Body', 'Gold', (0, -0.38, 0.74), 0.11, 0.025, rot=(90, 0, 0), seg=14)


CAST = {
    # 1. Flame Breath: head back, then a long jet out of the open mouth
    1: [
        (0, {}),
        (10, {'Head': R(-30), 'Jaw': R(12), 'Rig': R(-8), 'Tail': R(-25)}),
        (18, {'Head': R(12), 'Jaw': R(38), 'Rig': R(6), 'Tail': R(20)}),
        (30, {'Head': R(8, 0, 6), 'Jaw': R(40), 'Rig': R(5), 'Tail': R(14)}),
        (44, {'Head': R(10, 0, -6), 'Jaw': R(40), 'Rig': R(5), 'Tail': R(16)}),
        (58, {'Head': R(2), 'Jaw': R(6)}),
        (72, {}),
    ],
    # 2. Fire Blast: rear up with spread wings, then slam down and blast
    2: [
        (0, {}),
        (12, {'Rig': R(-28, loc=(0, 0, 0.1)), 'Head': R(-30), 'Jaw': R(25), **wings(40), 'LegFL': R(-35), 'LegFR': R(-35), 'Tail': R(-15)}),
        (22, {'Rig': R(8, loc=(0, -0.05, 0)), 'Head': R(25), 'Jaw': R(40), **wings(-15), 'LegFL': R(20), 'LegFR': R(20), 'Tail': R(15)}),
        (40, {'Rig': R(6), 'Head': R(22), 'Jaw': R(38), **wings(-8), 'LegFL': R(15), 'LegFR': R(15)}),
        (56, {'Rig': R(0), 'Head': R(4), 'Jaw': R(6), **wings(10)}),
        (72, {}),
    ],
    # 3. Dragon Fire Wheel: crouch, leap, spin a full turn with wings wide, land
    3: [
        (0, {}),
        (10, {'Rig': R(loc=(0, 0, -0.08)), **wings(-20), 'Head': R(10)}),
        (20, {'Rig': R(0, 0, 90, loc=(0, 0, 0.35)), **wings(55), 'Head': R(-22), 'Jaw': R(30), 'LegFL': R(-20), 'LegFR': R(-20)}),
        (34, {'Rig': R(0, 0, 230, loc=(0, 0, 0.4)), **wings(40), 'Head': R(-18), 'Jaw': R(30), 'LegFL': R(-20), 'LegFR': R(-20)}),
        (48, {'Rig': R(0, 0, 360, loc=(0, 0, 0.3)), **wings(30), 'Head': R(-10), 'Jaw': R(20)}),
        (60, {'Rig': R(0, 0, 360, loc=(0, 0, 0.0)), **wings(10), 'Head': R(2)}),
        (72, {'Rig': R(0, 0, 360)}),
    ],
}
