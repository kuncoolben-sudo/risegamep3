"""Six chibi character prototypes (Kai, Pond, Beam, Lily, Minnie, Maya) from the RISE concept sheet.

Run inside Blender (Scripting tab / MCP) to build them in a 'Characters' collection and export
public/models/char_<name>.glb, or headless:

    python tools/blender/build_characters.py [output_dir]

Reuses the primitive helpers of build_models.py and follows the same conventions: Z-up, facing -Y,
root > Head/Body/ArmL/ArmR/LegL/LegR nodes so src/world3d can animate them. Materials are named per
character (Skin_Kai, Hair_Kai, ...) so the Skin/Hair/Outfit appearance tint does not repaint the presets.
"""
import importlib.util
import math
import os
import sys

import bpy
import bmesh

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'F:\risewebgame\p3\tools\blender'
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else os.path.join(HERE, '../../public/models'))

_argv = sys.argv
sys.argv = [_argv[0], OUT]  # build_models reads argv[1] as its output dir at import time
_spec = importlib.util.spec_from_file_location('build_models', os.path.join(HERE, 'build_models.py'))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
sys.argv = _argv

M.PALETTE.update({'Iris': '#4a2c17', 'Sclera': '#ffffff', 'Mouth': '#b3503f', 'Brow': '#3a2415'})

CHARACTERS = [
    dict(name='Kai', skin='#f1c9a0', hair='#7a4423', style='messy', jacket='#2f6fd6', shirt='#f4efe4', bottom_kind='shorts',
         bottom='#8a7650', shoes='#6b4426', boots=True, socks='#e8e2d0', hood=True, pack='#8a5a2b', accent='#8a5a2b'),
    dict(name='Pond', skin='#f4d2b0', hair='#25211f', style='neat', jacket='#4f9a5a', shirt='#f0e8d8', bottom_kind='shorts',
         bottom='#4a6a9a', shoes='#6aa87a', boots=False, socks='#f4f4f4', hood=True, pack='#6b5a3a', glasses=True, accent='#6aa87a'),
    dict(name='Beam', skin='#f1c9a0', hair='#c96b2c', style='messy', jacket='#d63a2f', shirt='#ffffff', bottom_kind='shorts',
         bottom='#4b4b52', shoes='#d63a2f', boots=False, socks='#f4f4f4', hood=False, pack='#4b4b52', accent='#ffb13b'),
    dict(name='Lily', skin='#f6d6bd', hair='#7a4a2e', style='long', jacket='#f4a8c4', shirt='#ffffff', bottom_kind='skirt',
         bottom='#4f8fe0', shoes='#f27aa8', boots=False, socks='#ffffff', hood=True, pack=None, bow='#f27aa8', accent='#f27aa8'),
    dict(name='Minnie', skin='#f6d6bd', hair='#2e2230', style='bob', jacket='#a58be0', shirt='#f8f4ff', bottom_kind='overalls',
         bottom='#4a5f8f', shoes='#b9a6ee', boots=False, socks='#ffffff', hood=True, pack=None, headband='#8a63d2', accent='#e46aa0'),
    dict(name='Maya', skin='#f1c9a0', hair='#c8481f', style='ponytail', jacket='#5fa05a', shirt='#f2c84b', bottom_kind='shorts',
         bottom='#9a8a5a', shoes='#7a5230', boots=True, socks='#7a9a5a', hood=False, pack='#7a5230', leaf='#4caf50', accent='#4caf50'),
]


def _hair_cap(parent, hz, mat_name, name='Hair_cap'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.56, location=(0, 0.02, hz + 0.02))
    cap = bpy.context.active_object
    cap.scale = (1.0, 0.98, 0.98)
    bpy.ops.object.transform_apply(scale=True)
    b = bmesh.new()
    b.from_mesh(cap.data)
    # transform_apply bakes the location into the vertices, so measure relative to the sphere centre in world space
    def rel(v):
        w = cap.matrix_world @ v.co
        return w.y - 0.02, w.z - (hz + 0.02)
    kill = [v for v in b.verts if (rel(v)[1] < 0.14 and rel(v)[0] < 0.12) or rel(v)[1] < -0.1]
    bmesh.ops.delete(b, geom=kill, context='VERTS')
    b.to_mesh(cap.data)
    b.free()
    return M._finish(cap, name, mat_name, True, parent)


