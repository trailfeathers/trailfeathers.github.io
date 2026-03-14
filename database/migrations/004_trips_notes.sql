-- TrailFeathers - Migration 004: add notes column to trips.
-- Group: TrailFeathers
-- Authors: Kim, Smith, Domst, and Snider
-- Last updated: 3/13/26

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'trips' AND column_name = 'notes') THEN
    ALTER TABLE trips ADD COLUMN notes TEXT DEFAULT '';
  END IF;
END $$;
