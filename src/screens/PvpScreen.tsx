import { useCallback, useEffect, useMemo, useState } from 'react';
import { rpc, supabase, errorText } from '../lib/supabase';
import { speak, canSpeak } from '../lib/tts';
import { shuffled } from '../lib/util';
import type { MatchRow } from '../lib/types';
import { useGame } from '../state/GameContext';
import { Bar } from '../components/Hud';

const ACTIONS: { id: string; label: string; help: string }[] = [
  { id: 'attack', label: '⚔️ โจมตี', help: 'ไม่ใช้ Mana' },
  { id: 'skill', label: '⚡ ทักษะสัตว์เลี้ยง', help: 'Mana 10 · ต้องระดับ 2' },
  { id: 'guard', label: '🛡️ ป้องกัน', help: 'ลดดาเมจครั้งถัดไปครึ่งหนึ่ง' },
  { id: 'focus', label: '🧘 รวบรวมสมาธิ', help: '+Mana +5 HP' },
];
const ACTION_NAME: Record<string, string> = { attack: 'โจมตี', skill: 'ใช้ทักษะ', guard: 'ป้องกัน', focus: 'รวบรวมสมาธิ' };

export function PvpScreen({ onExit }: { onExit: () => void }) {
  const { character, say, refresh } = useGame();
  const [match, setMatch] = useState<MatchRow | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [now, setNow] = useState(Date.now());
  const me = character?.id;

  const load = useCallback(async (id?: string) => {
    let q = supabase.from('pvp_matches').select('*');
    q = id ? q.eq('id', id) : q.in('status', ['waiting', 'active']).order('created_at', { ascending: false }).limit(1);
    const { data } = await q;
    setMatch((data?.[0] as MatchRow | undefined) ?? null);
  }, []);

  useEffect(() => { load(); }, [load]);

  const matchId = match?.id;
  useEffect(() => {
    if (!matchId) return;
    const ch = supabase
      .channel(`match-${matchId}`)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'pvp_matches', filter: `id=eq.${matchId}` }, (p) => {
        if (p.eventType === 'DELETE') setMatch(null);
        else setMatch(p.new as MatchRow);
      })
      .subscribe();
    // polling keeps the game moving if realtime is not enabled for the table
    const t = window.setInterval(() => { load(matchId); setNow(Date.now()); }, 3000);
    return () => { supabase.removeChannel(ch); window.clearInterval(t); };
  }, [matchId, load]);

  const round = match?.round;
  useEffect(() => { setAnswer(null); }, [round]);

  const isP1 = match?.p1 === me;
  const choices = useMemo(() => shuffled(match?.q_choices ?? []), [match?.round, match?.id]);
  const myTurn = match?.status === 'active' && match.turn === me;
  useEffect(() => { if (myTurn && match?.q_say) speak(match.q_say); }, [myTurn, match?.round]); // eslint-disable-line react-hooks/exhaustive-deps

  async function call(fn: string, args: Record<string, unknown>) {
    setBusy(true);
    try {
      return await rpc(fn, args);
    } catch (e) {
      say(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function find() {
    const id = (await call('pvp_find_match', {})) as string | undefined;
    if (id) await load(id);
  }
  async function act(action: string) {
    if (!match) return;
    await call('pvp_act', { p_match: match.id, p_action: action, p_answer: answer });
    await load(match.id);
  }
  async function leave() {
    if (match?.status === 'waiting') await call('pvp_cancel', { p_match: match.id });
    else if (match?.status === 'active') await call('pvp_forfeit', { p_match: match.id });
    await refresh();
    onExit();
  }

  const fighter = (name: string | null, pet: string | null, hp: number, mana: number, guard: boolean, stage: number, active: boolean) => (
    <div className={`fighter ${active ? 'active' : ''}`}>
      <div className="fighter-pet">{pet}{guard && <span className="shield">🛡️</span>}</div>
      <b>{name}</b> <small>Lv.{stage}</small>
      <div className="bar hp"><div style={{ width: `${hp}%` }} /><span>❤️ {hp}</span></div>
      <div className="bar mana"><div style={{ width: `${(mana / 40) * 100}%` }} /><span>💧 {mana}</span></div>
    </div>
  );

  if (!match) {
    return (
      <section className="card center">
        <h2>⚔️ ลานประลอง 1v1</h2>
        <p>ดวลกับผู้เล่นอีกคนแบบผลัดกันเล่น ตอบคำถามภาษาอังกฤษถูกเพื่อเพิ่มพลังโจมตี</p>
        <p className="muted">HP/Mana ใช้ในการดวลเท่านั้น (ทำบทเรียนไม่เสียพลัง) ไม่มีระบบธาตุ ไม่เสียสัตว์เลี้ยงเมื่อแพ้</p>
        {character && (
          <div className="mini-bars">
            <Bar value={character.hp} max={character.max_hp} kind="hp" />
            <Bar value={character.mana} max={character.max_mana} kind="mana" />
          </div>
        )}
        <p className="muted small">เริ่มดวลด้วยพลังที่เหลืออยู่ — พักที่แคมป์/โรงเตี๊ยม หรือใช้ไอเทมใน 🎒 เพื่อฟื้นฟูก่อนดวล (แพ้แล้ว HP ไม่ต่ำกว่า 25)</p>
        <p>ชนะ {character?.pvp_wins} · แพ้ {character?.pvp_losses}</p>
        <button className="btn big" disabled={busy} onClick={find}>หาคู่ต่อสู้</button>
        <button className="btn ghost" onClick={onExit}>กลับแผนที่</button>
      </section>
    );
  }
  if (match.status === 'waiting') {
    return (
      <section className="card center">
        <h2>🔎 กำลังหาคู่ต่อสู้…</h2>
        <p className="muted">เปิดเกมอีกเครื่องหนึ่งแล้วกด "หาคู่ต่อสู้" เพื่อทดสอบได้</p>
        <button className="btn ghost" onClick={leave}>ยกเลิก</button>
      </section>
    );
  }

  const p1 = fighter(match.p1_name, match.p1_pet, match.p1_hp, match.p1_mana, match.p1_guard, match.p1_stage, match.turn === match.p1);
  const p2 = fighter(match.p2_name, match.p2_pet, match.p2_hp, match.p2_mana, match.p2_guard, match.p2_stage, match.turn === match.p2);
  const idleMs = now - new Date(match.updated_at).getTime();

  if (match.status === 'finished') {
    const won = match.winner === me;
    return (
      <section className="card center">
        <h2>{won ? '🏆 คุณชนะ!' : '💪 แพ้แล้ว ไม่เป็นไร'}</h2>
        <div className="arena">{p1}{p2}</div>
        <p>{won ? '+8' : '+2'} 🪙 · สัตว์เลี้ยงและความคืบหน้าของคุณยังอยู่ครบ</p>
        <button className="btn big" onClick={async () => { await refresh(); setMatch(null); }}>กลับล็อบบี้</button>
      </section>
    );
  }

  const myStage = isP1 ? match.p1_stage : match.p2_stage;
  const myMana = isP1 ? match.p1_mana : match.p2_mana;
  return (
    <section className="card pvp">
      <div className="arena">{p1}<span className="vs">VS</span>{p2}</div>
      {myTurn ? (
        <>
          <p className="turn">ตาของคุณ — รอบที่ {match.round}</p>
          <div className="prompt">
            {canSpeak && <button className="btn round" onClick={() => speak(match.q_say ?? '')}>🔊</button>}
            <span className="q">{match.q_prompt === 'Listen and choose' ? 'Listen and choose' : match.q_prompt}</span>
          </div>
          <div className="choices">
            {choices.map((c) => <button key={c} className={`choice ${answer === c ? 'picked' : ''}`} onClick={() => setAnswer(c)}>{c}</button>)}
          </div>
          <p className="muted small">ตอบถูกจะเพิ่มพลัง ตอบผิดหรือไม่ตอบพลังจะลดลง (แต่ยังเล่นต่อได้)</p>
          <div className="actions">
            {ACTIONS.map((a) => (
              <button key={a.id} className="btn" disabled={busy || (a.id === 'skill' && (myStage < 2 || myMana < 10))} onClick={() => act(a.id)}>
                {a.label}<small>{a.help}</small>
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <p className="turn wait">รอคู่ต่อสู้เลือก… ⏳</p>
          {idleMs > 90_000 && <button className="btn" onClick={async () => { await call('pvp_claim_timeout', { p_match: match.id }); await load(match.id); }}>คู่ต่อสู้หายไป — รับชัยชนะ</button>}
        </>
      )}
      <ul className="log">
        {[...match.log].reverse().slice(0, 6).map((l, k) => (
          <li key={k}>{l.actor}: {ACTION_NAME[l.action]}{l.damage ? ` (${l.damage} ดาเมจ)` : ''} {l.correct ? '✔' : '✖'}</li>
        ))}
      </ul>
      <button className="btn ghost" onClick={leave}>ยอมแพ้และออก</button>
    </section>
  );
}
