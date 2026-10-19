"""Toolkit shared by the pet builders in this folder (driven by ../build_pets.py).

Geometry is collected per (pivot, material) in bmesh accumulators, in world coordinates, and turned into one
mesh per pair by finish(). That keeps the GLBs small and the draw calls few. Pivots are empties (Head, WingL,
Tail, ...) that the Idle and Cast clips rotate; the game finds them by name.

Conventions as everywhere in tools/blender: Z up, pets face -Y (+Z in glTF), feet on z = 0, left is -X.
All lengths given to the primitives are multiplied by the pet's scale, angles are in degrees.
"""
import math

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

V = Vector
FPS = 24


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgba(h, a=1.0):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (_lin(r), _lin(g), _lin(b), a)


def _perp(d):
    """Any unit vector perpendicular to d."""
    a = V((1, 0, 0)) if abs(d.x) < 0.9 else V((0, 1, 0))
    return d.cross(a).normalized()


def _euler(rot):
    return Euler(tuple(math.radians(a) for a in rot), 'XYZ').to_matrix().to_4x4()


class Frame:
    """Local axes of a wing or fin: u runs outward along the arm, v backwards, w is the wing normal.

    lift tilts the wing up (degrees), sweep turns the arm backwards, pitch rolls the wing about its arm so the
    surface faces forwards instead of up (a raised, open wing). sx is -1 for the left side, +1 for the right."""

    def __init__(self, origin, sx, lift=0.0, sweep=0.0, pitch=0.0):
        self.o = V(origin)
        self.sx = sx
        lf, sw, pt = math.radians(lift), math.radians(sweep), math.radians(pitch)
        u0, v0, w0 = V((sx, 0, 0)), V((0, 1, 0)), V((0, 0, 1))
        u = u0 * math.cos(lf) + w0 * math.sin(lf)
        w = -u0 * math.sin(lf) + w0 * math.cos(lf)
        self.u = u * math.cos(sw) + v0 * math.sin(sw)
        v = -u * math.sin(sw) + v0 * math.cos(sw)
        self.v = v * math.cos(pt) + w * math.sin(pt)
        self.w = -v * math.sin(pt) + w * math.cos(pt)

    def p(self, u=0.0, v=0.0, w=0.0):
        return self.o + self.u * u + self.v * v + self.w * w


