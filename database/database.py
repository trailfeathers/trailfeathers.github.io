
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
