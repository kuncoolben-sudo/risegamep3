import { useCallback, useMemo } from 'react';
import { rpc, errorText } from '../lib/supabase';
import type { LocationRow } from '../lib/types';
import { useGame } from './GameContext';

// Shared by the 2D map and the 3D world: move the character to a location (server-validated).
export function useTravel() {
  const { locations, states, character, refresh, say } = useGame();
  const byId = useMemo(() => new Map(locations.map((l) => [l.id, l])), [locations]);
  const here = character?.location_id ?? 'start';

  const visit = useCallback(async (l: LocationRow): Promise<boolean> => {
    if (states[l.id] === 'locked') {
      say(`ยังไม่เปิด — ต้องผ่าน ${l.requires.map((r) => byId.get(r)?.name_en).join(', ')} ก่อน`);
      return false;
    }
    if (here !== l.id) {
      try {
        await rpc('travel', { p_loc: l.id });
        await refresh();
      } catch (e) {
        say(errorText(e));
        return false;
      }
    }
    return true;
  }, [states, here, byId, refresh, say]);

  return { visit, byId, here };
}
