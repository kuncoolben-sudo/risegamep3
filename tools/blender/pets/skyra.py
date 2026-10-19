"""Skyra, the storm griffin: a chick (form 1), a young griffin (2) and the full griffin (3)."""
import math

from .kit import Frame, R, wings

PALETTE = {
    'White': '#f2f6fc', 'Blue': '#3d84df', 'Sky': ('#7fd0ff', dict(emit='#4ab4ff', es=0.7)), 'Navy': '#26376a',
    'Gold': ('#e7b83e', dict(rough=0.5)), 'Beak': '#f4c63e', 'Iris': '#27a4ff', 'Pupil': '#0e1c38', 'Sclera': '#ffffff',
    'Shine': ('#ffffff', dict(emit='#ffffff', es=1.0)), 'Gem': ('#76dcff', dict(emit='#38c8ff', es=3.0)), 'Black': '#1b2234',
}
SCALE = {1: 1.0, 2: 1.0, 3: 1.3}


def build(p, form):
    (chick if form == 1 else griffin)(p, form)


def talons(p, piv, sx, x, y, z, length=0.14, r=0.025):
    for dx in (-0.05, 0, 0.05):
        p.cone(piv, 'Gold', (x + dx, y, z + 0.02), (x + dx * 1.5, y - length, z - 0.01), r, 0.004, seg=5)


def chick(p, form):
    p.pivot('Head', (0, -0.06, 0.62))
    p.pivot('WingL', (-0.3, 0.02, 0.5))
    p.pivot('WingR', (0.3, 0.02, 0.5))
    p.pivot('Tail', (0, 0.34, 0.4))
    p.sphere('Body', 'White', (0, 0.04, 0.4), 0.34, (1, 1.05, 0.95))
    p.sphere('Body', 'Blue', (0, 0.14, 0.5), 0.3, (0.95, 0.9, 0.6))
    p.sphere('Body', 'Gem', (0, -0.31, 0.42), 0.045, seg=6, rings=4)
    for sx in (-1, 1):
        p.cone('Body', 'Beak', (sx * 0.12, -0.02, 0.15), (sx * 0.12, -0.04, 0.02), 0.035, 0.03, seg=6)
        talons(p, 'Body', sx, sx * 0.12, -0.04, 0.02, 0.15, 0.022)
    hc = (0, -0.1, 0.86)
    p.sphere('Head', 'White', hc, 0.31, (1.0, 0.95, 0.95))
    p.cone('Head', 'Beak', (0, -0.38, 0.84), (0, -0.54, 0.79), 0.08, 0.0, seg=6)
    p.cone('Head', 'Beak', (0, -0.36, 0.78), (0, -0.49, 0.77), 0.05, 0.0, seg=5)
    for dx, tip in ((0, (0, 0.12, 1.36)), (-0.09, (-0.14, 0.1, 1.3)), (0.09, (0.14, 0.1, 1.3))):
        p.blade('Head', 'Blue', (dx * 0.6, -0.04, 1.12), tip, 0.12, face=(1, 0, 0))
    for sx in (-1, 1):
        p.eye('Head', hc, 0.31, sx, yaw=34, pitch=3, size=0.105)
        n = 'WingL' if sx < 0 else 'WingR'
        fr = Frame((sx * 0.3, 0.02, 0.5), sx, lift=-18, sweep=22)
        p.cone(n, 'Blue', fr.p(0), fr.p(0.2), 0.06, 0.045)
        p.feathers(n, fr, ['Blue', 'Sky'], 5, arm=0.2, lens=(0.36, 0.26), widths=(0.16, 0.16), angles=(12, 70), step=0.01, start=0.02, peak=0.6)
    for dx, tip in ((0, (0, 0.78, 0.6)), (-0.1, (-0.16, 0.72, 0.5)), (0.1, (0.16, 0.72, 0.5))):
        p.blade('Tail', ['Blue', 'Sky'][abs(int(dx * 20)) % 2], (dx * 0.4, 0.34, 0.44), tip, 0.13, face=(0, 0, 1))


