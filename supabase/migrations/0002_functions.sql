-- RISE English Adventure: game rules as security-definer RPCs.
-- Clients never write tables directly; every state change goes through here.

-- ---------- internal helpers (not callable by clients) ----------
create or replace function public._char_id() returns uuid
language sql stable security definer set search_path = public as $$
  select id from public.characters where user_id = auth.uid()
$$;

-- a location is cleared when it has required lessons and all are completed
create or replace function public._loc_cleared(p_char uuid, p_loc text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.lessons l where l.location_id = p_loc and l.required)
    and not exists (
      select 1 from public.lessons l
      where l.location_id = p_loc and l.required
        and not exists (
          select 1 from public.lesson_progress lp
          where lp.character_id = p_char and lp.lesson_id = l.id
        )
    )
$$;

create or replace function public._loc_unlocked(p_char uuid, p_loc text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.locations where id = p_loc)
    and not exists (
      select 1
      from public.locations loc
      cross join lateral unnest(loc.requires) as r
      where loc.id = p_loc and not public._loc_cleared(p_char, r)
    )
$$;

create or replace function public._unlocked_set(p_char uuid) returns text[]
language sql stable security definer set search_path = public as $$
  select coalesce(array_agg(id order by id), '{}')
  from public.locations
  where public._loc_unlocked(p_char, id)
$$;

-- ---------- map state ----------
create or replace function public.location_states()
returns table (location_id text, status text)
language sql stable security definer set search_path = public as $$
  select l.id,
    case
      when not public._loc_unlocked(public._char_id(), l.id) then 'locked'
      when public._loc_cleared(public._char_id(), l.id) then 'cleared'
      else 'open'
    end
  from public.locations l
  where public._char_id() is not null
$$;

-- ---------- character creation (one-time, with exactly one pet) ----------
create or replace function public.create_character(p_name text, p_appearance jsonb, p_species text)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_name text := btrim(coalesce(p_name, ''));
  v_id uuid;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  if char_length(v_name) < 1 or char_length(v_name) > 20 then raise exception 'invalid_name'; end if;
  if jsonb_typeof(p_appearance) is distinct from 'object' then raise exception 'invalid_appearance'; end if;
  if pg_column_size(p_appearance) > 2000 then raise exception 'invalid_appearance'; end if;
  if not exists (select 1 from pet_species where id = p_species) then raise exception 'invalid_pet'; end if;
  if exists (select 1 from characters where user_id = auth.uid()) then raise exception 'character_exists'; end if;

  insert into characters (user_id, name, appearance) values (auth.uid(), v_name, p_appearance)
  returning id into v_id;
  insert into pets (character_id, species_id) values (v_id, p_species);
  insert into inventory (character_id, item_id, qty) values (v_id, 'apple', 2), (v_id, 'tea', 1);
  return v_id;
end $$;

-- ---------- travel ----------
create or replace function public.travel(p_loc text) returns void
language plpgsql security definer set search_path = public as $$
declare v_char characters%rowtype;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  if not _loc_unlocked(v_char.id, p_loc) then raise exception 'locked'; end if;
  if v_char.location_id <> p_loc then
    update characters set location_id = p_loc, rested_here = false where id = v_char.id;
  end if;
end $$;

