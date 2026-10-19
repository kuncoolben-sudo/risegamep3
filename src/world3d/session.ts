// Remembers where the player stands in the 3D world while other screens are open
// (2D map, lessons, pet, bag), so coming back does not teleport the character.
export const worldSession: { characterId: string | null; pos: [number, number] | null } = { characterId: null, pos: null };
