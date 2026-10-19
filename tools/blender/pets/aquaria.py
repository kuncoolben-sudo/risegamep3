"""Aquaria, the water dragon: a baby (form 1), a fin-winged young dragon (2) and the sea queen (3)."""
import math

from .kit import Frame, R, wings

PALETTE = {
    'Blue': '#52c6ee', 'Cyan': '#9aeaff', 'Deep': '#2b8fd2', 'Pink': '#ff9ec9', 'PinkLt': '#ffe0ee',
    'Gold': ('#f2b84a', dict(rough=0.4, emit='#d99a1f', es=0.25)), 'Iris': '#7a52d8', 'Pupil': '#1c1040', 'Sclera': '#ffffff',
    'Shine': ('#ffffff', dict(emit='#ffffff', es=1.0)),
    'Fin': ('#ff9ed0', dict(alpha=0.72, emit='#ff7fc0', es=0.3)), 'FinBlue': ('#7fe0ff', dict(alpha=0.7, emit='#4fc8ff', es=0.5)),
    'Water': ('#8ff3ff', dict(alpha=0.62, emit='#5fe8ff', es=1.6)), 'Gem': ('#8aeaff', dict(emit='#4fd0ff', es=3.0)),
}
SCALE = {1: 1.0, 2: 1.05, 3: 1.3}


def build(p, form):
    (baby if form == 1 else adult)(p, form)


def tail_fan(p, piv, base, length, mats=('FinBlue', 'Fin'), n=5, spread=100):
    y0, z0 = base[1], base[2]
    for i in range(n):
        a = math.radians(-spread / 2 + spread * i / (n - 1))
        tip = (base[0], y0 + math.cos(a) * length, z0 + math.sin(a) * length)
        p.blade(piv, mats[i % len(mats)], base, tip, length * 0.4, 0.02, face=(1, 0, 0), peak=0.6)


def baby(p, form):
    p.pivot('Head', (0, -0.22, 0.6))
    p.pivot('EarL', (-0.26, -0.3, 0.88), parent='Head')
    p.pivot('EarR', (0.26, -0.3, 0.88), parent='Head')
    p.pivot('WingL', (-0.28, 0.1, 0.6))
    p.pivot('WingR', (0.28, 0.1, 0.6))
    p.pivot('Tail', (0, 0.42, 0.34))
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.19, -0.08, 0.34))
        p.pivot('LegB' + s, (sx * 0.21, 0.32, 0.34))
    p.sphere('Body', 'Blue', (0, 0.12, 0.4), 0.34, (1, 1.2, 0.95))
    p.sphere('Body', 'PinkLt', (0, -0.08, 0.32), 0.28, (0.8, 0.85, 0.8))
    hc = (0, -0.34, 0.8)
    p.sphere('Head', 'Blue', hc, 0.31, (1.06, 1.0, 0.95))
    p.sphere('Head', 'Blue', (0, -0.57, 0.72), 0.14, (1, 1.15, 0.85))
    p.sphere('Head', 'Pink', (0, -0.69, 0.74), 0.03, seg=6, rings=4)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.31, sx, yaw=34, pitch=6, size=0.115, iris='Iris')
        p.sphere('Head', 'Pink', (sx * 0.24, -0.5, 0.68), 0.06, (1, 0.3, 0.7), seg=6, rings=4)
        p.tube('Head', 'Gold', [(sx * 0.13, -0.34, 1.04), (sx * 0.2, -0.3, 1.22), (sx * 0.3, -0.2, 1.34)], [0.055, 0.04, 0.012], seg=6)
        e = 'EarL' if sx < 0 else 'EarR'
        p.blade(e, 'Fin', (sx * 0.26, -0.3, 0.88), (sx * 0.52, -0.2, 1.08), 0.15, face=(0, 1, 0))
        p.blade(e, 'FinBlue', (sx * 0.27, -0.3, 0.9), (sx * 0.42, -0.24, 1.2), 0.1, face=(0, 1, 0))
        fr = Frame((sx * 0.28, 0.1, 0.6), sx, lift=25, sweep=18, pitch=40)
        p.feathers('WingL' if sx < 0 else 'WingR', fr, ['Fin', 'FinBlue'], 4, 0.12, lens=(0.36, 0.26), widths=(0.14, 0.14), angles=(15, 65), step=0.01, start=0.02)
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'Blue', (sx * 0.19, -0.08, 0.38), (sx * 0.19, -0.1, 0.1), 0.09, 0.075)
        p.sphere('LegF' + s, 'Cyan', (sx * 0.19, -0.14, 0.05), 0.085, (1, 1.3, 0.6))
        p.cone('LegB' + s, 'Blue', (sx * 0.21, 0.32, 0.4), (sx * 0.21, 0.34, 0.1), 0.12, 0.08)
        p.sphere('LegB' + s, 'Cyan', (sx * 0.21, 0.28, 0.05), 0.09, (1, 1.3, 0.6))
    p.torus('Body', 'Gold', (0, -0.28, 0.54), 0.16, 0.022, rot=(65, 0, 0), seg=14)
    p.sphere('Body', 'Gem', (0, -0.4, 0.5), 0.045, seg=6, rings=4)
    path = [(0, 0.42, 0.34), (0, 0.66, 0.26), (0, 0.9, 0.3), (0, 1.08, 0.44)]
    p.tube('Tail', 'Blue', path, [0.15, 0.11, 0.08, 0.05])
    tail_fan(p, 'Tail', (0, 1.06, 0.44), 0.4, n=5, spread=110)


