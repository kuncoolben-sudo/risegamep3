import { Avatar } from './Avatar';
import { useGame } from '../state/GameContext';
import { NewsTicker } from './NewsTicker';

export type View = 'world' | 'map' | 'pet' | 'bag' | 'pvp' | 'lesson';

export function Bar({ value, max, kind }: { value: number; max: number; kind: 'hp' | 'mana' }) {
  return (
    <div className={`bar ${kind}`} title={`${value}/${max}`}>
      <div style={{ width: `${Math.max(0, Math.min(100, (value / max) * 100))}%` }} />
      <span>{kind === 'hp' ? '❤️' : '💧'} {value}/{max}</span>
    </div>
  );
}

export function Hud({ view, go, overlay }: { view: View; go: (v: View) => void; overlay?: boolean }) {
  const { character, pet, species, signOut } = useGame();
  if (!character) return null;
  const icon = species.find((s) => s.id === pet?.species_id)?.icon;
  return (
    <header className={`hud${overlay ? ' overlay' : ''}`}>
      <div className="hud-who">
        <Avatar look={character.appearance} size={48} />
        <div>
          <b>{character.name}</b> <span title="สัตว์เลี้ยง">{icon}</span>
          <div className="coins">🪙 {character.coins}</div>
        </div>
      </div>
      <NewsTicker />
      <nav>
        {([['world', '🌍', 'โลก 3D'], ['map', '🗺️', 'แผนที่ 2D'], ['pet', '🐾', 'สัตว์เลี้ยง'], ['bag', '🎒', 'กระเป๋า']] as const).map(([v, e, t]) => (
          <button key={v} className={`nav ${view === v ? 'on' : ''}`} onClick={() => go(v)} disabled={view === 'lesson'}>
            {e}<span>{t}</span>
          </button>
        ))}
        <button className="nav" onClick={signOut} title="ออกจากระบบ">🚪<span>ออก</span></button>
      </nav>
    </header>
  );
}
