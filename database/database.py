
"""
Single database module for TrailFeathers.
Uses DATABASE_URL (e.g. Neon PostgreSQL). Falls back to in-memory if not set.
"""
import os
from contextlib import contextmanager

# Prefer psycopg2 for RealDictCursor; fall back to psycopg (v3) if needed
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    _use_psycopg2 = True
except ImportError:
    import psycopg
    _use_psycopg2 = False


def get_db_connection():
    """Return a live DB connection (cursor returns dict-like rows). Caller must close it."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "For local dev, use a Neon PostgreSQL URL."
        )
    if _use_psycopg2:
        return psycopg2.connect(url, cursor_factory=RealDictCursor)
    conn = psycopg.connect(url)
    conn.row_factory = psycopg.rows.dict_row
    return conn


@contextmanager
def get_cursor():
    """Context manager: connection + cursor that returns dict rows. Commits on exit."""
    conn = get_db_connection()
    try:
        if _use_psycopg2:
            cur = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()


# ---------- Users ----------
def get_user_by_id(user_id):
    with get_cursor() as cur:
        cur.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def get_user_by_username(username):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        )
        return cur.fetchone()


def create_user(username, password_hash):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username",
            (username, password_hash),
        )
        return cur.fetchone()


def user_exists_by_username(username):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cur.fetchone() is not None


def get_first_user():
    """Return the first user by id, or None if users table is empty."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, username
               FROM users
               ORDER BY id ASC
               LIMIT 1""",
        )
        return cur.fetchone()


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


# ---------- Requirement types and activity requirements ----------
def list_requirement_types():
    """Return all requirement types: id, key, display_name. Ordered by display_name."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, key, display_name FROM requirement_types
               ORDER BY display_name""",
        )
        return cur.fetchall()


def list_activity_requirements(activity_type):
    """Return requirements for an activity: id, requirement_type_id, rule, quantity, n_persons,
       plus requirement type key and display_name from requirement_types."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT ar.id, ar.requirement_type_id, ar.rule, ar.quantity, ar.n_persons,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name
               FROM activity_requirements ar
               JOIN requirement_types rt ON rt.id = ar.requirement_type_id
               WHERE ar.activity_type = %s
               ORDER BY rt.display_name""",
            (activity_type,),
        )
        return cur.fetchall()


def _required_count_for_rule(rule, quantity, n_persons, num_people):
    """Compute required count given rule and head count."""
    import math
    if rule == "per_group":
        return quantity
    if rule == "per_person":
        return quantity * num_people
    if rule == "per_N_persons" and n_persons and n_persons > 0:
        return quantity * math.ceil(num_people / n_persons)
    return 0


def _covered_count_for_type(assigned_gear_rows):
    """From list of gear rows (with capacity_persons), sum coverage. Group-shareable (NULL) counts as 1 per type."""
    if not assigned_gear_rows:
        return 0
    total = 0
    for row in assigned_gear_rows:
        cap = row.get("capacity_persons")
        if cap is not None:
            total += cap
        else:
            total += 1
    return total


def get_trip_requirement_summary(trip_id):
    """For the trip's activity, return list of requirement rows with required_count, covered_count, status.
    Each row: requirement_type_id, requirement_key, requirement_display_name, rule, quantity, n_persons,
    required_count, covered_count, status ('met' | 'short').
    """
    trip = get_trip(trip_id)
    if not trip:
        return None
    activity_type = (trip.get("activity_type") or "").strip()
    if not activity_type:
        return []
    reqs = list_activity_requirements(activity_type)
    if not reqs:
        return []

    # Head count
    collabs = list_trip_collaborators(trip_id)
    num_people = len(collabs)

    # Assigned gear for this trip, with requirement_type_id and capacity_persons
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.requirement_type_id, g.capacity_persons
               FROM trip_gear tg
               JOIN gear g ON g.id = tg.gear_id
               WHERE tg.trip_id = %s""",
            (trip_id,),
        )
        assigned = cur.fetchall()

    # Group assigned gear by requirement_type_id
    by_type = {}
    for row in assigned:
        rt_id = row.get("requirement_type_id")
        if rt_id is not None:
            by_type.setdefault(rt_id, []).append(row)

    out = []
    for ar in reqs:
        rt_id = ar["requirement_type_id"]
        rule = ar["rule"]
        quantity = ar["quantity"]
        n_persons = ar.get("n_persons")
        required = _required_count_for_rule(rule, quantity, n_persons, num_people)
        covered = _covered_count_for_type(by_type.get(rt_id, []))
        status = "met" if covered >= required else "short"
        out.append({
            "requirement_type_id": rt_id,
            "requirement_key": ar["requirement_key"],
            "requirement_display_name": ar["requirement_display_name"],
            "rule": rule,
            "quantity": quantity,
            "n_persons": n_persons,
            "required_count": required,
            "covered_count": covered,
            "status": status,
        })
    return out


