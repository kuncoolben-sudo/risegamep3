// Power-release effects for the pets: a small data-driven engine on top of three.js (no React inside).
// An effect is a list of layers (particles, rings, beams, orbs...) that run on a clock measured in seconds
// from the start of the cast. Positions are in the pet's local space: +Y up, +Z forward, the pet's feet at 0.
import * as THREE from 'three';

export type Vec3 = [number, number, number];

export interface ParticlesSpec {
  kind: 'particles';
  from: number; to: number;
  rate?: number; burst?: number;            // per second while active / once at `from`
  life: [number, number];
  size: [number, number];                   // world units at birth and at death
  colors: [string, string];                 // birth -> death
  alpha?: number;
  origin: Vec3; spread?: number;            // random offset inside a sphere of this radius
  flat?: boolean;                           // spread over the ground disc instead of a sphere
  dir?: Vec3; cone?: number; speed?: [number, number];
  gravity?: number; drag?: number;
  orbit?: { r: [number, number]; w: [number, number]; vy: [number, number]; vr?: number };
  wave?: number;                            // sideways wobble for streams
  smoke?: boolean;                          // normal blending instead of additive
}
export interface RingSpec {
  kind: 'ring';
  from: number; to: number;
  origin: Vec3; r: [number, number]; width: number; color: string; opacity?: number;
  rot?: Vec3; spin?: number; count?: number; stagger?: number;
}
export interface DiscSpec {
  kind: 'disc';
  from: number; to: number;
  origin: Vec3; r: [number, number]; color: string; opacity?: number; rot?: Vec3; spin?: number;
}
export interface BeamSpec {
  kind: 'beam';
  from: number; to: number;
  a: Vec3; b: Vec3; r: [number, number]; color: string; opacity?: number;
}
export interface BoltSpec {
  kind: 'bolt';
  from: number; to: number;
  a: Vec3; b: Vec3; count: number; jitter: number; color: string;
}
export interface OrbSpec {
  kind: 'orb';
  from: number; to: number;
  path: Vec3[]; r: [number, number]; color: string; halo: string; pulse?: number;
}
export interface SlashSpec {
  kind: 'slash';
  from: number; to: number;
  origin: Vec3; r: number; arc: number; width: number; rot: Vec3; color: string;
}
export interface RootsSpec {
  kind: 'roots';
  from: number; to: number;
  origin: Vec3; count: number; reach: number; height: number; colors: [string, string];
}
export interface LeavesSpec {
  kind: 'leaves';
  from: number; to: number; launch?: number;
  origin: Vec3; count: number; r: [number, number]; colors: [string, string];
  dir?: Vec3; size?: number;
}
export interface GemSpec {
  kind: 'gem';
  from: number; to: number;
  origin: Vec3; r: number; color: string;
}
export interface WingsSpec {
  kind: 'wings';
  from: number; to: number;
  origin: Vec3; size: number; colors: [string, string];
}
export type LayerSpec = ParticlesSpec | RingSpec | DiscSpec | BeamSpec | BoltSpec | OrbSpec | SlashSpec | RootsSpec | LeavesSpec | GemSpec | WingsSpec;
export interface EffectSpec { duration: number; layers: LayerSpec[] }

interface Layer { obj: THREE.Object3D; update(t: number, dt: number, px: number): void; dispose(): void }

const rnd = (a: number, b: number) => a + Math.random() * (b - a);
const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const smooth = (x: number) => x * x * (3 - 2 * x);
const mix = (a: number, b: number, u: number) => a + (b - a) * u;
const vec = (a: Vec3) => new THREE.Vector3(a[0], a[1], a[2]);

/** 0..1 envelope for a [from, to] window: fades in over `fin` and out over `fout` (fractions of the window). */
function env(t: number, from: number, to: number, fin = 0.12, fout = 0.3): number {
  if (t < from || t > to) return 0;
  const u = (t - from) / (to - from);
  return smooth(clamp01(u / fin)) * smooth(clamp01((1 - u) / fout));
}

