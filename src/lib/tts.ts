// Reads English aloud with the browser's built-in speech synthesis.
export function speak(text: string) {
  if (!('speechSynthesis' in window) || !text) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'en-US';
  u.rate = 0.8;
  u.pitch = 1.1;
  window.speechSynthesis.speak(u);
}

export const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window;
