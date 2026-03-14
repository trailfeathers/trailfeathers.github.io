"""
TrailFeathers - Trip report catalog (trip_report_info): insert, list, get by id or trip; used by routes and LLM.
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor


def insert_trip_report_info(trip_id, info):
    """Insert one trip_report_info row for an existing trip. Returns inserted id."""
    summarized_description = (info.get("summarized_description") or "").strip()
    if not summarized_description:
        raise ValueError("summarized_description is required")

    hike_name = (info.get("hike_name") or "").strip() or None
    source_url = (info.get("source_url") or "").strip() or None
    distance = (info.get("distance") or "").strip() or None
    elevation_gain = (info.get("elevation_gain") or "").strip() or None
    highpoint = (info.get("highpoint") or "").strip() or None
    difficulty = (info.get("difficulty") or "").strip() or None
    trip_report_1 = (info.get("trip_report_1") or "").strip() or None
    trip_report_2 = (info.get("trip_report_2") or "").strip() or None
    lat = (info.get("lat") or "").strip() or None
    long_value = (info.get("long") or "").strip() or None

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO trip_report_info (
                    trip_id,
                    summarized_description,
                    hike_name,
                    source_url,
                    distance,
                    elevation_gain,
                    highpoint,
                    difficulty,
                    trip_report_1,
                    trip_report_2,
                    lat,
                    long
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id""",
            (
                trip_id,
                summarized_description,
                hike_name,
                source_url,
                distance,
                elevation_gain,
                highpoint,
                difficulty,
                trip_report_1,
                trip_report_2,
                lat,
                long_value,
            ),
        )
        row = cur.fetchone()
        return row["id"]


def list_trip_report_info_for_selection():
    """Return all trip_report_info rows for location catalog: id, hike_name, distance, elevation_gain, difficulty. Ordered by hike_name."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, hike_name, distance, elevation_gain, difficulty, source_url
               FROM trip_report_info
               WHERE (hike_name IS NOT NULL AND hike_name != '')
               ORDER BY hike_name""",
        )
        return cur.fetchall()


def get_trip_report_info_by_id(info_id):
    """Return one trip_report_info row by id, or None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, hike_name, summarized_description, source_url, distance,
                      elevation_gain, highpoint, difficulty, trip_report_1, trip_report_2, lat, long
               FROM trip_report_info WHERE id = %s""",
            (info_id,),
        )
        return cur.fetchone()


def get_trip_report_info_for_trip(trip_id):
    """Return trip_report_info for a trip (via trips.trip_report_info_id), or None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT tri.id, tri.hike_name, tri.summarized_description, tri.source_url,
                      tri.distance, tri.elevation_gain, tri.highpoint, tri.difficulty,
                      tri.trip_report_1, tri.trip_report_2, tri.lat, tri.long
               FROM trips t
               JOIN trip_report_info tri ON tri.id = t.trip_report_info_id
               WHERE t.id = %s""",
            (trip_id,),
        )
        return cur.fetchone()