class Pet:
    def __init__(self, key, palette, coll, scale=1.0):
        self.key, self.palette, self.coll, self.k = key, palette, coll, scale
        self.mats, self.acc, self.objs, self.rest = {}, {}, [], {}
        self.root = self._empty(key, (0, 0, 0), None, 0.12)
        self.rig = self._empty('Rig', (0, 0, 0), self.root)
        self.piv = {'Rig': (self.rig, V((0, 0, 0)))}
        self.rest['Rig'] = V((0, 0, 0))
        self.pivot('Body', (0, 0, 0))

    # ------------------------------------------------------------------ scene objects
    def _empty(self, name, loc, parent, size=0.04):
        o = bpy.data.objects.new(f'{self.key}|{name}', None)
        o['node'] = name
        o.empty_display_type = 'SPHERE'
        o.empty_display_size = size
        self.coll.objects.link(o)
        o.location = loc
        o.parent = parent
        self.objs.append(o)
        return o

    def pivot(self, name, loc, parent='Rig'):
        """A joint empty at loc (unscaled world coordinates). Children rotate with it; Rig moves everything."""
        pobj, pworld = self.piv[parent]
        loc = V(loc) * self.k
        o = self._empty(name, loc - pworld, pobj)
        self.piv[name] = (o, loc)
        self.rest[name] = loc - pworld
        return name

    def material(self, name):
        if name in self.mats:
            return self.mats[name]
        spec, opts = self.palette[name], {}
        if isinstance(spec, tuple):
            spec, opts = spec
        mat = bpy.data.materials.new(f'{self.key}|{name}')
        mat.use_nodes = True
        b = mat.node_tree.nodes['Principled BSDF']
        alpha = opts.get('alpha', 1.0)
        b.inputs['Base Color'].default_value = rgba(spec)
        b.inputs['Roughness'].default_value = opts.get('rough', 0.8)
        b.inputs['Metallic'].default_value = 0.0
        if 'emit' in opts:
            b.inputs['Emission Color'].default_value = rgba(opts['emit'])
            b.inputs['Emission Strength'].default_value = opts.get('es', 1.0)
        if alpha < 1.0:
            b.inputs['Alpha'].default_value = alpha
            mat.surface_render_method = 'BLENDED'
        self.mats[name] = mat
        return mat

    def _bm(self, p, m):
        if (p, m) not in self.acc:
            self.acc[(p, m)] = bmesh.new()
        return self.acc[(p, m)]

    # ------------------------------------------------------------------ primitives
    def sphere(self, p, m, c, r, s=(1, 1, 1), rot=(0, 0, 0), seg=10, rings=7, smooth=True):
        k = self.k
        mat = Matrix.Translation(V(c) * k) @ _euler(rot) @ Matrix.Diagonal((r * s[0] * k, r * s[1] * k, r * s[2] * k, 1.0))
        res = bmesh.ops.create_uvsphere(self._bm(p, m), u_segments=seg, v_segments=rings, radius=1.0, matrix=mat)
        for f in {f for v in res['verts'] for f in v.link_faces}:
            f.smooth = smooth

    def cone(self, p, m, a, b, r0, r1=None, seg=8, smooth=True, caps=True):
        """Tapered cylinder from a (radius r0) to b (radius r1, default r0)."""
        k = self.k
        a, b = V(a) * k, V(b) * k
        d = b - a
        if d.length < 1e-6:
            return
        r1 = r0 if r1 is None else r1
        mat = Matrix.Translation((a + b) / 2) @ V((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        res = bmesh.ops.create_cone(self._bm(p, m), cap_ends=caps, cap_tris=False, segments=seg,
                                    radius1=max(r0 * k, 1e-4), radius2=max(r1 * k, 1e-4), depth=d.length, matrix=mat)
        for f in {f for v in res['verts'] for f in v.link_faces}:
            f.smooth = smooth and len(f.verts) == 4

    def box(self, p, m, c, size, rot=(0, 0, 0)):
        k = self.k
        mat = Matrix.Translation(V(c) * k) @ _euler(rot) @ Matrix.Diagonal((size[0] * k, size[1] * k, size[2] * k, 1.0))
        bmesh.ops.create_cube(self._bm(p, m), size=1.0, matrix=mat)

    def tube(self, p, m, pts, r, seg=7, caps=True, smooth=True):
        """Pipe along a polyline; r is one radius or one per point."""
        k = self.k
        pts = [V(x) * k for x in pts]
        n = len(pts)
        rs = [x * k for x in (r if isinstance(r, (list, tuple)) else [r] * n)]
        bm = self._bm(p, m)
        rings, prev = [], None
        for i, c in enumerate(pts):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            nrm = _perp(t) if prev is None else prev - t * prev.dot(t)
            nrm = _perp(t) if nrm.length < 0.3 else nrm.normalized()
            prev = nrm
            bin_ = t.cross(nrm)
            rings.append([bm.verts.new(c + (nrm * math.cos(2 * math.pi * j / seg) + bin_ * math.sin(2 * math.pi * j / seg)) * max(rs[i], 1e-4))
                          for j in range(seg)])
        faces = []
        for i in range(n - 1):
            for j in range(seg):
                j2 = (j + 1) % seg
                faces.append(bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j])))
        for f in faces:
            f.smooth = smooth
        if caps:
            bm.faces.new(rings[0][::-1])
            bm.faces.new(rings[-1])

    def blade(self, p, m, a, b, w, t=0.025, face=(0, 0, 1), peak=0.4):
        """Flat leaf/feather/fin ray from a to b, widest at `peak` along its length; `face` is the broad side's normal."""
        k = self.k
        a, b = V(a) * k, V(b) * k
        d = b - a
        if d.length < 1e-6:
            return
        f = V(face)
        f = f - d.normalized() * f.dot(d.normalized())
        nrm = _perp(d.normalized()) if f.length < 1e-6 else f.normalized()
        side = nrm.cross(d).normalized()
        mid = a + d * peak
        w, t = w * k, t * k
        pts = [a, mid + side * w / 2, b, mid - side * w / 2]
        bm = self._bm(p, m)
        top = [bm.verts.new(q + nrm * t / 2) for q in pts]
        bot = [bm.verts.new(q - nrm * t / 2) for q in pts]
        faces = [bm.faces.new(top), bm.faces.new(bot[::-1])]
        for i in range(4):
            j = (i + 1) % 4
            faces.append(bm.faces.new((top[i], bot[i], bot[j], top[j])))
        bmesh.ops.recalc_face_normals(bm, faces=faces)

    def fan(self, p, m, hub, pts):
        """Flat membrane: triangles from hub to consecutive boundary points. Use a double-sided look (default)."""
        k = self.k
        bm = self._bm(p, m)
        h = bm.verts.new(V(hub) * k)
        vs = [bm.verts.new(V(q) * k) for q in pts]
        for i in range(len(vs) - 1):
            bm.faces.new((h, vs[i], vs[i + 1]))

    def torus(self, p, m, c, R, r, rot=(0, 0, 0), seg=18, minor=6):
        k = self.k
        mat = Matrix.Translation(V(c) * k) @ _euler(rot)
        bm = self._bm(p, m)
        grid = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring = []
            for j in range(minor):
                b = 2 * math.pi * j / minor
                rr = (R + r * math.cos(b)) * k
                ring.append(bm.verts.new(mat @ V((rr * math.cos(a), rr * math.sin(a), r * math.sin(b) * k))))
            grid.append(ring)
        faces = []
        for i in range(seg):
            for j in range(minor):
                i2, j2 = (i + 1) % seg, (j + 1) % minor
                faces.append(bm.faces.new((grid[i][j], grid[i2][j], grid[i2][j2], grid[i][j2])))
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        for f in faces:
            f.smooth = True

    # ------------------------------------------------------------------ composite parts
    def eye(self, p, hc, hr, sx, yaw=28, pitch=4, size=0.1, iris='Iris', white='Sclera', pupil='Pupil', shine='Shine'):
        """Big cute eye on a head sphere (centre hc, radius hr): white, iris, pupil and a highlight."""
        hc = V(hc)
        ya, pa = math.radians(yaw), math.radians(pitch)
        d = V((sx * math.sin(ya) * math.cos(pa), -math.cos(ya) * math.cos(pa), math.sin(pa)))
        rot = (-pitch, 0, sx * yaw)
        right = V((1, 0, 0)) - d * d.x
        right.normalize()
        up = d.cross(right).normalized()
        self.sphere(p, white, hc + d * hr * 0.9, size, (1, 0.45, 1.25), rot, 10, 7)
        self.sphere(p, iris, hc + d * hr * 0.97, size * 0.7, (1, 0.4, 1.3), rot, 10, 7)
        if pupil:
            self.sphere(p, pupil, hc + d * hr * 1.0, size * 0.4, (1, 0.35, 1.3), rot, 8, 6)
        if shine:
            self.sphere(p, shine, hc + d * hr * 1.02 + (right * 0.28 + up * 0.3) * size, size * 0.22, (1, 0.5, 1), rot, 6, 4)

    def feathers(self, p, frame, mats, n, arm, lens, widths, angles, thick=0.03, step=0.012, start=0.05, peak=0.45, w0=0.0):
        """Fan of blades along a wing arm. (lens, widths, angles) are (outer, inner) pairs; angles in degrees
        measured from the arm towards the back; mats is a material name or a list cycled through; each blade
        sits `step` above the previous one (from w0) so overlapping feathers never z-fight."""
        mats = [mats] if isinstance(mats, str) else mats
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0.0
            u = arm - (arm - start) * t
            th = math.radians(angles[0] + (angles[1] - angles[0]) * t)
            length = lens[0] + (lens[1] - lens[0]) * t
            width = widths[0] + (widths[1] - widths[0]) * t
            base = frame.p(u, 0, w0 + step * i)
            tip = base + (frame.u * math.cos(th) + frame.v * math.sin(th)) * length
            self.blade(p, mats[i % len(mats)], base, tip, width, thick, face=frame.w, peak=peak)

    def feather_points(self, frame, n, arm, lens, angles, start=0.05, frac=1.0, w0=0.0):
        """Points at `frac` along each feather of a feathers() fan (outer feather first): for membranes/underlays."""
        pts = []
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0.0
            u = arm - (arm - start) * t
            th = math.radians(angles[0] + (angles[1] - angles[0]) * t)
            length = (lens[0] + (lens[1] - lens[0]) * t) * frac
            pts.append(frame.p(u, 0, w0) + (frame.u * math.cos(th) + frame.v * math.sin(th)) * length)
        return pts

    def fluff_tail(self, p, m, tip_m, pts, radii, seg=8, rings=6, squash=1.0):
        """A fluffy tail: overlapping spheres along pts; the last third uses tip_m."""
        n = len(pts)
        for i, (c, r) in enumerate(zip(pts, radii)):
            self.sphere(p, tip_m if i >= n * 2 / 3 else m, c, r, (1, 1, squash), seg=seg, rings=rings)

    # ------------------------------------------------------------------ build + animate + export
    def finish(self):
        for (p, m), bm in self.acc.items():
            ob_p, world = self.piv[p]
            bmesh.ops.translate(bm, vec=-world, verts=bm.verts)
            me = bpy.data.meshes.new(f'{self.key}|{p}_{m}')
            bm.to_mesh(me)
            bm.free()
            me.materials.append(self.material(m))
            ob = bpy.data.objects.new(f'{self.key}|{p}_{m}', me)
            ob['node'] = f'{p}_{m}'
            self.coll.objects.link(ob)
            ob.parent = ob_p
            self.objs.append(ob)
        self.acc.clear()

    def animate(self, clip, keys):
        """keys = [(frame, {pivot: {'rot': (x, y, z) degrees, 'loc': (x, y, z), 'sc': s}})]; a pivot missing from
        a key sits at rest there. Each clip becomes an NLA track named `clip`, exported as one glTF animation."""
        names = sorted({q for _, st in keys for q in st if q in self.piv})  # a pose may name pivots this form lacks
        for q in names:
            ob, _ = self.piv[q]
            rest = self.rest[q]
            has_loc = any('loc' in st.get(q, {}) for _, st in keys)
            has_sc = any('sc' in st.get(q, {}) for _, st in keys)
            ob.animation_data_create()
            act = bpy.data.actions.new(f'{self.key}|{clip}|{q}')
            ob.animation_data.action = act
            for f, st in keys:
                s = st.get(q, {})
                ob.rotation_euler = tuple(math.radians(a) for a in s.get('rot', (0, 0, 0)))
                ob.location = rest + V(s.get('loc', (0, 0, 0))) * self.k
                sc = s.get('sc', 1.0)
                ob.scale = (sc, sc, sc) if isinstance(sc, (int, float)) else sc
                ob.keyframe_insert('rotation_euler', frame=f)
                if has_loc:
                    ob.keyframe_insert('location', frame=f)
                if has_sc:
                    ob.keyframe_insert('scale', frame=f)
            ob.rotation_euler = (0, 0, 0)
            ob.location = rest
            ob.scale = (1, 1, 1)
            track = ob.animation_data.nla_tracks.new()
            track.name = clip
            track.strips.new(clip, int(keys[0][0]), act)
            ob.animation_data.action = None

    def export(self, path):
        nodes = list(self.objs)
        for o in nodes:
            o.name = o['node']
        loc = self.root.location.copy()
        self.root.location = (0, 0, 0)
        bpy.context.view_layer.update()
        for o in bpy.context.view_layer.objects:  # select_all skips hidden objects, which would then be exported too
            try:
                o.select_set(False)
            except RuntimeError:
                pass
        for o in nodes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = self.root
        try:
            bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                                      export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False,
                                      export_texcoords=False, export_animations=True, export_animation_mode='NLA_TRACKS')
        finally:
            for o in nodes:
                o.name = f"{self.key}|{o['node']}"
            self.root.location = loc


