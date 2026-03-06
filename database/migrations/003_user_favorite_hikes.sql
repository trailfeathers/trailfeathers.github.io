-- Migration: user favorite hikes (from location catalog).
-- Links users to trip_report_info for "My favorite hikes" on Social Center.

CREATE TABLE IF NOT EXISTS user_favorite_hikes (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  trip_report_info_id BIGINT NOT NULL REFERENCES trip_report_info(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, trip_report_info_id)
);

CREATE INDEX IF NOT EXISTS idx_user_favorite_hikes_user_id ON user_favorite_hikes(user_id);
