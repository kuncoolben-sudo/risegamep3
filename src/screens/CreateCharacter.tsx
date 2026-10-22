import { Suspense, lazy, useState } from 'react';
import { Avatar, PRESET_LOOKS } from '../components/Avatar';
import { rpc, errorText } from '../lib/supabase';
import { CHARACTER_PRESETS, type Appearance, type CharacterPreset } from '../lib/types';
import { useGame } from '../state/GameContext';
import { PetShowcase } from '../components/PetShowcase';
import { PETS, isFantasyPet } from '../world3d/pets';

const CharacterPreview3D = lazy(() => import('../world3d/CharacterPreview3D'));

export function CreateCharacter() {
  const { species, refresh } = useGame();
  const [name, setName] = useState('');
  const [look, setLook] = useState<Appearance>({ ...PRESET_LOOKS.kai.look, preset: 'kai' });
  const [pet, setPet] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  // the six fantasy pets (with 3D forms); older species stay in the database for existing characters but are not offered
  const fantasy = species.filter((s) => PETS[s.id]);
  const offered = fantasy.length ? fantasy : species;
  const pick = (p: CharacterPreset) => setLook({ ...PRESET_LOOKS[p].look, preset: p });

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

  return (
    <main className="card create">
      <h1>สร้างตัวละครของคุณ</h1>
      <div className="create-grid">
        <div className="preview">
          <Suspense fallback={<Avatar look={look} size={150} />}>
            <CharacterPreview3D look={look} />
          </Suspense>
          <p className="pet-preview">{pet ? species.find((s) => s.id === pet)?.icon : '❔'}</p>
        </div>
        <div className="fields">
          <div>ตัวละครต้นแบบ
            <div className="chips">
              {CHARACTER_PRESETS.map((p) => (
                <button key={p} className={`chip ${look.preset === p ? 'on' : ''}`} onClick={() => pick(p)} title={PRESET_LOOKS[p].tagline}>
                  {PRESET_LOOKS[p].name}
                </button>
              ))}
            </div>
            {look.preset && <p className="muted small">{PRESET_LOOKS[look.preset].name} — {PRESET_LOOKS[look.preset].tagline}</p>}
          </div>
          <label>ชื่อตัวละคร
            <input value={name} maxLength={20} onChange={(e) => setName(e.target.value)} placeholder="เช่น Mina" />
          </label>
        </div>
      </div>
      <h2>เลือกสัตว์เลี้ยงคู่ใจ <small>(เลือกได้ตัวเดียว เปลี่ยนไม่ได้)</small></h2>
      <div className="pets">
        {offered.map((s) => (
          <button key={s.id} className={`pet-card ${pet === s.id ? 'on' : ''}`} onClick={() => setPet(s.id)}>
            <span className="pet-icon">{s.icon}</span>
            <b>{s.name_en}</b>
            <span>{s.name_th}</span>
            {PETS[s.id] && <small>{PETS[s.id].gender === 'male' ? '♂ เพศผู้' : '♀ เพศเมีย'} · {PETS[s.id].tagline_th}</small>}
            {!PETS[s.id] && <small>{s.blurb_th}</small>}
          </button>
        ))}
      </div>
      {isFantasyPet(pet) ? (
        <>
          <p className="muted small">{species.find((s) => s.id === pet)?.blurb_th}</p>
          <PetShowcase species={pet} stage={1} maxStage={1} />
        </>
      ) : (
        <p className="muted small">เลือกสัตว์เลี้ยงเพื่อดูโมเดล 3D ทั้ง 3 ร่างและท่าปล่อยพลัง</p>
      )}
      {err && <p className="error">{err}</p>}
      <button className="btn big" disabled={busy || !name.trim() || !pet} onClick={submit}>เริ่มผจญภัย!</button>
      <p className="muted small">รูปลักษณ์เป็นของตกแต่งเท่านั้น ไม่มีผลต่อพลังต่อสู้</p>
    </main>
  );
}
