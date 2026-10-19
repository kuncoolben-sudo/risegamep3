-- Pet Hospital: a rest stop next to the arena (open from the start) that heals the pet to full for 3 coins,
-- free when you are out of coins, like the inn but without the shop.

alter table public.locations drop constraint if exists locations_rest_type_check;
alter table public.locations add constraint locations_rest_type_check check (rest_type in ('inn', 'camp', 'hospital'));

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

  if v_loc.rest_type in ('inn', 'hospital') then
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
