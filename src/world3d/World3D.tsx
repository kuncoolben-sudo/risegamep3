import { Suspense, useCallback, useEffect, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from 'react';
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
import { LOCATION_MODEL, NEAR_RADIUS, WORLD_RADIUS, collideRadius, footprint, toWorld } from './config';
import { IslandWorld, OBSTACLE_SPOTS, Scenery } from './Island';
import { daylight, phaseAt } from './daylight';

// Opening flyover, once per visit: from out at sea, low enough to see the sky, to behind the player.
const INTRO_FROM = new THREE.Vector3(0, 26, 100);
const INTRO_LOOK = new THREE.Vector3(0, 2, -8);
const INTRO_HOLD = 1.0, INTRO_MOVE = 3.2; // seconds

interface Input { x: number; z: number }

function Building({ loc, status, active }: { loc: LocationRow; status: LocationStatus; active: boolean }) {
  const def = LOCATION_MODEL[loc.id] ?? { file: 'b_cottage' };
  const { scene } = useGLTF(modelUrl(def.file));
  const [x, z] = toWorld(loc.x, loc.y);
  const locked = status === 'locked';
  const fp = footprint(loc.id); // landmark dioramas: ring, lock dome and label follow the model's size
  const labelY = def.labelY ? def.labelY * (def.scale ?? 1) + 0.3 : 4.6;
  const lockMat = <meshStandardMaterial color="#cfd6e2" transparent opacity={0.55} depthWrite={false} />;
  return (
    <group position={[x, 0, z]}>
      <group scale={def.scale ?? 1}><Clone object={scene} castShadow receiveShadow /></group>
      {locked && (fp ? (
        <mesh scale={[1, (labelY - 0.5) / (fp + 0.2), 1]}>
          <sphereGeometry args={[fp + 0.2, 28, 10, 0, Math.PI * 2, 0, Math.PI / 2]} />
          {lockMat}
        </mesh>
      ) : (
        <mesh position={[0, 1.6, 0]}>
          <sphereGeometry args={[3, 20, 14]} />
          {lockMat}
        </mesh>
      ))}
      {(status === 'open' || active) && !locked && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, 0]}>
          <ringGeometry args={fp ? [fp + 0.15, fp + 0.55, 56] : [3.6, 4.0, 40]} />
          <meshBasicMaterial color={active ? '#ffcf40' : '#ffffff'} transparent opacity={active ? 0.95 : 0.55} />
        </mesh>
      )}
      <Html center position={[0, labelY, 0]} distanceFactor={16} zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
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

