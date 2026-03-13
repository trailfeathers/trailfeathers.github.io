/**
 * TrailFeathers main entry. Imports all feature modules so their DOMContentLoaded handlers run.
 * Use this as the single script on pages that use the refactored script (index, login, register,
 * dashboard, inventory, trip, trip_dashboard). Friends page uses its own script (social_center_friends.js).
 */
import "./config.js";
import "./utils.js";
import "./auth.js";
import "./dashboard.js";
import "./inventory.js";
import "./friends.js";
import "./trips.js";
import "./trip-dashboard.js";
import "./navigation.js";
