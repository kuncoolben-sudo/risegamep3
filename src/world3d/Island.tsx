import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import type { LocationRow } from '../lib/types';
import { modelUrl } from './assets';
import { SCENERY_COUNT, WORLD_RADIUS, footprint, rng, toWorld } from './config';
import { DECOR, GRASS_RADIUS, OBSTACLES, SEA_LEVEL } from './terrainData';

// The island under the map, built by tools/blender/build_world.py: the ground and what stands on it, the sea round it,
// the sky, and the trees, flowers and rocks scattered over it. The ground is flat wherever the places and roads are.

/** Sky models drawn unlit and behind everything: the dome first, then the clouds and the sun. */
function skyCopy(scene: THREE.Object3D) {
  const sky = scene.clone();
  sky.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.material = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide, fog: false, depthWrite: false });
    m.renderOrder = m.name === 'SkyDome' ? -2 : -1;
    m.frustumCulled = false;
  });
  return sky;
}

/** The sky round the camera (it moves with it, so it is always the same distance away). */
export function Sky({ radius }: { radius: number }) {
  const { scene } = useGLTF(modelUrl('w_sky'));
  const camera = useThree((s) => s.camera);
  const group = useRef<THREE.Group>(null);
  const sky = useMemo(() => skyCopy(scene), [scene]);
  useFrame(() => { group.current?.position.copy(camera.position); });
  return <group ref={group} scale={radius}><primitive object={sky} /></group>;
}

/** The sky rendered once into a small cube map, for the water to reflect. */
function useSkyReflection() {
  const { scene } = useGLTF(modelUrl('w_sky'));
  const gl = useThree((s) => s.gl);
  const [tex, setTex] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    const target = new THREE.WebGLCubeRenderTarget(128);
    const env = new THREE.Scene();
    env.add(skyCopy(scene));
    new THREE.CubeCamera(0.05, 10, target).update(gl, env);
    setTex(target.texture);
    return () => target.dispose();
  }, [scene, gl]);
  return tex;
}

/** One water material for the sea, the lake and the river: clear enough to see the sandy shallows through. */
export function useWater() {
  const env = useSkyReflection();
  return useMemo(() => new THREE.MeshStandardMaterial({
    color: '#26b0e3', transparent: true, opacity: 0.62, roughness: 0.18, metalness: 0.3, envMap: env, envMapIntensity: 1.1, depthWrite: false,
  }), [env]);
}

export function Sea({ water }: { water: THREE.Material }) {
  return (
    <mesh rotation-x={-Math.PI / 2} position-y={SEA_LEVEL} material={water}>
      <circleGeometry args={[900, 96]} />
    </mesh>
  );
}

export function Terrain({ water, shadows }: { water: THREE.Material; shadows: boolean }) {
  const { scene } = useGLTF(modelUrl('w_terrain'));
  useLayoutEffect(() => {
    scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      m.receiveShadow = true;
      m.castShadow = shadows && m.name !== 'Ground'; // the ground only takes shadows (no self-shadow acne)
      if ((m.material as THREE.Material).name.endsWith('Water')) m.material = water;
    });
  }, [scene, water, shadows]);
  return <primitive object={scene} />;
}

/** Sky, sea and ground together; the sea, the lake and the river share one water material. */
export function IslandWorld({ shadows }: { shadows: boolean }) {
  const water = useWater();
  return (
    <>
      <Sky radius={600} />
      <Sea water={water} />
      <Terrain water={water} shadows={shadows} />
    </>
  );
}

/** Players walk round these, as they do round the places (mountains, hills, the lake, the beach pavilion). */
export const OBSTACLE_SPOTS = OBSTACLES.map(([x, z, r]) => ({ x, z, r }));

export type PropKind = 'tree' | 'bigtree' | 'autumn' | 'bloom' | 'palm' | 'pine' | 'bush' | 'grass' | 'flowers' | 'rock' | 'boulder';
const KINDS: PropKind[] = ['tree', 'bigtree', 'autumn', 'bloom', 'palm', 'pine', 'bush', 'grass', 'flowers', 'rock', 'boulder'];
const SIZE: Record<PropKind, [number, number]> = {
  tree: [0.8, 1.3], bigtree: [0.8, 1.1], autumn: [0.8, 1.2], bloom: [0.8, 1.2], palm: [0.85, 1.25], pine: [0.8, 1.3],
  bush: [0.8, 1.3], grass: [0.9, 1.5], flowers: [1.0, 1.6], rock: [0.7, 1.3], boulder: [0.55, 0.9],
};
// What grows where on the walkable ground: palms on the sand, more pines and autumn trees towards the mountains.
const MIX: Record<'sand' | 'north' | 'grass', [PropKind, number][]> = {
  sand: [['palm', 5], ['bush', 1.2], ['grass', 2], ['rock', 1]],
  north: [['pine', 4], ['autumn', 2], ['tree', 2.5], ['bigtree', 0.7], ['bush', 2], ['grass', 2], ['flowers', 1.2], ['rock', 0.8], ['boulder', 0.5]],
  grass: [['tree', 3.5], ['bigtree', 1], ['bloom', 1.5], ['autumn', 0.8], ['pine', 1.5], ['bush', 2.2], ['grass', 2.5], ['flowers', 2.5], ['rock', 1], ['boulder', 0.3]],
};

