import { useMemo, useState } from 'react';
import { rpc, errorText } from '../lib/supabase';
import { useGame } from '../state/GameContext';
import type { LocationRow } from '../lib/types';

const TREES = [[40, 40], [180, 60], [300, 40], [450, 90], [560, 60], [700, 60], [900, 100], [960, 220], [940, 460], [980, 560], [820, 600],
  [700, 600], [560, 600], [330, 610], [200, 600], [30, 480], [40, 300], [260, 330], [420, 400], [560, 350], [690, 380], [400, 270], [880, 160]];

function pagesLabel(l: LocationRow) {
  return l.page_from ? `หน้า ${l.page_from}–${l.page_to}` : '';
}

export function MapScreen({ onPlay, onPvp }: { onPlay: (lessonId: string) => void; onPvp: () => void }) {
  const { locations, paths, lessons, items, states, character, progress, refresh, say } = useGame();
  const [sel, setSel] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const byId = useMemo(() => new Map(locations.map((l) => [l.id, l])), [locations]);
  const here = character?.location_id ?? 'start';
  const hereLoc = byId.get(here);
  const selected = sel ? byId.get(sel) : undefined;

  async function visit(l: LocationRow) {
    setSel(l.id);
    if (states[l.id] === 'locked') {
      say(`ยังไม่เปิด — ต้องผ่าน ${l.requires.map((r) => byId.get(r)?.name_en).join(', ')} ก่อน`);
      return;
    }
    if (here !== l.id) {
      setBusy(true);
      try {
        await rpc('travel', { p_loc: l.id });
        await refresh();
      } catch (e) {
        say(errorText(e));
      }
      setBusy(false);
    }
  }

  async function act(fn: string, args?: Record<string, unknown>, ok?: string) {
    setBusy(true);
    try {
      await rpc(fn, args);
      await refresh();
      if (ok) say(ok);
    } catch (e) {
      say(errorText(e));
    }
    setBusy(false);
  }

  const panel = () => {
    if (!selected) {
      // Main Quest: first unlocked location that still has a required lesson to clear
      const next = [...locations].sort((a, b) => a.requires.length - b.requires.length || a.x - b.x)
        .find((l) => states[l.id] === 'open' && l.kind === 'unit');
      const lesson = next && lessons.find((l) => l.location_id === next.id && l.required && !progress.has(l.id));
      return (
        <>
          {next && lesson && (
            <div className="quest">
              <b>❗ Main Quest</b>
              <p>{next.name_th}: {lesson.title}</p>
              <button className="btn" onClick={() => visit(next)}>ไปเลย ➜</button>
            </div>
          )}
          <p className="muted">แตะสถานที่บนแผนที่เพื่อเดินทาง</p>
        </>
      );
    }
    const st = states[selected.id];
    const here_ = here === selected.id;
    const header = (
      <div className="panel-head">
        <span className="big-emoji">{selected.icon}</span>
        <div>
          <h3>{selected.name_en}</h3>
          <div className="muted small">{selected.name_th} {pagesLabel(selected)}</div>
        </div>
        <button className="x" onClick={() => setSel(null)} aria-label="ปิด">✕</button>
      </div>
    );
    if (st === 'locked') return <>{header}<p>🔒 ยังไม่เปิด ต้องผ่าน: {selected.requires.map((r) => byId.get(r)?.name_en).join(', ')}</p></>;
    if (!here_) return <>{header}<p className="muted">กำลังเดินทาง…</p></>;
    if (selected.kind === 'pending')
      return <>{header}<p>{selected.blurb_th}</p><p className="notice">📖 เนื้อหาส่วนนี้ยังรอใส่จากหน้าหนังสือจริง — ภาพสารบัญระบุเฉพาะชื่อและเลขหน้า จึงยังไม่สร้างกิจกรรมขึ้นเอง</p></>;
    if (selected.kind === 'arena')
      return <>{header}<p>{selected.blurb_th}</p><button className="btn big" onClick={onPvp}>⚔️ เข้าสู่ลานประลอง</button></>;
    if (selected.kind === 'rest') {
      const inn = selected.rest_type === 'inn';
      return (
        <>
          {header}
          <p>{selected.blurb_th}</p>
          <button className="btn big" disabled={busy || (!inn && character?.rested_here)} onClick={() => act('rest', undefined, inn ? 'พักผ่อนจนเต็ม! 💤' : 'พักที่แคมป์แล้ว ✨')}>
            {inn ? ((character?.coins ?? 0) >= 3 ? '🛏️ พักจนเต็ม (3 🪙)' : '🛏️ พักจนเต็ม (ฟรี)') : character?.rested_here ? '⛺ พักแล้ว' : '⛺ พักที่แคมป์ (+40 HP, +15 Mana)'}
          </button>
          {inn && (
            <ul className="list">
              {items.map((i) => (
                <li key={i.id}>
                  <span className="big-emoji">{i.icon}</span>
                  <div><b>{i.name_en}</b><div className="muted small">{i.name_th}</div></div>
                  <button className="btn" disabled={busy || (character?.coins ?? 0) < i.price} onClick={() => act('buy_item', { p_item: i.id, p_qty: 1 }, `ซื้อ ${i.name_en} แล้ว`)}>{i.price} 🪙</button>
                </li>
              ))}
            </ul>
          )}
        </>
      );
    }
    const ls = lessons.filter((l) => l.location_id === selected.id);
    return (
      <>
        {header}
        <p>{selected.blurb_th}</p>
        <ul className="list">
          {ls.map((l) => {
            const p = progress.get(l.id);
            return (
              <li key={l.id}>
                <span className="stars">{[1, 2, 3].map((n) => (p && p.stars >= n ? '⭐' : '☆'))}</span>
                <div>
                  <b>{l.title}</b>
                  {!l.required && <span className="badge">ไม่บังคับ</span>}
                </div>
                <button className="btn" onClick={() => onPlay(l.id)}>{p ? 'เล่นอีกครั้ง' : 'เริ่ม'}</button>
              </li>
            );
          })}
        </ul>
      </>
    );
  };

  return (
    <div className="map-wrap">
      <div className="map">
        <svg viewBox="0 0 1000 660" role="img" aria-label="แผนที่โลก">
          <defs>
            <radialGradient id="grass" cx="50%" cy="50%" r="75%">
              <stop offset="0" stopColor="#b8e994" />
              <stop offset="1" stopColor="#78c850" />
            </radialGradient>
          </defs>
          <rect width="1000" height="660" rx="24" fill="url(#grass)" />
          {TREES.map(([x, y], i) => <text key={i} x={x} y={y} fontSize="34" opacity=".8">{i % 3 === 0 ? '🌳' : i % 3 === 1 ? '🌲' : '🌿'}</text>)}
          {paths.map(([a, b]) => {
            const A = byId.get(a);
            const B = byId.get(b);
            if (!A || !B) return null;
            const open = states[a] !== 'locked' && states[b] !== 'locked';
            return <line key={a + b} x1={A.x} y1={A.y} x2={B.x} y2={B.y} stroke={open ? '#e6c98a' : '#c9d6b3'} strokeWidth={open ? 14 : 8} strokeLinecap="round" strokeDasharray={open ? undefined : '2 14'} />;
          })}
          {locations.map((l) => {
            const st = states[l.id] ?? 'locked';
            return (
              <g key={l.id} className={`node ${st} ${sel === l.id ? 'sel' : ''}`} transform={`translate(${l.x} ${l.y})`} onClick={() => visit(l)} role="button" tabIndex={0}
                 onKeyDown={(e) => e.key === 'Enter' && visit(l)} aria-label={l.name_en}>
                <circle r="38" className="disc" />
                <text className="icon" textAnchor="middle" dy="12" fontSize="38">{l.icon}</text>
                {st === 'locked' && <text textAnchor="middle" dy="-22" dx="26" fontSize="22">🔒</text>}
                {st === 'cleared' && <text textAnchor="middle" dy="-22" dx="26" fontSize="22">✅</text>}
                {l.kind === 'pending' && st !== 'locked' && <text textAnchor="middle" dy="-22" dx="26" fontSize="22">📖</text>}
                <text className="label" textAnchor="middle" dy="62">{l.name_en}</text>
              </g>
            );
          })}
          {hereLoc && (
            <g className="token" style={{ transform: `translate(${hereLoc.x}px, ${hereLoc.y - 52}px)` }}>
              <text textAnchor="middle" fontSize="34">📍</text>
            </g>
          )}
        </svg>
      </div>
      <aside className="panel">{panel()}</aside>
    </div>
  );
}
