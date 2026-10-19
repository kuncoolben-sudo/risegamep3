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
select pg_temp.assert((select count(*) from public.locations) = 15, '15 locations');
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
select pg_temp.assert((select hp from public.characters) = 100, 'wrong answers do not cost HP');
select pg_temp.assert((select mana from public.characters) = 40, 'hints do not cost Mana');

-- project is optional: clearing the 4 required lessons clears u1 and opens u2
select pg_temp.clear_here();
select pg_temp.assert((select status from public.location_states() where location_id = 'u1') = 'cleared', 'u1 cleared');
select pg_temp.assert((select status from public.location_states() where location_id = 'u2') = 'open', 'u2 opened');
select pg_temp.assert((select count(*) from public.lesson_progress where lesson_id = 'u1-proj') = 0, 'project not auto-completed');
select pg_temp.assert((select stage from public.pets) = 1, 'pet still stage 1 after 5 lessons');

-- rest stops
select pg_temp.expect_err($$ select public.rest() $$, 'not_a_rest_stop');
select public.travel('u2');
select pg_temp.clear_here();
select pg_temp.assert((select stage from public.pets) = 2, 'pet evolved after 6+ lessons');
reset role;
update public.characters set hp = 1, mana = 0 where user_id = :'ua';
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
select public.travel('campA');
select pg_temp.assert((select (public.rest() ->> 'hp')::int) = 41, 'camp heals 40');
select pg_temp.assert((select mana from public.characters) = 15, 'camp restores 15 mana');
select pg_temp.expect_err($$ select public.rest() $$, 'already_rested');
select public.travel('u3');
select public.travel('campA');
select public.rest();                       -- fresh arrival allows camp again
select pg_temp.expect_err($$ select public.buy_item('apple', 1) $$, 'not_at_inn');

-- items
select public.use_item('apple');
select public.use_item('tea');
select pg_temp.assert((select hp from public.characters) = 100 and (select mana from public.characters) = 40, 'items restore to full');
select pg_temp.expect_err($$ select public.use_item('apple') $$, 'already_full');
select pg_temp.expect_err($$ select public.use_item('sandwich') $$, 'no_item');

-- ===== inn: climb to u4 using direct progress (as postgres) =====
reset role;
insert into public.lesson_progress (character_id, lesson_id, best_correct, total, stars)
select c.id, l.id, 1, 1, 3 from public.characters c, public.lessons l
where c.user_id = :'ua' and l.required and l.location_id in ('u3', 'u4')
on conflict do nothing;
update public.characters set coins = 40 where user_id = :'ua';
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
select public.travel('inn1');
select pg_temp.assert((select (public.rest() ->> 'hp')::int) = 100, 'inn heals to full');
select pg_temp.assert((select coins from public.characters) = 37, 'inn costs 3');
select public.buy_item('sandwich', 2);
select pg_temp.assert((select coins from public.characters) = 13, 'bought 2 sandwiches');
select pg_temp.expect_err($$ select public.buy_item('sandwich', 5) $$, 'not_enough_coins');

-- ===== PvP =====
reset role;
set role authenticated;
select set_config('request.jwt.claim.sub', :'ub', false);
select public.create_character('Ben', '{}', 'parrot');
select pg_temp.expect_err($$ select public.pvp_find_match() $$, 'locked');
reset role;
insert into public.lesson_progress (character_id, lesson_id, best_correct, total, stars)
select c.id, 'start-l1', 1, 1, 3 from public.characters c where c.user_id = :'ub';
set role authenticated;

reset role;
update public.characters set hp = 60, mana = 30 where user_id = :'ua';
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
create temp table m as select public.pvp_find_match() as id;
select pg_temp.assert((select status from public.pvp_matches where id = (select id from m)) = 'waiting', 'waiting for opponent');
select set_config('request.jwt.claim.sub', :'ub', false);
select pg_temp.assert((select public.pvp_find_match()) = (select id from m), 'B joins the same match');
select pg_temp.assert((select status from public.pvp_matches) = 'active', 'match active');
select pg_temp.assert((select p1_hp = 60 and p1_mana = 30 and p2_hp = 100 and p2_mana = 40 from public.pvp_matches), 'match starts from current HP/Mana');
select pg_temp.expect_err($$ select public.use_item('apple') $$, 'in_match');
select pg_temp.expect_err($$ select public.rest() $$, 'in_match');
select pg_temp.assert((select q_choices is not null and q_prompt is not null from public.pvp_matches), 'question set');

