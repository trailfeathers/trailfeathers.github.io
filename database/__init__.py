"""
TrailFeathers database package. Single import surface: use

  from database import get_cursor, create_user, list_gear, ...

All public API is re-exported from database.database, which pulls from submodules:
connection, users, trip_report_info, requirements, gear, friends, favorites, profiles,
top_four, user_trip_reports, wishlist, trips, trip_invites, trip_gear.
"""
from .database import *  # noqa: F401, F403
