import { useGame } from '../state/GameContext';
import { useAnnouncements } from '../state/useAnnouncements';
import { PETS } from '../world3d/pets';
import type { Announcement, PetSpecies } from '../lib/types';

function describe(a: Announcement, species: PetSpecies[]): string {
  if (a.kind === 'lesson') return `🎉 ${a.char_name} ผ่านบท “${a.detail.title ?? 'บทเรียน'}” ${'⭐'.repeat(a.detail.stars ?? 1)}`;
  const id = a.detail.species_id ?? '', stage = a.detail.stage ?? 2;
  const form = PETS[id]?.forms[stage - 1]?.name_th ?? `ร่างที่ ${stage}`;
  return `✨ ${species.find((s) => s.id === id)?.icon ?? '🐾'} สัตว์เลี้ยงของ ${a.char_name} เติบโตเป็น ${form}!`;
}

/** Fills the free space of the status bar with what other players just did. */
export function NewsTicker() {
  const { species } = useGame();
  const news = useAnnouncements();
  return (
    <div className="hud-news" aria-live="polite">
      {news && <p key={news.id} className={`news-item ${news.kind}`}>{describe(news, species)}</p>}
    </div>
  );
}
