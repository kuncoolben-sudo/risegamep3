"""The sky: a dome shaded from deep blue overhead to a pale haze at the horizon, a ring of flat cartoon clouds, the sun,
the moon and stars, all vertex-coloured. The game draws it unlit round the camera (radius 1 here, scaled up there): the
dome first, then the rest over it. These are the daytime colours; src/world3d/daylight.ts recolours the dome, tints the
clouds, moves the sun and fades the moon and stars in and out with the time of day."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from .layout import _lin, hexc, mix

STOPS = [(-1.0, '#7cc0ea'), (-0.03, '#c4ebff'), (0.0, '#cdeeff'), (0.04, '#a9ddff'), (0.12, '#82c8fa'), (0.3, '#5cb1f2'),
         (0.6, '#4a9fea'), (1.0, '#3a8ee2')]  # elevation (sine) -> colour; the game's fog matches the horizon
SUN = Vector((14.0, -10.0, 24.0)).normalized()  # where the game's daytime sunlight comes from (three.js (14, 24, 10))
MOON = Vector((-0.3, 0.78, 0.55)).normalized()  # high over the far side of the island (three.js (-0.3, 0.55, -0.78))
CLOUD = [(0.0, '#c8d7ec'), (0.45, '#eef5fd'), (1.0, '#ffffff')]  # bottom to top


def ramp(stops, z):
    for (z0, c0), (z1, c1) in zip(stops, stops[1:]):
        if z <= z1:
            return mix(hexc(c0), hexc(c1), max(0.0, min(1.0, (z - z0) / (z1 - z0))))
    return hexc(stops[-1][1])


def frame(n):
    """Horizontal and upward unit vectors of the plane facing the centre at direction n."""
    u = Vector((-n.y, n.x, 0.0))
    u = u.normalized() if u.length > 1e-6 else Vector((0.0, 1.0, 0.0))
    return u, n.cross(u)


class Painter:
    """Triangle fans with a colour per vertex, gathered into one mesh."""

    def __init__(self):
        self.bm = bmesh.new()
        self.cols = []

    def vert(self, co, col):
        self.cols.append([_lin(c) for c in col] + [1.0])
        return self.bm.verts.new(co)

    def fan(self, centre, ring, ccol, rcol):
        c = self.vert(centre, ccol)
        vs = [self.vert(p, col) for p, col in zip(ring, rcol)]
        for i in range(len(vs)):
            self.bm.faces.new((c, vs[i], vs[(i + 1) % len(vs)]))

    def mesh(self, name, coll):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
        for i, col in enumerate(self.cols):
            attr.data[i].color = col
        return finish(me, name, coll)


def finish(me, name, coll):
    me.color_attributes.active_color = me.color_attributes['Color']
    me.color_attributes.render_color_index = me.color_attributes.active_color_index
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    col = nodes.new('ShaderNodeVertexColor')
    col.layer_name = 'Color'
    mat.node_tree.links.new(col.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def dome(coll):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)  # seen from inside
    me = bpy.data.meshes.new('SkyDome')
    bm.to_mesh(me)
    bm.free()
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    for v in me.vertices:
        attr.data[v.index].color = [_lin(c) for c in ramp(STOPS, v.co.z)] + [1.0]
    for poly in me.polygons:
        poly.use_smooth = True
    return finish(me, 'SkyDome', coll)


def clouds(coll):
    paint = Painter()
    rnd = random.Random(4)
    for i in range(30):
        az = math.radians(i * 12 + rnd.uniform(-4, 4))
        high = i % 4 == 3
        el = math.radians(rnd.uniform(22, 46) if high else rnd.uniform(2.5, 14))
        w = rnd.uniform(0.07, 0.1) if high else rnd.uniform(0.09, 0.16)
        hc = w * rnd.uniform(0.42, 0.55)
        n = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        u, v = frame(n)
        base = n * 0.9

        def puff(cx, cy, rx, ry, seg=18):
            ring, rc = [], []
            for k in range(seg):
                a = 2 * math.pi * k / seg
                x, y = cx + math.cos(a) * rx, max(0.0, cy + math.sin(a) * ry)  # flat bottoms
                ring.append(base + u * x + v * y)
                rc.append(ramp(CLOUD, y / (hc * 1.1)))
            paint.fan(base + u * cx + v * max(0.0, cy), ring, ramp(CLOUD, max(0.0, cy) / (hc * 1.1) + 0.15), rc)

        puff(0.0, hc * 0.18, w * 0.95, hc * 0.32)
        k = rnd.randint(4, 6)
        for j in range(k):
            x = (-0.6 + 1.2 * j / (k - 1)) * w * 0.85 + rnd.uniform(-0.05, 0.05) * w
            r = w * rnd.uniform(0.3, 0.46) * (1 - 0.35 * abs(x) / w)
            puff(x, r * 0.55 + rnd.uniform(0, 0.15) * hc, r, r)
    return paint.mesh('Clouds', coll)


def sun(coll):
    paint = Painter()
    u, v = frame(SUN)
    sky = ramp(STOPS, SUN.z)
    for r, cc, rc in ((0.17, '#fff4d2', None), (0.05, '#fffef4', '#fff1b8')):
        ring = [SUN * 0.95 + (u * math.cos(2 * math.pi * k / 28) + v * math.sin(2 * math.pi * k / 28)) * r for k in range(28)]
        paint.fan(SUN * 0.95, ring, hexc(cc), [sky if rc is None else hexc(rc)] * 28)
    return paint.mesh('Sun', coll)


def disc(c, u, v, r, n=28):
    return [c + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * r for k in range(n)]


def moon(coll):
    """A pale moon with a soft glow (its rim takes the night sky's colour in the game) and three shallow craters."""
    paint = Painter()
    u, v = frame(MOON)
    c = MOON * 0.95
    paint.fan(c, disc(c, u, v, 0.1), hexc('#c9d6ff'), [ramp(STOPS, MOON.z)] * 28)
    paint.fan(c, disc(c, u, v, 0.036), hexc('#fffbe8'), [hexc('#f2edd8')] * 28)
    for ox, oy, r in ((0.011, 0.008, 0.007), (-0.012, -0.004, 0.005), (0.004, -0.014, 0.004)):
        cc = c + u * ox + v * oy
        paint.fan(cc, disc(cc, u, v, r, 12), hexc('#e2dac0'), [hexc('#e9e2ca')] * 12)
    return paint.mesh('Moon', coll)


def stars(coll):
    """Tiny four-pointed stars over the upper sky, a little denser away from the horizon."""
    paint = Painter()
    rnd = random.Random(8)
    for _ in range(420):
        z = rnd.uniform(0.06, 1.0)
        a = rnd.uniform(0, 2 * math.pi)
        n = Vector((math.sqrt(1 - z * z) * math.cos(a), math.sqrt(1 - z * z) * math.sin(a), z))
        u, v = frame(n)
        s = rnd.uniform(0.0022, 0.005)
        col = hexc(rnd.choice(('#ffffff', '#ffffff', '#fff6d8', '#dfe8ff')))
        c = n * 0.97
        paint.fan(c, [c + u * s, c + v * s, c - u * s, c - v * s], col, [col] * 4)
    return paint.mesh('Stars', coll)


def build(coll):
    return [dome(coll), clouds(coll), sun(coll), moon(coll), stars(coll)]
