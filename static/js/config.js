/**
 * API and client-side config for TrailFeathers.
 */

export const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

// Gear library: map requirement_type key → category for dashboard grouping (client-side only)
export const REQUIREMENT_KEY_TO_CATEGORY = {
  shelter: "Sleep Systems",
  sleeping_bag: "Sleep Systems",
  sleeping_pad: "Sleep Systems",
  emergency_shelter: "Sleep Systems",
  water_filter: "Food & Water",
  stove: "Food & Water",
  cookware: "Food & Water",
  water_capacity: "Food & Water",
  snacks_food: "Food & Water",
  cooler: "Food & Water",
  lantern: "Food & Water",
  backpack: "Packs",
  daypack: "Packs",
  first_aid: "Safety & First Aid",
  headlamp: "Safety & First Aid",
  navigation: "Safety & First Aid",
  rain_gear: "Safety & First Aid",
  sun_protection: "Safety & First Aid",
  beacon: "Safety & First Aid",
  avalanche_gear: "Safety & First Aid",
  insulation_layer: "Clothing & Layers",
  helmet: "Climbing & Technical",
  harness: "Climbing & Technical",
  rope: "Climbing & Technical",
  binoculars: "Other",
  field_guide: "Other",
  skis: "Other",
  other: "Other"
};

export const GEAR_CATEGORY_ORDER = [
  "Sleep Systems",
  "Food & Water",
  "Packs",
  "Safety & First Aid",
  "Clothing & Layers",
  "Climbing & Technical",
  "Other"
];
