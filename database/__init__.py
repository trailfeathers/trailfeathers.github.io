"""
TrailFeathers - Database package; single import surface (from database import ...).
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26

Re-exports from database.database; submodules: connection, users, trip_report_info, requirements,
gear, friends, favorites, profiles, top_four, user_trip_reports, wishlist, trips, trip_invites, trip_gear.
"""
from .database import *  # noqa: F401, F403
