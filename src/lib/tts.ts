// Reads English aloud with the browser's built-in speech synthesis, always with a British (en-GB)
// voice. It never falls back to the device's default voice, which may be Thai.
export const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window;

// Voices that sound good in en-GB on common platforms (iOS/macOS, Android/Chrome, Windows/Edge)
const PREFERRED = ['Daniel', 'Kate', 'Serena', 'Oliver', 'Google UK English Female', 'Google UK English Male', 'Microsoft Libby', 'Microsoft Sonia', 'Microsoft Ryan'];

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

if (canSpeak) {
  // voices load asynchronously in most browsers
  window.speechSynthesis.addEventListener?.('voiceschanged', () => { cached = undefined; });
}

export function speak(text: string) {
  if (!canSpeak || !text) return;
  if (!cached) cached = pickVoice(); // retry until voices have loaded (iOS may not fire voiceschanged)
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
  u.rate = 0.8;
  u.pitch = 1.05;
  synth.cancel();
  synth.speak(u);
}