function pick(mix: [PropKind, number][], k: number): PropKind {
  let left = k * mix.reduce((t, [, w]) => t + w, 0);
  for (const [kind, w] of mix) if ((left -= w) < 0) return kind;
  return mix[mix.length - 1][0];
}

interface Scatter { x: number; y: number; z: number; s: number; ry: number }

// One InstancedMesh per mesh of the model: hundreds of props cost a handful of draw calls.
function Instanced({ model, items }: { model: THREE.Object3D; items: Scatter[] }) {
  const parts = useMemo(() => {
    model.updateWorldMatrix(true, true);
    const out: { geo: THREE.BufferGeometry; mat: THREE.Material; local: THREE.Matrix4 }[] = [];
    model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) out.push({ geo: m.geometry, mat: m.material as THREE.Material, local: m.matrixWorld.clone() });
    });
    return out;
  }, [model]);
  const refs = useRef<(THREE.InstancedMesh | null)[]>([]);
  useLayoutEffect(() => {
    const P = new THREE.Matrix4(), M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), pos = new THREE.Vector3(), sc = new THREE.Vector3();
    parts.forEach((part, pi) => {
      const im = refs.current[pi];
      if (!im) return;
      items.forEach((it, i) => {
        q.setFromEuler(e.set(0, it.ry, 0));
        P.compose(pos.set(it.x, it.y, it.z), q, sc.setScalar(it.s));
        im.setMatrixAt(i, M.multiplyMatrices(P, part.local));
      });
      im.instanceMatrix.needsUpdate = true;
    });
  }, [parts, items]);
  if (items.length === 0) return null;
  return <>{parts.map((p, i) => <instancedMesh key={i} ref={(el) => { refs.current[i] = el; }} args={[p.geo, p.mat, items.length]} castShadow receiveShadow frustumCulled={false} />)}</>;
}

/** Props scattered over the walkable ground (clear of places, roads and obstacles) plus those placed on the slopes. */
export function Scenery({ locations, paths }: { locations: LocationRow[]; paths: [string, string][] }) {
  const { scene } = useGLTF(modelUrl('w_props'));
  const groups = useMemo(() => {
    const r = rng(7);
    const pts = locations.map((l) => [...toWorld(l.x, l.y), Math.max(5.2, (footprint(l.id) ?? 0) + 2.0)] as const);
    const byId = new Map(locations.map((l) => [l.id, l]));
    const segs = paths.flatMap(([a, b]) => {
      const A = byId.get(a), B = byId.get(b);
      return A && B ? [[toWorld(A.x, A.y), toWorld(B.x, B.y)] as const] : [];
    });
    const segDist = (px: number, pz: number, [[ax, az], [bx, bz]]: readonly [readonly number[], readonly number[]]) => {
      const dx = bx - ax, dz = bz - az;
      const t = Math.max(0, Math.min(1, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz)));
      return Math.hypot(px - (ax + t * dx), pz - (az + t * dz));
    };
    const out = Object.fromEntries(KINDS.map((k) => [k, [] as Scatter[]])) as Record<PropKind, Scatter[]>;
    let n = 0, tries = 0;
    while (n < SCENERY_COUNT && tries++ < 8000) {
      const ang = r() * Math.PI * 2, rad = Math.sqrt(r()) * (WORLD_RADIUS - 1);
      const x = Math.cos(ang) * rad, z = Math.sin(ang) * rad;
      if (pts.some(([px, pz, clear]) => Math.hypot(px - x, pz - z) < clear)) continue;
      if (segs.some((s) => segDist(x, z, s) < 2.0)) continue;
      if (OBSTACLES.some(([ox, oz, or]) => Math.hypot(ox - x, oz - z) < or + 1.2)) continue;
      const kind = pick(MIX[rad > GRASS_RADIUS - 0.8 ? 'sand' : z < -13 ? 'north' : 'grass'], r());
      const [lo, hi] = SIZE[kind];
      out[kind].push({ x, y: 0, z, s: lo + r() * (hi - lo), ry: r() * 6.28 });
      n++;
    }
    for (const [kind, x, y, z, s, ry] of DECOR) out[kind as PropKind]?.push({ x, y, z, s, ry });
    return out;
  }, [locations, paths]);
  return <>{KINDS.map((k) => {
    const model = scene.getObjectByName(k);
    return model ? <Instanced key={k} model={model} items={groups[k]} /> : null;
  })}</>;
}
