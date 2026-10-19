import { useGame } from '../state/GameContext';
import { STAGE_NAMES, STAGE_THRESHOLDS, STAT_BASE, STAT_PER_STAR, statValue, totalStars } from '../lib/util';
import { Bar } from '../components/Hud';
import { PetShowcase } from '../components/PetShowcase';
import { PETS, isFantasyPet, petForm } from '../world3d/pets';

export function PetScreen() {
  const { pet, species, progress } = useGame();
  const sp = species.find((s) => s.id === pet?.species_id);
  if (!pet || !sp) return null;
  const cleared = progress.size;
  const stars = totalStars(progress);
  const stat = statValue(stars);
  const fantasy = isFantasyPet(sp.id);
  const next = STAGE_THRESHOLDS[pet.stage - 1];
  return (
    <section className="card center">
      {fantasy ? (
        <PetShowcase species={sp.id} stage={pet.stage} maxStage={pet.stage} height={300} />
      ) : (
        <div className="pet-hero" style={{ fontSize: 80 + pet.stage * 28 }}>{sp.icon}{pet.stage === 3 && <span className="sparkle">✨</span>}</div>
      )}
      <h2>{sp.name_en} · {sp.name_th}</h2>
      <p className="badge">ระดับ {pet.stage}: {fantasy ? petForm(sp.id, pet.stage).name_th : STAGE_NAMES[pet.stage - 1]}</p>
      <p>{sp.blurb_th}</p>
      {next ? (
        <>
          <div className="bar xp"><div style={{ width: `${(cleared / next) * 100}%` }} /><span>ผ่านบทเรียน {cleared}/{next}</span></div>
          <p className="muted">เติบโตด้วยการเรียน ไม่ใช่การสุ่ม และไม่เสียสัตว์เลี้ยงเมื่อแพ้</p>
        </>
      ) : (
        <p className="muted">สัตว์เลี้ยงเติบโตเต็มที่แล้ว 🎉</p>
      )}
      {pet && (
        <div className="status-card">
          <b>สถานะการดวลของสัตว์เลี้ยง</b>
          <Bar value={pet.hp} max={pet.max_hp} kind="hp" />
          <Bar value={pet.mana} max={pet.max_mana} kind="mana" />
          <div className="stat-row">
            <span>⭐ ดาวสะสม <b>{stars}</b></span>
            <span>⚔️ ATK <b>{stat}</b></span>
            <span>💨 SPD <b>{stat}</b></span>
            <span>🛡️ DEF <b>{stat}</b></span>
          </div>
          <p className="muted small">ทุกสเตตัส = {STAT_BASE} + {STAT_PER_STAR} ต่อ 1 ดาวที่ได้ในบทเรียน (นับผลที่ดีที่สุดของแต่ละบท) — ทำบทเดิมให้ได้ดาวเพิ่มก็เพิ่มสเตตัสได้</p>
          <p className="muted small">HP/Mana เป็นของสัตว์เลี้ยงเท่านั้น ใช้ในการดวล ฟื้นฟูที่แคมป์/โรงเตี๊ยม หรือใช้ไอเทมในกระเป๋า</p>
        </div>
      )}
      <div className="skill">
        <b>⚡ ท่าที่ใช้ในการดวล (ออกเอง สุ่มจากร่างที่ปลดล็อก)</b>
        {fantasy ? (
          <ul className="power-list">
            {PETS[sp.id].forms.map((f, i) => (
              <li key={f.power_en} className={i + 1 <= pet.stage ? '' : 'locked'}>
                {i + 1 <= pet.stage ? '✅' : '🔒'} ร่าง {i + 1} · {f.power_th} <small>({f.power_en})</small>
                {i + 1 === pet.stage && pet.stage > 1 && <small> — ออกบ่อยที่สุด</small>}
              </li>
            ))}
          </ul>
        ) : (
          <p>{sp.skill_name}</p>
        )}
        <p className="muted small">ท่าละ 10 Mana ถ้า Mana พอ สัตว์เลี้ยงจะออกท่าเองราวครึ่งหนึ่งของการโจมตี ถ้าเติบโตแล้ว ท่าของร่างปัจจุบันออกบ่อยที่สุด ที่เหลือสุ่มจากร่างก่อนหน้า</p>
      </div>
    </section>
  );
}
