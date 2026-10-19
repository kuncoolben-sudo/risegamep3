import { Suspense, lazy, useEffect, useState } from 'react';
import { PETS, clampStage, petForm } from '../world3d/pets';
import { STAGE_THRESHOLDS } from '../lib/util';

const PetViewer3D = lazy(() => import('../world3d/PetViewer3D'));

// 3D look at a pet in each of its three forms, with the power each form releases. Forms above maxStage are
// shown too (so players can see what they are growing towards) but marked as locked.
export function PetShowcase({ species, stage, maxStage = 3, height = 320 }: { species: string; stage?: number; maxStage?: number; height?: number }) {
  const def = PETS[species];
  const [form, setForm] = useState<number>(clampStage(stage ?? 1));
  const [castKey, setCastKey] = useState(0);
  useEffect(() => { setForm(clampStage(stage ?? 1)); setCastKey(0); }, [species, stage]);
  if (!def) return null;
  const st = clampStage(form);
  const info = petForm(species, st);
  const locked = st > maxStage;
  return (
    <div className="showcase" style={{ ['--accent' as string]: def.accent }}>
      <Suspense fallback={<div className="showcase-loading" style={{ height }}>กำลังโหลดโมเดล 3D…</div>}>
        <PetViewer3D species={species} stage={st} castKey={castKey} height={height} />
      </Suspense>
      <div className="form-tabs">
        {def.forms.map((f, i) => (
          <button key={f.name_th} className={`chip ${st === i + 1 ? 'on' : ''}`} onClick={() => { setForm(i + 1); setCastKey(0); }}>
            {i + 1 > maxStage ? '🔒 ' : ''}ร่าง {i + 1} · {f.name_th}
          </button>
        ))}
      </div>
      <div className="power-info">
        <div>
          <b>⚡ {info.power_th}</b> <small>({info.power_en})</small>
          <p className="muted small">
            {locked ? `ร่างนี้ยังไม่ปลดล็อก — เติบโตด้วยการเรียน (ผ่านบทเรียน ${STAGE_THRESHOLDS[st - 2]} บท)` : 'ออกเองในการดวล (ใช้ Mana 10)'}
          </p>
        </div>
        <button className="btn" onClick={() => setCastKey((k) => k + 1)}>✨ ปล่อยพลัง</button>
      </div>
    </div>
  );
}
