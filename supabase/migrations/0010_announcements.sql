-- Public announcements for the status bar: a player passes a lesson for the first time, or a pet grows into its next
-- form. Rows are written only by the triggers below (security definer); every client can read them and listen for
-- new ones (realtime), so the whole game sees what other players achieve.

create table public.announcements (
  id bigint generated always as identity primary key,
  kind text not null check (kind in ('lesson', 'evolve')),
  char_name text not null,
  detail jsonb not null default '{}'::jsonb,  -- lesson: {title, stars}; evolve: {species_id, stage}
  created_at timestamptz not null default now()
);
create index announcements_created_idx on public.announcements (created_at);

alter table public.announcements enable row level security;
create policy "announcements are public" on public.announcements for select using (true);
revoke all on public.announcements from anon, authenticated;
grant select on public.announcements to anon, authenticated;

-- first pass of a lesson (retries only update the row, so they stay quiet); old announcements are dropped as we go
create or replace function public._announce_lesson() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into announcements (kind, char_name, detail)
  select 'lesson', c.name, jsonb_build_object('title', l.title, 'stars', new.stars)
  from characters c, lessons l
  where c.id = new.character_id and l.id = new.lesson_id;
  delete from announcements where created_at < now() - interval '2 days';
  return new;
end $$;

create trigger announce_lesson after insert on public.lesson_progress
  for each row execute function public._announce_lesson();

-- a pet moves up a stage (see complete_lesson)
create or replace function public._announce_evolve() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into announcements (kind, char_name, detail)
  select 'evolve', c.name, jsonb_build_object('species_id', new.species_id, 'stage', new.stage)
  from characters c
  where c.id = new.character_id;
  return new;
end $$;

create trigger announce_evolve after update of stage on public.pets
  for each row when (new.stage > old.stage) execute function public._announce_evolve();

-- realtime, like pvp_matches
do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    alter publication supabase_realtime add table public.announcements;
  end if;
end $$;
