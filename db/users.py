"""
TrailFeathers - User management: lookup by id/username, create user, check existence, get first user.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor


def get_user_by_id(user_id):
    """Return user row (id, username) or None."""
    with get_cursor() as cur:
        cur.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def get_user_by_username(username):
    """Return user row including password_hash, or None."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        )
        return cur.fetchone()


def create_user(username, password_hash):
    """Insert user; returns row with id, username."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username",
            (username, password_hash),
        )
        return cur.fetchone()


def user_exists_by_username(username):
    """True if a user with this username exists."""
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
