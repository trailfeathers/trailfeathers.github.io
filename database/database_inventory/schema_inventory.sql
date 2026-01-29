PRAGMA foreign_keys = ON;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Gear items
CREATE TABLE IF NOT EXISTS gear_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  capacity TEXT NOT NULL,
  attributes TEXT, -- JSON string
  created_at TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

  -- enum constraint
  CHECK (type IN (
    'SLEEPING_BAG',
    'SLEEPING_PAD',
    'SHELTER',
    'COOK_SET',
    'BACKPACK',
    'CLOTHING',
    'WATER_TREATMENT',
    'NAVIGATION',
    'FIRST_AID',
    "LUXURY",
    'OTHER'
  )),

  -- length constraints
  CHECK (length(name) BETWEEN 1 AND 50),
  CHECK (length(capacity) BETWEEN 1 AND 50)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_gear_items_user_id ON gear_items(user_id);
CREATE INDEX IF NOT EXISTS idx_gear_items_type ON gear_items(type);