def R(x=0, y=0, z=0, **kw):
    """Pose entry: rotation in degrees (plus loc=/sc= if given)."""
    d = {'rot': (x, y, z)}
    d.update(kw)
    return d


def wings(a, twist=0):
    """Both wings raised by a degrees (negative = lowered); twist pitches them forwards/backwards."""
    return {'WingL': R(twist, a, 0), 'WingR': R(twist, -a, 0)}


def idle(pet, amp=1.0):
    """Generic 2 s loop: breathing, a little head sway, wings/tails/ears fluttering. Species-specific pivots follow
    their name prefix (Wing, Tail, Ear, Fin, Leaf)."""
    a = amp
    keys = []
    swayers = [n for n in pet.piv if n.startswith(('Tail', 'Ear', 'Fin', 'Leaf'))]
    for f, ph in ((0, 0.0), (12, 1.0), (24, 0.0), (36, -1.0), (48, 0.0)):
        st = {}
        breathe = 0.5 - 0.5 * math.cos(math.pi * f / 24)  # 0 -> 1 -> 0 over the loop
        st['Body'] = {'sc': (1, 1, 1 + 0.025 * breathe * a)}
        st['Head'] = {'rot': (-3 * breathe * a, 0, 3 * ph * a), 'loc': (0, 0, 0.02 * breathe * a)} if 'Head' in pet.piv else {}
        if 'WingL' in pet.piv:
            fl = 6 * a * breathe
            st['WingL'] = {'rot': (0, fl, 0)}
            st['WingR'] = {'rot': (0, -fl, 0)}
        for i, n in enumerate(swayers):
            side = -1 if n.endswith('L') else 1
            st[n] = {'rot': (0, 0, 8 * a * math.sin(math.pi * f / 24 * 1.0 + i * 0.7) * (side if n.startswith(('Ear', 'Fin', 'Leaf')) else 1))}
        keys.append((f, {k2: v for k2, v in st.items() if v}))
    pet.animate('Idle', keys)
