import { useState } from 'react';
import { Avatar, DEFAULT_APPEARANCE, HAIR_COLORS, OUTFITS, SKINS, hairLabel } from '../components/Avatar';
import { rpc, errorText } from '../lib/supabase';
import type { Appearance } from '../lib/types';
import { useGame } from '../state/GameContext';

export function CreateCharacter() {
  const { species, refresh } = useGame();
  const [name, setName] = useState('');
  const [look, setLook] = useState<Appearance>(DEFAULT_APPEARANCE);
  const [pet, setPet] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const set = <K extends keyof Appearance>(k: K, v: Appearance[K]) => setLook((l) => ({ ...l, [k]: v }));

  async function submit() {
    setBusy(true);
    setErr('');
    try {
      await rpc('create_character', { p_name: name, p_appearance: look, p_species: pet });
      await refresh();
    } catch (e) {
      setErr(errorText(e));
      setBusy(false);
    }
  }

  const swatches = (colors: string[], value: string, onPick: (c: string) => void) => (
    <div className="swatches">
      {colors.map((c) => (
        <button key={c} className={`swatch ${value === c ? 'on' : ''}`} style={{ background: c }} onClick={() => onPick(c)} aria-label={c} />
      ))}
    </div>
  );
  const chips = <T extends string>(opts: [T, string][], value: T, onPick: (v: T) => void) => (
    <div className="chips">
      {opts.map(([v, label]) => (
        <button key={v} className={`chip ${value === v ? 'on' : ''}`} onClick={() => onPick(v)}>{label}</button>
      ))}
    </div>
  );

  return (
    <main className="card create">
      <h1>สร้างตัวละครของคุณ</h1>
      <div className="create-grid">
        <div className="preview">
          <Avatar look={look} size={150} />
          <p className="muted">{hairLabel(look)}</p>
          <p className="pet-preview">{pet ? species.find((s) => s.id === pet)?.icon : '❔'}</p>
        </div>
        <div className="fields">
          <label>ชื่อตัวละคร
            <input value={name} maxLength={20} onChange={(e) => setName(e.target.value)} placeholder="เช่น Mina" />
          </label>
          <label>ความยาวผม {chips([['short', 'short'], ['long', 'long']], look.hairLength, (v) => set('hairLength', v))}</label>
          <label>ทรงผม {chips([['straight', 'straight'], ['wavy', 'wavy'], ['curly', 'curly']], look.hairType, (v) => set('hairType', v))}</label>
          <label>สีผม {swatches(HAIR_COLORS, look.hairColor, (c) => set('hairColor', c))}</label>
          <label>หนวด/เครา {chips([['none', 'none'], ['moustache', 'moustache'], ['beard', 'beard']], look.facial, (v) => set('facial', v))}</label>
          <label>สีผิว {swatches(SKINS, look.skin, (c) => set('skin', c))}</label>
          <label>ชุด {swatches(OUTFITS, look.outfit, (c) => set('outfit', c))}</label>
        </div>
      </div>
      <h2>เลือกสัตว์เลี้ยงคู่ใจ <small>(เลือกได้ตัวเดียว เปลี่ยนไม่ได้)</small></h2>
      <div className="pets">
        {species.map((s) => (
          <button key={s.id} className={`pet-card ${pet === s.id ? 'on' : ''}`} onClick={() => setPet(s.id)}>
            <span className="pet-icon">{s.icon}</span>
            <b>{s.name_en}</b>
            <span>{s.name_th}</span>
            <small>{s.blurb_th}</small>
          </button>
        ))}
      </div>
      {err && <p className="error">{err}</p>}
      <button className="btn big" disabled={busy || !name.trim() || !pet} onClick={submit}>เริ่มผจญภัย!</button>
      <p className="muted small">รูปลักษณ์เป็นของตกแต่งเท่านั้น ไม่มีผลต่อพลังต่อสู้</p>
    </main>
  );
}
