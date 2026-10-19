import { Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Clone, Html, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { useGame } from '../state/GameContext';
import { useTravel } from '../state/useTravel';
import { useQuest } from '../state/useQuest';
import { LocationPanel } from '../components/LocationPanel';
import type { LocationRow, LocationStatus } from '../lib/types';
import { modelUrl } from './assets';
import { Character3D, Pet3D, type Limbs } from './Character3D';
import { worldSession } from './session';
import { COLLIDE_RADIUS, LOCATION_MODEL, NEAR_RADIUS, SCENERY_COUNT, WORLD_RADIUS, rng, toWorld } from './config';

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

type SceneryKind = 'tree' | 'pine' | 'rock' | 'flower';
interface Scatter { x: number; z: number; s: number; ry: number }

// One InstancedMesh per mesh of the model: hundreds of props cost a handful of draw calls.
function Instanced({ scene, items }: { scene: THREE.Object3D; items: Scatter[] }) {
  const parts = useMemo(() => {
    scene.updateWorldMatrix(true, true);
    const out: { geo: THREE.BufferGeometry; mat: THREE.Material; local: THREE.Matrix4 }[] = [];
    scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) out.push({ geo: m.geometry, mat: m.material as THREE.Material, local: m.matrixWorld.clone() });
    });
    return out;
  }, [scene]);
  const refs = useRef<(THREE.InstancedMesh | null)[]>([]);
  useLayoutEffect(() => {
    const P = new THREE.Matrix4(), M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), pos = new THREE.Vector3(), sc = new THREE.Vector3();
    parts.forEach((part, pi) => {
      const im = refs.current[pi];
      if (!im) return;
      items.forEach((it, i) => {
        q.setFromEuler(e.set(0, it.ry, 0));
        P.compose(pos.set(it.x, 0, it.z), q, sc.setScalar(it.s));
        im.setMatrixAt(i, M.multiplyMatrices(P, part.local));
      });
      im.instanceMatrix.needsUpdate = true;
    });
  }, [parts, items]);
  if (items.length === 0) return null;
  return <>{parts.map((p, i) => <instancedMesh key={i} ref={(el) => { refs.current[i] = el; }} args={[p.geo, p.mat, items.length]} castShadow frustumCulled={false} />)}</>;
}

function Scenery({ locations, paths }: { locations: LocationRow[]; paths: [string, string][] }) {
  const scenes: Record<SceneryKind, THREE.Object3D> = {
    tree: useGLTF(modelUrl('p_tree')).scene,
    pine: useGLTF(modelUrl('p_pine')).scene,
    rock: useGLTF(modelUrl('p_rock')).scene,
    flower: useGLTF(modelUrl('p_flower')).scene,
  };
  const groups = useMemo(() => {
    const r = rng(7);
    const pts = locations.map((l) => toWorld(l.x, l.y));
    const byId = new Map(locations.map((l) => [l.id, l]));
    const segs = paths.map(([a, b]) => [toWorld(byId.get(a)!.x, byId.get(a)!.y), toWorld(byId.get(b)!.x, byId.get(b)!.y)] as const);
    const segDist = (px: number, pz: number, [[ax, az], [bx, bz]]: readonly [readonly number[], readonly number[]]) => {
      const dx = bx - ax, dz = bz - az;
      const t = Math.max(0, Math.min(1, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz)));
      return Math.hypot(px - (ax + t * dx), pz - (az + t * dz));
    };
    const out: Record<SceneryKind, Scatter[]> = { tree: [], pine: [], rock: [], flower: [] };
    let n = 0, tries = 0;
    while (n < SCENERY_COUNT && tries++ < 6000) {
      const ang = r() * Math.PI * 2, rad = Math.sqrt(r()) * (WORLD_RADIUS - 1);
      const x = Math.cos(ang) * rad, z = Math.sin(ang) * rad;
      if (pts.some(([px, pz]) => Math.hypot(px - x, pz - z) < 5.2)) continue;
      if (segs.some((s) => segDist(x, z, s) < 2.0)) continue;
      const k = r();
      const kind: SceneryKind = k < 0.4 ? 'tree' : k < 0.65 ? 'pine' : k < 0.8 ? 'rock' : 'flower';
      const s = 0.8 + r() * 0.6;
      out[kind].push({ x, z, s: kind === 'flower' ? s * 1.4 : s, ry: r() * 6.28 });
      n++;
    }
    return out;
  }, [locations, paths]);
  return <>{(Object.keys(groups) as SceneryKind[]).map((k) => <Instanced key={k} scene={scenes[k]} items={groups[k]} />)}</>;
}

