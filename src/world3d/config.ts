// Map (2D design coordinates) -> 3D world coordinates, plus which model stands at each location.
// ~1.6x larger than the first version: longer walks between places, more to look at on the way
export const WORLD_RADIUS = 40;
export const toWorld = (x: number, y: number): [number, number] => [(x - 500) / 14, (y - 380) / 14];
export const SCENERY_COUNT = 280;

export const LOCATION_MODEL: Record<string, { file: string; scale?: number }> = {
  start: { file: 'b_cottage' },
  u1: { file: 'b_school' },
  u2: { file: 'b_weather' },
  u3: { file: 'b_family' },
  u4: { file: 'b_town' },
  u5: { file: 'b_cake', scale: 0.9 },
  u6: { file: 'b_clock' },
  u7: { file: 'b_beach' },
  u8: { file: 'b_story' },
  campA: { file: 'b_tent' },
  campB: { file: 'b_tent' },
  inn1: { file: 'b_inn' },
  hospital: { file: 'b_hospital' },
  arena: { file: 'b_arena' },
  festival: { file: 'b_festival' },
  sounds: { file: 'b_sound' },
};

export const COLLIDE_RADIUS: Record<string, number> = { arena: 3.8, b_town: 3.4, b_festival: 3.2, b_cake: 2.6 };
export const NEAR_RADIUS = 5.2;

// deterministic pseudo-random so the forest is the same on every load
export function rng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}
