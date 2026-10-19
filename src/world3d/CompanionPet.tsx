import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { FantasyPet, type PetHandle } from './FantasyPet';

// The player's fantasy pet out in the world. When the player stands still for a while it shows off the power of
// its current form (then rests for a good while so it never gets in the way).
export function CompanionPet({ species, stage }: { species: string; stage: number }) {
  const handle = useRef<PetHandle>(null);
  const group = useRef<THREE.Group>(null);
  const last = useRef(new THREE.Vector3());
  const still = useRef(0);
  const cooldown = useRef(8);
  const now = useMemo(() => new THREE.Vector3(), []);
  useFrame((_, dt) => {
    if (!group.current) return;
    group.current.getWorldPosition(now);
    still.current = now.distanceTo(last.current) < 0.004 ? still.current + Math.min(dt, 0.1) : 0;
    last.current.copy(now);
    cooldown.current -= Math.min(dt, 0.1);
    if (still.current > 7 && cooldown.current <= 0) {
      handle.current?.cast();
      still.current = 0;
      cooldown.current = 30;
    }
  });
  return <group ref={group} scale={0.8}><FantasyPet ref={handle} species={species} stage={stage} /></group>;
}
