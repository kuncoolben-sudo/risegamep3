"""The eight Thai landmark scenes of the map (Unit locations): public/models/loc_<id>.glb, one static model each.

Inside Blender (Scripting tab, or the MCP) this builds them in a 'Places' collection, in a row, and exports them. Headless:

    blender -b --python tools/blender/build_places.py -- [output_dir]
    python tools/blender/build_places.py [output_dir]

Each module in tools/blender/places/ has PALETTE, RADIUS (radius of its round base), LABEL_Y (height of the name label
above the model) and build(p); the game reads those two numbers from LOCATION_MODEL in src/world3d/config.ts, so update
them there when they change. The GLBs are Draco-compressed (decoded with public/draco/). Set the globals ONLY (list of
ids) and EXPORT (bool) before exec'ing this file to build a subset or to skip exporting.
"""
import importlib
import os
import sys

import bpy

# exec'd without __file__ (e.g. from the Blender MCP) it falls back to the repo's usual location
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r'F:\risewebgame\p3\tools\blender'
_argv = [a for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]) if os.path.isdir(a)]
OUT = os.path.abspath(globals().get('OUT_DIR') or (_argv[0] if _argv else os.path.join(HERE, '../../public/models')))
ONLY = globals().get('ONLY')
EXPORT = globals().get('EXPORT', True)

PLACES = ['palace', 'phuket', 'chiangmai', 'khaoyai', 'phiphi', 'whitetemple', 'amphawa', 'inthanon']

sys.path.insert(0, HERE)
for _n in [n for n in sys.modules if n.split('.')[0] in ('pets', 'places')]:
    del sys.modules[_n]  # re-exec in a live Blender session must see edited modules
kit = importlib.import_module('pets.kit')


def main():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    coll = bpy.data.collections.get('Places') or bpy.data.collections.new('Places')
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for o in list(coll.objects):  # rebuild cleanly on re-run
        bpy.data.objects.remove(o, do_unlink=True)
    for datablocks in (bpy.data.meshes, bpy.data.materials):
        for d in [d for d in datablocks if d.users == 0]:
            datablocks.remove(d)
    os.makedirs(OUT, exist_ok=True)
    report = []
    for i, name in enumerate(PLACES):
        if ONLY and name not in ONLY:
            continue
        mod = importlib.import_module(f'places.{name}')
        p = kit.Pet(f'loc_{name}', mod.PALETTE, coll, 1.0)
        mod.build(p)
        p.finish()
        p.root.location = (i * 13, 0, 0)
        if EXPORT:
            path = os.path.join(OUT, f'loc_{name}.glb')
            p.export(path, draco=True)
            tris = sum(len(o.data.polygons) for o in p.objs if o.type == 'MESH')
            report.append(f'{os.path.basename(path)}: {os.path.getsize(path) / 1024:.0f} KB, {tris} faces')
    for line in report:
        print(line)


main()
