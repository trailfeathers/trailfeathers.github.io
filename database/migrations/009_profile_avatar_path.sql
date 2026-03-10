-- Optional avatar chosen from static directory (e.g. profile_ducks).
-- When set, client uses static URL; when cleared and avatar BYTEA is set, client uses /api/.../avatar.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_profiles' AND column_name = 'avatar_path') THEN
    ALTER TABLE user_profiles ADD COLUMN avatar_path TEXT;
  END IF;
END $$;
