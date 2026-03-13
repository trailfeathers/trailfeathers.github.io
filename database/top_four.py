"""Top four hikes."""
from .connection import get_cursor
from .trip_report_info import get_trip_report_info_by_id


def user_has_trip_report_for_info(user_id, trip_report_info_id):
    """True if the user has written at least one trip report for this catalog hike."""
    if trip_report_info_id is None:
        return False
    try:
        info_id = int(trip_report_info_id)
    except (TypeError, ValueError):
        return False
    with get_cursor() as cur:
        cur.execute(
            """SELECT 1 FROM user_trip_reports WHERE user_id = %s AND trip_report_info_id = %s LIMIT 1""",
            (user_id, info_id),
        )
        return cur.fetchone() is not None


def list_top_four_hikes(user_id):
    """Return list of up to 4 items: position, trip_report_info_id, hike_name, etc. from trip_report_info.
    Also includes latest_report_id and image_report_id (latest trip report with uploaded image) for thumbnails.
    Positions 1-4; missing positions are not in list."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT
                 ut.position,
                 ut.trip_report_info_id,
                 tri.hike_name,
                 tri.distance,
                 tri.elevation_gain,
                 tri.difficulty,
                 tri.source_url,
                 lr.latest_report_id,
                 ir.image_report_id
               FROM user_top_four_hikes ut
               JOIN trip_report_info tri ON tri.id = ut.trip_report_info_id
               LEFT JOIN LATERAL (
                 SELECT utr.id AS latest_report_id
                 FROM user_trip_reports utr
                 WHERE utr.user_id = %s AND utr.trip_report_info_id = ut.trip_report_info_id
                 ORDER BY utr.updated_at DESC NULLS LAST, utr.created_at DESC
                 LIMIT 1
               ) lr ON TRUE
               LEFT JOIN LATERAL (
                 SELECT utr.id AS image_report_id
                 FROM user_trip_reports utr
                 WHERE utr.user_id = %s
                   AND utr.trip_report_info_id = ut.trip_report_info_id
                   AND utr.image IS NOT NULL
                 ORDER BY utr.updated_at DESC NULLS LAST, utr.created_at DESC
                 LIMIT 1
               ) ir ON TRUE
               WHERE ut.user_id = %s
               ORDER BY ut.position""",
            (user_id, user_id, user_id),
        )
        return cur.fetchall()


def set_top_four_slot(user_id, position, trip_report_info_id):
    """Set one slot (1-4) to a trip_report_info_id. User must have a trip report for that hike."""
    if position not in (1, 2, 3, 4):
        raise ValueError("Position must be 1, 2, 3, or 4")
    loc = get_trip_report_info_by_id(trip_report_info_id)
    if not loc:
        raise ValueError("Location not found in catalog.")
    if not user_has_trip_report_for_info(user_id, trip_report_info_id):
        raise ValueError(
            "You can only add hikes you've written a trip report for. Write a report first."
        )
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO user_top_four_hikes (user_id, position, trip_report_info_id)
               VALUES (%s, %s, %s)
               ON CONFLICT (user_id, position) DO UPDATE SET trip_report_info_id = EXCLUDED.trip_report_info_id""",
            (user_id, position, trip_report_info_id),
        )


def clear_top_four_slot(user_id, position):
    """Clear one slot (1-4). No-op if already empty."""
    if position not in (1, 2, 3, 4):
        raise ValueError("Position must be 1, 2, 3, or 4")
    with get_cursor() as cur:
        cur.execute(
            """DELETE FROM user_top_four_hikes WHERE user_id = %s AND position = %s""",
            (user_id, position),
        )


def list_top_four_eligible_hikes(user_id):
    """Distinct catalog hikes the user has at least one trip report for (for top-four picker)."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT DISTINCT utr.trip_report_info_id AS id, tri.hike_name
               FROM user_trip_reports utr
               JOIN trip_report_info tri ON tri.id = utr.trip_report_info_id
               WHERE utr.user_id = %s
               ORDER BY tri.hike_name""",
            (user_id,),
        )
        return cur.fetchall()


def replace_top_four(user_id, slots):
    """Replace user's top four. slots: list of dicts with position (1-4) and trip_report_info_id.
    Each trip_report_info_id must be a hike the user has written a trip report for.
    If a slot has a hike the user has no report for, that slot is cleared (skipped) instead of error."""
    with get_cursor() as cur:
        cur.execute("""DELETE FROM user_top_four_hikes WHERE user_id = %s""", (user_id,))
        for s in slots:
            pos = s.get("position")
            raw_id = s.get("trip_report_info_id")
            if pos not in (1, 2, 3, 4):
                continue
            try:
                info_id = int(raw_id) if raw_id is not None else None
            except (TypeError, ValueError):
                info_id = None
            if info_id is None:
                continue
            loc = get_trip_report_info_by_id(info_id)
            if not loc:
                continue
            if not user_has_trip_report_for_info(user_id, info_id):
                # Slot has a hike user has no report for (e.g. stale "remove to clear") — skip so slot stays cleared
                continue
            cur.execute(
                """INSERT INTO user_top_four_hikes (user_id, position, trip_report_info_id)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (user_id, position) DO UPDATE SET trip_report_info_id = EXCLUDED.trip_report_info_id""",
                (user_id, pos, info_id),
            )
