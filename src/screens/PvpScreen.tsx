import { Suspense, lazy, useCallback, useEffect, useMemo, useState } from 'react';
import { rpc, supabase, errorText } from '../lib/supabase';
import { STAT_BASE, STAT_PER_STAR, statValue, totalStars } from '../lib/util';
import type { DuelEvent, DuelStats, MatchRow } from '../lib/types';
import { useGame } from '../state/GameContext';
import { Bar } from '../components/Hud';
import { PETS, isFantasyPet } from '../world3d/pets';

const DuelArena3D = lazy(() => import('../world3d/DuelArena3D'));

const ATTACK_MS = 1300;
const POWER_MS = 3000;

// Replay of an automatic duel. The server has already played it (see supabase/migrations/0005 and 0006);
// this walks through the log: one action at a time, the 3D pets cast their powers and the bars follow.
export function PvpScreen({ onExit }: { onExit: () => void }) {
  const { character, pet, progress, say, refresh } = useGame();
  const [match, setMatch] = useState<MatchRow | null>(null);
  const [busy, setBusy] = useState(false);
  const [shown, setShown] = useState(0);
  const [replayId, setReplayId] = useState<string | null>(null);
  const me = character?.id;

  const load = useCallback(async (id: string) => {
    const { data } = await supabase.from('pvp_matches').select('*').eq('id', id);
    setMatch((data?.[0] as MatchRow | undefined) ?? null);
  }, []);

  // a finished match starts its replay once
  useEffect(() => {
    if (match?.status === 'finished' && match.log.length > 0 && replayId !== match.id) { setReplayId(match.id); setShown(0); }
  }, [match, replayId]);
  const log: DuelEvent[] = useMemo(() => (match?.status === 'finished' ? match.log : []), [match]);
  const replaying = !!match && replayId === match.id;
  useEffect(() => {
    if (!replaying || shown >= log.length) return;
    const t = window.setTimeout(() => setShown((n) => n + 1), shown === 0 ? 700 : (log[shown - 1].kind === 'power' ? POWER_MS : ATTACK_MS));
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [replaying, shown, log.length]);

  async function call<T>(fn: string, args: Record<string, unknown>): Promise<T | undefined> {
    setBusy(true);
    try {
      return (await rpc(fn, args)) as T;
    } catch (e) {
      say(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function find() {
    const id = await call<string>('pvp_find_match', {});
    if (id) await load(id);
  }
  async function back() {
    await refresh();
    setMatch(null);
    setReplayId(null);
    onExit();
  }

  const myStars = totalStars(progress);
  const myStat = statValue(myStars);

  if (!match) {
    return (
      <section className="card center">
        <h2>⚔️ ลานประลอง 1v1</h2>
        <p>จับคู่ทันที ไม่ต้องรอ — สู้กับสัตว์เลี้ยงของผู้เล่นคนอื่น (ไม่ต้องออนไลน์) และสัตว์เลี้ยงสู้กันเอง ไม่ต้องกดอะไร สเตตัสมาจากดาวที่สะสมในบทเรียน</p>
        {pet && (
          <div className="status-card">
            <div className="mini-bars">
              <Bar value={pet.hp} max={pet.max_hp} kind="hp" />
              <Bar value={pet.mana} max={pet.max_mana} kind="mana" />
            </div>
            <div className="stat-row">
              <span>⭐ ดาว <b>{myStars}</b></span>
              <span>⚔️ ATK <b>{myStat}</b></span>
              <span>💨 SPD <b>{myStat}</b></span>
              <span>🛡️ DEF <b>{myStat}</b></span>
            </div>
            <p className="muted small">สเตตัสแต่ละตัว = {STAT_BASE} + {STAT_PER_STAR} ต่อ 1 ดาว · SPD สูง = ได้ลงมือบ่อยกว่า · ท่าละ 10 Mana ออกเองแบบสุ่ม (ร่างปัจจุบันออกบ่อยสุด) · ไม่มีระบบธาตุ ไม่เสียสัตว์เลี้ยงเมื่อแพ้</p>
          </div>
        )}
        <p className="muted small">สัตว์เลี้ยงเริ่มดวลด้วยพลังที่เหลืออยู่ — พักที่แคมป์/โรงพยาบาล หรือใช้ไอเทมใน 🎒 เพื่อฟื้นฟูก่อนดวล (แพ้แล้ว HP ไม่ต่ำกว่า 25)</p>
        <p>ชนะ {character?.pvp_wins} · แพ้ {character?.pvp_losses}</p>
        <button className="btn big" disabled={busy} onClick={find}>เริ่มดวล</button>
        <button className="btn ghost" onClick={onExit}>กลับแผนที่</button>
      </section>
    );
  }
  // ---- replay of a finished duel
  const isP1 = match.p1 === me;
  const mine = isP1 ? 1 : 2, foe = isP1 ? 2 : 1;
  const side = (n: 1 | 2) => ({
    name: n === 1 ? match.p1_name : match.p2_name, icon: n === 1 ? match.p1_pet : match.p2_pet,
    species: n === 1 ? match.p1_species : match.p2_species, stage: n === 1 ? match.p1_stage : match.p2_stage,
    stats: (n === 1 ? match.p1_stats : match.p2_stats) as DuelStats | null,
  });
  const L = side(mine), R = side(foe);
  const last = shown > 0 ? log[shown - 1] : null;
  const hp = (n: 1 | 2) => last ? (n === 1 ? last.hp1 : last.hp2) : (n === 1 ? match.p1_stats?.hp0 : match.p2_stats?.hp0) ?? 100;
  const mana = (n: 1 | 2) => last ? (n === 1 ? last.mana1 : last.mana2) : (n === 1 ? match.p1_stats?.mana0 : match.p2_stats?.mana0) ?? 0;
  const finished = shown >= log.length;
  const won = match.winner === me;
  const loserSide: 1 | 2 | null = finished ? (match.winner === match.p1 ? 2 : 1) : null;
  const toArena = (n: 1 | 2): 1 | 2 => (n === mine ? 1 : 2);
  const cue = last ? { key: shown, by: toArena(last.by), kind: last.kind, form: last.form } : null;
  const arena = isFantasyPet(L.species) && isFantasyPet(R.species);
  const describe = (e: DuelEvent) => {
    const who = side(e.by).name, sp = side(e.by).species;
    const power = e.kind === 'power' && e.form && isFantasyPet(sp) ? PETS[sp].forms[e.form - 1] : null;
    return `${who}: ${e.kind === 'power' ? `⚡ ${power ? `${power.power_th} (${power.power_en})` : 'ใช้ทักษะ'}` : '⚔️ โจมตี'} −${e.dmg}`;
  };

  const fighter = (s: ReturnType<typeof side>, who: 1 | 2) => (
    <div className={`fighter ${last && last.by === who ? 'active' : ''}`}>
      <div className="fighter-pet">{s.icon}</div>
      <b>{s.name}</b> <small>ร่าง {s.stage}</small>
      <div className="bar hp"><div style={{ width: `${(hp(who) / (s.stats?.max_hp ?? 100)) * 100}%` }} /><span>❤️ {hp(who)}</span></div>
      <div className="bar mana"><div style={{ width: `${(mana(who) / (s.stats?.max_mana ?? 40)) * 100}%` }} /><span>💧 {mana(who)}</span></div>
    </div>
  );

  return (
    <section className="card pvp">
      <div className="arena">{fighter(L, mine)}<span className="vs">VS</span>{fighter(R, foe)}</div>
      {arena && (
        <Suspense fallback={<div className="showcase-loading" style={{ height: 300 }}>กำลังโหลดสนามดวล 3D…</div>}>
          <div className="arena3d">
            <DuelArena3D left={{ species: L.species!, stage: L.stage }} right={{ species: R.species!, stage: R.stage }} cue={cue} loser={loserSide === null ? null : toArena(loserSide)} height={320} />
            {last && !finished && <span key={shown} className={`hit-float ${toArena(last.by) === 1 ? 'to-right' : 'to-left'}`}>−{last.dmg}</span>}
          </div>
        </Suspense>
      )}
      {!finished ? (
        <div className="row">
          <p className="turn wait">{last ? describe(last) : 'เตรียมตัว… ⏳'}</p>
          <button className="btn ghost" onClick={() => setShown(log.length)}>⏩ ข้ามไปผลลัพธ์</button>
        </div>
      ) : (
        <div className="center">
          <h2>{won ? '🏆 คุณชนะ!' : '💪 แพ้แล้ว ไม่เป็นไร'}</h2>
          <p>{won ? '+8' : '+2'} 🪙 · สัตว์เลี้ยงและความคืบหน้าของคุณยังอยู่ครบ · ทำบทเรียนให้ได้ดาวเพิ่มเพื่อเพิ่มสเตตัส</p>
          <button className="btn big" onClick={back}>กลับล็อบบี้</button>
          <button className="btn ghost" onClick={() => setShown(0)}>↻ ดูซ้ำ</button>
        </div>
      )}
      <ul className="log">
        {log.slice(0, shown).reverse().slice(0, 6).map((e) => <li key={e.n}>{describe(e)}</li>)}
      </ul>
    </section>
  );
}
