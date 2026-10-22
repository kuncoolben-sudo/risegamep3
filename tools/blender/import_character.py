"""Turn a dense, textured character model (e.g. from an AI 3D generator: ~1M loose triangles, 4k textures, no skeleton)
into a game character: public/models/char_<preset>.glb.

    blender -b --python tools/blender/import_character.py -- <preset> [source.glb]

The source defaults to characters/<preset>.glb (not in git: the originals are ~80 MB each).

1. Weld the loose triangles into one surface and decimate a copy to ~24k triangles.
2. Unwrap the copy afresh and bake the original's colours onto it (2048 px). Decimating the original's own UVs smears
   its texture across its many seams, which shows as cracked, speckled patches.
3. Stand it up on z = 0, 1.9 m tall like the other characters, front towards -Y (the game camera).
4. Add the skeleton the game swings while walking (src/world3d/World3D.tsx `swing`): Body, Spine, Head, LegL/LegR and
   ArmL/ArmR for arms that hang free, each limb's x axis sideways, with weights from where each vertex sits, blended
   across the joints. An arm posed holding something (a strap, a book, waving) gets no bone and stays still.

Joints in CHARACTERS were read off a front render of each model at game size (1.9 m, centred on its bounding box);
measure a new model the same way before adding it.
"""
import os
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:]
PRESET = ARGS[0]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = ARGS[1] if len(ARGS) > 1 else os.path.join(ROOT, 'characters', PRESET + '.glb')
OUT = os.path.join(ROOT, 'public', 'models', f'char_{PRESET}.glb')
TRIS, SIZE, HEIGHT = 24000, 2048, 1.9

# cx: middle between the legs (cx_foot: between the feet, if a wide stance moves it); hip: top of the legs; legs: x of each knee / foot; arms: side -> (shoulder, hand) as (x, z),
# with 'in' the |x| where the arm starts (keeps belts and pouches off it) and 'top' how high its weights reach
CHARACTERS = {
    'kai': dict(cx=-0.03, hip=0.48, legs=(-0.18, 0.12), arms={'L': ((-0.30, 1.0), (-0.39, 0.55)), 'R': ((0.26, 1.0), (0.35, 0.55))}),
    'pond': dict(cx=-0.03, hip=0.48, legs=(-0.16, 0.13), arms={'L': ((-0.27, 1.02), (-0.37, 0.5))}, arm_in=0.27, arm_low=0.4),
    'beam': dict(cx=0.0, hip=0.47, legs=(-0.18, 0.18), arms={'R': ((0.22, 1.04), (0.28, 0.62))}, arm_in=0.23),
    'lily': dict(cx=-0.03, hip=0.58, legs=(-0.14, 0.1), arms={'L': ((-0.2, 1.1), (-0.33, 0.66))}, arm_top=0.98),
    'minnie': dict(cx=-0.05, hip=0.55, legs=(-0.18, 0.1), arms={}),
    'maya': dict(cx=0.0, cx_foot=-0.08, hip=0.55, legs=(-0.13, 0.12), arms={}),
}
C = CHARACTERS[PRESET]
CX, HIP = C['cx'], C['hip']
RIG = {  # name: head, tail, parent
    'Body': ((CX, 0, HIP), (CX, 0, 0.75), None),
    'Spine': ((CX, 0, 0.75), (CX, 0, 1.1), 'Body'),
    'Head': ((CX, 0, 1.1), (CX, 0, 1.85), 'Spine'),
    'LegL': ((C['legs'][0], 0, HIP), (C['legs'][0], -0.03, 0.05), 'Body'),
    'LegR': ((C['legs'][1], 0, HIP), (C['legs'][1], -0.03, 0.05), 'Body'),
}
for side, ((sx, sz), (hx, hz)) in C['arms'].items():
    RIG['Arm' + side] = ((sx, 0, sz), (hx, -0.02, hz), 'Spine')


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def only(*objs):
    for o in bpy.context.scene.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[-1]


