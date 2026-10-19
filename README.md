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

## อัปเดตฐานข้อมูลอัตโนมัติ (Supabase)

workflow **Migrate database (Supabase)** รัน `supabase/migrations/*` (ไฟล์ละครั้ง) และ `supabase/seed.sql` ให้เองทุกครั้งที่ merge เข้า `main` แล้วมีไฟล์ใน `supabase/` เปลี่ยน ไม่ต้องวาง SQL เองอีก

ตั้งค่าครั้งเดียว:
1. Supabase Dashboard → ปุ่ม **Connect** → แท็บ **Session pooler** → คัดลอก connection string (หน้าตา `postgresql://postgres.<ref>:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`) แล้วแทน `[YOUR-PASSWORD]` ด้วยรหัสผ่านฐานข้อมูล (ลืมรหัส: Project Settings → Database → Reset database password) — ต้องใช้ Session pooler ไม่ใช่ Direct เพราะ GitHub Actions เชื่อมต่อ IPv6 ไม่ได้
2. GitHub repo → Settings → Secrets and variables → Actions → เพิ่ม secret `SUPABASE_DB_URL` เป็น string ข้างบน
3. แท็บ Actions → **Migrate database (Supabase)** → Run workflow หนึ่งครั้ง (ฐานข้อมูลที่เคยวาง SQL เองจะถูกตรวจจับว่าไฟล์ไหนรันไปแล้ว ไม่รันซ้ำ)

ถ้าไม่ตั้ง secret workflow จะข้ามไปเฉยๆ ทดสอบตัวรัน: `npm run db:test:migrate`

## เสียงอังกฤษจาก Azure (เด็ก UK, พูดช้า)

เกมเล่นไฟล์ `public/audio/*.mp3` ก่อน (เสียงเหมือนกันทุกเครื่อง) ถ้าไม่มีไฟล์จะใช้เสียงในเครื่องแทน ไฟล์สร้างจาก Azure Speech (เสียง `en-GB-MaisieNeural`, ความเร็ว −25%) สำหรับข้อความทั้งหมดใน `content/units.json` (~240 ข้อความ ~3,500 ตัวอักษร อยู่ในโควต้าฟรีรายเดือนของ Azure)

ขอ key (ฟรี):
1. portal.azure.com → สร้างทรัพยากร **Speech** (Azure AI Speech), pricing tier **Free F0**, เลือก region เช่น `southeastasia`
2. เปิดทรัพยากร → Keys and Endpoint → คัดลอก **KEY 1** และชื่อ **Location/Region**
3. GitHub repo → Settings → Secrets and variables → Actions → เพิ่ม `AZURE_SPEECH_KEY` และ `AZURE_SPEECH_REGION`
4. แท็บ Actions → **Build audio (Azure TTS)** → Run workflow (สร้างไฟล์ commit เข้า main และ deploy ให้อัตโนมัติ)

บนเครื่องตัวเอง: `AZURE_SPEECH_KEY=… AZURE_SPEECH_REGION=… npm run audio:build` · ดูรายการข้อความ `npm run audio:build -- --dry` · ดูรายชื่อเสียง en-GB ที่ใช้ได้ `npm run audio:build -- --voices` (ตั้ง `AZURE_VOICE`, `AZURE_RATE`, `AZURE_PITCH` เพื่อเปลี่ยนเสียง/ความเร็ว) ถ้าแก้เนื้อหา ให้รันใหม่ ระบบสร้างเฉพาะข้อความที่เพิ่ม/เปลี่ยน

## โลก 3D

หน้าเริ่มต้นคือโลก 3D (Three.js + React Three Fiber) เดินด้วยจอยสติ๊กลอย (แตะค้างตรงไหนก็ได้บนจอแล้วลาก ปล่อยแล้วหยุด) หรือ WASD / ลูกศรบนคอม เดินเข้าใกล้สถานที่แล้วกด E หรือปุ่ม "เข้า" เพื่อเปิดบทเรียน พักฟื้น หรือเข้าลานประลอง (ใช้ RPC เดิมทั้งหมด) แผนที่ 2D ยังอยู่ในแท็บ "แผนที่ 2D" และมี "โหมดประหยัด" สำหรับเครื่องช้า

โมเดลทั้งหมดใน `public/models/*.glb` (ตัวละคร chibi, สัตว์เลี้ยง 4 ตัว, อาคาร 14 หลัง, ต้นไม้/หิน/ดอกไม้ รวม ~760KB) สร้างจากสคริปต์ Blender แบบไม่มีหน้าจอ:

```bash
pip install bpy                # Blender เป็นโมดูล Python (ต้อง Python 3.11–3.13)
npm run models:build           # รัน tools/blender/build_models.py
```
ชื่อโหนด/วัสดุในโมเดล (`ArmL`, `Hair_wavy`, วัสดุ `Skin`/`Hair`/`Outfit`) เป็นสัญญากับ `src/world3d/Character3D.tsx` ถ้าเปลี่ยนโมเดลเป็นงานจากนักวาด ให้คงชื่อเหล่านี้ไว้ ระบบปรับแต่งตัวละครจะทำงานต่อได้

## สัตว์เลี้ยง 6 ตัว 3 ร่าง พร้อมท่าปล่อยพลัง

Skyra (วายุเทพอินทรี) · Blazion (มังกรเพลิง) · Kirin (คีริน) · Lunara (นางฟ้าจันทรา) · Aquaria (นางเงือกมังกร) · Kitsune (คิทสึเนะ) ตามภาพ concept ร่างที่ 1/2/3 ตรงกับระดับสัตว์เลี้ยงเดิม (เติบโตเมื่อผ่าน 6 และ 18 บทเรียน)

