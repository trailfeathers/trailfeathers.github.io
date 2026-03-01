-- Seed requirement_types and activity_requirements.
-- Run after schema.sql (or after migration that creates tables and adds gear columns).
-- Safe to run multiple times: uses INSERT ... ON CONFLICT for requirement_types.

-- Requirement types (comprehensive gear taxonomy)
INSERT INTO requirement_types (key, display_name) VALUES
  ('shelter', 'Shelter (tent/tarp)'),
  ('sleeping_bag', 'Sleeping bag'),
  ('sleeping_pad', 'Sleeping pad'),
  ('backpack', 'Backpack'),
  ('water_filter', 'Water filter'),
  ('stove', 'Stove'),
  ('cookware', 'Cookware'),
  ('first_aid', 'First aid kit'),
  ('headlamp', 'Headlamp'),
  ('navigation', 'Navigation (map/compass/GPS)'),
  ('rain_gear', 'Rain gear'),
  ('insulation_layer', 'Insulation layer'),
  ('sun_protection', 'Sun protection'),
  ('emergency_shelter', 'Emergency shelter/bivy'),
  ('beacon', 'Beacon (avalanche/PLB)'),
  ('helmet', 'Helmet'),
  ('harness', 'Harness'),
  ('rope', 'Rope'),
  ('daypack', 'Daypack'),
  ('water_capacity', 'Water (capacity)'),
  ('snacks_food', 'Snacks/food'),
  ('binoculars', 'Binoculars'),
  ('field_guide', 'Field guide'),
  ('cooler', 'Cooler'),
  ('lantern', 'Lantern'),
  ('skis', 'Skis'),
  ('avalanche_gear', 'Avalanche gear'),
  ('other', 'Other')
ON CONFLICT (key) DO NOTHING;

-- Activity requirements: Backpacking (safety-expanded)
INSERT INTO activity_requirements (activity_type, requirement_type_id, rule, quantity, n_persons)
SELECT 'Backpacking', id, 'per_N_persons', 1, 2 FROM requirement_types WHERE key = 'shelter'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sleeping_bag'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sleeping_pad'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'backpack'
UNION ALL SELECT 'Backpacking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'water_filter'
UNION ALL SELECT 'Backpacking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'stove'
UNION ALL SELECT 'Backpacking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'cookware'
UNION ALL SELECT 'Backpacking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'first_aid'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'headlamp'
UNION ALL SELECT 'Backpacking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'navigation'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'rain_gear'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'insulation_layer'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sun_protection'
UNION ALL SELECT 'Backpacking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'emergency_shelter'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'water_capacity'
UNION ALL SELECT 'Backpacking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'snacks_food'
ON CONFLICT (activity_type, requirement_type_id) DO NOTHING;

-- Activity requirements: Hiking
INSERT INTO activity_requirements (activity_type, requirement_type_id, rule, quantity, n_persons)
SELECT 'Hiking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'daypack'
UNION ALL SELECT 'Hiking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'water_capacity'
UNION ALL SELECT 'Hiking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'snacks_food'
UNION ALL SELECT 'Hiking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'first_aid'
UNION ALL SELECT 'Hiking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sun_protection'
UNION ALL SELECT 'Hiking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'headlamp'
UNION ALL SELECT 'Hiking', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'navigation'
UNION ALL SELECT 'Hiking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'insulation_layer'
UNION ALL SELECT 'Hiking', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'rain_gear'
ON CONFLICT (activity_type, requirement_type_id) DO NOTHING;

-- Activity requirements: Car Camping
INSERT INTO activity_requirements (activity_type, requirement_type_id, rule, quantity, n_persons)
SELECT 'Car Camping', id, 'per_N_persons', 1, 2 FROM requirement_types WHERE key = 'shelter'
UNION ALL SELECT 'Car Camping', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sleeping_bag'
UNION ALL SELECT 'Car Camping', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sleeping_pad'
UNION ALL SELECT 'Car Camping', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'cooler'
UNION ALL SELECT 'Car Camping', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'lantern'
UNION ALL SELECT 'Car Camping', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'first_aid'
UNION ALL SELECT 'Car Camping', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sun_protection'
UNION ALL SELECT 'Car Camping', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'stove'
UNION ALL SELECT 'Car Camping', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'cookware'
ON CONFLICT (activity_type, requirement_type_id) DO NOTHING;

-- Activity requirements: Bird Watching
INSERT INTO activity_requirements (activity_type, requirement_type_id, rule, quantity, n_persons)
SELECT 'Bird Watching', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'binoculars'
UNION ALL SELECT 'Bird Watching', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'field_guide'
UNION ALL SELECT 'Bird Watching', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'daypack'
UNION ALL SELECT 'Bird Watching', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'water_capacity'
UNION ALL SELECT 'Bird Watching', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'snacks_food'
UNION ALL SELECT 'Bird Watching', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'sun_protection'
ON CONFLICT (activity_type, requirement_type_id) DO NOTHING;

-- Activity requirements: Backcountry Skiing
INSERT INTO activity_requirements (activity_type, requirement_type_id, rule, quantity, n_persons)
SELECT 'Backcountry Skiing', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'skis'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'avalanche_gear'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'beacon'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'first_aid'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'headlamp'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'insulation_layer'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'rain_gear'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'navigation'
UNION ALL SELECT 'Backcountry Skiing', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'emergency_shelter'
ON CONFLICT (activity_type, requirement_type_id) DO NOTHING;

-- Activity requirements: Mountaineering
INSERT INTO activity_requirements (activity_type, requirement_type_id, rule, quantity, n_persons)
SELECT 'Mountaineering', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'helmet'
UNION ALL SELECT 'Mountaineering', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'harness'
UNION ALL SELECT 'Mountaineering', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'rope'
UNION ALL SELECT 'Mountaineering', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'first_aid'
UNION ALL SELECT 'Mountaineering', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'headlamp'
UNION ALL SELECT 'Mountaineering', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'insulation_layer'
UNION ALL SELECT 'Mountaineering', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'rain_gear'
UNION ALL SELECT 'Mountaineering', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'navigation'
UNION ALL SELECT 'Mountaineering', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'emergency_shelter'
UNION ALL SELECT 'Mountaineering', id, 'per_person', 1, NULL FROM requirement_types WHERE key = 'backpack'
UNION ALL SELECT 'Mountaineering', id, 'per_group', 1, NULL FROM requirement_types WHERE key = 'water_filter'
ON CONFLICT (activity_type, requirement_type_id) DO NOTHING;
