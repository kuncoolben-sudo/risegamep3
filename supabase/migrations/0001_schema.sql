-- RISE English Adventure: schema, RLS and grants.
-- Game rules live in 0002_functions.sql (clients write only through RPCs).

-- ---------- static content (public read) ----------
create table public.locations (
  id text primary key,
  kind text not null check (kind in ('unit', 'rest', 'arena', 'pending')),
  name_en text not null,
  name_th text not null,
  blurb_th text,
  icon text not null,
  page_from int,
  page_to int,
  x int not null,
  y int not null,
  requires text[] not null default '{}',
  rest_type text check (rest_type in ('inn', 'camp')),
  content_status text not null default 'verified' check (content_status in ('verified', 'pending'))
);

create table public.location_paths (
  from_id text not null references public.locations (id) on delete cascade,
  to_id text not null references public.locations (id) on delete cascade,
  primary key (from_id, to_id)
);

create table public.lessons (
  id text primary key,
  location_id text not null references public.locations (id) on delete cascade,
  sort int not null,
  kind text not null check (kind in ('starter', 'lesson1', 'lesson2', 'chat', 'clil', 'project')),
  title text not null,
  pages text,
  required boolean not null default true,
  pass_ratio numeric not null default 0 check (pass_ratio >= 0 and pass_ratio <= 1)
);

create table public.activities (
  id bigint generated always as identity primary key,
  lesson_id text not null references public.lessons (id) on delete cascade,
  sort int not null,
  type text not null check (type in ('listen_choose', 'spell', 'sentence_order', 'qa_choose', 'project')),
  payload jsonb not null
);
create index activities_lesson_idx on public.activities (lesson_id, sort);

create table public.items (
  id text primary key,
  name_en text not null,
  name_th text not null,
  icon text not null,
  kind text not null check (kind in ('heal', 'mana')),
  heal_hp int not null default 0,
  heal_mana int not null default 0,
  price int not null default 0
);

create table public.pet_species (
  id text primary key,
  name_en text not null,
  name_th text not null,
  icon text not null,
  skill_name text not null,
  blurb_th text
);

-- ---------- player data ----------
create table public.characters (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users (id) on delete cascade,
  name text not null check (char_length(name) between 1 and 20),
  appearance jsonb not null,
  max_hp int not null default 100,
  hp int not null default 100,
  max_mana int not null default 40,
  mana int not null default 40,
  coins int not null default 20 check (coins >= 0),
  location_id text not null default 'start' references public.locations (id),
  rested_here boolean not null default false,
  pvp_wins int not null default 0,
  pvp_losses int not null default 0,
  created_at timestamptz not null default now()
);

-- primary key on character_id = exactly one pet per character
create table public.pets (
  character_id uuid primary key references public.characters (id) on delete cascade,
  species_id text not null references public.pet_species (id),
  nickname text check (nickname is null or char_length(nickname) between 1 and 20),
  stage int not null default 1 check (stage between 1 and 3)
);

create table public.lesson_progress (
  character_id uuid not null references public.characters (id) on delete cascade,
  lesson_id text not null references public.lessons (id) on delete cascade,
  best_correct int not null,
  total int not null,
  stars int not null check (stars between 1 and 3),
  attempts int not null default 1,
  note text check (note is null or char_length(note) <= 1000),
  completed_at timestamptz not null default now(),
  primary key (character_id, lesson_id)
);

create table public.inventory (
  character_id uuid not null references public.characters (id) on delete cascade,
  item_id text not null references public.items (id),
  qty int not null check (qty >= 0),
  primary key (character_id, item_id)
);

-- ---------- PvP 1v1 ----------
create table public.pvp_matches (
  id uuid primary key default gen_random_uuid(),
  status text not null default 'waiting' check (status in ('waiting', 'active', 'finished')),
  p1 uuid not null references public.characters (id) on delete cascade,
  p2 uuid references public.characters (id) on delete cascade,
  p1_name text not null,
  p2_name text,
  p1_pet text not null,
  p2_pet text,
  p1_stage int not null default 1,
  p2_stage int not null default 1,
  p1_hp int not null default 100,
  p2_hp int not null default 100,
  p1_mana int not null default 40,
  p2_mana int not null default 40,
  p1_guard boolean not null default false,
  p2_guard boolean not null default false,
  turn uuid,
  round int not null default 1,
  q_prompt text,
  q_say text,
  q_choices jsonb,
  winner uuid,
  log jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index pvp_waiting_idx on public.pvp_matches (created_at) where status = 'waiting';

-- the answer key is kept out of the realtime-visible table
create table public.pvp_secrets (
  match_id uuid primary key references public.pvp_matches (id) on delete cascade,
  q_answer text not null
);

-- ---------- RLS ----------
alter table public.locations enable row level security;
alter table public.location_paths enable row level security;
alter table public.lessons enable row level security;
alter table public.activities enable row level security;
alter table public.items enable row level security;
alter table public.pet_species enable row level security;
alter table public.characters enable row level security;
alter table public.pets enable row level security;
alter table public.lesson_progress enable row level security;
alter table public.inventory enable row level security;
alter table public.pvp_matches enable row level security;
alter table public.pvp_secrets enable row level security;

create policy "content is public" on public.locations for select using (true);
create policy "content is public" on public.location_paths for select using (true);
create policy "content is public" on public.lessons for select using (true);
create policy "content is public" on public.activities for select using (true);
create policy "content is public" on public.items for select using (true);
create policy "content is public" on public.pet_species for select using (true);

create policy "own character" on public.characters for select using (user_id = (select auth.uid()));
create policy "own pet" on public.pets for select
  using (character_id in (select id from public.characters where user_id = (select auth.uid())));
create policy "own progress" on public.lesson_progress for select
  using (character_id in (select id from public.characters where user_id = (select auth.uid())));
create policy "own inventory" on public.inventory for select
  using (character_id in (select id from public.characters where user_id = (select auth.uid())));
create policy "match participants" on public.pvp_matches for select
  using (
    p1 in (select id from public.characters where user_id = (select auth.uid()))
    or p2 in (select id from public.characters where user_id = (select auth.uid()))
  );
-- pvp_secrets: RLS on, no policy => unreadable by clients

-- ---------- grants: clients can read, never write directly ----------
revoke all on all tables in schema public from anon, authenticated;
grant select on public.locations, public.location_paths, public.lessons, public.activities,
  public.items, public.pet_species to anon, authenticated;
grant select on public.characters, public.pets, public.lesson_progress, public.inventory,
  public.pvp_matches to authenticated;

-- realtime for PvP
do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    alter publication supabase_realtime add table public.pvp_matches;
  end if;
end $$;
