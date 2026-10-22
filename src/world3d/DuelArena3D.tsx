import { Suspense, forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { FantasyPet, type PetHandle } from './FantasyPet';
import { Shadow } from './PetViewer3D';

export interface ArenaFighter { species: string; stage: number }
/** What just happened in the duel: bump key for every new action. side 1 = the pet on the left, 2 = on the right. */
export interface ArenaCue { key: number; by: 1 | 2; kind: 'attack' | 'power'; form: number | null }

interface FighterHandle { attack: () => void; power: (form: number) => void; hurt: () => void; faint: () => void }

const SPACING = 2.3;

// One pet in the arena: its own power effects, plus a lunge for plain attacks, a shake when hit and a fall when beaten.
const Fighter = forwardRef<FighterHandle, { side: 1 | 2; species: string; stage: number }>(function Fighter({ side, species, stage }, ref) {
  const group = useRef<THREE.Group>(null);
  const pet = useRef<PetHandle>(null);
  const t = useRef({ lunge: -1, hurt: -1, faint: -1 });
  const dir = side === 1 ? 1 : -1; // towards the opponent along x
  useImperativeHandle(ref, () => ({
    attack() { t.current.lunge = 0; },
    power(form) { pet.current?.cast(form); },
    hurt() { t.current.hurt = 0; },
    faint() { t.current.faint = 0; },
  }), []);
  useFrame((_, dt) => {
    const g = group.current;
    if (!g) return;
    const s = t.current;
    let x = -dir * SPACING, y = 0, roll = 0;
    if (s.lunge >= 0) {
      s.lunge += dt;
      const u = Math.min(1, s.lunge / 0.55);
      x += dir * Math.sin(Math.PI * u) * 1.1;
      y += Math.sin(Math.PI * u) * 0.25;
      if (u >= 1) s.lunge = -1;
    }
    if (s.hurt >= 0) {
      s.hurt += dt;
      const u = Math.min(1, s.hurt / 0.45);
      x += Math.sin(s.hurt * 45) * 0.12 * (1 - u) - dir * 0.2 * (1 - u);
      if (u >= 1) s.hurt = -1;
    }
    if (s.faint >= 0) {
      s.faint += dt;
      const u = Math.min(1, s.faint / 0.8);
      roll = dir * -1.35 * u * u;
      y -= 0.15 * u;
    }
    g.position.set(x, y, 0);
    g.rotation.set(0, dir * Math.PI / 2, roll);
  });
  return (
    <group ref={group} rotation-order="YXZ">
      <FantasyPet ref={pet} species={species} stage={stage} />
    </group>
  );
});

function Framing() {
  const camera = useThree((s) => s.camera);
  useEffect(() => {
    camera.position.set(0, 3.1, 9.2);
    camera.lookAt(0, 1.1, 0);
  }, [camera]);
  return null;
}

// The 3D duel: p1 on the left facing p2. cue says what to play; loser (1 | 2) falls when the duel ends.
export default function DuelArena3D({ left, right, cue, loser, height = 340 }: {
  left: ArenaFighter; right: ArenaFighter; cue: ArenaCue | null; loser: 1 | 2 | null; height?: number;
}) {
  const refs = { 1: useRef<FighterHandle>(null), 2: useRef<FighterHandle>(null) };
  useEffect(() => {
    if (!cue) return;
    const me = refs[cue.by].current, foe = refs[cue.by === 1 ? 2 : 1].current;
    let timer = 0;
    if (cue.kind === 'power') { me?.power(cue.form ?? 1); timer = window.setTimeout(() => foe?.hurt(), 950); }
    else { me?.attack(); timer = window.setTimeout(() => foe?.hurt(), 300); }
    return () => window.clearTimeout(timer);
  }, [cue?.key]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (loser) refs[loser].current?.faint(); }, [loser]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ width: '100%', height, borderRadius: 16, overflow: 'hidden', background: 'radial-gradient(circle at 50% 35%, #8f6cb8, #48306e 62%, #2e1f47)' }}>
      <Canvas dpr={[1, 1.75]} camera={{ fov: 34, near: 0.1, far: 80 }}>
        <ambientLight intensity={1.15} />
        <hemisphereLight args={['#bcd8ff', '#3a3050', 0.6]} />
        <directionalLight position={[3, 6, 5]} intensity={2.1} />
        <Suspense fallback={null}>
          <Fighter ref={refs[1]} side={1} species={left.species} stage={left.stage} />
          <Fighter ref={refs[2]} side={2} species={right.species} stage={right.stage} />
        </Suspense>
        <group position={[-SPACING, 0, 0]}><Shadow r={1.3 + left.stage * 0.3} /></group>
        <group position={[SPACING, 0, 0]}><Shadow r={1.3 + right.stage * 0.3} /></group>
        <Framing />
      </Canvas>
    </div>
  );
}
