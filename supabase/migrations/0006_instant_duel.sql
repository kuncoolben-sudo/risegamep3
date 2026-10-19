-- No waiting for a second player: pressing "find a match" picks another player's pet right away and the duel
-- is played at once. The opponent is a snapshot of that pet (its stars give the stats, it starts at full HP and
-- Mana); it does not need to be online and nothing happens to its owner. With nobody else around you spar
-- against a practice partner that has your own stats. Only the player who pressed the button gets the result:
-- win/loss, coins and the pet's HP/Mana (HP floor 25).

-- a result is for the challenger (p1) only
create or replace function public._pvp_finish(p_match uuid, p_p1_won boolean) returns void
language plpgsql security definer set search_path = public as $$
declare v_m pvp_matches%rowtype;
begin
  select * into v_m from pvp_matches where id = p_match;
  update pvp_matches
  set status = 'finished', winner = case when p_p1_won then p1 else p2 end, turn = null, updated_at = now()
  where id = p_match;
  if p_p1_won then
    update characters set pvp_wins = pvp_wins + 1, coins = coins + 8 where id = v_m.p1;
  else
    update characters set pvp_losses = pvp_losses + 1, coins = coins + 2 where id = v_m.p1;
  end if;
  update pets set hp = least(max_hp, greatest(25, v_m.p1_hp)), mana = least(max_mana, v_m.p1_mana) where character_id = v_m.p1;
end $$;
revoke execute on function public._pvp_finish(uuid, boolean) from public, anon, authenticated;
drop function if exists public._pvp_finish(uuid, uuid, uuid);

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
  if not found or m.p2_stats is null then raise exception 'match_not_ready'; end if;
  hp := array[m.p1_hp, m.p2_hp];
  mp := array[m.p1_mana, m.p2_mana];
  maxmp := array[coalesce((m.p1_stats ->> 'max_mana')::int, 40), coalesce((m.p2_stats ->> 'max_mana')::int, 40)];
  stg := array[m.p1_stage, m.p2_stage];
  atk := array[(m.p1_stats ->> 'atk')::int, (m.p2_stats ->> 'atk')::int];
  spd := array[(m.p1_stats ->> 'spd')::int, (m.p2_stats ->> 'spd')::int];
  def := array[(m.p1_stats ->> 'def')::int, (m.p2_stats ->> 'def')::int];

  while hp[1] > 0 and hp[2] > 0 and v_n < 60 loop
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

  v_win := case
    when hp[2] = 0 then 1 when hp[1] = 0 then 2
    when hp[1] > hp[2] then 1 when hp[2] > hp[1] then 2
    when random() < 0.5 then 1 else 2 end;
  update pvp_matches set p1_hp = hp[1], p2_hp = hp[2], p1_mana = mp[1], p2_mana = mp[2], log = v_log where id = p_match;
  perform _pvp_finish(p_match, v_win = 1);
end $$;

create or replace function public.pvp_find_match() returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_pet pets%rowtype;
  v_icon text;
  v_o characters%rowtype;
  v_opet pets%rowtype;
  v_oicon text;
  v_spec text;
  v_stats jsonb;
  v_id uuid;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  if not _loc_unlocked(v_char.id, 'arena') then raise exception 'locked'; end if;
  select * into v_pet from pets where character_id = v_char.id;
  select icon into v_icon from pet_species where id = v_pet.species_id;

  delete from pvp_matches where status = 'waiting';   -- the old wait-for-someone matches
  v_stats := _pet_stats(v_char.id);

  -- a random other player's pet, as it is now (stats from its stars, full HP and Mana)
  select c.* into v_o from characters c join pets p on p.character_id = c.id where c.id <> v_char.id order by random() limit 1;
  if found then
    select * into v_opet from pets where character_id = v_o.id;
    select icon into v_oicon from pet_species where id = v_opet.species_id;
    insert into pvp_matches (p1, p2, p1_name, p2_name, p1_pet, p2_pet, p1_species, p2_species, p1_stage, p2_stage,
                             p1_hp, p2_hp, p1_mana, p2_mana, p1_stats, p2_stats, status)
    values (v_char.id, v_o.id, v_char.name, v_o.name, v_icon, v_oicon, v_pet.species_id, v_opet.species_id, v_pet.stage, v_opet.stage,
            v_pet.hp, v_opet.max_hp, v_pet.mana, v_opet.max_mana,
            _pvp_fighter(v_char.id),
            _pet_stats(v_o.id) || jsonb_build_object('hp0', v_opet.max_hp, 'mana0', v_opet.max_mana, 'max_hp', v_opet.max_hp, 'max_mana', v_opet.max_mana),
            'active')
    returning id into v_id;
  else
    -- nobody else yet: a practice partner with your stats and a random pet of your stage
    select id, icon into v_spec, v_oicon from pet_species order by random() limit 1;
    insert into pvp_matches (p1, p2, p1_name, p2_name, p1_pet, p2_pet, p1_species, p2_species, p1_stage, p2_stage,
                             p1_hp, p2_hp, p1_mana, p2_mana, p1_stats, p2_stats, status)
    values (v_char.id, null, v_char.name, 'คู่ซ้อม', v_icon, v_oicon, v_pet.species_id, v_spec, v_pet.stage, v_pet.stage,
            v_pet.hp, 100, v_pet.mana, 40, _pvp_fighter(v_char.id),
            v_stats || jsonb_build_object('hp0', 100, 'mana0', 40, 'max_hp', 100, 'max_mana', 40), 'active')
    returning id into v_id;
  end if;
  perform _pvp_simulate(v_id);
  return v_id;
end $$;
