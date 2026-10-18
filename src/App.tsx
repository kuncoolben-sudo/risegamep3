import { useCallback, useState } from 'react';
import { GameProvider, useGame } from './state/GameContext';
import { Hud, type View } from './components/Hud';
import { AuthScreen, SetupScreen } from './screens/AuthScreen';
import { CreateCharacter } from './screens/CreateCharacter';
import { MapScreen } from './screens/MapScreen';
import { LessonScreen } from './screens/LessonScreen';
import { PetScreen } from './screens/PetScreen';
import { BagScreen } from './screens/BagScreen';
import { PvpScreen } from './screens/PvpScreen';

function Shell() {
  const { phase, notice, refresh } = useGame();
  const [view, setView] = useState<View>('map');
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [pvp, setPvp] = useState(false);
  const [live, setLive] = useState<{ hp: number; mana: number } | null>(null);
  const onLive = useCallback((hp: number, mana: number) => setLive({ hp, mana }), []);

  let body;
  if (phase === 'loading') body = <main className="card center"><p>กำลังโหลด…</p></main>;
  else if (phase === 'setup') body = <SetupScreen />;
  else if (phase === 'auth') body = <AuthScreen />;
  else if (phase === 'create') body = <CreateCharacter />;
  else {
    const leaveLesson = () => { setLessonId(null); setLive(null); setView('map'); refresh(); };
    body = (
      <>
        <Hud view={pvp ? 'pvp' : view} go={(v) => { setPvp(false); setView(v); }} hp={live?.hp} mana={live?.mana} />
        <main className="stage">
          {pvp ? <PvpScreen onExit={() => setPvp(false)} />
            : view === 'lesson' && lessonId ? <LessonScreen lessonId={lessonId} onExit={leaveLesson} onLive={onLive} />
            : view === 'pet' ? <PetScreen />
            : view === 'bag' ? <BagScreen />
            : <MapScreen onPlay={(id) => { setLessonId(id); setView('lesson'); }} onPvp={() => setPvp(true)} />}
        </main>
      </>
    );
  }
  return (
    <div className="app">
      {body}
      {notice && <div className="toast" role="status">{notice}</div>}
    </div>
  );
}

export default function App() {
  return <GameProvider><Shell /></GameProvider>;
}
