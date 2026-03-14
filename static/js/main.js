/**
 * TrailFeathers main entry. Imports all feature modules so their DOMContentLoaded handlers run.
 * Use this as the single script (type="module" src="js/main.js") on pages that use the refactored
 * script: index, login, register, dashboard, inventory, trip, trip_dashboard. The Social Center
 * friends page uses its own script (social_center_friends.js) and does not load this file.
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
