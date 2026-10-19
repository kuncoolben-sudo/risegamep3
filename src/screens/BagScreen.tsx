import { useState } from 'react';
import { rpc, errorText } from '../lib/supabase';
import { useGame } from '../state/GameContext';
import { Bar } from '../components/Hud';

export function BagScreen() {
  const { items, inventory, refresh, say, character, pet } = useGame();
  const [busy, setBusy] = useState(false);
  const owned = items.filter((i) => (inventory.get(i.id) ?? 0) > 0);

  async function use(id: string) {
    setBusy(true);
    try {
      await rpc('use_item', { p_item: id });
      await refresh();
    } catch (e) {
      say(errorText(e));
    }
    setBusy(false);
  }

  return (
    <section className="card">
      <h2>🎒 กระเป๋า</h2>
      <p>🪙 เหรียญ: <b>{character?.coins}</b> · ซื้อไอเทมได้ที่โรงพยาบาล</p>
      {pet && (
        <div className="mini-bars">
          <Bar value={pet.hp} max={pet.max_hp} kind="hp" />
          <Bar value={pet.mana} max={pet.max_mana} kind="mana" />
        </div>
      )}
      <p className="muted small">HP/Mana เป็นของสัตว์เลี้ยง ใช้ในการดวล (PvP) เท่านั้น</p>
      {owned.length === 0 && <p className="muted">ยังไม่มีไอเทม ทำบทเรียนให้ได้ 3 ดาวเพื่อรับแอปเปิล!</p>}
      <ul className="list">
        {owned.map((i) => (
          <li key={i.id}>
            <span className="big-emoji">{i.icon}</span>
            <div>
              <b>{i.name_en}</b> ×{inventory.get(i.id)}
              <div className="muted small">{i.name_th} · {i.heal_hp ? `+${i.heal_hp} HP ` : ''}{i.heal_mana ? `+${i.heal_mana} Mana` : ''}</div>
            </div>
            <button className="btn" disabled={busy} onClick={() => use(i.id)}>ใช้</button>
          </li>
        ))}
      </ul>
    </section>
  );
}
