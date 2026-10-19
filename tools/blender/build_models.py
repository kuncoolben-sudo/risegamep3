"""Builds every low-poly .glb used by the 3D world. Run headless:

    pip install bpy            # Blender as a Python module (Python 3.11-3.13)
    python tools/blender/build_models.py [output_dir]

Conventions: Blender is Z-up and characters face -Y, which glTF export turns into
Y-up facing +Z (what Three.js expects). Named nodes/materials are part of the contract
with src/world3d (e.g. 'ArmL', 'Hair_wavy', materials 'Skin', 'Hair', 'Outfit').
"""
import math
import os
import sys

import bpy  # must come before bmesh (the pip build registers bmesh on import)
import bmesh  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '../../public/models')
os.makedirs(OUT, exist_ok=True)

PALETTE = {
    'Skin': '#f1c27d', 'Hair': '#6b3e1c', 'Outfit': '#3b82f6', 'Pants': '#3a4a7a', 'Shoes': '#6b4426', 'Eye': '#1d1d1d', 'Cheek': '#ff9aa2',
    'Wall': '#fff1d6', 'WallBlue': '#9ad0ff', 'WallPink': '#ffb5c8', 'WallGreen': '#b9e6a1', 'WallYellow': '#ffe08a', 'WallPurple': '#c9b3ff',
    'RoofRed': '#e0524b', 'RoofBlue': '#3b7fd6', 'RoofOrange': '#f08a3c', 'RoofGreen': '#3fa66b', 'RoofPurple': '#8a63d2',
    'Wood': '#a9743f', 'DarkWood': '#7a4a24', 'Stone': '#b9bec7', 'Glass': '#bfe6ff', 'Gold': '#ffcf40', 'White': '#ffffff', 'Black': '#222222',
    'Leaf': '#4caf50', 'LeafDark': '#2f8f46', 'Trunk': '#8a5a2b', 'Sand': '#f3dfa2', 'Water': '#58b7ff', 'Red': '#e8453c', 'Cream': '#fff7e0',
    'Lion': '#f2a53a', 'Mane': '#a8541c', 'Penguin': '#2b3445', 'Belly': '#f6f6f6', 'Beak': '#ffb13b', 'Monkey': '#8c5a33', 'MonkeyFace': '#f0cfa0',
    'Parrot': '#e8453c', 'Wing': '#2f7de1', 'Cloud': '#ffffff', 'Sun': '#ffd23f', 'Book1': '#e8453c', 'Book2': '#3b82f6', 'Book3': '#3fa66b', 'Book4': '#f5b301',
}
_mats = {}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mat(name):
    if name in _mats:
        return _mats[name]
    h = PALETTE[name].lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1)
    bsdf.inputs['Roughness'].default_value = 0.85
    bsdf.inputs['Metallic'].default_value = 0.0
    _mats[name] = m
    return m


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()


def _finish(o, name, material, smooth, parent):
    o.name = name
    o.data.materials.append(mat(material))
    if smooth:
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()
    if parent is not None:
        o.parent = parent
    return o


def box(name, material, loc, size, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, material, False, parent)


def cyl(name, material, loc, r, h, seg=12, parent=None, smooth=False, r2=None, rot=(0, 0, 0)):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r, radius2=r2, depth=h, location=loc, rotation=rot)
    return _finish(bpy.context.active_object, name, material, smooth, parent)


def sphere(name, material, loc, r, scale=(1, 1, 1), seg=14, rings=9, parent=None, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, material, smooth, parent)


def roof(name, material, loc, w, d, h, parent=None, overhang=0.25):
    """Triangular prism roof; ridge runs along Y."""
    me = bpy.data.meshes.new(name)
    hw, hd = w / 2 + overhang, d / 2 + overhang
    verts = [(-hw, -hd, 0), (hw, -hd, 0), (0, -hd, h), (-hw, hd, 0), (hw, hd, 0), (0, hd, h)]
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    return _finish(o, name, material, False, parent)


def pyramid(name, material, loc, r, h, seg=4, parent=None, rot_z=math.pi / 4):
    return cyl(name, material, loc, r, h, seg=seg, r2=0.0, parent=parent, rot=(0, 0, rot_z))


def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    if parent is not None:
        o.parent = parent
    return o


def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    return o


