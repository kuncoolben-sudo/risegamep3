export function shuffled<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export const STAGE_THRESHOLDS = [6, 18]; // lessons cleared for stage 2 and 3 (must match complete_lesson)
export const STAGE_NAMES = ['ลูกสัตว์', 'สัตว์เติบโต', 'ผู้พิทักษ์'];

// Duel stats come from the stars collected in lessons: every stat is STAT_BASE + STAT_PER_STAR per star
// (best result of each lesson). Must match public._pet_stats in supabase/migrations/0005_auto_duel.sql.
export const STAT_BASE = 10;
export const STAT_PER_STAR = 2;
export const statValue = (stars: number) => STAT_BASE + STAT_PER_STAR * stars;
export const totalStars = (progress: Map<string, { stars: number }>) => [...progress.values()].reduce((n, p) => n + p.stars, 0);