# ---------- Gear ----------
def add_gear_item(user_id, payload):
    """Add a gear item for user. Returns new gear id."""
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Gear name is required")
    gear_type = (payload.get("type") or "other").strip() or "other"
    capacity = (payload.get("capacity") or "").strip() or None
    weight_oz = payload.get("weight_oz")
    if weight_oz is not None and weight_oz != "":
        try:
            weight_oz = float(weight_oz)
        except (TypeError, ValueError):
            weight_oz = None
    else:
        weight_oz = None
    brand = (payload.get("brand") or "").strip() or None
    condition = (payload.get("condition") or "").strip() or None
    notes = (payload.get("notes") or "").strip() or None
    requirement_type_id = payload.get("requirement_type_id")
    if requirement_type_id is not None and requirement_type_id != "":
        try:
            requirement_type_id = int(requirement_type_id)
        except (TypeError, ValueError):
            requirement_type_id = None
    else:
        requirement_type_id = None
    capacity_persons = payload.get("capacity_persons")
    if capacity_persons is not None and capacity_persons != "":
        try:
            capacity_persons = int(capacity_persons)
            if capacity_persons < 1:
                capacity_persons = None
        except (TypeError, ValueError):
            capacity_persons = None
    else:
        capacity_persons = None

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO gear (user_id, type, name, capacity, weight_oz, brand, condition, notes, requirement_type_id, capacity_persons)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (user_id, gear_type, name, capacity, weight_oz, brand, condition, notes, requirement_type_id, capacity_persons),
        )
        row = cur.fetchone()
        return row["id"]


def list_gear(user_id):
    """Return all gear for the given user (by user_id). Includes requirement_type key/display_name and capacity_persons."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.type, g.name, g.capacity, g.weight_oz, g.brand, g.condition, g.notes,
                      g.requirement_type_id, g.capacity_persons, g.created_at,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name
               FROM gear g
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               WHERE g.user_id = %s ORDER BY g.created_at DESC""",
            (user_id,),
        )
        return cur.fetchall()


def get_gear_item(gear_id, user_id):
    """Return one gear item by id if it belongs to user_id, else None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.type, g.name, g.capacity, g.weight_oz, g.brand, g.condition, g.notes,
                      g.requirement_type_id, g.capacity_persons, g.created_at,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name
               FROM gear g
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               WHERE g.id = %s AND g.user_id = %s""",
            (gear_id, user_id),
        )
        return cur.fetchone()


def _parse_gear_payload(payload):
    """Parse common gear fields from payload. Returns dict of (name, gear_type, capacity, weight_oz, brand, condition, notes, requirement_type_id, capacity_persons)."""
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Gear name is required")
    gear_type = (payload.get("type") or "other").strip() or "other"
    capacity = (payload.get("capacity") or "").strip() or None
    weight_oz = payload.get("weight_oz")
    if weight_oz is not None and weight_oz != "":
        try:
            weight_oz = float(weight_oz)
        except (TypeError, ValueError):
            weight_oz = None
    else:
        weight_oz = None
    brand = (payload.get("brand") or "").strip() or None
    condition = (payload.get("condition") or "").strip() or None
    notes = (payload.get("notes") or "").strip() or None
    requirement_type_id = payload.get("requirement_type_id")
    if requirement_type_id is not None and requirement_type_id != "":
        try:
            requirement_type_id = int(requirement_type_id)
        except (TypeError, ValueError):
            requirement_type_id = None
    else:
        requirement_type_id = None
    capacity_persons = payload.get("capacity_persons")
    if capacity_persons is not None and capacity_persons != "":
        try:
            capacity_persons = int(capacity_persons)
            if capacity_persons < 1:
                capacity_persons = None
        except (TypeError, ValueError):
            capacity_persons = None
    else:
        capacity_persons = None
    return {
        "name": name,
        "gear_type": gear_type,
        "capacity": capacity,
        "weight_oz": weight_oz,
        "brand": brand,
        "condition": condition,
        "notes": notes,
        "requirement_type_id": requirement_type_id,
        "capacity_persons": capacity_persons,
    }