def export(filename):
    path = os.path.join(OUT, filename)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False)
    tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    print(f'{filename}: {os.path.getsize(path) / 1024:.0f} KB, ~{tris} faces')


def house_body(root, wall='Wall', roof_m='RoofRed', w=3.0, d=2.6, h=1.8, door=True, chimney=False):
    box('Walls', wall, (0, 0, h / 2), (w, d, h), root)
    roof('Roof', roof_m, (0, 0, h), w, d, 1.2, root)
    if door:
        box('Door', 'DarkWood', (0, -d / 2 - 0.02, 0.6), (0.7, 0.08, 1.2), root)
    for sx in (-1, 1):
        box(f'Window{sx}', 'Glass', (sx * 0.95, -d / 2 - 0.02, 1.0), (0.5, 0.08, 0.5), root)
    if chimney:
        box('Chimney', 'Stone', (0.9, 0.5, h + 1.0), (0.4, 0.4, 0.9), root)


# ------------------------------------------------------------------ character
def build_character():
    reset()
    root = empty('Character')
    hz = 1.35  # head centre
    head = empty('Head', (0, 0, hz), root)
    sphere('HeadMesh', 'Skin', (0, 0, hz), 0.5, (1.0, 0.95, 0.92), parent=head)
    for sx in (-1, 1):
        sphere(f'Eye{sx}', 'Eye', (sx * 0.18, -0.43, hz - 0.03), 0.07, (1, 0.5, 1.3), seg=8, rings=6, parent=head)
        sphere(f'Cheek{sx}', 'Cheek', (sx * 0.3, -0.4, hz - 0.14), 0.07, (1, 0.35, 0.7), seg=8, rings=6, parent=head)
    sphere('Nose', 'Skin', (0, -0.48, hz - 0.1), 0.04, seg=6, rings=4, parent=head)

    # hair cap: dome on top + the whole back of the head, front/face left open
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.56, location=(0, 0.02, hz + 0.02))
    cap = bpy.context.active_object
    cap.scale = (1.0, 0.98, 0.98)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(cap.data)
    kill = [v for v in bm.verts if (v.co.z < 0.14 and v.co.y < 0.12) or v.co.z < -0.1]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(cap.data)
    bm.free()
    _finish(cap, 'Hair_cap', 'Hair', True, head)
    # fringe
    box('Hair_fringe', 'Hair', (0, -0.4, hz + 0.28), (0.78, 0.2, 0.16), head, rot=(math.radians(-18), 0, 0)).name = 'Hair_fringe'

    sphere('Hair_long', 'Hair', (0, 0.3, hz - 0.5), 0.5, (0.95, 0.5, 1.15), parent=head)
    wavy = [sphere(f'w{i}', 'Hair', (math.cos(a) * 0.58, 0.12 + math.sin(a) * 0.2, hz - 0.05 - abs(math.cos(a)) * 0.0 - (0.0 if i % 2 else 0.18)), 0.12, seg=8, rings=6, parent=head)
            for i, a in enumerate([x * math.pi / 6 for x in range(0, 12)])]
    join(wavy, 'Hair_wavy').parent = head
    curly = [sphere(f'c{i}', 'Hair', (math.cos(a) * 0.55, 0.1 + math.sin(a) * 0.3, hz + 0.1 + (0.18 if i % 2 else 0.0)), 0.18, seg=8, rings=6, parent=head)
             for i, a in enumerate([x * math.pi / 5 for x in range(0, 10)])]
    join(curly, 'Hair_curly').parent = head
    sphere('Facial_moustache', 'Hair', (0, -0.47, hz - 0.2), 0.17, (1.0, 0.25, 0.28), seg=8, rings=6, parent=head)
    sphere('Facial_beard', 'Hair', (0, -0.36, hz - 0.4), 0.3, (1.0, 0.7, 0.62), seg=10, rings=7, parent=head)

    body = empty('Body', (0, 0, 0.55), root)
    cyl('Torso', 'Outfit', (0, 0, 0.55), 0.3, 0.55, seg=12, r2=0.34, parent=body, smooth=True)
    box('Belt', 'Pants', (0, 0, 0.3), (0.62, 0.5, 0.1), body)
    for sx, nm in ((-1, 'ArmL'), (1, 'ArmR')):
        arm = empty(nm, (sx * 0.38, 0, 0.78), root)
        cyl(nm + 'Sleeve', 'Outfit', (sx * 0.38, 0, 0.7), 0.1, 0.25, seg=8, parent=arm, smooth=True)
        sphere(nm + 'Hand', 'Skin', (sx * 0.38, 0, 0.52), 0.1, seg=8, rings=6, parent=arm)
    for sx, nm in ((-1, 'LegL'), (1, 'LegR')):
        leg = empty(nm, (sx * 0.15, 0, 0.3), root)
        cyl(nm + 'Mesh', 'Pants', (sx * 0.15, 0, 0.2), 0.11, 0.3, seg=8, parent=leg, smooth=True)
        sphere(nm + 'Shoe', 'Shoes', (sx * 0.15, -0.05, 0.07), 0.14, (1, 1.3, 0.7), seg=8, rings=6, parent=leg)
    export('character.glb')


