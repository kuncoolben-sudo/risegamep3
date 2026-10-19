\set ON_ERROR_STOP on
\set ua '00000000-0000-0000-0000-00000000000a'
\set ub '00000000-0000-0000-0000-00000000000b'
insert into auth.users (id) values (:'ua'), (:'ub');

create function pg_temp.expect_err(sql text, want text) returns void language plpgsql as $$
begin
  begin
    execute sql;
  exception when others then
    if sqlerrm not like '%' || want || '%' then raise exception 'expected "%" but got "%" for: %', want, sqlerrm, sql; end if;
    return;
  end;
  raise exception 'expected error "%" but statement succeeded: %', want, sql;
end $$;

create function pg_temp.assert(cond boolean, msg text) returns void language plpgsql as $$
begin if not coalesce(cond, false) then raise exception 'ASSERT FAILED: %', msg; end if; end $$;

-- plays every required lesson of the location the player is standing in (all correct)
create function pg_temp.clear_here() returns int language plpgsql as $$
declare l record; n int; c int := 0;
begin
  for l in select id, location_id from public.lessons
           where location_id = (select location_id from public.characters where user_id = auth.uid()) and required order by sort loop
    select count(*) into n from public.activities where lesson_id = l.id;
    perform public.complete_lesson(l.id, n, n, 0, 0);
    c := c + 1;
  end loop;
  return c;
end $$;

-- ===== seed sanity =====
select pg_temp.assert((select count(*) from public.locations) = 16, '16 locations');
select pg_temp.assert((select count(*) from public.activities) > 100, 'activities seeded');
select pg_temp.assert(not exists (select 1 from public.lessons l where l.required and not exists (select 1 from public.activities a where a.lesson_id = l.id)), 'every required lesson has activities');

-- ===== player A =====
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);

select pg_temp.expect_err($$ select public.create_character('Ann', '{}', 'dragon') $$, 'invalid_pet');
select pg_temp.expect_err($$ select public.create_character('', '{}', 'lion') $$, 'invalid_name');
select public.create_character('Ann', '{"hair":"long wavy hair"}', 'lion');
select pg_temp.expect_err($$ select public.create_character('Ann2', '{}', 'parrot') $$, 'character_exists');
select pg_temp.assert((select count(*) from public.pets) = 1, 'exactly one pet');
select pg_temp.expect_err($$ insert into public.pets (character_id, species_id) select id, 'parrot' from public.characters $$, 'permission denied');
select pg_temp.expect_err($$ update public.characters set coins = 9999 $$, 'permission denied');
select pg_temp.expect_err($$ select * from public.pvp_secrets $$, 'permission denied');

select pg_temp.assert((select status from public.location_states() where location_id = 'start') = 'open', 'start open');
select pg_temp.assert((select status from public.location_states() where location_id = 'u1') = 'locked', 'u1 locked');
select pg_temp.expect_err($$ select public.travel('u1') $$, 'locked');
select pg_temp.expect_err($$ select public.complete_lesson('u1-l1', 1, 1, 0, 0) $$, 'locked');
select pg_temp.expect_err($$ select public.complete_lesson('start-l1', 99, 99, 0, 0) $$, 'invalid_result');

-- starter lesson: cheating on the total is rejected, honest result unlocks u1 + arena
select pg_temp.assert(pg_temp.clear_here() = 1, 'starter cleared');
select pg_temp.assert((select status from public.location_states() where location_id = 'u1') = 'open', 'u1 opened');
select pg_temp.assert((select status from public.location_states() where location_id = 'arena') = 'open', 'arena opened');
select pg_temp.assert((select coins from public.characters) = 45, 'coins 20 + 25 for 3 stars');

-- HP/Mana are PvP-only: wrong answers and hints in lessons cost nothing
select public.travel('u1');
select pg_temp.expect_err($$ select public.complete_lesson('u1-l1', 2, 3, 0, 0) $$, 'invalid_result');
select public.complete_lesson('u1-l1', (select count(*)::int from public.activities where lesson_id = 'u1-l1'),
  (select count(*)::int from public.activities where lesson_id = 'u1-l1'), 100, 2);
select pg_temp.assert((select hp from public.pets) = 100, 'wrong answers do not cost HP');
select pg_temp.assert((select mana from public.pets) = 40, 'hints do not cost Mana');
select pg_temp.assert(not exists (select 1 from information_schema.columns where table_name = 'characters' and column_name in ('hp', 'mana', 'max_hp', 'max_mana')), 'characters have no HP/Mana');

