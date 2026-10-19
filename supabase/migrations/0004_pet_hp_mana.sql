-- HP/Mana belong to the pet only. Characters no longer have HP/Mana.
alter table public.pets
  add column max_hp int not null default 100,
  add column hp int not null default 100,
  add column max_mana int not null default 40,
  add column mana int not null default 40,
  add constraint pets_hp_range check (hp between 0 and max_hp),
  add constraint pets_mana_range check (mana between 0 and max_mana);

update public.pets p
set max_hp = c.max_hp, hp = c.hp, max_mana = c.max_mana, mana = c.mana
from public.characters c where c.id = p.character_id;

alter table public.characters drop column hp, drop column mana, drop column max_hp, drop column max_mana;

-- lessons: still free; the result reports the pet's current HP/Mana
create or replace function public.complete_lesson(
  p_lesson text, p_correct int, p_total int, p_wrong int, p_hints int, p_note text default null
) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_pet pets%rowtype;
  v_lesson lessons%rowtype;
  v_old lesson_progress%rowtype;
  v_n int;
  v_ratio numeric;
  v_stars int;
  v_coins int := 0;
  v_before text[];
  v_after text[];
  v_cleared int;
  v_new_stage int;
  v_drop boolean := false;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  select * into v_pet from pets where character_id = v_char.id;
  select * into v_lesson from lessons where id = p_lesson;
  if not found then raise exception 'lesson_not_found'; end if;
  if not _loc_unlocked(v_char.id, v_lesson.location_id) then raise exception 'locked'; end if;
  if v_char.location_id <> v_lesson.location_id then raise exception 'not_here'; end if;

  select count(*) into v_n from activities where lesson_id = p_lesson;
  if v_n = 0 or p_total <> v_n or p_correct < 0 or p_correct > p_total
     or p_wrong < 0 or p_wrong > 200 or p_hints < 0 or p_hints > 200 then
    raise exception 'invalid_result';
  end if;
  if p_note is not null and char_length(p_note) > 1000 then raise exception 'invalid_note'; end if;

  v_ratio := p_correct::numeric / p_total;
  v_stars := case when v_ratio >= 0.9 then 3 when v_ratio >= 0.75 then 2 else 1 end;

  if v_ratio < v_lesson.pass_ratio then
    return jsonb_build_object('passed', false, 'stars', v_stars, 'coins_gained', 0,
      'hp', v_pet.hp, 'mana', v_pet.mana, 'new_unlocks', '[]'::jsonb, 'evolved', false, 'item_drop', null);
  end if;

  v_before := _unlocked_set(v_char.id);
  select * into v_old from lesson_progress where character_id = v_char.id and lesson_id = p_lesson;

  if not found then
    v_coins := 10 + 5 * v_stars;
    insert into lesson_progress (character_id, lesson_id, best_correct, total, stars, note)
    values (v_char.id, p_lesson, p_correct, p_total, v_stars, p_note);
    v_drop := v_stars = 3;
  else
    v_coins := 2;
    v_drop := v_old.stars < 3 and v_stars = 3;
    update lesson_progress
    set best_correct = greatest(best_correct, p_correct),
        total = p_total,
        stars = greatest(stars, v_stars),
        attempts = attempts + 1,
        note = coalesce(p_note, note)
    where character_id = v_char.id and lesson_id = p_lesson;
  end if;
  update characters set coins = coins + v_coins where id = v_char.id;

  if v_drop then
    insert into inventory (character_id, item_id, qty) values (v_char.id, 'apple', 1)
    on conflict (character_id, item_id) do update set qty = inventory.qty + 1;
  end if;

  select count(*) into v_cleared from lesson_progress where character_id = v_char.id;
  v_new_stage := 1 + (v_cleared >= 6)::int + (v_cleared >= 18)::int;
  if v_new_stage > v_pet.stage then
    update pets set stage = v_new_stage where character_id = v_char.id;
  end if;

  v_after := _unlocked_set(v_char.id);
  return jsonb_build_object(
    'passed', true, 'stars', v_stars, 'coins_gained', v_coins, 'hp', v_pet.hp, 'mana', v_pet.mana,
    'new_unlocks', to_jsonb(array(select unnest(v_after) except select unnest(v_before))),
    'evolved', v_new_stage > v_pet.stage, 'pet_stage', greatest(v_new_stage, v_pet.stage),
    'item_drop', case when v_drop then 'apple' else null end
  );
end $$;

