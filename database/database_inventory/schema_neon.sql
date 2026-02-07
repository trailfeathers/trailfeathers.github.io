CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  pw_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gear_items (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  type TEXT NOT NULL,
  name TEXT NOT NULL,
  capacity TEXT NOT NULL,

  weight TEXT,
  brand TEXT,
  item_condition TEXT,
  notes TEXT,

  qualities_json JSONB NOT NULL DEFAULT '{}'::jsonb,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gear_items_user_id ON gear_items(user_id);
CREATE INDEX IF NOT EXISTS idx_gear_items_type ON gear_items(type);