def griffin(p, form):
    big = form == 3
    p.pivot('Head', (0, -0.36, 1.02))
    p.pivot('WingL', (-0.25, 0.1, 1.08))
    p.pivot('WingR', (0.25, 0.1, 1.08))
    p.pivot('Tail', (0, 0.74, 0.8))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.2, -0.2, 0.64))
        p.pivot('LegB' + s, (sx * 0.2, 0.5, 0.62))
    # torso
    p.sphere('Body', 'Navy', (0, 0.18, 0.78), 0.38, (0.85, 1.4, 0.85))
    p.sphere('Body', 'White', (0, -0.2, 0.84), 0.3, (0.85, 0.9, 0.85))
    p.sphere('Body', 'Blue', (0, 0.12, 1.02), 0.26, (0.7, 1.25, 0.35))
    p.sphere('Body', 'Gem', (0, -0.47, 0.88), 0.055 if not big else 0.075, seg=8, rings=5)
    for sx in (-1, 1):
        p.sphere('Body', 'Navy', (sx * 0.2, 0.5, 0.62), 0.24, (0.8, 1, 1.05))
        p.box('Body', 'Gold', (sx * 0.3, -0.04, 1.02), (0.13, 0.32, 0.07), rot=(0, 0, -sx * 18))  # shoulder plates
    p.torus('Body', 'Gold', (0, -0.36, 0.98), 0.2, 0.03, rot=(60, 0, 0), seg=14)
    # legs: eagle forelegs, lion-ish hindlegs
    for sx, s in ((-1, 'L'), (1, 'R')):
        f, b = 'LegF' + s, 'LegB' + s
        p.cone(f, 'White', (sx * 0.2, -0.2, 0.66), (sx * 0.2, -0.28, 0.16), 0.085, 0.055)
        p.sphere(f, 'Gold', (sx * 0.2, -0.33, 0.07), 0.09, (1, 1.5, 0.55))
        talons(p, f, sx, sx * 0.2, -0.4, 0.05, 0.14)
        p.cone(b, 'Navy', (sx * 0.2, 0.5, 0.66), (sx * 0.2, 0.5, 0.16), 0.1, 0.06)
        p.sphere(b, 'Gold', (sx * 0.2, 0.44, 0.07), 0.1, (1, 1.5, 0.55))
        talons(p, b, sx, sx * 0.2, 0.34, 0.05, 0.13)
    # neck + head
    p.cone('Head', 'White', (0, -0.3, 0.92), (0, -0.5, 1.3), 0.2, 0.16)
    hc = (0, -0.55, 1.38)
    p.sphere('Head', 'White', hc, 0.25, (0.95, 1.05, 0.95))
    p.cone('Head', 'Beak', (0, -0.72, 1.38), (0, -0.99, 1.26), 0.1, 0.0, seg=6)
    p.cone('Head', 'Beak', (0, -0.95, 1.28), (0, -1.0, 1.15), 0.04, 0.0, seg=5)
    p.cone('Head', 'Beak', (0, -0.72, 1.32), (0, -0.93, 1.26), 0.07, 0.0, seg=5)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.25, sx, yaw=42, pitch=8, size=0.085)
        p.box('Head', 'Navy', (sx * 0.16, -0.7, 1.51), (0.16, 0.06, 0.045), rot=(0, 0, sx * 28))
    n_crest = 7 if big else 5
    for i in range(n_crest):
        dx = (i - (n_crest - 1) / 2) * 0.06
        tipz = 1.55 + (0.5 if big else 0.36) - abs(dx) * 1.6
        p.blade('Head', ['Blue', 'Sky'][i % 2], (dx * 0.5, -0.5, 1.56), (dx * 1.7, 0.14, tipz), 0.1, face=(1, 0, 0))
    if big:
        for sx in (-1, 1):  # gold horn-feathers
            p.blade('Head', 'Gold', (sx * 0.1, -0.5, 1.58), (sx * 0.2, -0.12, 1.98), 0.09, face=(1, 0, 0))
    # wings
    n = 9 if big else 7
    arm = 1.0 if big else 0.9
    for sx in (-1, 1):
        w = 'WingL' if sx < 0 else 'WingR'
        fr = Frame((sx * 0.25, 0.1, 1.08), sx, lift=34, sweep=22, pitch=55)
        p.cone(w, 'Navy', fr.p(0), fr.p(arm), 0.07, 0.04)
        for t in (0.35, 0.7):
            p.sphere(w, 'Gold', fr.p(arm * t, 0, 0.0), 0.06, seg=6, rings=4)
        lens, ang = (1.05, 0.62), (12, 74)
        p.fan(w, 'Navy', fr.p(0.05, 0, -0.012),
              [fr.p(arm, 0, -0.012)] + p.feather_points(fr, n, arm, lens, ang, 0.1, 0.72, w0=-0.012) + [fr.p(0.1, 0.12, -0.012)])
        p.feathers(w, fr, ['Navy', 'Blue'], n, arm, lens, widths=(0.27, 0.25), angles=ang, step=0.012, start=0.1, peak=0.62)
        p.feathers(w, fr, 'White', 5, arm * 0.7, lens=(0.5, 0.3), widths=(0.2, 0.2), angles=(22, 76), step=0.012, start=0.1, w0=0.07, peak=0.6)
        if big:
            p.feathers(w, fr, 'Sky', 4, arm, lens=(0.4, 0.3), widths=(0.1, 0.1), angles=(12, 40), step=0.012, start=0.5, w0=0.09)
    # tail fan
    for i, a in enumerate((-40, -20, 0, 20, 40)):
        r = math.radians(a)
        tip = (math.sin(r) * 0.55, 0.74 + math.cos(r) * (0.7 if big else 0.58), 0.8 + 0.12 - abs(a) * 0.002)
        p.blade('Tail', ['Blue', 'Navy', 'Sky'][i % 3], (0, 0.7, 0.8), tip, 0.16, face=(0, 0, 1))


