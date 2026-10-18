# RISE English Adventure

เกมผจญภัยเรียนภาษาอังกฤษจากหนังสือ **Aksorn RISE English ป.1** — สร้างตัวละคร เลือกสัตว์เลี้ยง 1 ตัว สำรวจแผนที่โลกเดียว เข้าสถานที่เพื่อเรียนแต่ละบท พักฟื้น HP/Mana ที่แคมป์และโรงเตี๊ยม และดวล PvP 1v1 แบบผลัดกันเล่น (ไม่มีระบบธาตุ)

Stack: Vite + React + TypeScript · Supabase (Postgres, Auth, RLS, RPC, Realtime)

## เริ่มใช้งาน

```bash
npm install
cp .env.example .env        # ใส่ URL และ anon key ของโปรเจกต์ Supabase
```

### ตั้งค่า Supabase

โปรเจกต์บนคลาวด์:
```bash
npx supabase link --project-ref <ref>
npx supabase db push                       # รัน supabase/migrations/*
# แล้วรัน supabase/seed.sql ใน SQL Editor (หรือ psql) เพื่อใส่เนื้อหาเกม
```
- Dashboard → Authentication → Providers → เปิด **Anonymous sign-ins**
- ตาราง `pvp_matches` ถูกเพิ่มเข้า realtime โดย migration; ถ้า realtime ใช้ไม่ได้ เกมจะ poll ทุก 3 วินาทีแทน

ใช้ local: `npx supabase start && npx supabase db reset` (config.toml เปิด anonymous sign-in และ seed ให้แล้ว)

```bash
npm run dev          # http://localhost:5173
npm run build
```

## โครงสร้าง

| ส่วน | ที่อยู่ |
|---|---|
| เนื้อหาจากหนังสือ (ถอดจากภาพสารบัญ) | `content/units.json` |
| แผนที่ สถานที่ ไอเทม สัตว์เลี้ยง | `content/world.json` |
| สร้าง `supabase/seed.sql` จาก content | `npm run seed:build` |
| Schema + RLS | `supabase/migrations/0001_schema.sql` |
| กติกาเกม (RPC ฝั่งเซิร์ฟเวอร์) | `supabase/migrations/0002_functions.sql` |
| ทดสอบฐานข้อมูลบน Postgres ชั่วคราว | `npm run db:test` |

## กติกาที่ล็อกไว้ในฐานข้อมูล

- ต้องสร้างตัวละครก่อนเล่น (`create_character`) — 1 บัญชี 1 ตัวละคร
- สัตว์เลี้ยง 1 ตัวต่อตัวละคร (primary key ของ `pets` = `character_id`) และ client เขียน/เปลี่ยนไม่ได้
- ไม่มีระบบธาตุ (ไม่มีคอลัมน์หรือตารางเกี่ยวกับธาตุ)
- Client **อ่านอย่างเดียว** ทุกการเขียน (เหรียญ, HP, ความคืบหน้า, PvP) ผ่าน RPC ที่ตรวจเงื่อนไขเอง
- PvP 1v1: ทุกคนเริ่ม HP 100 / Mana 40 เท่ากัน, เฉลยคำถามเก็บใน `pvp_secrets` (client อ่านไม่ได้)
- จุดพัก: แคมป์ (+40 HP, +15 Mana, 1 ครั้งต่อการมาถึง) · โรงเตี๊ยม (เต็ม, 3 เหรียญ, ฟรีถ้าเหรียญไม่พอ, ซื้อไอเทมได้)
- ตอบผิดเสีย HP ครั้งละ 5 แต่ไม่ต่ำกว่า 1 · คำใบ้ใช้ Mana 3

## ข้อควรรู้ / สิ่งที่ยังไม่ครบ

- **ภาพสารบัญมี Starter + Unit 1–6** (ไม่ใช่ Unit 1–8 ตามเอกสารเดิม) จึงทำตามภาพ ถ้ามี Unit 7–8 ให้เพิ่มใน `content/*.json` แล้ว `npm run seed:build`
- **Festivals (หน้า 92–95), English sounds (96–100), Extra activities / Language focus (101–112)** สารบัญบอกแค่ชื่อและเลขหน้า จึงเป็นสถานที่ "รอเนื้อหา" ไม่สร้างกิจกรรมขึ้นเอง
- Alphabet Review ไม่ปรากฏในภาพสารบัญ จึงยังไม่ได้ใส่
- กิจกรรมสร้างจากคำศัพท์/ประโยคที่พิมพ์ในสารบัญเท่านั้น (ฟังแล้วเลือก, สะกดคำ, เรียงประโยค, ถาม-ตอบ) ต้องตรวจกับหน้าหนังสือจริงก่อนสอนจริง
- เสียงใช้ Web Speech API ของเบราว์เซอร์ (ยังไม่มีไฟล์เสียงจากหนังสือ)
- คะแนนบทเรียนมาจาก client (ตรวจเฉพาะขอบเขต) และเฉลยอยู่ใน payload ของ `activities` — เหมาะกับเกมในห้องเรียน ไม่ใช่การสอบ
- ตัวเลขสมดุล (ดาเมจ, ค่าฟื้นฟู, เกณฑ์เติบโตสัตว์เลี้ยงที่ 6/18 บท) เป็นค่าตั้งต้นที่ต้องทดสอบกับผู้เรียน
