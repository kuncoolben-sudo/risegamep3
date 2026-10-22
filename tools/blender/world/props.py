"""The small things the game scatters over the island by the hundred (one InstancedMesh per part). Each kind is one kit
model whose root is named after the kind in public/models/w_props.glb; all stand on z = 0 at the origin."""
import math

from places.common import B, palm, pine, round_tree

KINDS = ['tree', 'bigtree', 'autumn', 'bloom', 'palm', 'pine', 'bush', 'grass', 'flowers', 'rock', 'boulder']

PALETTE = {
    'Trunk': '#7a5232', 'TrunkLight': '#9a6a3c', 'Leaf': '#4caf50', 'Leaf2': '#3d9a46', 'Autumn': '#f08a2a', 'Autumn2': '#f6b33c',
    'Pink': '#f6a8c8', 'Pink2': '#e884b0', 'Palm': '#3fa84f', 'Pine': '#2f8a4e', 'Bush': '#4aa648', 'Bush2': '#3a9240',
    'Grass': '#6cc04a', 'Grass2': '#58ad3e', 'Stem': '#4f9a3c', 'PetalPink': '#ff7aa8', 'PetalYellow': '#ffd23f',
    'PetalWhite': '#ffffff', 'Rock': '#a39b8b', 'RockDark': '#857d70', 'Moss': '#5aa64a',
}


def bigtree(p):
    """A rain tree: a thick trunk forking under a wide, flat crown."""
    p.cone(B, 'Trunk', (0, 0, 0), (0, 0, 1.3), 0.24, 0.17, seg=7)
    crown = [(0.0, 0.0, 2.45, 1.0), (1.05, 0.35, 2.25, 0.85), (-1.0, 0.45, 2.3, 0.85), (0.35, -0.95, 2.2, 0.8), (-0.45, -0.85, 2.35, 0.78)]
    for i, (x, y, z, r) in enumerate(crown):
        if i:
            p.tube(B, 'Trunk', [(0, 0, 1.2), (x * 0.5, y * 0.5, 1.75), (x * 0.8, y * 0.8, z - 0.25)], [0.12, 0.08, 0.05], seg=5)
        p.blob(B, 'Leaf' if i % 2 == 0 else 'Leaf2', (x, y, z), r, (1.25, 1.25, 0.62), 0.12, 3 + i, 8, 5)


def bush(p):
    for i, (x, y, z, r) in enumerate(((0, 0, 0.36, 0.5), (0.45, 0.2, 0.3, 0.38), (-0.42, 0.15, 0.28, 0.36), (0.05, -0.38, 0.27, 0.33))):
        p.blob(B, 'Bush' if i % 2 == 0 else 'Bush2', (x, y, z), r, (1.15, 1.0, 0.85), 0.14, 7 + i, 7, 5)


def grass(p):
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.3
        tip = (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.42 + 0.12 * (i % 3))
        p.blade(B, 'Grass' if i % 2 else 'Grass2', (math.cos(a) * 0.05, math.sin(a) * 0.05, 0), tip, 0.11, 0.01,
                face=(-math.sin(a), math.cos(a), 0), peak=0.3)


def flowers(p):
    for i, (x, y, h, m) in enumerate(((0.0, 0.0, 0.42, 'PetalPink'), (0.2, 0.12, 0.34, 'PetalYellow'), (-0.18, 0.1, 0.36, 'PetalWhite'),
                                      (0.08, -0.2, 0.3, 'PetalYellow'), (-0.12, -0.14, 0.38, 'PetalPink'))):
        p.cone(B, 'Stem', (x, y, 0), (x, y, h), 0.018, 0.014, seg=4)
        p.sphere(B, m, (x, y, h + 0.04), 0.075, (1, 1, 0.7), seg=6, rings=4)
        p.sphere(B, 'PetalYellow' if m != 'PetalYellow' else 'PetalWhite', (x, y, h + 0.075), 0.03, seg=5, rings=3)
    for a in (0.6, 2.8, 4.6):
        p.blade(B, 'Grass', (0, 0, 0), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.16), 0.1, 0.01, face=(0, 0, 1))


def boulder(p):
    p.blob(B, 'Rock', (0, 0, 0.45), 1.0, (1.3, 1.1, 0.85), 0.12, 21, 9, 6, flat_bottom=True)
    p.blob(B, 'RockDark', (0.75, -0.35, 0.3), 0.55, (1.1, 1, 0.8), 0.14, 22, 7, 5, flat_bottom=True)
    p.blob(B, 'Moss', (-0.1, 0.1, 1.15), 0.62, (1.3, 1.1, 0.45), 0.12, 23, 8, 5)


def build(kind, p):
    if kind == 'tree':
        round_tree(p, 'Trunk', 'Leaf', (0, 0, 0), 2.4, 0.95, 3, 'Leaf2')
    elif kind == 'bigtree':
        bigtree(p)
    elif kind == 'autumn':
        round_tree(p, 'Trunk', 'Autumn', (0, 0, 0), 2.3, 0.9, 6, 'Autumn2')
    elif kind == 'bloom':
        round_tree(p, 'Trunk', 'Pink', (0, 0, 0), 2.1, 0.85, 9, 'Pink2')
    elif kind == 'palm':
        palm(p, 'TrunkLight', 'Palm', (0, 0, 0), 3.0, (0.5, 0.0), 7, 1.2, 0.3)
    elif kind == 'pine':
        pine(p, 'Trunk', 'Pine', (0, 0, 0), 2.9, 0.82, 3)
    elif kind == 'bush':
        bush(p)
    elif kind == 'grass':
        grass(p)
    elif kind == 'flowers':
        flowers(p)
    elif kind == 'rock':
        p.blob(B, 'Rock', (0, 0, 0.22), 0.45, (1.25, 1.0, 0.75), 0.14, 17, 7, 5, flat_bottom=True)
    elif kind == 'boulder':
        boulder(p)