# ----------------------------------------------------------------------- pets
def build_pet(kind):
    reset()
    root = empty(kind)
    if kind == 'lion':
        sphere('Mane', 'Mane', (0, 0.02, 0.55), 0.42, parent=root)
        sphere('Head', 'Lion', (0, -0.12, 0.55), 0.33, parent=root)
        sphere('Body', 'Lion', (0, 0.28, 0.3), 0.3, (1, 1.2, 0.9), parent=root)
        for sx in (-1, 1):
            sphere('Ear', 'Mane', (sx * 0.24, -0.02, 0.85), 0.1, parent=root, seg=8, rings=6)
            sphere('Eye', 'Eye', (sx * 0.11, -0.4, 0.6), 0.04, seg=6, rings=4, parent=root)
            cyl('Paw', 'Lion', (sx * 0.15, 0.1, 0.08), 0.09, 0.16, seg=8, parent=root)
            cyl('Paw2', 'Lion', (sx * 0.15, 0.5, 0.08), 0.09, 0.16, seg=8, parent=root)
        sphere('Nose', 'Black', (0, -0.44, 0.5), 0.05, seg=6, rings=4, parent=root)
        cyl('Tail', 'Lion', (0, 0.72, 0.35), 0.04, 0.4, seg=6, parent=root, rot=(math.radians(60), 0, 0))
        sphere('TailTip', 'Mane', (0, 0.86, 0.5), 0.08, seg=6, rings=4, parent=root)
    elif kind == 'penguin':
        sphere('Body', 'Penguin', (0, 0, 0.45), 0.38, (1, 0.9, 1.25), parent=root)
        sphere('Belly', 'Belly', (0, -0.14, 0.4), 0.3, (0.9, 0.6, 1.1), parent=root)
        sphere('Head', 'Penguin', (0, -0.02, 0.95), 0.28, parent=root)
        cyl('Beak', 'Beak', (0, -0.3, 0.93), 0.07, 0.15, seg=6, r2=0.0, parent=root, rot=(math.radians(90), 0, 0))
        for sx in (-1, 1):
            sphere('Eye', 'White', (sx * 0.12, -0.24, 1.0), 0.07, seg=6, rings=4, parent=root)
            sphere('Pupil', 'Eye', (sx * 0.12, -0.3, 1.0), 0.035, seg=6, rings=4, parent=root)
            sphere('Wing', 'Penguin', (sx * 0.4, 0, 0.5), 0.1, (0.4, 0.9, 1.5), parent=root)
            sphere('Foot', 'Beak', (sx * 0.15, -0.12, 0.04), 0.12, (1, 1.4, 0.3), seg=8, rings=4, parent=root)
    elif kind == 'monkey':
        sphere('Body', 'Monkey', (0, 0.1, 0.38), 0.3, (1, 0.9, 1.1), parent=root)
        sphere('Head', 'Monkey', (0, -0.08, 0.82), 0.32, parent=root)
        sphere('Face', 'MonkeyFace', (0, -0.24, 0.78), 0.22, (1, 0.5, 0.85), parent=root)
        for sx in (-1, 1):
            sphere('Ear', 'MonkeyFace', (sx * 0.34, -0.06, 0.85), 0.11, (0.5, 0.4, 1), seg=8, rings=6, parent=root)
            sphere('Eye', 'Eye', (sx * 0.1, -0.4, 0.88), 0.04, seg=6, rings=4, parent=root)
            sphere('Arm', 'Monkey', (sx * 0.34, 0.0, 0.4), 0.09, (0.8, 0.8, 1.6), parent=root)
            sphere('Foot', 'Monkey', (sx * 0.14, -0.05, 0.06), 0.11, (1, 1.4, 0.6), seg=8, rings=4, parent=root)
        cyl('Tail', 'Monkey', (0, 0.5, 0.45), 0.04, 0.6, seg=6, parent=root, rot=(math.radians(35), 0, 0))
    elif kind == 'parrot':
        sphere('Body', 'Parrot', (0, 0.05, 0.5), 0.3, (0.9, 0.9, 1.3), parent=root)
        sphere('Head', 'Parrot', (0, -0.1, 0.98), 0.25, parent=root)
        cyl('Beak', 'Beak', (0, -0.32, 0.95), 0.08, 0.2, seg=6, r2=0.0, parent=root, rot=(math.radians(110), 0, 0))
        for sx in (-1, 1):
            sphere('Eye', 'White', (sx * 0.1, -0.27, 1.03), 0.06, seg=6, rings=4, parent=root)
            sphere('Pupil', 'Eye', (sx * 0.1, -0.32, 1.03), 0.03, seg=6, rings=4, parent=root)
            sphere('Wing', 'Wing', (sx * 0.3, 0.1, 0.55), 0.1, (0.35, 1.0, 1.7), parent=root)
            cyl('Leg', 'Beak', (sx * 0.1, 0.0, 0.1), 0.025, 0.2, seg=6, parent=root)
        sphere('Tail1', 'Wing', (0, 0.4, 0.3), 0.08, (0.6, 1.3, 2.5), parent=root)
        sphere('Crest', 'Gold', (0, -0.05, 1.22), 0.07, (0.6, 0.6, 1.6), seg=6, rings=4, parent=root)
    export(f'pet_{kind}.glb')


