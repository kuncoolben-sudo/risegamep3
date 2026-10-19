import { useGame } from '../state/GameContext';
import { STAGE_NAMES, STAGE_THRESHOLDS } from '../lib/util';
import { Bar } from '../components/Hud';

export function PetScreen() {
  const { pet, species, progress, character } = useGame();
  const sp = species.find((s) => s.id === pet?.species_id);
  if (!pet || !sp) return null;
  const cleared = progress.size;
  const next = STAGE_THRESHOLDS[pet.stage - 1];
  return (
    <section className="card center">
      <div className="pet-hero" style={{ fontSize: 80 + pet.stage * 28 }}>{sp.icon}{pet.stage === 3 && <span className="sparkle">✨</span>}</div>
      <h2>{sp.name_en} · {sp.name_th}</h2>
      <p className="badge">ระดับ {pet.stage}: {STAGE_NAMES[pet.stage - 1]}</p>
      <p>{sp.blurb_th}</p>
      {next ? (
        <>
          <div className="bar xp"><div style={{ width: `${(cleared / next) * 100}%` }} /><span>ผ่านบทเรียน {cleared}/{next}</span></div>
          <p className="muted">เติบโตด้วยการเรียน ไม่ใช่การสุ่ม และไม่เสียสัตว์เลี้ยงเมื่อแพ้</p>
        </>
      ) : (
        <p className="muted">สัตว์เลี้ยงเติบโตเต็มที่แล้ว 🎉</p>
      )}
      {character && (
        <div className="status-card">
          <b>สถานะการดวล</b>
          <Bar value={character.hp} max={character.max_hp} kind="hp" />
          <Bar value={character.mana} max={character.max_mana} kind="mana" />
          <div className="stat-row">
            <span>⚔️ โจมตี <b>{10 + 2 * pet.stage}</b></span>
            <span>⚡ ทักษะ <b>{pet.stage >= 2 ? 18 + 3 * pet.stage : '🔒'}</b></span>
          </div>
          <p className="muted small">HP/Mana ของตัวละครใช้ร่วมกับสัตว์เลี้ยงในการดวล ฟื้นฟูที่แคมป์/โรงเตี๊ยม หรือใช้ไอเทมในกระเป๋า</p>
        </div>
      )}
      <div className="skill">
        <b>⚡ ทักษะ: {sp.skill_name}</b>
        <p>{pet.stage >= 2 ? 'ใช้ได้ในการดวล (ใช้ Mana 10)' : `ปลดล็อกเมื่อเติบโตถึงระดับ 2 (ผ่าน ${STAGE_THRESHOLDS[0]} บทเรียน)`}</p>
      </div>
    </section>
  );
}