def update_gear_item(gear_id, user_id, payload):
    """Update a gear item. Item must belong to user_id. Raises ValueError if not found or validation fails."""
    item = get_gear_item(gear_id, user_id)
    if not item:
        raise ValueError("Gear item not found.")
    parsed = _parse_gear_payload(payload)
    with get_cursor() as cur:
        cur.execute(
            """UPDATE gear SET name = %s, type = %s, capacity = %s, weight_oz = %s, brand = %s, condition = %s, notes = %s, requirement_type_id = %s, capacity_persons = %s
               WHERE id = %s AND user_id = %s""",
            (
                parsed["name"],
                parsed["gear_type"],
                parsed["capacity"],
                parsed["weight_oz"],
                parsed["brand"],
                parsed["condition"],
                parsed["notes"],
                parsed["requirement_type_id"],
                parsed["capacity_persons"],
                gear_id,
                user_id,
            ),
        )


def delete_gear_item(gear_id, user_id):
    """Delete a gear item. Only succeeds if it belongs to user_id. Raises ValueError if not found."""
    item = get_gear_item(gear_id, user_id)
    if not item:
        raise ValueError("Gear item not found.")
    with get_cursor() as cur:
        cur.execute("DELETE FROM gear WHERE id = %s AND user_id = %s", (gear_id, user_id))


# ---------- Friends ----------
def create_friend_request(sender_id, receiver_id):
    """Create a pending friend request. Returns request id. Raises ValueError for invalid/duplicate."""
    if sender_id == receiver_id:
        raise ValueError("Cannot send a friend request to yourself")
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, sender_id, receiver_id, status FROM friend_requests
               WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)""",
            (sender_id, receiver_id, receiver_id, sender_id),
        )
        existing = cur.fetchone()
        if existing:
            if existing["status"] == "accepted":
                raise ValueError("Already friends")
            if existing["status"] == "pending":
                if existing["sender_id"] == sender_id:
                    raise ValueError("Request already sent")
                raise ValueError("They already sent you a request")
            raise ValueError("Request already exists")
        cur.execute(
            """INSERT INTO friend_requests (sender_id, receiver_id, status)
               VALUES (%s, %s, 'pending') RETURNING id""",
            (sender_id, receiver_id),
        )
        row = cur.fetchone()
        return row["id"]


def list_incoming_requests(receiver_id):
    """Return pending requests where receiver_id = receiver_id, with sender username."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT fr.id, fr.sender_id, fr.created_at, u.username AS sender_username
               FROM friend_requests fr
               JOIN users u ON u.id = fr.sender_id
               WHERE fr.receiver_id = %s AND fr.status = 'pending'
               ORDER BY fr.created_at DESC""",
            (receiver_id,),
        )
        return cur.fetchall()


def accept_friend_request(request_id, receiver_id):
    """Set request to accepted. Only the receiver can accept. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            """UPDATE friend_requests SET status = 'accepted'
               WHERE id = %s AND receiver_id = %s AND status = 'pending'""",
            (request_id, receiver_id),
        )
        return cur.rowcount > 0


def decline_friend_request(request_id, receiver_id):
    """Set request to declined. Only the receiver can decline. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            """UPDATE friend_requests SET status = 'declined'
               WHERE id = %s AND receiver_id = %s AND status = 'pending'""",
            (request_id, receiver_id),
        )
        return cur.rowcount > 0


def list_friends(user_id):
    """Return list of friends: [{ id, username }] for the other user in each accepted pair."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT u.id, u.username
               FROM friend_requests fr
               JOIN users u ON (u.id = fr.receiver_id AND fr.sender_id = %s)
                          OR (u.id = fr.sender_id AND fr.receiver_id = %s)
               WHERE fr.status = 'accepted'
                 AND (fr.sender_id = %s OR fr.receiver_id = %s)""",
            (user_id, user_id, user_id, user_id),
        )
        return cur.fetchall()


# ---------- User favorite hikes (from catalog) ----------


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
    """Add a hike to user's favorites. Ignores if already present. Raises ValueError if trip_report_info_id invalid."""
    location = get_trip_report_info_by_id(trip_report_info_id)
    if not location:
        raise ValueError("Location not found in catalog.")
    with get_cursor() as cur:
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


