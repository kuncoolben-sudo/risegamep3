-- Hospitals replace the inn: treatment is free (no 3-coin fee, no once-per-visit limit) and they keep the
-- shop for healing items (coins are still useful there). Camps are unchanged. The old 'inn' rest type still
-- works as a free hospital, so nothing breaks for a database that has not re-seeded yet.

create or replace function public.rest() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_char characters%rowtype;
  v_loc locations%rowtype;
begin
  select * into v_char from characters where user_id = auth.uid() for update;
  if not found then raise exception 'no_character'; end if;
  if _in_active_match(v_char.id) then raise exception 'in_match'; end if;
  select * into v_loc from locations where id = v_char.location_id;
  if v_loc.kind <> 'rest' then raise exception 'not_a_rest_stop'; end if;

  if v_loc.rest_type in ('inn', 'hospital') then
    update pets set hp = max_hp, mana = max_mana where character_id = v_char.id;
  else
    if v_char.rested_here then raise exception 'already_rested'; end if;
    update pets set hp = least(max_hp, hp + 40), mana = least(max_mana, mana + 15) where character_id = v_char.id;
    update characters set rested_here = true where id = v_char.id;
  end if;
  return (select jsonb_build_object('hp', p.hp, 'mana', p.mana, 'coins', c.coins, 'cost', 0)
          from pets p join characters c on c.id = p.character_id where c.id = v_char.id);
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
  if not exists (select 1 from locations where id = v_char.location_id and rest_type in ('inn', 'hospital')) then
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
