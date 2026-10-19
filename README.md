# RISE English Adventure

เกมผจญภัยเรียนภาษาอังกฤษจากหนังสือ **Aksorn RISE English ป.3** — สร้างตัวละคร เลือกสัตว์เลี้ยง 1 ตัว สำรวจแผนที่โลกเดียว เข้าสถานที่เพื่อเรียนแต่ละบท พักฟื้น HP/Mana ที่แคมป์และโรงเตี๊ยม และดวล PvP 1v1 แบบผลัดกันเล่น (ไม่มีระบบธาตุ)

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

## เผยแพร่บน GitHub Pages

1. Settings → Pages → **Source: GitHub Actions** (ถ้าเลือก "Deploy from a branch" จะขึ้นหน้าว่าง เพราะเสิร์ฟไฟล์ต้นฉบับที่ยังไม่ได้ build)
2. Settings → Secrets and variables → Actions → เพิ่ม `VITE_SUPABASE_URL` และ `VITE_SUPABASE_ANON_KEY`
3. Merge เข้า `main` (หรือรัน workflow "Deploy to GitHub Pages" ด้วยมือ) — workflow อยู่ที่ `.github/workflows/deploy.yml` และตั้ง base path เป็น `/<ชื่อ repo>/` ให้เอง

## โลก 3D

หน้าเริ่มต้นคือโลก 3D (Three.js + React Three Fiber) เดินด้วย WASD / ลูกศร / คลิกพื้น / จอยสติ๊กบนมือถือ เดินเข้าใกล้สถานที่แล้วกด E หรือปุ่ม "เข้า" เพื่อเปิดบทเรียน พักฟื้น หรือเข้าลานประลอง (ใช้ RPC เดิมทั้งหมด) แผนที่ 2D ยังอยู่ในแท็บ "แผนที่ 2D" และมี "โหมดประหยัด" สำหรับเครื่องช้า

โมเดลทั้งหมดใน `public/models/*.glb` (ตัวละคร chibi, สัตว์เลี้ยง 4 ตัว, อาคาร 14 หลัง, ต้นไม้/หิน/ดอกไม้ รวม ~760KB) สร้างจากสคริปต์ Blender แบบไม่มีหน้าจอ:

```bash
pip install bpy                # Blender เป็นโมดูล Python (ต้อง Python 3.11–3.13)
npm run models:build           # รัน tools/blender/build_models.py
```
ชื่อโหนด/วัสดุในโมเดล (`ArmL`, `Hair_wavy`, วัสดุ `Skin`/`Hair`/`Outfit`) เป็นสัญญากับ `src/world3d/Character3D.tsx` ถ้าเปลี่ยนโมเดลเป็นงานจากนักวาด ให้คงชื่อเหล่านี้ไว้ ระบบปรับแต่งตัวละครจะทำงานต่อได้

## กติกาที่ล็อกไว้ในฐานข้อมูล

- ต้องสร้างตัวละครก่อนเล่น (`create_character`) — 1 บัญชี 1 ตัวละคร
- สัตว์เลี้ยง 1 ตัวต่อตัวละคร (primary key ของ `pets` = `character_id`) และ client เขียน/เปลี่ยนไม่ได้
- ไม่มีระบบธาตุ (ไม่มีคอลัมน์หรือตารางเกี่ยวกับธาตุ)
- Client **อ่านอย่างเดียว** ทุกการเขียน (เหรียญ, HP, ความคืบหน้า, PvP) ผ่าน RPC ที่ตรวจเงื่อนไขเอง
- PvP 1v1: ทุกคนเริ่ม HP 100 / Mana 40 เท่ากัน, เฉลยคำถามเก็บใน `pvp_secrets` (client อ่านไม่ได้)
- จุดพัก: แคมป์ (+40 HP, +15 Mana, 1 ครั้งต่อการมาถึง) · โรงเตี๊ยม (เต็ม, 3 เหรียญ, ฟรีถ้าเหรียญไม่พอ, ซื้อไอเทมได้)
- ตอบผิดเสีย HP ครั้งละ 5 แต่ไม่ต่ำกว่า 1 · คำใบ้ใช้ Mana 3

## ข้อควรรู้ / สิ่งที่ยังไม่ครบ

- เนื้อหาปัจจุบันถอดจากภาพสารบัญของหนังสือ **ป.3: Starter + Unit 1–8** (ถ้าเปลี่ยนระดับชั้นอีก แก้ `content/*.json` แล้ว `npm run seed:build`)
- **Festivals (หน้า 120–123) และ English sounds (124–128)** สารบัญบอกแค่ชื่อและเลขหน้า จึงเป็นสถานที่ "รอเนื้อหา" ไม่สร้างกิจกรรมขึ้นเอง
- Alphabet Review ไม่ปรากฏในภาพสารบัญ จึงยังไม่ได้ใส่
- กิจกรรมสร้างจากคำศัพท์/ประโยคที่พิมพ์ในสารบัญเท่านั้น (ฟังแล้วเลือก, สะกดคำ, เรียงประโยค, ถาม-ตอบ) ต้องตรวจกับหน้าหนังสือจริงก่อนสอนจริง
- เสียงใช้ Web Speech API ของเบราว์เซอร์ (ยังไม่มีไฟล์เสียงจากหนังสือ)
- คะแนนบทเรียนมาจาก client (ตรวจเฉพาะขอบเขต) และเฉลยอยู่ใน payload ของ `activities` — เหมาะกับเกมในห้องเรียน ไม่ใช่การสอบ
- ตัวเลขสมดุล (ดาเมจ, ค่าฟื้นฟู, เกณฑ์เติบโตสัตว์เลี้ยงที่ 6/18 บท) เป็นค่าตั้งต้นที่ต้องทดสอบกับผู้เรียน
