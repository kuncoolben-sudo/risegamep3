// One effect per pet form (see pets.ts). Times are seconds from the start of the Cast clip, whose release pose
// lands around 0.7 s. Everything is cosmetic: powers have no element rules, only a look.
import type { EffectSpec, LayerSpec, Vec3 } from './fx';
import { clampStage, petForm } from './pets';

const HALF_PI = Math.PI / 2;
const ground = (from: number, to: number, r1: number, color: string, o: { origin?: Vec3; count?: number; stagger?: number; r0?: number; w?: number } = {}): LayerSpec => ({
  kind: 'ring', from, to, origin: o.origin ?? [0, 0.03, 0], r: [o.r0 ?? 0.4, r1], width: o.w ?? 0.14, color, rot: [-HALF_PI, 0, 0], count: o.count ?? 1, stagger: o.stagger ?? 0,
});

type Ctx = { m: Vec3; top: Vec3; body: Vec3; k: number; D: number };

const recipes: Record<string, (c: Ctx) => LayerSpec[]> = {
  // ---- Skyra: lightning and wind
  'skyra-1': ({ m, k, D }) => [
    { kind: 'particles', from: 0.7, to: 1.9, rate: 240, life: [0.35, 0.6], size: [0.17 * k, 0.05 * k], colors: ['#ffffff', '#3da0ff'], origin: m, spread: 0.05, dir: [0, 0.03, 1], cone: 0.2, speed: [5.5, 8.5], drag: 0.2 },
    { kind: 'particles', from: 0.7, to: 1.9, rate: 70, life: [0.5, 0.9], size: [0.1 * k, 0.02], colors: ['#bfe9ff', '#2a6dff'], origin: m, spread: 0.1, dir: [0, 0, 1], cone: 0.7, speed: [2, 4] },
    { kind: 'bolt', from: 0.75, to: 1.9, a: m, b: [m[0], m[1] + 0.1, m[2] + D], count: 3, jitter: 0.3 * k, color: '#d6efff' },
  ],
  'skyra-2': ({ body, k }) => {
    const y = body[1] + 0.2 * k, out: LayerSpec[] = [];
    for (let s = 0; s < 2; s++) {
      for (let i = -1; i <= 1; i++) {
        out.push({ kind: 'slash', from: 0.75 + s * 0.9 + Math.abs(i) * 0.03, to: 0.95 + s * 0.9, origin: [i * 0.42 * k, y, 1.25 + k * 0.3], r: 0.95 * k, arc: 2.4, width: 0.26 * k, rot: [0.1, 0, (s ? 0.75 : -0.75) + i * 0.05], color: i ? '#8fd0ff' : '#ffffff' });
      }
      out.push({ kind: 'particles', from: 0.85 + s * 0.9, to: 0.9 + s * 0.9, burst: 70, life: [0.3, 0.7], size: [0.14 * k, 0.03], colors: ['#ffffff', '#3d9bff'], origin: [0, y, 1.4 + k * 0.3], spread: 0.6, dir: [0, 0, 1], cone: Math.PI, speed: [1.5, 5] });
    }
    return out;
  },
  'skyra-3': ({ body, k }) => [
    ground(0.75, 1.7, 3.2 * k, '#bfe6ff', { count: 3, stagger: 0.3, w: 0.16 * k }),
    { kind: 'particles', from: 0.8, to: 0.85, burst: 150, life: [0.8, 1.4], size: [0.2 * k, 0.05], colors: ['#ffffff', '#6ec4ff'], origin: [0, body[1] + 0.3 * k, 0], spread: 0.3, dir: [0, 0.2, 1], cone: Math.PI, speed: [2.5, 5], gravity: -0.8 },
    { kind: 'particles', from: 0.8, to: 2.2, rate: 90, life: [0.8, 1.4], size: [0.35 * k, 0.1], colors: ['#e8f6ff', '#8ccaff'], alpha: 0.6, origin: [0, 0.1, 0], orbit: { r: [0.6 * k, 2 * k], w: [2, 4], vy: [0.5, 1.6] } },
  ],
  // ---- Blazion: fire
  'blazion-1': ({ m, k }) => [
    { kind: 'particles', from: 0.7, to: 2.0, rate: 380, life: [0.4, 0.75], size: [0.3 * k, 0.12 * k], colors: ['#fff3a0', '#ff3b00'], origin: m, spread: 0.04, dir: [0, 0.05, 1], cone: 0.17, speed: [4.5, 7.5], gravity: 0.8, drag: 0.1 },
    { kind: 'particles', from: 0.9, to: 2.2, rate: 40, life: [0.7, 1.1], size: [0.35 * k, 0.8 * k], colors: ['#ff7a1a', '#2a1d1d'], alpha: 0.5, smoke: true, origin: [m[0], m[1], m[2] + 0.8], dir: [0, 0.2, 1], cone: 0.5, speed: [2.5, 4.5], gravity: 1 },
    { kind: 'orb', from: 0.6, to: 2.0, path: [m, m], r: [0.12 * k, 0.22 * k], color: '#ffd24a', halo: '#ff7a1a' },
  ],
  'blazion-2': ({ m, k, D }) => {
    const hit: Vec3 = [0, m[1] * 0.45, D];
    return [
      { kind: 'orb', from: 0.55, to: 1.45, path: [m, [m[0], m[1] + 0.1, m[2] + 0.5], hit], r: [0.08 * k, 0.32 * k], color: '#ffb12a', halo: '#ff6a1a' },
      { kind: 'particles', from: 0.95, to: 1.4, rate: 220, life: [0.25, 0.4], size: [0.3 * k, 0.1], colors: ['#fff0a0', '#ff4a00'], origin: [m[0], m[1] + 0.1, m[2] + 0.5], dir: [0, -0.1, 1], cone: 0.12, speed: [5, 7] },
      { kind: 'particles', from: 1.45, to: 1.5, burst: 280, life: [0.5, 1.0], size: [0.38 * k, 0.1], colors: ['#fff0a0', '#ff3000'], origin: hit, spread: 0.2, cone: Math.PI, speed: [1.5, 6], gravity: 0.5 },
      { kind: 'particles', from: 1.45, to: 1.5, burst: 60, life: [0.8, 1.4], size: [0.5 * k, 1.1 * k], colors: ['#ff8a2a', '#2a1d1d'], alpha: 0.5, smoke: true, origin: hit, spread: 0.3, cone: Math.PI, speed: [0.8, 2.5], gravity: 1 },
      ground(1.45, 2.3, 2.8 * k, '#ff8a2a', { origin: [0, 0.03, D], w: 0.2 * k, r0: 0.3 }),
      { kind: 'disc', from: 1.45, to: 1.95, origin: hit, r: [0.4, 2.2 * k], color: '#ffdd88', opacity: 0.9 },
    ];
  },
  'blazion-3': ({ body, k }) => {
    const y = body[1] + 0.1;
    return [
      { kind: 'ring', from: 0.7, to: 2.5, origin: [0, y, 0], r: [1.7 * k, 1.8 * k], width: 0.2 * k, color: '#ff8a2a', rot: [0, 0, 0], spin: 7 },
      { kind: 'ring', from: 0.7, to: 2.5, origin: [0, y, 0], r: [1.7 * k, 1.8 * k], width: 0.2 * k, color: '#ffd24a', rot: [0, HALF_PI, 0], spin: 7 },
      { kind: 'particles', from: 0.7, to: 2.5, rate: 320, life: [0.5, 0.9], size: [0.3 * k, 0.1], colors: ['#fff0a0', '#ff3b00'], origin: [0, y, 0], orbit: { r: [1.55 * k, 1.9 * k], w: [5, 7], vy: [-0.1, 0.5] } },
      ground(0.7, 1.7, 3 * k, '#ff8a2a', { count: 2, stagger: 0.4 }),
    ];
  },
  // ---- Kirin: forest
  'kirin-1': ({ k }) => [
    { kind: 'roots', from: 0.75, to: 2.2, origin: [0, 0, 1.3], count: 7, reach: 1.2 * k, height: 1.1 * k, colors: ['#2f7a3a', '#6a4a2a'] },
    { kind: 'particles', from: 0.75, to: 2.2, rate: 90, life: [0.8, 1.3], size: [0.14 * k, 0.04], colors: ['#c8ff8a', '#3fd06a'], origin: [0, 0.05, 1.3], spread: 1.1, flat: true, dir: [0, 1, 0], cone: 0.3, speed: [0.6, 1.4] },
    ground(0.75, 1.5, 1.8 * k, '#7dff9a', { origin: [0, 0.03, 1.3], count: 2, stagger: 0.35 }),
  ],
  'kirin-2': ({ body, k }) => [
    { kind: 'leaves', from: 0.6, to: 2.4, launch: 1.3, origin: [0, body[1] * 0.4, 0], count: 36, r: [0.9 * k, 1.3 * k], colors: ['#59d46a', '#9a4fd6'], dir: [0, 0.1, 1], size: 0.24 * k },
    { kind: 'particles', from: 1.3, to: 2.4, rate: 120, life: [0.5, 0.9], size: [0.2 * k, 0.05], colors: ['#b6ff6a', '#6a2aa0'], origin: [0, body[1], 0.6], dir: [0, 0, 1], cone: 0.5, speed: [2, 4] },
    ground(0.7, 1.5, 2.4 * k, '#8a5ad6', { count: 2, stagger: 0.35 }),
  ],
  'kirin-3': ({ k }) => [
    { kind: 'particles', from: 0.7, to: 2.4, rate: 340, life: [0.8, 1.2], size: [0.28 * k, 0.08], colors: ['#d6ffb0', '#2fbf5a'], alpha: 0.8, origin: [0, 0.05, 0], orbit: { r: [0.5 * k, 1.2 * k], w: [4.5, 7.5], vy: [1.8, 3.6], vr: 0.35 } },
    { kind: 'leaves', from: 0.7, to: 2.4, launch: 99, origin: [0, 0.2, 0], count: 30, r: [0.8 * k, 1.6 * k], colors: ['#52c76d', '#b8e04a'], size: 0.26 * k },
    { kind: 'beam', from: 0.7, to: 2.4, a: [0, 3.6 * k, 0], b: [0, 0, 0], r: [0.5 * k, 1.3 * k], color: '#5dff8a', opacity: 0.22 },
    ground(0.7, 1.8, 3 * k, '#7dff9a', { count: 2, stagger: 0.4 }),
  ],
  // ---- Lunara: moonlight
  'lunara-1': ({ top, k }) => [
    { kind: 'beam', from: 0.7, to: 2.3, a: [0, 3.4 * k, 0], b: [0, 0, 0], r: [0.3, 1.1 * k], color: '#d8c8ff', opacity: 0.35 },
    { kind: 'particles', from: 0.7, to: 2.5, rate: 120, life: [0.8, 1.4], size: [0.12 * k, 0.03], colors: ['#ffffff', '#c8a8ff'], origin: [0, 0.05, 0], orbit: { r: [0.2, 1.0 * k], w: [1.5, 3], vy: [0.5, 1.2] } },
    { kind: 'orb', from: 0.6, to: 2.6, path: [[0, top[1] + 0.55 * k, 0]], r: [0.16 * k, 0.26 * k], color: '#fff2b0', halo: '#ffd86a', pulse: 0.05 },
    { kind: 'disc', from: 0.7, to: 2.4, origin: [0, 0.04, 0], r: [0.4, 1.6 * k], color: '#cdb8ff', opacity: 0.7, rot: [-HALF_PI, 0, 0] },
  ],
  'lunara-2': ({ body, k }) => [
    { kind: 'ring', from: 0.7, to: 2.2, origin: body, r: [0.6 * k, 1.5 * k], width: 0.07 * k, color: '#e0b0ff', rot: [1.1, 0, 0.3], spin: 2.5, opacity: 0.9 },
    { kind: 'ring', from: 0.8, to: 2.2, origin: body, r: [0.6 * k, 1.5 * k], width: 0.07 * k, color: '#ffb0e0', rot: [0.2, 0, -0.8], spin: -3.2, opacity: 0.9 },
    { kind: 'ring', from: 0.9, to: 2.2, origin: body, r: [0.6 * k, 1.5 * k], width: 0.07 * k, color: '#b0c8ff', rot: [-0.7, 0, 1.2], spin: 4, opacity: 0.9 },
    { kind: 'particles', from: 0.7, to: 2.3, rate: 160, life: [0.6, 1.0], size: [0.14 * k, 0.04], colors: ['#ffffff', '#d080ff'], origin: body, orbit: { r: [1.2 * k, 1.6 * k], w: [4, 6], vy: [-0.2, 0.2] } },
    ground(0.7, 1.6, 2.4 * k, '#ffb0e0', { count: 2, stagger: 0.3 }),
  ],
  'lunara-3': ({ body, top, k }) => [
    { kind: 'wings', from: 0.7, to: 2.5, origin: [0, body[1] + 0.35, -0.15], size: 1.0 * k, colors: ['#d9c8ff', '#9cc4ff'] },
    { kind: 'particles', from: 0.8, to: 2.4, rate: 110, life: [1.0, 1.6], size: [0.14 * k, 0.04], colors: ['#fff6c8', '#b79cff'], origin: [0, top[1] + 1.4, 0], spread: 1.8, flat: true, dir: [0, -1, 0], cone: 0.25, speed: [0.8, 1.8] },
    { kind: 'disc', from: 0.7, to: 2.4, origin: [0, 0.04, 0], r: [0.4, 2.2 * k], color: '#cdb8ff', opacity: 0.6, rot: [-HALF_PI, 0, 0] },
    ground(0.8, 1.8, 3 * k, '#d9c8ff', { count: 2, stagger: 0.4 }),
  ],
  // ---- Aquaria: water
  'aquaria-1': ({ k }) => [
    { kind: 'particles', from: 0.7, to: 2.3, rate: 300, life: [0.7, 1.1], size: [0.24 * k, 0.07], colors: ['#e8ffff', '#2aa8ff'], origin: [0, 0.1, 0], orbit: { r: [0.5 * k, 1.6 * k], w: [5, 8], vy: [0.3, 1.4], vr: 0.15 } },
    ground(0.7, 1.7, 2.6 * k, '#6fdcff', { count: 3, stagger: 0.3, w: 0.16 * k }),
    { kind: 'particles', from: 0.8, to: 0.85, burst: 60, life: [0.6, 1.0], size: [0.12 * k, 0.05], colors: ['#ffffff', '#5acbff'], origin: [0, 0.2, 0], spread: 0.6, dir: [0, 1, 0], cone: 0.8, speed: [2, 4], gravity: -4 },
  ],
  'aquaria-2': ({ m, k, D }) => [
    { kind: 'particles', from: 0.7, to: 2.0, rate: 320, life: [0.5, 0.8], size: [0.26 * k, 0.1 * k], colors: ['#f0ffff', '#2f9aff'], origin: m, spread: 0.04, dir: [0, 0.06, 1], cone: 0.12, speed: [4, 6.5], wave: 0.35 },
    { kind: 'particles', from: 0.7, to: 2.0, rate: 120, life: [0.5, 0.9], size: [0.1 * k, 0.03], colors: ['#ffffff', '#7fe3ff'], origin: m, spread: 0.08, dir: [0, 0.1, 1], cone: 0.35, speed: [3, 5.5], wave: 0.5 },
    { kind: 'beam', from: 0.75, to: 1.9, a: m, b: [m[0], m[1] + 0.1, m[2] + D], r: [0.05, 0.18 * k], color: '#6fdcff', opacity: 0.25 },
    ground(0.9, 1.8, 2 * k, '#6fdcff', { origin: [0, 0.03, D * 0.7], count: 2, stagger: 0.3 }),
  ],
  'aquaria-3': ({ top, k }) => {
    const o: Vec3 = [0, top[1] + 0.8, 0];
    return [
      { kind: 'gem', from: 0.6, to: 2.6, origin: o, r: 0.26 * k, color: '#7fe8ff' },
      { kind: 'particles', from: 1.0, to: 1.05, burst: 120, life: [0.7, 1.2], size: [0.16 * k, 0.05], colors: ['#ffffff', '#38b8ff'], origin: o, spread: 0.1, cone: Math.PI, speed: [1.5, 4], gravity: -0.3 },
      { kind: 'particles', from: 0.8, to: 2.4, rate: 70, life: [1.2, 1.8], size: [0.16 * k, 0.2 * k], colors: ['#d8f8ff', '#7fe0ff'], alpha: 0.5, origin: [0, 0.1, 0], spread: 1.4, flat: true, dir: [0, 1, 0], cone: 0.3, speed: [0.6, 1.4] },
      ground(0.8, 1.9, 3 * k, '#6fdcff', { count: 2, stagger: 0.4 }),
    ];
  },
  // ---- Kitsune: foxfire and knowledge
  'kitsune-1': ({ m, k, D }) => {
    const hit: Vec3 = [0, m[1] + 0.2, D];
    return [
      { kind: 'orb', from: 0.6, to: 1.7, path: [[0.2, m[1] - 0.1, 0.5], [0.2, m[1], 0.7], hit], r: [0.08 * k, 0.24 * k], color: '#ff86e0', halo: '#c05cff' },
      { kind: 'particles', from: 1.1, to: 1.7, rate: 220, life: [0.3, 0.5], size: [0.22 * k, 0.05], colors: ['#ffd0f5', '#9a3cff'], origin: [0, m[1] + 0.1, 0.8], dir: [0, 0, 1], cone: 0.12, speed: [3.5, 5.5] },
      { kind: 'particles', from: 1.7, to: 1.75, burst: 140, life: [0.5, 0.9], size: [0.22 * k, 0.05], colors: ['#fff0ff', '#b050ff'], origin: hit, spread: 0.15, cone: Math.PI, speed: [1, 4] },
      ground(1.7, 2.4, 2 * k, '#d870ff', { origin: [0, 0.03, D], r0: 0.3 }),
    ];
  },
  'kitsune-2': ({ k }) => [
    { kind: 'particles', from: 0.7, to: 2.3, rate: 55, life: [1.0, 1.6], size: [0.8 * k, 1.9 * k], colors: ['#ffd2f0', '#b890ff'], alpha: 0.3, origin: [0, 0.3, 0.4], spread: 1.0, flat: true, dir: [0, 0.2, 1], cone: HALF_PI, speed: [0.5, 1.4] },
    { kind: 'particles', from: 0.7, to: 2.3, rate: 100, life: [0.8, 1.4], size: [0.1 * k, 0.03], colors: ['#ffffff', '#ffb0ff'], origin: [0, 0.4, 0.4], spread: 1.6, flat: true, dir: [0, 1, 0], cone: 0.6, speed: [0.3, 1] },
    ground(0.7, 1.7, 3 * k, '#e8a8ff', { count: 2, stagger: 0.4 }),
  ],
  'kitsune-3': ({ k }) => {
    const py = 1.1 * k + 0.3;
    return [
      { kind: 'ring', from: 0.7, to: 2.5, origin: [0, py, 2.0], r: [1.0 * k, 1.05 * k], width: 0.13 * k, color: '#e06bff', rot: [0, 0, 0], opacity: 0.95 },
      { kind: 'disc', from: 0.7, to: 2.5, origin: [0, py, 2.0], r: [0.2, 0.95 * k], color: '#b060ff', opacity: 0.6 },
      { kind: 'beam', from: 0.8, to: 2.4, a: [0, py, 2.0], b: [0, py * 0.6, 0.2], r: [0.9 * k, 0.3 * k], color: '#d890ff', opacity: 0.18 },
      { kind: 'particles', from: 0.9, to: 2.5, rate: 130, life: [0.8, 1.3], size: [0.16 * k, 0.05], colors: ['#ffffff', '#ff9ed0'], origin: [0, py, 2.0], spread: 0.5, dir: [0, -0.05, -1], cone: 0.3, speed: [1.2, 2.6] },
      ground(0.8, 1.8, 3 * k, '#e06bff', { count: 2, stagger: 0.4 }),
    ];
  },
};

/** The effect of the power of form `powerForm`, played by a body of form `bodyStage` (an evolved pet also casts its earlier powers). */
export function effectFor(species: string, powerForm: number, bodyStage: number = powerForm): EffectSpec | null {
  const build = recipes[`${species}-${clampStage(powerForm)}`];
  if (!build) return null;
  const f = petForm(species, bodyStage);
  return { duration: 3.2, layers: build({ m: f.anchors.mouth, top: f.anchors.top, body: f.anchors.body, k: f.k, D: 2.4 + 0.5 * (clampStage(powerForm) - 1) }) };
}
