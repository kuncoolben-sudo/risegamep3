-- Duels are automatic. Nobody picks an action: when the second fighter arrives the server plays the whole duel
-- and stores it as a replay log that both clients show. No elements, no questions, nothing for the client to write.
--
-- Stats come from the stars collected in lessons: ATK, SPD and DEF are each 10 + 2 per star (best result per lesson).
--   SPD   fills an action meter, so a faster pet acts more often
--   ATK/DEF  damage = power * ATK / (ATK + DEF), +-15 %
--   moves a pet with at least 10 Mana casts a power 60 % of the time (costs 10 Mana), otherwise it attacks
--   powers every form up to the pet's stage can be cast, from stage 1 on: half of the casts are the current form's
--           power, the rest are picked at random from the earlier forms
--   power 30 + 10 * form (attack 24); Mana +2 after every action
-- The fighters start from their pet's current HP/Mana and the result carries over (HP floor 25), as before.

alter table public.pvp_matches
  add column if not exists p1_species text,
  add column if not exists p2_species text,
  add column if not exists p1_stats jsonb,
  add column if not exists p2_stats jsonb;

-- matches that were still being played turn by turn can no longer continue
update public.pvp_matches set status = 'finished', turn = null where status = 'active';

-- stars -> stats
create or replace function public._pet_stats(p_char uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('stars', s, 'atk', 10 + 2 * s, 'spd', 10 + 2 * s, 'def', 10 + 2 * s)
  from (select coalesce(sum(stars), 0)::int as s from public.lesson_progress where character_id = p_char) t
$$;

-- what the replay needs to know about a fighter at the start of the duel
create or replace function public._pvp_fighter(p_char uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select public._pet_stats(p_char)
         || jsonb_build_object('hp0', p.hp, 'mana0', p.mana, 'max_hp', p.max_hp, 'max_mana', p.max_mana)
  from public.pets p where p.character_id = p_char
$$;

create or replace function public._pvp_simulate(p_match uuid) returns void
language plpgsql security definer set search_path = public as $$
declare
  m pvp_matches%rowtype;
  hp int[]; mp int[]; maxmp int[]; stg int[]; atk int[]; spd int[]; def int[];
  meter int[] := array[0, 0];
  v_log jsonb := '[]'::jsonb;
  v_n int := 0;
  a int; d int; t int;
  v_kind text; v_form int; v_power numeric; v_dmg int;
  v_win int;
begin
  select * into m from pvp_matches where id = p_match for update;
  if not found or m.p2 is null then raise exception 'match_not_ready'; end if;
  hp := array[m.p1_hp, m.p2_hp];
  mp := array[m.p1_mana, m.p2_mana];
  maxmp := array[coalesce((m.p1_stats ->> 'max_mana')::int, 40), coalesce((m.p2_stats ->> 'max_mana')::int, 40)];
  stg := array[m.p1_stage, m.p2_stage];
  atk := array[(m.p1_stats ->> 'atk')::int, (m.p2_stats ->> 'atk')::int];
  spd := array[(m.p1_stats ->> 'spd')::int, (m.p2_stats ->> 'spd')::int];
  def := array[(m.p1_stats ->> 'def')::int, (m.p2_stats ->> 'def')::int];

  while hp[1] > 0 and hp[2] > 0 and v_n < 60 loop
    -- let the action meters run until somebody reaches 100
    t := greatest(0, least(ceil((100 - meter[1])::numeric / spd[1]), ceil((100 - meter[2])::numeric / spd[2])))::int;
    meter := array[meter[1] + t * spd[1], meter[2] + t * spd[2]];
    if meter[1] >= 100 and (meter[2] < 100 or meter[1] > meter[2] or (meter[1] = meter[2] and random() < 0.5)) then
      a := 1;
    else
      a := 2;
    end if;
    d := 3 - a;
    meter[a] := meter[a] - 100;

    if mp[a] >= 10 and random() < 0.6 then
      v_kind := 'power';
      v_form := case when stg[a] = 1 or random() < 0.5 then stg[a] else 1 + floor(random() * (stg[a] - 1))::int end;
      v_power := 30 + 10 * v_form;
      mp[a] := mp[a] - 10;
    else
      v_kind := 'attack';
      v_form := null;
      v_power := 24;
    end if;
    v_dmg := greatest(1, round(v_power * atk[a] / (atk[a] + def[d])::numeric * (0.85 + random() * 0.3))::int);
    hp[d] := greatest(0, hp[d] - v_dmg);
    mp[a] := least(maxmp[a], mp[a] + 2);
    v_n := v_n + 1;
    v_log := v_log || jsonb_build_array(jsonb_build_object(
      'n', v_n, 'by', a, 'kind', v_kind, 'form', v_form, 'dmg', v_dmg,
      'hp1', hp[1], 'hp2', hp[2], 'mana1', mp[1], 'mana2', mp[2]));
  end loop;

  -- somebody went down, or after 60 actions the one with more HP left wins (a draw is a coin toss)
  v_win := case
    when hp[2] = 0 then 1 when hp[1] = 0 then 2
    when hp[1] > hp[2] then 1 when hp[2] > hp[1] then 2
    when random() < 0.5 then 1 else 2 end;
  update pvp_matches set p1_hp = hp[1], p2_hp = hp[2], p1_mana = mp[1], p2_mana = mp[2], log = v_log where id = p_match;
  perform _pvp_finish(p_match, case when v_win = 1 then m.p1 else m.p2 end, case when v_win = 1 then m.p2 else m.p1 end);
end $$;

-- the first fighter waits; the second one starts the duel, which is over before the call returns
create or replace function public.pvp_find_match() returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_pet pets%rowtype;
  v_p1pet pets%rowtype;
  v_icon text;
  v_m pvp_matches%rowtype;
  v_id uuid;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  if not _loc_unlocked(v_char.id, 'arena') then raise exception 'locked'; end if;
  select * into v_pet from pets where character_id = v_char.id;
  select icon into v_icon from pet_species where id = v_pet.species_id;

  delete from pvp_matches where p1 = v_char.id and status = 'waiting' and created_at < now() - interval '2 minutes';

  select id into v_id from pvp_matches where status = 'waiting' and p1 = v_char.id limit 1;
  if found then return v_id; end if;

  select * into v_m from pvp_matches
  where status = 'waiting' and p1 <> v_char.id and created_at > now() - interval '2 minutes'
  order by created_at limit 1 for update skip locked;
  if found then
    select * into v_p1pet from pets where character_id = v_m.p1;
    update pvp_matches
    set p1_species = v_p1pet.species_id, p1_stage = v_p1pet.stage, p1_hp = v_p1pet.hp, p1_mana = v_p1pet.mana,
        p1_stats = _pvp_fighter(v_m.p1),
        p2 = v_char.id, p2_name = v_char.name, p2_pet = v_icon, p2_species = v_pet.species_id, p2_stage = v_pet.stage,
        p2_hp = v_pet.hp, p2_mana = v_pet.mana, p2_stats = _pvp_fighter(v_char.id),
        status = 'active', updated_at = now()
    where id = v_m.id;
    perform _pvp_simulate(v_m.id);
    return v_m.id;
  end if;

  insert into pvp_matches (p1, p1_name, p1_pet, p1_species, p1_stage, p1_hp, p1_mana)
  values (v_char.id, v_char.name, v_icon, v_pet.species_id, v_pet.stage, v_pet.hp, v_pet.mana)
  returning id into v_id;
  return v_id;
end $$;

-- nothing to act, forfeit or time out any more
drop function if exists public.pvp_act(uuid, text, text);
drop function if exists public.pvp_forfeit(uuid);
drop function if exists public.pvp_claim_timeout(uuid);
drop function if exists public._pvp_new_question(uuid);

revoke execute on function public._pet_stats(uuid), public._pvp_fighter(uuid), public._pvp_simulate(uuid)
  from public, anon, authenticated;