-- ---------- lessons ----------
-- p_correct: activities answered correctly on first try; p_wrong: wrong taps; p_hints: hints used.
create or replace function public.complete_lesson(
  p_lesson text, p_correct int, p_total int, p_wrong int, p_hints int, p_note text default null
) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_lesson lessons%rowtype;
  v_old lesson_progress%rowtype;
  v_n int;
  v_ratio numeric;
  v_stars int;
  v_coins int := 0;
  v_exhausted boolean;
  v_before text[];
  v_after text[];
  v_cleared int;
  v_old_stage int;
  v_new_stage int;
  v_drop boolean := false;
  v_hp int;
  v_mana int;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
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
  v_exhausted := v_char.hp * 10 <= v_char.max_hp;
  v_stars := case when v_ratio >= 0.9 then 3 when v_ratio >= 0.75 then 2 else 1 end;

  -- mild costs: wrong answers never drop below 1 HP, hints spend Mana
  v_hp := greatest(1, v_char.hp - 5 * p_wrong);
  v_mana := greatest(0, v_char.mana - 3 * p_hints);
  update characters set hp = v_hp, mana = v_mana where id = v_char.id;

  if v_ratio < v_lesson.pass_ratio then
    return jsonb_build_object('passed', false, 'stars', v_stars, 'coins_gained', 0,
      'hp', v_hp, 'mana', v_mana, 'new_unlocks', '[]'::jsonb, 'evolved', false, 'item_drop', null);
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
  if v_exhausted then v_coins := v_coins / 2; end if;
  update characters set coins = coins + v_coins where id = v_char.id;

  if v_drop then
    insert into inventory (character_id, item_id, qty) values (v_char.id, 'apple', 1)
    on conflict (character_id, item_id) do update set qty = inventory.qty + 1;
  end if;

  select count(*) into v_cleared from lesson_progress where character_id = v_char.id;
  select stage into v_old_stage from pets where character_id = v_char.id;
  v_new_stage := 1 + (v_cleared >= 6)::int + (v_cleared >= 18)::int;
  if v_new_stage > v_old_stage then
    update pets set stage = v_new_stage where character_id = v_char.id;
  end if;

  v_after := _unlocked_set(v_char.id);
  return jsonb_build_object(
    'passed', true, 'stars', v_stars, 'coins_gained', v_coins, 'hp', v_hp, 'mana', v_mana,
    'new_unlocks', to_jsonb(array(select unnest(v_after) except select unnest(v_before))),
    'evolved', v_new_stage > v_old_stage, 'pet_stage', greatest(v_new_stage, v_old_stage),
    'item_drop', case when v_drop then 'apple' else null end
  );
end $$;

-- ---------- rest stops ----------
create or replace function public.rest() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_loc locations%rowtype;
  v_cost int := 0;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  select * into v_loc from locations where id = v_char.location_id;
  if v_loc.kind <> 'rest' then raise exception 'not_a_rest_stop'; end if;

  if v_loc.rest_type = 'inn' then
    v_cost := case when v_char.coins >= 3 then 3 else 0 end;   -- free when you are out of coins
    update characters set hp = max_hp, mana = max_mana, coins = coins - v_cost where id = v_char.id;
  else
    if v_char.rested_here then raise exception 'already_rested'; end if;
    update characters
    set hp = least(max_hp, hp + 40), mana = least(max_mana, mana + 15), rested_here = true
    where id = v_char.id;
  end if;
  return (select jsonb_build_object('hp', hp, 'mana', mana, 'coins', coins, 'cost', v_cost)
          from characters where id = v_char.id);
end $$;

