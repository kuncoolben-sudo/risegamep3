"""Turn a dense, textured character model (e.g. from an AI 3D generator: ~1M loose triangles, 4k textures, no skeleton)
into a game character: public/models/char_<preset>.glb.

    blender -b --python tools/blender/import_character.py -- <source.glb> <output.glb>

1. Weld the loose triangles into one surface and decimate a copy to ~24k triangles.
2. Unwrap the copy afresh and bake the original's colours onto it (2048 px). Decimating the original's own UVs smears
   its texture across its many seams, which shows as cracked, speckled patches.
3. Stand it up on z = 0, 1.9 m tall like the other characters, front towards -Y (the game camera).
4. Add the skeleton the game swings while walking (src/world3d/World3D.tsx `swing`): Body, Spine, Head, ArmL/ArmR,
   LegL/LegR, each limb's x axis sideways, with weights from where each vertex sits, blended across the joints.

The joint heights in RIG fit Kai's proportions (big head, short legs: hips 0.48, shoulders 1.0, hands 0.55); check them
against a new model (slice it by height) before using this for another character.
"""
import sys

import bpy
from mathutils import Vector

SRC, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
TRIS, SIZE, HEIGHT = 24000, 2048, 1.9
CX = -0.03  # Kai's middle, between the legs (after centring)
RIG = {  # name: head, tail, parent
    'Body': ((CX, 0, 0.48), (CX, 0, 0.75), None),
    'Spine': ((CX, 0, 0.75), (CX, 0, 1.1), 'Body'),
    'Head': ((CX, 0, 1.1), (CX, 0, 1.85), 'Spine'),
    'ArmL': ((CX - 0.27, 0, 1.0), (CX - 0.36, -0.02, 0.55), 'Spine'),
    'ArmR': ((CX + 0.29, 0, 1.0), (CX + 0.38, -0.02, 0.55), 'Spine'),
    'LegL': ((CX - 0.15, 0, 0.48), (CX - 0.16, -0.03, 0.05), 'Body'),
    'LegR': ((CX + 0.15, 0, 0.48), (CX + 0.16, -0.03, 0.05), 'Body'),
}


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
    for name in ('ArmL', 'ArmR', 'LegL', 'LegR'):  # the game swings limbs about their own x axis: make it sideways
        b = data.edit_bones[name]
        b.roll = max((r * 0.0174533 for r in range(0, 360, 5)), key=lambda r: (setattr(b, 'roll', r), b.x_axis.x)[1])
    bpy.ops.object.mode_set(mode='OBJECT')

    groups = {n: ob.vertex_groups.new(name=n) for n in RIG}
    for v in ob.data.vertices:
        x, z = v.co.x - CX, v.co.z
        w = {}
        side = 'L' if x < 0 else 'R'
        leg = smooth(0.56, 0.42, z)  # thighs blend into the hips
        if leg > 0:
            w['Leg' + side] = leg
        arm_w = smooth(0.21, 0.29, abs(x)) * smooth(0.42, 0.5, z) * smooth(1.1, 0.98, z)
        if arm_w > 0:
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
