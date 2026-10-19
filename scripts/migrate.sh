#!/usr/bin/env bash
# Applies supabase/migrations/*.sql (in order, once each) and then the idempotent supabase/seed.sql.
#   SUPABASE_DB_URL='postgresql://postgres.<ref>:<password>@<pooler-host>:5432/postgres' bash scripts/migrate.sh
# Applied migrations are recorded in public._migrations. A database that was set up by hand
# (migrations pasted into the SQL editor before this runner existed) is detected and baselined,
# so already-applied files are marked instead of re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -z "${SUPABASE_DB_URL:-}" ]; then
  echo "SUPABASE_DB_URL is not set - skipping database migration."
  exit 0
fi
q() { psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -X -q -t -A "$@"; }

q -c "create table if not exists public._migrations (name text primary key, applied_at timestamptz not null default now());
      alter table public._migrations enable row level security;
      revoke all on public._migrations from anon, authenticated;" >/dev/null 2>&1 || q -c "create table if not exists public._migrations (name text primary key, applied_at timestamptz not null default now());"

# one-time baseline for databases created by pasting the SQL by hand
if [ "$(q -c 'select count(*) from public._migrations')" = "0" ]; then
  declare -A CHECK=(
    [0001_schema.sql]="select to_regclass('public.locations') is not null"
    [0002_functions.sql]="select to_regprocedure('public.create_character(text,jsonb,text)') is not null"
    [0003_hp_mana_pvp_only.sql]="select to_regprocedure('public._in_active_match(uuid)') is not null"
    [0004_pet_hp_mana.sql]="select exists (select 1 from information_schema.columns where table_schema='public' and table_name='pets' and column_name='hp')"
  )
  for name in 0001_schema.sql 0002_functions.sql 0003_hp_mana_pvp_only.sql 0004_pet_hp_mana.sql; do
    [ "$(q -c "${CHECK[$name]}")" = "t" ] || break      # stop at the first one that is not there yet
    q -c "insert into public._migrations (name) values ('$name') on conflict do nothing"
    echo "baseline: $name already applied"
  done
fi

for f in "$ROOT"/supabase/migrations/*.sql; do
  name="$(basename "$f")"
  if [ "$(q -c "select count(*) from public._migrations where name = '$name'")" != "0" ]; then
    echo "skip   $name"
    continue
  fi
  echo "apply  $name"
  psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -X -q -1 -f "$f"
  q -c "insert into public._migrations (name) values ('$name')"
done

echo "seed   supabase/seed.sql"
psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -X -q -f "$ROOT/supabase/seed.sql"
echo "database is up to date"