let glowTex: THREE.Texture | null = null;
function glowTexture(): THREE.Texture {
  if (glowTex) return glowTex;
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(255,255,255,1)');
  grad.addColorStop(0.35, 'rgba(255,255,255,0.55)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  glowTex = new THREE.CanvasTexture(c);
  return glowTex;
}

function additive(color: string, opacity: number, map?: THREE.Texture) {
  return new THREE.MeshBasicMaterial({
    color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, map: map ?? null,
  });
}

// ---------------------------------------------------------------- particles
const PVERT = `
attribute float aSize; attribute float aAlpha; attribute vec3 aColor;
varying vec3 vC; varying float vA; uniform float uH;
void main() {
  vC = aColor; vA = aAlpha;
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = aSize * projectionMatrix[1][1] * uH * 0.5 / max(0.0001, gl_Position.w);
}`;
const PFRAG = `
varying vec3 vC; varying float vA;
void main() {
  float r = length(gl_PointCoord - 0.5) * 2.0;
  float a = smoothstep(1.0, 0.0, r); a *= a;
  gl_FragColor = vec4(vC, a * vA);
  if (gl_FragColor.a < 0.003) discard;
}`;

function coneDir(dir: THREE.Vector3, half: number, out: THREE.Vector3) {
  const up = Math.abs(dir.y) < 0.99 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
  const a = new THREE.Vector3().crossVectors(dir, up).normalize();
  const b = new THREE.Vector3().crossVectors(dir, a);
  const phi = Math.random() * Math.PI * 2;
  const ct = 1 - Math.random() * (1 - Math.cos(half));
  const st = Math.sqrt(1 - ct * ct);
  return out.copy(dir).multiplyScalar(ct).addScaledVector(a, st * Math.cos(phi)).addScaledVector(b, st * Math.sin(phi));
}

function particleLayer(s: ParticlesSpec): Layer {
  const maxLife = s.life[1];
  const n = Math.min(900, Math.ceil((s.rate ?? 0) * maxLife * 1.1 + (s.burst ?? 0) + 8));
  const pos = new Float32Array(n * 3), col = new Float32Array(n * 3), size = new Float32Array(n), alpha = new Float32Array(n);
  const vel = new Float32Array(n * 3), age = new Float32Array(n).fill(-1), life = new Float32Array(n);
  const s0 = new Float32Array(n), s1 = new Float32Array(n), ph = new Float32Array(n);
  const th = new Float32Array(n), rad = new Float32Array(n), w = new Float32Array(n), vy = new Float32Array(n);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aColor', new THREE.BufferAttribute(col, 3));
  geo.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
  geo.setAttribute('aAlpha', new THREE.BufferAttribute(alpha, 1));
  const mat = new THREE.ShaderMaterial({
    vertexShader: PVERT, fragmentShader: PFRAG, uniforms: { uH: { value: 600 } }, transparent: true, depthWrite: false,
    blending: s.smoke ? THREE.NormalBlending : THREE.AdditiveBlending,
  });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  const c0 = new THREE.Color(s.colors[0]), c1 = new THREE.Color(s.colors[1]), tmp = new THREE.Color();
  const origin = vec(s.origin), dir = vec(s.dir ?? [0, 0, 1]).normalize(), d = new THREE.Vector3();
  let acc = 0, burstDone = false, cursor = 0, last = 0;

  const spawn = () => {
    // find a dead slot, scanning forward from the cursor
    for (let k = 0; k < n; k++) {
      const i = (cursor + k) % n;
      if (age[i] >= 0 && age[i] < life[i]) continue;
      cursor = (i + 1) % n;
      age[i] = 0; life[i] = rnd(s.life[0], s.life[1]);
      s0[i] = s.size[0] * rnd(0.8, 1.2); s1[i] = s.size[1] * rnd(0.8, 1.2); ph[i] = Math.random() * 6.28;
      const sp = s.spread ?? 0;
      let ox = origin.x, oy = origin.y, oz = origin.z;
      if (sp > 0) {
        const a = Math.random() * 6.28, r = sp * Math.sqrt(Math.random());
        if (s.flat) { ox += Math.cos(a) * r; oz += Math.sin(a) * r; }
        else { d.set(rnd(-1, 1), rnd(-1, 1), rnd(-1, 1)).normalize().multiplyScalar(r); ox += d.x; oy += d.y; oz += d.z; }
      }
      pos[i * 3] = ox; pos[i * 3 + 1] = oy; pos[i * 3 + 2] = oz;
      if (s.orbit) {
        th[i] = Math.random() * 6.28; rad[i] = rnd(s.orbit.r[0], s.orbit.r[1]); w[i] = rnd(s.orbit.w[0], s.orbit.w[1]); vy[i] = rnd(s.orbit.vy[0], s.orbit.vy[1]);
        pos[i * 3] = origin.x + Math.cos(th[i]) * rad[i]; pos[i * 3 + 2] = origin.z + Math.sin(th[i]) * rad[i]; pos[i * 3 + 1] = origin.y;
      } else {
        coneDir(dir, s.cone ?? 0.3, d).multiplyScalar(rnd((s.speed ?? [1, 2])[0], (s.speed ?? [1, 2])[1]));
        vel[i * 3] = d.x; vel[i * 3 + 1] = d.y; vel[i * 3 + 2] = d.z;
      }
      return;
    }
  };

  return {
    obj: pts,
    update(t, dt, px) {
      mat.uniforms.uH.value = px;
      if (t < last) { age.fill(-1); burstDone = false; acc = 0; } // the clock restarted
      last = t;
      const active = t >= s.from && t <= s.to;
      if (active && !burstDone && s.burst) { for (let k = 0; k < s.burst; k++) spawn(); burstDone = true; }
      if (active && s.rate) { acc += s.rate * dt; while (acc >= 1) { spawn(); acc -= 1; } }
      const peak = s.alpha ?? 1;
      for (let i = 0; i < n; i++) {
        if (age[i] < 0 || age[i] >= life[i]) { size[i] = 0; alpha[i] = 0; continue; }
        age[i] += dt;
        const u = clamp01(age[i] / life[i]);
        if (s.orbit) {
          th[i] += w[i] * dt; rad[i] += (s.orbit.vr ?? 0) * dt;
          pos[i * 3] = origin.x + Math.cos(th[i]) * rad[i]; pos[i * 3 + 2] = origin.z + Math.sin(th[i]) * rad[i]; pos[i * 3 + 1] = origin.y + vy[i] * age[i];
        } else {
          const drag = 1 - Math.min(1, (s.drag ?? 0) * dt);
          vel[i * 3] *= drag; vel[i * 3 + 1] = vel[i * 3 + 1] * drag + (s.gravity ?? 0) * dt; vel[i * 3 + 2] *= drag;
          pos[i * 3] += vel[i * 3] * dt + (s.wave ? Math.sin(age[i] * 14 + ph[i]) * s.wave * dt * 3 : 0);
          pos[i * 3 + 1] += vel[i * 3 + 1] * dt; pos[i * 3 + 2] += vel[i * 3 + 2] * dt;
        }
        size[i] = mix(s0[i], s1[i], u);
        alpha[i] = peak * smooth(clamp01(u / 0.12)) * (1 - u);
        tmp.copy(c0).lerp(c1, u);
        col[i * 3] = tmp.r; col[i * 3 + 1] = tmp.g; col[i * 3 + 2] = tmp.b;
      }
      geo.attributes.position.needsUpdate = true; geo.attributes.aColor.needsUpdate = true;
      geo.attributes.aSize.needsUpdate = true; geo.attributes.aAlpha.needsUpdate = true;
    },
    dispose() { geo.dispose(); mat.dispose(); },
  };
}

// ---------------------------------------------------------------- simple meshes
function ringLayer(s: RingSpec): Layer {
  const group = new THREE.Group();
  const count = s.count ?? 1;
  const rAvg = (s.r[0] + s.r[1]) / 2;
  const geo = new THREE.RingGeometry(Math.max(0.05, 1 - s.width / rAvg), 1, 64);
  const mats: THREE.MeshBasicMaterial[] = [];
  const holders: THREE.Group[] = [];
  for (let i = 0; i < count; i++) {
    const holder = new THREE.Group();
    holder.rotation.order = 'YXZ';
    const m = additive(s.color, 0);
    mats.push(m);
    holder.add(new THREE.Mesh(geo, m));
    group.add(holder);
    holders.push(holder);
  }
  group.position.set(...s.origin);
  return {
    obj: group,
    update(t) {
      for (let i = 0; i < count; i++) {
        const from = s.from + i * (s.stagger ?? 0), to = s.to + i * (s.stagger ?? 0);
        const e = env(t, from, to, 0.15, 0.55), u = clamp01((t - from) / (to - from));
        const h = holders[i];
        h.visible = e > 0.001;
        mats[i].opacity = e * (s.opacity ?? 0.8);
        const r = mix(s.r[0], s.r[1], smooth(u));
        h.scale.set(r, r, r);
        h.rotation.set(s.rot?.[0] ?? 0, (s.rot?.[1] ?? 0) + (s.spin ?? 0) * (t - from), s.rot?.[2] ?? 0);
      }
    },
    dispose() { geo.dispose(); mats.forEach((m) => m.dispose()); },
  };
}

function discLayer(s: DiscSpec): Layer {
  const geo = new THREE.CircleGeometry(1, 48);
  const m = additive(s.color, 0, glowTexture());
  const mesh = new THREE.Mesh(geo, m);
  mesh.rotation.order = 'YXZ';
  mesh.position.set(...s.origin);
  return {
    obj: mesh,
    update(t) {
      const e = env(t, s.from, s.to, 0.2, 0.4), u = clamp01((t - s.from) / (s.to - s.from));
      mesh.visible = e > 0.001;
      m.opacity = e * (s.opacity ?? 0.8);
      const r = mix(s.r[0], s.r[1], smooth(u));
      mesh.scale.set(r, r, r);
      mesh.rotation.set(s.rot?.[0] ?? 0, (s.rot?.[1] ?? 0) + (s.spin ?? 0) * (t - s.from), s.rot?.[2] ?? 0);
    },
    dispose() { geo.dispose(); m.dispose(); },
  };
}

function beamLayer(s: BeamSpec): Layer {
  const a = vec(s.a), b = vec(s.b);
  const len = a.distanceTo(b);
  const geo = new THREE.CylinderGeometry(s.r[1], s.r[0], 1, 20, 1, true);
  const m = additive(s.color, 0);
  const mesh = new THREE.Mesh(geo, m);
  mesh.position.copy(a).lerp(b, 0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
  mesh.scale.set(1, len, 1);
  return {
    obj: mesh,
    update(t) {
      const e = env(t, s.from, s.to, 0.15, 0.4);
      mesh.visible = e > 0.001;
      m.opacity = e * (s.opacity ?? 0.4) * (0.85 + 0.15 * Math.sin(t * 22));
    },
    dispose() { geo.dispose(); m.dispose(); },
  };
}

function boltLayer(s: BoltSpec): Layer {
  const group = new THREE.Group();
  const segs = 14;
  const lines: THREE.Line[] = [];
  const mat = new THREE.LineBasicMaterial({ color: s.color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
  for (let i = 0; i < s.count; i++) {
    const g = new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(new Float32Array((segs + 1) * 3), 3));
    const line = new THREE.Line(g, mat);
    line.frustumCulled = false;
    lines.push(line);
    group.add(line);
  }
  const a = vec(s.a), b = vec(s.b), axis = b.clone().sub(a), side = new THREE.Vector3(), up = new THREE.Vector3();
  side.crossVectors(axis, new THREE.Vector3(0, 1, 0)).normalize();
  up.crossVectors(side, axis).normalize();
  let next = 0;
  return {
    obj: group,
    update(t) {
      const e = env(t, s.from, s.to, 0.05, 0.25);
      group.visible = e > 0.001;
      mat.opacity = e;
      if (next - t > 0.06) next = 0; // the clock restarted
      if (t < next) return;
      next = t + 0.05; // re-roll the jagged paths ~20 times a second
      for (const line of lines) {
        const p = line.geometry.attributes.position as THREE.BufferAttribute;
        const fork = Math.random() * 0.5;
        for (let k = 0; k <= segs; k++) {
          const u = k / segs, taper = Math.sin(Math.PI * Math.min(1, u * 1.05)) * s.jitter;
          const o = a.clone().lerp(b, u).addScaledVector(side, rnd(-1, 1) * taper * (0.5 + fork)).addScaledVector(up, rnd(-1, 1) * taper * 0.6);
          p.setXYZ(k, o.x, o.y, o.z);
        }
        p.needsUpdate = true;
      }
    },
    dispose() { lines.forEach((l) => l.geometry.dispose()); mat.dispose(); },
  };
}

function orbLayer(s: OrbSpec): Layer {
  const group = new THREE.Group();
  const core = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), additive(s.color, 0));
  const haloMat = new THREE.SpriteMaterial({ map: glowTexture(), color: s.halo, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
  const halo = new THREE.Sprite(haloMat);
  group.add(core, halo);
  const pts = s.path.map(vec);
  return {
    obj: group,
    update(t) {
      const e = env(t, s.from, s.to, 0.1, 0.12), u = clamp01((t - s.from) / (s.to - s.from));
      group.visible = e > 0.001;
      const f = u * (pts.length - 1), i = Math.min(pts.length - 2, Math.floor(f));
      if (pts.length > 1) group.position.copy(pts[i]).lerp(pts[i + 1], smooth(f - i));
      else group.position.copy(pts[0]);
      const r = mix(s.r[0], s.r[1], u) * (1 + (s.pulse ?? 0.12) * Math.sin(t * 24));
      core.scale.setScalar(r);
      halo.scale.setScalar(r * 3.6);
      (core.material as THREE.MeshBasicMaterial).opacity = e * 0.8;
      haloMat.opacity = e * 0.7;
    },
    dispose() { core.geometry.dispose(); (core.material as THREE.Material).dispose(); haloMat.dispose(); },
  };
}

function slashLayer(s: SlashSpec): Layer {
  const seg = 36, pos: number[] = [], idx: number[] = [];
  for (let k = 0; k <= seg; k++) {
    const u = k / seg, ang = (u - 0.5) * s.arc, wd = s.width * Math.pow(Math.sin(Math.PI * u), 0.8);
    pos.push(Math.cos(ang) * (s.r + wd / 2), Math.sin(ang) * (s.r + wd / 2), 0, Math.cos(ang) * (s.r - wd / 2), Math.sin(ang) * (s.r - wd / 2), 0);
    if (k < seg) idx.push(k * 2, k * 2 + 1, k * 2 + 2, k * 2 + 1, k * 2 + 3, k * 2 + 2);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  const m = additive(s.color, 0);
  const mesh = new THREE.Mesh(geo, m);
  mesh.position.set(...s.origin);
  mesh.rotation.set(...s.rot);
  return {
    obj: mesh,
    update(t) {
      const u = clamp01((t - s.from) / (s.to - s.from));
      mesh.visible = t >= s.from && t <= s.to + 0.35;
      geo.setDrawRange(0, Math.floor(clamp01(u * 3) * seg) * 6);
      m.opacity = t <= s.to ? 1 : clamp01(1 - (t - s.to) / 0.35);
    },
    dispose() { geo.dispose(); m.dispose(); },
  };
}

function rootsLayer(s: RootsSpec): Layer {
  const group = new THREE.Group();
  const geo = new THREE.ConeGeometry(0.14, 1, 7);
  geo.translate(0, 0.5, 0);
  const items: { mesh: THREE.Mesh; ang: number; len: number; delay: number; tilt: number }[] = [];
  for (let i = 0; i < s.count; i++) {
    const m = new THREE.MeshLambertMaterial({ color: i % 2 ? s.colors[0] : s.colors[1] });
    const mesh = new THREE.Mesh(geo, m);
    const ang = (i / (s.count - 1) - 0.5) * 2.2, len = s.height * rnd(0.7, 1.15);
    mesh.position.set(s.origin[0] + Math.sin(ang) * s.reach * 0.5, s.origin[1], s.origin[2] + Math.cos(ang) * s.reach * rnd(0.5, 1));
    group.add(mesh);
    items.push({ mesh, ang, len, delay: Math.abs(ang) * 0.12 + rnd(0, 0.15), tilt: rnd(-0.5, 0.5) });
  }
  return {
    obj: group,
    update(t) {
      for (const it of items) {
        const u = clamp01((t - s.from - it.delay) / 0.35), fade = t > s.to ? clamp01(1 - (t - s.to) / 0.4) : 1;
        const g = (1 - Math.pow(1 - u, 3)) * fade;
        it.mesh.visible = g > 0.01;
        it.mesh.scale.set(1 + (1 - u) * 0.3, it.len * g, 1 + (1 - u) * 0.3);
        it.mesh.rotation.set(it.tilt + Math.sin(t * 6 + it.ang) * 0.08, 0, -it.ang * 0.3);
      }
    },
    dispose() { geo.dispose(); items.forEach((it) => (it.mesh.material as THREE.Material).dispose()); },
  };
}

function leavesLayer(s: LeavesSpec): Layer {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute([0, 0.5, 0, 0.5, 0, 0, 0, -0.5, 0, -0.5, 0, 0], 3));
  g.setIndex([0, 1, 2, 0, 2, 3]);
  const mat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, transparent: true, depthWrite: false });
  const mesh = new THREE.InstancedMesh(g, mat, s.count);
  mesh.frustumCulled = false;
  const c0 = new THREE.Color(s.colors[0]), c1 = new THREE.Color(s.colors[1]), dummy = new THREE.Object3D();
  const base = vec(s.dir ?? [0, 0, 1]).normalize();
  const data = Array.from({ length: s.count }, (_, i) => {
    mesh.setColorAt(i, i % 2 ? c0 : c1);
    return { th: (i / s.count) * 6.28 + rnd(0, 0.5), r: rnd(s.r[0], s.r[1]), h: rnd(0.2, 1.4), w: rnd(2.5, 4.5), spin: rnd(2, 6), off: new THREE.Vector3(rnd(-0.6, 0.6), rnd(-0.3, 0.5), rnd(0, 1)), sz: rnd(0.7, 1.3) };
  });
  const origin = vec(s.origin), launch = s.launch ?? (s.from + s.to) / 2;
  return {
    obj: mesh,
    update(t) {
      const e = env(t, s.from, s.to, 0.1, 0.25);
      mesh.visible = e > 0.001;
      mat.opacity = e;
      data.forEach((d, i) => {
        const a = d.th + d.w * (t - s.from);
        dummy.position.set(origin.x + Math.cos(a) * d.r, origin.y + d.h + 0.15 * Math.sin(a * 2), origin.z + Math.sin(a) * d.r);
        if (t > launch) {
          const k = t - launch;
          dummy.position.addScaledVector(base, k * (3 + d.off.z * 3)).add(new THREE.Vector3(d.off.x * k, d.off.y * k, 0));
        }
        dummy.rotation.set(t * d.spin, a, t * d.spin * 0.7);
        dummy.scale.setScalar((s.size ?? 0.22) * d.sz);
        dummy.updateMatrix();
        mesh.setMatrixAt(i, dummy.matrix);
      });
      mesh.instanceMatrix.needsUpdate = true;
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    },
    dispose() { g.dispose(); mat.dispose(); mesh.dispose(); },
  };
}

function gemLayer(s: GemSpec): Layer {
  const group = new THREE.Group();
  const geo = new THREE.OctahedronGeometry(1, 0);
  const m = additive(s.color, 0);
  const core = new THREE.Mesh(geo, m);
  const haloMat = new THREE.SpriteMaterial({ map: glowTexture(), color: s.color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
  const halo = new THREE.Sprite(haloMat);
  group.add(core, halo);
  group.position.set(...s.origin);
  return {
    obj: group,
    update(t) {
      const e = env(t, s.from, s.to, 0.2, 0.25), u = clamp01((t - s.from) / (s.to - s.from));
      group.visible = e > 0.001;
      const r = s.r * (0.5 + 0.5 * smooth(clamp01(u * 4))) * (1 + 0.08 * Math.sin(t * 9));
      core.scale.set(r * 0.7, r, r * 0.7);
      core.rotation.y = t * 2.4;
      halo.scale.setScalar(r * 5);
      group.position.y = s.origin[1] + Math.sin(t * 3) * 0.06;
      m.opacity = e * 0.9;
      haloMat.opacity = e * 0.7;
    },
    dispose() { geo.dispose(); m.dispose(); haloMat.dispose(); },
  };
}

function wingsLayer(s: WingsSpec): Layer {
  const group = new THREE.Group();
  const mats: THREE.MeshBasicMaterial[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const shapes: { sx: number; cu: number; cv: number; a: number; b: number; rot: number; col: string }[] = [];
  for (const sx of [-1, 1]) {
    shapes.push({ sx, cu: 0.95, cv: 0.55, a: 1.0, b: 0.7, rot: 0.45, col: s.colors[0] });
    shapes.push({ sx, cu: 0.65, cv: -0.35, a: 0.65, b: 0.42, rot: -0.35, col: s.colors[1] });
  }
  for (const sh of shapes) {
    const pts: THREE.Vector2[] = [];
    for (let i = 0; i < 28; i++) {
      const t = (i / 28) * Math.PI * 2, x = Math.cos(t) * sh.a, y = Math.sin(t) * sh.b;
      pts.push(new THREE.Vector2(sh.cu + x * Math.cos(sh.rot) - y * Math.sin(sh.rot), sh.cv + x * Math.sin(sh.rot) + y * Math.cos(sh.rot)));
    }
    const geo = new THREE.ShapeGeometry(new THREE.Shape(pts));
    geos.push(geo);
    const m = additive(sh.col, 0, glowTexture());
    mats.push(m);
    const mesh = new THREE.Mesh(geo, m);
    mesh.scale.x = sh.sx;
    group.add(mesh);
  }
  group.position.set(...s.origin);
  group.scale.setScalar(s.size);
  return {
    obj: group,
    update(t) {
      const e = env(t, s.from, s.to, 0.25, 0.3);
      group.visible = e > 0.001;
      mats.forEach((m) => { m.opacity = e * (0.55 + 0.2 * Math.sin(t * 6)); });
      group.scale.setScalar(s.size * (0.8 + 0.2 * smooth(clamp01((t - s.from) / 0.5))));
    },
    dispose() { geos.forEach((g) => g.dispose()); mats.forEach((m) => m.dispose()); },
  };
}

function makeLayer(s: LayerSpec): Layer {
  switch (s.kind) {
    case 'particles': return particleLayer(s);
    case 'ring': return ringLayer(s);
    case 'disc': return discLayer(s);
    case 'beam': return beamLayer(s);
    case 'bolt': return boltLayer(s);
    case 'orb': return orbLayer(s);
    case 'slash': return slashLayer(s);
    case 'roots': return rootsLayer(s);
    case 'leaves': return leavesLayer(s);
    case 'gem': return gemLayer(s);
    case 'wings': return wingsLayer(s);
  }
}

/** One running effect: add `group` to the scene, call update() every frame, dispose() when done with it. */
export class Effect {
  readonly group = new THREE.Group();
  private layers: Layer[];
  private t = -1; // -1 = idle
  readonly duration: number;

  constructor(spec: EffectSpec) {
    this.duration = spec.duration;
    this.layers = spec.layers.map(makeLayer);
    this.layers.forEach((l) => this.group.add(l.obj));
    this.group.visible = false;
  }

  play() { this.t = 0; this.group.visible = true; }
  stop() { this.t = -1; this.group.visible = false; }
  get playing() { return this.t >= 0; }

  update(dt: number, pixelHeight: number) {
    if (this.t < 0) return;
    this.t += dt;
    for (const l of this.layers) l.update(this.t, dt, pixelHeight);
    if (this.t > this.duration) this.stop();
  }

  dispose() { this.layers.forEach((l) => l.dispose()); }
}
