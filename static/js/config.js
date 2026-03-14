/**
 * TrailFeathers - API and client-side config (API_BASE, REQUIREMENT_KEY_TO_CATEGORY, GEAR_CATEGORY_ORDER).
 * Group: TrailFeathers
 * Authors: Kim, Smith, Domst, and Snider
 * Last updated: 3/13/26
 *
 * API_BASE is the backend root (e.g. for fetch(API_BASE + "/api/gear")).
 * REQUIREMENT_KEY_TO_CATEGORY and GEAR_CATEGORY_ORDER are used only on the client
 * to group gear items into sections (Sleep Systems, Food & Water, etc.) on the inventory page.
 */

export const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

/** Map requirement_type key → display category for inventory grouping (client-side only). */
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

/** Order in which category sections appear on the inventory page. */
export const GEAR_CATEGORY_ORDER = [
  "Sleep Systems",
  "Food & Water",
  "Packs",
  "Safety & First Aid",
  "Clothing & Layers",
  "Climbing & Technical",
  "Other"
];
