import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import { Clone, Html, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { useGame } from '../state/GameContext';
import { useTravel } from '../state/useTravel';
import { LocationPanel } from '../components/LocationPanel';
import type { LocationRow, LocationStatus } from '../lib/types';
import { modelUrl } from './assets';
import { Character3D, Pet3D, type Limbs } from './Character3D';
import { COLLIDE_RADIUS, LOCATION_MODEL, NEAR_RADIUS, WORLD_RADIUS, rng, toWorld } from './config';

interface Input { x: number; z: number }

function Building({ loc, status, active }: { loc: LocationRow; status: LocationStatus; active: boolean }) {
  const def = LOCATION_MODEL[loc.id] ?? { file: 'b_cottage' };
  const { scene } = useGLTF(modelUrl(def.file));
  const [x, z] = toWorld(loc.x, loc.y);
  const locked = status === 'locked';
  return (
    <group position={[x, 0, z]}>
      <group scale={def.scale ?? 1}><Clone object={scene} castShadow receiveShadow /></group>
      {locked && (
        <mesh position={[0, 1.6, 0]}>
          <sphereGeometry args={[3, 20, 14]} />
          <meshStandardMaterial color="#cfd6e2" transparent opacity={0.55} depthWrite={false} />
        </mesh>
      )}
      {(status === 'open' || active) && !locked && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, 0]}>
          <ringGeometry args={[3.6, 4.0, 40]} />
          <meshBasicMaterial color={active ? '#ffcf40' : '#ffffff'} transparent opacity={active ? 0.95 : 0.55} />
        </mesh>
      )}
      <Html center position={[0, 4.6, 0]} distanceFactor={16} zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div className={`label3d ${status}`}>{locked ? '🔒 ' : status === 'cleared' ? '✅ ' : ''}{loc.name_en}</div>
      </Html>
    </group>
  );
}

function Road({ a, b, open }: { a: LocationRow; b: LocationRow; open: boolean }) {
  const [ax, az] = toWorld(a.x, a.y);
  const [bx, bz] = toWorld(b.x, b.y);
  const len = Math.hypot(bx - ax, bz - az);
  const ang = Math.atan2(bx - ax, bz - az);
  return (
    <mesh position={[(ax + bx) / 2, 0.03, (az + bz) / 2]} rotation={[-Math.PI / 2, 0, ang - Math.PI]} receiveShadow>
      <planeGeometry args={[open ? 1.5 : 1.0, len]} />
      <meshStandardMaterial color={open ? '#e8cf94' : '#bccba3'} />
    </mesh>
  );
}

function Scenery({ locations, paths }: { locations: LocationRow[]; paths: [string, string][] }) {
  const tree = useGLTF(modelUrl('p_tree')).scene;
  const pine = useGLTF(modelUrl('p_pine')).scene;
  const rock = useGLTF(modelUrl('p_rock')).scene;
  const flower = useGLTF(modelUrl('p_flower')).scene;
  const items = useMemo(() => {
    const r = rng(7);
    const pts = locations.map((l) => toWorld(l.x, l.y));
    const byId = new Map(locations.map((l) => [l.id, l]));
    const segs = paths.map(([a, b]) => [toWorld(byId.get(a)!.x, byId.get(a)!.y), toWorld(byId.get(b)!.x, byId.get(b)!.y)] as const);
    const segDist = (px: number, pz: number, [[ax, az], [bx, bz]]: readonly [readonly number[], readonly number[]]) => {
      const dx = bx - ax, dz = bz - az;
      const t = Math.max(0, Math.min(1, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz)));
      return Math.hypot(px - (ax + t * dx), pz - (az + t * dz));
    };
    const out: { kind: 'tree' | 'pine' | 'rock' | 'flower'; x: number; z: number; s: number; ry: number }[] = [];
    let tries = 0;
    while (out.length < 90 && tries++ < 2000) {
      const ang = r() * Math.PI * 2, rad = Math.sqrt(r()) * (WORLD_RADIUS - 1);
      const x = Math.cos(ang) * rad, z = Math.sin(ang) * rad;
      if (pts.some(([px, pz]) => Math.hypot(px - x, pz - z) < 5.2)) continue;
      if (segs.some((s) => segDist(x, z, s) < 2.0)) continue;
      const k = r();
      out.push({ kind: k < 0.4 ? 'tree' : k < 0.65 ? 'pine' : k < 0.8 ? 'rock' : 'flower', x, z, s: 0.8 + r() * 0.6, ry: r() * 6.28 });
    }
    return out;
  }, [locations, paths]);
  const src = { tree, pine, rock, flower };
  return <>{items.map((it, i) => <group key={i} position={[it.x, 0, it.z]} rotation={[0, it.ry, 0]} scale={it.kind === 'flower' ? it.s * 1.4 : it.s}><Clone object={src[it.kind]} castShadow /></group>)}</>;
}

