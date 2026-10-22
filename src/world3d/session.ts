// Remembers where the player stands in the 3D world while other screens are open
// (2D map, lessons, pet, bag), so coming back does not teleport the character,
// and whether the opening flyover over the island has already played on this visit.
export const worldSession: { characterId: string | null; pos: [number, number] | null; introDone: boolean } = {
  characterId: null, pos: null, introDone: false,
};
