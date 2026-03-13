"""
Database connection utilities for TrailFeathers.
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
