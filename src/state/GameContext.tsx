import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { Session } from '@supabase/supabase-js';
import { configured, supabase } from '../lib/supabase';
import type {
  CharacterRow, ItemRow, LessonRow, LocationRow, LocationStatus, PetRow, PetSpecies, ProgressRow,
} from '../lib/types';

export type Phase = 'loading' | 'setup' | 'auth' | 'create' | 'ready';

interface Game {
  phase: Phase;
  session: Session | null;
  character: CharacterRow | null;
  pet: PetRow | null;
  locations: LocationRow[];
  paths: [string, string][];
  lessons: LessonRow[];
  items: ItemRow[];
  species: PetSpecies[];
  progress: Map<string, ProgressRow>;
  inventory: Map<string, number>;
  states: Record<string, LocationStatus>;
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
  notice: string | null;
  say: (msg: string) => void;
}

const Ctx = createContext<Game | null>(null);

export function useGame(): Game {
  const g = useContext(Ctx);
  if (!g) throw new Error('useGame outside provider');
  return g;
}

export function GameProvider({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<Phase>(configured ? 'loading' : 'setup');
  const [session, setSession] = useState<Session | null>(null);
  const [character, setCharacter] = useState<CharacterRow | null>(null);
  const [pet, setPet] = useState<PetRow | null>(null);
  const [locations, setLocations] = useState<LocationRow[]>([]);
  const [paths, setPaths] = useState<[string, string][]>([]);
  const [lessons, setLessons] = useState<LessonRow[]>([]);
  const [items, setItems] = useState<ItemRow[]>([]);
  const [species, setSpecies] = useState<PetSpecies[]>([]);
  const [progress, setProgress] = useState<Map<string, ProgressRow>>(new Map());
  const [inventory, setInventory] = useState<Map<string, number>>(new Map());
  const [states, setStates] = useState<Record<string, LocationStatus>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const noticeTimer = useRef<number>();
  const staticLoaded = useRef(false);

  const say = useCallback((msg: string) => {
    setNotice(msg);
    window.clearTimeout(noticeTimer.current);
    noticeTimer.current = window.setTimeout(() => setNotice(null), 3500);
  }, []);

  const loadStatic = useCallback(async () => {
    if (staticLoaded.current) return;
    const [loc, pa, le, it, sp] = await Promise.all([
      supabase.from('locations').select('*'),
      supabase.from('location_paths').select('*'),
      supabase.from('lessons').select('*').order('sort'),
      supabase.from('items').select('*'),
      supabase.from('pet_species').select('*'),
    ]);
    for (const r of [loc, pa, le, it, sp]) if (r.error) throw r.error;
    setLocations(loc.data as LocationRow[]);
    setPaths((pa.data as { from_id: string; to_id: string }[]).map((p) => [p.from_id, p.to_id]));
    setLessons(le.data as LessonRow[]);
    setItems(it.data as ItemRow[]);
    setSpecies(sp.data as PetSpecies[]);
    staticLoaded.current = true;
  }, []);

  const refresh = useCallback(async () => {
    const { data: s } = await supabase.auth.getSession();
    setSession(s.session);
    if (!s.session) {
      setCharacter(null);
      setPet(null);
      setPhase('auth');
      return;
    }
    await loadStatic();
    const { data: ch, error } = await supabase.from('characters').select('*').maybeSingle();
    if (error) throw error;
    if (!ch) {
      setCharacter(null);
      setPet(null);
      setPhase('create');
      return;
    }
    const [pe, pr, inv, st] = await Promise.all([
      supabase.from('pets').select('*').maybeSingle(),
      supabase.from('lesson_progress').select('*'),
      supabase.from('inventory').select('*'),
      supabase.rpc('location_states'),
    ]);
    for (const r of [pe, pr, inv, st]) if (r.error) throw r.error;
    setCharacter(ch as CharacterRow);
    setPet(pe.data as PetRow);
    setProgress(new Map((pr.data as ProgressRow[]).map((p) => [p.lesson_id, p])));
    setInventory(new Map((inv.data as { item_id: string; qty: number }[]).map((i) => [i.item_id, i.qty])));
    setStates(Object.fromEntries((st.data as { location_id: string; status: LocationStatus }[]).map((r) => [r.location_id, r.status])));
    setPhase('ready');
  }, [loadStatic]);

  useEffect(() => {
    if (!configured) return;
    refresh().catch((e) => {
      console.error(e);
      setPhase('auth');
    });
    const { data: sub } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN' || event === 'SIGNED_OUT') refresh().catch(console.error);
    });
    return () => sub.subscription.unsubscribe();
  }, [refresh]);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    await refresh();
  }, [refresh]);

  const value = useMemo<Game>(
    () => ({
      phase, session, character, pet, locations, paths, lessons, items, species, progress, inventory, states,
      refresh, signOut, notice, say,
    }),
    [phase, session, character, pet, locations, paths, lessons, items, species, progress, inventory, states, refresh, signOut, notice, say],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