# ---------- Trips ----------
ACTIVITY_TYPES = frozenset({
    "Backpacking",
    "Hiking",
    "Car Camping",
    "Bird Watching",
    "Backcountry Skiing",
    "Mountaineering",
})


def create_trip(creator_id, payload):
    """Create a trip and add creator as collaborator. Location must be chosen from catalog (trip_report_info_id). Returns trip id."""
    trip_name = (payload.get("trip_name") or "").strip()
    if not trip_name:
        raise ValueError("Trip name is required")
    activity_type = (payload.get("activity_type") or "").strip()
    if not activity_type or activity_type not in ACTIVITY_TYPES:
        raise ValueError("Activity type must be one of: " + ", ".join(sorted(ACTIVITY_TYPES)))
    intended_start_date = payload.get("intended_start_date")
    if intended_start_date is not None and intended_start_date != "":
        intended_start_date = intended_start_date.strip() or None

    trip_report_info_id = payload.get("trip_report_info_id")
    if trip_report_info_id is None:
        raise ValueError("Please select a location from the catalog.")
    try:
        info_id = int(trip_report_info_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid location selection.")
    location = get_trip_report_info_by_id(info_id)
    if not location:
        raise ValueError("Selected location not found. Please choose from the list.")
    trail_name = (location.get("hike_name") or "").strip() or "Unknown trail"

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO trips (creator_id, trip_name, trail_name, activity_type, intended_start_date, trip_report_info_id)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (creator_id, trip_name, trail_name, activity_type, intended_start_date, info_id),
        )
        row = cur.fetchone()
        trip_id = row["id"]
        cur.execute(
            """INSERT INTO trip_collaborators (trip_id, user_id, role) VALUES (%s, %s, 'creator')""",
            (trip_id, creator_id),
        )
        return trip_id


def list_trips_for_user(user_id):
    """Return trips where user is creator or in trip_collaborators. Includes creator username and trip_report_info_id."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT t.id, t.trip_name, t.trail_name, t.activity_type, t.intended_start_date,
                      t.creator_id, t.trip_report_info_id, u.username AS creator_username, t.created_at
               FROM trips t
               JOIN users u ON u.id = t.creator_id
               WHERE t.creator_id = %s
                  OR EXISTS (SELECT 1 FROM trip_collaborators tc WHERE tc.trip_id = t.id AND tc.user_id = %s)
               ORDER BY t.created_at DESC""",
            (user_id, user_id),
        )
        return cur.fetchall()


def update_trip(trip_id, user_id, payload):
    """Update a trip. User must have access (creator or collaborator). Updates trip_name, trail/location, activity_type, intended_start_date."""
    if not user_has_trip_access(user_id, trip_id):
        raise ValueError("You do not have access to this trip.")
    trip_name = (payload.get("trip_name") or "").strip()
    if not trip_name:
        raise ValueError("Trip name is required")
    activity_type = (payload.get("activity_type") or "").strip()
    if not activity_type or activity_type not in ACTIVITY_TYPES:
        raise ValueError("Activity type must be one of: " + ", ".join(sorted(ACTIVITY_TYPES)))
    intended_start_date = payload.get("intended_start_date")
    if intended_start_date is not None and intended_start_date != "":
        intended_start_date = intended_start_date.strip() or None
    else:
        intended_start_date = None

    trip_report_info_id = payload.get("trip_report_info_id")
    if trip_report_info_id is None:
        raise ValueError("Please select a location from the catalog.")
    try:
        info_id = int(trip_report_info_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid location selection.")
    location = get_trip_report_info_by_id(info_id)
    if not location:
        raise ValueError("Selected location not found. Please choose from the list.")
    trail_name = (location.get("hike_name") or "").strip() or "Unknown trail"

    with get_cursor() as cur:
        cur.execute(
            """UPDATE trips SET trip_name = %s, trail_name = %s, activity_type = %s, intended_start_date = %s, trip_report_info_id = %s
               WHERE id = %s""",
            (trip_name, trail_name, activity_type, intended_start_date, info_id, trip_id),
        )


def delete_trip(trip_id, user_id):
    """Delete a trip. Only the creator may delete. CASCADE removes collaborators, invites, gear."""
    trip = get_trip(trip_id)
    if not trip:
        raise ValueError("Trip not found.")
    if trip["creator_id"] != user_id:
        raise ValueError("Only the trip creator can delete this trip.")
    with get_cursor() as cur:
        cur.execute("DELETE FROM trips WHERE id = %s", (trip_id,))


def get_trip(trip_id):
    """Return one trip with creator username and trip_report_info_id, or None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT t.id, t.trip_name, t.trail_name, t.activity_type, t.intended_start_date,
                      t.creator_id, t.trip_report_info_id, u.username AS creator_username, t.created_at
               FROM trips t
               JOIN users u ON u.id = t.creator_id
               WHERE t.id = %s""",
            (trip_id,),
        )
        return cur.fetchone()


