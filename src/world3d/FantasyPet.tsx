import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { clone } from 'three/examples/jsm/utils/SkeletonUtils.js';
import * as THREE from 'three';
import { modelUrl } from './assets';
import { Effect } from './fx';
import { effectFor } from './fxRecipes';
import { clampStage, petModelName } from './pets';

export interface PetHandle {
  /** Release the power of a form (default: the pet's current form). Forms above the pet's stage are ignored. */
  cast: (form?: number) => void;
}

// A fantasy pet form from tools/blender/build_pets.py: loops its Idle clip and, on cast(), plays the matching
// Cast clip (Cast for the current form, Cast1/Cast2 for the powers of earlier forms) together with that power's effect.
export const FantasyPet = forwardRef<PetHandle, { species: string; stage: number; castKey?: number }>(function FantasyPet({ species, stage, castKey = 0 }, ref) {
  const st = clampStage(stage);
  const gltf = useGLTF(modelUrl(petModelName(species, st)));
  const model = useMemo(() => clone(gltf.scene), [gltf]);
  const mixer = useMemo(() => new THREE.AnimationMixer(model), [model]);
  const acts = useMemo(() => {
    const action = (name: string) => {
      const clip = gltf.animations.find((c) => c.name === name);
      if (!clip) return null;
      const a = mixer.clipAction(clip);
      if (name !== 'Idle') { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
      return a;
    };
    const casts: Record<number, THREE.AnimationAction | null> = {};
    for (let f = 1; f <= st; f++) casts[f] = action(f === st ? 'Cast' : `Cast${f}`);
    return { idle: action('Idle'), casts };
  }, [gltf, mixer, st]);
  // one effect per power this body can release, anchored to this body
  const effects = useMemo(() => {
    const list: Record<number, Effect | null> = {};
    for (let f = 1; f <= st; f++) {
      const spec = effectFor(species, f, st);
      list[f] = spec ? new Effect(spec) : null;
    }
    return list;
  }, [species, st]);
  const gl = useThree((s) => s.gl);

  useEffect(() => {
    acts.idle?.reset().play();
    const done = (e: { action?: THREE.AnimationAction }) => {
      if (acts.idle && e.action && Object.values(acts.casts).includes(e.action)) acts.idle.reset().play().crossFadeFrom(e.action, 0.3, false);
    };
    mixer.addEventListener('finished', done as never);
    return () => { mixer.removeEventListener('finished', done as never); mixer.stopAllAction(); };
  }, [acts, mixer]);
  useEffect(() => () => Object.values(effects).forEach((e) => e?.dispose()), [effects]);

  useFrame((_, dt) => {
    const d = Math.min(dt, 0.1);
    mixer.update(d);
    for (const e of Object.values(effects)) e?.update(d, gl.domElement.height);
  });

  const cast = useCallback((form?: number) => {
    const f = Math.min(st, Math.max(1, Math.round(form ?? st)));
    const a = acts.casts[f];
    if (a) {
      a.reset().play();
      if (acts.idle) a.crossFadeFrom(acts.idle, 0.15, false);
    }
    effects[f]?.play();
  }, [acts, effects, st]);
  useImperativeHandle(ref, () => ({ cast }), [cast]);
  // castKey > 0 at mount (a click made while the model was still loading) casts as soon as the pet is there
  useEffect(() => { if (castKey > 0) cast(); }, [castKey, cast]);

  return (
    <group>
      <primitive object={model} />
      {Object.entries(effects).map(([f, e]) => e && <primitive key={f} object={e.group} />)}
    </group>
  );
});
