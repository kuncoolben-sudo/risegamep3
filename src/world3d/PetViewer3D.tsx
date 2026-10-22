import { Suspense, useEffect, useMemo, useRef, type ElementRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { FantasyPet } from './FantasyPet';
import { clampStage } from './pets';

// Soft blob under the pet so it does not float.
export function Shadow({ r }: { r: number }) {
  const tex = useMemo(() => {
    const c = document.createElement('canvas');
    c.width = c.height = 64;
    const g = c.getContext('2d')!;
    const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, 'rgba(0,0,0,0.38)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grad;
    g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }, []);
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]} scale={r}>
      <circleGeometry args={[1, 32]} />
      <meshBasicMaterial map={tex} transparent depthWrite={false} />
    </mesh>
  );
}

// Frames the pet for its form (later forms are bigger and their powers reach further) and lets the player drag around it.
function Framing({ stage }: { stage: 1 | 2 | 3 }) {
  const camera = useThree((s) => s.camera);
  const controls = useRef<ElementRef<typeof OrbitControls>>(null);
  const dist = [5.6, 7.2, 9.2][stage - 1], y = [0.55, 0.9, 1.2][stage - 1], z = [0.7, 1.1, 1.5][stage - 1];
  useEffect(() => {
    // from the pet's left, slightly in front: it faces to the right and its power sweeps across the picture
    camera.position.set(-dist * 0.82, y + dist * 0.26, z + dist * 0.48);
    controls.current?.target.set(0, y, z);
    controls.current?.update();
  }, [camera, dist, y, z]);
  return <OrbitControls ref={controls} enablePan={false} enableZoom={false} minPolarAngle={Math.PI / 3.2} maxPolarAngle={Math.PI / 2.05} />;
}

// Turntable view of one pet form. Bump castKey to make it release its power; drag to look around.
export default function PetViewer3D({ species, stage, castKey = 0, height = 320 }: { species: string; stage: number; castKey?: number; height?: number }) {
  const st = clampStage(stage);
  return (
    <div style={{ width: '100%', height, borderRadius: 16, overflow: 'hidden', background: 'radial-gradient(circle at 50% 40%, #8f6cb8, #48306e 62%, #2e1f47)' }}>
      <Canvas dpr={[1, 1.75]} camera={{ fov: 34, near: 0.1, far: 60 }}>
        <ambientLight intensity={1.15} />
        <hemisphereLight args={['#bcd8ff', '#3a3050', 0.6]} />
        <directionalLight position={[3, 6, 4]} intensity={2.1} />
        <Suspense fallback={null}>
          <FantasyPet species={species} stage={st} castKey={castKey} />
        </Suspense>
        <Shadow r={0.9 + st * 0.35} />
        <Framing stage={st} />
      </Canvas>
    </div>
  );
}
