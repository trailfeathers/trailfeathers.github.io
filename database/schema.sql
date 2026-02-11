
-- USERS (username for login, per project description)
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GEAR (belongs to one user)
CREATE TABLE IF NOT EXISTS gear (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  capacity TEXT,
  weight_oz NUMERIC,
  brand TEXT,
  condition TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TRIPS (created by one user)
CREATE TABLE IF NOT EXISTS trips (
  id BIGSERIAL PRIMARY KEY,
  creator_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  trip_name TEXT NOT NULL,
  trail_name TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  intended_start_date TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TRIP COLLABORATORS (many-to-many)
CREATE TABLE IF NOT EXISTS trip_collaborators (
  trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member',
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (trip_id, user_id)
);

-- OPTIONAL: Assign gear to trips (for “who brings what”)
CREATE TABLE IF NOT EXISTS trip_gear (
  trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  gear_id BIGINT NOT NULL REFERENCES gear(id) ON DELETE CASCADE,
  assigned_to_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  quantity INT NOT NULL DEFAULT 1,
  PRIMARY KEY (trip_id, gear_id)
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_gear_user_id ON gear(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_creator_id ON trips(creator_id);
CREATE INDEX IF NOT EXISTS idx_trip_collab_user_id ON trip_collaborators(user_id);