def adult(p, form):
    big = form == 3
    p.pivot('Head', (0, -0.3, 0.8))
    p.pivot('EarL', (-0.27, -0.55, 1.2), parent='Head')
    p.pivot('EarR', (0.27, -0.55, 1.2), parent='Head')
    p.pivot('WingL', (-0.22, 0.15, 0.95))
    p.pivot('WingR', (0.22, 0.15, 0.95))
    p.pivot('Tail', (0, 0.75, 0.55))
    p.pivot('Tail2', (0, 1.3, 0.38), parent='Tail')
    for sx, s in ((-1, 'L'), (1, 'R')):
        p.pivot('LegF' + s, (sx * 0.22, -0.1, 0.6))
        p.pivot('LegB' + s, (sx * 0.24, 0.5, 0.6))
    p.sphere('Body', 'Blue', (0, 0.22, 0.68), 0.36, (0.82, 1.55, 0.82))
    p.sphere('Body', 'PinkLt', (0, 0.02, 0.56), 0.3, (0.65, 1.3, 0.62))
    for i in range(5):
        y = -0.05 + i * 0.22
        top = 0.68 + 0.3 * math.sqrt(max(0.0, 1 - ((y - 0.22) / 0.56) ** 2))
        p.blade('Body', ['FinBlue', 'Fin'][i % 2], (0, y, top - 0.02), (0, y + 0.1, top + (0.34 if big else 0.26)), 0.15, face=(1, 0, 0))
    p.tube('Head', 'Blue', [(0, -0.26, 0.74), (0, -0.4, 0.94), (0, -0.48, 1.08)], [0.19, 0.16, 0.15])
    hc = (0, -0.56, 1.2)
    p.sphere('Head', 'Blue', hc, 0.28, (1.05, 1.0, 0.95))
    p.sphere('Head', 'Blue', (0, -0.78, 1.12), 0.13, (1, 1.15, 0.85))
    p.sphere('Head', 'Pink', (0, -0.89, 1.14), 0.03, seg=6, rings=4)
    for sx in (-1, 1):
        p.eye('Head', hc, 0.28, sx, yaw=38, pitch=6, size=0.1, iris='Iris')
        p.sphere('Head', 'Pink', (sx * 0.22, -0.7, 1.1), 0.055, (1, 0.3, 0.7), seg=6, rings=4)
        p.tube('Head', 'Gold', [(sx * 0.14, -0.5, 1.4), (sx * 0.22, -0.44, 1.62), (sx * 0.34, -0.3, 1.78 if big else 1.72)], [0.06, 0.045, 0.012], seg=6)
        if big:
            p.tube('Head', 'Gold', [(sx * 0.06, -0.52, 1.44), (sx * 0.08, -0.46, 1.66), (sx * 0.06, -0.38, 1.82)], [0.045, 0.032, 0.01], seg=5)
        e = 'EarL' if sx < 0 else 'EarR'
        for j, (dx, dz) in enumerate(((0.28, 0.1), (0.2, 0.3), (0.1, 0.46))):
            p.blade(e, ['Fin', 'FinBlue', 'Fin'][j], (sx * 0.27, -0.55, 1.2), (sx * (0.27 + dx), -0.4, 1.2 + dz + (0.1 if big else 0)), 0.14, face=(0, 1, 0))
        s = 'L' if sx < 0 else 'R'
        p.cone('LegF' + s, 'Blue', (sx * 0.22, -0.1, 0.64), (sx * 0.22, -0.14, 0.14), 0.095, 0.065)
        p.sphere('LegF' + s, 'Cyan', (sx * 0.22, -0.19, 0.06), 0.09, (1, 1.4, 0.6))
        p.cone('LegB' + s, 'Blue', (sx * 0.24, 0.5, 0.64), (sx * 0.24, 0.52, 0.14), 0.13, 0.07)
        p.sphere('LegB' + s, 'Cyan', (sx * 0.24, 0.46, 0.06), 0.095, (1, 1.4, 0.6))
        fr = Frame((sx * 0.22, 0.15, 0.95), sx, lift=34, sweep=16, pitch=58)
        n = 7 if big else 5
        arm = 0.5
        lens = (1.0, 0.55) if big else (0.85, 0.5)
        ang = (14, 74)
        w = 'WingL' if sx < 0 else 'WingR'
        p.fan(w, 'FinBlue', fr.p(0.05, 0, -0.01), [fr.p(arm, 0, -0.01)] + p.feather_points(fr, n, arm, lens, ang, 0.08, 0.7, w0=-0.01) + [fr.p(0.1, 0.1, -0.01)])
        p.feathers(w, fr, ['Fin', 'FinBlue'], n, arm, lens, widths=(0.22, 0.2), angles=ang, step=0.012, start=0.08, peak=0.6)
        p.tube(w, 'Gold', [fr.p(0, 0, 0), fr.p(arm, 0, 0)], [0.04, 0.025], seg=5)
        if big:
            p.sphere(w, 'Gem', fr.p(arm * 0.5, 0, 0.0), 0.04, seg=6, rings=4)
    p.torus('Body', 'Gold', (0, -0.3, 0.98), 0.17, 0.024, rot=(62, 0, 0), seg=14)
    p.sphere('Body', 'Gem', (0, -0.44, 0.92), 0.055 if not big else 0.08, seg=7, rings=5)
    p.tube('Tail', 'Blue', [(0, 0.75, 0.55), (0, 1.02, 0.42), (0, 1.3, 0.38)], [0.19, 0.14, 0.1])
    p.tube('Tail2', 'Blue', [(0, 1.3, 0.38), (0, 1.55, 0.44), (0, 1.74, 0.56)], [0.1, 0.07, 0.045])
    tail_fan(p, 'Tail2', (0, 1.72, 0.55), 0.55 if big else 0.45, n=7 if big else 5, spread=120)
    if big:
        for sx in (-1, 1):  # water flames licking round the front feet
            for dx, dy in ((0.0, -0.2), (0.1, -0.06), (-0.1, -0.06)):
                p.blade('LegF' + ('L' if sx < 0 else 'R'), 'Water', (sx * 0.22 + dx * 0.5, -0.2 + dy, 0.04), (sx * 0.22 + dx * 2.2, -0.2 + dy * 1.5, 0.38), 0.1,
                        face=(0, 1, 0))