-- project is optional: clearing the 4 required lessons clears u1 and opens u2
select pg_temp.clear_here();
select pg_temp.assert((select status from public.location_states() where location_id = 'u1') = 'cleared', 'u1 cleared');
select pg_temp.assert((select status from public.location_states() where location_id = 'u2') = 'open', 'u2 opened');
select pg_temp.assert((select count(*) from public.lesson_progress where lesson_id = 'u1-proj') = 0, 'project not auto-completed');
select pg_temp.assert((select stage from public.pets) = 1, 'pet still stage 1 after 5 lessons');

-- rest stops
select pg_temp.expect_err($$ select public.rest() $$, 'not_a_rest_stop');
-- the pet hospital next to the arena: open from the start, heals to full for free
reset role;
update public.pets set hp = 10, mana = 0 where character_id = (select id from public.characters where user_id = :'ua');
create temp table hosp as select coins as c0 from public.characters where user_id = :'ua';
grant select on hosp to authenticated;
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
select public.travel('hospital');
select pg_temp.assert((select (public.rest() ->> 'hp')::int) = 100, 'hospital heals HP to full');
select pg_temp.assert((select mana from public.pets) = 40, 'hospital restores Mana to full');
select pg_temp.assert((select coins from public.characters) = (select c0 from hosp), 'treatment is free');
select public.buy_item('apple', 1);   -- the hospital also sells items
select pg_temp.assert((select coins from public.characters) < (select c0 from hosp), 'bought an apple');
select public.rest();   -- and again: no once-per-visit limit
reset role;
update public.characters set coins = (select c0 from hosp) where user_id = :'ua';
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
select public.travel('start');
select public.travel('u2');
select pg_temp.clear_here();
select pg_temp.assert((select stage from public.pets) = 2, 'pet evolved after 6+ lessons');
reset role;
update public.pets set hp = 1, mana = 0 where character_id = (select id from public.characters where user_id = :'ua');
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
select public.travel('campA');
select pg_temp.assert((select (public.rest() ->> 'hp')::int) = 41, 'camp heals 40');
select pg_temp.assert((select mana from public.pets) = 15, 'camp restores 15 mana');
select pg_temp.expect_err($$ select public.rest() $$, 'already_rested');
select public.travel('u3');
select public.travel('campA');
select public.rest();                       -- fresh arrival allows camp again
select pg_temp.expect_err($$ select public.buy_item('apple', 1) $$, 'not_at_inn');

-- items
select public.use_item('apple');
select public.use_item('tea');
select pg_temp.assert((select hp from public.pets) = 100 and (select mana from public.pets) = 40, 'items restore to full');
select pg_temp.expect_err($$ select public.use_item('apple') $$, 'already_full');
select pg_temp.expect_err($$ select public.use_item('sandwich') $$, 'no_item');

-- ===== riverside hospital: climb to u4 using direct progress (as postgres) =====
reset role;
insert into public.lesson_progress (character_id, lesson_id, best_correct, total, stars)
select c.id, l.id, 1, 1, 3 from public.characters c, public.lessons l
where c.user_id = :'ua' and l.required and l.location_id in ('u3', 'u4')
on conflict do nothing;
update public.characters set coins = 40 where user_id = :'ua';
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
select public.travel('inn1');
select pg_temp.assert((select (public.rest() ->> 'hp')::int) = 100, 'riverside hospital heals to full');
select pg_temp.assert((select coins from public.characters) = 40, 'treatment is free');
select public.buy_item('sandwich', 2);
select pg_temp.assert((select coins from public.characters) = 16, 'bought 2 sandwiches');
select pg_temp.expect_err($$ select public.buy_item('sandwich', 5) $$, 'not_enough_coins');

-- ===== PvP: instant duels against another player's pet =====
reset role;
set role authenticated;
select set_config('request.jwt.claim.sub', :'ub', false);
select public.create_character('Ben', '{}', 'parrot');
select pg_temp.expect_err($$ select public.pvp_find_match() $$, 'locked');
reset role;
insert into public.lesson_progress (character_id, lesson_id, best_correct, total, stars)
select c.id, 'start-l1', 1, 1, 3 from public.characters c where c.user_id = :'ub';
update public.pets set hp = 60, mana = 30 where character_id = (select id from public.characters where user_id = :'ua');
update public.pets set hp = 50, mana = 5 where character_id = (select id from public.characters where user_id = :'ub');
create temp table before as select coins as b_coins from public.characters where user_id = :'ub';
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);

