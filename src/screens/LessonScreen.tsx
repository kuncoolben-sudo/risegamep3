import { useEffect, useMemo, useState } from 'react';
import { rpc, supabase, errorText } from '../lib/supabase';
import { canSpeak, speak } from '../lib/tts';
import { shuffled } from '../lib/util';
import type { ActivityRow, LessonResult } from '../lib/types';
import { useGame } from '../state/GameContext';

const HINT_COST = 3;
const WRONG_COST = 5;

interface ActProps {
  a: ActivityRow;
  canHint: boolean;
  onWrong: () => void;
  onHint: () => void;
  onDone: (firstTry: boolean, note?: string) => void;
}

function Speaker({ text }: { text?: string }) {
  if (!canSpeak || !text) return null;
  return <button className="btn round" onClick={() => speak(text)} aria-label="ฟังเสียง">🔊</button>;
}

function Choice({ a, canHint, onWrong, onHint, onDone }: ActProps) {
  const choices = useMemo(() => shuffled(a.payload.choices ?? []), [a.id]);
  const [bad, setBad] = useState<Set<string>>(new Set());
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [ok, setOk] = useState(false);
  useEffect(() => speak(a.payload.say ?? ''), [a.id]);
  const answer = a.payload.answer!;

  function pick(c: string) {
    if (ok) return;
    if (c === answer) {
      setOk(true);
      speak(answer);
    } else {
      setBad(new Set(bad).add(c));
      onWrong();
    }
  }
  function hint() {
    const wrongs = choices.filter((c) => c !== answer && !hidden.has(c) && !bad.has(c));
    if (wrongs.length < 2) return;
    onHint();
    setHidden(new Set([...hidden, ...wrongs.slice(0, 2)]));
  }
  return (
    <div className="act">
      <h2>{a.type === 'qa_choose' ? 'Choose the answer' : 'Listen and choose'}</h2>
      <div className="prompt">
        <Speaker text={a.payload.say} />
        {a.type === 'qa_choose' && <span className="q">{a.payload.question}</span>}
      </div>
      <div className="choices">
        {choices.map((c) => (
          <button key={c} disabled={hidden.has(c)} className={`choice ${ok && c === answer ? 'right' : ''} ${bad.has(c) ? 'wrong' : ''}`} onClick={() => pick(c)}>{c}</button>
        ))}
      </div>
      <div className="act-foot">
        <button className="btn ghost" disabled={ok || !canHint} onClick={hint}>💡 คำใบ้ (−{HINT_COST} Mana)</button>
        {ok && <button className="btn" onClick={() => onDone(bad.size === 0 && hidden.size === 0)}>ถัดไป ➜</button>}
      </div>
      {ok && <p className="good">✔ Correct!</p>}
    </div>
  );
}

// spell (letters) and sentence_order (words) share one tap-in-order mechanic
function Sequence({ a, canHint, onWrong, onHint, onDone }: ActProps) {
  const spell = a.type === 'spell';
  const answer = a.payload.answer!;
  const units = useMemo(() => (spell ? answer.split('') : answer.split(/\s+/)), [a.id]);
  const tiles = useMemo(() => shuffled(units.map((t, i) => ({ t, i }))), [a.id]);
  const [used, setUsed] = useState<number[]>([]);
  const [placed, setPlaced] = useState<string[]>([]);
  const [slip, setSlip] = useState(false);
  const [hinted, setHinted] = useState(false);
  const [mistake, setMistake] = useState(false);
  const done = placed.length === units.length;
  useEffect(() => speak(a.payload.say ?? ''), [a.id]);

  function place(tileIdx: number) {
    if (done || used.includes(tileIdx)) return;
    const tile = tiles[tileIdx];
    if (tile.t === units[placed.length]) {
      setUsed([...used, tileIdx]);
      setPlaced([...placed, tile.t]);
      if (placed.length + 1 === units.length) speak(answer);
    } else {
      setSlip(true);
      setMistake(true);
      onWrong();
      window.setTimeout(() => setSlip(false), 350);
    }
  }
  function hint() {
    const want = units[placed.length];
    const idx = tiles.findIndex((t, k) => t.t === want && !used.includes(k));
    if (idx < 0) return;
    onHint();
    setHinted(true);
    place(idx);
  }
  return (
    <div className="act">
      <h2>{spell ? 'Listen and spell' : 'Put the words in order'}</h2>
      <div className="prompt"><Speaker text={a.payload.say} /><span className="muted">{spell ? 'ฟังแล้วเรียงตัวอักษร' : 'ฟังแล้วเรียงคำให้เป็นประโยค'}</span></div>
      <div className={`slots ${slip ? 'shake' : ''}`}>
        {units.map((_, k) => <span key={k} className={`slot ${placed[k] ? 'filled' : ''}`}>{placed[k] ?? ''}</span>)}
      </div>
      <div className="tiles">
        {tiles.map((tile, k) => (
          <button key={k} className="tile" disabled={used.includes(k)} onClick={() => place(k)}>{tile.t}</button>
        ))}
      </div>
      <div className="act-foot">
        <button className="btn ghost" disabled={done || !canHint} onClick={hint}>💡 คำใบ้ (−{HINT_COST} Mana)</button>
        {done && <button className="btn" onClick={() => onDone(!mistake && !hinted)}>ถัดไป ➜</button>}
      </div>
      {done && <p className="good">✔ {answer}</p>}
    </div>
  );
}