def user_has_trip_access(user_id, trip_id):
    """True if user is creator or in trip_collaborators."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT 1 FROM trips t
               WHERE t.id = %s AND t.creator_id = %s
               UNION
               SELECT 1 FROM trip_collaborators tc WHERE tc.trip_id = %s AND tc.user_id = %s""",
            (trip_id, user_id, trip_id, user_id),
        )
        return cur.fetchone() is not None


def list_trip_collaborators(trip_id):
    """Return list of collaborators: id, username, role (includes creator from trip_collaborators)."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT u.id, u.username, tc.role
               FROM trip_collaborators tc
               JOIN users u ON u.id = tc.user_id
               WHERE tc.trip_id = %s
               ORDER BY tc.role = 'creator' DESC, tc.added_at ASC""",
            (trip_id,),
        )
        return cur.fetchall()


def add_trip_collaborator(trip_id, user_id, role="member"):
    """Add a user to trip. Raises ValueError if already a collaborator."""
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM trip_collaborators WHERE trip_id = %s AND user_id = %s", (trip_id, user_id))
        if cur.fetchone():
            raise ValueError("Already a collaborator")
        cur.execute(
            """INSERT INTO trip_collaborators (trip_id, user_id, role) VALUES (%s, %s, %s)""",
            (trip_id, user_id, role),
        )


# ---------- Trip invites ----------
def create_trip_invite(trip_id, inviter_id, invitee_id):
    """Create a pending trip invite. Invitee must be a friend; must not already be collaborator or invited. Returns invite id."""
    if inviter_id == invitee_id:
        raise ValueError("Cannot invite yourself")
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM trip_collaborators WHERE trip_id = %s AND user_id = %s", (trip_id, invitee_id))
        if cur.fetchone():
            raise ValueError("Already a member")
        cur.execute(
            "SELECT id, status FROM trip_invites WHERE trip_id = %s AND invitee_id = %s",
            (trip_id, invitee_id),
        )
        existing = cur.fetchone()
        if existing:
            if existing["status"] == "pending":
                raise ValueError("Already invited")
            raise ValueError("Invite was already responded to")
        cur.execute(
            """INSERT INTO trip_invites (trip_id, inviter_id, invitee_id, status)
               VALUES (%s, %s, %s, 'pending') RETURNING id""",
            (trip_id, inviter_id, invitee_id),
        )
        return cur.fetchone()["id"]


def list_trip_invites_pending(trip_id):
    """Return pending invites for this trip: id, invitee_id, invitee_username, inviter_username, created_at."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT ti.id, ti.invitee_id, ti.created_at,
                      ue.username AS invitee_username, ui.username AS inviter_username
               FROM trip_invites ti
               JOIN users ue ON ue.id = ti.invitee_id
               JOIN users ui ON ui.id = ti.inviter_id
               WHERE ti.trip_id = %s AND ti.status = 'pending'
               ORDER BY ti.created_at DESC""",
            (trip_id,),
        )
        return cur.fetchall()


def list_incoming_trip_invites(user_id):
    """Return pending trip invites for this user (invitee): id, trip_id, trip_name, inviter_username, created_at."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT ti.id, ti.trip_id, ti.created_at,
                      t.trip_name, u.username AS inviter_username
               FROM trip_invites ti
               JOIN trips t ON t.id = ti.trip_id
               JOIN users u ON u.id = ti.inviter_id
               WHERE ti.invitee_id = %s AND ti.status = 'pending'
               ORDER BY ti.created_at DESC""",
            (user_id,),
        )
        return cur.fetchall()


