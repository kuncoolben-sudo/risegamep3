#!/usr/bin/env bash
# Runs the migrations + seed + tests/db.test.sql against a throw-away local Postgres.
# Needs the postgres 16 binaries (apt: postgresql-16). No Supabase stack required.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$(ls -d /usr/lib/postgresql/*/bin | tail -1)"
TMP="$(mktemp -d)"
PORT=54399
if [ "$(id -u)" = 0 ]; then
  chown postgres "$TMP"
  RUN=(runuser -u postgres --)
else
  RUN=()
fi
cleanup() { "${RUN[@]}" "$BIN/pg_ctl" -D "$TMP/data" -m immediate stop >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT
"${RUN[@]}" "$BIN/initdb" -D "$TMP/data" -A trust >/dev/null
"${RUN[@]}" "$BIN/pg_ctl" -D "$TMP/data" -o "-p $PORT -k $TMP -c listen_addresses=''" -l "$TMP/log" -w start >/dev/null
PSQL=("${RUN[@]}" psql -h "$TMP" -p "$PORT" -U postgres -v ON_ERROR_STOP=1 -q -X)
"${PSQL[@]}" -d postgres -c "create database game" >/dev/null
# minimal stand-ins for what Supabase provides
"${PSQL[@]}" -d game <<'SQL'
create role anon nologin; create role authenticated nologin;
create schema auth;
create table auth.users (id uuid primary key default gen_random_uuid());
create function auth.uid() returns uuid language sql stable as
  $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated;
grant execute on function auth.uid() to anon, authenticated;
grant usage on schema public to anon, authenticated;
create publication supabase_realtime;
SQL
for f in "$ROOT"/supabase/migrations/*.sql "$ROOT"/supabase/seed.sql "$ROOT"/tests/db.test.sql; do
  echo "== $(basename "$f")"
  if [[ "$f" == *.test.sql ]]; then "${PSQL[@]}" -d game -o /dev/null -f "$f"; else "${PSQL[@]}" -d game -f "$f"; fi
done
echo "ALL DB TESTS PASSED"
