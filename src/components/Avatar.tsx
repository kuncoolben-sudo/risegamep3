import type { Appearance } from '../lib/types';

export const SKINS = ['#ffdfc4', '#f1c27d', '#c68642', '#8d5524'];
export const HAIR_COLORS = ['#2b1b0e', '#6b3e1c', '#e0b050', '#c0392b', '#7f8c8d', '#3b82f6'];
export const OUTFITS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#a855f7', '#ec4899'];

export const DEFAULT_APPEARANCE: Appearance = {
  skin: SKINS[1], hairLength: 'short', hairType: 'straight', hairColor: HAIR_COLORS[1], facial: 'none', outfit: OUTFITS[1],
};

// plain-English hair description
export function hairLabel(a: Appearance): string {
  return `${a.hairLength} ${a.hairType} hair`;
}

export function Avatar({ look, size = 96 }: { look: Appearance; size?: number }) {
  const { skin, hairLength, hairType, hairColor, facial, outfit } = look;
  const long = hairLength === 'long';
  // hair "edge" decoration along the outline: smooth, scalloped (wavy) or bumpy (curly)
  const bumps: [number, number, number][] = [];
  if (hairType !== 'straight') {
    const r = hairType === 'curly' ? 5.5 : 4;
    const n = hairType === 'curly' ? 9 : 6;
    for (let i = 0; i < n; i++) {
      const ang = Math.PI + (Math.PI * (i + 0.5)) / n;
      bumps.push([50 + Math.cos(ang) * 26, 50 + Math.sin(ang) * 26, r]);
    }
    if (long) {
      for (const side of [-1, 1]) for (let k = 0; k < 3; k++) bumps.push([50 + side * 31, 58 + k * 12, hairType === 'curly' ? 6 : 4.5]);
    }
  }
  return (
    <svg viewBox="0 0 100 120" width={size} height={size * 1.2} role="img" aria-label="avatar">
      {long && <rect x="19" y="30" width="62" height="64" rx="26" fill={hairColor} />}
      <path d="M18 120 C18 92 82 92 82 120 Z" fill={outfit} />
      <rect x="43" y="68" width="14" height="14" fill={skin} />
      <circle cx="50" cy="50" r="24" fill={skin} />
      {bumps.map(([cx, cy, r], i) => <circle key={i} cx={cx} cy={cy} r={r} fill={hairColor} />)}
      <path d="M25 48 C24 24 76 24 75 48 C70 38 62 34 50 34 C38 34 30 38 25 48 Z" fill={hairColor} />
      <circle cx="41" cy="52" r="3" fill="#222" />
      <circle cx="59" cy="52" r="3" fill="#222" />
      <path d="M42 62 Q50 69 58 62" stroke="#7a3b1d" strokeWidth="2.2" fill="none" strokeLinecap="round" />
      {facial === 'moustache' && <path d="M40 59 Q45 55 50 58 Q55 55 60 59 Q55 61 50 60 Q45 61 40 59 Z" fill={hairColor} />}
      {facial === 'beard' && <path d="M29 58 Q32 82 50 82 Q68 82 71 58 Q66 70 50 70 Q34 70 29 58 Z" fill={hairColor} />}
    </svg>
  );
}