create or replace function public.rest() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_loc locations%rowtype;
  v_cost int := 0;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  if _in_active_match(v_char.id) then raise exception 'in_match'; end if;
  select * into v_loc from locations where id = v_char.location_id;
  if v_loc.kind <> 'rest' then raise exception 'not_a_rest_stop'; end if;

  if v_loc.rest_type = 'inn' then
    v_cost := case when v_char.coins >= 3 then 3 else 0 end;   -- free when you are out of coins
    update pets set hp = max_hp, mana = max_mana where character_id = v_char.id;
    update characters set coins = coins - v_cost where id = v_char.id;
  else
    if v_char.rested_here then raise exception 'already_rested'; end if;
    update pets set hp = least(max_hp, hp + 40), mana = least(max_mana, mana + 15) where character_id = v_char.id;
    update characters set rested_here = true where id = v_char.id;
  end if;
  return (select jsonb_build_object('hp', p.hp, 'mana', p.mana, 'coins', c.coins, 'cost', v_cost)
          from pets p join characters c on c.id = p.character_id where c.id = v_char.id);
end $$;

create or replace function public.use_item(p_item text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_pet pets%rowtype;
  v_item items%rowtype;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  if _in_active_match(v_char.id) then raise exception 'in_match'; end if;
  select * into v_pet from pets where character_id = v_char.id for update;
  select * into v_item from items where id = p_item;
  if not found then raise exception 'item_not_found'; end if;
  if not exists (select 1 from inventory where character_id = v_char.id and item_id = p_item and qty > 0) then
    raise exception 'no_item';
  end if;
  if (v_item.heal_hp = 0 or v_pet.hp >= v_pet.max_hp) and (v_item.heal_mana = 0 or v_pet.mana >= v_pet.max_mana) then
    raise exception 'already_full';
  end if;
  update inventory set qty = qty - 1 where character_id = v_char.id and item_id = p_item;
  update pets
  set hp = least(max_hp, hp + v_item.heal_hp), mana = least(max_mana, mana + v_item.heal_mana)
  where character_id = v_char.id;
  return (select jsonb_build_object('hp', hp, 'mana', mana) from pets where character_id = v_char.id);
end $$;

-- PvP: the pets fight, each from its current HP/Mana
create or replace function public.pvp_find_match() returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_pet pets%rowtype;
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
  update pvp_matches set status = 'finished', turn = null
  where status = 'active' and (p1 = v_char.id or p2 = v_char.id) and updated_at < now() - interval '10 minutes';

  select id into v_id from pvp_matches
  where status in ('waiting', 'active') and (p1 = v_char.id or p2 = v_char.id) limit 1;
  if found then return v_id; end if;

  select * into v_m from pvp_matches
  where status = 'waiting' and p1 <> v_char.id and created_at > now() - interval '2 minutes'
  order by created_at limit 1 for update skip locked;
  if found then
    update pvp_matches
    set p2 = v_char.id, p2_name = v_char.name, p2_pet = v_icon, p2_stage = v_pet.stage,
        p2_hp = v_pet.hp, p2_mana = v_pet.mana,
        p1_hp = (select hp from pets where character_id = v_m.p1),
        p1_mana = (select mana from pets where character_id = v_m.p1),
        status = 'active', turn = p1, updated_at = now()
    where id = v_m.id;
    perform _pvp_new_question(v_m.id);
    return v_m.id;
  end if;

  insert into pvp_matches (p1, p1_name, p1_pet, p1_stage, p1_hp, p1_mana)
  values (v_char.id, v_char.name, v_icon, v_pet.stage, v_pet.hp, v_pet.mana)
  returning id into v_id;
  return v_id;
end $$;

-- the result carries over to the pets (HP floor 25)
create or replace function public._pvp_finish(p_match uuid, p_winner uuid, p_loser uuid) returns void
language plpgsql security definer set search_path = public as $$
declare v_m pvp_matches%rowtype;
begin
  select * into v_m from pvp_matches where id = p_match;
  update pvp_matches set status = 'finished', winner = p_winner, turn = null, updated_at = now() where id = p_match;
  update characters set pvp_wins = pvp_wins + 1, coins = coins + 8 where id = p_winner;
  update characters set pvp_losses = pvp_losses + 1, coins = coins + 2 where id = p_loser;
  update pets set hp = least(max_hp, greatest(25, v_m.p1_hp)), mana = least(max_mana, v_m.p1_mana) where character_id = v_m.p1;
  update pets set hp = least(max_hp, greatest(25, v_m.p2_hp)), mana = least(max_mana, v_m.p2_mana) where character_id = v_m.p2;
end $$;
