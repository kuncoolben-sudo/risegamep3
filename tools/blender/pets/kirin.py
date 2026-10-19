"""Kirin, the forest guardian: a leaf-crowned cub (form 1), a maned kirin with antlers (2) and the divine kirin (3)."""
import math

from .kit import Frame, R

PALETTE = {
    'Cream': '#f6ecd0', 'Tan': '#e0c48f', 'Green': '#2fa56a', 'LeafG': '#52c76d', 'Teal': '#21a2a6', 'DeepTeal': '#17728a',
    'Gold': ('#e8bd4a', dict(rough=0.5)), 'Iris': '#27d3b0', 'Pupil': '#0b2a29', 'Sclera': '#f6fff6',
    'Shine': ('#ffffff', dict(emit='#ffffff', es=1.0)), 'Glow': ('#9bffb8', dict(emit='#4dff86', es=3.0)),
    'Dark': '#264646', 'Hoof': '#2a4a4a',
}
SCALE = {1: 1.0, 2: 1.05, 3: 1.3}


def build(p, form):
    (cub if form == 1 else adult)(p, form)


def leaf_fan(p, piv, base, tips, w, mats, face=(0, 1, 0)):
    for i, t in enumerate(tips):
        p.blade(piv, mats[i % len(mats)], base, t, w, 0.025, face=face, peak=0.5)


def cub(p, form):
    p.pivot('Head', (0, -0.22, 0.6))
    p.pivot('Tail', (0, 0.4, 0.4))
    p.pivot('LeafL', (-0.2, 0.1, 0.66))
    p.pivot('LeafR', (0.2, 0.1, 0.66))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.17, -0.08, 0.3))
        p.pivot('LegB' + s, (sx * 0.2, 0.32, 0.3))
    p.sphere('Body', 'Cream', (0, 0.1, 0.38), 0.34, (1, 1.2, 0.95))
    p.sphere('Body', 'Green', (0, 0.12, 0.52), 0.28, (0.85, 1.1, 0.5))
    hc = (0, -0.34, 0.8)
    p.sphere('Head', 'Cream', hc, 0.3, (1.05, 1.0, 0.95))
    p.sphere('Head', 'Cream', (0, -0.57, 0.72), 0.14, (1, 1.2, 0.85))
    p.sphere('Head', 'Dark', (0, -0.7, 0.75), 0.035, seg=6, rings=4)
    leaf_fan(p, 'Head', (0, -0.3, 1.04), [(0, -0.05, 1.42), (-0.12, -0.12, 1.36), (0.12, -0.12, 1.36), (-0.22, -0.18, 1.24), (0.22, -0.18, 1.24)],
             0.14, ['LeafG', 'Green'])
    for sx in (-1, 1):
        p.eye('Head', hc, 0.3, sx, yaw=36, pitch=6, size=0.1, iris='Iris')
        p.blade('Head', 'Tan', (sx * 0.2, -0.3, 1.0), (sx * 0.36, -0.24, 1.22), 0.13, face=(0, 1, 0))
        p.blade('Head', 'Teal', (sx * 0.21, -0.32, 1.02), (sx * 0.33, -0.27, 1.17), 0.07, face=(0, 1, 0))
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'Cream', (sx * 0.17, -0.08, 0.34), (sx * 0.17, -0.1, 0.16), 0.09, 0.075)
        p.cone('LegF' + s, 'Green', (sx * 0.17, -0.1, 0.18), (sx * 0.17, -0.11, 0.06), 0.08, 0.085)
        p.sphere('LegF' + s, 'Hoof', (sx * 0.17, -0.14, 0.04), 0.08, (1, 1.3, 0.55))
        p.cone('LegB' + s, 'Cream', (sx * 0.2, 0.32, 0.36), (sx * 0.2, 0.34, 0.16), 0.11, 0.08)
        p.cone('LegB' + s, 'Green', (sx * 0.2, 0.34, 0.18), (sx * 0.2, 0.33, 0.06), 0.08, 0.085)
        p.sphere('LegB' + s, 'Hoof', (sx * 0.2, 0.3, 0.04), 0.085, (1, 1.3, 0.55))
        fr = Frame((sx * 0.2, 0.1, 0.66), sx, lift=50, sweep=20, pitch=50)
        p.feathers('LeafL' if sx < 0 else 'LeafR', fr, ['LeafG', 'Green'], 3, 0.1, lens=(0.3, 0.22), widths=(0.12, 0.12), angles=(10, 50), step=0.01, start=0.02)
    path = [(0, 0.4, 0.36), (0, 0.62, 0.4), (0, 0.8, 0.5)]
    p.tube('Tail', 'Cream', path, [0.1, 0.08, 0.06])
    p.sphere('Tail', 'Teal', (0, 0.88, 0.56), 0.13, (1, 1.3, 1))
    p.sphere('Tail', 'DeepTeal', (0, 0.98, 0.64), 0.1, (1, 1.2, 1))
    leaf_fan(p, 'Tail', (0, 0.92, 0.6), [(0, 1.14, 0.84), (-0.1, 1.1, 0.78), (0.1, 1.1, 0.78)], 0.1, ['Teal', 'LeafG'], face=(1, 0, 0))


