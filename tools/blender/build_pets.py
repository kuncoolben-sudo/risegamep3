"""Six fantasy pets x three forms (growth stages 1-3), each with an Idle loop and a Cast (power) clip, plus Cast1/Cast2 with the powers of the earlier forms.

Inside Blender (Scripting tab, or the MCP) this builds them in a 'Pets' collection, one row per species, and
exports public/models/pet_<id>_<form>.glb. Headless (Blender binary, or `pip install bpy` and python):

    blender -b --python tools/blender/build_pets.py -- [output_dir]
    python tools/blender/build_pets.py [output_dir]

Species modules live in tools/blender/pets/ (kit.py has the shared toolkit and the conventions). Set the globals
ONLY (list of species ids) and EXPORT (bool) before exec'ing this file to build a subset or to skip exporting.
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

SPECIES = ['skyra', 'blazion', 'kirin', 'lunara', 'aquaria', 'kitsune']

sys.path.insert(0, HERE)
for _n in [n for n in sys.modules if n == 'pets' or n.startswith('pets.')]:
    del sys.modules[_n]  # re-exec in a live Blender session must see edited modules
kit = importlib.import_module('pets.kit')


def cast_keys(mod, pose, body):
    """Clip keys of the power of form `pose` for a body of form `body` (modules with form-dependent pivots define cast_keys)."""
    fn = getattr(mod, 'cast_keys', None)
    return fn(pose, body) if fn else mod.CAST[pose]


def main():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    coll = bpy.data.collections.get('Pets') or bpy.data.collections.new('Pets')
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for o in list(coll.objects):  # rebuild cleanly on re-run
        bpy.data.objects.remove(o, do_unlink=True)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.actions):
        for d in [d for d in datablocks if d.users == 0]:
            datablocks.remove(d)
    os.makedirs(OUT, exist_ok=True)
    report = []
    for si, name in enumerate(SPECIES):
        if ONLY and name not in ONLY:
            continue
        mod = importlib.import_module(f'pets.{name}')
        for form in (1, 2, 3):
            pet = kit.Pet(f'{name}_{form}', mod.PALETTE, coll, mod.SCALE[form])
            mod.build(pet, form)
            pet.finish()
            kit.idle(pet)
            pet.animate('Cast', cast_keys(mod, form, form))
            for earlier in range(1, form):  # the powers of the earlier forms, played by this body: Cast1, Cast2
                pet.animate(f'Cast{earlier}', cast_keys(mod, earlier, form))
            pet.root.location = (si * 11 + (form - 2) * 3.6, 0, 0)
            if EXPORT:
                path = os.path.join(OUT, f'pet_{name}_{form}.glb')
                pet.export(path)
                report.append(f'{os.path.basename(path)}: {os.path.getsize(path) / 1024:.0f} KB')
    for line in report:
        print(line)


main()
