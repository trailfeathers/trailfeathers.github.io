
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

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO gear (user_id, type, name, capacity, weight_oz, brand, condition, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (user_id, gear_type, name, capacity, weight_oz, brand, condition, notes),
        )
        row = cur.fetchone()
        return row["id"]


def list_gear(user_id):
    """Return all gear for the given user (by user_id)."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, type, name, capacity, weight_oz, brand, condition, notes, created_at
               FROM gear WHERE user_id = %s ORDER BY created_at DESC""",
            (user_id,),
        )
        return cur.fetchall()


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
    """Create a trip and add creator as collaborator. Returns trip id."""
    trip_name = (payload.get("trip_name") or "").strip()
    if not trip_name:
        raise ValueError("Trip name is required")
    trail_name = (payload.get("trail_name") or "").strip() or None
    activity_type = (payload.get("activity_type") or "").strip()
    if not activity_type or activity_type not in ACTIVITY_TYPES:
        raise ValueError("Activity type must be one of: " + ", ".join(sorted(ACTIVITY_TYPES)))
    intended_start_date = payload.get("intended_start_date")
    if intended_start_date is not None and intended_start_date != "":
        intended_start_date = intended_start_date.strip() or None
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO trips (creator_id, trip_name, trail_name, activity_type, intended_start_date)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (creator_id, trip_name, trail_name, activity_type, intended_start_date),
        )
        row = cur.fetchone()
        trip_id = row["id"]
        cur.execute(
            """INSERT INTO trip_collaborators (trip_id, user_id, role) VALUES (%s, %s, 'creator')""",
            (trip_id, creator_id),
        )
        return trip_id


def list_trips_for_user(user_id):
    """Return trips where user is creator or in trip_collaborators. Includes creator username."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT t.id, t.trip_name, t.trail_name, t.activity_type, t.intended_start_date,
                      t.creator_id, u.username AS creator_username, t.created_at
               FROM trips t
               JOIN users u ON u.id = t.creator_id
               WHERE t.creator_id = %s
                  OR EXISTS (SELECT 1 FROM trip_collaborators tc WHERE tc.trip_id = t.id AND tc.user_id = %s)
               ORDER BY t.created_at DESC""",
            (user_id, user_id),
        )
        return cur.fetchall()


def get_trip(trip_id):
    """Return one trip with creator username, or None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT t.id, t.trip_name, t.trail_name, t.activity_type, t.intended_start_date,
                      t.creator_id, u.username AS creator_username, t.created_at
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