- **โมเดล** `public/models/pet_<id>_<ร่าง>.glb` (18 ไฟล์ รวม ~2 MB โหลดเฉพาะตัวที่ใช้) สร้างจาก `tools/blender/build_pets.py` (`npm run pets:build`; ตัวช่วยร่วมอยู่ใน `tools/blender/pets/kit.py`) แต่ละไฟล์มีคลิป `Idle` (วนลูป) และ `Cast` (ท่าปล่อยพลัง) และโหนดจุดหมุนชื่อ `Head`, `Jaw`, `WingL/WingR`, `Tail`, `LegFL`… ถ้าเปลี่ยนเป็นงานจากนักวาด ให้คงชื่อโหนดและคลิปไว้
- **เอฟเฟกต์พลัง** `src/world3d/fx.ts` (เอนจินอนุภาค/วงแหวน/สายฟ้า…) กับ `src/world3d/fxRecipes.ts` (18 สูตร ตามร่าง) เป็นแค่ภาพ ไม่มีผลต่อกติกาและไม่มีระบบธาตุ
- **ชื่อร่าง ชื่อพลัง และเพศ** อยู่ใน `src/world3d/pets.ts` ส่วนชื่อ/คำบรรยายของสายพันธุ์อยู่ใน `content/world.json` (`pet_species`) แล้ว `npm run seed:build`
- **ดูได้ที่ไหน** หน้าสร้างตัวละคร (เลือกสัตว์เลี้ยง) และหน้าสัตว์เลี้ยง: หมุนดู ดูครบ 3 ร่าง กด "ปล่อยพลัง" ในโลก 3D สัตว์จะโชว์พลังของร่างปัจจุบันเองเมื่อผู้เล่นยืนนิ่งนาน
- **การดวล** กติกาเดิมไม่เปลี่ยน: ทักษะใช้ได้ตั้งแต่ร่าง 2 ส่วนท่าของร่าง 1 เป็นท่าโชว์
- สายพันธุ์เดิม (lion/penguin/monkey/parrot) ยังอยู่ในฐานข้อมูลสำหรับตัวละครที่สร้างไปแล้ว แต่ไม่แสดงในหน้าสร้างตัวละคร

## กติกาที่ล็อกไว้ในฐานข้อมูล

- ต้องสร้างตัวละครก่อนเล่น (`create_character`) — 1 บัญชี 1 ตัวละคร
- สัตว์เลี้ยง 1 ตัวต่อตัวละคร (primary key ของ `pets` = `character_id`) และ client เขียน/เปลี่ยนไม่ได้
- ไม่มีระบบธาตุ (ไม่มีคอลัมน์หรือตารางเกี่ยวกับธาตุ)
- Client **อ่านอย่างเดียว** ทุกการเขียน (เหรียญ, HP, ความคืบหน้า, PvP) ผ่าน RPC ที่ตรวจเงื่อนไขเอง
- PvP 1v1: ค่าสูงสุดเท่ากัน (HP 100 / Mana 40) และสัตว์เลี้ยงของแต่ละคนใช้พลังที่เหลืออยู่, เฉลยคำถามเก็บใน `pvp_secrets` (client อ่านไม่ได้)
- จุดพัก: แคมป์ (+40 HP, +15 Mana, 1 ครั้งต่อการมาถึง) · โรงเตี๊ยม (เต็ม, 3 เหรียญ, ฟรีถ้าเหรียญไม่พอ, ซื้อไอเทมได้)
- HP/Mana เป็นของ **สัตว์เลี้ยง** เท่านั้น (ตัวละครไม่มี) และใช้ใน PvP เท่านั้น: บทเรียนไม่เสียพลัง และคำใบ้ใช้ฟรี · ดวลเริ่มจาก HP/Mana ที่เหลือ ผลการดวลติดตัวไป (แพ้แล้ว HP ไม่ต่ำกว่า 25) · ฟื้นฟูด้วยแคมป์/โรงเตี๊ยม/ไอเทม แต่ใช้ระหว่างดวลไม่ได้

## ข้อควรรู้ / สิ่งที่ยังไม่ครบ

- เนื้อหาปัจจุบันถอดจากภาพสารบัญของหนังสือ **ป.3: Starter + Unit 1–8** (ถ้าเปลี่ยนระดับชั้นอีก แก้ `content/*.json` แล้ว `npm run seed:build`)
- **Festivals (หน้า 120–123) และ English sounds (124–128)** สารบัญบอกแค่ชื่อและเลขหน้า จึงเป็นสถานที่ "รอเนื้อหา" ไม่สร้างกิจกรรมขึ้นเอง
- Alphabet Review ไม่ปรากฏในภาพสารบัญ จึงยังไม่ได้ใส่
- กิจกรรมสร้างจากคำศัพท์/ประโยคที่พิมพ์ในสารบัญเท่านั้น (ฟังแล้วเลือก, สะกดคำ, เรียงประโยค, ถาม-ตอบ) ต้องตรวจกับหน้าหนังสือจริงก่อนสอนจริง
- เสียงใช้ Web Speech API ของเบราว์เซอร์ (ยังไม่มีไฟล์เสียงจากหนังสือ)
- คะแนนบทเรียนมาจาก client (ตรวจเฉพาะขอบเขต) และเฉลยอยู่ใน payload ของ `activities` — เหมาะกับเกมในห้องเรียน ไม่ใช่การสอบ
- ตัวเลขสมดุล (ดาเมจ, ค่าฟื้นฟู, เกณฑ์เติบโตสัตว์เลี้ยงที่ 6/18 บท) เป็นค่าตั้งต้นที่ต้องทดสอบกับผู้เรียน