CAST = {
    # 1. Storm Strike: the chick beats its wings, head back, then thrusts a lightning stream out of its beak
    1: [
        (0, {}),
        (10, {**wings(-25), 'Head': R(10), 'Rig': R(loc=(0, 0, -0.04)), 'Tail': R(-15)}),
        (18, {**wings(55), 'Head': R(-28), 'Rig': R(loc=(0, 0, 0.1))}),
        (26, {**wings(-35), 'Head': R(14), 'Tail': R(8)}),
        (34, {**wings(50), 'Head': R(-18), 'Rig': R(loc=(0, 0, 0.08))}),
        (44, {**wings(-10), 'Head': R(-8)}),
        (58, {**wings(10)}),
        (72, {}),
    ],
    # 2. Thunder Claw: crouch, one claw back, slash forward, then the other
    2: [
        (0, {}),
        (12, {'LegFR': R(55), 'Head': R(10, 0, 8), **wings(30), 'Rig': R(6, loc=(0, 0, -0.05))}),
        (20, {'LegFR': R(-95), 'Head': R(18, 0, -8), **wings(55), 'Rig': R(-4, loc=(0, -0.05, 0.02))}),
        (30, {'LegFR': R(-95), 'Head': R(18, 0, -8), **wings(55)}),
        (36, {'LegFR': R(10), 'LegFL': R(55), 'Head': R(10, 0, -8), **wings(30), 'Rig': R(6, loc=(0, 0, -0.04))}),
        (44, {'LegFL': R(-95), 'Head': R(18, 0, 8), **wings(55), 'Rig': R(-4, loc=(0, -0.05, 0.02))}),
        (54, {'LegFL': R(-95), 'Head': R(14, 0, 6), **wings(45)}),
        (72, {}),
    ],
    # 3. Wings of the Wind: leap up, wings sweep wide and flap while hovering
    3: [
        (0, {}),
        (14, {'Rig': R(loc=(0, 0, -0.06)), **wings(-30), 'Head': R(8)}),
        (24, {'Rig': R(loc=(0, 0, 0.45)), **wings(68), 'Head': R(-22), 'Tail': R(-20), 'LegFL': R(-25), 'LegFR': R(-25),
              'LegBL': R(25), 'LegBR': R(25)}),
        (32, {'Rig': R(loc=(0, 0, 0.5)), **wings(-40), 'Head': R(-16), 'LegFL': R(-25), 'LegFR': R(-25), 'LegBL': R(25), 'LegBR': R(25)}),
        (40, {'Rig': R(loc=(0, 0, 0.45)), **wings(60), 'Head': R(-22), 'LegFL': R(-25), 'LegFR': R(-25), 'LegBL': R(25), 'LegBR': R(25)}),
        (48, {'Rig': R(loc=(0, 0, 0.5)), **wings(-35), 'Head': R(-16), 'LegFL': R(-25), 'LegFR': R(-25), 'LegBL': R(25), 'LegBR': R(25)}),
        (60, {'Rig': R(loc=(0, 0, 0.1)), **wings(20), 'Head': R(-6)}),
        (72, {}),
    ],
}
