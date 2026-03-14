-- TrailFeathers - Migration 005: user_profiles, user_top_four_hikes, user_trip_reports tables.
-- Group: TrailFeathers
-- Authors: Kim, Smith, Domst, and Snider
-- Last updated: 3/13/26

-- User profiles (1:1 with users): display_name, bio
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id BIGINT NOT NULL PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  display_name TEXT,
  bio TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Top four hikes per user (Letterboxd-style): position 1–4
CREATE TABLE IF NOT EXISTS user_top_four_hikes (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  position INT NOT NULL CHECK (position >= 1 AND position <= 4),
  trip_report_info_id BIGINT NOT NULL REFERENCES trip_report_info(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, position)
);

CREATE INDEX IF NOT EXISTS idx_user_top_four_hikes_user_id ON user_top_four_hikes(user_id);

-- User-authored trip reports (detached from trips; no trip_id for now)
CREATE TABLE IF NOT EXISTS user_trip_reports (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  trip_report_info_id BIGINT NOT NULL REFERENCES trip_report_info(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  body TEXT NOT NULL DEFAULT '',
  date_hiked DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_trip_reports_user_id ON user_trip_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_user_trip_reports_trip_report_info_id ON user_trip_reports(trip_report_info_id);
