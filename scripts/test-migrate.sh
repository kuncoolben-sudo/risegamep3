#!/usr/bin/env bash
# Tests scripts/migrate.sh on throw-away Postgres clusters: fresh DB, hand-built DB (baseline), re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$(ls -d /usr/lib/postgresql/*/bin | tail -1)"
TMP="$(mktemp -d)"; PORT=54397
if [ "$(id -u)" = 0 ]; then chown postgres "$TMP"; RUN=(runuser -u postgres --); else RUN=(); fi
trap '"${RUN[@]}" "$BIN/pg_ctl" -D "$TMP/data" -m immediate stop >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
"${RUN[@]}" "$BIN/initdb" -D "$TMP/data" -A trust >/dev/null
"${RUN[@]}" "$BIN/pg_ctl" -D "$TMP/data" -o "-p $PORT -k $TMP -c listen_addresses=''" -l "$TMP/log" -w start >/dev/null
P=("${RUN[@]}" psql -h "$TMP" -p "$PORT" -U postgres -v ON_ERROR_STOP=1 -X -q -t -A)
url() { echo "postgresql:///$1?host=$TMP&port=$PORT&user=postgres"; }
stub() { "${P[@]}" -d "$1" >/dev/null 2>&1 <<'SQL' || true
create role anon nologin; create role authenticated nologin;
SQL
true
"${P[@]}" -d "$1" >/dev/null <<'SQL'
create schema auth;
create table auth.users (id uuid primary key default gen_random_uuid());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated; grant usage on schema public to anon, authenticated; create publication supabase_realtime;
SQL
}
ok() { echo "  ok: $1"; }
fail() { echo "  FAIL: $1"; exit 1; }

echo "1) fresh database"
"${P[@]}" -d postgres -c "create database fresh" >/dev/null; stub fresh
SUPABASE_DB_URL="$(url fresh)" bash "$ROOT/scripts/migrate.sh" > "$TMP/out1"
[ "$("${P[@]}" -d fresh -c 'select count(*) from public._migrations')" = "$(ls "$ROOT"/supabase/migrations/*.sql | wc -l)" ] && ok "all migrations recorded" || fail "migrations not recorded"
[ "$("${P[@]}" -d fresh -c 'select count(*) from public.locations')" = "15" ] && ok "seed loaded" || fail "seed missing"
[ "$("${P[@]}" -d fresh -c "select count(*) from information_schema.columns where table_name='pets' and column_name='hp'")" = "1" ] && ok "0004 applied" || fail "0004 missing"

echo "2) re-run changes nothing"
SUPABASE_DB_URL="$(url fresh)" bash "$ROOT/scripts/migrate.sh" > "$TMP/out2"
grep -q "apply" "$TMP/out2" && fail "re-run applied something" || ok "nothing re-applied"

echo "3) database built by hand up to 0003 (migrations pasted in the SQL editor), with a player"
"${P[@]}" -d postgres -c "create database manual" >/dev/null; stub manual
for f in 0001_schema 0002_functions 0003_hp_mana_pvp_only; do "${P[@]}" -d manual -f "$ROOT/supabase/migrations/$f.sql" >/dev/null; done
"${P[@]}" -d manual -f "$ROOT/supabase/seed.sql" >/dev/null
"${P[@]}" -d manual -c "insert into auth.users(id) values ('00000000-0000-0000-0000-00000000000a'); insert into characters(user_id,name,appearance,hp,mana,coins) values ('00000000-0000-0000-0000-00000000000a','Old','{}',37,11,99); insert into pets(character_id,species_id) select id,'lion' from characters;"
SUPABASE_DB_URL="$(url manual)" bash "$ROOT/scripts/migrate.sh" > "$TMP/out3"
grep -q "baseline: 0003" "$TMP/out3" && ok "0001-0003 detected as already applied" || fail "baseline not detected"
grep -q "apply  0004" "$TMP/out3" && ok "only 0004 applied" || fail "0004 not applied"
grep -q "apply  0001\|apply  0002\|apply  0003" "$TMP/out3" && fail "re-ran old migrations" || ok "old migrations not re-run"
[ "$("${P[@]}" -d manual -c "select hp || '/' || mana from pets")" = "37/11" ] && ok "player data preserved on the pet" || fail "player data lost"

echo "4) no secret -> skipped, exit 0"
env -u SUPABASE_DB_URL bash "$ROOT/scripts/migrate.sh" | grep -q skipping && ok "skipped" || fail "did not skip"
echo "MIGRATE RUNNER TESTS PASSED"
