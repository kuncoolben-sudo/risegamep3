import { useState, type ReactNode } from 'react';
import { rpc, errorText } from '../lib/supabase';
import { useGame } from '../state/GameContext';
import { Bar } from './Hud';
import { useTravel } from '../state/useTravel';
import type { LocationRow } from '../lib/types';

function pagesLabel(l: LocationRow) {
  return l.page_from ? `หน้า ${l.page_from}–${l.page_to}` : '';
}

// What you can do at a location: lessons, rest, shop, arena. Used by both the 2D map and the 3D world.
export function LocationPanel({ selected, onClose, onPlay, onPvp, onGo, empty }: {
  selected: LocationRow | null | undefined;
  onClose: () => void;
  onPlay: (lessonId: string) => void;
  onPvp: () => void;
  /** when set (2D map): show only the place info and a "go" button instead of its lessons */
  onGo?: (loc: LocationRow) => void;
  empty?: ReactNode;
}) {
  const { lessons, items, states, character, pet, progress, refresh, say } = useGame();
  const { byId, here } = useTravel();
  const [busy, setBusy] = useState(false);

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

  if (!selected) return <>{empty ?? <p className="muted">แตะสถานที่เพื่อเดินทาง</p>}</>;
  const st = states[selected.id];
  const header = (
    <div className="panel-head">
      <span className="big-emoji">{selected.icon}</span>
      <div>
        <h3>{selected.name_en}</h3>
        <div className="muted small">{selected.name_th} {pagesLabel(selected)}</div>
      </div>
      <button className="x" onClick={onClose} aria-label="ปิด">✕</button>
    </div>
  );
  if (st === 'locked') return <>{header}<p>🔒 ยังไม่เปิด ต้องผ่าน: {selected.requires.map((r) => byId.get(r)?.name_en).join(', ')}</p></>;
  if (onGo) {
    return (
      <>
        {header}
        <p>{selected.blurb_th}</p>
        <button className="btn big" onClick={() => onGo(selected)}>🚶 ไปเลย</button>
        <p className="muted small">ตัวละครจะเดินไปที่นั่นในโลก 3D</p>
      </>
    );
  }
  if (here !== selected.id) return <>{header}<p className="muted">กำลังเดินทาง…</p></>;
  if (selected.kind === 'pending')
    return <>{header}<p>{selected.blurb_th}</p><p className="notice">📖 เนื้อหาส่วนนี้ยังรอใส่จากหน้าหนังสือจริง — ภาพสารบัญระบุเฉพาะชื่อและเลขหน้า จึงยังไม่สร้างกิจกรรมขึ้นเอง</p></>;
  if (selected.kind === 'arena')
    return <>{header}<p>{selected.blurb_th}</p><button className="btn big" onClick={onPvp}>⚔️ เข้าสู่ลานประลอง</button></>;
  if (selected.kind === 'rest') {
    const free = selected.rest_type === 'inn' || selected.rest_type === 'hospital'; // heals to full, free, and sells items
    return (
      <>
        {header}
        <p>{selected.blurb_th}</p>
        {pet && (
          <div className="mini-bars">
            <Bar value={pet.hp} max={pet.max_hp} kind="hp" />
            <Bar value={pet.mana} max={pet.max_mana} kind="mana" />
          </div>
        )}
        <button className="btn big" disabled={busy || (!free && character?.rested_here)} onClick={() => act('rest', undefined, free ? 'รักษาเรียบร้อย! 💖' : 'พักที่แคมป์แล้ว ✨')}>
          {free ? '🏥 รักษาจนเต็ม (ฟรี)' : character?.rested_here ? '⛺ พักแล้ว' : '⛺ พักที่แคมป์ (+40 HP, +15 Mana)'}
        </button>
        {free && (
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
}
