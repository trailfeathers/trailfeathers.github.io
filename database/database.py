
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
