-- Migration: store images in Postgres (BYTEA) for profile avatars and trip report photos.
-- Run after 005_profiles_and_user_trip_reports.sql.
-- PostgreSQL BYTEA supports binary data up to ~1GB per value; suitable for avatars and moderate-sized photos.

-- Profile avatar (optional): small image (e.g. JPEG/PNG) for user profile.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_profiles' AND column_name = 'avatar') THEN
    ALTER TABLE user_profiles ADD COLUMN avatar BYTEA;
  END IF;
END $$;

-- Optional: MIME type for avatar so the app can serve correct Content-Type.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_profiles' AND column_name = 'avatar_media_type') THEN
    ALTER TABLE user_profiles ADD COLUMN avatar_media_type TEXT;
  END IF;
END $$;

-- Trip report image (optional): one photo per report (e.g. hero image).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_trip_reports' AND column_name = 'image') THEN
    ALTER TABLE user_trip_reports ADD COLUMN image BYTEA;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_trip_reports' AND column_name = 'image_media_type') THEN
    ALTER TABLE user_trip_reports ADD COLUMN image_media_type TEXT;
  END IF;
END $$;
