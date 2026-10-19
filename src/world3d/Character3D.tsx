import { useEffect, useMemo, type MutableRefObject } from 'react';
import { useGLTF } from '@react-three/drei';
import { clone } from 'three/examples/jsm/utils/SkeletonUtils.js';
import * as THREE from 'three';
import { modelUrl } from './assets';
import type { Appearance } from '../lib/types';

export interface Limbs {
  armL?: THREE.Object3D;
  armR?: THREE.Object3D;
  legL?: THREE.Object3D;
  legR?: THREE.Object3D;
  body?: THREE.Object3D;
}

function prepare(scene: THREE.Object3D) {
  const model = clone(scene);
  model.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (mesh.isMesh) {
      mesh.material = (mesh.material as THREE.Material).clone(); // own copy so each character can be tinted
      mesh.castShadow = true;
    }
  });
  return model;
}

// Chibi player model built by tools/blender/build_models.py. Look comes from characters.appearance.
export function Character3D({ look, limbs }: { look: Appearance; limbs?: MutableRefObject<Limbs> }) {
  const gltf = useGLTF(modelUrl('character'));
  const model = useMemo(() => prepare(gltf.scene), [gltf]);

  useEffect(() => {
    const show = (name: string, on: boolean) => {
      const o = model.getObjectByName(name);
      if (o) o.visible = on;
    };
    show('Hair_long', look.hairLength === 'long');
    show('Hair_wavy', look.hairType === 'wavy');
    show('Hair_curly', look.hairType === 'curly');
    show('Facial_moustache', look.facial === 'moustache');
    show('Facial_beard', look.facial === 'beard');
    const tint: Record<string, string> = { Skin: look.skin, Hair: look.hairColor, Outfit: look.outfit };
    model.traverse((o) => {
      const m = (o as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
      if (m && tint[m.name]) m.color.set(tint[m.name]);
    });
  }, [model, look]);

  useEffect(() => {
    if (!limbs) return;
    limbs.current = {
      armL: model.getObjectByName('ArmL') ?? undefined,
      armR: model.getObjectByName('ArmR') ?? undefined,
      legL: model.getObjectByName('LegL') ?? undefined,
      legR: model.getObjectByName('LegR') ?? undefined,
      body: model.getObjectByName('Body') ?? undefined,
    };
  }, [model, limbs]);

  return <primitive object={model} scale={1.0} />;
}

export function Pet3D({ species, stage }: { species: string; stage: number }) {
  const gltf = useGLTF(modelUrl(`pet_${species}`));
  const model = useMemo(() => prepare(gltf.scene), [gltf]);
  return <primitive object={model} scale={0.7 + stage * 0.22} />;
}

for (const f of ['character', 'pet_lion', 'pet_penguin', 'pet_monkey', 'pet_parrot']) useGLTF.preload(modelUrl(f));
