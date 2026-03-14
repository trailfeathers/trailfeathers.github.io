"""
TrailFeathers - User wishlist: list, add, remove by trip_report_info_id; used by wishlist routes.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor
from .trip_reports import get_trip_report_info_by_id


def list_wishlist(user_id):
    """Return list of wishlist items: id (trip_report_info_id), hike_name, distance, elevation_gain, difficulty, source_url."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT tri.id, tri.hike_name, tri.distance, tri.elevation_gain, tri.difficulty, tri.source_url
               FROM user_wishlist uw
               JOIN trip_report_info tri ON tri.id = uw.trip_report_info_id
               WHERE uw.user_id = %s
               ORDER BY tri.hike_name""",
            (user_id,),
        )
        return cur.fetchall()


def add_wishlist_item(user_id, trip_report_info_id):
    """Add a hike to wishlist. Raises ValueError if location not found."""
    loc = get_trip_report_info_by_id(trip_report_info_id)
    if not loc:
        raise ValueError("Location not found in catalog.")
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO user_wishlist (user_id, trip_report_info_id)
               VALUES (%s, %s)
               ON CONFLICT (user_id, trip_report_info_id) DO NOTHING""",
            (user_id, trip_report_info_id),
        )


def remove_wishlist_item(user_id, trip_report_info_id):
    """Remove a hike from wishlist. No-op if not present."""
    with get_cursor() as cur:
        cur.execute(
            """DELETE FROM user_wishlist WHERE user_id = %s AND trip_report_info_id = %s""",
            (user_id, trip_report_info_id),
        )


