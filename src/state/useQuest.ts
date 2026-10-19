import { useMemo } from 'react';
import type { LessonRow, LocationRow } from '../lib/types';
import { useGame } from './GameContext';

// Main Quest: first unlocked unit that still has a required lesson to clear.
export function useQuest(): { location: LocationRow; lesson: LessonRow } | null {
  const { locations, lessons, states, progress } = useGame();
  return useMemo(() => {
    const next = [...locations].sort((a, b) => a.requires.length - b.requires.length || a.x - b.x)
      .find((l) => states[l.id] === 'open' && l.kind === 'unit');
    const lesson = next && lessons.find((l) => l.location_id === next.id && l.required && !progress.has(l.id));
    return next && lesson ? { location: next, lesson } : null;
  }, [locations, lessons, states, progress]);
}