# ------------------------------------------------------------------ buildings
def building(name, fn):
    reset()
    root = empty(name)
    fn(root)
    export(f'{name}.glb')


def b_cottage(r):  # Starter / Hello Village
    house_body(r, 'Wall', 'RoofRed', chimney=True)
    box('Sign', 'Wood', (1.9, -1.6, 0.6), (0.1, 0.1, 1.2), r)
    box('SignBoard', 'WallYellow', (1.9, -1.64, 1.1), (0.7, 0.08, 0.4), r)


def b_school(r):  # Unit 1
    box('Walls', 'WallYellow', (0, 0, 1.2), (5.0, 2.8, 2.4), r)
    roof('Roof', 'RoofRed', (0, 0, 2.4), 5.0, 2.8, 1.0, r)
    box('Clock', 'Cream', (0, -1.43, 2.5), (1.1, 0.12, 1.1), r)
    cyl('ClockFace', 'White', (0, -1.5, 2.5), 0.42, 0.06, seg=16, parent=r, rot=(math.radians(90), 0, 0))
    box('Hand1', 'Black', (0, -1.55, 2.62), (0.06, 0.04, 0.3), r)
    box('Hand2', 'Black', (0.12, -1.55, 2.5), (0.25, 0.04, 0.06), r)
    box('Door', 'DarkWood', (0, -1.43, 0.7), (1.0, 0.1, 1.4), r)
    for sx in (-1.6, -0.9, 0.9, 1.6):
        box('Win', 'Glass', (sx, -1.43, 1.3), (0.5, 0.1, 0.7), r)
    cyl('Pole', 'Stone', (3.0, -1.4, 1.5), 0.04, 3.0, seg=6, parent=r)
    box('Flag', 'Red', (3.3, -1.4, 2.7), (0.6, 0.04, 0.4), r)


def b_weather(r):  # Unit 2 weather tower
    cyl('Tower', 'WallBlue', (0, 0, 1.4), 1.0, 2.8, seg=12, parent=r, r2=0.8)
    cyl('Top', 'RoofBlue', (0, 0, 3.4), 1.1, 1.2, seg=12, parent=r, r2=0.0)
    sphere('Sun', 'Sun', (1.7, 0, 3.4), 0.5, parent=r)
    for i, (x, z) in enumerate(((-1.6, 3.0), (-2.1, 3.3), (-1.1, 3.3))):
        sphere(f'Cloud{i}', 'Cloud', (x, 0, z), 0.45, (1.2, 0.8, 0.8), parent=r)
    box('Door', 'DarkWood', (0, -0.95, 0.5), (0.6, 0.1, 1.0), r)


