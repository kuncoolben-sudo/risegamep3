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