def _cut_below(obj, z_world):
    b = bmesh.new()
    b.from_mesh(obj.data)
    bmesh.ops.delete(b, geom=[v for v in b.verts if (obj.matrix_world @ v.co).z < z_world], context='VERTS')
    b.to_mesh(obj.data)
    b.free()


def build(spec):
    n = spec['name']
    k = lambda s: f'{s}_{n}'  # noqa: E731
    for slot, key in (('Skin', 'skin'), ('Hair', 'hair'), ('Jacket', 'jacket'), ('Shirt', 'shirt'), ('Bottom', 'bottom'),
                      ('Shoes', 'shoes'), ('Socks', 'socks'), ('Accent', 'accent')):
        M.PALETTE[k(slot)] = spec[key]
    for slot, key in (('Pack', 'pack'), ('Bow', 'bow'), ('Band', 'headband'), ('Leaf', 'leaf')):
        if spec.get(key):
            M.PALETTE[k(slot)] = spec[key]

    root = M.empty(f'Char_{n}')
    hz = 1.35
    head = M.empty('Head', (0, 0, hz), root)
    M.sphere('HeadMesh', k('Skin'), (0, 0, hz), 0.5, (1.0, 0.95, 0.92), parent=head)
    for sx in (-1, 1):
        M.sphere(f'EyeWhite{sx}', 'Sclera', (sx * 0.18, -0.41, hz - 0.02), 0.11, (1, 0.45, 1.25), seg=10, rings=8, parent=head)
        M.sphere(f'Eye{sx}', 'Iris', (sx * 0.18, -0.46, hz - 0.03), 0.075, (1, 0.4, 1.3), seg=10, rings=8, parent=head)
        M.sphere(f'EyeShine{sx}', 'Sclera', (sx * 0.18 + 0.025, -0.49, hz + 0.02), 0.022, seg=6, rings=4, parent=head)
        M.box(f'Brow{sx}', 'Brow', (sx * 0.18, -0.45, hz + 0.16), (0.14, 0.03, 0.03), head, rot=(0, math.radians(-sx * 8), 0))
        M.sphere(f'Cheek{sx}', 'Cheek', (sx * 0.3, -0.39, hz - 0.15), 0.07, (1, 0.35, 0.7), seg=8, rings=6, parent=head)
        M.sphere(f'Ear{sx}', k('Skin'), (sx * 0.49, 0.0, hz - 0.05), 0.08, (0.5, 1, 1), seg=8, rings=6, parent=head)
    M.sphere('Nose', k('Skin'), (0, -0.48, hz - 0.1), 0.035, seg=6, rings=4, parent=head)
    M.sphere('Mouth', 'Mouth', (0, -0.46, hz - 0.22), 0.05, (1.5, 0.3, 0.5), seg=8, rings=6, parent=head)

    style = spec['style']
    _hair_cap(head, hz, k('Hair'))
    if style in ('messy', 'neat'):
        n_tufts = 5 if style == 'messy' else 3
        for i in range(n_tufts):
            a = math.radians(-60 + i * (120 / (n_tufts - 1)))
            M.sphere(f'Tuft{i}', k('Hair'), (math.sin(a) * 0.3, -0.4, hz + 0.3 - abs(math.sin(a)) * 0.08), 0.14,
                     (1.2, 0.8, 1.0), seg=8, rings=6, parent=head)
        if style == 'messy':
            for i, a in enumerate((-50, -15, 20, 55)):
                r = math.radians(a)
                M.cyl(f'Spike{i}', k('Hair'), (math.sin(r) * 0.3, -0.05, hz + 0.58), 0.12, 0.3, seg=6, r2=0.0, parent=head,
                      rot=(math.radians(-10), math.radians(a * 0.6), 0))
    else:
        M.box('Hair_fringe', k('Hair'), (0, -0.41, hz + 0.26), (0.8, 0.16, 0.2), head, rot=(math.radians(-18), 0, 0))
    if style == 'bob':
        for sx in (-1, 1):
            M.sphere(f'BobSide{sx}', k('Hair'), (sx * 0.43, -0.02, hz - 0.2), 0.2, (0.8, 1.1, 1.4), seg=10, rings=8, parent=head)
        M.sphere('BobBack', k('Hair'), (0, 0.28, hz - 0.2), 0.46, (1.0, 0.75, 0.9), seg=12, rings=8, parent=head)
    if style == 'long':
        M.sphere('LongBack', k('Hair'), (0, 0.3, hz - 0.5), 0.5, (0.95, 0.5, 1.15), parent=head)
        for sx in (-1, 1):
            for j, dz in enumerate((0.25, 0.5, 0.72)):
                M.sphere(f'Lock{sx}_{j}', k('Hair'), (sx * (0.46 - j * 0.02), 0.02, hz - dz), 0.15 - j * 0.015, (0.8, 1, 1.2), seg=8, rings=6, parent=head)
    if style == 'ponytail':
        for j, (y, dz, r) in enumerate(((0.52, 0.05, 0.17), (0.6, -0.1, 0.15), (0.64, -0.28, 0.13), (0.62, -0.45, 0.1))):
            M.sphere(f'Pony{j}', k('Hair'), (0.0, y, hz + 0.28 + dz), r, (1, 1, 1.25), seg=8, rings=6, parent=head)
        M.sphere('PonyTie', k('Accent'), (0, 0.5, hz + 0.3), 0.07, seg=6, rings=4, parent=head)
    if spec.get('glasses'):
        for sx in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.14, minor_radius=0.018, major_segments=20, minor_segments=6,
                                             location=(sx * 0.18, -0.5, hz - 0.02), rotation=(math.pi / 2, 0, 0))
            M._finish(bpy.context.active_object, f'Glasses{sx}', 'Black', True, head)
        M.box('GlassesBridge', 'Black', (0, -0.5, hz - 0.01), (0.1, 0.02, 0.02), head)
    if spec.get('bow'):
        for sx in (-1, 1):
            M.sphere(f'BowWing{sx}', k('Bow'), (0.3 + sx * 0.12, -0.25, hz + 0.45), 0.11, (1.1, 0.5, 0.8), seg=8, rings=6, parent=head)
        M.sphere('BowKnot', k('Bow'), (0.3, -0.27, hz + 0.45), 0.06, seg=6, rings=4, parent=head)
    if spec.get('headband'):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.57, minor_radius=0.035, major_segments=24, minor_segments=6,
                                         location=(0, 0.0, hz + 0.02), rotation=(math.pi / 2 + 0.3, 0, 0))
        band = bpy.context.active_object
        bpy.ops.object.transform_apply(rotation=True)
        _cut_below(band, hz + 0.05)
        M._finish(band, 'Headband', k('Band'), True, head)
    if spec.get('leaf'):
        for sx in (-1, 1):
            M.sphere(f'Leaf{sx}', k('Leaf'), (0.1 + sx * 0.1, 0.4, hz + 0.58), 0.1, (0.6, 1.2, 0.4), seg=6, rings=4, parent=head)

    body = M.empty('Body', (0, 0, 0.55), root)
    M.cyl('Torso', k('Jacket'), (0, 0, 0.55), 0.3, 0.55, seg=12, r2=0.34, parent=body, smooth=True)
    M.box('ShirtFront', k('Shirt'), (0, -0.3, 0.55), (0.16, 0.05, 0.46), body)
    if spec['bottom_kind'] == 'overalls':
        M.box('Bib', k('Bottom'), (0, -0.31, 0.45), (0.3, 0.05, 0.3), body)
        for sx in (-1, 1):
            M.box(f'Strap{sx}', k('Bottom'), (sx * 0.12, -0.3, 0.7), (0.05, 0.05, 0.22), body)
    if spec['bottom_kind'] == 'skirt':
        M.cyl('Skirt', k('Bottom'), (0, 0, 0.33), 0.44, 0.24, seg=14, r2=0.3, parent=body, smooth=True)
    else:
        M.box('Belt', k('Bottom'), (0, 0, 0.3), (0.62, 0.5, 0.1), body)
    if spec.get('hood'):
        M.sphere('Hood', k('Jacket'), (0, 0.2, 0.9), 0.22, (1.35, 0.6, 0.8), seg=10, rings=8, parent=body)
    if spec.get('pack'):
        M.box('Backpack', k('Pack'), (0, 0.33, 0.58), (0.5, 0.22, 0.5), body)
        for sx in (-1, 1):
            M.box(f'PackStrap{sx}', k('Pack'), (sx * 0.17, -0.0, 0.68), (0.07, 0.62, 0.05), body)

    for sx, nm in ((-1, 'ArmL'), (1, 'ArmR')):
        arm = M.empty(nm, (sx * 0.38, 0, 0.78), root)
        M.cyl(nm + 'Sleeve', k('Jacket'), (sx * 0.38, 0, 0.7), 0.1, 0.25, seg=8, parent=arm, smooth=True)
        M.sphere(nm + 'Hand', k('Skin'), (sx * 0.38, 0, 0.52), 0.1, seg=8, rings=6, parent=arm)
    for sx, nm in ((-1, 'LegL'), (1, 'LegR')):
        leg = M.empty(nm, (sx * 0.15, 0, 0.3), root)
        if spec['bottom_kind'] != 'skirt':
            M.cyl(nm + 'Mesh', k('Bottom'), (sx * 0.15, 0, 0.26), 0.125, 0.2, seg=8, parent=leg, smooth=True)
        M.cyl(nm + 'Sock', k('Socks'), (sx * 0.15, 0, 0.14), 0.085, 0.2, seg=8, parent=leg, smooth=True)
        if spec.get('boots'):
            M.cyl(nm + 'Boot', k('Shoes'), (sx * 0.15, 0, 0.1), 0.11, 0.18, seg=8, parent=leg, smooth=True)
        M.sphere(nm + 'Shoe', k('Shoes'), (sx * 0.15, -0.05, 0.07), 0.14, (1, 1.3, 0.7), seg=8, rings=6, parent=leg)
    # Parts were placed at world coordinates, then parented to pivot empties that sit at those same
    # coordinates: cancel the parent offset so the pivots can still be rotated (arms, legs) in game.
    bpy.context.view_layer.update()
    for o in descendants(root):
        if o.parent is not None and o.parent is not root:
            o.matrix_parent_inverse = o.parent.matrix_world.inverted()
    return root