def low_poly():
    """The decimated copy, baked with the original's colours; the original is removed."""
    hi = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    hi.parent = None
    only(hi)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    nt = hi.active_material.node_tree  # its colour straight to emission: the bake copies it exactly
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    emit = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(bsdf.inputs['Base Color'].links[0].from_socket, emit.inputs['Color'])
    nt.links.new(emit.outputs[0], next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL').inputs['Surface'])

    lo = hi.copy()
    lo.data = hi.data.copy()
    bpy.context.scene.collection.objects.link(lo)
    only(lo)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=max(hi.dimensions) * 0.0005)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = lo.modifiers.new('dec', 'DECIMATE')
    mod.ratio = TRIS / sum(len(p.vertices) - 2 for p in lo.data.polygons)
    bpy.ops.object.modifier_apply(modifier='dec')
    while lo.data.uv_layers:
        lo.data.uv_layers.remove(lo.data.uv_layers[0])
    lo.data.uv_layers.new(name='UV')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.396, island_margin=0.012, area_weight=1.0)
    bpy.ops.object.mode_set(mode='OBJECT')

    img = bpy.data.images.new('Color', SIZE, SIZE)
    mat = bpy.data.materials.new('Character')
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = img
    pb = mat.node_tree.nodes['Principled BSDF']
    mat.node_tree.links.new(tex.outputs['Color'], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = 0.65
    mat.node_tree.nodes.active = tex
    lo.data.materials.clear()
    lo.data.materials.append(mat)

    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    size = max(hi.dimensions)
    only(hi, lo)
    bpy.ops.object.bake(type='EMIT', use_selected_to_active=True, cage_extrusion=size * 0.03, max_ray_distance=size * 0.06, margin=16)
    img.pack()
    bpy.data.objects.remove(hi, do_unlink=True)

    co = [lo.matrix_world @ v.co for v in lo.data.vertices]
    mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
    mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
    k = HEIGHT / (mx.z - mn.z)
    lo.location = (-(mn.x + mx.x) / 2 * k, -(mn.y + mx.y) / 2 * k, -mn.z * k)
    lo.scale = (k, k, k)
    only(lo)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return lo


def rig(ob):
    data = bpy.data.armatures.new('Rig')
    arm = bpy.data.objects.new('Rig', data)
    bpy.context.scene.collection.objects.link(arm)
    only(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, (h, t, par) in RIG.items():
        b = data.edit_bones.new(name)
        b.head, b.tail = Vector(h), Vector(t)
        if par:
            b.parent = data.edit_bones[par]
    for name in [n for n in RIG if n[:3] in ('Arm', 'Leg')]:  # the game swings limbs about their own x axis: make it sideways
        b = data.edit_bones[name]
        b.roll = max((r * 0.0174533 for r in range(0, 360, 5)), key=lambda r: (setattr(b, 'roll', r), b.x_axis.x)[1])
    bpy.ops.object.mode_set(mode='OBJECT')

    groups = {n: ob.vertex_groups.new(name=n) for n in RIG}
    for v in ob.data.vertices:
        x, z = v.co.x - CX, v.co.z
        w = {}
        split = (C.get('cx_foot', CX) - CX) * (1 - smooth(0.05, 0.4, z))
        side = 'L' if x < split else 'R'
        leg = smooth(HIP + 0.08, HIP - 0.06, z)  # thighs blend into the hips
        if leg > 0:
            w['Leg' + side] = leg
        a_in, low, top = C.get('arm_in', 0.21), C.get('arm_low', 0.42), C.get('arm_top', 1.1)
        arm_w = smooth(a_in, a_in + 0.08, abs(x)) * smooth(low, low + 0.08, z) * smooth(top, top - 0.12, z)
        if arm_w > 0 and 'Arm' + side in RIG:
            w['Arm' + side] = arm_w
        head = smooth(1.06, 1.18, z)
        if head > 0:
            w['Head'] = head
        rest = 1 - sum(w.values())
        if rest > 0:
            w['Spine' if z > 0.75 else 'Body'] = rest
        for n, val in w.items():
            groups[n].add([v.index], val, 'REPLACE')
    ob.parent = arm
    ob.modifiers.new('Rig', 'ARMATURE').object = arm
    return arm


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
body = low_poly()
skeleton = rig(body)
only(body, skeleton)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True, export_image_format='JPEG',
                          export_image_quality=88, export_draco_mesh_compression_enable=True, export_animations=False, export_skins=True)
print('wrote', OUT)
