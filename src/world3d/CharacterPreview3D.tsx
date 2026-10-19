import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Character3D } from './Character3D';
import type { Appearance } from '../lib/types';

// Slowly turning 3D preview for the character creator; drag to rotate.
export default function CharacterPreview3D({ look, height = 260 }: { look: Appearance; height?: number }) {
  return (
    <div style={{ width: '100%', height }}>
      <Canvas dpr={[1, 1.75]} camera={{ fov: 32, position: [0, 1.15, 4.4] }}>
        <ambientLight intensity={1.1} />
        <directionalLight position={[3, 5, 4]} intensity={2.2} />
        <Suspense fallback={null}>
          <Character3D look={look} />
        </Suspense>
        <OrbitControls target={[0, 0.85, 0]} enablePan={false} enableZoom={false} autoRotate autoRotateSpeed={2.2}
          minPolarAngle={Math.PI / 2.6} maxPolarAngle={Math.PI / 2.1} />
      </Canvas>
    </div>
  );
}