def b_family(r):  # Unit 3 big family house
    house_body(r, 'WallPink', 'RoofOrange', w=4.2, d=3.0, h=2.0, chimney=True)
    box('Fence', 'Wood', (0, -2.2, 0.3), (4.6, 0.08, 0.5), r)
    for x in (-2.3, 2.3):
        box('Post', 'DarkWood', (x, -2.2, 0.35), (0.12, 0.12, 0.7), r)


def b_town(r):  # Unit 4 around town
    box('Bank', 'Stone', (-1.8, 0, 1.4), (1.8, 1.8, 2.8), r)
    roof('BankRoof', 'RoofBlue', (-1.8, 0, 2.8), 1.8, 1.8, 0.6, r)
    for sx in (-2.4, -1.8, -1.2):
        cyl('Col', 'White', (sx, -1.0, 1.0), 0.1, 2.0, seg=8, parent=r)
    box('Shop', 'WallGreen', (0.4, 0, 0.9), (1.8, 1.8, 1.8), r)
    box('Awning', 'Red', (0.4, -1.1, 1.5), (1.9, 0.5, 0.1), r, rot=(math.radians(-15), 0, 0))
    box('Tall', 'WallPurple', (2.4, 0.2, 1.8), (1.4, 1.4, 3.6), r)
    for z in (1.0, 2.0, 3.0):
        box('W', 'Glass', (2.4, -0.52, z), (0.8, 0.06, 0.4), r)
    box('Road', 'Stone', (0.2, -2.2, 0.03), (6.0, 1.0, 0.06), r)


def b_cake(r):  # Unit 5 birthday food
    cyl('Layer1', 'WallPink', (0, 0, 0.7), 1.6, 1.4, seg=20, parent=r, smooth=True)
    cyl('Layer2', 'Cream', (0, 0, 1.8), 1.15, 0.9, seg=20, parent=r, smooth=True)
    cyl('Layer3', 'WallPink', (0, 0, 2.5), 0.7, 0.6, seg=20, parent=r, smooth=True)
    for i in range(8):
        a = i * math.pi / 4
        sphere('Cherry', 'Red', (math.cos(a) * 1.15, math.sin(a) * 1.15, 1.45), 0.12, seg=8, rings=6, parent=r)
    cyl('Candle', 'WallBlue', (0, 0, 3.0), 0.06, 0.5, seg=6, parent=r)
    sphere('Flame', 'Sun', (0, 0, 3.35), 0.1, (0.7, 0.7, 1.4), seg=8, rings=6, parent=r)
    box('Door', 'DarkWood', (0, -1.58, 0.45), (0.7, 0.1, 0.9), r)


def b_clock(r):  # Unit 6 My day
    box('Base', 'Stone', (0, 0, 0.5), (2.2, 2.2, 1.0), r)
    box('Tower', 'WallPurple', (0, 0, 2.4), (1.6, 1.6, 2.8), r)
    pyramid('Top', 'RoofPurple', (0, 0, 4.2), 1.3, 1.6, parent=r)
    for sy, rx in ((-0.82, 90), (0.82, -90)):
        cyl('Face', 'White', (0, sy, 2.8), 0.6, 0.08, seg=20, parent=r, rot=(math.radians(rx), 0, 0))
    box('Hand1', 'Black', (0, -0.9, 3.0), (0.07, 0.04, 0.45), r)
    box('Hand2', 'Black', (0.18, -0.9, 2.8), (0.35, 0.04, 0.07), r)
    box('Door', 'DarkWood', (0, -1.1, 0.4), (0.8, 0.1, 0.8), r)


def b_beach(r):  # Unit 7
    box('Hut', 'WallYellow', (0, 0, 0.9), (2.6, 2.2, 1.8), r)
    roof('Roof', 'RoofGreen', (0, 0, 1.8), 2.6, 2.2, 1.0, r, overhang=0.4)
    box('Door', 'DarkWood', (0, -1.12, 0.6), (0.7, 0.1, 1.2), r)
    cyl('UPole', 'Wood', (2.4, -1.0, 1.2), 0.05, 2.4, seg=6, parent=r)
    cyl('Umb', 'Red', (2.4, -1.0, 2.5), 1.2, 0.5, seg=10, parent=r, r2=0.0)
    box('Towel', 'WallBlue', (2.4, -2.0, 0.03), (1.0, 1.8, 0.06), r)
    sphere('Ball', 'Red', (-2.2, -1.4, 0.3), 0.3, parent=r)
    box('Board', 'Sand', (-2.0, 0.6, 0.9), (0.5, 0.08, 1.8), r, rot=(math.radians(-8), 0, math.radians(15)))


