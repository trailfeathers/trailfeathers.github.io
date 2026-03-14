"""
TrailFeathers - User favorite hikes (up to 4 per user): list, add, remove; used by friends routes.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor
from .trip_report_info import get_trip_report_info_by_id


def list_favorite_hikes(user_id):
    """Return list of favorite hikes for user: [{ id, hike_name, distance, elevation_gain, difficulty, source_url }] from trip_report_info."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT tri.id, tri.hike_name, tri.distance, tri.elevation_gain, tri.difficulty, tri.source_url
               FROM user_favorite_hikes ufh
               JOIN trip_report_info tri ON tri.id = ufh.trip_report_info_id
               WHERE ufh.user_id = %s
               ORDER BY tri.hike_name""",
            (user_id,),
        )
        return cur.fetchall()


def add_favorite_hike(user_id, trip_report_info_id):
    """Add a hike to user's favorites. At most 4 per user. Ignores if already present. Raises ValueError if trip_report_info_id invalid or limit reached."""
    location = get_trip_report_info_by_id(trip_report_info_id)
    if not location:
        raise ValueError("Location not found in catalog.")
    with get_cursor() as cur:
        cur.execute(
            """SELECT COUNT(*) AS n FROM user_favorite_hikes WHERE user_id = %s""",
            (user_id,),
        )
        n = cur.fetchone()["n"]
        if n >= 4:
            raise ValueError("You can have at most 4 favorite hikes.")
        cur.execute(
            """INSERT INTO user_favorite_hikes (user_id, trip_report_info_id)
               VALUES (%s, %s)
               ON CONFLICT (user_id, trip_report_info_id) DO NOTHING""",
            (user_id, trip_report_info_id),
        )


def remove_favorite_hike(user_id, trip_report_info_id):
    """Remove a hike from user's favorites. No-op if not present."""
    with get_cursor() as cur:
        cur.execute(
            """DELETE FROM user_favorite_hikes
               WHERE user_id = %s AND trip_report_info_id = %s""",
            (user_id, trip_report_info_id),
        )
