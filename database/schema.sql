
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

-- TRIP INVITES (pending acceptance; on accept, add to trip_collaborators)
CREATE TABLE IF NOT EXISTS trip_invites (
  id BIGSERIAL PRIMARY KEY,
  trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  inviter_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  invitee_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(trip_id, invitee_id)
);

-- OPTIONAL: Assign gear to trips (for “who brings what”)
CREATE TABLE IF NOT EXISTS trip_gear (
  trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  gear_id BIGINT NOT NULL REFERENCES gear(id) ON DELETE CASCADE,
  assigned_to_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  quantity INT NOT NULL DEFAULT 1,
  PRIMARY KEY (trip_id, gear_id)
);

-- FRIEND REQUESTS (sender_id requests receiver_id; status: pending → accepted or declined)
CREATE TABLE IF NOT EXISTS friend_requests (
  id BIGSERIAL PRIMARY KEY,
  sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(sender_id, receiver_id)
);

-- TRIP REPORT INFO (summarized trail/report data per trip; summarized_description instead of full description)
CREATE TABLE IF NOT EXISTS trip_report_info (
  id BIGSERIAL PRIMARY KEY,
  trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  summarized_description TEXT NOT NULL,
  hike_name TEXT,
  source_url TEXT,
  distance TEXT,
  elevation_gain TEXT,
  highpoint TEXT,
  difficulty TEXT,
  trip_report_1 TEXT,
  trip_report_2 TEXT,
  lat/long TEXT
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_gear_user_id ON gear(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_creator_id ON trips(creator_id);
CREATE INDEX IF NOT EXISTS idx_trip_collab_user_id ON trip_collaborators(user_id);
CREATE INDEX IF NOT EXISTS idx_friend_requests_receiver_id ON friend_requests(receiver_id);
CREATE INDEX IF NOT EXISTS idx_friend_requests_sender_id ON friend_requests(sender_id);
CREATE INDEX IF NOT EXISTS idx_trip_invites_trip_id ON trip_invites(trip_id);
CREATE INDEX IF NOT EXISTS idx_trip_invites_invitee_id ON trip_invites(invitee_id);
CREATE INDEX IF NOT EXISTS idx_trip_report_info_trip_id ON trip_report_info(trip_id);