def b_story(r):  # Unit 8 storybook castle
    box('Keep', 'WallPurple', (0, 0, 1.6), (2.4, 2.0, 3.2), r)
    pyramid('KeepRoof', 'RoofBlue', (0, 0, 3.8), 1.9, 1.5, parent=r)
    for sx in (-1.9, 1.9):
        cyl('Tower', 'WallPink', (sx, 0, 1.6), 0.7, 3.2, seg=10, parent=r)
        cyl('TRoof', 'RoofRed', (sx, 0, 3.7), 0.9, 1.2, seg=10, parent=r, r2=0.0)
    for i, m in enumerate(('Book1', 'Book2', 'Book3', 'Book4')):
        box(f'Book{i}', m, (0, -1.8 - i * 0.0, 0.18 + i * 0.3), (1.6 - i * 0.15, 0.9, 0.28), r, rot=(0, 0, math.radians(i * 12 - 18)))
    box('Door', 'DarkWood', (0, -1.02, 0.7), (0.9, 0.1, 1.4), r)


def b_tent(r):  # camps
    pyramid('Tent', 'RoofOrange', (0, 0, 0.9), 1.8, 1.8, seg=4, parent=r)
    box('Flap', 'DarkWood', (0, -0.9, 0.5), (0.7, 0.05, 1.0), r, rot=(math.radians(-8), 0, 0))
    cyl('Log1', 'Trunk', (2.0, -0.6, 0.15), 0.15, 1.0, seg=8, parent=r, rot=(0, math.radians(90), math.radians(20)))
    cyl('Log2', 'Trunk', (2.0, -0.2, 0.15), 0.15, 1.0, seg=8, parent=r, rot=(0, math.radians(90), math.radians(-15)))
    cyl('Fire', 'Stone', (1.8, -1.3, 0.1), 0.45, 0.2, seg=10, parent=r)
    cyl('Flame', 'Sun', (1.8, -1.3, 0.45), 0.25, 0.6, seg=8, parent=r, r2=0.0)


def b_inn(r):  # inn with bed sign
    house_body(r, 'WallYellow', 'RoofGreen', w=3.8, d=2.8, h=1.9)
    cyl('SignPole', 'Wood', (2.4, -1.6, 1.0), 0.05, 2.0, seg=6, parent=r)
    box('Sign', 'Cream', (2.4, -1.65, 1.9), (0.9, 0.08, 0.6), r)
    box('Bed', 'Red', (2.4, -1.72, 1.9), (0.6, 0.06, 0.25), r)
    box('Lantern', 'Gold', (-1.2, -1.45, 1.5), (0.2, 0.2, 0.3), r)


def b_arena(r):  # duel arena
    cyl('Floor', 'Sand', (0, 0, 0.1), 3.2, 0.2, seg=24, parent=r)
    cyl('Ring', 'Stone', (0, 0, 0.22), 2.2, 0.06, seg=24, parent=r)
    for i in range(10):
        a = i * math.pi / 5
        cyl('Pillar', 'Stone', (math.cos(a) * 3.0, math.sin(a) * 3.0, 0.9), 0.22, 1.6, seg=8, parent=r)
        sphere('Cap', 'Gold', (math.cos(a) * 3.0, math.sin(a) * 3.0, 1.8), 0.2, seg=8, rings=6, parent=r)
    box('Sword1', 'Stone', (0, 0, 0.6), (0.12, 0.05, 0.9), r, rot=(0, math.radians(35), 0))
    box('Sword2', 'Stone', (0, 0, 0.6), (0.12, 0.05, 0.9), r, rot=(0, math.radians(-35), 0))


