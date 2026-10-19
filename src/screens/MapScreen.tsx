import { useState } from 'react';
import { useGame } from '../state/GameContext';
import { useTravel } from '../state/useTravel';
import { useQuest } from '../state/useQuest';
import { LocationPanel } from '../components/LocationPanel';
import type { LocationRow } from '../lib/types';

const TREES = [[40, 40], [180, 60], [300, 40], [450, 90], [560, 60], [700, 60], [900, 100], [960, 220], [940, 460], [980, 560], [820, 600],
  [700, 600], [560, 600], [330, 610], [200, 600], [30, 480], [40, 300], [260, 330], [420, 400], [560, 350], [690, 380], [400, 270], [880, 160]];

export function MapScreen({ onGo }: { onGo: (locationId: string) => void }) {
  const { locations, paths, states } = useGame();
  const questInfo = useQuest();
  const { byId, here } = useTravel();
  const [sel, setSel] = useState<string | null>(null);
  const hereLoc = byId.get(here);
  const selected = sel ? byId.get(sel) : undefined;

  const go = (l: LocationRow) => onGo(l.id);

  const quest = (
    <>
      {questInfo && (
        <div className="quest">
          <b>❗ Main Quest</b>
          <p>{questInfo.location.name_th}: {questInfo.lesson.title}</p>
          <button className="btn" onClick={() => go(questInfo.location)}>ไปเลย ➜</button>
        </div>
      )}
      <p className="muted">แตะสถานที่บนแผนที่เพื่อเดินทาง</p>
    </>
  );

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
              <g key={l.id} className={`node ${st} ${sel === l.id ? 'sel' : ''}`} transform={`translate(${l.x} ${l.y})`} onClick={() => setSel(l.id)} role="button" tabIndex={0}
                 onKeyDown={(e) => e.key === 'Enter' && setSel(l.id)} aria-label={l.name_en}>
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
      <aside className="panel"><LocationPanel selected={selected} onClose={() => setSel(null)} onPlay={() => {}} onPvp={() => {}} onGo={go} empty={quest} /></aside>
    </div>
  );
}