function Player({ start, input, target, locations, onNear }: {
  start: [number, number];
  input: React.MutableRefObject<Input>;
  target: React.MutableRefObject<THREE.Vector3 | null>;
  locations: LocationRow[];
  onNear: (id: string | null) => void;
}) {
  const { character, pet, species } = useGame();
  const group = useRef<THREE.Group>(null);
  const petRef = useRef<THREE.Group>(null);
  const limbs = useRef<Limbs>({});
  const keys = useRef(new Set<string>());
  const lastNear = useRef<string | null>(null);
  const yaw = useRef(0);
  const { camera } = useThree();
  const spots = useMemo(() => locations.map((l) => {
    const [x, z] = toWorld(l.x, l.y);
    return { id: l.id, x, z, r: COLLIDE_RADIUS[LOCATION_MODEL[l.id]?.file] ?? COLLIDE_RADIUS[l.id] ?? 2.6 };
  }), [locations]);

  useEffect(() => {
    const typing = () => ['INPUT', 'TEXTAREA'].includes((document.activeElement?.tagName ?? ''));
    const down = (e: KeyboardEvent) => { if (!typing()) { keys.current.add(e.key.toLowerCase()); target.current = null; } };
    const up = (e: KeyboardEvent) => keys.current.delete(e.key.toLowerCase());
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); };
  }, [target]);

  useEffect(() => { group.current?.position.set(start[0], 0, start[1]); camera.position.set(start[0], 16, start[1] + 14); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useFrame((state, dt) => {
    const g = group.current;
    if (!g || !character) return;
    const k = keys.current;
    let dx = (k.has('d') || k.has('arrowright') ? 1 : 0) - (k.has('a') || k.has('arrowleft') ? 1 : 0) + input.current.x;
    let dz = (k.has('s') || k.has('arrowdown') ? 1 : 0) - (k.has('w') || k.has('arrowup') ? 1 : 0) + input.current.z;
    if (dx === 0 && dz === 0 && target.current) {
      const tx = target.current.x - g.position.x, tz = target.current.z - g.position.z;
      const d = Math.hypot(tx, tz);
      if (d < 0.25) target.current = null;
      else { dx = tx / d; dz = tz / d; }
    }
    const mag = Math.min(1, Math.hypot(dx, dz));
    const moving = mag > 0.05;
    if (moving) {
      const n = Math.hypot(dx, dz);
      g.position.x += (dx / n) * 5.5 * mag * dt;
      g.position.z += (dz / n) * 5.5 * mag * dt;
      const want = Math.atan2(dx, dz);
      let diff = want - yaw.current;
      diff = Math.atan2(Math.sin(diff), Math.cos(diff));
      yaw.current += diff * Math.min(1, dt * 12);
    }
    // keep on the island and out of buildings
    const rad = Math.hypot(g.position.x, g.position.z);
    if (rad > WORLD_RADIUS) { g.position.x *= WORLD_RADIUS / rad; g.position.z *= WORLD_RADIUS / rad; }
    let near: string | null = null, best = NEAR_RADIUS;
    for (const s of spots) {
      const ex = g.position.x - s.x, ez = g.position.z - s.z;
      const d = Math.hypot(ex, ez);
      if (d < s.r) { g.position.x = s.x + (ex / (d || 1)) * s.r; g.position.z = s.z + (ez / (d || 1)) * s.r; }
      if (d < best) { best = d; near = s.id; }
    }
    if (near !== lastNear.current) { lastNear.current = near; onNear(near); }
    g.rotation.y = yaw.current;
    // walk cycle
    const t = state.clock.elapsedTime * 11;
    const sw = moving ? Math.sin(t) * 0.8 * mag : 0;
    const L = limbs.current;
    if (L.armL) L.armL.rotation.x = THREE.MathUtils.lerp(L.armL.rotation.x, sw, 0.4);
    if (L.armR) L.armR.rotation.x = THREE.MathUtils.lerp(L.armR.rotation.x, -sw, 0.4);
    if (L.legL) L.legL.rotation.x = THREE.MathUtils.lerp(L.legL.rotation.x, -sw, 0.4);
    if (L.legR) L.legR.rotation.x = THREE.MathUtils.lerp(L.legR.rotation.x, sw, 0.4);
    g.position.y = moving ? Math.abs(Math.sin(t)) * 0.08 : 0;
    // pet trails behind
    const p = petRef.current;
    if (p) {
      const back = new THREE.Vector3(-Math.sin(yaw.current), 0, -Math.cos(yaw.current)).multiplyScalar(1.6);
      const goal = new THREE.Vector3(g.position.x + back.x + Math.cos(yaw.current) * 0.9, 0, g.position.z + back.z - Math.sin(yaw.current) * 0.9);
      const before = p.position.clone();
      p.position.lerp(goal, Math.min(1, dt * 4));
      const mv = p.position.clone().sub(before);
      if (mv.length() > 0.002) p.rotation.y = Math.atan2(mv.x, mv.z);
      p.position.y = mv.length() > 0.004 ? Math.abs(Math.sin(t * 0.9)) * 0.1 : 0;
    }
    // camera follows
    const camGoal = new THREE.Vector3(g.position.x, 16, g.position.z + 14);
    camera.position.lerp(camGoal, Math.min(1, dt * 3));
    camera.lookAt(g.position.x, 1, g.position.z);
  });

  const sp = species.find((s) => s.id === pet?.species_id);
  return (
    <>
      <group ref={group}><Character3D look={character!.appearance} limbs={limbs} /></group>
      {sp && pet && <group ref={petRef} position={[start[0] + 1.2, 0, start[1] - 1.6]}><Pet3D species={sp.id} stage={pet.stage} /></group>}
    </>
  );
}

function Joystick({ input }: { input: React.MutableRefObject<Input> }) {
  const [knob, setKnob] = useState({ x: 0, y: 0 });
  const base = useRef<HTMLDivElement>(null);
  const move = (e: React.PointerEvent) => {
    const r = base.current!.getBoundingClientRect();
    let x = (e.clientX - (r.left + r.width / 2)) / (r.width / 2), y = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
    const m = Math.hypot(x, y);
    if (m > 1) { x /= m; y /= m; }
    input.current = { x, z: y };
    setKnob({ x, y });
  };
  const end = () => { input.current = { x: 0, z: 0 }; setKnob({ x: 0, y: 0 }); };
  return (
    <div className="joy" ref={base} onPointerDown={(e) => { (e.target as Element).setPointerCapture(e.pointerId); move(e); }} onPointerMove={(e) => e.buttons && move(e)} onPointerUp={end} onPointerCancel={end}>
      <div className="joy-knob" style={{ transform: `translate(${knob.x * 34}px, ${knob.y * 34}px)` }} />
    </div>
  );
}

export function World3D({ onPlay, onPvp }: { onPlay: (lessonId: string) => void; onPvp: () => void }) {
  const { locations, paths, states, character } = useGame();
  const { visit, byId, here } = useTravel();
  const input = useRef<Input>({ x: 0, z: 0 });
  const target = useRef<THREE.Vector3 | null>(null);
  const [near, setNear] = useState<string | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [lowPower, setLowPower] = useState(() => { try { return localStorage.getItem('lowPower') === '1'; } catch { return false; } });
  const start = useMemo<[number, number]>(() => {
    const l = byId.get(here);
    const [x, z] = l ? toWorld(l.x, l.y) : [0, 0];
    return [x, z + 4.2];
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const onNear = useCallback((id: string | null) => {
    setNear(id);
    setSel((s) => (s && s !== id ? null : s)); // walking away closes the panel
  }, []);

  const enter = useCallback(async () => {
    const l = near ? byId.get(near) : undefined;
    if (!l) return;
    setSel(l.id);
    await visit(l);
  }, [near, byId, visit]);

  useEffect(() => {
    const k = (e: KeyboardEvent) => { if ((e.key === 'e' || e.key === 'Enter') && !(e.target instanceof HTMLInputElement)) enter(); };
    window.addEventListener('keydown', k);
    return () => window.removeEventListener('keydown', k);
  }, [enter]);

  const toggleLow = () => setLowPower((v) => { try { localStorage.setItem('lowPower', v ? '0' : '1'); } catch { /* ignore */ } return !v; });
  const nearLoc = near ? byId.get(near) : undefined;
  const coarse = typeof window !== 'undefined' && window.matchMedia?.('(pointer: coarse)').matches;

  return (
    <div className="world">
      <Canvas shadows={!lowPower} dpr={lowPower ? 1 : [1, 1.75]} camera={{ fov: 42, near: 0.1, far: 200 }} gl={{ antialias: !lowPower }}>
        <color attach="background" args={['#9fd8ff']} />
        <fog attach="fog" args={['#bfe6ff', 38, 90]} />
        <ambientLight intensity={1.15} />
        <hemisphereLight args={['#dff3ff', '#8bc26a', 0.6]} />
        <directionalLight position={[14, 24, 10]} intensity={2.0} castShadow={!lowPower} shadow-mapSize={[1024, 1024]}
          shadow-camera-left={-34} shadow-camera-right={34} shadow-camera-top={34} shadow-camera-bottom={-34} shadow-camera-far={80} />
        <Suspense fallback={null}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.25, 0]}>
            <circleGeometry args={[120, 48]} />
            <meshStandardMaterial color="#58b7ff" />
          </mesh>
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow
            onPointerDown={(e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); target.current = e.point.clone(); }}>
            <circleGeometry args={[WORLD_RADIUS + 1.5, 64]} />
            <meshStandardMaterial color="#86cf62" />
          </mesh>
          {paths.map(([a, b]) => {
            const A = byId.get(a), B = byId.get(b);
            return A && B ? <Road key={a + b} a={A} b={B} open={states[a] !== 'locked' && states[b] !== 'locked'} /> : null;
          })}
          {locations.map((l) => <Building key={l.id} loc={l} status={states[l.id] ?? 'locked'} active={near === l.id} />)}
          <Scenery locations={locations} paths={paths} />
          {character && <Player start={start} input={input} target={target} locations={locations} onNear={onNear} />}
        </Suspense>
      </Canvas>

      <div className="world-hint">{coarse ? 'ลากจอยสติ๊กเพื่อเดิน' : 'WASD / ลูกศร หรือคลิกพื้นเพื่อเดิน · E เพื่อเข้า'}</div>
      <button className="btn ghost world-low" onClick={toggleLow}>{lowPower ? '⚡ โหมดประหยัด: เปิด' : '⚡ โหมดประหยัด'}</button>
      {coarse && <Joystick input={input} />}
      {nearLoc && !sel && (
        <button className="btn big enter-btn" onClick={enter}>{nearLoc.icon} เข้า {nearLoc.name_en}</button>
      )}
      {sel && (
        <aside className="panel world-panel">
          <LocationPanel selected={byId.get(sel)} onClose={() => setSel(null)} onPlay={onPlay} onPvp={onPvp} />
        </aside>
      )}
    </div>
  );
}
