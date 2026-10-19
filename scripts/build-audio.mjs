// Pre-generates MP3 speech for every English word/sentence in content/units.json with Azure Speech.
//   AZURE_SPEECH_KEY=... AZURE_SPEECH_REGION=southeastasia node scripts/build-audio.mjs
//   node scripts/build-audio.mjs --dry        # list texts + character count, no key needed
//   node scripts/build-audio.mjs --voices     # list en-GB voices available to your key
// Output: public/audio/<hash>.mp3 and public/audio/manifest.json ({ "normalized text": "<hash>.mp3" }).
// Existing files are reused, so re-running only pays for new/changed texts (free tier: 0.5M chars/month).
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const outDir = join(root, 'public/audio');
const args = new Set(process.argv.slice(2));

const KEY = process.env.AZURE_SPEECH_KEY;
const REGION = process.env.AZURE_SPEECH_REGION || 'southeastasia';
const VOICE = process.env.AZURE_VOICE || 'en-GB-MaisieNeural'; // British child voice
const RATE = process.env.AZURE_RATE || '-25%'; // slow and clear
const PITCH = process.env.AZURE_PITCH || '0%';
const ENDPOINT = process.env.AZURE_TTS_ENDPOINT || `https://${REGION}.tts.speech.microsoft.com/cognitiveservices/v1`;
const VOICES_URL = process.env.AZURE_VOICES_ENDPOINT || `https://${REGION}.tts.speech.microsoft.com/cognitiveservices/voices/list`;

// must match normalize() in src/lib/tts.ts
const normalize = (t) => t.trim().toLowerCase().replace(/\s+/g, ' ');

function collectTexts() {
  const book = JSON.parse(readFileSync(join(root, 'content/units.json'), 'utf8'));
  const set = new Map();
  const add = (t) => {
    if (!t || t.includes('...')) return;
    set.set(normalize(t), t.trim());
  };
  for (const lessons of Object.values(book.units)) {
    for (const l of lessons) {
      for (const g of l.groups ?? []) g.words.forEach(add);
      (l.sentences ?? []).forEach(add);
      for (const qa of l.qa ?? []) { add(qa.q); add(qa.a); }
    }
  }
  return set;
}

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const ssml = (text) =>
  `<speak version="1.0" xml:lang="en-GB" xmlns="http://www.w3.org/2001/10/synthesis"><voice name="${VOICE}"><prosody rate="${RATE}" pitch="${PITCH}">${esc(text)}</prosody></voice></speak>`;
const fileFor = (norm) => createHash('sha1').update(`${VOICE}|${RATE}|${PITCH}|${norm}`).digest('hex').slice(0, 14) + '.mp3';

async function listVoices() {
  const r = await fetch(VOICES_URL, { headers: { 'Ocp-Apim-Subscription-Key': KEY } });
  if (!r.ok) throw new Error(`voices list failed: ${r.status} ${await r.text()}`);
  return (await r.json()).filter((v) => v.Locale === 'en-GB');
}

async function synth(text) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    const r = await fetch(ENDPOINT, {
      method: 'POST',
      headers: {
        'Ocp-Apim-Subscription-Key': KEY,
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3',
        'User-Agent': 'risegamep4-audio',
      },
      body: ssml(text),
    });
    if (r.ok) return Buffer.from(await r.arrayBuffer());
    if (r.status === 429 || r.status >= 500) { await new Promise((res) => setTimeout(res, 1500 * attempt)); continue; }
    throw new Error(`Azure TTS ${r.status} for "${text}": ${await r.text()}`);
  }
  throw new Error(`Azure TTS kept failing for "${text}"`);
}

const texts = collectTexts();
const chars = [...texts.values()].reduce((n, t) => n + t.length, 0);
console.log(`${texts.size} texts, ${chars} characters (voice ${VOICE}, rate ${RATE}, region ${REGION})`);

if (args.has('--dry')) {
  for (const t of texts.values()) console.log(' -', t);
  process.exit(0);
}
if (!KEY) {
  console.error('Missing AZURE_SPEECH_KEY (see README: เสียงจาก Azure).');
  process.exit(1);
}
if (args.has('--voices')) {
  for (const v of await listVoices()) console.log(`${v.ShortName}\t${v.Gender}\t${(v.VoiceType || '')}\t${v.StyleList ? v.StyleList.join(',') : ''}`);
  process.exit(0);
}

const voices = await listVoices().catch((e) => { console.warn('could not verify voice:', e.message); return null; });
if (voices && !voices.some((v) => v.ShortName === VOICE)) {
  console.error(`Voice ${VOICE} is not available. en-GB voices: ${voices.map((v) => v.ShortName).join(', ')}\nSet AZURE_VOICE to one of them.`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
const manifest = {};
let made = 0;
for (const [norm, text] of texts) {
  const file = fileFor(norm);
  manifest[norm] = file;
  if (existsSync(join(outDir, file))) continue;
  writeFileSync(join(outDir, file), await synth(text));
  made++;
  if (made % 20 === 0) console.log(`  generated ${made}…`);
}
writeFileSync(join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 1) + '\n');
console.log(`done: ${made} new files, ${texts.size - made} reused → public/audio/`);
