-- TrailFeathers - Migration 009: avatar_path column (preset avatars from static, e.g. profile_ducks).
-- Group: TrailFeathers
-- Authors: Kim, Smith, Domst, and Snider
-- Last updated: 3/13/26

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_profiles' AND column_name = 'avatar_path') THEN
    ALTER TABLE user_profiles ADD COLUMN avatar_path TEXT;
  END IF;
END $$;
