"""Head-and-shoulders portraits of the preset characters for the status bar: public/avatars/<preset>.png (transparent, 192 px).

    blender -b --factory-startup --python tools/blender/render_avatars.py

Run after import_character.py; reads public/models/char_<preset>.glb.
"""
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRESETS = ['kai', 'pond', 'beam', 'lily', 'minnie', 'maya']
OUT_DIR = os.path.join(ROOT, 'public', 'avatars')
os.makedirs(OUT_DIR, exist_ok=True)
CENTER_Z, SCALE = 1.54, 0.82  # the big head, a little of the shoulders

for preset in PRESETS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'public', 'models', f'char_{preset}.glb'))
    sc = bpy.context.scene
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = SCALE
    cam.location = (0, -10, CENTER_Z)
    cam.rotation_euler = (1.5708, 0, 0)
    sc.camera = cam
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3
    sun.rotation_euler = (0.9, 0.15, 0.5)
    sc.collection.objects.link(sun)
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.4
    r = sc.render
    r.engine = 'BLENDER_EEVEE'
    r.film_transparent = True
    r.resolution_x = r.resolution_y = 192
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGBA'
    r.filepath = os.path.join(OUT_DIR, f'{preset}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', r.filepath)
