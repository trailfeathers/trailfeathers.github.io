-- TrailFeathers - Migration 006: BYTEA columns for profile avatar and trip report images.
-- Group: TrailFeathers
-- Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
-- Last updated: 3/13/26

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