def descendants(o):
    yield o
    for c in o.children:
        yield from descendants(c)


def tag_nodes(root, owner):
    """Blender keeps object names unique per file, so the second character's 'Head' would become 'Head.001',
    but the game looks nodes up by their plain name ('ArmL', 'Head'...). Keep the plain name in a property and
    give each object a per-character name; export_root swaps the plain names back for the export."""
    for o in descendants(root):
        o['node'] = o.name
        o.name = f'{owner}|{o.name}'


def export_root(root, owner, path):
    loc = root.location.copy()
    root.location = (0, 0, 0)
    nodes = list(descendants(root))
    for o in nodes:
        o.name = o['node']
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in nodes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    try:
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                                  export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False)
    finally:
        for o in nodes:
            o.name = f"{owner}|{o['node']}"
        root.location = loc


def main():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    coll = bpy.data.collections.get('Characters') or bpy.data.collections.new('Characters')
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for o in list(coll.objects):  # rebuild cleanly on re-run
        bpy.data.objects.remove(o, do_unlink=True)
    for m in [m for m in bpy.data.materials if m.users == 0]:  # no 'Skin_Kai.001' copies on re-run
        bpy.data.materials.remove(m)
    for i, spec in enumerate(CHARACTERS):
        before = set(bpy.data.objects)
        root = build(spec)
        for o in set(bpy.data.objects) - before:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll.objects.link(o)
        tag_nodes(root, spec['name'])
        root.location = ((i - (len(CHARACTERS) - 1) / 2) * 1.6, 0, 0)
        path = os.path.join(OUT, f"char_{spec['name'].lower()}.glb")
        export_root(root, spec['name'], path)
        print(f"{path}: {os.path.getsize(path) / 1024:.0f} KB")


main()
