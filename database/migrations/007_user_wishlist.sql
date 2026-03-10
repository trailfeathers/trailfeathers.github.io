-- Migration: user wishlist ("Hikes I want to try").
-- Run after 005_profiles_and_user_trip_reports.sql (trip_report_info exists).

CREATE TABLE IF NOT EXISTS user_wishlist (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  trip_report_info_id BIGINT NOT NULL REFERENCES trip_report_info(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, trip_report_info_id)
);

CREATE INDEX IF NOT EXISTS idx_user_wishlist_user_id ON user_wishlist(user_id);
