-- Closer duels: the opponent is picked among the three players whose star total is nearest to yours (random
-- among those), not from everybody. Stars give the stats, so similar stars mean similar fighters.

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

  -- one of the three players whose star total is closest to yours (so duels are close), picked at random;
  -- the pet is taken as it is now: stats from its stars, full HP and Mana
  select c.* into v_o from characters c where c.id in (
    select x.id from (
      select ch.id, abs(coalesce((select sum(lp.stars) from lesson_progress lp where lp.character_id = ch.id), 0) - (v_stats ->> 'stars')::int) as gap, random() as tie
      from characters ch join pets pe on pe.character_id = ch.id where ch.id <> v_char.id
    ) x order by x.gap, x.tie limit 3
  ) order by random() limit 1;
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
