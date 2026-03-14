-- TrailFeathers - Migration 002: link trips to trip_report_info (location catalog).
-- Group: TrailFeathers
-- Authors: Kim, Smith, Domst, and Snider
-- Last updated: 3/13/26

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'trips' AND column_name = 'trip_report_info_id') THEN
    ALTER TABLE trips ADD COLUMN trip_report_info_id BIGINT REFERENCES trip_report_info(id) ON DELETE SET NULL;
    CREATE INDEX IF NOT EXISTS idx_trips_trip_report_info_id ON trips(trip_report_info_id);
  END IF;
END $$;