CAST = {
    # 1. Whirlpool: crouch, then spin on the spot with the tail swinging
    1: [
        (0, {}),
        (8, {'Rig': R(loc=(0, 0, -0.04)), 'Head': R(10), 'Tail': R(0, 0, 25)}),
        (18, {'Rig': R(0, 0, 100, loc=(0, 0, 0.14)), 'Head': R(-14), 'Tail': R(0, 0, -30), **wings(35)}),
        (32, {'Rig': R(0, 0, 230, loc=(0, 0, 0.16)), 'Head': R(-14), 'Tail': R(0, 0, 30), **wings(20)}),
        (46, {'Rig': R(0, 0, 340, loc=(0, 0, 0.1)), 'Head': R(-8), 'Tail': R(0, 0, -20), **wings(30)}),
        (60, {'Rig': R(0, 0, 360, loc=(0, 0, 0)), 'Head': R(0)}),
        (72, {'Rig': R(0, 0, 360)}),
    ],
    # 2. Holy Stream: head back with wings open, then a flowing stream forward
    2: [
        (0, {}),
        (12, {'Head': R(-28), 'Rig': R(-8, loc=(0, 0, 0.03)), **wings(30), 'Tail': R(-25), 'Tail2': R(-20)}),
        (22, {'Head': R(14), 'Rig': R(4), **wings(55), 'Tail': R(10), 'Tail2': R(15)}),
        (40, {'Head': R(10, 0, 8), 'Rig': R(3), **wings(48), 'Tail': R(12, 0, 15), 'Tail2': R(10)}),
        (56, {'Head': R(2), **wings(15)}),
        (72, {}),
    ],
    # 3. Sea Gem: rise up, chest out, wings spread, gem glowing
    3: [
        (0, {}),
        (12, {'Rig': R(loc=(0, 0, -0.06)), **wings(-15), 'Head': R(8)}),
        (26, {'Rig': R(-10, loc=(0, 0, 0.5)), **wings(62), 'Head': R(-20), 'Tail': R(-20), 'Tail2': R(-25)}),
        (40, {'Rig': R(-8, loc=(0, 0, 0.55)), **wings(48), 'Head': R(-16), 'Tail': R(-15), 'Tail2': R(-20)}),
        (54, {'Rig': R(-8, loc=(0, 0, 0.5)), **wings(60), 'Head': R(-20)}),
        (64, {'Rig': R(0, loc=(0, 0, 0.1)), **wings(15), 'Head': R(-4)}),
        (72, {}),
    ],
}