-- no waiting: the duel is played and over before the call returns
create temp table m as select public.pvp_find_match() as id;
reset role;
select pg_temp.assert((select status = 'finished' and winner is not null and jsonb_array_length(log) between 2 and 60 from public.pvp_matches where id = (select id from m)), 'duel played at once');
select pg_temp.assert((select p1 = (select id from public.characters where user_id = :'ua') and p2 = (select id from public.characters where user_id = :'ub') from public.pvp_matches), 'the opponent is the other player');
select pg_temp.assert((select p1_species = 'lion' and p2_species = 'parrot' and p1_stage >= 1 and p2_stage = 1 from public.pvp_matches), 'species and stages recorded');
select pg_temp.assert((select (log -> 0) ? 'n' and (log -> 0) ? 'by' and (log -> 0) ? 'kind' and (log -> 0) ? 'dmg' and (log -> 0) ? 'hp1' from public.pvp_matches), 'log entries have the replay fields');
select pg_temp.expect_err($$ select public.pvp_act(null::uuid, 'attack', 'x') $$, 'does not exist');
select pg_temp.expect_err($$ select public.pvp_claim_timeout(null::uuid) $$, 'does not exist');

-- the opponent is a snapshot: full HP/Mana, nothing happens to its owner
select pg_temp.assert((select (p2_stats ->> 'hp0')::int = 100 and (p2_stats ->> 'mana0')::int = 40 from public.pvp_matches), 'opponent starts at full HP and Mana');
select pg_temp.assert((select pvp_wins = 0 and pvp_losses = 0 and coins = (select b_coins from before) from public.characters where user_id = :'ub'), 'the opponent owner gets no result');
select pg_temp.assert((select hp = 50 and mana = 5 from public.pets where character_id = (select id from public.characters where user_id = :'ub')), 'the opponent pet is untouched');

-- stats = 10 + 2 per star on every stat, taken from the best result of each lesson
select pg_temp.assert((select (p1_stats ->> 'stars')::int = (select coalesce(sum(stars), 0) from public.lesson_progress where character_id = p1)
                       and (p1_stats ->> 'atk')::int = 10 + 2 * (p1_stats ->> 'stars')::int
                       and (p1_stats ->> 'spd')::int = (p1_stats ->> 'atk')::int and (p1_stats ->> 'def')::int = (p1_stats ->> 'atk')::int
                       from public.pvp_matches), 'A stats come from stars');
select pg_temp.assert((select (p2_stats ->> 'stars')::int = 3 and (p2_stats ->> 'atk')::int = 16 and (p2_stats ->> 'spd')::int = 16 and (p2_stats ->> 'def')::int = 16 from public.pvp_matches), 'B: 3 stars = 16 on each stat');
select pg_temp.assert((select (p1_stats ->> 'hp0')::int = 60 and (p1_stats ->> 'mana0')::int = 30 from public.pvp_matches), 'the challenger starts from the pets current HP/Mana');
-- the log is consistent: HP only goes down, the last entry is the final state, powers only up to the actor's stage
select pg_temp.assert((select bool_and(coalesce(hp1 <= lag_hp1, true) and coalesce(hp2 <= lag_hp2, true))
                       from (select (e ->> 'hp1')::int as hp1, (e ->> 'hp2')::int as hp2,
                                    lag((e ->> 'hp1')::int) over (order by (e ->> 'n')::int) as lag_hp1,
                                    lag((e ->> 'hp2')::int) over (order by (e ->> 'n')::int) as lag_hp2
                             from public.pvp_matches, jsonb_array_elements(log) e) x), 'HP never goes up during a duel');
select pg_temp.assert((select (log -> -1 ->> 'hp1')::int = p1_hp and (log -> -1 ->> 'hp2')::int = p2_hp and (p1_hp = 0 or p2_hp = 0 or jsonb_array_length(log) = 60) from public.pvp_matches), 'last log entry is the final state');
select pg_temp.assert(not exists (select 1 from public.pvp_matches, jsonb_array_elements(log) e
                                   where (e ->> 'kind' = 'power' and ((e ->> 'form')::int < 1 or (e ->> 'form')::int > case when (e ->> 'by')::int = 1 then p1_stage else p2_stage end))
                                      or (e ->> 'kind' = 'attack' and e ->> 'form' is not null)), 'powers stay within the unlocked forms');
-- only the challenger gets the result
select pg_temp.assert((select pvp_wins + pvp_losses = 1 from public.characters where user_id = :'ua'), 'win/loss recorded for the challenger');
select pg_temp.assert((select c.hp = greatest(25, pm.p1_hp) and c.mana = pm.p1_mana from public.pvp_matches pm join public.pets c on c.character_id = pm.p1), 'A pet keeps the duel HP/Mana (floor 25)');
select pg_temp.assert((select (winner = p1) = (pvp_wins = 1) from public.pvp_matches, public.characters where characters.id = p1), 'winner matches the record');

