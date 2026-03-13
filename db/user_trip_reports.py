"""User trip reports."""
from .connection import get_cursor
from .trip_reports import get_trip_report_info_by_id


def list_user_trip_reports(user_id):
    """Return list of trip reports for user: id, title, trip_report_info_id, hike_name, date_hiked, created_at, updated_at."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT utr.id, utr.title, utr.trip_report_info_id, utr.body, utr.date_hiked, utr.created_at, utr.updated_at,
                      tri.hike_name
               FROM user_trip_reports utr
               JOIN trip_report_info tri ON tri.id = utr.trip_report_info_id
               WHERE utr.user_id = %s
               ORDER BY utr.created_at DESC""",
            (user_id,),
        )
        return cur.fetchall()


def get_user_trip_report(report_id, user_id=None):
    """Return one trip report by id. If user_id given, only return if owner; else return any (for public view). Includes hike_name, image_uploaded."""
    with get_cursor() as cur:
        if user_id is not None:
            cur.execute(
                """SELECT utr.id, utr.user_id, utr.trip_report_info_id, utr.title, utr.body, utr.date_hiked, utr.created_at, utr.updated_at,
                          tri.hike_name,
                          (utr.image IS NOT NULL) AS image_uploaded
                   FROM user_trip_reports utr
                   JOIN trip_report_info tri ON tri.id = utr.trip_report_info_id
                   WHERE utr.id = %s AND utr.user_id = %s""",
                (report_id, user_id),
            )
        else:
            cur.execute(
                """SELECT utr.id, utr.user_id, utr.trip_report_info_id, utr.title, utr.body, utr.date_hiked, utr.created_at, utr.updated_at,
                          tri.hike_name,
                          (utr.image IS NOT NULL) AS image_uploaded
                   FROM user_trip_reports utr
                   JOIN trip_report_info tri ON tri.id = utr.trip_report_info_id
                   WHERE utr.id = %s""",
                (report_id,),
            )
        return cur.fetchone()


def set_trip_report_image_upload(report_id, user_id, image_bytes, media_type):
    """Store uploaded image for a trip report. Owner only. Max 5MB. Raises ValueError if not found or invalid."""
    report = get_user_trip_report(report_id, user_id)
    if not report:
        raise ValueError("Trip report not found.")
    if not image_bytes or len(image_bytes) > 5 * 1024 * 1024:
        raise ValueError("Image required and must be under 5MB.")
    mt = (media_type or "image/jpeg").strip().lower()
    if mt not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        raise ValueError("Allowed types: image/jpeg, image/png, image/gif, image/webp")
    with get_cursor() as cur:
        cur.execute(
            """UPDATE user_trip_reports SET image = %s, image_media_type = %s, updated_at = NOW()
               WHERE id = %s AND user_id = %s""",
            (image_bytes, mt, report_id, user_id),
        )


def get_trip_report_image_payload(report_id):
    """Return dict with keys bytes, media_type if report has image; else None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT image, image_media_type FROM user_trip_reports WHERE id = %s AND image IS NOT NULL""",
            (report_id,),
        )
        row = cur.fetchone()
        if not row or not row.get("image"):
            return None
        return {"bytes": row["image"], "media_type": row.get("image_media_type") or "image/jpeg"}


def create_user_trip_report(user_id, trip_report_info_id, title, body="", date_hiked=None):
    """Create a trip report. Returns new report id."""
    title = (title or "").strip()
    if not title:
        raise ValueError("Title is required")
    loc = get_trip_report_info_by_id(trip_report_info_id)
    if not loc:
        raise ValueError("Location not found in catalog.")
    body = (body or "").strip() or ""
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO user_trip_reports (user_id, trip_report_info_id, title, body, date_hiked, updated_at)
               VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id""",
            (user_id, trip_report_info_id, title, body, date_hiked),
        )
        return cur.fetchone()["id"]


def update_user_trip_report(report_id, user_id, trip_report_info_id=None, title=None, body=None, date_hiked=None):
    """Update a trip report. Only owner. Optional fields: trip_report_info_id, title, body, date_hiked."""
    report = get_user_trip_report(report_id, user_id)
    if not report:
        raise ValueError("Trip report not found.")
    updates = []
    params = []
    if title is not None:
        t = (title or "").strip()
        if not t:
            raise ValueError("Title cannot be empty")
        updates.append("title = %s")
        params.append(t)
    if body is not None:
        updates.append("body = %s")
        params.append((body or "").strip() or "")
    if date_hiked is not None:
        updates.append("date_hiked = %s")
        params.append(date_hiked)
    if trip_report_info_id is not None:
        loc = get_trip_report_info_by_id(trip_report_info_id)
        if not loc:
            raise ValueError("Location not found in catalog.")
        updates.append("trip_report_info_id = %s")
        params.append(trip_report_info_id)
    if not updates:
        return
    updates.append("updated_at = NOW()")
    params.extend([report_id, user_id])
    with get_cursor() as cur:
        cur.execute(
            """UPDATE user_trip_reports SET """ + ", ".join(updates) + """ WHERE id = %s AND user_id = %s""",
            params,
        )


def delete_user_trip_report(report_id, user_id):
    """Delete a trip report. Only owner. Raises ValueError if not found."""
    report = get_user_trip_report(report_id, user_id)
    if not report:
        raise ValueError("Trip report not found.")
    with get_cursor() as cur:
        cur.execute("""DELETE FROM user_trip_reports WHERE id = %s AND user_id = %s""", (report_id, user_id))


