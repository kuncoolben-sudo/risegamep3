import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { clone } from 'three/examples/jsm/utils/SkeletonUtils.js';
import * as THREE from 'three';
import { modelUrl } from './assets';
import { Effect } from './fx';
import { effectFor } from './fxRecipes';
import { petModelName } from './pets';

export interface PetHandle { cast: () => void }

// A fantasy pet form from tools/blender/build_pets.py: loops its Idle clip and, on cast(), plays the Cast clip
// together with the power effect of that form.
export const FantasyPet = forwardRef<PetHandle, { species: string; stage: number; castKey?: number }>(function FantasyPet({ species, stage, castKey = 0 }, ref) {
  const gltf = useGLTF(modelUrl(petModelName(species, stage)));
  const model = useMemo(() => clone(gltf.scene), [gltf]);
  const mixer = useMemo(() => new THREE.AnimationMixer(model), [model]);
  const acts = useMemo(() => {
    const find = (name: string) => gltf.animations.find((c) => c.name === name);
    const idleClip = find('Idle'), castClip = find('Cast');
    const idle = idleClip ? mixer.clipAction(idleClip) : null;
    const cast = castClip ? mixer.clipAction(castClip) : null;
    if (cast) { cast.setLoop(THREE.LoopOnce, 1); cast.clampWhenFinished = true; }
    return { idle, cast };
  }, [gltf, mixer]);
  const effect = useMemo(() => {
    const spec = effectFor(species, stage);
    return spec ? new Effect(spec) : null;
  }, [species, stage]);
  const gl = useThree((s) => s.gl);

  useEffect(() => {
    acts.idle?.reset().play();
    const done = (e: { action?: THREE.AnimationAction }) => {
      if (e.action === acts.cast && acts.idle) acts.idle.reset().play().crossFadeFrom(acts.cast, 0.3, false);
    };
    mixer.addEventListener('finished', done as never);
    return () => { mixer.removeEventListener('finished', done as never); mixer.stopAllAction(); };
  }, [acts, mixer]);
  useEffect(() => () => effect?.dispose(), [effect]);

  useFrame((_, dt) => {
    mixer.update(Math.min(dt, 0.1));
    effect?.update(Math.min(dt, 0.1), gl.domElement.height);
  });

  const cast = useCallback(() => {
    if (acts.cast) {
      acts.cast.reset().play();
      if (acts.idle) acts.cast.crossFadeFrom(acts.idle, 0.15, false);
    }
    effect?.play();
  }, [acts, effect]);
  useImperativeHandle(ref, () => ({ cast }), [cast]);
  // castKey > 0 at mount (a click made while the model was still loading) casts as soon as the pet is there
  useEffect(() => { if (castKey > 0) cast(); }, [castKey, cast]);

  return (
    <group>
      <primitive object={model} />
      {effect && <primitive object={effect.group} />}
    </group>
  );
});