def b_festival(r):  # striped festival tent
    cyl('Base', 'Cream', (0, 0, 0.9), 2.2, 1.8, seg=12, parent=r)
    for i in range(6):
        a = i * math.pi / 3
        box(f'Stripe{i}', 'Red' if i % 2 == 0 else 'White', (math.cos(a) * 2.1, math.sin(a) * 2.1, 0.9), (0.9, 0.12, 1.7), r, rot=(0, 0, a + math.pi / 2))
    cyl('Top', 'Red', (0, 0, 2.5), 2.5, 1.6, seg=12, parent=r, r2=0.0)
    cyl('Pole', 'Wood', (0, 0, 3.6), 0.05, 0.9, seg=6, parent=r)
    box('Flag', 'Gold', (0.3, 0, 3.9), (0.6, 0.04, 0.4), r)
    for i, m in enumerate(('Red', 'Wing', 'Gold', 'Leaf')):
        sphere(f'Balloon{i}', m, (3.0 + i * 0.35, -0.3 + i * 0.2, 2.4 + i * 0.3), 0.3, (1, 1, 1.2), seg=8, rings=6, parent=r)


def b_sound(r):  # sound library
    box('Walls', 'WallBlue', (0, 0, 1.2), (3.6, 2.6, 2.4), r)
    roof('Roof', 'RoofPurple', (0, 0, 2.4), 3.6, 2.6, 1.0, r)
    box('Door', 'DarkWood', (0, -1.33, 0.65), (0.9, 0.1, 1.3), r)
    for sx in (-1.2, 1.2):
        cyl('Speaker', 'Black', (sx, -1.35, 1.5), 0.45, 0.2, seg=16, parent=r, rot=(math.radians(90), 0, 0))
        cyl('Cone', 'Stone', (sx, -1.47, 1.5), 0.2, 0.1, seg=12, parent=r, rot=(math.radians(90), 0, 0))
    for i in range(3):
        sphere('Note', 'Gold', (2.4, -0.8 + i * 0.1, 1.2 + i * 0.5), 0.14, seg=8, rings=6, parent=r)
        box('Stem', 'Gold', (2.52, -0.8 + i * 0.1, 1.45 + i * 0.5), (0.04, 0.04, 0.4), r)


# ---------------------------------------------------------------------- props
def b_tree(r):
    cyl('Trunk', 'Trunk', (0, 0, 0.5), 0.2, 1.0, seg=8, parent=r)
    sphere('Leaves', 'Leaf', (0, 0, 1.6), 0.9, (1, 1, 1.1), parent=r)
    sphere('Leaves2', 'LeafDark', (0.4, 0.2, 1.3), 0.55, parent=r)


def b_pine(r):
    cyl('Trunk', 'Trunk', (0, 0, 0.4), 0.18, 0.8, seg=6, parent=r)
    for i, (rr, z) in enumerate(((0.95, 1.0), (0.75, 1.6), (0.5, 2.2))):
        cyl(f'L{i}', 'LeafDark', (0, 0, z), rr, 0.9, seg=8, parent=r, r2=0.0)


def b_rock(r):
    sphere('Rock', 'Stone', (0, 0, 0.3), 0.5, (1.2, 1.0, 0.7), seg=7, rings=5, parent=r, smooth=False)
    sphere('Rock2', 'Stone', (0.5, 0.3, 0.2), 0.3, (1, 1, 0.7), seg=7, rings=5, parent=r, smooth=False)


def b_flower(r):
    cyl('Stem', 'Leaf', (0, 0, 0.2), 0.03, 0.4, seg=5, parent=r)
    for i in range(5):
        a = i * 2 * math.pi / 5
        sphere('P', 'WallPink', (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.45), 0.08, seg=6, rings=4, parent=r)
    sphere('C', 'Sun', (0, 0, 0.45), 0.06, seg=6, rings=4, parent=r)


if __name__ == '__main__':
    build_character()
    for k in ('lion', 'penguin', 'monkey', 'parrot'):
        build_pet(k)
    for n, f in (('b_cottage', b_cottage), ('b_school', b_school), ('b_weather', b_weather), ('b_family', b_family), ('b_town', b_town),
                 ('b_cake', b_cake), ('b_clock', b_clock), ('b_beach', b_beach), ('b_story', b_story), ('b_tent', b_tent), ('b_inn', b_inn),
                 ('b_arena', b_arena), ('b_festival', b_festival), ('b_sound', b_sound),
                 ('p_tree', b_tree), ('p_pine', b_pine), ('p_rock', b_rock), ('p_flower', b_flower)):
        building(n, f)
