-- Supabase Postgres. Run once in the SQL editor (or by the build). Phase 0 needs only kv and claims.
CREATE TABLE IF NOT EXISTS kv (
  kind text NOT NULL,
  key text NOT NULL,
  value jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (kind, key)
);
CREATE TABLE IF NOT EXISTS claims (name text PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now());
-- The app connects as the database owner over DATABASE_URL; no browser ever talks to Supabase directly,
-- so row level security is switched on with no policies to block the public API keys.
ALTER TABLE kv ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
