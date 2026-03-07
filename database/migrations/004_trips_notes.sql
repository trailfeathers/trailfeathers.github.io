-- Migration: add notes to trips for shared trip coordination (e.g. "can you buy meals?", "I don't have a filter").
-- Run after schema.sql and migrations 001–003.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'trips' AND column_name = 'notes') THEN
    ALTER TABLE trips ADD COLUMN notes TEXT DEFAULT '';
  END IF;
END $$;
