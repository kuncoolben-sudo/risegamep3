import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export const configured = Boolean(url && key);
export const supabase = createClient(url ?? 'http://localhost:54321', key ?? 'missing-key');

const ERRORS: Record<string, string> = {
  locked: 'พื้นที่นี้ยังไม่เปิด ต้องผ่านบทก่อนหน้าก่อน',
  not_here: 'ต้องเดินทางไปที่สถานที่นี้ก่อน',
  not_a_rest_stop: 'ที่นี่ไม่ใช่จุดพัก',
  already_rested: 'พักที่แคมป์นี้ไปแล้ว ลองเดินทางไปที่อื่นแล้วกลับมาใหม่',
  already_full: 'ตอนนี้ยังเต็มอยู่',
  not_enough_coins: 'เหรียญไม่พอ',
  not_at_inn: 'ซื้อของได้ที่โรงเตี๊ยมเท่านั้น',
  not_your_turn: 'ยังไม่ถึงตาของคุณ',
  skill_locked: 'สัตว์เลี้ยงต้องเติบโตถึงระดับ 2 ก่อนจึงใช้ทักษะได้',
  no_mana: 'Mana ไม่พอ',
  character_exists: 'มีตัวละครอยู่แล้ว',
  invalid_name: 'ชื่อต้องยาว 1–20 ตัวอักษร',
};

export function errorText(e: unknown): string {
  const msg = (e as { message?: string })?.message ?? String(e);
  for (const k of Object.keys(ERRORS)) if (msg.includes(k)) return ERRORS[k];
  return msg;
}

export async function rpc<T = unknown>(fn: string, args?: Record<string, unknown>): Promise<T> {
  const { data, error } = await supabase.rpc(fn, args);
  if (error) throw error;
  return data as T;
}