// The sun follows the player so shadows stay sharp wherever you walk in the larger world.
function SunLight({ target, shadows }: { target: MutableRefObject<THREE.Vector3>; shadows: boolean }) {
  const light = useRef<THREE.DirectionalLight>(null);
  const aim = useMemo(() => new THREE.Object3D(), []);
  useFrame(() => {
    const l = light.current;
    if (!l) return;
    const t = target.current;
    l.position.set(t.x + 14, 24, t.z + 10);
    aim.position.set(t.x, 0, t.z);
    aim.updateMatrixWorld();
  });
  return (
    <>
      <primitive object={aim} />
      <directionalLight ref={light} target={aim} intensity={2.0} castShadow={shadows} shadow-mapSize={[1024, 1024]}
        shadow-camera-left={-28} shadow-camera-right={28} shadow-camera-top={28} shadow-camera-bottom={-28} shadow-camera-near={1} shadow-camera-far={70} />
    </>
  );
}

// Minimap + compass arrow to the Main Quest. Updated straight on the DOM each frame (no React re-render).
function Minimap({ locations, states, pos, quest }: {
  locations: LocationRow[]; states: Record<string, LocationStatus>; pos: MutableRefObject<THREE.Vector3>; quest: LocationRow | null;
}) {
  const SIZE = 128;
  const k = (SIZE / 2 - 4) / WORLD_RADIUS;
  const dot = useRef<HTMLDivElement>(null);
  const arrow = useRef<HTMLDivElement>(null);
  const dist = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const p = pos.current;
      if (dot.current) dot.current.style.transform = `translate(${p.x * k}px, ${p.z * k}px)`;
      if (quest && arrow.current) {
        const [qx, qz] = toWorld(quest.x, quest.y);
        const dx = qx - p.x, dz = qz - p.z, d = Math.hypot(dx, dz);
        arrow.current.style.display = d < 7 ? 'none' : 'flex';
        arrow.current.style.setProperty('--rot', `${Math.atan2(dx, -dz)}rad`); // camera looks toward -Z
        if (dist.current) dist.current.textContent = `${Math.round(d)} ม.`;
      }
      raf = requestAnimationFrame(tick);
    };
    tick();
    return () => cancelAnimationFrame(raf);
  }, [pos, quest, k]);
  return (
    <div className="minimap-wrap">
      <div className="minimap" style={{ width: SIZE, height: SIZE }}>
        {locations.map((l) => {
          const [x, z] = toWorld(l.x, l.y);
          return <i key={l.id} className={`mm-dot ${states[l.id] ?? 'locked'} ${quest?.id === l.id ? 'quest' : ''}`} style={{ left: SIZE / 2 + x * k, top: SIZE / 2 + z * k }} title={l.name_en} />;
        })}
        <div className="mm-me" ref={dot} />
      </div>
      {quest && (
        <div className="quest-arrow" ref={arrow}>
          <b className="arrow-icon">▲</b>
          <span><small>{quest.name_en}</small><br /><span ref={dist} /></span>
        </div>
      )}
    </div>
  );
}

