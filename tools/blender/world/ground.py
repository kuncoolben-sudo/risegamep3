"""The island's ground as one flat-shaded mesh with a colour per face (vertex colours: one material, one draw call).

Vertices are scattered with a quadtree (fine where the ground changes shape: the north features, the cliffs, the
waterlines and the islets; coarse on the flat grass and the deep sea floor), jittered and Delaunay-triangulated."""
import math
import random

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

from . import layout as L

RMAX = 200.0  # the sea floor reaches this far; the game's sea and fog hide its edge


def spacing(x, y):
    """Wanted distance between ground vertices at (x, y)."""
    r = math.hypot(x, y)
    kind = L.islet_at(x, y, 1.2)
    if kind:
        return 2.5 if kind == 'volcano' else 1.25
    phi = math.degrees(math.atan2(y, x)) % 360
    if y > 16 and r < 50:
        return 1.25  # lake, waterfall and mountains inside the island
    if 34 < r < 50:
        return 1.25 if L.window(phi, *L.CLIFFS, 12) > 0 else 2.5  # cliffs need detail, beaches less
    if y > 14 and r < 96:
        return 2.5  # the high range behind
    if r < 34:
        return 5.0  # flat grass
    return 5.0 if r < 80 else 10.0


def points():
    rnd = random.Random(5)
    pts = []

    def cell(x0, y0, size):
        cx, cy = x0 + size / 2, y0 + size / 2
        want = min(spacing(cx, cy), spacing(x0, y0), spacing(x0 + size, y0), spacing(x0, y0 + size), spacing(x0 + size, y0 + size))
        if size > want * 1.05:
            h = size / 2
            for dx in (0, h):
                for dy in (0, h):
                    cell(x0 + dx, y0 + dy, h)
        else:
            j = size * 0.36
            x, y = cx + rnd.uniform(-j, j), cy + rnd.uniform(-j, j)
            if math.hypot(x, y) < RMAX - 2:
                pts.append((x, y))

    top = 20.0  # cell sizes 20, 10, 5, 2.5, 1.25
    n = int(math.ceil(RMAX / top))
    for i in range(-n, n):
        for j in range(-n, n):
            cell(i * top, j * top, top)
    for k in range(64):  # a round rim
        a = 2 * math.pi * k / 64
        pts.append((math.cos(a) * RMAX, math.sin(a) * RMAX))
    return pts


def build(coll):
    pts = points()
    verts, _, faces, _, _, _ = delaunay_2d_cdt([Vector(p) for p in pts], [], [], 0, 1e-5)
    bm = bmesh.new()
    bv = [bm.verts.new((v.x, v.y, L.height(v.x, v.y))) for v in verts]
    for f in faces:
        try:
            bm.faces.new([bv[i] for i in f])
        except ValueError:
            pass
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new('Ground')
    bm.to_mesh(me)
    bm.free()
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'CORNER')
    rnd = random.Random(9)
    for poly in me.polygons:
        c = poly.center
        col = L.face_color(c.x, c.y, c.z, poly.normal.z, rnd.uniform(-0.035, 0.035))
        for li in poly.loop_indices:
            attr.data[li].color = col
    me.color_attributes.active_color = attr
    me.color_attributes.render_color_index = me.color_attributes.active_color_index
    mat = bpy.data.materials.new('Ground')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 1.0
    col = nodes.new('ShaderNodeVertexColor')
    col.layer_name = 'Color'
    mat.node_tree.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
    me.materials.append(mat)
    ob = bpy.data.objects.new('Ground', me)
    coll.objects.link(ob)
    return ob, len(me.polygons)
