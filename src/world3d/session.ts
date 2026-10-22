// Remembers where the player stands in the 3D world while other screens are open
// (2D map, lessons, pet, bag), so coming back does not teleport the character,
// whether the opening flyover over the island has already played on this visit,
// and how far the camera is zoomed.
export const worldSession: { characterId: string | null; pos: [number, number] | null; introDone: boolean; zoom: number | null } = {
  characterId: null, pos: null, introDone: false, zoom: null,
};