-- another duel straight away, and a practice partner when nobody else exists
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
create temp table m2 as select public.pvp_find_match() as id;
reset role;
select pg_temp.assert((select id from m2) <> (select id from m), 'a new duel right away');
do $$
declare v_id uuid; v_m public.pvp_matches%rowtype;
begin
  begin
    delete from public.characters where user_id = '00000000-0000-0000-0000-00000000000b';
    perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', true);
    v_id := public.pvp_find_match();
    select * into v_m from public.pvp_matches where id = v_id;
    if not (v_m.status = 'finished' and v_m.p2 is null and v_m.p2_name is not null and v_m.p2_species is not null
            and v_m.p2_stats ->> 'atk' = v_m.p1_stats ->> 'atk' and jsonb_array_length(v_m.log) > 0) then
      raise exception 'ASSERT FAILED: practice partner duel';
    end if;
    raise exception 'rolled back on purpose';
  exception when others then
    if sqlerrm <> 'rolled back on purpose' then raise; end if;
  end;
end $$;

-- matchmaking: the opponent is one of the three players closest in stars (three clones of A's progress vs far-off B)
insert into auth.users (id) select gen_random_uuid() from generate_series(1, 3);
insert into public.characters (user_id, name, appearance)
select id, 'Clone' || row_number() over (), '{}' from auth.users where id not in (:'ua', :'ub');
insert into public.pets (character_id, species_id) select id, 'lion' from public.characters where name like 'Clone%';
insert into public.lesson_progress (character_id, lesson_id, best_correct, total, stars)
select cl.id, lp.lesson_id, lp.best_correct, lp.total, lp.stars
from public.characters cl, public.lesson_progress lp where cl.name like 'Clone%' and lp.character_id = (select id from public.characters where user_id = :'ua');
create temp table near (i int, opp uuid);
do $$
declare i int; v_id uuid;
begin
  perform set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', true);
  for i in 1..30 loop
    v_id := public.pvp_find_match();
    insert into near select i, p2 from public.pvp_matches where id = v_id;
  end loop;
end $$;
select pg_temp.assert(not exists (select 1 from near where opp = (select id from public.characters where user_id = :'ub')), 'the far-off player is never picked while closer ones exist');
select pg_temp.assert((select count(distinct opp) = 3 from near), 'all three close players come up');

-- many duels with set stats: the stronger and faster pet wins, a stage-3 pet casts every form it has, a stage-1 pet only its first
create temp table sim (a_wins boolean, a_forms int[], b_forms int[], a_acts int, b_acts int);
do $$
declare
  ua_c uuid := (select id from public.characters where user_id = '00000000-0000-0000-0000-00000000000a');
  ub_c uuid := (select id from public.characters where user_id = '00000000-0000-0000-0000-00000000000b');
  v_id uuid; v_m public.pvp_matches%rowtype; i int;
begin
  for i in 1..40 loop
    insert into public.pvp_matches (p1, p2, p1_name, p2_name, p1_pet, p2_pet, p1_species, p2_species, p1_stage, p2_stage, p1_hp, p2_hp, p1_mana, p2_mana, status, p1_stats, p2_stats)
    values (ua_c, ub_c, 'A', 'B', 'x', 'y', 'skyra', 'blazion', 3, 1, 100, 100, 40, 40, 'active',
            '{"stars":40,"atk":90,"spd":90,"def":90,"max_mana":40}', '{"stars":3,"atk":16,"spd":16,"def":16,"max_mana":40}')
    returning id into v_id;
    perform public._pvp_simulate(v_id);
    select * into v_m from public.pvp_matches where id = v_id;
    insert into sim values (
      v_m.winner = ua_c,
      array(select (e ->> 'form')::int from jsonb_array_elements(v_m.log) e where e ->> 'kind' = 'power' and (e ->> 'by')::int = 1),
      array(select (e ->> 'form')::int from jsonb_array_elements(v_m.log) e where e ->> 'kind' = 'power' and (e ->> 'by')::int = 2),
      (select count(*) from jsonb_array_elements(v_m.log) e where (e ->> 'by')::int = 1),
      (select count(*) from jsonb_array_elements(v_m.log) e where (e ->> 'by')::int = 2));
  end loop;
end $$;
select pg_temp.assert((select count(*) from sim where a_wins) >= 38, 'the pet with far more stars wins (got ' || (select count(*) from sim where a_wins) || ' of 40)');
select pg_temp.assert((select sum(a_acts) > 2 * sum(b_acts) from sim), 'a faster pet acts more often');
select pg_temp.assert((select count(distinct f) = 3 from sim, unnest(a_forms) f), 'a stage 3 pet casts forms 1, 2 and 3');
select pg_temp.assert((select count(*) filter (where f = 3)::numeric / count(*) between 0.35 and 0.65 from sim, unnest(a_forms) f), 'about half of the casts are the current form');
select pg_temp.assert(not exists (select 1 from sim, unnest(b_forms) f where f <> 1), 'a stage 1 pet only casts form 1');

set role authenticated;
select set_config('request.jwt.claim.sub', :'ub', false);
select pg_temp.assert((select count(*) from public.characters) = 1, 'B only sees own character (RLS)');