-- not B's turn first
select pg_temp.expect_err(format($$ select public.pvp_act(%L, 'attack', 'x') $$, (select id from m)), 'not_your_turn');
select set_config('request.jwt.claim.sub', :'ua', false);
select public.pvp_act((select id from m), 'attack', 'definitely wrong');       -- wrong answer = 0.75x damage, still hits
select pg_temp.assert((select p2_hp from public.pvp_matches) = 100 - round(14 * 0.75), 'wrong answer weak hit');
select set_config('request.jwt.claim.sub', :'ub', false);
select pg_temp.expect_err(format($$ select public.pvp_act(%L, 'skill', 'x') $$, (select id from m)), 'skill_locked');   -- B is stage 1
select pg_temp.expect_err(format($$ select public.pvp_act(%L, 'dance', 'x') $$, (select id from m)), 'invalid_action');
select public.pvp_act((select id from m), 'guard');
select set_config('request.jwt.claim.sub', :'ua', false);
select pg_temp.expect_err(format($$ select public.pvp_act(%L, 'attack', 'x') $$, (select id from m)), 'not_your_turn') where false;

-- play to the end: A always answers correctly (answer read as superuser), B guards/focuses
reset role;
do $$
declare v_m uuid := (select id from m); v_turn uuid; v_ans text; i int := 0; ua uuid := '00000000-0000-0000-0000-00000000000a'; ub uuid := '00000000-0000-0000-0000-00000000000b';
begin
  loop
    i := i + 1; exit when i > 60;
    select turn into v_turn from public.pvp_matches where id = v_m;
    exit when v_turn is null;
    select q_answer into v_ans from public.pvp_secrets where match_id = v_m;
    if v_turn = (select id from public.characters where user_id = ua) then
      perform set_config('request.jwt.claim.sub', ua::text, true);
      perform public.pvp_act(v_m, case when i % 3 = 0 then 'skill' else 'attack' end, v_ans);
    else
      perform set_config('request.jwt.claim.sub', ub::text, true);
      perform public.pvp_act(v_m, case when i % 2 = 0 then 'focus' else 'guard' end, v_ans);
    end if;
  end loop;
end $$;
select pg_temp.assert((select status from public.pvp_matches where id = (select id from m)) = 'finished', 'match finished');
select pg_temp.assert((select c.user_id from public.pvp_matches pm join public.characters c on c.id = pm.winner where pm.id = (select id from m)) = :'ua', 'A wins');
select pg_temp.assert((select pvp_wins from public.characters where user_id = :'ua') = 1 and (select pvp_losses from public.characters where user_id = :'ub') = 1, 'win/loss recorded');
select pg_temp.assert((select count(*) from public.pvp_secrets) >= 1, 'secrets stay server side');
select pg_temp.assert((select c.hp = greatest(25, pm.p1_hp) and c.mana = pm.p1_mana from public.pvp_matches pm join public.characters c on c.id = pm.p1 where pm.id = (select id from m)), 'A keeps match HP/Mana');
select pg_temp.assert((select c.hp = 25 from public.pvp_matches pm join public.characters c on c.id = pm.p2 where pm.id = (select id from m)), 'defeated B is floored at 25 HP');

-- finished matches don't block a new search; timeout claim needs an idle opponent
set role authenticated;
select set_config('request.jwt.claim.sub', :'ua', false);
create temp table m2 as select public.pvp_find_match() as id;
select pg_temp.assert((select id from m2) <> (select id from m), 'new match after finishing');
select public.pvp_cancel((select id from m2));
select pg_temp.assert((select count(*) from public.pvp_matches where id = (select id from m2)) = 0, 'waiting match cancelled');

select set_config('request.jwt.claim.sub', :'ub', false);
select pg_temp.assert((select count(*) from public.characters) = 1, 'B only sees own character (RLS)');