def adult(p, form):
    big = form == 3
    p.pivot('Head', (0, -0.32, 0.82))
    p.pivot('Mane', (0, -0.58, 1.18), parent='Head')
    p.pivot('Tail', (0, 0.76, 0.62))
    p.pivot('LeafL', (-0.3, 0.15, 1.0))
    p.pivot('LeafR', (0.3, 0.15, 1.0))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.26, -0.12, 0.68))
        p.pivot('LegB' + s, (sx * 0.28, 0.5, 0.66))
    p.sphere('Body', 'Cream', (0, 0.22, 0.7), 0.38, (0.9, 1.45, 0.85))
    p.sphere('Body', 'Tan', (0, 0.08, 0.56), 0.3, (0.7, 1.2, 0.6))
    p.sphere('Body', 'Green', (0, 0.2, 0.98), 0.24, (0.75, 1.3, 0.3))
    for i in range(4):
        y = -0.05 + i * 0.2
        p.blade('Body', 'LeafG' if i % 2 else 'Green', (0, y, 0.98), (0, y + 0.1, 1.24 - i * 0.03), 0.13, face=(1, 0, 0))
    for sx in (-1, 1):
        p.sphere('Body', 'Cream', (sx * 0.28, 0.5, 0.58), 0.26)
        p.box('Body', 'Gold', (sx * 0.34, -0.02, 0.98), (0.13, 0.3, 0.06), rot=(0, 0, -sx * 18))
    p.tube('Head', 'Cream', [(0, -0.3, 0.78), (0, -0.45, 0.98), (0, -0.55, 1.1)], [0.22, 0.2, 0.18])
    p.sphere('Body', 'Glow', (0, -0.42, 0.9), 0.06 if not big else 0.08, seg=8, rings=5)
    hc = (0, -0.6, 1.18)
    p.sphere('Head', 'Cream', hc, 0.27, (1.0, 1.05, 0.95))
    p.sphere('Head', 'Cream', (0, -0.83, 1.09), 0.15, (1, 1.2, 0.8))
    p.sphere('Head', 'Dark', (0, -0.96, 1.12), 0.035, seg=6, rings=4)
    # mane halo around the face + leafy crown
    for i in range(12):
        a = 2 * math.pi * i / 12
        p.sphere('Mane', ['Teal', 'DeepTeal'][i % 2], (math.cos(a) * 0.36, -0.5, 1.18 + math.sin(a) * 0.34), 0.15, (1, 1.1, 1), seg=8, rings=6)
    for i in range(7 if big else 5):
        a = math.radians(25 + i * (130 / (6 if big else 4)))
        r1, r2 = 0.34, 0.62 if big else 0.55
        p.blade('Mane', 'LeafG' if i % 2 else 'Green', (math.cos(a) * r1, -0.5, 1.18 + math.sin(a) * r1),
                (math.cos(a) * r2, -0.46, 1.18 + math.sin(a) * r2), 0.14, face=(0, 1, 0), peak=0.55)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.27, sx, yaw=40, pitch=8, size=0.085, iris='Iris')
        p.box('Head', 'Green', (sx * 0.15, -0.78, 1.34), (0.14, 0.05, 0.04), rot=(0, 0, sx * 22))
        p.blade('Head', 'Tan', (sx * 0.2, -0.5, 1.38), (sx * 0.34, -0.42, 1.56), 0.12, face=(0, 1, 0))
        # gold antlers
        top = 2.2 if big else 2.0
        p.tube('Head', 'Gold', [(sx * 0.1, -0.56, 1.4), (sx * 0.22, -0.5, 1.75), (sx * 0.36, -0.4, top)], [0.055, 0.042, 0.012], seg=6)
        p.tube('Head', 'Gold', [(sx * 0.16, -0.54, 1.6), (sx * 0.36, -0.5, 1.78)], [0.04, 0.012], seg=5)
        if big:
            p.tube('Head', 'Gold', [(sx * 0.27, -0.45, 1.88), (sx * 0.48, -0.4, 2.02)], [0.038, 0.012], seg=5)
            p.tube('Head', 'Gold', [(sx * 0.11, -0.55, 1.5), (sx * 0.0, -0.6, 1.72)], [0.032, 0.01], seg=5)
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'Cream', (sx * 0.26, -0.12, 0.7), (sx * 0.26, -0.15, 0.3), 0.11, 0.085)
        p.cone('LegF' + s, 'Green', (sx * 0.26, -0.15, 0.32), (sx * 0.26, -0.17, 0.08), 0.09, 0.1)
        p.sphere('LegF' + s, 'Teal', (sx * 0.26, -0.13, 0.22), 0.08)
        p.sphere('LegF' + s, 'Hoof', (sx * 0.26, -0.2, 0.05), 0.09, (1, 1.3, 0.55))
        p.cone('LegB' + s, 'Cream', (sx * 0.28, 0.5, 0.68), (sx * 0.28, 0.52, 0.3), 0.14, 0.09)
        p.cone('LegB' + s, 'Green', (sx * 0.28, 0.52, 0.32), (sx * 0.28, 0.5, 0.08), 0.09, 0.1)
        p.sphere('LegB' + s, 'Teal', (sx * 0.28, 0.54, 0.22), 0.08)
        p.sphere('LegB' + s, 'Hoof', (sx * 0.28, 0.45, 0.05), 0.095, (1, 1.3, 0.55))
        fr = Frame((sx * 0.3, 0.15, 1.0), sx, lift=48, sweep=26, pitch=58)
        p.feathers('LeafL' if sx < 0 else 'LeafR', fr, ['LeafG', 'Green'], 6 if big else 3, 0.3, lens=(0.95 if big else 0.55, 0.55 if big else 0.4),
                   widths=(0.26, 0.24), angles=(10, 72), step=0.012, start=0.04, peak=0.5)
    path = [(0, 0.76, 0.6), (0, 1.02, 0.5), (0, 1.28, 0.55)]
    p.tube('Tail', 'Cream', path, [0.13, 0.1, 0.08])
    p.sphere('Tail', 'Teal', (0, 1.36, 0.6), 0.18, (1, 1.4, 1))
    p.sphere('Tail', 'DeepTeal', (0, 1.52, 0.67), 0.15, (1, 1.3, 1))
    leaf_fan(p, 'Tail', (0, 1.5, 0.66), [(0, 1.84, 0.86), (-0.12, 1.78, 0.8), (0.12, 1.78, 0.8)], 0.13, ['Teal', 'LeafG'], face=(1, 0, 0))
    if big:
        p.cone('Tail', 'Glow', (0, 1.6, 0.74), (0, 1.84, 1.18), 0.1, 0.0, seg=6)
        p.sphere('Tail', 'Glow', (0, 1.6, 0.76), 0.09, seg=7, rings=5)
        p.sphere('Head', 'Glow', (0, -0.82, 1.38), 0.045, seg=6, rings=4)


