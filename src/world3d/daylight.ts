import * as THREE from 'three';

// The sky and the light follow the clock of the player's device: morning, day, sunset and night, with a smooth change
// between them. Each look gives the sky dome's colours (by height above the horizon; the fog and the far sea take the
// horizon's), the clouds' tint, the sea, the sun (or moon) as a light, the ambient and sky light, and which of the sun,
// moon and stars show. Add ?time=morning|day|sunset|night to the address to see one whatever the clock says. The button in the world picks
// auto (the clock), always day or always night.

export type DayPhase = 'morning' | 'day' | 'sunset' | 'night';

export interface Look {
  sky: [number, string][]; // sine of the elevation -> colour, from straight down to straight up
  clouds: string;
  sea: string;
  sun: [string, string]; // the sun's core and rim
  light: { dir: [number, number, number]; color: string; intensity: number };
  ambient: [string, number];
  hemi: [string, string, number]; // sky colour, ground colour, intensity
  sunOn: number;
  moonOn: number;
  starsOn: number;
}

export const LOOKS: Record<DayPhase, Look> = {
  morning: {
    sky: [[-1, '#9cc4dc'], [-0.03, '#ffe0c4'], [0, '#ffdcbc'], [0.05, '#ffe9d2'], [0.14, '#d3e8f4'], [0.35, '#a2d0f1'], [1, '#6db0ea']],
    clouds: '#fff0e2', sea: '#35b2da', sun: ['#fff8e2', '#ffdca0'],
    light: { dir: [24, 12, 12], color: '#ffd6a6', intensity: 1.8 },
    ambient: ['#fff2e4', 1.05], hemi: ['#ffe8d2', '#8bc26a', 0.55],
    sunOn: 1, moonOn: 0, starsOn: 0,
  },
  day: {
    sky: [[-1, '#7cc0ea'], [-0.03, '#c4ebff'], [0, '#cdeeff'], [0.04, '#a9ddff'], [0.12, '#82c8fa'], [0.3, '#5cb1f2'], [0.6, '#4a9fea'], [1, '#3a8ee2']],
    clouds: '#ffffff', sea: '#26b0e3', sun: ['#fffef4', '#fff1b8'],
    light: { dir: [14, 24, 10], color: '#ffffff', intensity: 2.0 },
    ambient: ['#ffffff', 1.15], hemi: ['#dff3ff', '#8bc26a', 0.6],
    sunOn: 1, moonOn: 0, starsOn: 0,
  },
  sunset: {
    sky: [[-1, '#5d5f98'], [-0.03, '#ffb07a'], [0, '#ffa46c'], [0.05, '#ff8e6c'], [0.14, '#e47a92'], [0.3, '#a46ca8'], [0.6, '#5e5c9e'], [1, '#3c4688']],
    clouds: '#ffb39a', sea: '#3a86b8', sun: ['#fff1d4', '#ffb066'],
    light: { dir: [-24, 10, 10], color: '#ff9f66', intensity: 1.7 },
    ambient: ['#ffd8c4', 0.95], hemi: ['#ffc0a2', '#6f8f58', 0.55],
    sunOn: 1, moonOn: 0, starsOn: 0.15,
  },
  night: {
    sky: [[-1, '#0d1633'], [-0.03, '#22335f'], [0, '#283b6c'], [0.08, '#1d2c58'], [0.3, '#142047'], [1, '#0b1335']],
    clouds: '#48567f', sea: '#183c68', sun: ['#fffef4', '#fff1b8'],
    light: { dir: [-9, 16.5, -23.4], color: '#c4d2ff', intensity: 1.2 },
    ambient: ['#b2c2f0', 1.0], hemi: ['#8299dc', '#3a4d58', 0.7],
    sunOn: 0, moonOn: 1, starsOn: 1,
  },
};

/** The player's choice: follow the device clock, or keep it day or night. Remembered on this device. */
export type DayMode = 'auto' | 'day' | 'night';

export function getDayMode(): DayMode {
  try {
    const v = localStorage.getItem('dayMode');
    return v === 'day' || v === 'night' ? v : 'auto';
  } catch { return 'auto'; }
}

export function setDayMode(mode: DayMode) {
  try { localStorage.setItem('dayMode', mode); } catch { /* ignore */ }
  daylight.go(phaseAt()); // blends over a few seconds
}

export function phaseAt(d = new Date()): DayPhase {
  const force = new URLSearchParams(window.location.search).get('time');
  if (force && force in LOOKS) return force as DayPhase;
  const mode = getDayMode();
  if (mode !== 'auto') return mode;
  const h = d.getHours() + d.getMinutes() / 60;
  return h >= 5 && h < 9 ? 'morning' : h >= 9 && h < 16 ? 'day' : h >= 16 && h < 19 ? 'sunset' : 'night';
}

const ramp = (stops: [number, string][], y: number, out: THREE.Color, tmp: THREE.Color) => {
  for (let i = 1; i < stops.length; i++) {
    if (y <= stops[i][0] || i === stops.length - 1) {
      const [y0, c0] = stops[i - 1], [y1, c1] = stops[i];
      return out.set(c0).lerp(tmp.set(c1), Math.max(0, Math.min(1, (y - y0) / (y1 - y0))));
    }
  }
  return out.set(stops[stops.length - 1][1]);
};

const T1 = new THREE.Color(), T2 = new THREE.Color(), T3 = new THREE.Color(), V1 = new THREE.Vector3();

/** The current look: blends from one phase's look to the next over CHANGE seconds. version counts every change. */
export class Daylight {
  static CHANGE = 4;
  from: Look;
  to: Look;
  t = 1;
  version = 1;

  constructor(phase: DayPhase) {
    this.from = this.to = LOOKS[phase];
  }

  go(phase: DayPhase) {
    const next = LOOKS[phase];
    if (next === this.to) return;
    this.from = this.to;
    this.to = next;
    this.t = 0;
  }

  step(dt: number) {
    if (this.t >= 1) return;
    this.t = Math.min(1, this.t + dt / Daylight.CHANGE);
    this.version++;
  }

  private get k() {
    return this.t * this.t * (3 - 2 * this.t);
  }

  color(pick: (l: Look) => string, out: THREE.Color) {
    return out.set(pick(this.from)).lerp(T1.set(pick(this.to)), this.k);
  }

  num(pick: (l: Look) => number) {
    const a = pick(this.from);
    return a + (pick(this.to) - a) * this.k;
  }

  /** Sky colour at the given sine of the elevation (0 is the horizon, which the fog matches). */
  sky(y: number, out: THREE.Color) {
    ramp(this.from.sky, y, out, T2);
    return out.lerp(ramp(this.to.sky, y, T3, T2), this.k);
  }

  /** Unit vector towards the light: the sun, or the moon at night. */
  lightDir(out: THREE.Vector3) {
    return out.fromArray(this.from.light.dir).normalize().lerp(V1.fromArray(this.to.light.dir).normalize(), this.k).normalize();
  }

  /** Unit vector towards where the sun disc is drawn (it does not follow the light over to the moon at dusk). */
  sunDir(out: THREE.Vector3) {
    const a = this.from.sunOn > 0 ? this.from : this.to, b = this.to.sunOn > 0 ? this.to : this.from;
    return out.fromArray(a.light.dir).normalize().lerp(V1.fromArray(b.light.dir).normalize(), this.k).normalize();
  }
}

// One for the whole visit, so going back to the world does not replay the change.
export const daylight = new Daylight(phaseAt());