// Sun (or moon), sky light and ambient light, coloured by the time of day (daylight.ts), which this also moves on and
// checks against the clock; the fog and the background take the horizon's colour. The sun follows the player so
// shadows stay sharp wherever you walk in the larger world.
function Lights({ target, shadows }: { target: MutableRefObject<THREE.Vector3>; shadows: boolean }) {
  const light = useRef<THREE.DirectionalLight>(null);
  const ambient = useRef<THREE.AmbientLight>(null);
  const hemi = useRef<THREE.HemisphereLight>(null);
  const aim = useMemo(() => new THREE.Object3D(), []);
  const dir = useMemo(() => new THREE.Vector3(), []);
  const scene = useThree((s) => s.scene);
  useEffect(() => {
    const id = window.setInterval(() => daylight.go(phaseAt()), 30_000);
    return () => window.clearInterval(id);
  }, []);
  useFrame((_, dt) => {
    daylight.step(dt);
    const t = target.current;
    const l = light.current;
    if (l) {
      daylight.lightDir(dir).multiplyScalar(30);
      l.position.set(t.x + dir.x, dir.y, t.z + dir.z);
      daylight.color((k) => k.light.color, l.color);
      l.intensity = daylight.num((k) => k.light.intensity);
    }
    aim.position.set(t.x, 0, t.z);
    aim.updateMatrixWorld();
    if (ambient.current) {
      daylight.color((k) => k.ambient[0], ambient.current.color);
      ambient.current.intensity = daylight.num((k) => k.ambient[1]);
    }
    if (hemi.current) {
      daylight.color((k) => k.hemi[0], hemi.current.color);
      daylight.color((k) => k.hemi[1], hemi.current.groundColor);
      hemi.current.intensity = daylight.num((k) => k.hemi[2]);
    }
    if (scene.fog instanceof THREE.Fog) daylight.sky(0, scene.fog.color);
    if (scene.background instanceof THREE.Color) daylight.sky(0, scene.background);
  });
  return (
    <>
      <ambientLight ref={ambient} />
      <hemisphereLight ref={hemi} />
      <primitive object={aim} />
      <directionalLight ref={light} target={aim} castShadow={shadows} shadow-mapSize={[1024, 1024]}
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
  const spots = useMemo(() => [
    ...locations.map((l) => {
      const [x, z] = toWorld(l.x, l.y);
      const r = collideRadius(l.id);
      return { id: l.id as string | null, x, z, r, reach: Math.max(NEAR_RADIUS, r + 1.7) }; // reach: close enough to enter (past where auto-walk stops)
    }),
    ...OBSTACLE_SPOTS.map((o) => ({ id: null, ...o, reach: 0 })), // mountains, the lake…: walked round, never entered
  ], [locations]);
  const intro = useRef(worldSession.introDone || dest ? -1 : 0); // seconds into the opening flyover, -1 once it is over

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

  useEffect(() => {
    pos.current.set(start[0], 0, start[1]);
    group.current?.position.set(start[0], 0, start[1]);
    if (intro.current === 0) {
      worldSession.introDone = true;
      camera.position.copy(INTRO_FROM);
      camera.lookAt(INTRO_LOOK);
    } else camera.position.set(start[0], 16, start[1] + 14);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
    let near: string | null = null, best = Infinity;
    for (const s of spots) {
      const ex = g.position.x - s.x, ez = g.position.z - s.z;
      const d = Math.hypot(ex, ez);
      if (auto && s.id !== destRef.current && d < s.r + 0.4) { g.position.x += (-ez / (d || 1)) * 3 * dt; g.position.z += (ex / (d || 1)) * 3 * dt; } // nudge sideways so we slide round it
      if (d < s.r) { g.position.x = s.x + (ex / (d || 1)) * s.r; g.position.z = s.z + (ez / (d || 1)) * s.r; }
      if (d < s.reach && d < best) { best = d; near = s.id; }
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
    // camera follows, after the opening flyover (which any move of the player cuts short)
    const camGoal = new THREE.Vector3(g.position.x, 16, g.position.z + 14);
    if (intro.current >= 0 && (manual || destRef.current)) intro.current = -1;
    if (intro.current >= 0) {
      intro.current += dt;
      const u = Math.min(1, Math.max(0, (intro.current - INTRO_HOLD) / INTRO_MOVE)), e = u * u * (3 - 2 * u);
      camera.position.lerpVectors(INTRO_FROM, camGoal, e);
      camera.lookAt(INTRO_LOOK.x + (g.position.x - INTRO_LOOK.x) * e, INTRO_LOOK.y + (1 - INTRO_LOOK.y) * e, INTRO_LOOK.z + (g.position.z - INTRO_LOOK.z) * e);
      if (u >= 1) intro.current = -1;
    } else {
      camera.position.lerp(camGoal, Math.min(1, dt * 3));
      camera.lookAt(g.position.x, 1, g.position.z);
    }
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
    return [x, z + Math.max(4.2, (l ? collideRadius(l.id) : 0) + 1.0)];
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
      <Canvas shadows={!lowPower} dpr={lowPower ? 1 : [1, 1.75]} camera={{ fov: 42, near: 0.3, far: 1200 }} gl={{ antialias: !lowPower }}>
        <color attach="background" args={['#bfe6ff']} />
        <fog attach="fog" args={['#cdeeff', 160, 620]} />
        <Lights target={playerPos} shadows={!lowPower} />
        <Suspense fallback={null}>
          <IslandWorld shadows={!lowPower} />
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
