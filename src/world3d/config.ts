// Map (2D design coordinates) -> 3D world coordinates, plus which model stands at each location.
// ~1.6x larger than the first version: longer walks between places, more to look at on the way
export const WORLD_RADIUS = 40;
export const toWorld = (x: number, y: number): [number, number] => [(x - 500) / 14, (y - 380) / 14];
export const SCENERY_COUNT = 280;

// file: a GLB in public/models. The eight unit landmarks (tools/blender/build_places.py) are round dioramas that also
// give their footprint radius and label height in model units; those size the ring, lock dome, collision and label.
export interface LocationModel { file: string; scale?: number; radius?: number; labelY?: number }

const LANDMARK = 0.75; // the landmark dioramas are ~10 m across; this fits them between the neighbouring places
export const LOCATION_MODEL: Record<string, LocationModel> = {
  start: { file: 'b_cottage' },
  u1: { file: 'loc_palace', scale: LANDMARK, radius: 5.4, labelY: 6.8 },
  u2: { file: 'loc_inthanon', scale: LANDMARK, radius: 5.0, labelY: 7.8 },
  u3: { file: 'loc_chiangmai', scale: LANDMARK, radius: 4.8, labelY: 7.4 },
  u4: { file: 'loc_phiphi', scale: LANDMARK, radius: 5.0, labelY: 6.0 },
  u5: { file: 'loc_amphawa', scale: LANDMARK, radius: 5.0, labelY: 5.0 },
  u6: { file: 'loc_whitetemple', scale: LANDMARK, radius: 5.0, labelY: 7.2 },
  u7: { file: 'loc_phuket', scale: LANDMARK, radius: 5.0, labelY: 5.2 },
  u8: { file: 'loc_khaoyai', scale: LANDMARK, radius: 5.0, labelY: 6.2 },
  campA: { file: 'b_tent' },
  campB: { file: 'b_tent' },
  inn1: { file: 'b_hospital' },
  hospital: { file: 'b_hospital' },
  arena: { file: 'b_arena' },
  festival: { file: 'b_festival' },
  sounds: { file: 'b_sound' },
};

export const COLLIDE_RADIUS: Record<string, number> = { arena: 3.8, b_festival: 3.2 };
export const NEAR_RADIUS = 5.2;

/** Radius of a landmark diorama on the ground in world units (null for the small buildings). */
export function footprint(id: string): number | null {
  const m = LOCATION_MODEL[id];
  return m?.radius ? m.radius * (m.scale ?? 1) : null;
}

/** How close to a location's centre the player may walk. */
export function collideRadius(id: string): number {
  const fp = footprint(id);
  if (fp) return fp * 0.9; // a step onto the rim of the diorama
  return COLLIDE_RADIUS[LOCATION_MODEL[id]?.file ?? ''] ?? COLLIDE_RADIUS[id] ?? 2.6;
}

// deterministic pseudo-random so the forest is the same on every load
export function rng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}
