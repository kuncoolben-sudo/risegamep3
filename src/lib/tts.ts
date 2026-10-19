// Reads English aloud. 1) plays the pre-generated Azure MP3 from public/audio (same voice on every
// device, built by scripts/build-audio.mjs); 2) otherwise uses the browser's speech synthesis with a
// British (en-GB) voice. It never falls back to the device's default voice, which may be Thai.
const hasSynth = typeof window !== 'undefined' && 'speechSynthesis' in window;
export const canSpeak = typeof window !== 'undefined' && (hasSynth || typeof Audio !== 'undefined');

// must match normalize() in scripts/build-audio.mjs
const normalize = (t: string) => t.trim().toLowerCase().replace(/\s+/g, ' ');

let manifest: Record<string, string> | null = null;
let manifestLoading: Promise<void> | null = null;
function loadManifest() {
  manifestLoading ??= fetch(`${import.meta.env.BASE_URL}audio/manifest.json`, { cache: 'no-cache' })
    .then((r) => (r.ok ? r.json() : {}))
    .then((m) => { manifest = m as Record<string, string>; })
    .catch(() => { manifest = {}; });
  return manifestLoading;
}

// one shared element: iOS only lets an element play after it was "unlocked" by a user gesture
let player: HTMLAudioElement | null = null;
if (typeof window !== 'undefined' && typeof Audio !== 'undefined') {
  loadManifest();
  player = new Audio();
  const unlock = () => {
    window.removeEventListener('pointerdown', unlock);
    if (!player) return;
    player.muted = true;
    player.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
    player.play().then(() => { player!.pause(); player!.muted = false; }).catch(() => { if (player) player.muted = false; });
  };
  window.addEventListener('pointerdown', unlock);
}

// en-GB voices on common platforms, lighter/female voices first: they suit a child-like tone best
// (iOS/macOS, Android/Chrome, Windows/Edge)
const PREFERRED = ['Kate', 'Serena', 'Martha', 'Google UK English Female', 'Microsoft Libby', 'Microsoft Sonia', 'Daniel', 'Oliver', 'Google UK English Male', 'Microsoft Ryan'];

let cached: SpeechSynthesisVoice | null | undefined;

function pickVoice(): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();
  if (voices.length === 0) return null;
  const lang = (v: SpeechSynthesisVoice) => v.lang.replace('_', '-').toLowerCase();
  const uk = voices.filter((v) => lang(v) === 'en-gb');
  for (const name of PREFERRED) {
    const hit = uk.find((v) => v.name.includes(name));
    if (hit) return hit;
  }
  if (uk.length) return uk[0];
  // no British voice installed: any other English voice is better than Thai
  return voices.find((v) => lang(v).startsWith('en')) ?? null;
}

if (hasSynth) {
  // voices load asynchronously in most browsers
  window.speechSynthesis.addEventListener?.('voiceschanged', () => { cached = undefined; });
}

export function speak(text: string) {
  if (!text) return;
  const file = manifest?.[normalize(text)];
  if (file && player) {
    if (hasSynth) window.speechSynthesis.cancel();
    player.src = `${import.meta.env.BASE_URL}audio/${file}`;
    player.currentTime = 0;
    player.play().catch(() => speakWithDevice(text)); // autoplay blocked or file missing
    return;
  }
  speakWithDevice(text);
}

function speakWithDevice(text: string) {
  if (!hasSynth) return;
  if (!cached) cached = pickVoice(); // retry until voices have loaded (iOS may not fire voiceschanged)
  if (player) player.pause();
  const voice = cached;
  const synth = window.speechSynthesis;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'en-GB';
  if (voice) {
    u.voice = voice;
    u.lang = voice.lang;
  } else if (synth.getVoices().length > 0) {
    return; // voices exist but none is English: stay silent rather than read English with a Thai voice
  }
  // slow and clear for young learners; raised pitch gives a friendly child-like tone
  const words = text.trim().split(/\s+/).length;
  u.rate = words <= 2 ? 0.6 : 0.68;
  u.pitch = 1.45;
  u.volume = 1;
  synth.cancel();
  synth.speak(u);
}