CAST = {
    # 1. Root Power: stomp twice, crest flared
    1: [
        (0, {}),
        (8, {'LegFL': R(-50), 'LegFR': R(-50), 'Head': R(-12), 'Rig': R(-6, loc=(0, 0, 0.02))}),
        (14, {'LegFL': R(5), 'LegFR': R(5), 'Head': R(10), 'Rig': R(2, loc=(0, 0, -0.03))}),
        (22, {'LegFL': R(-50), 'LegFR': R(-50), 'Head': R(-14), 'Rig': R(-6, loc=(0, 0, 0.02)), 'LeafL': R(0, 0, 25), 'LeafR': R(0, 0, -25)}),
        (28, {'LegFL': R(5), 'LegFR': R(5), 'Head': R(12), 'Rig': R(2, loc=(0, 0, -0.04))}),
        (46, {'Head': R(8), 'Rig': R(1), 'Tail': R(0, 0, 18)}),
        (62, {'Head': R(2)}),
        (72, {}),
    ],
    # 2. Poison Leaf: mane flares, head lunges, tail whips
    2: [
        (0, {}),
        (12, {'Head': R(-14), 'Mane': R(sc=1.05), 'Rig': R(-6, loc=(0, 0, 0.02)), 'Tail': R(-10)}),
        (22, {'Head': R(18, 0, 8), 'Mane': R(sc=1.28), 'Rig': R(4, loc=(0, -0.05, 0)), 'Tail': R(0, 0, 35), 'LeafL': R(0, 30, 0), 'LeafR': R(0, -30, 0)}),
        (34, {'Head': R(16, 0, -8), 'Mane': R(sc=1.25), 'Tail': R(0, 0, -35), 'LeafL': R(0, 10, 0), 'LeafR': R(0, -10, 0)}),
        (48, {'Head': R(14, 0, 6), 'Mane': R(sc=1.2), 'Tail': R(0, 0, 25)}),
        (62, {'Head': R(2), 'Mane': R(sc=1.05)}),
        (72, {}),
    ],
    # 3. Forest Storm: rear up, leaf wings spread, antlers raised
    3: [
        (0, {}),
        (14, {'Rig': R(-24, loc=(0, 0, 0.1)), 'Head': R(-22), 'Mane': R(sc=1.2), 'LegFL': R(-40), 'LegFR': R(-40), 'LeafL': R(0, 25, 0), 'LeafR': R(0, -25, 0)}),
        (26, {'Rig': R(-28, loc=(0, 0, 0.12)), 'Head': R(-26), 'Mane': R(sc=1.35), 'LegFL': R(-55), 'LegFR': R(-55), 'LeafL': R(0, 45, 0), 'LeafR': R(0, -45, 0), 'Tail': R(-20)}),
        (44, {'Rig': R(-26, loc=(0, 0, 0.11)), 'Head': R(-24), 'Mane': R(sc=1.3), 'LegFL': R(-50), 'LegFR': R(-50), 'LeafL': R(0, 35, 0), 'LeafR': R(0, -35, 0)}),
        (56, {'Rig': R(6), 'Head': R(12), 'Mane': R(sc=1.1), 'LeafL': R(0, 10, 0), 'LeafR': R(0, -10, 0)}),
        (72, {}),
    ],
}
