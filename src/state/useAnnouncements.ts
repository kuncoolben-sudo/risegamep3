import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import type { Announcement } from '../lib/types';

const SHOW_MS = 6000;
const STALE_MS = 2 * 60 * 1000; // an announcement that waited this long in the queue is no longer news
const POLL_MS = 20000; // safety net for when realtime is unavailable

// Highest announcement id seen in this page session. Kept outside the hook so the status bar (which is
// re-created when you switch screens) neither repeats old news nor misses what happened in between.
let lastId = -1;

/** The announcement to show now (one at a time, each for a few seconds), from other players' lessons and pet growth. */
export function useAnnouncements(): Announcement | null {
  const [queue, setQueue] = useState<Announcement[]>([]);
  const [current, setCurrent] = useState<Announcement | null>(null);

  useEffect(() => {
    let alive = true;
    const take = (rows: Announcement[]) => {
      const fresh = rows.filter((r) => r.id > lastId).sort((a, b) => a.id - b.id);
      if (!alive || fresh.length === 0) return;
      lastId = fresh[fresh.length - 1].id;
      setQueue((q) => [...q, ...fresh].slice(-8));
    };
    const poll = async () => {
      if (lastId < 0) { // first look: remember where the feed is now, show nothing old
        const { data } = await supabase.from('announcements').select('id').order('id', { ascending: false }).limit(1);
        if (alive && lastId < 0) lastId = (data as { id: number }[] | null)?.[0]?.id ?? 0;
        return;
      }
      const { data } = await supabase.from('announcements').select('*').gt('id', lastId).order('id').limit(10);
      take((data as Announcement[] | null) ?? []);
    };
    poll();
    const timer = window.setInterval(poll, POLL_MS);
    const channel = supabase
      .channel(`announcements-${Math.random().toString(36).slice(2)}`)
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'announcements' }, (e) => take([e.new as Announcement]))
      .subscribe();
    return () => { alive = false; window.clearInterval(timer); supabase.removeChannel(channel); };
  }, []);

  useEffect(() => {
    if (current || queue.length === 0) return;
    const [next, ...rest] = queue;
    setQueue(rest);
    if (Date.now() - new Date(next.created_at).getTime() < STALE_MS) setCurrent(next);
  }, [current, queue]);

  useEffect(() => {
    if (!current) return;
    const t = window.setTimeout(() => setCurrent(null), SHOW_MS);
    return () => window.clearTimeout(t);
  }, [current]);

  return current;
}