function ProjectAct({ a, onDone }: ActProps) {
  const [note, setNote] = useState('');
  const [checked, setChecked] = useState(false);
  return (
    <div className="act">
      <h2>Project Time</h2>
      <p className="q">{a.payload.title}</p>
      <p className="muted">ทำชิ้นงานตามหนังสือ (วาด/เขียนในสมุดหรือบนกระดาษ) แล้วจดบันทึกสั้น ๆ ไว้ที่นี่ได้</p>
      <textarea rows={4} maxLength={1000} value={note} onChange={(e) => setNote(e.target.value)} placeholder="บันทึกของฉัน (ไม่บังคับ)" />
      <label className="check"><input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} /> ฉันทำโครงงานเสร็จแล้ว</label>
      <div className="act-foot"><button className="btn" disabled={!checked} onClick={() => onDone(true, note.trim() || undefined)}>เสร็จสิ้น ✔</button></div>
    </div>
  );
}

export function LessonScreen({ lessonId, onExit, onLive }: { lessonId: string; onExit: () => void; onLive: (hp: number, mana: number) => void }) {
  const { lessons, character, refresh, locations, say } = useGame();
  const lesson = lessons.find((l) => l.id === lessonId);
  const [acts, setActs] = useState<ActivityRow[] | null>(null);
  const [i, setI] = useState(0);
  const [stats, setStats] = useState({ correct: 0, wrong: 0, hints: 0 });
  const [note, setNote] = useState<string | undefined>();
  const [result, setResult] = useState<LessonResult | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    supabase.from('activities').select('*').eq('lesson_id', lessonId).order('sort').then(({ data, error }) => {
      if (error) say(errorText(error));
      else setActs(data as ActivityRow[]);
    });
  }, [lessonId, say]);

  const hp = Math.max(1, (character?.hp ?? 1) - WRONG_COST * stats.wrong);
  const mana = Math.max(0, (character?.mana ?? 0) - HINT_COST * stats.hints);
  useEffect(() => onLive(hp, mana), [hp, mana, onLive]);

  async function finish(s: typeof stats, n?: string) {
    setSaving(true);
    try {
      const r = await rpc<LessonResult>('complete_lesson', {
        p_lesson: lessonId, p_correct: s.correct, p_total: acts!.length, p_wrong: s.wrong, p_hints: s.hints, p_note: n ?? null,
      });
      setResult(r);
      await refresh();
    } catch (e) {
      say(errorText(e));
      onExit();
    }
    setSaving(false);
  }

  if (!lesson || !acts) return <section className="card center"><p>กำลังโหลด…</p></section>;
  if (acts.length === 0) return <section className="card center"><p>บทนี้ยังไม่มีกิจกรรม</p><button className="btn" onClick={onExit}>กลับ</button></section>;

  if (result) {
    const names = result.new_unlocks.map((id) => locations.find((l) => l.id === id)?.name_en ?? id);
    return (
      <section className="card center result">
        <h2>{result.passed ? 'ผ่านแล้ว! 🎉' : 'ลองอีกครั้งนะ 💪'}</h2>
        <div className="big-stars">{[1, 2, 3].map((n) => (result.stars >= n ? '⭐' : '☆'))}</div>
        {result.passed && <p>🪙 +{result.coins_gained} เหรียญ</p>}
        {result.item_drop && <p>🍎 ได้ไอเทมใหม่!</p>}
        {result.evolved && <p className="badge">🐾 สัตว์เลี้ยงของคุณเติบโตเป็นระดับ {result.pet_stage}!</p>}
        {names.length > 0 && <p>🗺️ ปลดล็อก: <b>{names.join(', ')}</b></p>}
        {character && character.hp * 10 <= character.max_hp && <p className="notice">เหนื่อยแล้ว — ไปพักที่แคมป์หรือโรงเตี๊ยมกันเถอะ</p>}
        <button className="btn big" onClick={onExit}>กลับแผนที่</button>
      </section>
    );
  }

  const a = acts[i];
  const props: ActProps = {
    a,
    canHint: mana >= HINT_COST,
    onWrong: () => setStats((s) => ({ ...s, wrong: s.wrong + 1 })),
    onHint: () => setStats((s) => ({ ...s, hints: s.hints + 1 })),
    onDone: (firstTry, n) => {
      const next = { ...stats, correct: stats.correct + (firstTry ? 1 : 0) };
      setStats(next);
      if (n) setNote(n);
      if (i + 1 < acts.length) setI(i + 1);
      else finish(next, n ?? note);
    },
  };
  return (
    <section className="card lesson">
      <div className="lesson-top">
        <button className="btn ghost" onClick={onExit}>✕ ออก</button>
        <b>{lesson.title}</b>
        <span className="muted">{i + 1}/{acts.length}</span>
      </div>
      <div className="bar xp"><div style={{ width: `${(i / acts.length) * 100}%` }} /></div>
      {saving ? <p>กำลังบันทึก…</p> : a.type === 'project' ? <ProjectAct key={a.id} {...props} /> : a.type === 'spell' || a.type === 'sentence_order' ? <Sequence key={a.id} {...props} /> : <Choice key={a.id} {...props} />}
    </section>
  );
}
