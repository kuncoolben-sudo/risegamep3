import type { Appearance, CharacterPreset } from '../lib/types';

// Concept-sheet characters (3D models char_<id>.glb). The colours only drive the 2D avatar; the 3D model keeps its own look.
export const PRESET_LOOKS: Record<CharacterPreset, { name: string; tagline: string; look: Omit<Appearance, 'preset'> }> = {
  kai: { name: 'Kai', tagline: 'The Brave Explorer', look: { skin: '#f1c9a0', hairLength: 'short', hairType: 'straight', hairColor: '#7a4423', facial: 'none', outfit: '#2f6fd6' } },
  pond: { name: 'Pond', tagline: 'The Smart Thinker', look: { skin: '#f4d2b0', hairLength: 'short', hairType: 'straight', hairColor: '#25211f', facial: 'none', outfit: '#4f9a5a' } },
  beam: { name: 'Beam', tagline: 'The Kind Leader', look: { skin: '#f1c9a0', hairLength: 'short', hairType: 'straight', hairColor: '#c96b2c', facial: 'none', outfit: '#d63a2f' } },
  lily: { name: 'Lily', tagline: 'The Cheerful Dreamer', look: { skin: '#f6d6bd', hairLength: 'long', hairType: 'wavy', hairColor: '#7a4a2e', facial: 'none', outfit: '#f4a8c4' } },
  minnie: { name: 'Minnie', tagline: 'The Creative Artist', look: { skin: '#f6d6bd', hairLength: 'short', hairType: 'straight', hairColor: '#2e2230', facial: 'none', outfit: '#a58be0' } },
  maya: { name: 'Maya', tagline: 'The Nature Lover', look: { skin: '#f1c9a0', hairLength: 'long', hairType: 'straight', hairColor: '#c8481f', facial: 'none', outfit: '#5fa05a' } },
};

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