function Player({ start, input, pos, locations, onNear, dest, onDest }: {
  start: [number, number];
  input: React.MutableRefObject<Input>;
  pos: MutableRefObject<THREE.Vector3>;
  locations: LocationRow[];
  onNear: (id: string | null) => void;
  dest: string | null;
  onDest: (id: string | null) => void;
}) {
  const { character, pet, species } = useGame();
  const destRef = useRef<string | null>(dest);
  destRef.current = dest;
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
    const down = (e: KeyboardEvent) => { if (!typing()) keys.current.add(e.key.toLowerCase()); };
    const up = (e: KeyboardEvent) => keys.current.delete(e.key.toLowerCase());
    const clear = () => keys.current.clear();
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', clear);
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); window.removeEventListener('blur', clear); };
  }, []);

  useEffect(() => { pos.current.set(start[0], 0, start[1]); group.current?.position.set(start[0], 0, start[1]); camera.position.set(start[0], 16, start[1] + 14); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useFrame((state, dt) => {
    const g = group.current;
    if (!g || !character) return;
    const k = keys.current;
    let dx = (k.has('d') || k.has('arrowright') ? 1 : 0) - (k.has('a') || k.has('arrowleft') ? 1 : 0) + input.current.x;
    let dz = (k.has('s') || k.has('arrowdown') ? 1 : 0) - (k.has('w') || k.has('arrowup') ? 1 : 0) + input.current.z;
    const manual = Math.hypot(dx, dz) > 0.05;
    const target = destRef.current ? spots.find((sp) => sp.id === destRef.current) : undefined;
    let auto = false;
    if (target && manual) onDest(null); // the player took the controls: cancel the auto-walk
    else if (target) {
      // walk to the side of the building facing us, stop when close enough to enter
      const ex = g.position.x - target.x, ez = g.position.z - target.z, d = Math.hypot(ex, ez) || 1;
      if (d <= target.r + 1.6) onDest(null);
      else {
        const gx = target.x + (ex / d) * (target.r + 1.2) - g.position.x, gz = target.z + (ez / d) * (target.r + 1.2) - g.position.z;
        const gd = Math.hypot(gx, gz) || 1;
        dx = gx / gd; dz = gz / gd; auto = true;
      }
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
      if (auto && s.id !== destRef.current && d < s.r + 0.4) { g.position.x += (-ez / (d || 1)) * 3 * dt; g.position.z += (ex / (d || 1)) * 3 * dt; } // nudge sideways so we slide round it
      if (d < s.r) { g.position.x = s.x + (ex / (d || 1)) * s.r; g.position.z = s.z + (ez / (d || 1)) * s.r; }
      if (d < best) { best = d; near = s.id; }
    }
    if (near !== lastNear.current) { lastNear.current = near; onNear(near); }
    pos.current.copy(g.position);
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

// Floating joystick: press anywhere on the world, drag to move, release to stop.
function JoystickLayer({ input }: { input: React.MutableRefObject<Input> }) {
  const RADIUS = 56;
  const [ui, setUi] = useState<{ ox: number; oy: number; kx: number; ky: number } | null>(null);
  const pointer = useRef<number | null>(null);
  const origin = useRef({ x: 0, y: 0 });
  const local = (e: React.PointerEvent) => {
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };
  const stop = () => { pointer.current = null; input.current = { x: 0, z: 0 }; setUi(null); };
  return (
    <div className="joy-layer"
      onPointerDown={(e) => {
        if (pointer.current !== null) return;
        pointer.current = e.pointerId;
        e.currentTarget.setPointerCapture(e.pointerId);
        origin.current = local(e);
        setUi({ ox: origin.current.x, oy: origin.current.y, kx: 0, ky: 0 });
      }}
      onPointerMove={(e) => {
        if (e.pointerId !== pointer.current) return;
        const p = local(e);
        let dx = p.x - origin.current.x, dy = p.y - origin.current.y;
        const m = Math.hypot(dx, dy);
        if (m > RADIUS) { dx *= RADIUS / m; dy *= RADIUS / m; }
        const nx = dx / RADIUS, ny = dy / RADIUS;
        input.current = Math.hypot(nx, ny) < 0.12 ? { x: 0, z: 0 } : { x: nx, z: ny };
        setUi({ ox: origin.current.x, oy: origin.current.y, kx: dx, ky: dy });
      }}
      onPointerUp={(e) => { if (e.pointerId === pointer.current) stop(); }}
      onPointerCancel={(e) => { if (e.pointerId === pointer.current) stop(); }}
      onLostPointerCapture={stop}
    >
      {ui && (
        <div className="joy" style={{ left: ui.ox - 60, top: ui.oy - 60 }}>
          <div className="joy-knob" style={{ transform: `translate(${ui.kx}px, ${ui.ky}px)` }} />
        </div>
      )}
    </div>
  );
}

export function World3D({ onPlay, onPvp, hud, goTo, onGoConsumed }: {
  onPlay: (lessonId: string) => void; onPvp: () => void; hud?: ReactNode; goTo?: string | null; onGoConsumed?: () => void;
}) {
  const { locations, paths, states, character } = useGame();
  const { visit, byId, here } = useTravel();
  const input = useRef<Input>({ x: 0, z: 0 });
  const playerPos = useRef(new THREE.Vector3());
  const quest = useQuest();
  const [near, setNear] = useState<string | null>(null);
  const [dest, setDest] = useState<string | null>(goTo ?? null);
  const [sel, setSel] = useState<string | null>(null);
  const [lowPower, setLowPower] = useState(() => { try { return localStorage.getItem('lowPower') === '1'; } catch { return false; } });
  const start = useMemo<[number, number]>(() => {
    if (worldSession.characterId === character?.id && worldSession.pos) return worldSession.pos;
    const l = byId.get(here);
    const [x, z] = l ? toWorld(l.x, l.y) : [0, 0];
    return [x, z + 4.2];
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { if (goTo) onGoConsumed?.(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => { worldSession.characterId = character?.id ?? null; worldSession.pos = [playerPos.current.x, playerPos.current.z]; }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
  const coarse = typeof window !== 'undefined' && !!window.matchMedia?.('(pointer: coarse)').matches;

  return (
    <div className="world">
      <Canvas shadows={!lowPower} dpr={lowPower ? 1 : [1, 1.75]} camera={{ fov: 42, near: 0.1, far: 150 }} gl={{ antialias: !lowPower }}>
        <color attach="background" args={['#9fd8ff']} />
        <fog attach="fog" args={['#bfe6ff', 50, 115]} />
        <ambientLight intensity={1.15} />
        <hemisphereLight args={['#dff3ff', '#8bc26a', 0.6]} />
        <SunLight target={playerPos} shadows={!lowPower} />
        <Suspense fallback={null}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.25, 0]}>
            <circleGeometry args={[170, 48]} />
            <meshStandardMaterial color="#58b7ff" />
          </mesh>
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <circleGeometry args={[WORLD_RADIUS + 1.5, 64]} />
            <meshStandardMaterial color="#86cf62" />
          </mesh>
          {paths.map(([a, b]) => {
            const A = byId.get(a), B = byId.get(b);
            return A && B ? <Road key={a + b} a={A} b={B} open={states[a] !== 'locked' && states[b] !== 'locked'} /> : null;
          })}
          {locations.map((l) => <Building key={l.id} loc={l} status={states[l.id] ?? 'locked'} active={near === l.id} />)}
          <Scenery locations={locations} paths={paths} />
          {character && <Player start={start} input={input} pos={playerPos} locations={locations} onNear={onNear} dest={dest} onDest={setDest} />}
        </Suspense>
      </Canvas>

      <JoystickLayer input={input} />
      {hud}
      <Minimap locations={locations} states={states} pos={playerPos} quest={quest?.location ?? null} />
      <div className="world-hint">{dest ? `🚶 กำลังเดินไป ${byId.get(dest)?.name_en ?? ''}… (แตะจอเพื่อเดินเอง)` : coarse ? 'แตะค้างตรงไหนก็ได้บนจอแล้วลากเพื่อเดิน' : 'ลากเมาส์ค้าง หรือ WASD / ลูกศร · E เพื่อเข้า'}</div>
      <button className="btn ghost world-low" onClick={toggleLow}>{lowPower ? '⚡ โหมดประหยัด: เปิด' : '⚡ โหมดประหยัด'}</button>
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