-- ---------- items ----------
create or replace function public.use_item(p_item text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_item items%rowtype;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  select * into v_item from items where id = p_item;
  if not found then raise exception 'item_not_found'; end if;
  if not exists (select 1 from inventory where character_id = v_char.id and item_id = p_item and qty > 0) then
    raise exception 'no_item';
  end if;
  if (v_item.heal_hp = 0 or v_char.hp >= v_char.max_hp) and (v_item.heal_mana = 0 or v_char.mana >= v_char.max_mana) then
    raise exception 'already_full';
  end if;
  update inventory set qty = qty - 1 where character_id = v_char.id and item_id = p_item;
  update characters
  set hp = least(max_hp, hp + v_item.heal_hp), mana = least(max_mana, mana + v_item.heal_mana)
  where id = v_char.id;
  return (select jsonb_build_object('hp', hp, 'mana', mana) from characters where id = v_char.id);
end $$;

create or replace function public.buy_item(p_item text, p_qty int default 1) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_item items%rowtype;
  v_total int;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  if p_qty < 1 or p_qty > 10 then raise exception 'invalid_qty'; end if;
  if not exists (select 1 from locations where id = v_char.location_id and rest_type = 'inn') then
    raise exception 'not_at_inn';
  end if;
  select * into v_item from items where id = p_item;
  if not found then raise exception 'item_not_found'; end if;
  v_total := v_item.price * p_qty;
  if v_char.coins < v_total then raise exception 'not_enough_coins'; end if;
  update characters set coins = coins - v_total where id = v_char.id;
  insert into inventory (character_id, item_id, qty) values (v_char.id, p_item, p_qty)
  on conflict (character_id, item_id) do update set qty = inventory.qty + p_qty;
  return jsonb_build_object('coins', v_char.coins - v_total);
end $$;

-- ---------- PvP 1v1 (turn based, no elements) ----------
create or replace function public._pvp_new_question(p_match uuid) returns void
language plpgsql security definer set search_path = public as $$
declare v_a activities%rowtype;
begin
  select * into v_a from activities where type in ('qa_choose', 'listen_choose') order by random() limit 1;
  if not found then raise exception 'no_questions'; end if;
  update pvp_matches
  set q_prompt = case when v_a.type = 'qa_choose' then v_a.payload ->> 'question' else 'Listen and choose' end,
      q_say = v_a.payload ->> 'say',
      q_choices = v_a.payload -> 'choices'
  where id = p_match;
  insert into pvp_secrets (match_id, q_answer) values (p_match, v_a.payload ->> 'answer')
  on conflict (match_id) do update set q_answer = excluded.q_answer;
end $$;

create or replace function public._pvp_finish(p_match uuid, p_winner uuid, p_loser uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  update pvp_matches set status = 'finished', winner = p_winner, turn = null, updated_at = now() where id = p_match;
  update characters set pvp_wins = pvp_wins + 1, coins = coins + 8 where id = p_winner;
  update characters set pvp_losses = pvp_losses + 1, coins = coins + 2 where id = p_loser;
end $$;

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
        status = 'active', turn = p1, updated_at = now()
    where id = v_m.id;
    perform _pvp_new_question(v_m.id);
    return v_m.id;
  end if;

  insert into pvp_matches (p1, p1_name, p1_pet, p1_stage)
  values (v_char.id, v_char.name, v_icon, v_pet.stage)
  returning id into v_id;
  return v_id;
end $$;

create or replace function public.pvp_cancel(p_match uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  delete from pvp_matches where id = p_match and status = 'waiting' and p1 = _char_id();
end $$;

-- action: attack | skill | guard | focus; answer: the chosen answer text for this turn's question
create or replace function public.pvp_act(p_match uuid, p_action text, p_answer text default null)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_me uuid := _char_id();
  v_m pvp_matches%rowtype;
  v_p1 boolean;
  v_stage int; v_mana int; v_hp int; v_opp_hp int; v_opp_guard boolean; v_opp uuid;
  v_ans text;
  v_ok boolean;
  v_dmg int := 0;
  v_my_name text;
begin
  if v_me is null then raise exception 'no_character'; end if;
  select * into v_m from pvp_matches where id = p_match for update;
  if not found or v_m.status <> 'active' then raise exception 'match_not_active'; end if;
  if v_m.turn is distinct from v_me then raise exception 'not_your_turn'; end if;

  v_p1 := v_m.p1 = v_me;
  v_stage := case when v_p1 then v_m.p1_stage else v_m.p2_stage end;
  v_mana := case when v_p1 then v_m.p1_mana else v_m.p2_mana end;
  v_hp := case when v_p1 then v_m.p1_hp else v_m.p2_hp end;
  v_opp := case when v_p1 then v_m.p2 else v_m.p1 end;
  v_opp_hp := case when v_p1 then v_m.p2_hp else v_m.p1_hp end;
  v_opp_guard := case when v_p1 then v_m.p2_guard else v_m.p1_guard end;
  v_my_name := case when v_p1 then v_m.p1_name else v_m.p2_name end;

  select q_answer into v_ans from pvp_secrets where match_id = p_match;
  v_ok := p_answer is not null and lower(btrim(p_answer)) = lower(btrim(v_ans));

  if p_action = 'attack' then
    v_dmg := round((10 + 2 * v_stage) * case when v_ok then 1.5 else 0.75 end);
  elsif p_action = 'skill' then
    if v_stage < 2 then raise exception 'skill_locked'; end if;
    if v_mana < 10 then raise exception 'no_mana'; end if;
    v_mana := v_mana - 10;
    v_dmg := round((18 + 3 * v_stage) * case when v_ok then 1.3 else 0.65 end);
  elsif p_action = 'focus' then
    v_mana := least(40, v_mana + case when v_ok then 12 else 8 end);
    v_hp := least(100, v_hp + 5);
  elsif p_action <> 'guard' then
    raise exception 'invalid_action';
  end if;

  if v_dmg > 0 and v_opp_guard then
    v_dmg := ceil(v_dmg / 2.0);
  end if;
  if v_dmg > 0 then v_opp_guard := false; end if;
  v_opp_hp := greatest(0, v_opp_hp - v_dmg);
  v_mana := least(40, v_mana + 2);

  if v_p1 then
    update pvp_matches set p1_hp = v_hp, p1_mana = v_mana, p1_guard = (p_action = 'guard'),
      p2_hp = v_opp_hp, p2_guard = v_opp_guard where id = p_match;
  else
    update pvp_matches set p2_hp = v_hp, p2_mana = v_mana, p2_guard = (p_action = 'guard'),
      p1_hp = v_opp_hp, p1_guard = v_opp_guard where id = p_match;
  end if;

  update pvp_matches
  set log = log || jsonb_build_array(jsonb_build_object(
        'round', v_m.round, 'actor', v_my_name, 'action', p_action, 'correct', v_ok, 'damage', v_dmg)),
      updated_at = now()
  where id = p_match;

  if v_opp_hp = 0 then
    perform _pvp_finish(p_match, v_me, v_opp);
  else
    update pvp_matches set turn = v_opp, round = round + 1 where id = p_match;
    perform _pvp_new_question(p_match);
  end if;
end $$;

create or replace function public.pvp_forfeit(p_match uuid) returns void
language plpgsql security definer set search_path = public as $$
declare v_me uuid := _char_id(); v_m pvp_matches%rowtype;
begin
  select * into v_m from pvp_matches where id = p_match for update;
  if not found or v_m.status <> 'active' or v_me not in (v_m.p1, v_m.p2) then return; end if;
  perform _pvp_finish(p_match, case when v_me = v_m.p1 then v_m.p2 else v_m.p1 end, v_me);
end $$;

-- the waiting player may claim the win if the opponent has been idle for 90 seconds
create or replace function public.pvp_claim_timeout(p_match uuid) returns boolean
language plpgsql security definer set search_path = public as $$
declare v_me uuid := _char_id(); v_m pvp_matches%rowtype;
begin
  select * into v_m from pvp_matches where id = p_match for update;
  if not found or v_m.status <> 'active' or v_me not in (v_m.p1, v_m.p2) then return false; end if;
  if v_m.turn = v_me or v_m.updated_at > now() - interval '90 seconds' then return false; end if;
  perform _pvp_finish(p_match, v_me, v_m.turn);
  return true;
end $$;

-- ---------- execute privileges ----------
revoke execute on all functions in schema public from public, anon, authenticated;
grant execute on function
  public.location_states(), public.create_character(text, jsonb, text), public.travel(text),
  public.complete_lesson(text, int, int, int, int, text), public.rest(), public.use_item(text),
  public.buy_item(text, int), public.pvp_find_match(), public.pvp_cancel(uuid),
  public.pvp_act(uuid, text, text), public.pvp_forfeit(uuid), public.pvp_claim_timeout(uuid)
to authenticated;