def has_pending_invite_to_trip(user_id, trip_id):
    """True if user has a pending invite to this trip."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM trip_invites WHERE trip_id = %s AND invitee_id = %s AND status = 'pending'",
            (trip_id, user_id),
        )
        return cur.fetchone() is not None


def accept_trip_invite(invite_id, user_id):
    """Invitee accepts: add to trip_collaborators, set invite status accepted. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT trip_id, invitee_id FROM trip_invites WHERE id = %s AND status = 'pending'",
            (invite_id,),
        )
        row = cur.fetchone()
        if not row or row["invitee_id"] != user_id:
            return False
        trip_id = row["trip_id"]
        cur.execute(
            "UPDATE trip_invites SET status = 'accepted' WHERE id = %s",
            (invite_id,),
        )
        cur.execute(
            "INSERT INTO trip_collaborators (trip_id, user_id, role) VALUES (%s, %s, 'member') ON CONFLICT (trip_id, user_id) DO NOTHING",
            (trip_id, user_id),
        )
        return True


def decline_trip_invite(invite_id, user_id):
    """Invitee declines. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE trip_invites SET status = 'declined' WHERE id = %s AND invitee_id = %s AND status = 'pending'",
            (invite_id, user_id),
        )
        return cur.rowcount > 0


def get_trip_id_for_invite(invite_id):
    """Return trip_id for an invite, or None if not found."""
    with get_cursor() as cur:
        cur.execute("SELECT trip_id FROM trip_invites WHERE id = %s", (invite_id,))
        row = cur.fetchone()
        return row["trip_id"] if row else None


# ---------- Trip Gear (Equipment Assignment) ----------
def get_trip_gear_pool(trip_id):
    """Get all gear from trip collaborators that could be assigned to this trip. Includes requirement_type and capacity_persons."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.user_id, g.type, g.name, g.capacity, g.weight_oz, 
                      g.brand, g.condition, g.notes, g.requirement_type_id, g.capacity_persons,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name,
                      u.username AS owner_username,
                      CASE WHEN tg.gear_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_assigned
               FROM trip_collaborators tc
               JOIN users u ON u.id = tc.user_id
               JOIN gear g ON g.user_id = tc.user_id
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               LEFT JOIN trip_gear tg ON tg.trip_id = %s AND tg.gear_id = g.id
               WHERE tc.trip_id = %s
               ORDER BY u.username, g.type, g.name""",
            (trip_id, trip_id),
        )
        return cur.fetchall()


def get_trip_assigned_gear(trip_id):
    """Get gear already assigned to this trip with owner info. Includes requirement_type and capacity_persons."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.type, g.name, g.capacity, g.weight_oz, 
                      g.brand, g.condition, g.requirement_type_id, g.capacity_persons,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name,
                      tg.quantity, u.username AS owner_username, tg.assigned_to_user_id
               FROM trip_gear tg
               JOIN gear g ON g.id = tg.gear_id
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               JOIN users u ON u.id = g.user_id
               WHERE tg.trip_id = %s
               ORDER BY g.type, g.name""",
            (trip_id,),
        )
        return cur.fetchall()


def assign_gear_to_trip(trip_id, gear_id):
    """Assign a piece of gear to a trip. Owner is determined by gear ownership."""
    with get_cursor() as cur:
        # Verify gear owner is a collaborator
        cur.execute(
            """SELECT g.user_id FROM gear g
               JOIN trip_collaborators tc ON tc.user_id = g.user_id AND tc.trip_id = %s
               WHERE g.id = %s""",
            (trip_id, gear_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Gear not found or owner not in trip")
        
        owner_id = row["user_id"]
        cur.execute(
            """INSERT INTO trip_gear (trip_id, gear_id, assigned_to_user_id, quantity)
               VALUES (%s, %s, %s, 1)
               ON CONFLICT (trip_id, gear_id) DO NOTHING""",
            (trip_id, gear_id, owner_id),
        )


def unassign_gear_from_trip(trip_id, gear_id):
    """Remove gear assignment from a trip."""
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM trip_gear WHERE trip_id = %s AND gear_id = %s",
            (trip_id, gear_id),
        )

