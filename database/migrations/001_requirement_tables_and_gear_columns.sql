-- TrailFeathers - Migration 001: add requirement tables and gear columns.
-- Group: TrailFeathers
-- Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
-- Last updated: 3/13/26
-- Run if DB was created before requirement_types/activity_requirements. Then run seed_requirements.sql.

-- 1. Create requirement tables (must exist before gear can reference them)
CREATE TABLE IF NOT EXISTS requirement_types (
  id BIGSERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_requirement_types_key ON requirement_types(key);

CREATE TABLE IF NOT EXISTS activity_requirements (
  id BIGSERIAL PRIMARY KEY,
  activity_type TEXT NOT NULL,
  requirement_type_id BIGINT NOT NULL REFERENCES requirement_types(id) ON DELETE CASCADE,
  rule TEXT NOT NULL CHECK (rule IN ('per_group', 'per_person', 'per_N_persons')),
  quantity INT NOT NULL DEFAULT 1,
  n_persons INT,
  CONSTRAINT activity_requirements_n_persons CHECK (
    (rule = 'per_N_persons' AND n_persons IS NOT NULL AND n_persons > 0) OR
    (rule != 'per_N_persons' AND n_persons IS NULL)
  ),
  UNIQUE(activity_type, requirement_type_id)
);
CREATE INDEX IF NOT EXISTS idx_activity_requirements_activity_type ON activity_requirements(activity_type);

-- 2. Add columns to gear if they don't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'gear' AND column_name = 'requirement_type_id') THEN
    ALTER TABLE gear ADD COLUMN requirement_type_id BIGINT REFERENCES requirement_types(id) ON DELETE SET NULL;
    CREATE INDEX IF NOT EXISTS idx_gear_requirement_type_id ON gear(requirement_type_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'gear' AND column_name = 'capacity_persons') THEN
    ALTER TABLE gear ADD COLUMN capacity_persons INT;
    ALTER TABLE gear ADD CONSTRAINT gear_capacity_persons_positive CHECK (capacity_persons IS NULL OR capacity_persons > 0);
  END IF;
END $$;
